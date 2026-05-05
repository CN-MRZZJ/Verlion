import csv
import io
import re

from app.rules import group_values, load_rule_config, scoring_strategy_for_event_type, team_event_default_group
from app.models.repositories import SportsRepository


class MeetImportMixin:
    def import_events_rows(self, rows: list[dict[str, str]]) -> dict:
        required = {"name", "category", "event_type", "gender", "group", "is_individual"}
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
                    group = row["group"].strip()
                    is_individual = int(row["is_individual"].strip())

                    if category not in {"competitive", "fun"}:
                        raise ValueError("category 必须为 competitive 或 fun")
                    valid_event_types = set(load_rule_config().get("event_scoring_strategy", {}))
                    valid_event_types.discard("_comment")
                    if event_type not in valid_event_types:
                        raise ValueError(f"event_type 必须为 {'/'.join(sorted(valid_event_types))}")
                    if scoring_strategy and scoring_strategy not in {"time", "length", "count", "count_miss"}:
                        raise ValueError("scoring_strategy 必须为 time/length/count/count_miss")
                    target_genders = self._expand_event_genders(gender_raw)
                    allowed_event_groups = group_values("event")
                    if group not in allowed_event_groups:
                        raise ValueError(f"group 必须为 {'/'.join(sorted(allowed_event_groups))}")
                    if is_individual not in {0, 1}:
                        raise ValueError("is_individual 必须为 0 或 1")
                    if category == "fun" and event_type != "fun":
                        raise ValueError("趣味项目的 event_type 必须为 fun")
                    if category == "competitive" and event_type == "fun":
                        raise ValueError("竞技项目的 event_type 不能为 fun")
                    team_default_group = team_event_default_group()
                    if (category == "fun" or is_individual == 0) and group != team_default_group:
                        raise ValueError(f"趣味项目和集体项目必须使用 group={team_default_group}")
                    try:
                        fixed = scoring_strategy_for_event_type(event_type)
                        if scoring_strategy and scoring_strategy != fixed:
                            raise ValueError(f"{event_type} 项目的 scoring_strategy 必须为 {fixed}")
                        scoring_strategy = fixed
                    except ValueError:
                        if not scoring_strategy:
                            scoring_strategy = "count"

                    for gender in target_genders:
                        if repo.event_exists(
                            name,
                            category,
                            event_type,
                            scoring_strategy,
                            gender,
                            group,
                            is_individual,
                        ):
                            skipped += 1
                            skipped_details.append(
                                f"第{idx}行: 已存在，已跳过（name={name}, gender={gender}, group={group}）"
                            )
                            continue

                        repo.insert_event(
                            name,
                            category,
                            event_type,
                            scoring_strategy,
                            gender,
                            group,
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

                    group_raw = (row.get("group") or "").strip()
                    group = group_raw if group_raw else None
                    allowed_athlete_groups = group_values("athlete")
                    if group and group not in allowed_athlete_groups:
                        raise ValueError(f"group 必须为 {'/'.join(sorted(allowed_athlete_groups))}")

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
                        group=group,
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
                    csv_group = (row.get("group") or "").strip()
                    athlete_group = athlete.get("group") or ""
                    if csv_group and csv_group != athlete_group:
                        raise ValueError("group 与已导入运动员信息不一致")

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
            key = f"{event['name']}|{event['group']}"
            if key not in group_map:
                group_map[key] = []
                grouped_events.append((key, group_map[key]))
            group_map[key].append(event)

        event_columns: list[str] = []
        for key, items in grouped_events:
            ref = items[0]
            ids = sorted(int(e["id"]) for e in items)
            ids_token = "|".join(str(i) for i in ids)
            event_columns.append(f"{ref['name']}-{self._event_group_label(str(ref['group']))}[{ids_token}]")
        fieldnames = ["athlete_no", "name", "gender", "group", "department_name"] + event_columns
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for athlete in athletes:
            row = {
                "athlete_no": athlete.get("athlete_no", "") or "",
                "name": athlete.get("name", "") or "",
                "gender": athlete.get("gender", "") or "",
                "group": athlete.get("group", "") or "",
                "department_name": athlete.get("department_name", "") or "",
            }
            athlete_id = int(athlete["athlete_ref_id"])
            for (key, items), col in zip(grouped_events, event_columns):
                marked = any(registered_map.get((athlete_id, int(e["id"]))) for e in items)
                row[col] = "1" if marked else ""
            writer.writerow(row)

        filename = f"{target_category}_registrations_matrix.csv"
        return output.getvalue(), filename
