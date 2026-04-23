import sqlite3
from typing import Optional


class AthleteRepositoryMixin:
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
