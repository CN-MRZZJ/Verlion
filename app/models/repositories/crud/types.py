from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class WhereClause:
    sql: str
    params: tuple[Any, ...] = ()


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: tuple[str, ...]
    primary_key: str = "id"
    insert_columns: tuple[str, ...] = ()
    update_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        all_columns = set(self.columns)
        if self.primary_key not in all_columns:
            raise ValueError(f"{self.name} 缺少主键字段: {self.primary_key}")

        insert_columns = self.insert_columns or tuple(c for c in self.columns if c != self.primary_key)
        update_columns = self.update_columns or tuple(c for c in insert_columns if c != self.primary_key)
        object.__setattr__(self, "insert_columns", insert_columns)
        object.__setattr__(self, "update_columns", update_columns)
        self.require_columns(insert_columns)
        self.require_columns(update_columns)

    def require_columns(self, columns: Iterable[str]) -> None:
        invalid = set(columns) - set(self.columns)
        if invalid:
            raise ValueError(f"{self.name} 包含未知字段: {', '.join(sorted(invalid))}")

    def writable_insert_values(self, values: Mapping[str, Any]) -> dict[str, Any]:
        return self._filter_values(values, self.insert_columns)

    def writable_update_values(self, values: Mapping[str, Any]) -> dict[str, Any]:
        return self._filter_values(values, self.update_columns)

    def _filter_values(self, values: Mapping[str, Any], allowed: tuple[str, ...]) -> dict[str, Any]:
        self.require_columns(values.keys())
        return {key: values[key] for key in allowed if key in values}
