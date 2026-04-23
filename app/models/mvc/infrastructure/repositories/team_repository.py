import sqlite3
from typing import Optional


class TeamRepositoryMixin:
    def insert_team(self, department_id: int, event_id: int, name: str) -> int:
            cur = self.conn.execute("INSERT INTO teams(department_id, event_id, name) VALUES(?,?,?)", (department_id, event_id, name))
            return int(cur.lastrowid)

    def get_team_by_id(self, team_id: int):
            return self.conn.execute("SELECT * FROM teams WHERE id=?", (team_id,)).fetchone()

    def team_exists(self, department_id: int, event_id: int, name: str) -> bool:
            row = self.conn.execute(
                "SELECT id FROM teams WHERE department_id=? AND event_id=? AND name=? LIMIT 1",
                (department_id, event_id, name),
            ).fetchone()
            return row is not None

    def insert_team_member(self, team_id: int, athlete_type: str, athlete_ref_id: int) -> int:
            cur = self.conn.execute(
                "INSERT INTO team_members(team_id, athlete_type, athlete_ref_id) VALUES(?,?,?)",
                (team_id, athlete_type, athlete_ref_id),
            )
            return int(cur.lastrowid)

    def team_member_exists(self, team_id: int, athlete_type: str, athlete_ref_id: int) -> bool:
            row = self.conn.execute(
                """
                SELECT id
                FROM team_members
                WHERE team_id=? AND athlete_type=? AND athlete_ref_id=?
                LIMIT 1
                """,
                (team_id, athlete_type, athlete_ref_id),
            ).fetchone()
            return row is not None

    def delete_team_member(self, team_id: int, athlete_type: str, athlete_ref_id: int) -> int:
            cur = self.conn.execute(
                """
                DELETE FROM team_members
                WHERE team_id=? AND athlete_type=? AND athlete_ref_id=?
                """,
                (team_id, athlete_type, athlete_ref_id),
            )
            return int(cur.rowcount or 0)

    def delete_team_related_data(self, team_id: int) -> dict[str, int]:
            counts = {"results": 0, "team_members": 0}
            cur_results = self.conn.execute("DELETE FROM results WHERE team_id=?", (team_id,))
            counts["results"] = int(cur_results.rowcount or 0)

            cur_members = self.conn.execute("DELETE FROM team_members WHERE team_id=?", (team_id,))
            counts["team_members"] = int(cur_members.rowcount or 0)
            return counts

    def delete_team_by_id(self, team_id: int) -> int:
            cur = self.conn.execute("DELETE FROM teams WHERE id=?", (team_id,))
            return int(cur.rowcount or 0)

    def list_team_members_with_details(self, team_id: int):
            return self.conn.execute(
                """
                SELECT
                    tm.id,
                    tm.team_id,
                    tm.athlete_type,
                    tm.athlete_ref_id,
                    COALESCE(ca.athlete_no, fa.athlete_no) AS athlete_no,
                    COALESCE(ca.name, fa.name) AS athlete_name,
                    COALESCE(ca.gender, fa.gender) AS gender,
                    COALESCE(ca.age_group, fa.age_group) AS age_group,
                    d.name AS department_name
                FROM team_members tm
                LEFT JOIN competitive_athletes ca ON tm.athlete_type='competitive' AND ca.id = tm.athlete_ref_id
                LEFT JOIN fun_athletes fa ON tm.athlete_type='fun' AND fa.id = tm.athlete_ref_id
                LEFT JOIN departments d ON d.id = COALESCE(ca.department_id, fa.department_id)
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
                    e.age_group
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
            age_group: str = "",
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
            if age_group:
                where.append("e.age_group = ?")
                params.append(age_group)
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
                    "age_group": "e.age_group",
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
                SELECT t.id, t.event_id, t.name AS team_name, d.name AS department_name, e.name AS event_name, e.gender, e.age_group
                FROM teams t
                JOIN departments d ON d.id = t.department_id
                JOIN events e ON e.id = t.event_id
                WHERE {where_sql}
                ORDER BY {order_sql}
            """
            return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)
