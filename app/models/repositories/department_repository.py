import sqlite3
from typing import Optional

from .crud import DEPARTMENTS, WhereClause


class DepartmentRepositoryMixin:
    def insert_department(self, name: str, total_members: int) -> int:
            return self._crud_insert(DEPARTMENTS, {"name": name, "total_members": total_members})

    def get_department_by_name(self, name: str):
            return self._crud_get_one(DEPARTMENTS, WhereClause("name=?", (name,)), columns=("id", "total_members"))

    def update_department_total_members(self, department_id: int, total_members: int) -> None:
            self._crud_update_by_id(DEPARTMENTS, department_id, {"total_members": total_members})

    def departments_count(self) -> int:
            return self._crud_count(DEPARTMENTS)

    def list_departments(self):
            return self._crud_list(DEPARTMENTS, columns=("id", "name", "total_members"), order_by="id")
