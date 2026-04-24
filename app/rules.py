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


def point_rule_for_result_type(result_type: str) -> dict[int, int]:
    configured = load_rule_config().get("point_rule", {})
    if "individual" not in configured and "team" not in configured:
        configured = {"individual": configured, "team": configured}

    if result_type not in configured:
        allowed = "/".join(sorted(configured)) or "未配置"
        raise ValueError(f"result_type 必须是 {allowed}")
    return {int(rank): int(points) for rank, points in configured[result_type].items()}


def result_type_for_event(is_individual: int | bool) -> str:
    return "individual" if int(is_individual) == 1 else "team"


def points_for_rank(rank: int, is_individual: int | bool) -> int:
    rule = point_rule_for_result_type(result_type_for_event(is_individual))
    return rule.get(int(rank), 0)


def scoring_strategy_for_event_type(event_type: str) -> str:
    mapping = load_rule_config().get("event_scoring_strategy", {})
    if event_type not in mapping:
        allowed = "/".join(sorted(mapping)) or "未配置"
        raise ValueError(f"event_type 必须是 {allowed}")
    return str(mapping[event_type])
