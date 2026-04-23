import sqlite3
from typing import Optional


class DepartmentRepositoryMixin:
    def insert_department(self, name: str, total_members: int) -> int:
            cur = self.conn.execute("INSERT INTO departments(name, total_members) VALUES(?,?)", (name, total_members))
            return int(cur.lastrowid)

    def get_department_by_name(self, name: str):
            return self.conn.execute("SELECT id, total_members FROM departments WHERE name=?", (name,)).fetchone()

    def update_department_total_members(self, department_id: int, total_members: int) -> None:
            self.conn.execute("UPDATE departments SET total_members=? WHERE id=?", (total_members, department_id))

    def departments_count(self) -> int:
            return int(self.conn.execute("SELECT COUNT(*) AS c FROM departments").fetchone()["c"])

    def list_departments(self):
            return self.conn.execute(
                """
                SELECT id, name, total_members
                FROM departments
                ORDER BY id
                """
            ).fetchall()
