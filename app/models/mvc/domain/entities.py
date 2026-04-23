from dataclasses import dataclass
from typing import Optional


@dataclass
class Department:
    id: int
    name: str
    total_members: int


@dataclass
class Athlete:
    athlete_type: str
    athlete_ref_id: int
    athlete_no: Optional[str]
    name: str
    gender: str
    age_group: Optional[str]
    department_name: Optional[str] = None


@dataclass
class Event:
    id: int
    name: str
    category: str
    event_type: str
    scoring_strategy: str
    gender: str
    age_group: str
    is_individual: int


@dataclass
class Team:
    id: int
    event_id: int
    team_name: str
    department_name: str


@dataclass
class Result:
    id: int
    event_name: str
    category: str
    scoring_strategy: str
    rank: int
    points: int
    target_name: str
    department_name: Optional[str]
    performance: Optional[str] = None


@dataclass
class User:
    username: str
