import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def load_schema_sql() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(load_schema_sql())
            self._migrate_split_athlete_tables(conn)
            self._migrate_age_group_constraints(conn)
            self._migrate_results_entered_by(conn)
            self._migrate_attempts_table(conn)
            self._migrate_event_progress_columns(conn)
            conn.commit()

    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        return row is not None

    def _table_sql(self, conn: sqlite3.Connection, table_name: str) -> str:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        return str(row["sql"] or "") if row else ""

    def _table_columns(self, conn: sqlite3.Connection, table_name: str) -> set[str]:
        return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}

    def _migrate_results_entered_by(self, conn: sqlite3.Connection) -> None:
        if self._table_exists(conn, "results") and "entered_by" not in self._table_columns(conn, "results"):
            conn.execute("ALTER TABLE results ADD COLUMN entered_by TEXT NOT NULL DEFAULT ''")

    def _migrate_attempts_table(self, conn: sqlite3.Connection) -> None:
        if not self._table_exists(conn, "attempts"):
            conn.execute("""
                CREATE TABLE attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    athlete_type TEXT CHECK(athlete_type IN ('competitive','fun') OR athlete_type IS NULL),
                    athlete_ref_id INTEGER,
                    team_id INTEGER,
                    attempt_number INTEGER NOT NULL DEFAULT 1,
                    rank INTEGER NOT NULL CHECK(rank >= 1),
                    performance TEXT,
                    is_void INTEGER NOT NULL DEFAULT 0 CHECK(is_void IN (0,1)),
                    entered_by TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
                    FOREIGN KEY(event_id) REFERENCES events(id),
                    FOREIGN KEY(team_id) REFERENCES teams(id),
                    CHECK(
                        (athlete_ref_id IS NOT NULL AND athlete_type IS NOT NULL AND team_id IS NULL)
                        OR
                        (athlete_ref_id IS NULL AND athlete_type IS NULL AND team_id IS NOT NULL)
                    )
                )
            """)
            return
        existing = self._table_columns(conn, "attempts")
        if "attempt_number" not in existing:
            conn.execute("ALTER TABLE attempts ADD COLUMN attempt_number INTEGER NOT NULL DEFAULT 1")
        if "is_void" not in existing:
            conn.execute("ALTER TABLE attempts ADD COLUMN is_void INTEGER NOT NULL DEFAULT 0 CHECK(is_void IN (0,1))")

    def _migrate_age_group_constraints(self, conn: sqlite3.Connection) -> None:
        if self._table_exists(conn, "athletes") and "age_group IN ('A','B','C')" in self._table_sql(conn, "athletes"):
            self._rebuild_athletes_without_age_group_check(conn)
        if self._table_exists(conn, "events") and "age_group IN ('A','B','C','ALL')" in self._table_sql(conn, "events"):
            self._rebuild_events_without_age_group_check(conn)

    def _rebuild_athletes_without_age_group_check(self, conn: sqlite3.Connection) -> None:
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS athletes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                athlete_type TEXT NOT NULL CHECK(athlete_type IN ('competitive','fun')),
                athlete_no TEXT,
                name TEXT NOT NULL,
                gender TEXT NOT NULL CHECK(gender IN ('male','female')),
                birth_date TEXT,
                department_id INTEGER NOT NULL,
                age_group TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
                UNIQUE(athlete_type, athlete_no),
                FOREIGN KEY(department_id) REFERENCES departments(id)
            )
            """
        )
        conn.execute(
            """
            INSERT INTO athletes_new(id, athlete_type, athlete_no, name, gender, birth_date, department_id, age_group, created_at)
            SELECT id, athlete_type, athlete_no, name, gender, birth_date, department_id, age_group, created_at
            FROM athletes
            """
        )
        conn.execute("DROP TABLE athletes")
        conn.execute("ALTER TABLE athletes_new RENAME TO athletes")
        conn.execute("PRAGMA foreign_keys = ON;")

    def _rebuild_events_without_age_group_check(self, conn: sqlite3.Connection) -> None:
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL CHECK(category IN ('competitive','fun')),
                event_type TEXT NOT NULL CHECK(event_type IN ('track','field','fun')),
                scoring_strategy TEXT NOT NULL CHECK(scoring_strategy IN ('time','length','count','count_miss')),
                gender TEXT NOT NULL CHECK(gender IN ('male','female','mixed')),
                age_group TEXT NOT NULL,
                is_individual INTEGER NOT NULL CHECK(is_individual IN (0,1))
            )
            """
        )
        conn.execute(
            """
            INSERT INTO events_new(id, name, category, event_type, scoring_strategy, gender, age_group, is_individual)
            SELECT id, name, category, event_type, scoring_strategy, gender, age_group, is_individual
            FROM events
            """
        )
        conn.execute("DROP TABLE events")
        conn.execute("ALTER TABLE events_new RENAME TO events")
        conn.execute("PRAGMA foreign_keys = ON;")

    def _migrate_split_athlete_tables(self, conn: sqlite3.Connection) -> None:
        old_tables = [
            ("competitive", "competitive_athletes"),
            ("fun", "fun_athletes"),
        ]
        existing_old_tables = [(athlete_type, table) for athlete_type, table in old_tables if self._table_exists(conn, table)]
        if not existing_old_tables:
            return

        mappings: dict[tuple[str, int], int] = {}
        for athlete_type, table in existing_old_tables:
            rows = conn.execute(
                f"""
                SELECT id, athlete_no, name, gender, birth_date, department_id, age_group, created_at
                FROM {table}
                ORDER BY id
                """
            ).fetchall()
            for row in rows:
                existing = None
                if row["athlete_no"]:
                    existing = conn.execute(
                        "SELECT id FROM athletes WHERE athlete_type=? AND athlete_no=?",
                        (athlete_type, row["athlete_no"]),
                    ).fetchone()
                if existing:
                    new_id = int(existing["id"])
                else:
                    cur = conn.execute(
                        """
                        INSERT INTO athletes(
                            athlete_type,
                            athlete_no,
                            name,
                            gender,
                            birth_date,
                            department_id,
                            age_group,
                            created_at
                        )
                        VALUES(?,?,?,?,?,?,?,?)
                        """,
                        (
                            athlete_type,
                            row["athlete_no"],
                            row["name"],
                            row["gender"],
                            row["birth_date"],
                            row["department_id"],
                            row["age_group"],
                            row["created_at"],
                        ),
                    )
                    new_id = int(cur.lastrowid)
                mappings[(athlete_type, int(row["id"]))] = new_id

        for (athlete_type, old_id), new_id in mappings.items():
            for table in ("athlete_registrations", "team_members", "results"):
                conn.execute(
                    f"""
                    UPDATE {table}
                    SET athlete_ref_id=?
                    WHERE athlete_type=? AND athlete_ref_id=?
                    """,
                    (new_id, athlete_type, old_id),
                )

        for _, table in existing_old_tables:
            conn.execute(f"DROP TABLE {table}")

    def _migrate_event_progress_columns(self, conn: sqlite3.Connection) -> None:
        """Rename print_done→publish_done and add checkin_done, competition_done."""
        if not self._table_exists(conn, "event_progress"):
            return
        existing = self._table_columns(conn, "event_progress")
        if "checkin_done" in existing and "competition_done" in existing and "publish_done" in existing:
            return
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS event_progress_new (
                event_id INTEGER PRIMARY KEY,
                checkin_done INTEGER NOT NULL DEFAULT 0 CHECK(checkin_done IN (0,1)),
                competition_done INTEGER NOT NULL DEFAULT 0 CHECK(competition_done IN (0,1)),
                record_done INTEGER NOT NULL DEFAULT 0 CHECK(record_done IN (0,1)),
                publish_done INTEGER NOT NULL DEFAULT 0 CHECK(publish_done IN (0,1)),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
                FOREIGN KEY(event_id) REFERENCES events(id)
            )
            """
        )
        conn.execute(
            """
            INSERT INTO event_progress_new(event_id, checkin_done, competition_done, record_done, publish_done, updated_at)
            SELECT event_id, 0, 0, record_done, print_done, updated_at
            FROM event_progress
            """
        )
        conn.execute("DROP TABLE event_progress")
        conn.execute("ALTER TABLE event_progress_new RENAME TO event_progress")
        conn.execute("PRAGMA foreign_keys = ON;")
