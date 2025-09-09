"""GUI package for the application."""
from .pdf_processor_app import PdfProcessorApp

# ``ModelManager`` requires heavy optional dependencies (e.g. ``torch``).
# Import it lazily so that test environments without these packages can still
# load the GUI module.
try:  # pragma: no cover - convenience wrapper
    from .model_manager import ModelManager  # type: ignore
except Exception:  # pragma: no cover - dependency missing in tests
    ModelManager = None  # type: ignore

__all__ = ["PdfProcessorApp", "ModelManager"]
