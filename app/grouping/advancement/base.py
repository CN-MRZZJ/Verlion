from abc import ABC, abstractmethod

from app.grouping.schema import AdvancementInput, AdvancementOutput


class BaseAdvancement(ABC):
    name: str = ""

    @abstractmethod
    def run(self, input: AdvancementInput) -> AdvancementOutput:
        ...
