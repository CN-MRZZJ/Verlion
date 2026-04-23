from datetime import date

from .legacy import legacy_interface
from .mvc.domain.rules import POINT_RULE
from .mvc.domain.rules import calc_age_group as _calc_age_group
from .mvc.domain.rules import scoring_strategy_for_event_type as _scoring_strategy_for_event_type


@legacy_interface("app.models.meet.scoring_strategy_for_event_type 是兼容旧接口，将在未来前后端分离阶段移除，请改用 app.models.mvc.domain.rules.scoring_strategy_for_event_type")
def scoring_strategy_for_event_type(event_type: str) -> str:
    return _scoring_strategy_for_event_type(event_type)


@legacy_interface("app.models.meet.calc_age_group 是兼容旧接口，将在未来前后端分离阶段移除，请改用 app.models.mvc.domain.rules.calc_age_group")
def calc_age_group(gender: str, birth_date: date, meet_date: date) -> str:
    return _calc_age_group(gender, birth_date, meet_date)


__all__ = ["POINT_RULE", "calc_age_group", "scoring_strategy_for_event_type"]
