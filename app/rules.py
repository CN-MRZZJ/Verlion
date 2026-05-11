import json
from functools import lru_cache
from typing import Any

from app.models.database import Database

_rules_db: Database | None = None


def set_rules_db(db: Database) -> None:
    global _rules_db
    _rules_db = db


def _get_rules_db() -> Database:
    if _rules_db is None:
        raise RuntimeError("rules DB not initialized — call set_rules_db() at startup")
    return _rules_db


def invalidate_rules_cache() -> None:
    load_rule_config.cache_clear()


@lru_cache(maxsize=1)
def load_rule_config() -> dict[str, Any]:
    db = _get_rules_db()
    with db.connect() as conn:
        event_types_rows = conn.execute(
            "SELECT code, name, scoring_strategy FROM event_types ORDER BY code"
        ).fetchall()
        event_scoring_strategy = {r["code"]: r["scoring_strategy"] for r in event_types_rows}

        point_rows = conn.execute(
            "SELECT result_type, rank, points FROM point_rules ORDER BY result_type, rank"
        ).fetchall()
        point_rule: dict[str, dict[str, int]] = {"individual": {}, "team": {}}
        for r in point_rows:
            point_rule[r["result_type"]][str(r["rank"])] = r["points"]

        age_rows = conn.execute(
            "SELECT scope, value, label FROM group_options ORDER BY scope, sort_order"
        ).fetchall()
        group_options: dict[str, Any] = {"athlete": [], "event": [], "fallback_label": "不限组", "team_event_default": "ALL"}
        for r in age_rows:
            group_options[r["scope"]].append({"value": r["value"], "label": r["label"]})

        for key, default in [
            ("rule.attempt_policy", "best"),
            ("rule.team_event_default", "ALL"),
        ]:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            if row:
                val = str(row["value"]).strip()
                if key == "rule.attempt_policy":
                    group_options["_attempt_policy"] = val
                elif key == "rule.team_event_default":
                    group_options["team_event_default"] = val

        attempt_policy_val = group_options.pop("_attempt_policy", None)

    return {
        "attempt_policy": str(attempt_policy_val) if attempt_policy_val else "best",
        "event_scoring_strategy": event_scoring_strategy,
        "point_rule": point_rule,
        "group_options": group_options,
    }


def save_rule_config(config: dict[str, Any]) -> None:
    validate_rule_config(config)
    db = _get_rules_db()
    with db.connect() as conn:
        name_map = {"track": "径赛", "field": "田赛", "fun": "趣味"}
        for code, strategy in config.get("event_scoring_strategy", {}).items():
            if str(code).startswith("_"):
                continue
            existing = conn.execute(
                "SELECT name FROM event_types WHERE code=?", (code,)
            ).fetchone()
            display_name = existing["name"] if existing else name_map.get(code, code)
            conn.execute(
                "INSERT INTO event_types(code, name, scoring_strategy) VALUES(?,?,?)"
                " ON CONFLICT(code) DO UPDATE SET scoring_strategy=excluded.scoring_strategy",
                (code, display_name, strategy),
            )
        keep_codes = [
            c for c in config.get("event_scoring_strategy", {})
            if not str(c).startswith("_")
        ]
        if keep_codes:
            placeholders = ",".join("?" for _ in keep_codes)
            conn.execute(
                f"DELETE FROM event_types WHERE code NOT IN ({placeholders})",
                tuple(keep_codes),
            )
        else:
            conn.execute("DELETE FROM event_types")

        conn.execute("DELETE FROM point_rules")
        for result_type in ("individual", "team"):
            rules = config.get("point_rule", {}).get(result_type, {})
            for rank, points in rules.items():
                if str(rank).startswith("_"):
                    continue
                conn.execute(
                    "INSERT INTO point_rules(result_type, rank, points) VALUES(?,?,?)",
                    (result_type, int(rank), int(points)),
                )

        conn.execute("DELETE FROM group_options")
        groups = config.get("group_options", {})
        for scope in ("athlete", "event"):
            for sort_idx, item in enumerate(groups.get(scope, [])):
                if not isinstance(item, dict):
                    continue
                conn.execute(
                    "INSERT INTO group_options(scope, value, label, sort_order) VALUES(?,?,?,?)",
                    (scope, item["value"], item["label"], sort_idx),
                )

        for key, json_path, default in [
            ("rule.attempt_policy", "attempt_policy", "best"),
            ("rule.team_event_default", "group_options.team_event_default", "ALL"),
        ]:
            val = config
            for part in json_path.split("."):
                val = val.get(part, {}) if isinstance(val, dict) else str(val or default)
            if not isinstance(val, str):
                val = str(val or default).strip()
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(val).strip()),
            )

        conn.commit()

    load_rule_config.cache_clear()


def validate_rule_config(config: dict[str, Any]) -> None:
    attempt_policy = config.get("attempt_policy", "best")
    if str(attempt_policy) not in ("best", "latest"):
        raise ValueError("attempt_policy 必须为 best 或 latest")

    point_rule = config.get("point_rule")
    if not isinstance(point_rule, dict):
        raise ValueError("point_rule 必须是对象")
    for result_type in ("individual", "team"):
        rule = point_rule.get(result_type)
        if not isinstance(rule, dict):
            raise ValueError(f"point_rule.{result_type} 必须是对象")
        for rank, points in rule.items():
            if str(rank).startswith("_"):
                continue
            if int(rank) < 1:
                raise ValueError("名次必须 >= 1")
            if int(points) < 0:
                raise ValueError("积分必须 >= 0")

    scoring = config.get("event_scoring_strategy")
    if not isinstance(scoring, dict):
        raise ValueError("event_scoring_strategy 必须是对象")
    allowed_scoring = {"time", "length", "count", "count_miss"}
    for event_type, strategy in scoring.items():
        if str(event_type).startswith("_"):
            continue
        if str(strategy) not in allowed_scoring:
            raise ValueError(f"{event_type} 的 scoring_strategy 无效: {strategy}")

    groups = config.get("group_options")
    if not isinstance(groups, dict):
        raise ValueError("group_options 必须是对象")
    for scope in ("athlete", "event"):
        options = groups.get(scope)
        if not isinstance(options, list):
            raise ValueError(f"group_options.{scope} 必须是数组")
        seen_values: set[str] = set()
        for item in options:
            value = str(item.get("value", "")).strip() if isinstance(item, dict) else ""
            if not isinstance(item, dict) or not value:
                raise ValueError(f"group_options.{scope} 包含无效选项")
            if not str(item.get("label", "")).strip():
                raise ValueError(f"group_options.{scope} 的 label 不能为空")
            if value in seen_values:
                raise ValueError(f"group_options.{scope} 存在重复值: {value}")
            seen_values.add(value)
    team_event_default = str(groups.get("team_event_default", "")).strip()
    if team_event_default and team_event_default not in {item["value"] for item in _group_options_from_config(groups, "event")}:
        raise ValueError("group_options.team_event_default 必须存在于 event 组别选项中")


def point_rule_for_result_type(result_type: str) -> dict[int, int]:
    configured = load_rule_config().get("point_rule", {})
    if "individual" not in configured and "team" not in configured:
        configured = {"individual": configured, "team": configured}

    rule_config = configured.get(result_type)
    if not isinstance(rule_config, dict):
        allowed = "/".join(sorted(key for key in configured if not key.startswith("_"))) or "未配置"
        raise ValueError(f"result_type 必须是 {allowed}")
    return {int(rank): int(points) for rank, points in rule_config.items() if not str(rank).startswith("_")}


def result_type_for_event(is_individual: int | bool) -> str:
    return "individual" if int(is_individual) == 1 else "team"


def points_for_rank(rank: int, is_individual: int | bool) -> int:
    rule = point_rule_for_result_type(result_type_for_event(is_individual))
    return rule.get(int(rank), 0)


def scoring_strategy_for_event_type(event_type: str) -> str:
    mapping = {
        key: value
        for key, value in load_rule_config().get("event_scoring_strategy", {}).items()
        if not str(key).startswith("_")
    }
    if event_type not in mapping:
        allowed = "/".join(sorted(mapping)) or "未配置"
        raise ValueError(f"event_type 必须是 {allowed}")
    return str(mapping[event_type])


def _group_options_from_config(configured: dict[str, Any], scope: str) -> list[dict[str, str]]:
    options = configured.get(scope, [])
    return [
        {"value": str(item.get("value", "")), "label": str(item.get("label", ""))}
        for item in options
        if isinstance(item, dict) and item.get("value")
    ]


def group_options(scope: str = "event") -> list[dict[str, str]]:
    configured = load_rule_config().get("group_options", {})
    return _group_options_from_config(configured, scope)


def group_values(scope: str = "event") -> set[str]:
    return {item["value"] for item in group_options(scope)}


def group_labels(scope: str = "event") -> dict[str, str]:
    labels: dict[str, str] = {}
    for item in group_options(scope):
        labels[item["value"]] = item["label"]
    return labels


def group_label(group: str, scope: str = "event") -> str:
    if not group:
        return ""
    labels = group_labels(scope)
    if group in labels:
        return labels[group]
    return str(group)


def athlete_group_label(group: str) -> str:
    return group_label(group, "athlete")


def event_group_label(group: str) -> str:
    return group_label(group, "event")


def team_event_default_group() -> str:
    configured = load_rule_config().get("group_options", {})
    default_value = str(configured.get("team_event_default", "")).strip()
    if default_value:
        return default_value
    options = group_options("event")
    return options[0]["value"] if options else "ALL"


def attempt_policy() -> str:
    policy = str(load_rule_config().get("attempt_policy", "best")).strip().lower()
    if policy not in ("best", "latest"):
        policy = "best"
    return policy
