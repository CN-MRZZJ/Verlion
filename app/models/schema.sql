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
    "group" TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
    UNIQUE(athlete_type, athlete_no),
    FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('competitive','fun')),
    event_type TEXT NOT NULL,
    scoring_strategy TEXT NOT NULL CHECK(scoring_strategy IN ('time','length','count','count_miss')),
    gender TEXT NOT NULL CHECK(gender IN ('male','female','mixed')),
    "group" TEXT NOT NULL,
    is_individual INTEGER NOT NULL CHECK(is_individual IN (0,1)),
    competition_format TEXT NOT NULL CHECK(competition_format IN ('heats','knockout','round_robin')) DEFAULT 'heats'
);

CREATE TABLE IF NOT EXISTS heats_config (
    event_id INTEGER PRIMARY KEY,
    heat_rounds INTEGER NOT NULL DEFAULT 1 CHECK(heat_rounds BETWEEN 1 AND 4),
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS athlete_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_type TEXT NOT NULL CHECK(athlete_type IN ('competitive','fun')),
    athlete_ref_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
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
    round_id INTEGER NOT NULL DEFAULT 1,
    athlete_type TEXT CHECK(athlete_type IN ('competitive','fun') OR athlete_type IS NULL),
    athlete_ref_id INTEGER,
    team_id INTEGER,
    rank INTEGER NOT NULL CHECK(rank >= 1),
    points INTEGER NOT NULL DEFAULT 0,
    performance TEXT,
    entered_by TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
    FOREIGN KEY(event_id) REFERENCES events(id),
    FOREIGN KEY(team_id) REFERENCES teams(id),
    CHECK(
        (athlete_ref_id IS NOT NULL AND athlete_type IS NOT NULL AND team_id IS NULL)
        OR
        (athlete_ref_id IS NULL AND athlete_type IS NULL AND team_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    round_id INTEGER NOT NULL DEFAULT 1,
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
);

CREATE TABLE IF NOT EXISTS event_types (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    scoring_strategy TEXT NOT NULL CHECK(scoring_strategy IN ('time','length','count','count_miss')),
    competition_format TEXT NOT NULL DEFAULT 'heats' CHECK(competition_format IN ('heats','knockout','round_robin'))
);

CREATE TABLE IF NOT EXISTS point_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_type TEXT NOT NULL CHECK(result_type IN ('individual','team')),
    rank INTEGER NOT NULL CHECK(rank >= 1),
    points INTEGER NOT NULL CHECK(points >= 0),
    UNIQUE(result_type, rank)
);

CREATE TABLE IF NOT EXISTS group_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL CHECK(scope IN ('athlete','event')),
    value TEXT NOT NULL,
    label TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE(scope, value)
);

CREATE TABLE IF NOT EXISTS event_progress (
    event_id INTEGER PRIMARY KEY,
    checkin_done INTEGER NOT NULL DEFAULT 0 CHECK(checkin_done IN (0,1)),
    competition_done INTEGER NOT NULL DEFAULT 0 CHECK(competition_done IN (0,1)),
    record_done INTEGER NOT NULL DEFAULT 0 CHECK(record_done IN (0,1)),
    publish_done INTEGER NOT NULL DEFAULT 0 CHECK(publish_done IN (0,1)),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    round_name TEXT NOT NULL,
    advancement_rule TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+08:00')),
    UNIQUE(event_id, round_number),
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS heats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL,
    heat_number INTEGER NOT NULL,
    heat_name TEXT NOT NULL,
    UNIQUE(round_id, heat_number),
    FOREIGN KEY(round_id) REFERENCES rounds(id)
);

CREATE TABLE IF NOT EXISTS heat_entries (
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
);
