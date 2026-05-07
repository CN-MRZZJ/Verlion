from abc import ABC, abstractmethod

from app.grouping.schema import GroupingInput, GroupingOutput


class BaseAlgorithm(ABC):
    name: str

    @abstractmethod
    def run(self, input: GroupingInput) -> GroupingOutput: ...
