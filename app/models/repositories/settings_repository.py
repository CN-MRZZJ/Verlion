import sqlite3
from typing import Optional

from .crud import SETTINGS, WhereClause


class SettingsRepositoryMixin:
    def set_meet_date(self, meet_date_iso: str) -> None:
            self.set_setting("meet_date", meet_date_iso)

    def get_meet_date_iso(self) -> Optional[str]:
            return self.get_setting("meet_date")

    def set_setting(self, key: str, value: str) -> None:
            self._crud_upsert(SETTINGS, {"key": key, "value": value}, conflict_columns=("key",), update_columns=("value",))

    def get_setting(self, key: str) -> Optional[str]:
            row = self._crud_get_one(SETTINGS, WhereClause("key=?", (key,)), columns=("value",))
            return row["value"] if row else None
