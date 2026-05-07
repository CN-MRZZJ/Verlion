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
    columns=("id", "athlete_type", "athlete_no", "name", "gender", "birth_date", "department_id", "group", "created_at"),
    insert_columns=("athlete_type", "athlete_no", "name", "gender", "birth_date", "department_id", "group"),
    update_columns=("athlete_type", "athlete_no", "name", "gender", "birth_date", "department_id", "group"),
)

ATHLETE_TABLES = {
    "competitive": ATHLETES,
    "fun": ATHLETES,
}

EVENTS = TableSchema(
    name="events",
    columns=("id", "name", "category", "event_type", "scoring_strategy", "gender", "group", "is_individual", "competition_format"),
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
    columns=("id", "event_id", "round_id", "athlete_type", "athlete_ref_id", "team_id", "rank", "points", "performance", "entered_by", "created_at"),
    insert_columns=("event_id", "round_id", "athlete_type", "athlete_ref_id", "team_id", "rank", "points", "performance", "entered_by"),
    update_columns=("event_id", "round_id", "athlete_type", "athlete_ref_id", "team_id", "rank", "points", "performance", "entered_by"),
)

ATTEMPTS = TableSchema(
    name="attempts",
    columns=("id", "event_id", "round_id", "athlete_type", "athlete_ref_id", "team_id", "attempt_number", "rank", "performance", "is_void", "entered_by", "created_at"),
    insert_columns=("event_id", "round_id", "athlete_type", "athlete_ref_id", "team_id", "attempt_number", "rank", "performance", "is_void", "entered_by"),
    update_columns=("event_id", "round_id", "athlete_type", "athlete_ref_id", "team_id", "attempt_number", "rank", "performance", "is_void", "entered_by"),
)

EVENT_TYPES = TableSchema(
    name="event_types",
    primary_key="code",
    columns=("code", "name", "scoring_strategy", "competition_format"),
    insert_columns=("code", "name", "scoring_strategy", "competition_format"),
    update_columns=("name", "scoring_strategy", "competition_format"),
)

POINT_RULES = TableSchema(
    name="point_rules",
    columns=("id", "result_type", "rank", "points"),
    insert_columns=("result_type", "rank", "points"),
    update_columns=("points",),
)

GROUP_OPTIONS = TableSchema(
    name="group_options",
    columns=("id", "scope", "value", "label", "sort_order"),
    insert_columns=("scope", "value", "label", "sort_order"),
    update_columns=("label", "sort_order"),
)

EVENT_PROGRESS = TableSchema(
    name="event_progress",
    primary_key="event_id",
    columns=("event_id", "checkin_done", "competition_done", "record_done", "publish_done", "updated_at"),
    insert_columns=("event_id", "checkin_done", "competition_done", "record_done", "publish_done", "updated_at"),
    update_columns=("checkin_done", "competition_done", "record_done", "publish_done", "updated_at"),
)

HEATS_CONFIG = TableSchema(
    name="heats_config",
    primary_key="event_id",
    columns=("event_id", "heat_rounds"),
    insert_columns=("event_id", "heat_rounds"),
    update_columns=("heat_rounds",),
)

ROUNDS = TableSchema(
    name="rounds",
    columns=("id", "event_id", "round_number", "round_name", "advancement_rule", "created_at"),
    insert_columns=("event_id", "round_number", "round_name", "advancement_rule"),
    update_columns=("round_name", "advancement_rule"),
)

HEATS = TableSchema(
    name="heats",
    columns=("id", "round_id", "heat_number", "heat_name"),
    insert_columns=("round_id", "heat_number", "heat_name"),
    update_columns=("heat_name",),
)

HEAT_ENTRIES = TableSchema(
    name="heat_entries",
    columns=("id", "heat_id", "athlete_type", "athlete_ref_id", "team_id", "lane"),
    insert_columns=("heat_id", "athlete_type", "athlete_ref_id", "team_id", "lane"),
    update_columns=("athlete_type", "athlete_ref_id", "team_id", "heat_id", "lane"),
)
