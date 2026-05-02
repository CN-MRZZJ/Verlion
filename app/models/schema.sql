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

CREATE TABLE IF NOT EXISTS athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_type TEXT NOT NULL CHECK(athlete_type IN ('competitive','fun')),
    athlete_no TEXT,
    name TEXT NOT NULL,
    gender TEXT NOT NULL CHECK(gender IN ('male','female')),
    birth_date TEXT,
    department_id INTEGER NOT NULL,
    age_group TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(athlete_type, athlete_no),
    FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('competitive','fun')),
    event_type TEXT NOT NULL CHECK(event_type IN ('track','field','fun')),
    scoring_strategy TEXT NOT NULL CHECK(scoring_strategy IN ('time','length','count','count_miss')),
    gender TEXT NOT NULL CHECK(gender IN ('male','female','mixed')),
    age_group TEXT NOT NULL,
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
    entered_by TEXT NOT NULL DEFAULT '',
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
