import sqlite3
from typing import Optional


class RegistrationRepositoryMixin:
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

    def page_registrations(
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
                where.append("(COALESCE(ca.name, fa.name) LIKE ? OR e.name LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if department_name:
                where.append("d.name = ?")
                params.append(department_name)
            if gender:
                where.append("COALESCE(ca.gender, fa.gender) = ?")
                params.append(gender)
            if age_group:
                where.append("COALESCE(ca.age_group, fa.age_group) = ?")
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
