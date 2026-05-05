from .types import TableSchema

SETTINGS = TableSchema(
    name="settings",
    primary_key="key",
    columns=("key", "value"),
    insert_columns=("key", "value"),
    update_columns=("value",),
)

DEPARTMENTS = TableSchema(
    name="departments",
    columns=("id", "name", "total_members"),
)

ATHLETES = TableSchema(
    name="athletes",
    columns=("id", "athlete_type", "athlete_no", "name", "gender", "birth_date", "department_id", "age_group", "created_at"),
    insert_columns=("athlete_type", "athlete_no", "name", "gender", "birth_date", "department_id", "age_group"),
    update_columns=("athlete_type", "athlete_no", "name", "gender", "birth_date", "department_id", "age_group"),
)

ATHLETE_TABLES = {
    "competitive": ATHLETES,
    "fun": ATHLETES,
}

EVENTS = TableSchema(
    name="events",
    columns=("id", "name", "category", "event_type", "scoring_strategy", "gender", "age_group", "is_individual"),
)

ATHLETE_REGISTRATIONS = TableSchema(
    name="athlete_registrations",
    columns=("id", "athlete_type", "athlete_ref_id", "event_id", "created_at"),
    insert_columns=("athlete_type", "athlete_ref_id", "event_id"),
    update_columns=("athlete_type", "athlete_ref_id", "event_id"),
)

TEAMS = TableSchema(
    name="teams",
    columns=("id", "department_id", "event_id", "name"),
)

TEAM_MEMBERS = TableSchema(
    name="team_members",
    columns=("id", "team_id", "athlete_type", "athlete_ref_id"),
)

RESULTS = TableSchema(
    name="results",
    columns=("id", "event_id", "athlete_type", "athlete_ref_id", "team_id", "rank", "points", "performance", "entered_by", "created_at"),
    insert_columns=("event_id", "athlete_type", "athlete_ref_id", "team_id", "rank", "points", "performance", "entered_by"),
    update_columns=("event_id", "athlete_type", "athlete_ref_id", "team_id", "rank", "points", "performance", "entered_by"),
)

ATTEMPTS = TableSchema(
    name="attempts",
    columns=("id", "event_id", "athlete_type", "athlete_ref_id", "team_id", "attempt_number", "rank", "performance", "is_void", "entered_by", "created_at"),
    insert_columns=("event_id", "athlete_type", "athlete_ref_id", "team_id", "attempt_number", "rank", "performance", "is_void", "entered_by"),
    update_columns=("event_id", "athlete_type", "athlete_ref_id", "team_id", "attempt_number", "rank", "performance", "is_void", "entered_by"),
)

EVENT_PROGRESS = TableSchema(
    name="event_progress",
    primary_key="event_id",
    columns=("event_id", "checkin_done", "competition_done", "record_done", "publish_done", "updated_at"),
    insert_columns=("event_id", "checkin_done", "competition_done", "record_done", "publish_done", "updated_at"),
    update_columns=("checkin_done", "competition_done", "record_done", "publish_done", "updated_at"),
)
