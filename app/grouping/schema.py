from dataclasses import dataclass, field


@dataclass
class Participant:
    athlete_id: int
    name: str
    athlete_type: str = "competitive"
    department: str = ""
    seed_mark: float | None = None


@dataclass
class GroupingConfig:
    lanes_per_heat: int = 8
    algorithm: str = "random"
    params: dict = field(default_factory=dict)


@dataclass
class Lane:
    athlete_id: int
    athlete_type: str = "competitive"
    lane: int | None = None


@dataclass
class Heat:
    heat_number: int
    heat_name: str
    lanes: list[Lane] = field(default_factory=list)


@dataclass
class Stage:
    stage_number: int
    stage_name: str
    heats: list[Heat] = field(default_factory=list)


@dataclass
class GroupingInput:
    event_id: int
    participants: list[Participant] = field(default_factory=list)
    config: GroupingConfig = field(default_factory=GroupingConfig)


@dataclass
class GroupingOutput:
    event_id: int
    stages: list[Stage] = field(default_factory=list)
