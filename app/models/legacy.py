from __future__ import annotations

import functools
import warnings
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def legacy_interface(message: str) -> Callable[[F], F]:
    """Mark an API as legacy so it can be removed in a later MVC/front-back split phase."""

    def _decorator(obj: F) -> F:
        setattr(obj, "__legacy__", True)
        setattr(obj, "__legacy_message__", message)

        if isinstance(obj, type):
            original_init = obj.__init__

            @functools.wraps(original_init)
            def _wrapped_init(self, *args: Any, **kwargs: Any) -> None:
                warnings.warn(message, DeprecationWarning, stacklevel=2)
                original_init(self, *args, **kwargs)

            obj.__init__ = _wrapped_init  # type: ignore[assignment]
            return obj

        @functools.wraps(obj)
        def _wrapped(*args: Any, **kwargs: Any):
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return obj(*args, **kwargs)

        return cast(F, _wrapped)

    return _decorator
