from typing import Any, Mapping, Sequence

from .types import TableSchema, WhereClause


class CrudRepositoryMixin:
    def _crud_insert(self, schema: TableSchema, values: Mapping[str, Any]) -> int:
        payload = schema.writable_insert_values(values)
        if not payload:
            raise ValueError(f"{schema.name} 没有可插入字段")

        columns = tuple(payload.keys())
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(columns)
        cur = self.conn.execute(
            f"INSERT INTO {schema.name}({column_sql}) VALUES({placeholders})",
            tuple(payload[column] for column in columns),
        )
        return int(cur.lastrowid)

    def _crud_upsert(
        self,
        schema: TableSchema,
        values: Mapping[str, Any],
        conflict_columns: Sequence[str],
        update_columns: Sequence[str] | None = None,
    ) -> int:
        payload = schema.writable_insert_values(values)
        schema.require_columns(conflict_columns)
        if update_columns is None:
            update_columns = tuple(column for column in payload if column not in conflict_columns)
        schema.require_columns(update_columns)
        if not payload or not update_columns:
            raise ValueError(f"{schema.name} 没有可 upsert 字段")

        columns = tuple(payload.keys())
        column_sql = ", ".join(columns)
        placeholders = ", ".join("?" for _ in columns)
        conflict_sql = ", ".join(conflict_columns)
        update_sql = ", ".join(f"{column}=excluded.{column}" for column in update_columns)
        cur = self.conn.execute(
            f"""
            INSERT INTO {schema.name}({column_sql}) VALUES({placeholders})
            ON CONFLICT({conflict_sql}) DO UPDATE SET {update_sql}
            """,
            tuple(payload[column] for column in columns),
        )
        return int(cur.lastrowid or 0)

    def _crud_get_by_id(self, schema: TableSchema, row_id: Any, columns: Sequence[str] | str = "*"):
        select_sql = self._select_columns(schema, columns)
        return self.conn.execute(
            f"SELECT {select_sql} FROM {schema.name} WHERE {schema.primary_key}=?",
            (row_id,),
        ).fetchone()

    def _crud_get_one(
        self,
        schema: TableSchema,
        where: WhereClause,
        columns: Sequence[str] | str = "*",
        order_by: str = "",
    ):
        select_sql = self._select_columns(schema, columns)
        order_sql = f" ORDER BY {order_by}" if order_by else ""
        return self.conn.execute(
            f"SELECT {select_sql} FROM {schema.name} WHERE {where.sql}{order_sql} LIMIT 1",
            where.params,
        ).fetchone()

    def _crud_list(
        self,
        schema: TableSchema,
        columns: Sequence[str] | str = "*",
        where: WhereClause | None = None,
        order_by: str = "",
    ):
        select_sql = self._select_columns(schema, columns)
        where_sql = f" WHERE {where.sql}" if where else ""
        order_sql = f" ORDER BY {order_by}" if order_by else ""
        params = where.params if where else ()
        return self.conn.execute(f"SELECT {select_sql} FROM {schema.name}{where_sql}{order_sql}", params).fetchall()

    def _crud_update_by_id(self, schema: TableSchema, row_id: Any, values: Mapping[str, Any]) -> int:
        return self._crud_update_where(schema, values, WhereClause(f"{schema.primary_key}=?", (row_id,)))

    def _crud_update_where(self, schema: TableSchema, values: Mapping[str, Any], where: WhereClause) -> int:
        payload = schema.writable_update_values(values)
        if not payload:
            raise ValueError(f"{schema.name} 没有可更新字段")

        columns = tuple(payload.keys())
        set_sql = ", ".join(f"{column}=?" for column in columns)
        cur = self.conn.execute(
            f"UPDATE {schema.name} SET {set_sql} WHERE {where.sql}",
            tuple(payload[column] for column in columns) + where.params,
        )
        return int(cur.rowcount or 0)

    def _crud_delete_by_id(self, schema: TableSchema, row_id: Any) -> int:
        return self._crud_delete_where(schema, WhereClause(f"{schema.primary_key}=?", (row_id,)))

    def _crud_delete_where(self, schema: TableSchema, where: WhereClause) -> int:
        cur = self.conn.execute(f"DELETE FROM {schema.name} WHERE {where.sql}", where.params)
        return int(cur.rowcount or 0)

    def _crud_exists(self, schema: TableSchema, where: WhereClause) -> bool:
        return self._crud_get_one(schema, where, columns=(schema.primary_key,)) is not None

    def _crud_count(self, schema: TableSchema, where: WhereClause | None = None) -> int:
        where_sql = f" WHERE {where.sql}" if where else ""
        params = where.params if where else ()
        row = self.conn.execute(f"SELECT COUNT(*) AS c FROM {schema.name}{where_sql}", params).fetchone()
        return int(row["c"])

    def _select_columns(self, schema: TableSchema, columns: Sequence[str] | str) -> str:
        if columns == "*":
            return "*"
        schema.require_columns(columns)
        return ", ".join(columns)
