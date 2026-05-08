import io
import json
import os
import re
import shutil
import subprocess
import tempfile

from openpyxl import load_workbook

from app.models.repositories import SportsRepository


class MeetNoticeMixin:
    def _rank_rows_for_notice(self, scoring_strategy: str, rows: list[dict]) -> list[dict]:
        tie_eps = 1e-9

        def _sort_key(item: dict):
            val = self._parse_performance_numeric(scoring_strategy, item.get("performance"))
            if val is None:
                return (1, float("inf"), int(item.get("id", 0)))
            if scoring_strategy == "time":
                return (0, val, int(item.get("id", 0)))
            return (0, -val, int(item.get("id", 0)))

        ranked = sorted(rows, key=_sort_key)
        prev_val = None
        prev_rank = 0
        for pos, row in enumerate(ranked, start=1):
            val = self._parse_performance_numeric(scoring_strategy, row.get("performance"))
            if prev_val is not None and val is not None and abs(val - prev_val) <= tie_eps:
                rank = prev_rank
            else:
                rank = pos
            row["rank"] = rank
            prev_val = val
            prev_rank = rank
        return ranked

    def export_personal_result_notice_xlsx(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
    ) -> tuple[bytes, str]:
        return self._export_result_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=template_dir,
            layout_config_path=layout_config_path,
            personal_only=True,
        )

    def export_team_result_notice_xlsx(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
    ) -> tuple[bytes, str]:
        return self._export_result_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=template_dir,
            layout_config_path=layout_config_path,
            personal_only=False,
        )

    def _export_result_notice_xlsx(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
        personal_only: bool,
    ) -> tuple[bytes, str]:
        safe_template_name = os.path.basename((template_name or "").strip())
        if not safe_template_name:
            raise ValueError("template_name 不能为空")
        if not safe_template_name.lower().endswith((".xlsx", ".xlsm")):
            raise ValueError("模板文件必须是 .xlsx 或 .xlsm")

        template_path = os.path.join(template_dir, safe_template_name)
        if not os.path.isfile(template_path):
            raise ValueError(f"模板文件不存在: {safe_template_name}")
        if not os.path.isfile(layout_config_path):
            raise ValueError("公示单坐标配置文件不存在")

        with open(layout_config_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        sheet_name = str(layout.get("sheet_name", "")).strip() or "Sheet1"
        environment_cells = layout.get("environment_cells", {}) or {}
        row_template = layout.get("row_template", {}) or {}
        start_row = int(layout.get("start_row", 15))
        max_rows = int(layout.get("max_rows", 8))

        if not row_template.get("rank"):
            raise ValueError("row_template 缺少 rank 列配置")

        if personal_only:
            event, rows, env = self._get_personal_notice_payload(event_id)
        else:
            event, rows, env = self._get_team_notice_payload(event_id)

        wb = load_workbook(template_path)
        ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active

        env_values = {
            "date": env.get("date", ""),
            "wind_direction": env.get("wind_direction", ""),
            "wind_speed": env.get("wind_speed", ""),
            "air_quality": env.get("air_quality", ""),
            "weather": env.get("weather", ""),
            "temperature_high": env.get("temperature_high", ""),
            "temperature_low": env.get("temperature_low", ""),
            "event_name": self._event_display_name(event),
            "notice_title": self._notice_title_for_event(event, layout),
        }
        for key, cell in environment_cells.items():
            if key in env_values and cell:
                ws[str(cell)] = env_values[key]

        for idx, row in enumerate(rows[:max_rows]):
            row_num = start_row + idx
            rank_cell = row_template.get("rank")
            if rank_cell:
                ws[f"{rank_cell}{row_num}"] = row.get("rank", "")
            name_cell = row_template.get("name")
            if name_cell:
                ws[f"{name_cell}{row_num}"] = row.get("name", "")
            dept_cell = row_template.get("department")
            if dept_cell:
                ws[f"{dept_cell}{row_num}"] = row.get("department_name", "")
            perf_cell = row_template.get("performance")
            if perf_cell:
                ws[f"{perf_cell}{row_num}"] = row.get("performance", "")

        buf = io.BytesIO()
        wb.save(buf)
        event_name_token = re.sub(r"[\\/:*?\"<>|]+", "_", self._event_display_name(event))
        filename = f"{'个人' if personal_only else '团体'}成绩公示单_{event_name_token}.xlsx"
        return buf.getvalue(), filename

    def _get_personal_notice_payload(self, event_id: int) -> tuple[dict, list[dict], dict[str, str]]:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event_row = repo.get_event_by_id(event_id)
            if not event_row:
                raise ValueError(f"项目不存在: {event_id}")
            event = dict(event_row)
            if int(event.get("is_individual", 0)) != 1:
                raise ValueError("仅个人项目支持导出个人成绩公示单")
            scoring_strategy = str(event.get("scoring_strategy", ""))
            raw_rows = [dict(r) for r in repo.list_individual_results_for_event_all(event_id)]
            rows = self._rank_rows_for_notice(scoring_strategy, raw_rows)[:8]
            for row in rows:
                row["performance"] = self._format_performance_for_display(scoring_strategy, row.get("performance"))
                row["name"] = row.get("athlete_name", "")
        env = self.get_report_environment_settings()
        return event, rows, env

    def _get_team_notice_payload(self, event_id: int) -> tuple[dict, list[dict], dict[str, str]]:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event_row = repo.get_event_by_id(event_id)
            if not event_row:
                raise ValueError(f"项目不存在: {event_id}")
            event = dict(event_row)
            if int(event.get("is_individual", 0)) != 0:
                raise ValueError("仅团体项目支持导出团体成绩公示单")
            scoring_strategy = str(event.get("scoring_strategy", ""))
            raw_rows = [dict(r) for r in repo.list_team_results_for_event_all(event_id)]
            rows = self._rank_rows_for_notice(scoring_strategy, raw_rows)[:8]
            for row in rows:
                row["performance"] = self._format_performance_for_display(scoring_strategy, row.get("performance"))
                row["name"] = row.get("team_name", "")
        env = self.get_report_environment_settings()
        return event, rows, env

    def _convert_xlsx_to_pdf_with_excel(self, xlsx_path: str, pdf_path: str) -> None:
        try:
            import pythoncom  # type: ignore
            import win32com.client as win32  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("缺少 pywin32 或无法加载 win32com") from exc

        excel = None
        wb = None
        inited = False
        try:
            pythoncom.CoInitialize()
            inited = True
            excel = win32.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            wb = excel.Workbooks.Open(os.path.abspath(xlsx_path))
            wb.ExportAsFixedFormat(0, os.path.abspath(pdf_path))
        finally:
            if wb is not None:
                try:
                    wb.Close(False)
                except Exception:
                    pass
            if excel is not None:
                try:
                    excel.Quit()
                except Exception:
                    pass
            if inited:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _convert_xlsx_to_pdf_with_libreoffice(self, xlsx_path: str, out_dir: str) -> str:
        exe = shutil.which("soffice")
        if not exe:
            raise RuntimeError("未找到 soffice")
        cmd = [exe, "--headless", "--convert-to", "pdf", "--outdir", out_dir, xlsx_path]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            stderr = (p.stderr or "").strip()
            raise RuntimeError(f"soffice 转换失败: {stderr or p.returncode}")
        pdf_path = os.path.splitext(xlsx_path)[0] + ".pdf"
        if not os.path.exists(pdf_path):
            raise RuntimeError("soffice 未生成 pdf 文件")
        return pdf_path

    def _convert_xlsx_bytes_to_pdf_bytes(self, xlsx_bytes: bytes) -> bytes:
        errors: list[str] = []
        with tempfile.TemporaryDirectory(prefix="sports_notice_") as tmpdir:
            xlsx_path = os.path.join(tmpdir, "notice.xlsx")
            pdf_path = os.path.join(tmpdir, "notice.pdf")
            with open(xlsx_path, "wb") as f:
                f.write(xlsx_bytes)

            try:
                self._convert_xlsx_to_pdf_with_excel(xlsx_path, pdf_path)
                if not os.path.exists(pdf_path):
                    raise RuntimeError("Excel 未生成 pdf 文件")
                with open(pdf_path, "rb") as f:
                    return f.read()
            except Exception as exc:
                errors.append(f"Excel 转换失败: {exc}")

            try:
                generated_pdf = self._convert_xlsx_to_pdf_with_libreoffice(xlsx_path, tmpdir)
                with open(generated_pdf, "rb") as f:
                    return f.read()
            except Exception as exc:
                errors.append(f"LibreOffice 转换失败: {exc}")

        joined = "；".join(errors)
        raise ValueError(
            "xlsx 转 pdf 失败。请安装 Microsoft Excel（并安装 pywin32）或安装 LibreOffice(soffice)。"
            + (f" 详情：{joined}" if joined else "")
        )

    def export_personal_result_notice_pdf(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
    ) -> tuple[bytes, str]:
        xlsx_bytes, xlsx_filename = self.export_personal_result_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=template_dir,
            layout_config_path=layout_config_path,
        )
        pdf_bytes = self._convert_xlsx_bytes_to_pdf_bytes(xlsx_bytes)
        pdf_filename = re.sub(r"\.xlsx$", ".pdf", xlsx_filename, flags=re.IGNORECASE)
        return pdf_bytes, pdf_filename

    def export_team_result_notice_pdf(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
    ) -> tuple[bytes, str]:
        xlsx_bytes, xlsx_filename = self.export_team_result_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=template_dir,
            layout_config_path=layout_config_path,
        )
        pdf_bytes = self._convert_xlsx_bytes_to_pdf_bytes(xlsx_bytes)
        pdf_filename = re.sub(r"\.xlsx$", ".pdf", xlsx_filename, flags=re.IGNORECASE)
        return pdf_bytes, pdf_filename

    # ── Attempt notices ────────────────────────────────────────────

    def export_personal_attempt_notice_xlsx(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
        attempt_number: int | None = None,
    ) -> tuple[bytes, str]:
        return self._export_attempt_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=template_dir,
            layout_config_path=layout_config_path,
            personal_only=True,
            attempt_number=attempt_number,
        )

    def export_team_attempt_notice_xlsx(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
        attempt_number: int | None = None,
    ) -> tuple[bytes, str]:
        return self._export_attempt_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=template_dir,
            layout_config_path=layout_config_path,
            personal_only=False,
            attempt_number=attempt_number,
        )

    def _export_attempt_notice_xlsx(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
        personal_only: bool,
        attempt_number: int | None = None,
    ) -> tuple[bytes, str]:
        safe_template_name = os.path.basename((template_name or "").strip())
        if not safe_template_name:
            raise ValueError("template_name 不能为空")
        if not safe_template_name.lower().endswith((".xlsx", ".xlsm")):
            raise ValueError("模板文件必须是 .xlsx 或 .xlsm")

        template_path = os.path.join(template_dir, safe_template_name)
        if not os.path.isfile(template_path):
            raise ValueError(f"模板文件不存在: {safe_template_name}")
        if not os.path.isfile(layout_config_path):
            raise ValueError("公示单坐标配置文件不存在")

        with open(layout_config_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        sheet_name = str(layout.get("sheet_name", "")).strip() or "Sheet1"
        environment_cells = layout.get("environment_cells", {}) or {}
        row_template = layout.get("row_template", {}) or {}
        attempt_columns = row_template.get("attempt_columns", []) or []
        start_row = int(layout.get("start_row", 15))
        max_rows = int(layout.get("max_rows", 40))

        if personal_only:
            event, groups, env = self._get_personal_attempt_notice_payload(event_id, attempt_number)
        else:
            event, groups, env = self._get_team_attempt_notice_payload(event_id, attempt_number)

        scoring_strategy = str(event.get("scoring_strategy", ""))
        if attempt_number is not None:
            for grp in groups:
                att = grp["attempts"][0] if grp["attempts"] else {}
                grp["performance"] = att.get("performance")
            groups = self._rank_rows_for_notice(scoring_strategy, groups)

        wb = load_workbook(template_path)
        template_ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active

        env_values = {
            "date": env.get("date", ""),
            "wind_direction": env.get("wind_direction", ""),
            "wind_speed": env.get("wind_speed", ""),
            "air_quality": env.get("air_quality", ""),
            "weather": env.get("weather", ""),
            "temperature_high": env.get("temperature_high", ""),
            "temperature_low": env.get("temperature_low", ""),
            "event_name": self._event_display_name(event),
            "notice_title": self._notice_title_for_event(event, layout),
        }
        if attempt_number is not None:
            env_values["notice_title"] = f"{env_values['notice_title']} - 第{attempt_number}轮"

        total = len(groups)
        page_count = max((total + max_rows - 1) // max_rows, 1) if max_rows > 0 else 1

        for page in range(page_count):
            if page == 0:
                ws = template_ws
            else:
                ws = wb.copy_worksheet(template_ws)
                ws.title = f"{sheet_name}_{page + 1}"

            for key, cell in environment_cells.items():
                if key in env_values and cell:
                    ws[str(cell)] = env_values[key]

            page_start = page * max_rows
            for idx, group in enumerate(groups[page_start:page_start + max_rows]):
                row_num = start_row + idx
                rank_cell = row_template.get("rank")
                if rank_cell:
                    ws[f"{rank_cell}{row_num}"] = group.get("rank", "")
                no_cell = row_template.get("athlete_no")
                if no_cell:
                    ws[f"{no_cell}{row_num}"] = group.get("athlete_no", "")
                name_cell = row_template.get("name")
                if name_cell:
                    ws[f"{name_cell}{row_num}"] = group.get("name", "")
                dept_cell = row_template.get("department")
                if dept_cell:
                    ws[f"{dept_cell}{row_num}"] = group.get("department_name", "")

                for att_idx, att in enumerate(group.get("attempts", [])):
                    if att_idx >= len(attempt_columns):
                        break
                    col = attempt_columns[att_idx]
                    if personal_only and not col:
                        continue
                    perf = self._format_performance_for_display(
                        scoring_strategy, att.get("performance")
                    )
                    if int(att.get("is_void", 0)):
                        perf = f"{perf}(作废)" if perf else "(作废)"
                    ws[f"{col}{row_num}"] = perf

        buf = io.BytesIO()
        wb.save(buf)
        event_name_token = re.sub(r"[\\/:*?\"<>|]+", "_", self._event_display_name(event))
        filename = f"{'个人' if personal_only else '团体'}轮次成绩表_{event_name_token}.xlsx"
        return buf.getvalue(), filename

    def _get_personal_attempt_notice_payload(self, event_id: int, attempt_number: int | None = None) -> tuple[dict, list[dict], dict[str, str]]:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event_row = repo.get_event_by_id(event_id)
            if not event_row:
                raise ValueError(f"项目不存在: {event_id}")
            event = dict(event_row)
            if int(event.get("is_individual", 0)) != 1:
                raise ValueError("仅个人项目支持导出个人轮次成绩表")
            raw = [dict(r) for r in repo.list_personal_attempts_for_event(event_id, attempt_number)]
        groups = self._group_attempts_by_athlete(raw)
        env = self.get_report_environment_settings()
        return event, groups, env

    def _get_team_attempt_notice_payload(self, event_id: int, attempt_number: int | None = None) -> tuple[dict, list[dict], dict[str, str]]:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event_row = repo.get_event_by_id(event_id)
            if not event_row:
                raise ValueError(f"项目不存在: {event_id}")
            event = dict(event_row)
            if int(event.get("is_individual", 0)) != 0:
                raise ValueError("仅团体项目支持导出团体轮次成绩表")
            raw = [dict(r) for r in repo.list_team_attempts_for_event(event_id, attempt_number)]
        groups = self._group_attempts_by_team(raw)
        env = self.get_report_environment_settings()
        return event, groups, env

    def _group_attempts_by_athlete(self, rows: list[dict]) -> list[dict]:
        groups: dict[str, dict] = {}
        order: list[str] = []
        for row in rows:
            key = f"{row.get('athlete_no', '')}|{row.get('athlete_name', '')}"
            if key not in groups:
                groups[key] = {
                    "athlete_no": row.get("athlete_no", ""),
                    "name": row.get("athlete_name", ""),
                    "department_name": row.get("department_name", ""),
                    "attempts": [],
                }
                order.append(key)
            groups[key]["attempts"].append({
                "attempt_number": row.get("attempt_number"),
                "performance": row.get("performance"),
                "is_void": row.get("is_void", 0),
            })
        result = []
        for idx, key in enumerate(order):
            entry = dict(groups[key])
            entry["rank"] = idx + 1
            result.append(entry)
        return result

    def _group_attempts_by_team(self, rows: list[dict]) -> list[dict]:
        groups: dict[str, dict] = {}
        order: list[str] = []
        for row in rows:
            key = str(row.get("team_name", ""))
            if key not in groups:
                groups[key] = {
                    "name": row.get("team_name", ""),
                    "department_name": row.get("department_name", ""),
                    "attempts": [],
                }
                order.append(key)
            groups[key]["attempts"].append({
                "attempt_number": row.get("attempt_number"),
                "performance": row.get("performance"),
                "is_void": row.get("is_void", 0),
            })
        result = []
        for idx, key in enumerate(order):
            entry = dict(groups[key])
            entry["rank"] = idx + 1
            result.append(entry)
        return result

    def export_personal_attempt_notice_pdf(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
        attempt_number: int | None = None,
    ) -> tuple[bytes, str]:
        xlsx_bytes, xlsx_filename = self.export_personal_attempt_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=template_dir,
            layout_config_path=layout_config_path,
            attempt_number=attempt_number,
        )
        pdf_bytes = self._convert_xlsx_bytes_to_pdf_bytes(xlsx_bytes)
        pdf_filename = re.sub(r"\.xlsx$", ".pdf", xlsx_filename, flags=re.IGNORECASE)
        return pdf_bytes, pdf_filename

    def export_team_attempt_notice_pdf(
        self,
        event_id: int,
        template_name: str,
        template_dir: str,
        layout_config_path: str,
        attempt_number: int | None = None,
    ) -> tuple[bytes, str]:
        xlsx_bytes, xlsx_filename = self.export_team_attempt_notice_xlsx(
            event_id=event_id,
            template_name=template_name,
            template_dir=template_dir,
            layout_config_path=layout_config_path,
            attempt_number=attempt_number,
        )
        pdf_bytes = self._convert_xlsx_bytes_to_pdf_bytes(xlsx_bytes)
        pdf_filename = re.sub(r"\.xlsx$", ".pdf", xlsx_filename, flags=re.IGNORECASE)
        return pdf_bytes, pdf_filename
