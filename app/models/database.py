from .legacy import legacy_interface
from .mvc.infrastructure.database import Database as _MvcDatabase
from .mvc.infrastructure.database import SCHEMA_SQL


@legacy_interface("app.models.database.Database 是兼容旧接口，将在未来前后端分离阶段移除，请改用 app.models.mvc.infrastructure.Database")
class Database(_MvcDatabase):
    """Legacy compatibility wrapper for the MVC infrastructure Database."""

    pass


__all__ = ["Database", "SCHEMA_SQL"]
