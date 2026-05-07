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
            self._migrate_rules_tables(conn)
            self._migrate_group_rename(conn)
            self._migrate_event_type_check(conn)
            self._migrate_heats_tables(conn)
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

    def _migrate_rules_tables(self, conn: sqlite3.Connection) -> None:
        """Create rules config tables and seed from sports_rules.json if empty."""
        if not self._table_exists(conn, "event_types"):
            conn.execute("""
                CREATE TABLE event_types (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    scoring_strategy TEXT NOT NULL CHECK(scoring_strategy IN ('time','length','count','count_miss'))
                )
            """)
        if not self._table_exists(conn, "point_rules"):
            conn.execute("""
                CREATE TABLE point_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_type TEXT NOT NULL CHECK(result_type IN ('individual','team')),
                    rank INTEGER NOT NULL CHECK(rank >= 1),
                    points INTEGER NOT NULL CHECK(points >= 0),
                    UNIQUE(result_type, rank)
                )
            """)
        if not self._table_exists(conn, "group_options"):
            conn.execute("""
                CREATE TABLE group_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope TEXT NOT NULL CHECK(scope IN ('athlete','event')),
                    value TEXT NOT NULL,
                    label TEXT NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(scope, value)
                )
            """)
        self._seed_rules_from_json(conn)

    def _migrate_group_rename(self, conn: sqlite3.Connection) -> None:
        """Rename age_group → group in tables and columns."""
        if self._table_exists(conn, "age_group_options") and not self._table_exists(conn, "group_options"):
            conn.execute("ALTER TABLE age_group_options RENAME TO group_options")

        if self._table_exists(conn, "athletes"):
            cols = self._table_columns(conn, "athletes")
            if "age_group" in cols:
                conn.execute('ALTER TABLE athletes RENAME COLUMN age_group TO "group"')

        if self._table_exists(conn, "events"):
            cols = self._table_columns(conn, "events")
            if "age_group" in cols:
                conn.execute('ALTER TABLE events RENAME COLUMN age_group TO "group"')

    def _migrate_event_type_check(self, conn: sqlite3.Connection) -> None:
        """Remove hardcoded CHECK on event_type, now managed via event_types table."""
        if self._table_exists(conn, "events") and "event_type IN ('track','field','fun')" in self._table_sql(conn, "events"):
            conn.execute("PRAGMA foreign_keys = OFF;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL CHECK(category IN ('competitive','fun')),
                    event_type TEXT NOT NULL,
                    scoring_strategy TEXT NOT NULL CHECK(scoring_strategy IN ('time','length','count','count_miss')),
                    gender TEXT NOT NULL CHECK(gender IN ('male','female','mixed')),
                    "group" TEXT NOT NULL,
                    is_individual INTEGER NOT NULL CHECK(is_individual IN (0,1))
                )
                """
            )
            conn.execute(
                """
                INSERT INTO events_new(id, name, category, event_type, scoring_strategy, gender, "group", is_individual)
                SELECT id, name, category, event_type, scoring_strategy, gender, "group", is_individual
                FROM events
                """
            )
            conn.execute("DROP TABLE events")
            conn.execute("ALTER TABLE events_new RENAME TO events")
            conn.execute("PRAGMA foreign_keys = ON;")

    def _seed_rules_from_json(self, conn: sqlite3.Connection) -> None:
        """One-time seed from sports_rules.json into new tables if empty."""
        import json

        json_path = Path(__file__).resolve().parent.parent.parent / "sports_rules.json"
        if not json_path.exists():
            return

        with json_path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        count = conn.execute("SELECT COUNT(*) AS c FROM event_types").fetchone()["c"]
        if count == 0:
            name_map = {"track": "径赛", "field": "田赛", "fun": "趣味"}
            for code, strategy in config.get("event_scoring_strategy", {}).items():
                if str(code).startswith("_"):
                    continue
                conn.execute(
                    "INSERT INTO event_types(code, name, scoring_strategy) VALUES(?,?,?)",
                    (code, name_map.get(code, code), strategy),
                )

        count = conn.execute("SELECT COUNT(*) AS c FROM point_rules").fetchone()["c"]
        if count == 0:
            point_rule = config.get("point_rule", {})
            for result_type in ("individual", "team"):
                rules = point_rule.get(result_type, {})
                for rank, points in rules.items():
                    if str(rank).startswith("_"):
                        continue
                    conn.execute(
                        "INSERT INTO point_rules(result_type, rank, points) VALUES(?,?,?)",
                        (result_type, int(rank), int(points)),
                    )

        count = conn.execute("SELECT COUNT(*) AS c FROM group_options").fetchone()["c"]
        if count == 0:
            groups = config.get("age_group_options") or config.get("group_options", {})
            for scope in ("athlete", "event"):
                for sort_idx, item in enumerate(groups.get(scope, [])):
                    if not isinstance(item, dict):
                        continue
                    conn.execute(
                        "INSERT INTO group_options(scope, value, label, sort_order) VALUES(?,?,?,?)",
                        (scope, item.get("value", ""), item.get("label", ""), sort_idx),
                    )

        for key, default in [
            ("rule.attempt_policy", "best"),
            ("rule.team_event_default", "ALL"),
        ]:
            existing = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            if not existing:
                if key == "rule.attempt_policy":
                    val = str(config.get("attempt_policy", default)).strip()
                else:
                    groups = config.get("group_options") or config.get("age_group_options", {})
                    val = str(groups.get("team_event_default", default)).strip()
                conn.execute("INSERT INTO settings(key, value) VALUES(?,?)", (key, val))

    def _migrate_heats_tables(self, conn: sqlite3.Connection) -> None:
        if not self._table_exists(conn, "rounds"):
            conn.execute("""
                CREATE TABLE rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    round_number INTEGER NOT NULL,
                    round_name TEXT NOT NULL,
                    advancement_rule TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
                    UNIQUE(event_id, round_number),
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )
            """)
        if not self._table_exists(conn, "heats"):
            conn.execute("""
                CREATE TABLE heats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_id INTEGER NOT NULL,
                    heat_number INTEGER NOT NULL,
                    heat_name TEXT NOT NULL,
                    UNIQUE(round_id, heat_number),
                    FOREIGN KEY(round_id) REFERENCES rounds(id)
                )
            """)
        if not self._table_exists(conn, "heat_entries"):
            conn.execute("""
                CREATE TABLE heat_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    heat_id INTEGER NOT NULL,
                    athlete_type TEXT CHECK(athlete_type IN ('competitive','fun') OR athlete_type IS NULL),
                    athlete_ref_id INTEGER,
                    team_id INTEGER,
                    lane INTEGER,
                    FOREIGN KEY(heat_id) REFERENCES heats(id),
                    CHECK(
                        (athlete_ref_id IS NOT NULL AND athlete_type IS NOT NULL AND team_id IS NULL)
                        OR
                        (athlete_ref_id IS NULL AND athlete_type IS NULL AND team_id IS NOT NULL)
                    )
                )
            """)
        elif "UNIQUE(heat_id, lane)" in self._table_sql(conn, "heat_entries"):
            conn.execute("PRAGMA foreign_keys = OFF;")
            conn.execute("""
                CREATE TABLE heat_entries_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    heat_id INTEGER NOT NULL,
                    athlete_type TEXT CHECK(athlete_type IN ('competitive','fun') OR athlete_type IS NULL),
                    athlete_ref_id INTEGER,
                    team_id INTEGER,
                    lane INTEGER,
                    FOREIGN KEY(heat_id) REFERENCES heats(id),
                    CHECK(
                        (athlete_ref_id IS NOT NULL AND athlete_type IS NOT NULL AND team_id IS NULL)
                        OR
                        (athlete_ref_id IS NULL AND athlete_type IS NULL AND team_id IS NOT NULL)
                    )
                )
            """)
            conn.execute("""
                INSERT INTO heat_entries_new(id, heat_id, athlete_type, athlete_ref_id, team_id, lane)
                SELECT id, heat_id, athlete_type, athlete_ref_id, team_id, lane
                FROM heat_entries
            """)
            conn.execute("DROP TABLE heat_entries")
            conn.execute("ALTER TABLE heat_entries_new RENAME TO heat_entries")
            conn.execute("PRAGMA foreign_keys = ON;")
