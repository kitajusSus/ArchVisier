try:  # pragma: no cover - import attempt
    from PySide6 import QtWidgets, QtGui, QtCore
    QT_AVAILABLE = True
except Exception:  # pragma: no cover - missing system deps
    QT_AVAILABLE = False

    class _FallbackMeta(type):
        """Metaclass providing stub behaviour for Qt classes."""

        def __getattr__(cls, name):  # pragma: no cover - simple stub
            return cls

        def __or__(cls, other):  # pragma: no cover - simple stub
            return cls

        def __and__(cls, other):  # pragma: no cover - simple stub
            return cls

        def __bool__(cls):  # pragma: no cover - simple stub
            return False

    class _QtFallback(metaclass=_FallbackMeta):
        """Fallback object used when Qt libraries are unavailable.

        The class and its instances swallow all attribute access, method calls
        and basic operators so that importing UI modules in environments
        without Qt does not immediately crash.  It behaves as a very permissive
        stub and should only be used for testing or environments where the GUI
        is not required.
        """

        def __init__(self, *args, **kwargs):  # pragma: no cover - simple stub
            pass

        def __getattr__(self, name):  # pragma: no cover - simple stub
            return _QtFallback()

        def __call__(self, *args, **kwargs):  # pragma: no cover - simple stub
            return _QtFallback()

        def __or__(self, other):  # pragma: no cover - simple stub
            return _QtFallback()

        def __and__(self, other):  # pragma: no cover - simple stub
            return _QtFallback()

        def __bool__(self):  # pragma: no cover - simple stub
            return False

    QtWidgets = _QtFallback
    QtGui = _QtFallback
    QtCore = _QtFallback
