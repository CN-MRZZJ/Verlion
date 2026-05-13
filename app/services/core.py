from .admin import MeetAdminMixin
from .athletes import MeetAthleteMixin
from .base import MeetServiceBase
from .departments import MeetDepartmentMixin
from .event_type_service import MeetEventTypeMixin
from .heats import MeetHeatsMixin
from .imports import MeetImportMixin
from .notice import MeetNoticeMixin
from .results import MeetResultMixin
from .worksheet import MeetWorksheetMixin
from .teams import MeetTeamMixin
from .views import MeetViewMixin


class SportsMeetService(
    MeetServiceBase,
    MeetAthleteMixin,
    MeetTeamMixin,
    MeetResultMixin,
    MeetViewMixin,
    MeetNoticeMixin,
    MeetImportMixin,
    MeetAdminMixin,
    MeetDepartmentMixin,
    MeetEventTypeMixin,
    MeetHeatsMixin,
    MeetWorksheetMixin,
):
    pass
