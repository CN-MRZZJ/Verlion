from datetime import date
import csv
import io
import re
from typing import Optional

from app.models import (
    POINT_RULE,
    Database,
    SportsRepository,
    calc_age_group,
    scoring_strategy_for_event_type,
)


class SportsMeetService:
    CLEAR_TABLES = {
        "settings": "系统设置",
        "departments": "部门",
        "events": "项目",
        "competitive_athletes": "竞技运动员",
        "fun_athletes": "趣味运动员",
        "teams": "队伍",
        "team_members": "队伍成员",
        "athlete_registrations": "报名记录",
        "results": "成绩记录",
    }

    def __init__(self, db_path: str) -> None:
        self.db = Database(db_path)

    def init_db(self) -> None:
        self.db.initialize()

    def set_meet_date(self, meet_date: date) -> None:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            repo.set_meet_date(meet_date.isoformat())
            conn.commit()

    def get_meet_date(self) -> date:
        with self.db.connect() as conn:
            iso = SportsRepository(conn).get_meet_date_iso()
            return date.fromisoformat(iso) if iso else date(2026, 4, 23)

    def calc_age_group(self, gender: str, birth_date: date) -> str:
        return calc_age_group(gender, birth_date, self.get_meet_date())

    def _validate_athlete_type(self, athlete_type: str) -> str:
        if athlete_type not in {"competitive", "fun"}:
            raise ValueError("athlete_type 必须为 competitive 或 fun")
        return athlete_type

    def _expand_event_genders(self, gender_raw: str) -> list[str]:
        gender = (gender_raw or "").strip().lower()
        aliases = {
            "male": ["male"],
            "female": ["female"],
            "mixed": ["mixed"],
            "男女": ["male", "female"],
            "both": ["male", "female"],
            "all": ["male", "female"],
            "male+female": ["male", "female"],
            "male/female": ["male", "female"],
            "mf": ["male", "female"],
        }
        if gender in aliases:
            return aliases[gender]
        raise ValueError("gender 必须为 male/female/mixed，或男女合并值（男女/both/male+female/all）")

    def _parse_performance_numeric(self, strategy: str, performance: Optional[str]) -> Optional[float]:
        text = (performance or "").strip()
        if not text:
            return None
        if strategy == "time":
            if ":" in text:
                parts = [p for p in text.split(":") if p != ""]
                try:
                    nums = [float(p) for p in parts]
                    sec = 0.0
                    for n in nums:
                        sec = sec * 60 + n
                    return sec
                except ValueError:
                    pass
            m = re.search(r"[-+]?\d+(?:\.\d+)?", text)
            return float(m.group(0)) if m else None
        if strategy in {"length", "count"}:
            m = re.search(r"[-+]?\d+(?:\.\d+)?", text)
            return float(m.group(0)) if m else None
        return None

    def _auto_rank_for_result(
        self,
        repo: SportsRepository,
        event_id: int,
        scoring_strategy: str,
        performance: Optional[str],
    ) -> int:
        rows = repo.list_event_results(event_id)
        if not rows:
            return 1
        max_rank = max(int(r["rank"]) for r in rows)
        new_val = self._parse_performance_numeric(scoring_strategy, performance)
        if new_val is None:
            return max_rank + 1

        better = 0
        comparable = 0
        for row in rows:
            old_val = self._parse_performance_numeric(scoring_strategy, row["performance"])
            if old_val is None:
                continue
            comparable += 1
            if scoring_strategy == "time":
                if old_val < new_val:
                    better += 1
            else:
                if old_val > new_val:
                    better += 1
        if comparable == 0:
            return max_rank + 1
        return better + 1

    def _recalculate_event_ranks(self, repo: SportsRepository, event_id: int, scoring_strategy: str) -> None:
        rows = [dict(r) for r in repo.list_event_results(event_id)]
        if not rows:
            return

        def _sort_key(item: dict):
            val = self._parse_performance_numeric(scoring_strategy, item.get("performance"))
            if val is None:
                return (1, float("inf"), int(item["id"]))
            if scoring_strategy == "time":
                return (0, val, int(item["id"]))
            return (0, -val, int(item["id"]))

        ranked = sorted(rows, key=_sort_key)
        for idx, row in enumerate(ranked, start=1):
            repo.update_result_rank_points(int(row["id"]), idx, POINT_RULE.get(idx, 0))

    def add_department(self, name: str, total_members: int) -> int:
        with self.db.connect() as conn:
            department_id = SportsRepository(conn).insert_department(name, total_members)
            conn.commit()
            return department_id

    def add_athlete(
        self,
        name: str,
        gender: str,
        department_id: int,
        athlete_no: Optional[str] = None,
        age_group: Optional[str] = None,
        athlete_type: str = "competitive",
    ) -> int:
        athlete_type = self._validate_athlete_type(athlete_type)
        if gender not in ("male", "female"):
            raise ValueError("gender 必须是 male 或 female")
        if age_group is not None and age_group != "" and age_group not in ("A", "B", "C"):
            raise ValueError("age_group 必须是 A/B/C")
        resolved_group = age_group if age_group else None

        with self.db.connect() as conn:
            athlete_id = SportsRepository(conn).insert_athlete(
                athlete_type=athlete_type,
                athlete_no=athlete_no,
                name=name,
                gender=gender,
                department_id=department_id,
                age_group=resolved_group,
            )
            conn.commit()
            return athlete_id

    def list_events(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).list_events()

    def list_athletes(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).list_athletes_with_department()

    def list_registration_pairs(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).list_registration_pairs()

    def register_athlete_event(self, athlete_type: str, athlete_ref_id: int, event_id: int) -> int:
        athlete_type = self._validate_athlete_type(athlete_type)
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            athlete = repo.get_athlete_by_id(athlete_type, athlete_ref_id)
            if not athlete:
                raise ValueError(f"运动员不存在: {athlete_type}/{athlete_ref_id}")
            event = repo.get_event_by_id(event_id)
            if not event:
                raise ValueError(f"比赛项目不存在: {event_id}")

            if event["category"] != athlete_type:
                raise ValueError("项目类别与运动员类型不匹配")
            if event["is_individual"] != 1:
                raise ValueError("该项目为集体项目，请使用组队流程")
            if event["gender"] != athlete["gender"]:
                raise ValueError("项目性别与运动员不匹配")
            reg_id = repo.insert_athlete_registration(athlete_type, athlete_ref_id, event_id)
            conn.commit()
            return reg_id

    def create_team(self, department_id: int, event_id: int, name: str) -> int:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event = repo.get_event_by_id(event_id)
            if not event:
                raise ValueError(f"比赛项目不存在: {event_id}")
            if event["is_individual"] != 0:
                raise ValueError("仅集体项目可以创建队伍")
            team_id = repo.insert_team(department_id, event_id, name)
            conn.commit()
            return team_id

    def add_team_member(self, team_id: int, athlete_type: str, athlete_ref_id: int) -> int:
        athlete_type = self._validate_athlete_type(athlete_type)
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            team = repo.get_team_by_id(team_id)
            if not team:
                raise ValueError(f"队伍不存在: {team_id}")
            athlete = repo.get_athlete_by_id(athlete_type, athlete_ref_id)
            if not athlete:
                raise ValueError(f"运动员不存在: {athlete_type}/{athlete_ref_id}")
            if athlete["department_id"] != team["department_id"]:
                raise ValueError("队伍成员必须来自同一部门")

            event = repo.get_event_by_id(int(team["event_id"]))
            if event and event["category"] != athlete_type:
                raise ValueError("队伍项目类别与运动员类型不匹配")

            team_member_id = repo.insert_team_member(team_id, athlete_type, athlete_ref_id)
            conn.commit()
            return team_member_id

    def record_result(
        self,
        event_id: int,
        rank: Optional[int] = None,
        athlete_type: Optional[str] = None,
        athlete_ref_id: Optional[int] = None,
        team_id: Optional[int] = None,
        performance: Optional[str] = None,
    ) -> int:
        has_athlete = athlete_ref_id is not None
        has_team = team_id is not None
        if has_athlete == has_team:
            raise ValueError("必须且只能传 athlete_ref_id 或 team_id 其中之一")

        if has_athlete:
            if not athlete_type:
                raise ValueError("录入个人成绩时，athlete_type 必填")
            athlete_type = self._validate_athlete_type(athlete_type)

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event = repo.get_event_by_id(event_id)
            if not event:
                raise ValueError(f"比赛项目不存在: {event_id}")

            if has_athlete:
                athlete = repo.get_athlete_by_id(athlete_type or "", int(athlete_ref_id))
                if not athlete:
                    raise ValueError(f"运动员不存在: {athlete_type}/{athlete_ref_id}")
                if event["category"] != athlete_type:
                    raise ValueError("项目类别与运动员类型不匹配")
            if has_team and not repo.get_team_by_id(int(team_id)):
                raise ValueError(f"队伍不存在: {team_id}")

            auto_rank = rank is None
            final_rank = int(rank) if rank is not None else self._auto_rank_for_result(
                repo,
                event_id,
                str(event["scoring_strategy"]),
                performance,
            )
            if final_rank < 1:
                raise ValueError("rank 必须 >= 1")

            result_id = repo.insert_result(
                event_id=event_id,
                rank=final_rank,
                points=POINT_RULE.get(final_rank, 0),
                athlete_type=athlete_type if has_athlete else None,
                athlete_ref_id=athlete_ref_id if has_athlete else None,
                team_id=team_id if has_team else None,
                performance=performance,
            )
            if auto_rank:
                self._recalculate_event_ranks(repo, event_id, str(event["scoring_strategy"]))
            conn.commit()
            return result_id

    def standings(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).standings()

    def participation_rate(self):
        with self.db.connect() as conn:
            return SportsRepository(conn).participation_rate()

    def dashboard_summary(self) -> dict:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            return {
                "event_count": repo.events_count(),
                "dept_count": repo.departments_count(),
                "athlete_count": repo.athletes_count(),
                "standings": repo.standings()[:10],
                "recent_results": repo.recent_results(10),
            }

    def workbench_data(self) -> dict:
        summary = self.dashboard_summary()
        status = self.get_initialization_status()
        alerts = []
        if not status["completed"]:
            alerts.append("系统初始化未完成，请先设置比赛日期并导入项目。")
        if summary["athlete_count"] == 0:
            alerts.append("暂无运动员数据，建议尽快导入名单。")
        return {
            **summary,
            "init_completed": status["completed"],
            "alerts": alerts,
        }

    def list_department_names(self) -> list[str]:
        with self.db.connect() as conn:
            rows = SportsRepository(conn).list_departments()
            return [row["name"] for row in rows]

    def get_data_view(self, view_name: str) -> list[dict]:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            if view_name == "events":
                rows = repo.list_events()
            elif view_name == "athletes":
                rows = repo.list_athletes_with_department()
            elif view_name == "departments":
                rows = repo.list_departments()
            elif view_name == "teams":
                rows = repo.list_teams_with_details()
            elif view_name == "registrations":
                rows = repo.list_registrations_with_details()
            elif view_name == "results":
                rows = repo.list_results_with_details()
            elif view_name == "standings":
                rows = repo.standings()
            elif view_name == "participation":
                rows = repo.participation_rate()
            else:
                raise ValueError(f"不支持的数据视图: {view_name}")
            return [dict(row) for row in rows]

    def get_grid_page(
        self,
        view_name: str,
        page: int,
        page_size: int,
        keyword: str = "",
        department_name: str = "",
        gender: str = "",
        age_group: str = "",
        category: str = "",
        scoring_strategy: str = "",
        sort_by: str = "",
        sort_dir: str = "desc",
    ) -> dict:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            if view_name == "events":
                total, rows = repo.page_events(
                    page, page_size, keyword, gender, age_group, category, scoring_strategy, sort_by, sort_dir
                )
            elif view_name == "athletes":
                total, rows = repo.page_athletes(
                    page, page_size, keyword, department_name, gender, age_group, sort_by, sort_dir
                )
            elif view_name == "departments":
                total, rows = repo.page_departments(page, page_size, keyword, sort_by, sort_dir)
            elif view_name == "teams":
                total, rows = repo.page_teams(page, page_size, keyword, department_name, sort_by, sort_dir)
            elif view_name == "registrations":
                total, rows = repo.page_registrations(page, page_size, keyword, department_name, sort_by, sort_dir)
            elif view_name == "results":
                total, rows = repo.page_results(
                    page, page_size, keyword, department_name, category, scoring_strategy, sort_by, sort_dir
                )
            elif view_name == "standings":
                total, rows = repo.page_standings(page, page_size, sort_by, sort_dir)
            elif view_name == "participation":
                total, rows = repo.page_participation(page, page_size, sort_by, sort_dir)
            else:
                raise ValueError(f"不支持的数据视图: {view_name}")

            items = [dict(r) for r in rows]
            return {
                "view": view_name,
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "columns": list(items[0].keys()) if items else [],
                "items": items,
            }

    def export_grid_csv(
        self,
        view_name: str,
        keyword: str = "",
        department_name: str = "",
        gender: str = "",
        age_group: str = "",
        category: str = "",
        scoring_strategy: str = "",
    ) -> str:
        first = self.get_grid_page(
            view_name=view_name,
            page=1,
            page_size=100000,
            keyword=keyword,
            department_name=department_name,
            gender=gender,
            age_group=age_group,
            category=category,
            scoring_strategy=scoring_strategy,
        )
        columns = first["columns"]
        items = first["items"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in items:
            writer.writerow(row)
        return output.getvalue()

    def get_initialization_status(self) -> dict:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            meet_date_iso = repo.get_meet_date_iso()
            event_count = repo.events_count()
            department_count = repo.departments_count()
            athlete_count = repo.athletes_count()

            checks = [
                {
                    "key": "meet_date",
                    "label": "比赛日期已设置",
                    "ok": bool(meet_date_iso),
                    "detail": meet_date_iso or "未设置",
                },
                {
                    "key": "events",
                    "label": "项目数据已导入",
                    "ok": event_count > 0,
                    "detail": f"{event_count} 个项目",
                },
            ]

            completed = all(item["ok"] for item in checks)
            return {
                "completed": completed,
                "checks": checks,
                "summary": {
                    "event_count": event_count,
                    "department_count": department_count,
                    "athlete_count": athlete_count,
                },
            }

    def import_events_rows(self, rows: list[dict[str, str]]) -> dict:
        required = {"name", "category", "event_type", "gender", "age_group", "is_individual"}
        missing = required - set(rows[0].keys()) if rows else required
        if missing:
            raise ValueError(f"项目模板缺少字段: {sorted(missing)}")

        inserted = 0
        skipped = 0
        errors: list[str] = []
        skipped_details: list[str] = []

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            for idx, row in enumerate(rows, start=2):
                try:
                    name = row["name"].strip()
                    category = row["category"].strip()
                    event_type = row["event_type"].strip()
                    scoring_strategy = (row.get("scoring_strategy") or "").strip()
                    gender_raw = row["gender"].strip()
                    age_group = row["age_group"].strip()
                    is_individual = int(row["is_individual"].strip())

                    if category not in {"competitive", "fun"}:
                        raise ValueError("category 必须为 competitive 或 fun")
                    if event_type not in {"track", "field", "fun"}:
                        raise ValueError("event_type 必须为 track/field/fun")
                    if scoring_strategy and scoring_strategy not in {"time", "length", "count"}:
                        raise ValueError("scoring_strategy 必须为 time/length/count")
                    target_genders = self._expand_event_genders(gender_raw)
                    if age_group not in {"A", "B", "C", "ALL"}:
                        raise ValueError("age_group 必须为 A/B/C/ALL")
                    if is_individual not in {0, 1}:
                        raise ValueError("is_individual 必须为 0 或 1")
                    if category == "fun" and event_type != "fun":
                        raise ValueError("趣味项目的 event_type 必须为 fun")
                    if category == "competitive" and event_type == "fun":
                        raise ValueError("竞技项目的 event_type 不能为 fun")
                    if (category == "fun" or is_individual == 0) and age_group != "ALL":
                        raise ValueError("趣味项目和集体项目必须使用 age_group=ALL")
                    if event_type in {"track", "field"}:
                        fixed = scoring_strategy_for_event_type(event_type)
                        if scoring_strategy and scoring_strategy != fixed:
                            raise ValueError(f"{event_type} 项目的 scoring_strategy 必须为 {fixed}")
                        scoring_strategy = fixed
                    else:
                        if not scoring_strategy:
                            scoring_strategy = "count"

                    for gender in target_genders:
                        if repo.event_exists(
                            name,
                            category,
                            event_type,
                            scoring_strategy,
                            gender,
                            age_group,
                            is_individual,
                        ):
                            skipped += 1
                            skipped_details.append(
                                f"第{idx}行: 已存在，已跳过（name={name}, gender={gender}, age_group={age_group}）"
                            )
                            continue

                        repo.insert_event(
                            name,
                            category,
                            event_type,
                            scoring_strategy,
                            gender,
                            age_group,
                            is_individual,
                        )
                        inserted += 1
                except Exception as exc:
                    errors.append(f"第{idx}行: {exc}")

            conn.commit()

        return {
            "inserted": inserted,
            "skipped": skipped,
            "errors": errors,
            "skipped_details": skipped_details,
        }

    def import_athletes_rows(self, rows: list[dict[str, str]], athlete_type: str) -> dict:
        athlete_type = self._validate_athlete_type(athlete_type)
        required = {"athlete_no", "name", "gender", "department_name"}
        missing = required - set(rows[0].keys()) if rows else required
        if missing:
            raise ValueError(f"名单模板缺少字段: {sorted(missing)}")

        inserted = 0
        skipped = 0
        errors: list[str] = []
        skipped_details: list[str] = []

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            for idx, row in enumerate(rows, start=2):
                try:
                    athlete_no = (row.get("athlete_no") or "").strip()
                    if not athlete_no:
                        raise ValueError("athlete_no 不能为空")
                    name = (row.get("name") or "").strip()
                    gender = (row.get("gender") or "").strip()
                    department_name = (row.get("department_name") or "").strip()
                    if not name:
                        raise ValueError("name 不能为空")
                    if gender not in {"male", "female"}:
                        raise ValueError("gender 必须为 male/female")
                    if not department_name:
                        raise ValueError("department_name 不能为空")

                    age_group_raw = (row.get("age_group") or "").strip()
                    age_group = age_group_raw if age_group_raw else None
                    if age_group and age_group not in {"A", "B", "C"}:
                        raise ValueError("age_group 必须为 A/B/C")

                    total_members_text = (row.get("total_members") or "0").strip()
                    total_members = int(total_members_text) if total_members_text else 0

                    dept = repo.get_department_by_name(department_name)
                    if dept:
                        dept_id = int(dept["id"])
                        if total_members > int(dept["total_members"]):
                            repo.update_department_total_members(dept_id, total_members)
                    else:
                        dept_id = repo.insert_department(department_name, total_members)

                    exists = repo.get_athlete_by_no(athlete_type, athlete_no)
                    if exists:
                        skipped += 1
                        skipped_details.append(f"第{idx}行: athlete_no={athlete_no} 已存在，已跳过")
                        continue

                    repo.insert_athlete(
                        athlete_type=athlete_type,
                        athlete_no=athlete_no,
                        name=name,
                        gender=gender,
                        department_id=dept_id,
                        age_group=age_group,
                    )
                    inserted += 1
                except Exception as exc:
                    errors.append(f"第{idx}行: {exc}")
            conn.commit()

        return {
            "inserted": inserted,
            "skipped": skipped,
            "errors": errors,
            "skipped_details": skipped_details,
        }

    def import_registrations_rows(self, rows: list[dict[str, str]], target_category: str) -> dict:
        return self.import_registration_matrix_rows(rows, target_category)

    def _parse_event_ids_from_header(self, header: str) -> list[int]:
        text = (header or "").strip()
        matched = re.search(r"\[([0-9|,/\s]+)\]\s*$", text)
        if matched:
            raw = matched.group(1)
            parts = re.split(r"[|,/\s]+", raw)
            ids = [int(p) for p in parts if p and p.isdigit()]
            return ids
        lowered = text.lower()
        if lowered.startswith("event_id_"):
            suffix = lowered.replace("event_id_", "", 1).strip()
            if suffix.isdigit():
                return [int(suffix)]
        return []

    def _is_selected_mark(self, value: str) -> bool:
        mark = (value or "").strip().lower()
        return mark in {"1", "y", "yes", "true", "t", "x", "√", "是"}

    def _event_gender_label(self, gender: str) -> str:
        if gender == "male":
            return "男子"
        if gender == "female":
            return "女子"
        return "混合"

    def _event_group_label(self, age_group: str) -> str:
        if age_group == "A":
            return "甲组"
        if age_group == "B":
            return "乙组"
        if age_group == "C":
            return "丙组"
        return "不限组"

    def import_registration_matrix_rows(self, rows: list[dict[str, str]], target_category: str) -> dict:
        if target_category not in {"competitive", "fun"}:
            raise ValueError("target_category 必须是 competitive 或 fun")
        required = {"athlete_no"}
        missing = required - set(rows[0].keys()) if rows else required
        if missing:
            raise ValueError(f"报名模板缺少字段: {sorted(missing)}")
        headers = list(rows[0].keys()) if rows else []
        event_columns: list[tuple[str, list[int]]] = []
        for header in headers:
            event_ids = self._parse_event_ids_from_header(header)
            if event_ids:
                event_columns.append((header, event_ids))
        if not event_columns:
            raise ValueError("未识别到项目列。请使用“项目名-组别[event_id]”或“项目名-组别[event_id1|event_id2]”。")

        inserted = 0
        skipped = 0
        errors: list[str] = []
        skipped_details: list[str] = []

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            all_events = [dict(r) for r in repo.list_individual_events_by_category(target_category)]
            event_cache: dict[int, dict] = {int(e["id"]): e for e in all_events}
            for idx, row in enumerate(rows, start=2):
                try:
                    athlete_no = (row.get("athlete_no") or "").strip()
                    if not athlete_no:
                        raise ValueError("athlete_no 不能为空")

                    athlete = repo.get_athlete_by_no(target_category, athlete_no)
                    if not athlete:
                        raise ValueError(f"运动员不存在: {athlete_no}（请先导入名单）")
                    athlete_id = int(athlete["id"])

                    csv_gender = (row.get("gender") or "").strip()
                    if csv_gender and csv_gender != athlete["gender"]:
                        raise ValueError("gender 与已导入运动员信息不一致")
                    csv_group = (row.get("age_group") or "").strip()
                    athlete_group = athlete.get("age_group") or ""
                    if csv_group and csv_group != athlete_group:
                        raise ValueError("age_group 与已导入运动员信息不一致")

                    selected_any = False
                    for header, event_ids in event_columns:
                        if not self._is_selected_mark(str(row.get(header, ""))):
                            continue
                        selected_any = True

                        candidate_events: list[dict] = []
                        for event_id in event_ids:
                            event = event_cache.get(event_id, {})
                            if event:
                                candidate_events.append(event)
                        if not candidate_events:
                            errors.append(f"第{idx}行: 项目不存在: {event_ids}")
                            continue
                        chosen_event = None
                        for event in candidate_events:
                            if event["category"] == target_category and int(event["is_individual"]) == 1 and event["gender"] == athlete["gender"]:
                                chosen_event = event
                                break
                        if chosen_event is None:
                            for event in candidate_events:
                                if event["category"] == target_category and int(event["is_individual"]) == 1 and event["gender"] == "mixed":
                                    chosen_event = event
                                    break
                        if chosen_event is None:
                            errors.append(f"第{idx}行: 无法按性别自动匹配项目（候选ID={event_ids}）")
                            continue

                        try:
                            repo.insert_athlete_registration(target_category, athlete_id, int(chosen_event["id"]))
                            inserted += 1
                        except Exception:
                            skipped += 1
                            skipped_details.append(
                                f"第{idx}行: 重复报名或唯一约束冲突，已跳过（athlete_no={athlete_no}, event_id={chosen_event['id']}）"
                            )
                    if not selected_any:
                        skipped += 1
                        skipped_details.append(f"第{idx}行: 未勾选任何项目，已跳过（athlete_no={athlete_no}）")
                except Exception as exc:
                    errors.append(f"第{idx}行: {exc}")
            conn.commit()

        return {
            "inserted": inserted,
            "skipped": skipped,
            "errors": errors,
            "skipped_details": skipped_details,
        }

    def export_registration_template_csv(self, target_category: str, event_id: int) -> tuple[str, str]:
        # 兼容旧接口：按单项目导出两列表头
        if target_category not in {"competitive", "fun"}:
            raise ValueError("category 必须是 competitive 或 fun")
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event = repo.get_event_by_id(event_id)
            if not event:
                raise ValueError(f"项目不存在: {event_id}")
            if event["category"] != target_category:
                raise ValueError(f"项目类别不匹配，应为 {target_category}")
            if int(event["is_individual"]) != 1:
                raise ValueError("仅个人项目支持报名模板导出")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["event_id", "athlete_no"])
        writer.writeheader()
        writer.writerow({"event_id": event_id, "athlete_no": ""})
        filename = f"{target_category}_registrations_event_{event_id}.csv"
        return output.getvalue(), filename

    def export_registration_matrix_template_csv(self, target_category: str) -> tuple[str, str]:
        if target_category not in {"competitive", "fun"}:
            raise ValueError("category 必须是 competitive 或 fun")

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            events = [dict(row) for row in repo.list_individual_events_by_category(target_category)]
            athletes = [dict(row) for row in repo.list_athletes_by_type_with_department(target_category)]
            pairs = repo.list_registration_pairs_by_type(target_category)

        registered_map: dict[tuple[int, int], bool] = {}
        for row in pairs:
            registered_map[(int(row["athlete_ref_id"]), int(row["event_id"]))] = True

        grouped_events: list[tuple[str, list[dict]]] = []
        group_map: dict[str, list[dict]] = {}
        for event in events:
            key = f"{event['name']}|{event['age_group']}"
            if key not in group_map:
                group_map[key] = []
                grouped_events.append((key, group_map[key]))
            group_map[key].append(event)

        event_columns: list[str] = []
        for key, items in grouped_events:
            ref = items[0]
            ids = sorted(int(e["id"]) for e in items)
            ids_token = "|".join(str(i) for i in ids)
            event_columns.append(
                f"{ref['name']}-{self._event_group_label(str(ref['age_group']))}[{ids_token}]"
            )
        fieldnames = ["athlete_no", "name", "gender", "age_group", "department_name"] + event_columns
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for athlete in athletes:
            row = {
                "athlete_no": athlete.get("athlete_no", "") or "",
                "name": athlete.get("name", "") or "",
                "gender": athlete.get("gender", "") or "",
                "age_group": athlete.get("age_group", "") or "",
                "department_name": athlete.get("department_name", "") or "",
            }
            athlete_id = int(athlete["athlete_ref_id"])
            for (key, items), col in zip(grouped_events, event_columns):
                marked = any(registered_map.get((athlete_id, int(e["id"]))) for e in items)
                row[col] = "1" if marked else ""
            writer.writerow(row)

        filename = f"{target_category}_registrations_matrix.csv"
        return output.getvalue(), filename

    def clear_table_data(
        self,
        requested_tables: list[str],
        confirm_text: str,
        confirm_code: str,
        acknowledged: bool,
    ) -> dict:
        selected = sorted({t for t in requested_tables if t in self.CLEAR_TABLES})
        if not selected:
            raise ValueError("请至少选择一张表")
        if not acknowledged:
            raise ValueError("请先勾选确认选项")
        if (confirm_text or "").strip().upper() != "DELETE":
            raise ValueError("请正确输入确认口令 DELETE")
        expected_code = f"CLEAR-{len(selected)}"
        if (confirm_code or "").strip().upper() != expected_code:
            raise ValueError(f"校验码错误，应为 {expected_code}")

        counts: dict[str, int] = {k: 0 for k in self.CLEAR_TABLES}

        def _exec_delete(conn, table_key: str, sql: str, params: tuple = ()) -> None:
            cur = conn.execute(sql, params)
            delta = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
            counts[table_key] += delta

        with self.db.connect() as conn:
            clear_settings = "settings" in selected
            clear_departments = "departments" in selected
            clear_events = "events" in selected
            clear_comp = "competitive_athletes" in selected or clear_departments
            clear_fun = "fun_athletes" in selected or clear_departments
            clear_teams = "teams" in selected or clear_events or clear_departments
            clear_team_members = "team_members" in selected
            clear_regs = "athlete_registrations" in selected
            clear_results = "results" in selected

            if clear_departments:
                _exec_delete(conn, "results", "DELETE FROM results")
                _exec_delete(conn, "athlete_registrations", "DELETE FROM athlete_registrations")
                _exec_delete(conn, "team_members", "DELETE FROM team_members")
                _exec_delete(conn, "teams", "DELETE FROM teams")
                _exec_delete(conn, "competitive_athletes", "DELETE FROM competitive_athletes")
                _exec_delete(conn, "fun_athletes", "DELETE FROM fun_athletes")
                _exec_delete(conn, "departments", "DELETE FROM departments")
            else:
                if clear_events:
                    _exec_delete(conn, "results", "DELETE FROM results")
                    _exec_delete(conn, "athlete_registrations", "DELETE FROM athlete_registrations")
                    _exec_delete(conn, "team_members", "DELETE FROM team_members")
                    _exec_delete(conn, "teams", "DELETE FROM teams")
                    _exec_delete(conn, "events", "DELETE FROM events")
                else:
                    if clear_teams:
                        _exec_delete(conn, "results", "DELETE FROM results WHERE team_id IS NOT NULL")
                        _exec_delete(conn, "team_members", "DELETE FROM team_members")
                        _exec_delete(conn, "teams", "DELETE FROM teams")
                    elif clear_team_members:
                        _exec_delete(conn, "team_members", "DELETE FROM team_members")

                    if clear_comp:
                        _exec_delete(conn, "results", "DELETE FROM results WHERE athlete_type='competitive'")
                        _exec_delete(
                            conn,
                            "athlete_registrations",
                            "DELETE FROM athlete_registrations WHERE athlete_type='competitive'",
                        )
                        _exec_delete(conn, "team_members", "DELETE FROM team_members WHERE athlete_type='competitive'")
                        _exec_delete(conn, "competitive_athletes", "DELETE FROM competitive_athletes")

                    if clear_fun:
                        _exec_delete(conn, "results", "DELETE FROM results WHERE athlete_type='fun'")
                        _exec_delete(
                            conn,
                            "athlete_registrations",
                            "DELETE FROM athlete_registrations WHERE athlete_type='fun'",
                        )
                        _exec_delete(conn, "team_members", "DELETE FROM team_members WHERE athlete_type='fun'")
                        _exec_delete(conn, "fun_athletes", "DELETE FROM fun_athletes")

                    if clear_results:
                        _exec_delete(conn, "results", "DELETE FROM results")
                    if clear_regs:
                        _exec_delete(conn, "athlete_registrations", "DELETE FROM athlete_registrations")
                    if clear_team_members and not clear_teams:
                        _exec_delete(conn, "team_members", "DELETE FROM team_members")

            if clear_settings:
                _exec_delete(conn, "settings", "DELETE FROM settings")

            conn.commit()

        affected = {k: v for k, v in counts.items() if v > 0}
        return {
            "requested_tables": selected,
            "expected_code": expected_code,
            "deleted_rows": affected,
        }
