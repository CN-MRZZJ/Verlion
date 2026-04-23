from .legacy import legacy_interface
from .mvc.domain.user import User as _MvcUser


@legacy_interface("app.models.user.User 是兼容旧接口，将在未来前后端分离阶段移除，请改用 app.models.mvc.domain.entities.User")
class User(_MvcUser):
    """Legacy compatibility wrapper for the MVC user entity."""

    pass


__all__ = ["User"]
