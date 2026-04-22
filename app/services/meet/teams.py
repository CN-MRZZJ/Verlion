from typing import Optional

from app.models import SportsRepository
from .validators import require_text


class MeetTeamMixin:
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

    def list_team_events(self) -> list[dict]:
        items = [dict(r) for r in self._repo_read(lambda repo: repo.list_events())]
        return [i for i in items if int(i.get("is_individual", 1)) == 0]

    def query_teams(
        self,
        keyword: str = "",
        department_name: str = "",
        event_id: Optional[int] = None,
    ) -> list[dict]:
        kw = (keyword or "").strip().lower()
        dept = (department_name or "").strip()
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            teams = [dict(r) for r in repo.list_teams_with_details()]

            items: list[dict] = []
            for t in teams:
                if dept and str(t.get("department_name", "")) != dept:
                    continue
                if event_id is not None and int(t.get("event_id", 0)) != int(event_id):
                    continue
                hay = " ".join(
                    [
                        str(t.get("team_name", "") or ""),
                        str(t.get("department_name", "") or ""),
                        str(t.get("event_name", "") or ""),
                    ]
                ).lower()
                if kw and kw not in hay:
                    continue

                members = [dict(r) for r in repo.list_team_members_with_details(int(t["id"]))]
                member_names = []
                for m in members:
                    at = str(m.get("athlete_type", ""))
                    prefix = "竞" if at == "competitive" else ("趣" if at == "fun" else "")
                    member_names.append(f"{prefix}{m.get('athlete_no', '')}/{m.get('athlete_name', '')}")

                item = dict(t)
                item["member_count"] = len(members)
                item["members_summary"] = "；".join(member_names)
                items.append(item)

            items.sort(key=lambda x: int(x.get("id", 0)))
            return items

    def add_team_by_department_name(self, department_name: str, event_id: int, team_name: str) -> int:
        dept_name = require_text(department_name, "department_name")
        name = require_text(team_name, "team_name")

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            event = repo.get_event_by_id(event_id)
            if not event:
                raise ValueError(f"比赛项目不存在: {event_id}")
            if int(event["is_individual"]) != 0:
                raise ValueError("仅团体项目可建队")

            dept = repo.get_department_by_name(dept_name)
            if not dept:
                dept_id = repo.insert_department(dept_name, 0)
            else:
                dept_id = int(dept["id"])

            if repo.team_exists(dept_id, event_id, name):
                raise ValueError("该单位在此项目下已存在同名队伍")

            team_id = repo.insert_team(dept_id, event_id, name)
            conn.commit()
            return team_id

    def delete_team(self, team_id: int) -> dict:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            team = repo.get_team_by_id(team_id)
            if not team:
                raise ValueError(f"队伍不存在: {team_id}")
            related = repo.delete_team_related_data(team_id)
            deleted = repo.delete_team_by_id(team_id)
            conn.commit()
            return {"team_id": team_id, "deleted_team": deleted, "deleted_related": related}

    def get_team_members(self, team_id: int) -> list[dict]:
        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            team = repo.get_team_by_id(team_id)
            if not team:
                raise ValueError(f"队伍不存在: {team_id}")
            rows = [dict(r) for r in repo.list_team_members_with_details(team_id)]
            for r in rows:
                at = str(r.get("athlete_type", ""))
                r["athlete_type_text"] = "竞技" if at == "competitive" else ("趣味" if at == "fun" else at)
                g = str(r.get("gender", ""))
                r["gender_text"] = "男" if g == "male" else ("女" if g == "female" else g)
            return rows

    def adjust_team_member(self, team_id: int, athlete_type: str, athlete_no: str, op: str) -> dict:
        athlete_type = self._validate_athlete_type((athlete_type or "").strip())
        athlete_no_text = require_text(athlete_no, "athlete_no")
        if op not in {"add", "remove"}:
            raise ValueError("op 必须是 add 或 remove")

        with self.db.connect() as conn:
            repo = SportsRepository(conn)
            team = repo.get_team_by_id(team_id)
            if not team:
                raise ValueError(f"队伍不存在: {team_id}")
            athlete = repo.get_athlete_by_no(athlete_type, athlete_no_text)
            if not athlete:
                raise ValueError(f"运动员不存在: {athlete_type}/{athlete_no_text}")
            athlete_ref_id = int(athlete["athlete_ref_id"])

            event = repo.get_event_by_id(int(team["event_id"]))
            if not event:
                raise ValueError("队伍关联项目不存在")
            if int(event["is_individual"]) != 0:
                raise ValueError("仅团体项目允许队伍成员操作")
            if str(event["category"]) != athlete_type:
                raise ValueError("队伍项目类别与运动员类型不匹配")
            if int(athlete["department_id"]) != int(team["department_id"]):
                raise ValueError("队伍成员必须来自同一单位")
            if str(event["gender"]) in {"male", "female"} and str(event["gender"]) != str(athlete["gender"]):
                raise ValueError("队伍项目性别与运动员不匹配")

            exists = repo.team_member_exists(team_id, athlete_type, athlete_ref_id)
            changed = 0
            status = "ok"
            if op == "add":
                if exists:
                    status = "exists"
                else:
                    repo.insert_team_member(team_id, athlete_type, athlete_ref_id)
                    changed = 1
            else:
                changed = repo.delete_team_member(team_id, athlete_type, athlete_ref_id)
                if changed == 0:
                    status = "not_found"
            conn.commit()
            return {
                "team_id": team_id,
                "athlete_type": athlete_type,
                "athlete_no": athlete_no_text,
                "op": op,
                "changed": changed,
                "status": status,
            }
