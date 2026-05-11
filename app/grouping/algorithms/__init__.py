from .base import BaseAlgorithm
from .random import RandomAlgorithm
from .seeded import SeededAlgorithm

_registry: dict[str, BaseAlgorithm] = {}


def register(algorithm: BaseAlgorithm) -> None:
    _registry[algorithm.name] = algorithm


def get_algorithm(name: str) -> BaseAlgorithm:
    if name not in _registry:
        raise ValueError(f"未知编排算法: {name}")
    return _registry[name]


def list_algorithms() -> list[str]:
    return list(_registry.keys())


register(RandomAlgorithm())
register(SeededAlgorithm())
