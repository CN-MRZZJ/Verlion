import sqlite3
from typing import Optional

from .crud import ATHLETE_REGISTRATIONS, RESULTS, TEAM_MEMBERS, WhereClause


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
            return self._crud_insert(
                self._athlete_schema(athlete_type),
                {
                    "athlete_no": athlete_no,
                    "athlete_type": athlete_type,
                    "name": name,
                    "gender": gender,
                    "birth_date": birth_date_iso,
                    "department_id": department_id,
                    "age_group": age_group,
                },
            )

    def update_athlete_age_group(self, athlete_type: str, athlete_ref_id: int, age_group: str) -> None:
            self._crud_update_where(
                self._athlete_schema(athlete_type),
                {"age_group": age_group},
                WhereClause("id=? AND athlete_type=?", (athlete_ref_id, athlete_type)),
            )

    def get_athlete_by_id(self, athlete_type: str, athlete_ref_id: int):
            row = self._crud_get_one(
                self._athlete_schema(athlete_type),
                WhereClause("id=? AND athlete_type=?", (athlete_ref_id, athlete_type)),
            )
            if not row:
                return None
            payload = dict(row)
            payload["athlete_ref_id"] = payload["id"]
            return payload

    def get_athlete_by_no(self, athlete_type: str, athlete_no: str):
            row = self._crud_get_one(
                self._athlete_schema(athlete_type),
                WhereClause("athlete_type=? AND athlete_no=?", (athlete_type, athlete_no)),
            )
            if not row:
                return None
            payload = dict(row)
            payload["athlete_ref_id"] = payload["id"]
            return payload

    def get_athlete_by_profile(self, athlete_type: str, name: str, gender: str, department_id: int):
            row = self._crud_get_one(
                self._athlete_schema(athlete_type),
                WhereClause(
                    "athlete_type=? AND name=? AND gender=? AND department_id=?",
                    (athlete_type, name, gender, department_id),
                ),
                order_by="id ASC",
            )
            if not row:
                return None
            payload = dict(row)
            payload["athlete_ref_id"] = payload["id"]
            return payload

    def list_athletes_with_department(self):
            return self.conn.execute(
                """
                SELECT
                    a.athlete_type,
                    a.id AS athlete_ref_id,
                    a.athlete_no,
                    a.name,
                    a.gender,
                    a.age_group,
                    d.name AS department_name
                FROM athletes a
                JOIN departments d ON d.id = a.department_id
                ORDER BY a.athlete_type, a.id
                """
            ).fetchall()

    def list_athletes_by_type_with_department(self, athlete_type: str):
            self._athlete_schema(athlete_type)
            return self.conn.execute(
                """
                SELECT
                    a.id AS athlete_ref_id,
                    a.athlete_no,
                    a.name,
                    a.gender,
                    a.age_group,
                    d.name AS department_name
                FROM athletes a
                JOIN departments d ON d.id = a.department_id
                WHERE a.athlete_type=?
                ORDER BY a.id
                """,
                (athlete_type,),
            ).fetchall()

    def athletes_count(self) -> int:
            return self._crud_count(self._athlete_schema("competitive"))

    def delete_athlete_related_data(self, athlete_type: str, athlete_ref_id: int) -> dict[str, int]:
            counts = {"results": 0, "registrations": 0, "team_members": 0}
            counts["results"] = self._crud_delete_where(
                RESULTS,
                WhereClause("athlete_type=? AND athlete_ref_id=?", (athlete_type, athlete_ref_id)),
            )

            counts["registrations"] = self._crud_delete_where(
                ATHLETE_REGISTRATIONS,
                WhereClause("athlete_type=? AND athlete_ref_id=?", (athlete_type, athlete_ref_id)),
            )

            counts["team_members"] = self._crud_delete_where(
                TEAM_MEMBERS,
                WhereClause("athlete_type=? AND athlete_ref_id=?", (athlete_type, athlete_ref_id)),
            )
            return counts

    def delete_athlete_by_id(self, athlete_type: str, athlete_ref_id: int) -> int:
            return self._crud_delete_where(
                self._athlete_schema(athlete_type),
                WhereClause("id=? AND athlete_type=?", (athlete_ref_id, athlete_type)),
            )

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
