from .common import main_bp

# Import submodules so they can register routes on main_bp.
from . import api, athletes, imports, notice, pages, results, teams  # noqa: F401

__all__ = ["main_bp"]
