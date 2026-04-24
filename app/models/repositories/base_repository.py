import sqlite3
from typing import Optional

from .crud import ATHLETE_TABLES, CrudRepositoryMixin


class BaseRepositoryMixin(CrudRepositoryMixin):
    def __init__(self, conn: sqlite3.Connection) -> None:
            self.conn = conn

    def _athlete_table(self, athlete_type: str) -> str:
            return self._athlete_schema(athlete_type).name

    def _athlete_schema(self, athlete_type: str):
            if athlete_type not in ATHLETE_TABLES:
                raise ValueError("athlete_type 必须为 competitive 或 fun")
            return ATHLETE_TABLES[athlete_type]

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
