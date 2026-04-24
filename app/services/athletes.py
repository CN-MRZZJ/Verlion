from typing import Optional

from app.models.repositories import SportsRepository
from .validators import ensure_in, optional_text, require_text


class MeetAthleteMixin:
    def add_department(self, name: str, total_members: int) -> int:
        return self._repo_write(lambda repo: repo.insert_department(name, total_members))

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
        ensure_in(gender, {"male", "female"}, "gender 必须是 male 或 female")
        if age_group is not None and age_group != "" and age_group not in ("A", "B", "C"):
            raise ValueError("age_group 必须是 A/B/C")
        resolved_group = age_group if age_group else None

        def _action(repo: SportsRepository) -> int:
            return repo.insert_athlete(
                athlete_type=athlete_type,
                athlete_no=athlete_no,
                name=name,
                gender=gender,
                department_id=department_id,
                age_group=resolved_group,
            )

        return self._repo_write(_action)

    def list_athletes(self):
        return self._repo_read(lambda repo: repo.list_athletes_with_department())

    def query_athletes(self, athlete_type: str = "", keyword: str = "") -> list[dict]:
        type_filter = (athlete_type or "").strip()
        if type_filter and type_filter not in {"competitive", "fun"}:
            raise ValueError("athlete_type 必须为 competitive/fun 或留空")
        kw = (keyword or "").strip().lower()

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            athletes = [dict(r) for r in repo.list_athletes_with_department()]
            pairs = [dict(r) for r in repo.list_registration_pairs()]
            events = [dict(r) for r in repo.list_events()]

        event_map = {int(e["id"]): e for e in events}
        reg_map: dict[tuple[str, int], list[int]] = {}
        for p in pairs:
            key = (str(p["athlete_type"]), int(p["athlete_ref_id"]))
            reg_map.setdefault(key, []).append(int(p["event_id"]))

        def _event_label(event: dict) -> str:
            g = self._event_gender_label(str(event.get("gender", "")))
            ag = self._event_group_label(str(event.get("age_group", "")))
            return f"{event.get('name', '')}{g}{ag}"

        items: list[dict] = []
        for a in athletes:
            at = str(a.get("athlete_type", ""))
            if type_filter and at != type_filter:
                continue

            hay = " ".join(
                [
                    str(a.get("athlete_no", "") or ""),
                    str(a.get("name", "") or ""),
                    str(a.get("department_name", "") or ""),
                ]
            ).lower()
            if kw and kw not in hay:
                continue

            key = (at, int(a.get("athlete_ref_id", 0)))
            event_ids = reg_map.get(key, [])
            labels = []
            for eid in event_ids:
                e = event_map.get(eid)
                if e and int(e.get("is_individual", 0)) == 1:
                    labels.append(_event_label(e))
            labels = sorted(set(labels))

            items.append(
                {
                    "athlete_type": at,
                    "athlete_ref_id": a.get("athlete_ref_id"),
                    "athlete_no": a.get("athlete_no", "") or "",
                    "name": a.get("name", "") or "",
                    "gender": a.get("gender", "") or "",
                    "age_group": a.get("age_group", "") or "",
                    "department_name": a.get("department_name", "") or "",
                    "registration_count": len(labels),
                    "registered_events": "；".join(labels),
                }
            )
        items.sort(key=lambda x: (str(x["athlete_type"]), str(x["athlete_no"]), str(x["name"])))
        return items

    def get_registered_individual_events(self, athlete_type: str, athlete_no: str) -> list[dict]:
        athlete_type = self._validate_athlete_type((athlete_type or "").strip())
        athlete_no_text = require_text(athlete_no, "athlete_no")

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            athlete = repo.get_athlete_by_no(athlete_type, athlete_no_text)
            if not athlete:
                raise ValueError(f"运动员不存在: {athlete_type}/{athlete_no_text}")
            rows = repo.list_registered_individual_events_for_athlete(
                athlete_type=athlete_type,
                athlete_ref_id=int(athlete["athlete_ref_id"]),
            )
            items = [dict(r) for r in rows]

        for it in items:
            it["label"] = (
                f"{it.get('name', '')}"
                f"{self._event_gender_label(str(it.get('gender', '')))}"
                f"{self._event_group_label(str(it.get('age_group', '')))}"
            )
        return items

    def list_individual_events_by_category(self, category: str):
        if category not in {"competitive", "fun"}:
            raise ValueError("category 必须为 competitive 或 fun")
        with self.db.connect() as conn:
            return SportsRepository(conn).list_individual_events_by_category(category)

    def add_athlete_by_department_name(
        self,
        athlete_type: str,
        athlete_no: Optional[str],
        name: str,
        gender: str,
        department_name: str,
        age_group: Optional[str] = None,
    ) -> int:
        athlete_type = self._validate_athlete_type(athlete_type)
        athlete_no_text = require_text(athlete_no, "athlete_no")
        name_text = require_text(name, "name")
        ensure_in(gender, {"male", "female"}, "gender 必须是 male 或 female")
        dept_name = require_text(department_name, "department_name")
        age_group_text = optional_text(age_group)
        if age_group_text and age_group_text not in {"A", "B", "C"}:
            raise ValueError("age_group 必须是 A/B/C")

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            exists = repo.get_athlete_by_no(athlete_type, athlete_no_text)
            if exists:
                raise ValueError(f"athlete_no 已存在: {athlete_no_text}")
            dept = repo.get_department_by_name(dept_name)
            if dept:
                dept_id = int(dept["id"])
            else:
                dept_id = repo.insert_department(dept_name, 0)
            athlete_id = repo.insert_athlete(
                athlete_type=athlete_type,
                athlete_no=athlete_no_text,
                name=name_text,
                gender=gender,
                department_id=dept_id,
                age_group=age_group_text,
            )
            conn.commit()
            return athlete_id

    def delete_athlete_by_no(self, athlete_type: str, athlete_no: str) -> dict:
        athlete_type = self._validate_athlete_type(athlete_type)
        athlete_no_text = require_text(athlete_no, "athlete_no")
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            athlete = repo.get_athlete_by_no(athlete_type, athlete_no_text)
            if not athlete:
                raise ValueError(f"运动员不存在: {athlete_type}/{athlete_no_text}")
            athlete_ref_id = int(athlete["athlete_ref_id"])
            related = repo.delete_athlete_related_data(athlete_type, athlete_ref_id)
            deleted = repo.delete_athlete_by_id(athlete_type, athlete_ref_id)
            conn.commit()
            return {
                "deleted_athlete": deleted,
                "deleted_related": related,
                "athlete_type": athlete_type,
                "athlete_no": athlete_no_text,
            }

    def adjust_athlete_registration(self, athlete_type: str, athlete_no: str, event_id: int, op: str) -> dict:
        athlete_type = self._validate_athlete_type(athlete_type)
        athlete_no_text = require_text(athlete_no, "athlete_no")
        if op not in {"add", "remove"}:
            raise ValueError("op 必须是 add 或 remove")

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            athlete = repo.get_athlete_by_no(athlete_type, athlete_no_text)
            if not athlete:
                raise ValueError(f"运动员不存在: {athlete_type}/{athlete_no_text}")
            athlete_ref_id = int(athlete["athlete_ref_id"])
            event = repo.get_event_by_id(event_id)
            if not event:
                raise ValueError(f"比赛项目不存在: {event_id}")
            if event["category"] != athlete_type:
                raise ValueError("项目类别与运动员类型不匹配")
            if int(event["is_individual"]) != 1:
                raise ValueError("仅个人项目支持运动员报名")
            if event["gender"] not in {athlete["gender"], "mixed"}:
                raise ValueError("项目性别与运动员不匹配")

            exists = repo.athlete_registration_exists(athlete_type, athlete_ref_id, event_id)
            changed = 0
            if op == "add":
                if exists:
                    conn.commit()
                    return {"changed": 0, "status": "exists"}
                repo.insert_athlete_registration(athlete_type, athlete_ref_id, event_id)
                changed = 1
            else:
                changed = repo.delete_athlete_registration(athlete_type, athlete_ref_id, event_id)

            conn.commit()
            return {
                "changed": changed,
                "status": "ok",
                "athlete_type": athlete_type,
                "athlete_no": athlete_no_text,
                "event_id": event_id,
                "op": op,
            }

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
