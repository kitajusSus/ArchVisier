"""Application configuration management.

This module defines :class:`AppSettings` – a Pydantic model that stores
paths to OCR resources, GUI defaults and parameters affecting the OCR
pre‑processing pipeline.  Settings are loaded from ``config.json`` or a
``.env`` file, whichever is found first, and can be persisted back to
``config.json`` via :func:`save_settings`.
"""

import json
import sys
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, validator

# Determine base path for bundled or source execution
if getattr(sys, "frozen", False):
    BASE_PATH = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    BASE_PATH = Path(__file__).resolve().parent

CONFIG_FILE = BASE_PATH / "config.json"
ENV_FILE = BASE_PATH / ".env"


def _coerce_odd(value: int, default: int) -> int:
    """Return a valid odd kernel size.

    Parameters are coerced to integers and adjusted to the nearest odd number
    greater than one.  If coercion fails, ``default`` is used.
    """
    try:
        v = int(value)
    except (TypeError, ValueError):
        v = default
    if v <= 1:
        v = default if default > 1 else 3
    if v % 2 == 0:
        v += 1
    return v


def _get_default(field_name: str) -> int:
    """Return the default value for ``field_name`` from :class:`AppSettings`.

    The project ships with a lightweight ``pydantic`` stub for tests while the
    real application uses the full library (v1 or v2).  This helper therefore
    probes multiple mechanisms to obtain the declared default and finally falls
    back to instantiating :class:`AppSettings` when class attributes are not
    populated (as is the case for Pydantic v2).
    """

    # Pydantic v2 exposes ``model_fields``.
    fields_v2 = getattr(AppSettings, "model_fields", None)
    if fields_v2 and field_name in fields_v2:
        return fields_v2[field_name].default  # type: ignore[attr-defined]

    # Pydantic v1 stores field definitions in ``__fields__``.
    fields_v1 = getattr(AppSettings, "__fields__", None)
    if fields_v1 and field_name in fields_v1:
        return fields_v1[field_name].default  # type: ignore[attr-defined]

    # Lightweight test stub: read the class attribute directly.
    if hasattr(AppSettings, field_name):
        return getattr(AppSettings, field_name)

    # Final fallback – instantiate the model and read the attribute.
    return getattr(AppSettings(), field_name)


class AppSettings(BaseModel):
    """Application configuration loaded from ``config.json`` or ``.env``."""

    # Paths to OCR resources; leave empty to rely on system PATH
    tesseract_folder: str = Field(default="")
    poppler_folder: str = Field(default="")

    # OCR language
    ocr_language: str = "pol"
    ocr_psm: int = 3
    ocr_oem: int = 3

    # GUI defaults
    gui_title: str = "Archiwizator v3.2 (Qt)"
    gui_width: int = 1000
    gui_height: int = 700
    theme: str = "light"
    # Whether the side control panel is visible on startup
    panel_visible: bool = True

    # Default name of subdirectory for processed files
    default_output_subdir: str = "zarchiwizowane"

    # OCR processing parameters
    ocr_dpi: int = 300
    # Maximum number of threads used for OCR; 0 means auto-detect
    ocr_workers: int = 0
    blur_kernel_size: int = 3
    adaptive_threshold_block_size: int = 11
    adaptive_threshold_c: int = 2

    @validator("blur_kernel_size", pre=True, always=True, allow_reuse=True)
    def _ensure_blur_kernel_odd(cls, value):
        """Coerce blur kernel size to a valid odd number."""
        return _coerce_odd(value, 3)

    @validator(
        "adaptive_threshold_block_size", pre=True, always=True, allow_reuse=True
    )
    def _ensure_threshold_block_size_odd(cls, value):
        """Coerce adaptive threshold block size to a valid odd number."""
        return _coerce_odd(value, 11)


# ---------------------------------------------------------------------------
# Configuration persistence helpers

def _load_env_file() -> dict[str, str]:
    data: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def load_settings() -> AppSettings:
    """Load settings from ``config.json`` or ``.env`` and auto-detect bundled binaries."""
    data: dict[str, Any] = {}
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = _load_env_file()

    settings = AppSettings(**data)

    # Ensure kernel parameters are valid even when Pydantic validators are
    # not executed (e.g. in test stubs).
    settings.blur_kernel_size = _coerce_odd(
        settings.blur_kernel_size, _get_default("blur_kernel_size")
    )
    settings.adaptive_threshold_block_size = _coerce_odd(
        settings.adaptive_threshold_block_size, _get_default("adaptive_threshold_block_size")
    )

    # If paths are blank, fall back to bundled folders if they exist
    if not settings.tesseract_folder:
        bundled_tesseract = BASE_PATH / "tesseract"
        if bundled_tesseract.exists():
            settings.tesseract_folder = str(bundled_tesseract)
    if not settings.poppler_folder:
        bundled_poppler = BASE_PATH / "poppler" / "bin"
        if bundled_poppler.exists():
            settings.poppler_folder = str(bundled_poppler)

    return settings


def save_settings(settings: AppSettings) -> None:
    """Persist settings to ``config.json`` and update global state."""
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(settings.dict(), f, indent=2, ensure_ascii=False)
    global SETTINGS
    SETTINGS = settings


# Load settings eagerly so modules can import ``SETTINGS``
SETTINGS: AppSettings = load_settings()
