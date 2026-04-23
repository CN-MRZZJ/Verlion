from .athlete_repository import AthleteRepositoryMixin
from .base_repository import BaseRepositoryMixin
from .department_repository import DepartmentRepositoryMixin
from .event_repository import EventRepositoryMixin
from .query_repository import QueryRepositoryMixin
from .registration_repository import RegistrationRepositoryMixin
from .reporting_repository import ReportingRepositoryMixin
from .result_repository import ResultRepositoryMixin
from .settings_repository import SettingsRepositoryMixin
from .team_repository import TeamRepositoryMixin


class SportsRepository(
    BaseRepositoryMixin,
    SettingsRepositoryMixin,
    DepartmentRepositoryMixin,
    AthleteRepositoryMixin,
    EventRepositoryMixin,
    RegistrationRepositoryMixin,
    TeamRepositoryMixin,
    ResultRepositoryMixin,
    ReportingRepositoryMixin,
    QueryRepositoryMixin,
):
    pass


__all__ = ["SportsRepository"]
