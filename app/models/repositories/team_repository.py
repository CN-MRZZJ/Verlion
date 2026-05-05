import sqlite3
from typing import Optional

from .crud import RESULTS, TEAMS, TEAM_MEMBERS, WhereClause


class TeamRepositoryMixin:
    def insert_team(self, department_id: int, event_id: int, name: str) -> int:
            return self._crud_insert(TEAMS, {"department_id": department_id, "event_id": event_id, "name": name})

    def get_team_by_id(self, team_id: int):
            return self._crud_get_by_id(TEAMS, team_id)

    def team_exists(self, department_id: int, event_id: int, name: str) -> bool:
            return self._crud_exists(TEAMS, WhereClause("department_id=? AND event_id=? AND name=?", (department_id, event_id, name)))

    def insert_team_member(self, team_id: int, athlete_type: str, athlete_ref_id: int) -> int:
            return self._crud_insert(
                TEAM_MEMBERS,
                {"team_id": team_id, "athlete_type": athlete_type, "athlete_ref_id": athlete_ref_id},
            )

    def team_member_exists(self, team_id: int, athlete_type: str, athlete_ref_id: int) -> bool:
            return self._crud_exists(
                TEAM_MEMBERS,
                WhereClause("team_id=? AND athlete_type=? AND athlete_ref_id=?", (team_id, athlete_type, athlete_ref_id)),
            )

    def delete_team_member(self, team_id: int, athlete_type: str, athlete_ref_id: int) -> int:
            return self._crud_delete_where(
                TEAM_MEMBERS,
                WhereClause("team_id=? AND athlete_type=? AND athlete_ref_id=?", (team_id, athlete_type, athlete_ref_id)),
            )

    def delete_team_related_data(self, team_id: int) -> dict[str, int]:
            counts = {"results": 0, "team_members": 0}
            counts["results"] = self._crud_delete_where(RESULTS, WhereClause("team_id=?", (team_id,)))

            counts["team_members"] = self._crud_delete_where(TEAM_MEMBERS, WhereClause("team_id=?", (team_id,)))
            return counts

    def delete_team_by_id(self, team_id: int) -> int:
            return self._crud_delete_by_id(TEAMS, team_id)

    def list_team_members_with_details(self, team_id: int):
            return self.conn.execute(
                """
                SELECT
                    tm.id,
                    tm.team_id,
                    tm.athlete_type,
                    tm.athlete_ref_id,
                    a.athlete_no,
                    a.name AS athlete_name,
                    a.gender,
                    a."group",
                    d.name AS department_name
                FROM team_members tm
                LEFT JOIN athletes a ON a.athlete_type = tm.athlete_type AND a.id = tm.athlete_ref_id
                LEFT JOIN departments d ON d.id = a.department_id
                WHERE tm.team_id=?
                ORDER BY tm.id
                """,
                (team_id,),
            ).fetchall()

    def list_teams_with_details(self):
            return self.conn.execute(
                """
                SELECT
                    t.id,
                    t.event_id,
                    t.name AS team_name,
                    d.name AS department_name,
                    e.name AS event_name,
                    e.gender,
                    e."group"
                FROM teams t
                JOIN departments d ON d.id = t.department_id
                JOIN events e ON e.id = t.event_id
                ORDER BY t.id
                """
            ).fetchall()

    def list_team_names_by_event_department(self, event_id: int, department_id: int):
            return self.conn.execute(
                """
                SELECT name
                FROM teams
                WHERE event_id=? AND department_id=?
                ORDER BY id
                """,
                (event_id, department_id),
            ).fetchall()

    def page_teams(
            self,
            page: int,
            page_size: int,
            keyword: str,
            department_name: str,
            gender: str = "",
            group: str = "",
            category: str = "",
            scoring_strategy: str = "",
            sort_by: str = "",
            sort_dir: str = "desc",
        ):
            where = ["1=1"]
            params: list = []
            if keyword:
                where.append("(t.name LIKE ? OR e.name LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if department_name:
                where.append("d.name = ?")
                params.append(department_name)
            if gender:
                where.append("e.gender = ?")
                params.append(gender)
            if group:
                where.append('e."group" = ?')
                params.append(group)
            if category:
                where.append("e.category = ?")
                params.append(category)
            if scoring_strategy:
                where.append("e.scoring_strategy = ?")
                params.append(scoring_strategy)
            where_sql = " AND ".join(where)
            order_sql = self._resolve_order(
                sort_by,
                sort_dir,
                {
                    "id": "t.id",
                    "team_name": "t.name",
                    "department_name": "d.name",
                    "event_name": "e.name",
                    "gender": "e.gender",
                    "group": 'e."group"',
                },
                "t.id DESC",
            )
            count_sql = f"""
                SELECT COUNT(*) AS c
                FROM teams t
                JOIN departments d ON d.id = t.department_id
                JOIN events e ON e.id = t.event_id
                WHERE {where_sql}
            """
            data_sql = f"""
                SELECT t.id, t.event_id, t.name AS team_name, d.name AS department_name, e.name AS event_name, e.gender, e."group"
                FROM teams t
                JOIN departments d ON d.id = t.department_id
                JOIN events e ON e.id = t.event_id
                WHERE {where_sql}
                ORDER BY {order_sql}
            """
            return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)
