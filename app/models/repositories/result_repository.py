import sqlite3
from typing import Optional

from .crud import ATTEMPTS, RESULTS


class ResultRepositoryMixin:
    def insert_result(
            self,
            event_id: int,
            rank: int,
            points: int,
            athlete_type: Optional[str],
            athlete_ref_id: Optional[int],
            team_id: Optional[int],
            performance: Optional[str],
            entered_by: Optional[str] = None,
        ) -> int:
            return self._crud_insert(
                RESULTS,
                {
                    "event_id": event_id,
                    "athlete_type": athlete_type,
                    "athlete_ref_id": athlete_ref_id,
                    "team_id": team_id,
                    "rank": rank,
                    "points": points,
                    "performance": performance,
                    "entered_by": entered_by or "",
                },
            )

    def insert_attempt(
            self,
            event_id: int,
            rank: int,
            athlete_type: Optional[str],
            athlete_ref_id: Optional[int],
            team_id: Optional[int],
            performance: Optional[str],
            entered_by: Optional[str] = None,
        ) -> int:
            return self._crud_insert(
                ATTEMPTS,
                {
                    "event_id": event_id,
                    "athlete_type": athlete_type,
                    "athlete_ref_id": athlete_ref_id,
                    "team_id": team_id,
                    "rank": rank,
                    "performance": performance,
                    "entered_by": entered_by or "",
                },
            )

    def list_attempts_for_target(
            self,
            event_id: int,
            athlete_type: Optional[str],
            athlete_ref_id: Optional[int],
            team_id: Optional[int],
        ):
            if athlete_ref_id is not None:
                return self.conn.execute(
                    """
                    SELECT id, rank, performance, created_at
                    FROM attempts
                    WHERE event_id=? AND athlete_type=? AND athlete_ref_id=? AND team_id IS NULL
                    ORDER BY id ASC
                    """,
                    (event_id, athlete_type, athlete_ref_id),
                ).fetchall()

            if team_id is not None:
                return self.conn.execute(
                    """
                    SELECT id, rank, performance, created_at
                    FROM attempts
                    WHERE event_id=? AND team_id=? AND athlete_ref_id IS NULL AND athlete_type IS NULL
                    ORDER BY id ASC
                    """,
                    (event_id, team_id),
                ).fetchall()

            return []

    def get_result_by_target(
            self,
            event_id: int,
            athlete_type: Optional[str],
            athlete_ref_id: Optional[int],
            team_id: Optional[int],
        ):
            if athlete_ref_id is not None:
                return self.conn.execute(
                    """
                    SELECT id, rank, points, performance, entered_by
                    FROM results
                    WHERE event_id=? AND athlete_type=? AND athlete_ref_id=? AND team_id IS NULL
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (event_id, athlete_type, athlete_ref_id),
                ).fetchone()

            if team_id is not None:
                return self.conn.execute(
                    """
                    SELECT id, rank, points, performance, entered_by
                    FROM results
                    WHERE event_id=? AND team_id=? AND athlete_ref_id IS NULL AND athlete_type IS NULL
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (event_id, team_id),
                ).fetchone()

            return None

    def update_result(
            self,
            result_id: int,
            rank: int,
            points: int,
            performance: Optional[str],
            entered_by: Optional[str] = None,
        ) -> None:
            values = {"rank": rank, "points": points, "performance": performance}
            if entered_by is not None:
                values["entered_by"] = entered_by
            self._crud_update_by_id(RESULTS, result_id, values)

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
                    a.name AS athlete_name,
                    COALESCE(d1.name, '') AS department_name,
                    r.performance
                FROM results r
                LEFT JOIN athletes a ON a.athlete_type = r.athlete_type AND a.id = r.athlete_ref_id
                LEFT JOIN departments d1 ON d1.id = a.department_id
                WHERE r.event_id=? AND r.athlete_ref_id IS NOT NULL
                ORDER BY r.rank ASC, r.id ASC
                LIMIT 8
                """,
                (event_id,),
            ).fetchall()

    def list_individual_results_for_event_all(self, event_id: int):
            return self.conn.execute(
                """
                SELECT
                    r.id,
                    r.rank,
                    a.name AS athlete_name,
                    COALESCE(d1.name, '') AS department_name,
                    r.performance
                FROM results r
                LEFT JOIN athletes a ON a.athlete_type = r.athlete_type AND a.id = r.athlete_ref_id
                LEFT JOIN departments d1 ON d1.id = a.department_id
                WHERE r.event_id=? AND r.athlete_ref_id IS NOT NULL
                ORDER BY r.id ASC
                """,
                (event_id,),
            ).fetchall()

    def list_team_results_for_event_all(self, event_id: int):
            return self.conn.execute(
                """
                SELECT
                    r.id,
                    r.rank,
                    COALESCE(t.name, '') AS team_name,
                    COALESCE(d.name, '') AS department_name,
                    r.performance
                FROM results r
                LEFT JOIN teams t ON t.id = r.team_id
                LEFT JOIN departments d ON d.id = t.department_id
                WHERE r.event_id=? AND r.team_id IS NOT NULL
                ORDER BY r.id ASC
                """,
                (event_id,),
            ).fetchall()

    def update_result_rank_points(self, result_id: int, rank: int, points: int) -> None:
            self._crud_update_by_id(RESULTS, result_id, {"rank": rank, "points": points})

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
                        WHEN r.athlete_ref_id IS NOT NULL THEN a.name
                        ELSE t.name
                    END AS target_name,
                    CASE
                        WHEN r.athlete_ref_id IS NOT NULL THEN d1.name
                        ELSE d2.name
                    END AS department_name,
                    r.rank,
                    r.points,
                    r.performance,
                    r.entered_by,
                    r.created_at
                FROM results r
                JOIN events e ON e.id = r.event_id
                LEFT JOIN athletes a ON a.athlete_type = r.athlete_type AND a.id = r.athlete_ref_id
                LEFT JOIN departments d1 ON d1.id = a.department_id
                LEFT JOIN teams t ON t.id = r.team_id
                LEFT JOIN departments d2 ON d2.id = t.department_id
                ORDER BY r.id DESC
                """
            ).fetchall()

    def list_result_details(self):
            return self.conn.execute(
                """
                WITH team_member_summary AS (
                    SELECT
                        tm.team_id,
                        GROUP_CONCAT(a.athlete_no, '; ') AS team_member_athlete_nos,
                        GROUP_CONCAT(a.name, '; ') AS team_member_names,
                        GROUP_CONCAT(
                            CASE a.gender
                                WHEN 'male' THEN '男'
                                WHEN 'female' THEN '女'
                                ELSE COALESCE(a.gender, '')
                            END,
                            '; '
                        ) AS team_member_genders
                    FROM team_members tm
                    LEFT JOIN athletes a ON a.athlete_type = tm.athlete_type AND a.id = tm.athlete_ref_id
                    GROUP BY tm.team_id
                )
                SELECT
                    r.id,
                    r.event_id,
                    e.name AS event_name,
                    e.category,
                    e.event_type,
                    e.scoring_strategy,
                    e.gender AS event_gender,
                    e.age_group,
                    e.is_individual,
                    CASE WHEN r.athlete_ref_id IS NOT NULL THEN 'athlete' ELSE 'team' END AS result_type,
                    COALESCE(r.athlete_type, '') AS athlete_type,
                    COALESCE(r.athlete_ref_id, '') AS athlete_ref_id,
                    COALESCE(a.athlete_no, '') AS athlete_no,
                    COALESCE(a.name, '') AS athlete_name,
                    COALESCE(a.gender, '') AS athlete_gender,
                    COALESCE(r.team_id, '') AS team_id,
                    COALESCE(t.name, '') AS team_name,
                    COALESCE(ms.team_member_athlete_nos, '') AS team_member_athlete_nos,
                    COALESCE(ms.team_member_names, '') AS team_member_names,
                    COALESCE(ms.team_member_genders, '') AS team_member_genders,
                    CASE WHEN r.athlete_ref_id IS NOT NULL THEN d1.name ELSE d2.name END AS department_name,
                    r.rank,
                    r.points,
                    r.performance,
                    r.entered_by,
                    r.created_at
                FROM results r
                JOIN events e ON e.id = r.event_id
                LEFT JOIN athletes a ON a.athlete_type = r.athlete_type AND a.id = r.athlete_ref_id
                LEFT JOIN departments d1 ON d1.id = a.department_id
                LEFT JOIN teams t ON t.id = r.team_id
                LEFT JOIN departments d2 ON d2.id = t.department_id
                LEFT JOIN team_member_summary ms ON ms.team_id = t.id
                ORDER BY e.category ASC, e.gender ASC, e.age_group ASC, e.name ASC, r.rank ASC, r.id ASC
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
                        WHEN r.athlete_ref_id IS NOT NULL THEN a.name
                        ELSE t.name
                    END AS target_name,
                    r.rank,
                    r.points,
                    r.performance,
                    r.entered_by
                FROM results r
                JOIN events e ON e.id = r.event_id
                LEFT JOIN athletes a ON a.athlete_type = r.athlete_type AND a.id = r.athlete_ref_id
                LEFT JOIN teams t ON t.id = r.team_id
                ORDER BY r.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def page_results(
            self,
            page: int,
            page_size: int,
            keyword: str,
            department_name: str,
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
                where.append("(e.name LIKE ? OR COALESCE(a.name, t.name) LIKE ? OR r.entered_by LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
            if department_name:
                where.append("(d1.name = ? OR d2.name = ?)")
                params.extend([department_name, department_name])
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
                    "entered_by": "r.entered_by",
                    "created_at": "r.created_at",
                },
                "r.id DESC",
            )
            count_sql = f"""
                SELECT COUNT(*) AS c
                FROM results r
                JOIN events e ON e.id = r.event_id
                LEFT JOIN athletes a ON a.athlete_type = r.athlete_type AND a.id = r.athlete_ref_id
                LEFT JOIN departments d1 ON d1.id = a.department_id
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
                    CASE WHEN r.athlete_ref_id IS NOT NULL THEN a.name ELSE t.name END AS target_name,
                    CASE WHEN r.athlete_ref_id IS NOT NULL THEN d1.name ELSE d2.name END AS department_name,
                    r.rank,
                    r.points,
                    r.performance,
                    r.entered_by,
                    r.created_at
                FROM results r
                JOIN events e ON e.id = r.event_id
                LEFT JOIN athletes a ON a.athlete_type = r.athlete_type AND a.id = r.athlete_ref_id
                LEFT JOIN departments d1 ON d1.id = a.department_id
                LEFT JOIN teams t ON t.id = r.team_id
                LEFT JOIN departments d2 ON d2.id = t.department_id
                WHERE {where_sql}
                ORDER BY {order_sql}
            """
            return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)

    def page_result_details(
            self,
            page: int,
            page_size: int,
            keyword: str,
            department_name: str,
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
                where.append(
                    """
                    (
                        e.name LIKE ?
                        OR COALESCE(a.name, t.name) LIKE ?
                        OR COALESCE(a.athlete_no, '') LIKE ?
                        OR COALESCE(ms.team_member_athlete_nos, '') LIKE ?
                        OR COALESCE(ms.team_member_names, '') LIKE ?
                        OR r.entered_by LIKE ?
                    )
                    """
                )
                like = f"%{keyword}%"
                params.extend([like, like, like, like, like, like])
            if department_name:
                where.append("(d1.name = ? OR d2.name = ?)")
                params.extend([department_name, department_name])
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
                    "id": "r.id",
                    "event_id": "r.event_id",
                    "event_full_name": "e.name",
                    "event_name": "e.name",
                    "category": "e.category",
                    "event_type": "e.event_type",
                    "scoring_strategy": "e.scoring_strategy",
                    "event_gender": "e.gender",
                    "age_group": "e.age_group",
                    "is_individual": "e.is_individual",
                    "result_type": "result_type",
                    "athlete_type": "athlete_type",
                    "athlete_ref_id": "r.athlete_ref_id",
                    "athlete_no": "a.athlete_no",
                    "athlete_name": "a.name",
                    "athlete_gender": "a.gender",
                    "team_id": "r.team_id",
                    "team_name": "t.name",
                    "department_name": "department_name",
                    "rank": "r.rank",
                    "points": "r.points",
                    "performance": "r.performance",
                    "entered_by": "r.entered_by",
                    "created_at": "r.created_at",
                },
                "e.category ASC, e.gender ASC, e.age_group ASC, e.name ASC, r.rank ASC, r.id ASC",
            )
            base_from = f"""
                FROM results r
                JOIN events e ON e.id = r.event_id
                LEFT JOIN athletes a ON a.athlete_type = r.athlete_type AND a.id = r.athlete_ref_id
                LEFT JOIN departments d1 ON d1.id = a.department_id
                LEFT JOIN teams t ON t.id = r.team_id
                LEFT JOIN departments d2 ON d2.id = t.department_id
                LEFT JOIN (
                    SELECT
                        tm.team_id,
                        GROUP_CONCAT(a2.athlete_no, '; ') AS team_member_athlete_nos,
                        GROUP_CONCAT(a2.name, '; ') AS team_member_names,
                        GROUP_CONCAT(
                            CASE a2.gender
                                WHEN 'male' THEN '男'
                                WHEN 'female' THEN '女'
                                ELSE COALESCE(a2.gender, '')
                            END,
                            '; '
                        ) AS team_member_genders
                    FROM team_members tm
                    LEFT JOIN athletes a2 ON a2.athlete_type = tm.athlete_type AND a2.id = tm.athlete_ref_id
                    GROUP BY tm.team_id
                ) ms ON ms.team_id = t.id
                WHERE {where_sql}
            """
            count_sql = f"SELECT COUNT(*) AS c {base_from}"
            data_sql = f"""
                SELECT
                    r.id,
                    r.event_id,
                    e.name AS event_name,
                    e.category,
                    e.event_type,
                    e.scoring_strategy,
                    e.gender AS event_gender,
                    e.age_group,
                    e.is_individual,
                    CASE WHEN r.athlete_ref_id IS NOT NULL THEN 'athlete' ELSE 'team' END AS result_type,
                    COALESCE(r.athlete_type, '') AS athlete_type,
                    COALESCE(r.athlete_ref_id, '') AS athlete_ref_id,
                    COALESCE(a.athlete_no, '') AS athlete_no,
                    COALESCE(a.name, '') AS athlete_name,
                    COALESCE(a.gender, '') AS athlete_gender,
                    COALESCE(r.team_id, '') AS team_id,
                    COALESCE(t.name, '') AS team_name,
                    COALESCE(ms.team_member_athlete_nos, '') AS team_member_athlete_nos,
                    COALESCE(ms.team_member_names, '') AS team_member_names,
                    COALESCE(ms.team_member_genders, '') AS team_member_genders,
                    CASE WHEN r.athlete_ref_id IS NOT NULL THEN d1.name ELSE d2.name END AS department_name,
                    r.rank,
                    r.points,
                    r.performance,
                    r.entered_by,
                    r.created_at
                {base_from}
                ORDER BY {order_sql}
            """
            return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)
