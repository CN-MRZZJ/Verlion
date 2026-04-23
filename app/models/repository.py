from .legacy import legacy_interface
from .mvc.infrastructure.repositories.sports_repository import SportsRepository as _MvcSportsRepository


@legacy_interface("app.models.repository.SportsRepository 是兼容旧接口，将在未来前后端分离阶段移除，请改用 app.models.mvc.infrastructure.repositories.SportsRepository")
class SportsRepository(_MvcSportsRepository):
    """Legacy compatibility wrapper for the MVC repository implementation."""

    pass


__all__ = ["SportsRepository"]
