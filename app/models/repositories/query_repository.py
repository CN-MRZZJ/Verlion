import sqlite3
from typing import Optional


class QueryRepositoryMixin:
    def page_athletes(
            self,
            page: int,
            page_size: int,
            keyword: str,
            department_name: str,
            gender: str,
            group: str,
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
            if group:
                where.append('u."group" = ?')
                params.append(group)
            where_sql = " AND ".join(where)

            athlete_sql = """
                SELECT
                    a.athlete_type,
                    a.id AS athlete_ref_id,
                    a.athlete_no,
                    a.name,
                    a.gender,
                    a."group",
                    d.name AS department_name
                FROM athletes a
                JOIN departments d ON d.id = a.department_id
            """

            count_sql = f"SELECT COUNT(*) AS c FROM ({athlete_sql}) u WHERE {where_sql}"
            order_sql = self._resolve_order(
                sort_by,
                sort_dir,
                {
                    "athlete_type": "u.athlete_type",
                    "athlete_ref_id": "u.athlete_ref_id",
                    "athlete_no": "u.athlete_no",
                    "name": "u.name",
                    "gender": "u.gender",
                    "group": 'u."group"',
                    "department_name": "u.department_name",
                },
                "u.athlete_type ASC, u.athlete_ref_id DESC",
            )
            data_sql = f"""
                SELECT u.athlete_type, u.athlete_ref_id, u.athlete_no, u.name, u.gender, u."group", u.department_name
                FROM ({athlete_sql}) u
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
