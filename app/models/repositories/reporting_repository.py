import sqlite3
from typing import Optional


class ReportingRepositoryMixin:
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

    def page_standings(self, page: int, page_size: int, keyword: str = "", sort_by: str = "", sort_dir: str = "desc"):
            where = ["1=1"]
            params: list = []
            if keyword:
                where.append("d.name LIKE ?")
                params.append(f"%{keyword}%")
            where_sql = " AND ".join(where)
            count_sql = f"SELECT COUNT(*) AS c FROM departments d WHERE {where_sql}"
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
                WHERE """ + where_sql + """
                ORDER BY """ + order_sql + """
            """
            return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)

    def page_participation(self, page: int, page_size: int, keyword: str = "", sort_by: str = "", sort_dir: str = "desc"):
            where = ["1=1"]
            params: list = []
            if keyword:
                where.append("d.name LIKE ?")
                params.append(f"%{keyword}%")
            where_sql = " AND ".join(where)
            count_sql = f"SELECT COUNT(*) AS c FROM departments d WHERE {where_sql}"
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
                WHERE """ + where_sql + """
                GROUP BY d.id, d.name, d.total_members
                ORDER BY """ + order_sql + """
            """
            return self._paged_query(count_sql, data_sql, tuple(params), page, page_size)
