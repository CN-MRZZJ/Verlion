import sqlite3
from typing import Optional


class SettingsRepositoryMixin:
    def set_meet_date(self, meet_date_iso: str) -> None:
            self.conn.execute(
                "INSERT INTO settings(key, value) VALUES('meet_date', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (meet_date_iso,),
            )

    def get_meet_date_iso(self) -> Optional[str]:
            row = self.conn.execute("SELECT value FROM settings WHERE key='meet_date'").fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
            self.conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def get_setting(self, key: str) -> Optional[str]:
            row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return row["value"] if row else None
