import sqlite3
from typing import Optional


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
        ) -> int:
            cur = self.conn.execute(
                "INSERT INTO results(event_id, athlete_type, athlete_ref_id, team_id, rank, points, performance) VALUES(?,?,?,?,?,?,?)",
                (event_id, athlete_type, athlete_ref_id, team_id, rank, points, performance),
            )
            return int(cur.lastrowid)

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
                    SELECT id, rank, points, performance
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
                    SELECT id, rank, points, performance
                    FROM results
                    WHERE event_id=? AND team_id=? AND athlete_ref_id IS NULL AND athlete_type IS NULL
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (event_id, team_id),
                ).fetchone()

            return None

    def update_result(self, result_id: int, rank: int, points: int, performance: Optional[str]) -> None:
            self.conn.execute(
                """
                UPDATE results
                SET rank=?, points=?, performance=?
                WHERE id=?
                """,
                (rank, points, performance, result_id),
            )

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

    def list_individual_results_for_event_all(self, event_id: int):
            return self.conn.execute(
                """
                SELECT
                    r.id,
                    r.rank,
                    COALESCE(ca.name, fa.name) AS athlete_name,
                    COALESCE(d1.name, '') AS department_name,
                    r.performance
                FROM results r
                LEFT JOIN competitive_athletes ca ON r.athlete_type='competitive' AND ca.id = r.athlete_ref_id
                LEFT JOIN fun_athletes fa ON r.athlete_type='fun' AND fa.id = r.athlete_ref_id
                LEFT JOIN departments d1 ON d1.id = COALESCE(ca.department_id, fa.department_id)
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
            self.conn.execute(
                "UPDATE results SET rank=?, points=? WHERE id=?",
                (rank, points, result_id),
            )

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
                where.append("(e.name LIKE ? OR COALESCE(ca.name, fa.name, t.name) LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
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
