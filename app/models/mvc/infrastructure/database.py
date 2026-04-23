import sqlite3
from contextlib import contextmanager
from typing import Iterator

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    total_members INTEGER NOT NULL CHECK(total_members >= 0)
);

CREATE TABLE IF NOT EXISTS competitive_athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_no TEXT UNIQUE,
    name TEXT NOT NULL,
    gender TEXT NOT NULL CHECK(gender IN ('male','female')),
    birth_date TEXT,
    department_id INTEGER NOT NULL,
    age_group TEXT CHECK(age_group IN ('A','B','C') OR age_group IS NULL),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS fun_athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_no TEXT UNIQUE,
    name TEXT NOT NULL,
    gender TEXT NOT NULL CHECK(gender IN ('male','female')),
    birth_date TEXT,
    department_id INTEGER NOT NULL,
    age_group TEXT CHECK(age_group IN ('A','B','C') OR age_group IS NULL),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('competitive','fun')),
    event_type TEXT NOT NULL CHECK(event_type IN ('track','field','fun')),
    scoring_strategy TEXT NOT NULL CHECK(scoring_strategy IN ('time','length','count','count_miss')),
    gender TEXT NOT NULL CHECK(gender IN ('male','female','mixed')),
    age_group TEXT NOT NULL CHECK(age_group IN ('A','B','C','ALL')),
    is_individual INTEGER NOT NULL CHECK(is_individual IN (0,1))
);

CREATE TABLE IF NOT EXISTS athlete_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_type TEXT NOT NULL CHECK(athlete_type IN ('competitive','fun')),
    athlete_ref_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(athlete_type, athlete_ref_id, event_id),
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(event_id, name),
    FOREIGN KEY(department_id) REFERENCES departments(id),
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    athlete_type TEXT NOT NULL CHECK(athlete_type IN ('competitive','fun')),
    athlete_ref_id INTEGER NOT NULL,
    UNIQUE(team_id, athlete_type, athlete_ref_id),
    FOREIGN KEY(team_id) REFERENCES teams(id)
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    athlete_type TEXT CHECK(athlete_type IN ('competitive','fun') OR athlete_type IS NULL),
    athlete_ref_id INTEGER,
    team_id INTEGER,
    rank INTEGER NOT NULL CHECK(rank >= 1),
    points INTEGER NOT NULL DEFAULT 0,
    performance TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(event_id) REFERENCES events(id),
    FOREIGN KEY(team_id) REFERENCES teams(id),
    CHECK(
        (athlete_ref_id IS NOT NULL AND athlete_type IS NOT NULL AND team_id IS NULL)
        OR
        (athlete_ref_id IS NULL AND athlete_type IS NULL AND team_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS event_progress (
    event_id INTEGER PRIMARY KEY,
    record_done INTEGER NOT NULL DEFAULT 0 CHECK(record_done IN (0,1)),
    print_done INTEGER NOT NULL DEFAULT 0 CHECK(print_done IN (0,1)),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(event_id) REFERENCES events(id)
);
"""


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
            conn.executescript(SCHEMA_SQL)
            self._migrate_events_structure(conn)
            self._migrate_split_athletes(conn)
            conn.commit()

    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        return row is not None

    def _table_columns(self, conn: sqlite3.Connection, table_name: str) -> set[str]:
        if not self._table_exists(conn, table_name):
            return set()
        return {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}

    def _copy_old_athlete_to_target(
        self,
        conn: sqlite3.Connection,
        old_athlete_id: int,
        target_type: str,
        old_cache: dict[int, sqlite3.Row],
        mapping: dict[tuple[str, int], int],
    ) -> int:
        key = (target_type, old_athlete_id)
        if key in mapping:
            return mapping[key]

        source = old_cache.get(old_athlete_id)
        if source is None:
            raise ValueError(f"旧运动员不存在: {old_athlete_id}")

        table = "competitive_athletes" if target_type == "competitive" else "fun_athletes"
        cur = conn.execute(
            f"""
            INSERT INTO {table}(athlete_no, name, gender, birth_date, department_id, age_group, created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                source["athlete_no"],
                source["name"],
                source["gender"],
                source["birth_date"],
                source["department_id"],
                source["age_group"],
                source["created_at"],
            ),
        )
        new_id = int(cur.lastrowid)
        mapping[key] = new_id
        return new_id

    def _migrate_split_athletes(self, conn: sqlite3.Connection) -> None:
        has_old_athletes = self._table_exists(conn, "athletes")
        reg_cols = self._table_columns(conn, "athlete_registrations")
        team_member_cols = self._table_columns(conn, "team_members")
        result_cols = self._table_columns(conn, "results")

        need_reg_rebuild = "athlete_ref_id" not in reg_cols and "athlete_id" in reg_cols
        need_team_member_rebuild = "athlete_ref_id" not in team_member_cols and "athlete_id" in team_member_cols
        need_result_rebuild = "athlete_ref_id" not in result_cols and "athlete_id" in result_cols

        if not has_old_athletes and not need_reg_rebuild and not need_team_member_rebuild and not need_result_rebuild:
            return

        conn.execute("PRAGMA foreign_keys = OFF;")
        try:
            old_rows = {}
            if has_old_athletes:
                for row in conn.execute("SELECT * FROM athletes").fetchall():
                    old_rows[int(row["id"])] = row

            mapping: dict[tuple[str, int], int] = {}

            if need_reg_rebuild:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS athlete_registrations_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        athlete_type TEXT NOT NULL CHECK(athlete_type IN ('competitive','fun')),
                        athlete_ref_id INTEGER NOT NULL,
                        event_id INTEGER NOT NULL,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        UNIQUE(athlete_type, athlete_ref_id, event_id),
                        FOREIGN KEY(event_id) REFERENCES events(id)
                    )
                    """
                )

                old_regs = conn.execute(
                    """
                    SELECT r.id, r.athlete_id, r.event_id, r.created_at, e.category
                    FROM athlete_registrations r
                    JOIN events e ON e.id = r.event_id
                    """
                ).fetchall()

                for row in old_regs:
                    athlete_type = "fun" if row["category"] == "fun" else "competitive"
                    new_ref_id = self._copy_old_athlete_to_target(
                        conn,
                        int(row["athlete_id"]),
                        athlete_type,
                        old_rows,
                        mapping,
                    )
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO athlete_registrations_new(id, athlete_type, athlete_ref_id, event_id, created_at)
                        VALUES(?,?,?,?,?)
                        """,
                        (row["id"], athlete_type, new_ref_id, row["event_id"], row["created_at"]),
                    )

                conn.execute("DROP TABLE athlete_registrations")
                conn.execute("ALTER TABLE athlete_registrations_new RENAME TO athlete_registrations")

            if need_team_member_rebuild:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS team_members_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team_id INTEGER NOT NULL,
                        athlete_type TEXT NOT NULL CHECK(athlete_type IN ('competitive','fun')),
                        athlete_ref_id INTEGER NOT NULL,
                        UNIQUE(team_id, athlete_type, athlete_ref_id),
                        FOREIGN KEY(team_id) REFERENCES teams(id)
                    )
                    """
                )

                old_members = conn.execute(
                    """
                    SELECT tm.id, tm.team_id, tm.athlete_id, e.category
                    FROM team_members tm
                    JOIN teams t ON t.id = tm.team_id
                    JOIN events e ON e.id = t.event_id
                    """
                ).fetchall()

                for row in old_members:
                    athlete_type = "fun" if row["category"] == "fun" else "competitive"
                    new_ref_id = self._copy_old_athlete_to_target(
                        conn,
                        int(row["athlete_id"]),
                        athlete_type,
                        old_rows,
                        mapping,
                    )
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO team_members_new(id, team_id, athlete_type, athlete_ref_id)
                        VALUES(?,?,?,?)
                        """,
                        (row["id"], row["team_id"], athlete_type, new_ref_id),
                    )

                conn.execute("DROP TABLE team_members")
                conn.execute("ALTER TABLE team_members_new RENAME TO team_members")

            if need_result_rebuild:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS results_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id INTEGER NOT NULL,
                        athlete_type TEXT CHECK(athlete_type IN ('competitive','fun') OR athlete_type IS NULL),
                        athlete_ref_id INTEGER,
                        team_id INTEGER,
                        rank INTEGER NOT NULL CHECK(rank >= 1),
                        points INTEGER NOT NULL DEFAULT 0,
                        performance TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        FOREIGN KEY(event_id) REFERENCES events(id),
                        FOREIGN KEY(team_id) REFERENCES teams(id),
                        CHECK(
                            (athlete_ref_id IS NOT NULL AND athlete_type IS NOT NULL AND team_id IS NULL)
                            OR
                            (athlete_ref_id IS NULL AND athlete_type IS NULL AND team_id IS NOT NULL)
                        )
                    )
                    """
                )

                old_results = conn.execute(
                    """
                    SELECT r.id, r.event_id, r.athlete_id, r.team_id, r.rank, r.points, r.performance, r.created_at, e.category
                    FROM results r
                    JOIN events e ON e.id = r.event_id
                    """
                ).fetchall()

                for row in old_results:
                    athlete_type = None
                    athlete_ref_id = None
                    if row["athlete_id"] is not None:
                        athlete_type = "fun" if row["category"] == "fun" else "competitive"
                        athlete_ref_id = self._copy_old_athlete_to_target(
                            conn,
                            int(row["athlete_id"]),
                            athlete_type,
                            old_rows,
                            mapping,
                        )
                    conn.execute(
                        """
                        INSERT INTO results_new(id, event_id, athlete_type, athlete_ref_id, team_id, rank, points, performance, created_at)
                        VALUES(?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            row["id"],
                            row["event_id"],
                            athlete_type,
                            athlete_ref_id,
                            row["team_id"],
                            row["rank"],
                            row["points"],
                            row["performance"],
                            row["created_at"],
                        ),
                    )

                conn.execute("DROP TABLE results")
                conn.execute("ALTER TABLE results_new RENAME TO results")

            if has_old_athletes:
                conn.execute("DROP TABLE athletes")
        finally:
            conn.execute("PRAGMA foreign_keys = ON;")

    def _migrate_events_structure(self, conn: sqlite3.Connection) -> None:
        table_sql_row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='events'"
        ).fetchone()
        if not table_sql_row:
            return
        table_sql = table_sql_row["sql"] or ""
        normalized_sql = "".join(table_sql.lower().split())
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
        needs_rebuild = False
        if "scoring_strategy" not in columns:
            needs_rebuild = True
        if "event_typetextnotnullcheck(event_typein('track','field','fun'))" not in normalized_sql:
            needs_rebuild = True
        legacy_tokens = ["'relay'", "'accuracy'", "'power'", "'fitness'", "'team_fun'"]
        if any(tok in table_sql.lower() for tok in legacy_tokens):
            needs_rebuild = True
        if "'all'" not in table_sql.lower():
            needs_rebuild = True
        if "'count_miss'" not in table_sql.lower():
            needs_rebuild = True
        if not needs_rebuild:
            return

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
                age_group TEXT NOT NULL CHECK(age_group IN ('A','B','C','ALL')),
                is_individual INTEGER NOT NULL CHECK(is_individual IN (0,1))
            );
            """
        )
        conn.execute(
            """
            INSERT INTO events_new(id, name, category, event_type, scoring_strategy, gender, age_group, is_individual)
            SELECT
                id,
                name,
                category,
                CASE
                    WHEN event_type IN ('track','relay') THEN 'track'
                    WHEN event_type='field' THEN 'field'
                    ELSE 'fun'
                END,
                CASE
                    WHEN event_type IN ('track','relay') THEN 'time'
                    WHEN event_type='field' THEN 'length'
                    ELSE 'count'
                END,
                gender,
                CASE
                    WHEN event_type='relay' OR category='fun' OR is_individual=0 THEN 'ALL'
                    ELSE age_group
                END,
                is_individual
            FROM events
            """
        )
        conn.execute("DROP TABLE events")
        conn.execute("ALTER TABLE events_new RENAME TO events")
        conn.execute("PRAGMA foreign_keys = ON;")
