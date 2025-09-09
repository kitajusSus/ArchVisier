"""Minimal stub of the :mod:`pydantic` package used in tests.

This stub provides just enough functionality for the project's configuration
module during tests where the real dependency is unavailable.  It only
implements :class:`BaseModel` with ``dict`` support and a simplified
``Field`` helper that respects ``default_factory``.
"""

from typing import Any, Callable


def Field(*, default: Any = None, default_factory: Callable[[], Any] | None = None):
    """Return the default value or invoke ``default_factory`` if provided."""

    return default_factory() if default_factory is not None else default


class BaseModel:
    """Very small subset of :class:`pydantic.BaseModel` used in tests."""

    def __init__(self, **data: Any) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    def dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.__dict__.copy()


def validator(*fields: str, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator used in tests to mimic :func:`pydantic.validator`.

    The real pydantic library performs complex validation.  Our stub simply
    returns the wrapped function unchanged so that validation logic executes
    when fields are assigned.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator

