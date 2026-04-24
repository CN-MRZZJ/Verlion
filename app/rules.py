import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_RULE_CONFIG_PATH = Path(__file__).resolve().parent.parent / "sports_rules.json"
RULE_CONFIG_PATH = Path(os.getenv("SPORTS_RULES_CONFIG", str(DEFAULT_RULE_CONFIG_PATH)))


@lru_cache(maxsize=1)
def load_rule_config() -> dict[str, Any]:
    with RULE_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_rule_config(config: dict[str, Any]) -> None:
    validate_rule_config(config)
    RULE_CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    load_rule_config.cache_clear()


def validate_rule_config(config: dict[str, Any]) -> None:
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

    age_groups = config.get("age_group_options")
    if not isinstance(age_groups, dict):
        raise ValueError("age_group_options 必须是对象")
    for scope in ("athlete", "event"):
        options = age_groups.get(scope)
        if not isinstance(options, list):
            raise ValueError(f"age_group_options.{scope} 必须是数组")
        seen_values: set[str] = set()
        for item in options:
            value = str(item.get("value", "")).strip() if isinstance(item, dict) else ""
            if not isinstance(item, dict) or not value:
                raise ValueError(f"age_group_options.{scope} 包含无效选项")
            if not str(item.get("label", "")).strip():
                raise ValueError(f"age_group_options.{scope} 的 label 不能为空")
            if value in seen_values:
                raise ValueError(f"age_group_options.{scope} 存在重复值: {value}")
            seen_values.add(value)
    team_event_default = str(age_groups.get("team_event_default", "")).strip()
    if team_event_default and team_event_default not in {item["value"] for item in _age_group_options_from_config(age_groups, "event")}:
        raise ValueError("age_group_options.team_event_default 必须存在于 event 组别选项中")


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


def _age_group_options_from_config(configured: dict[str, Any], scope: str) -> list[dict[str, str]]:
    options = configured.get(scope, [])
    return [
        {"value": str(item.get("value", "")), "label": str(item.get("label", ""))}
        for item in options
        if isinstance(item, dict) and item.get("value")
    ]


def age_group_options(scope: str = "event") -> list[dict[str, str]]:
    configured = load_rule_config().get("age_group_options", {})
    return _age_group_options_from_config(configured, scope)


def age_group_values(scope: str = "event") -> set[str]:
    return {item["value"] for item in age_group_options(scope)}


def age_group_labels(scope: str = "event") -> dict[str, str]:
    labels: dict[str, str] = {}
    for item in age_group_options(scope):
        labels[item["value"]] = item["label"]
    return labels


def age_group_label(age_group: str, scope: str = "event") -> str:
    if not age_group:
        return ""
    labels = age_group_labels(scope)
    if age_group in labels:
        return labels[age_group]
    return str(age_group)


def athlete_age_group_label(age_group: str) -> str:
    return age_group_label(age_group, "athlete")


def event_age_group_label(age_group: str) -> str:
    return age_group_label(age_group, "event")


def team_event_default_age_group() -> str:
    configured = load_rule_config().get("age_group_options", {})
    default_value = str(configured.get("team_event_default", "")).strip()
    if default_value:
        return default_value
    options = age_group_options("event")
    return options[0]["value"] if options else "ALL"
