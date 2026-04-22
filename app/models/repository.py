import sqlite3
from typing import Optional


class SportsRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _athlete_table(self, athlete_type: str) -> str:
        if athlete_type not in {"competitive", "fun"}:
            raise ValueError("athlete_type 必须为 competitive 或 fun")
        return "competitive_athletes" if athlete_type == "competitive" else "fun_athletes"

    def set_meet_date(self, meet_date_iso: str) -> None:
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES('meet_date', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (meet_date_iso,),
        )

    def get_meet_date_iso(self) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM settings WHERE key='meet_date'").fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def get_setting(self, key: str) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def insert_department(self, name: str, total_members: int) -> int:
        cur = self.conn.execute("INSERT INTO departments(name, total_members) VALUES(?,?)", (name, total_members))
        return int(cur.lastrowid)

    def get_department_by_name(self, name: str):
        return self.conn.execute("SELECT id, total_members FROM departments WHERE name=?", (name,)).fetchone()

    def update_department_total_members(self, department_id: int, total_members: int) -> None:
        self.conn.execute("UPDATE departments SET total_members=? WHERE id=?", (total_members, department_id))

    def insert_athlete(
        self,
        athlete_type: str,
        athlete_no: Optional[str],
        name: str,
        gender: str,
        department_id: int,
        age_group: Optional[str],
        birth_date_iso: Optional[str] = None,
    ) -> int:
        table = self._athlete_table(athlete_type)
        cur = self.conn.execute(
            f"INSERT INTO {table}(athlete_no, name, gender, birth_date, department_id, age_group) VALUES(?,?,?,?,?,?)",
            (athlete_no, name, gender, birth_date_iso, department_id, age_group),
        )
        return int(cur.lastrowid)

    def update_athlete_age_group(self, athlete_type: str, athlete_ref_id: int, age_group: str) -> None:
        table = self._athlete_table(athlete_type)
        self.conn.execute(f"UPDATE {table} SET age_group=? WHERE id=?", (age_group, athlete_ref_id))

    def get_athlete_by_id(self, athlete_type: str, athlete_ref_id: int):
        table = self._athlete_table(athlete_type)
        row = self.conn.execute(f"SELECT * FROM {table} WHERE id=?", (athlete_ref_id,)).fetchone()
        if not row:
            return None
        payload = dict(row)
        payload["athlete_type"] = athlete_type
        payload["athlete_ref_id"] = payload["id"]
        return payload

    def get_athlete_by_no(self, athlete_type: str, athlete_no: str):
        table = self._athlete_table(athlete_type)
        row = self.conn.execute(f"SELECT * FROM {table} WHERE athlete_no=?", (athlete_no,)).fetchone()
        if not row:
            return None
        payload = dict(row)
        payload["athlete_type"] = athlete_type
        payload["athlete_ref_id"] = payload["id"]
        return payload

    def get_athlete_by_profile(self, athlete_type: str, name: str, gender: str, department_id: int):
        table = self._athlete_table(athlete_type)
        row = self.conn.execute(
            f"""
            SELECT * FROM {table}
            WHERE name=? AND gender=? AND department_id=?
            ORDER BY id ASC
            LIMIT 1
            """,
            (name, gender, department_id),
        ).fetchone()
        if not row:
            return None
        payload = dict(row)
        payload["athlete_type"] = athlete_type
        payload["athlete_ref_id"] = payload["id"]
        return payload

    def list_athletes_with_department(self):
        return self.conn.execute(
            """
            SELECT * FROM (
                SELECT
                    'competitive' AS athlete_type,
                    a.id AS athlete_ref_id,
                    a.athlete_no,
                    a.name,
                    a.gender,
                    a.age_group,
                    d.name AS department_name
                FROM competitive_athletes a
                JOIN departments d ON d.id = a.department_id
                UNION ALL
                SELECT
                    'fun' AS athlete_type,
                    a.id AS athlete_ref_id,
                    a.athlete_no,
                    a.name,
                    a.gender,
                    a.age_group,
                    d.name AS department_name
                FROM fun_athletes a
                JOIN departments d ON d.id = a.department_id
            ) t
            ORDER BY t.athlete_type, t.athlete_ref_id
            """
        ).fetchall()

    def list_athletes_by_type_with_department(self, athlete_type: str):
        table = self._athlete_table(athlete_type)
        return self.conn.execute(
            f"""
            SELECT
                a.id AS athlete_ref_id,
                a.athlete_no,
                a.name,
                a.gender,
                a.age_group,
                d.name AS department_name
            FROM {table} a
            JOIN departments d ON d.id = a.department_id
            ORDER BY a.id
            """
        ).fetchall()

    def insert_event(
        self,
        name: str,
        category: str,
        event_type: str,
        scoring_strategy: str,
        gender: str,
        age_group: str,
        is_individual: int,
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO events(name, category, event_type, scoring_strategy, gender, age_group, is_individual) VALUES(?,?,?,?,?,?,?)",
            (name, category, event_type, scoring_strategy, gender, age_group, is_individual),
        )
        return int(cur.lastrowid)

    def event_exists(
        self,
        name: str,
        category: str,
        event_type: str,
        scoring_strategy: str,
        gender: str,
        age_group: str,
        is_individual: int,
    ) -> bool:
        row = self.conn.execute(
            """
            SELECT id FROM events
            WHERE name=? AND category=? AND event_type=? AND scoring_strategy=? AND gender=? AND age_group=? AND is_individual=?
            """,
            (name, category, event_type, scoring_strategy, gender, age_group, is_individual),
        ).fetchone()
        return row is not None

    def get_event_by_id(self, event_id: int):
        return self.conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()

    def list_events(self):
        return self.conn.execute(
            "SELECT id, name, category, event_type, scoring_strategy, gender, age_group, is_individual FROM events ORDER BY id"
        ).fetchall()

    def list_individual_events_by_category(self, category: str):
        return self.conn.execute(
            """
            SELECT id, name, category, gender, age_group, is_individual
            FROM events
            WHERE category=? AND is_individual=1
            ORDER BY id
            """,
            (category,),
        ).fetchall()

    def events_count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"])

    def insert_athlete_registration(self, athlete_type: str, athlete_ref_id: int, event_id: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO athlete_registrations(athlete_type, athlete_ref_id, event_id) VALUES(?,?,?)",
            (athlete_type, athlete_ref_id, event_id),
        )
        return int(cur.lastrowid)

    def list_registration_pairs_by_type(self, athlete_type: str):
        return self.conn.execute(
            """
            SELECT athlete_ref_id, event_id
            FROM athlete_registrations
            WHERE athlete_type=?
            """,
            (athlete_type,),
        ).fetchall()

    def list_registered_individual_events_for_athlete(self, athlete_type: str, athlete_ref_id: int):
        return self.conn.execute(
            """
            SELECT
                e.id,
                e.name,
                e.gender,
                e.age_group
            FROM athlete_registrations r
            JOIN events e ON e.id = r.event_id
            WHERE r.athlete_type=? AND r.athlete_ref_id=? AND e.is_individual=1
            ORDER BY e.id
            """,
            (athlete_type, athlete_ref_id),
        ).fetchall()

    def list_registration_pairs(self):
        return self.conn.execute(
            """
            SELECT athlete_type, athlete_ref_id, event_id
            FROM athlete_registrations
            """
        ).fetchall()

    def athlete_registration_exists(self, athlete_type: str, athlete_ref_id: int, event_id: int) -> bool:
        row = self.conn.execute(
            """
            SELECT id
            FROM athlete_registrations
            WHERE athlete_type=? AND athlete_ref_id=? AND event_id=?
            LIMIT 1
            """,
            (athlete_type, athlete_ref_id, event_id),
        ).fetchone()
        return row is not None

    def delete_athlete_registration(self, athlete_type: str, athlete_ref_id: int, event_id: int) -> int:
        cur = self.conn.execute(
            """
            DELETE FROM athlete_registrations
            WHERE athlete_type=? AND athlete_ref_id=? AND event_id=?
            """,
            (athlete_type, athlete_ref_id, event_id),
        )
        return int(cur.rowcount or 0)

    def delete_athlete_related_data(self, athlete_type: str, athlete_ref_id: int) -> dict[str, int]:
        counts = {"results": 0, "registrations": 0, "team_members": 0}
        cur_results = self.conn.execute(
            "DELETE FROM results WHERE athlete_type=? AND athlete_ref_id=?",
            (athlete_type, athlete_ref_id),
        )
        counts["results"] = int(cur_results.rowcount or 0)

        cur_regs = self.conn.execute(
            "DELETE FROM athlete_registrations WHERE athlete_type=? AND athlete_ref_id=?",
            (athlete_type, athlete_ref_id),
        )
        counts["registrations"] = int(cur_regs.rowcount or 0)

        cur_team_members = self.conn.execute(
            "DELETE FROM team_members WHERE athlete_type=? AND athlete_ref_id=?",
            (athlete_type, athlete_ref_id),
        )
        counts["team_members"] = int(cur_team_members.rowcount or 0)
        return counts

    def delete_athlete_by_id(self, athlete_type: str, athlete_ref_id: int) -> int:
        table = self._athlete_table(athlete_type)
        cur = self.conn.execute(f"DELETE FROM {table} WHERE id=?", (athlete_ref_id,))
        return int(cur.rowcount or 0)

    def count_fun_individual_registrations(self, athlete_type: str, athlete_ref_id: int) -> int:
        row = self.conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM athlete_registrations r
            JOIN events e ON e.id = r.event_id
            WHERE r.athlete_type=? AND r.athlete_ref_id=? AND e.category='fun' AND e.is_individual=1
            """,
            (athlete_type, athlete_ref_id),
        ).fetchone()
        return int(row["c"])

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

    def insert_result(
        self,
        event_id: int,
        rank: int,
        points: int,
        athlete_type: Optional[str],
        athlete_ref_id: Optional[int],
        team_id: Optional[int],
        performance: Optional[str],
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO results(event_id, athlete_type, athlete_ref_id, team_id, rank, points, performance) VALUES(?,?,?,?,?,?,?)",
            (event_id, athlete_type, athlete_ref_id, team_id, rank, points, performance),
        )
        return int(cur.lastrowid)

    def list_event_results(self, event_id: int):
        return self.conn.execute(
            """
            SELECT id, rank, performance
            FROM results
            WHERE event_id=?
            ORDER BY rank ASC, id ASC
            """,
            (event_id,),
        ).fetchall()

    def list_individual_results_for_event(self, event_id: int):
        return self.conn.execute(
            """
            SELECT
                r.rank,
                COALESCE(ca.name, fa.name) AS athlete_name,
                COALESCE(d1.name, '') AS department_name,
                r.performance
            FROM results r
            LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
            LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
            LEFT JOIN departments d1 ON d1.id = COALESCE(ca.department_id, fa.department_id)
            WHERE r.event_id=? AND r.athlete_ref_id IS NOT NULL
            ORDER BY r.rank ASC, r.id ASC
            LIMIT 8
            """,
            (event_id,),
        ).fetchall()

    def update_result_rank_points(self, result_id: int, rank: int, points: int) -> None:
        self.conn.execute(
            "UPDATE results SET rank=?, points=? WHERE id=?",
            (rank, points, result_id),
        )

    def standings(self):
        return self.conn.execute(
            """
            WITH athlete_points AS (
                SELECT COALESCE(ca.department_id, fa.department_id) AS department_id, SUM(r.points) AS p
                FROM results r
                LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
                LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
                WHERE r.athlete_ref_id IS NOT NULL
                GROUP BY COALESCE(ca.department_id, fa.department_id)
            ),
            team_points AS (
                SELECT t.department_id AS department_id, SUM(r.points) AS p
                FROM results r
                JOIN teams t ON t.id = r.team_id
                GROUP BY t.department_id
            )
            SELECT d.id, d.name,
                   COALESCE(ap.p, 0) + COALESCE(tp.p, 0) AS total_points
            FROM departments d
            LEFT JOIN athlete_points ap ON ap.department_id = d.id
            LEFT JOIN team_points tp ON tp.department_id = d.id
            ORDER BY total_points DESC, d.id ASC
            """
        ).fetchall()

    def participation_rate(self):
        return self.conn.execute(
            """
            WITH personal_competitors AS (
                SELECT DISTINCT r.athlete_type, r.athlete_ref_id,
                    COALESCE(ca.department_id, fa.department_id) AS department_id
                FROM athlete_registrations r
                JOIN events e ON e.id = r.event_id
                LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
                LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
                WHERE e.is_individual = 1
            )
            SELECT d.id,
                   d.name,
                   d.total_members,
                   COUNT(pc.athlete_ref_id) AS active_members,
                   CASE
                     WHEN d.total_members = 0 THEN 0
                     ELSE ROUND(COUNT(pc.athlete_ref_id) * 100.0 / d.total_members, 2)
                   END AS participation_percent
            FROM departments d
            LEFT JOIN personal_competitors pc ON pc.department_id = d.id
            GROUP BY d.id, d.name, d.total_members
            ORDER BY participation_percent DESC, d.id ASC
            """
        ).fetchall()

    def recent_results(self, limit: int = 10):
        return self.conn.execute(
            """
            SELECT
                r.id,
                e.name AS event_name,
                e.scoring_strategy,
                CASE
                    WHEN r.athlete_ref_id IS NOT NULL THEN COALESCE(ca.name, fa.name)
                    ELSE t.name
                END AS target_name,
                r.rank,
                r.points,
                r.performance
            FROM results r
            JOIN events e ON e.id = r.event_id
            LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
            LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
            LEFT JOIN teams t ON t.id = r.team_id
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def departments_count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) AS c FROM departments").fetchone()["c"])

    def athletes_count(self) -> int:
        row = self.conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM competitive_athletes)
                +
                (SELECT COUNT(*) FROM fun_athletes) AS c
            """
        ).fetchone()
        return int(row["c"])

    def list_departments(self):
        return self.conn.execute(
            """
            SELECT id, name, total_members
            FROM departments
            ORDER BY id
            """
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

    def list_registrations_with_details(self):
        return self.conn.execute(
            """
            SELECT
                r.id,
                r.athlete_type,
                COALESCE(ca.name, fa.name) AS athlete_name,
                COALESCE(ca.gender, fa.gender) AS gender,
                COALESCE(ca.age_group, fa.age_group) AS age_group,
                d.name AS department_name,
                e.name AS event_name,
                e.category,
                r.created_at
            FROM athlete_registrations r
            LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
            LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
            LEFT JOIN departments d ON d.id = COALESCE(ca.department_id, fa.department_id)
            JOIN events e ON e.id = r.event_id
            ORDER BY r.id DESC
            """
        ).fetchall()

    def list_results_with_details(self):
        return self.conn.execute(
            """
            SELECT
                r.id,
                e.name AS event_name,
                e.category,
                e.scoring_strategy,
                e.age_group,
                CASE
                    WHEN r.athlete_ref_id IS NOT NULL THEN 'athlete'
                    ELSE 'team'
                END AS result_type,
                CASE
                    WHEN r.athlete_ref_id IS NOT NULL THEN r.athlete_type
                    ELSE ''
                END AS athlete_type,
                CASE
                    WHEN r.athlete_ref_id IS NOT NULL THEN COALESCE(ca.name, fa.name)
                    ELSE t.name
                END AS target_name,
                CASE
                    WHEN r.athlete_ref_id IS NOT NULL THEN d1.name
                    ELSE d2.name
                END AS department_name,
                r.rank,
                r.points,
                r.performance,
                r.created_at
            FROM results r
            JOIN events e ON e.id = r.event_id
            LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
            LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
            LEFT JOIN departments d1 ON d1.id = COALESCE(ca.department_id, fa.department_id)
            LEFT JOIN teams t ON t.id = r.team_id
            LEFT JOIN departments d2 ON d2.id = t.department_id
            ORDER BY r.id DESC
            """
        ).fetchall()

    def _paged_query(self, count_sql: str, data_sql: str, params: tuple, page: int, page_size: int):
        page = max(page, 1)
        page_size = max(page_size, 1)
        offset = (page - 1) * page_size
        total = self.conn.execute(count_sql, params).fetchone()["c"]
        rows = self.conn.execute(data_sql + " LIMIT ? OFFSET ?", params + (page_size, offset)).fetchall()
        return int(total), rows

    def _resolve_order(self, sort_by: str, sort_dir: str, allowed: dict[str, str], default_order: str) -> str:
        if sort_by in allowed:
            direction = "ASC" if str(sort_dir).lower() == "asc" else "DESC"
            return f"{allowed[sort_by]} {direction}"
        return default_order

    def page_events(
        self,
        page: int,
        page_size: int,
        keyword: str,
        gender: str,
        age_group: str,
        category: str,
        scoring_strategy: str,
        sort_by: str = "",
        sort_dir: str = "desc",
    ):
        where = ["1=1"]
        params: list = []
        if keyword:
            where.append("(name LIKE ? OR event_type LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if category:
            where.append("category = ?")
            params.append(category)
        if gender:
            where.append("gender = ?")
            params.append(gender)
        if age_group:
            where.append("age_group = ?")
            params.append(age_group)
        if scoring_strategy:
            where.append("scoring_strategy = ?")
            params.append(scoring_strategy)
        where_sql = " AND ".join(where)
        order_sql = self._resolve_order(
            sort_by,
            sort_dir,
            {
                "id": "id",
                "name": "name",
                "category": "category",
                "event_type": "event_type",
                "gender": "gender",
                "age_group": "age_group",
                "is_individual": "is_individual",
                "scoring_strategy": "scoring_strategy",
            },
            "id DESC",
        )
        count_sql = f"SELECT COUNT(*) AS c FROM events WHERE {where_sql}"
        data_sql = f"""
            SELECT id, name, category, event_type, gender, age_group, is_individual
            , scoring_strategy
            FROM events
            WHERE {where_sql}
            ORDER BY {order_sql}
        """
        return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)

    def page_athletes(
        self,
        page: int,
        page_size: int,
        keyword: str,
        department_name: str,
        gender: str,
        age_group: str,
        sort_by: str = "",
        sort_dir: str = "desc",
    ):
        where = ["1=1"]
        params: list = []
        if keyword:
            where.append("(u.name LIKE ? OR u.athlete_no LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if department_name:
            where.append("u.department_name = ?")
            params.append(department_name)
        if gender:
            where.append("u.gender = ?")
            params.append(gender)
        if age_group:
            where.append("u.age_group = ?")
            params.append(age_group)
        where_sql = " AND ".join(where)

        union_sql = """
            SELECT
                'competitive' AS athlete_type,
                a.id AS athlete_ref_id,
                a.athlete_no,
                a.name,
                a.gender,
                a.age_group,
                d.name AS department_name
            FROM competitive_athletes a
            JOIN departments d ON d.id = a.department_id
            UNION ALL
            SELECT
                'fun' AS athlete_type,
                a.id AS athlete_ref_id,
                a.athlete_no,
                a.name,
                a.gender,
                a.age_group,
                d.name AS department_name
            FROM fun_athletes a
            JOIN departments d ON d.id = a.department_id
        """

        count_sql = f"SELECT COUNT(*) AS c FROM ({union_sql}) u WHERE {where_sql}"
        order_sql = self._resolve_order(
            sort_by,
            sort_dir,
            {
                "athlete_type": "u.athlete_type",
                "athlete_ref_id": "u.athlete_ref_id",
                "athlete_no": "u.athlete_no",
                "name": "u.name",
                "gender": "u.gender",
                "age_group": "u.age_group",
                "department_name": "u.department_name",
            },
            "u.athlete_type ASC, u.athlete_ref_id DESC",
        )
        data_sql = f"""
            SELECT u.athlete_type, u.athlete_ref_id, u.athlete_no, u.name, u.gender, u.age_group, u.department_name
            FROM ({union_sql}) u
            WHERE {where_sql}
            ORDER BY {order_sql}
        """
        return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)

    def page_departments(self, page: int, page_size: int, keyword: str, sort_by: str = "", sort_dir: str = "desc"):
        where = ["1=1"]
        params: list = []
        if keyword:
            where.append("name LIKE ?")
            params.append(f"%{keyword}%")
        where_sql = " AND ".join(where)
        order_sql = self._resolve_order(
            sort_by,
            sort_dir,
            {"id": "id", "name": "name", "total_members": "total_members"},
            "id DESC",
        )
        count_sql = f"SELECT COUNT(*) AS c FROM departments WHERE {where_sql}"
        data_sql = f"""
            SELECT id, name, total_members
            FROM departments
            WHERE {where_sql}
            ORDER BY {order_sql}
        """
        return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)

    def page_teams(
        self,
        page: int,
        page_size: int,
        keyword: str,
        department_name: str,
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

    def page_registrations(
        self,
        page: int,
        page_size: int,
        keyword: str,
        department_name: str,
        sort_by: str = "",
        sort_dir: str = "desc",
    ):
        where = ["1=1"]
        params: list = []
        if keyword:
            where.append("(COALESCE(ca.name, fa.name) LIKE ? OR e.name LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if department_name:
            where.append("d.name = ?")
            params.append(department_name)
        where_sql = " AND ".join(where)
        order_sql = self._resolve_order(
            sort_by,
            sort_dir,
            {
                "id": "r.id",
                "athlete_type": "r.athlete_type",
                "athlete_name": "athlete_name",
                "gender": "gender",
                "age_group": "age_group",
                "department_name": "d.name",
                "event_name": "e.name",
                "category": "e.category",
                "created_at": "r.created_at",
            },
            "r.id DESC",
        )
        count_sql = f"""
            SELECT COUNT(*) AS c
            FROM athlete_registrations r
            JOIN events e ON e.id = r.event_id
            LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
            LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
            LEFT JOIN departments d ON d.id = COALESCE(ca.department_id, fa.department_id)
            WHERE {where_sql}
        """
        data_sql = f"""
            SELECT
                r.id,
                r.athlete_type,
                COALESCE(ca.name, fa.name) AS athlete_name,
                COALESCE(ca.gender, fa.gender) AS gender,
                COALESCE(ca.age_group, fa.age_group) AS age_group,
                d.name AS department_name,
                e.name AS event_name,
                e.category,
                r.created_at
            FROM athlete_registrations r
            JOIN events e ON e.id = r.event_id
            LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
            LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
            LEFT JOIN departments d ON d.id = COALESCE(ca.department_id, fa.department_id)
            WHERE {where_sql}
            ORDER BY {order_sql}
        """
        return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)

    def page_results(
        self,
        page: int,
        page_size: int,
        keyword: str,
        department_name: str,
        category: str,
        scoring_strategy: str,
        sort_by: str = "",
        sort_dir: str = "desc",
    ):
        where = ["1=1"]
        params: list = []
        if keyword:
            where.append("(e.name LIKE ? OR COALESCE(ca.name, fa.name, t.name) LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if department_name:
            where.append("(d1.name = ? OR d2.name = ?)")
            params.extend([department_name, department_name])
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
                "id": "r.id",
                "event_name": "e.name",
                "category": "e.category",
                "scoring_strategy": "e.scoring_strategy",
                "age_group": "e.age_group",
                "result_type": "result_type",
                "athlete_type": "athlete_type",
                "target_name": "target_name",
                "department_name": "department_name",
                "rank": "r.rank",
                "points": "r.points",
                "performance": "r.performance",
                "created_at": "r.created_at",
            },
            "r.id DESC",
        )
        count_sql = f"""
            SELECT COUNT(*) AS c
            FROM results r
            JOIN events e ON e.id = r.event_id
            LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
            LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
            LEFT JOIN departments d1 ON d1.id = COALESCE(ca.department_id, fa.department_id)
            LEFT JOIN teams t ON t.id = r.team_id
            LEFT JOIN departments d2 ON d2.id = t.department_id
            WHERE {where_sql}
        """
        data_sql = f"""
            SELECT
                r.id,
                e.name AS event_name,
                e.category,
                e.scoring_strategy,
                e.age_group,
                CASE WHEN r.athlete_ref_id IS NOT NULL THEN 'athlete' ELSE 'team' END AS result_type,
                COALESCE(r.athlete_type, '') AS athlete_type,
                CASE WHEN r.athlete_ref_id IS NOT NULL THEN COALESCE(ca.name, fa.name) ELSE t.name END AS target_name,
                CASE WHEN r.athlete_ref_id IS NOT NULL THEN d1.name ELSE d2.name END AS department_name,
                r.rank,
                r.points,
                r.performance,
                r.created_at
            FROM results r
            JOIN events e ON e.id = r.event_id
            LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
            LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
            LEFT JOIN departments d1 ON d1.id = COALESCE(ca.department_id, fa.department_id)
            LEFT JOIN teams t ON t.id = r.team_id
            LEFT JOIN departments d2 ON d2.id = t.department_id
            WHERE {where_sql}
            ORDER BY {order_sql}
        """
        return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)

    def page_standings(self, page: int, page_size: int, sort_by: str = "", sort_dir: str = "desc"):
        count_sql = "SELECT COUNT(*) AS c FROM departments"
        order_sql = self._resolve_order(
            sort_by,
            sort_dir,
            {"id": "d.id", "name": "d.name", "total_points": "total_points"},
            "total_points DESC, d.id ASC",
        )
        data_sql = """
            WITH athlete_points AS (
                SELECT COALESCE(ca.department_id, fa.department_id) AS department_id, SUM(r.points) AS p
                FROM results r
                LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
                LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
                WHERE r.athlete_ref_id IS NOT NULL
                GROUP BY COALESCE(ca.department_id, fa.department_id)
            ),
            team_points AS (
                SELECT t.department_id AS department_id, SUM(r.points) AS p
                FROM results r
                JOIN teams t ON t.id = r.team_id
                GROUP BY t.department_id
            )
            SELECT d.id, d.name, COALESCE(ap.p, 0) + COALESCE(tp.p, 0) AS total_points
            FROM departments d
            LEFT JOIN athlete_points ap ON ap.department_id = d.id
            LEFT JOIN team_points tp ON tp.department_id = d.id
            ORDER BY """ + order_sql + """
        """
        return self._paged_query(count_sql, data_sql, (), page, page_size)

    def page_participation(self, page: int, page_size: int, sort_by: str = "", sort_dir: str = "desc"):
        count_sql = "SELECT COUNT(*) AS c FROM departments"
        order_sql = self._resolve_order(
            sort_by,
            sort_dir,
            {
                "id": "d.id",
                "name": "d.name",
                "total_members": "d.total_members",
                "active_members": "active_members",
                "participation_percent": "participation_percent",
            },
            "participation_percent DESC, d.id ASC",
        )
        data_sql = """
            WITH personal_competitors AS (
                SELECT DISTINCT r.athlete_type, r.athlete_ref_id,
                    COALESCE(ca.department_id, fa.department_id) AS department_id
                FROM athlete_registrations r
                JOIN events e ON e.id = r.event_id
                LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
                LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
                WHERE e.is_individual = 1
            )
            SELECT d.id, d.name, d.total_members, COUNT(pc.athlete_ref_id) AS active_members,
                   CASE
                     WHEN d.total_members = 0 THEN 0
                     ELSE ROUND(COUNT(pc.athlete_ref_id) * 100.0 / d.total_members, 2)
                   END AS participation_percent
            FROM departments d
            LEFT JOIN personal_competitors pc ON pc.department_id = d.id
            GROUP BY d.id, d.name, d.total_members
            ORDER BY """ + order_sql + """
        """
        return self._paged_query(count_sql, data_sql, (), page, page_size)
