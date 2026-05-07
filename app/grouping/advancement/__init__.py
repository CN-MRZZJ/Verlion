from .base import BaseAdvancement

_registry: dict[str, BaseAdvancement] = {}


def register(advancement: BaseAdvancement) -> None:
    if advancement.name:
        _registry[advancement.name] = advancement


def get_advancement(name: str) -> BaseAdvancement:
    if name not in _registry:
        raise ValueError(f"未知晋级策略: {name}，可用: {list(_registry.keys())}")
    return _registry[name]


def list_advancements() -> list[str]:
    return list(_registry.keys())


# Auto-register built-in strategies
from .overall_top import OverallTopAdvancement  # noqa: E402, F401
from .per_heat_top import PerHeatTopAdvancement  # noqa: E402, F401

register(PerHeatTopAdvancement())
register(OverallTopAdvancement())
