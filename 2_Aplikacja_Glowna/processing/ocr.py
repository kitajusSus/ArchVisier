"""OCR utilities for the application."""
import os
import sys
import logging
import traceback
from typing import List, Optional, Sequence, Tuple
from queue import Queue
import threading

import re
import subprocess
try:
    import numpy as np
except Exception:  # pragma: no cover - minimal stub
    class _NP:
        @staticmethod
        def array(obj):
            return obj

    np = _NP()

import cv2
import pytesseract
try:  # pragma: no cover - handled in tests via real module
    import Levenshtein
except Exception:  # pragma: no cover - fallback if module missing
    import ctypes

    def _levenshtein_distance_py(a: str, b: str) -> int:
        """Simple Levenshtein distance implementation."""
        dp = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost,
                )
        return dp[-1][-1]

    _lib = None
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _native = os.path.join(_base, "native")
    _libname = "levenshtein.dll" if os.name == "nt" else "liblevenshtein.so"
    try:  # pragma: no cover - depends on library presence
        _lib = ctypes.CDLL(os.path.join(_native, _libname))
        _lib.levenshtein_distance.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        _lib.levenshtein_distance.restype = ctypes.c_int

        def _levenshtein_distance(a: str, b: str) -> int:
            return _lib.levenshtein_distance(a.encode("utf-8"), b.encode("utf-8"))

    except OSError:  # pragma: no cover - fallback to pure python
        def _levenshtein_distance(a: str, b: str) -> int:
            return _levenshtein_distance_py(a, b)

    class _LevenshteinModule:
        @staticmethod
        def distance(a: str, b: str) -> int:
            return _levenshtein_distance(a, b)

    Levenshtein = _LevenshteinModule()

try:  # pragma: no cover
    from langdetect import detect
except Exception:  # pragma: no cover - simple heuristic fallback
    def detect(text: str) -> str:
        polish_chars = set("ąćęłńóśżź")
        return "pl" if any(ch in polish_chars for ch in text.lower()) else "en"
from pdf2image import convert_from_path, pdfinfo_from_path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import config as app_config
except ModuleNotFoundError:  # pragma: no cover - fallback for tests
    import importlib.util
    import pathlib
    import sys as _sys

    _config_path = pathlib.Path(__file__).resolve().parent.parent / "config.py"
    spec = importlib.util.spec_from_file_location("config", _config_path)
    app_config = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    spec.loader.exec_module(app_config)  # type: ignore
    _sys.modules["config"] = app_config

logger = logging.getLogger(__name__)


def _configure_pytesseract() -> None:
    """Apply OCR-related paths from configuration."""
    folder = app_config.SETTINGS.tesseract_folder
    if folder:
        pytesseract.pytesseract.tesseract_cmd = os.path.join(
            folder, "tesseract.exe"
        )
        os.environ["TESSDATA_PREFIX"] = os.path.join(folder, "tessdata")
    pytesseract.pytesseract.popen_kwargs = {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)
    }


_configure_pytesseract()


# Small fallback dictionaries for word correction
POLISH_DICTIONARY = {"test", "przyklad"}
ENGLISH_DICTIONARY = {"test", "example"}


def _correct_token(token: str, dictionary: set) -> str:
    """Correct a single token using Levenshtein distance."""
    if not token.isalpha():
        return token
    lower = token.lower()
    if lower in dictionary:
        return token
    closest = min(dictionary, key=lambda w: Levenshtein.distance(lower, w))
    if Levenshtein.distance(lower, closest) <= 2:
        return closest
    return token


def correct_text(text: str, lang: str) -> str:
    """Correct OCR text using a simple dictionary-based approach."""
    dictionary = POLISH_DICTIONARY if lang == "pol" else ENGLISH_DICTIONARY
    tokens = re.split(r"(\W+)", text)
    corrected = [_correct_token(t, dictionary) for t in tokens]
    return "".join(corrected)


def _build_config(config: str, psm: int, oem: int) -> str:
    """Merge user config with ``psm`` and ``oem`` options."""
    parts = []
    config = config.strip()
    if config:
        parts.append(config)
    if "--psm" not in config:
        parts.append(f"--psm {psm}")
    if "--oem" not in config:
        parts.append(f"--oem {oem}")
    return " ".join(parts)


def extract_text_with_ocr(
    pdf_path: str,
    progress_queue: Optional[Queue] = None,
    language: str = "pol",
    config: str = "",
    psm: int = 3,
    oem: int = 3,
) -> Tuple[str, str]:
    """Perform OCR on a single PDF file.

    Args:
        pdf_path: Path to the PDF file.
        progress_queue: Optional queue to report page processing progress.
        language: OCR language or ``"auto"`` for detection.
        config: Additional Tesseract configuration string.
        psm: Page segmentation mode for Tesseract.
        oem: OCR engine mode for Tesseract.

    Returns:
        A tuple ``(text, status)`` containing recognized text and status
        message.
    """

    try:
        config = _build_config(config, psm, oem)
        kwargs = {}
        if os.name == "nt":
            kwargs["popen_kwargs"] = {
                "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)
            }
        try:
            images = convert_from_path(
                pdf_path,
                app_config.SETTINGS.ocr_dpi,
                poppler_path=app_config.SETTINGS.poppler_folder or None,
                fmt="jpeg",
                **kwargs,
            )
        except TypeError:
            images = convert_from_path(
                pdf_path,
                app_config.SETTINGS.ocr_dpi,
                poppler_path=app_config.SETTINGS.poppler_folder or None,
                fmt="jpeg",
            )
        if not images:
            return "BŁĄD: Plik PDF jest pusty lub uszkodzony.", ""

        full_text = ""
        for pil_image in images:
            open_cv_image = np.array(pil_image)
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.medianBlur(gray, app_config.SETTINGS.blur_kernel_size)
            processed_cv_image = cv2.adaptiveThreshold(
                blurred,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                app_config.SETTINGS.adaptive_threshold_block_size,
                app_config.SETTINGS.adaptive_threshold_c,
            )

            lang = language
            text_page = ""
            if language == "auto":
                preliminary = pytesseract.image_to_string(
                    processed_cv_image, lang="pol+eng", config=config
                )
                try:
                    detected = detect(preliminary)
                    lang = "pol" if detected == "pl" else "eng"
                except Exception:  # pragma: no cover - fall back to polish
                    lang = "pol"
                text_page = pytesseract.image_to_string(
                    processed_cv_image, lang=lang, config=config
                )
            else:
                text_page = pytesseract.image_to_string(
                    processed_cv_image, lang=lang, config=config
                )

            text_page = correct_text(text_page, lang)
            full_text += text_page + "\n"
            if progress_queue is not None:
                progress_queue.put(("page_done", 1))
        return full_text, "Sukces"
    except pytesseract.TesseractError as e:
        logger.error("Błąd OCR (kod %s): %s", e.status, e.message.strip())
        return f"BŁĄD TECHNICZNY OCR: {e.message.strip()}", traceback.format_exc()
    except Exception as e:
        logger.error("Błąd OCR: %s", e)
        return f"BŁĄD TECHNICZNY OCR: {e}", traceback.format_exc()


def extract_texts_with_ocr_parallel(
    pdf_paths: Sequence[str],
    cancel_event: threading.Event,
    progress_queue: Optional[Queue] = None,
    language: str = "pol",
    config: str = "",
    psm: int = 3,
    oem: int = 3,
) -> Tuple[List[Optional[Tuple[str, str]]], int]:
    """Perform OCR on multiple PDFs in parallel.

    Args:
        pdf_paths: Iterable of PDF paths to process.
        cancel_event: Event flag to stop processing early.
        progress_queue: Optional queue for progress updates.
        language: OCR language or ``"auto"`` for detection.
        config: Additional Tesseract configuration string.
        psm: Page segmentation mode for Tesseract.
        oem: OCR engine mode for Tesseract.

    Returns:
        A tuple with a list of per-file OCR results and total page count.
    """

    def _count_pages(path: str) -> int:
        try:
            kwargs = {}
            if os.name == "nt":
                kwargs["popen_kwargs"] = {
                    "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)
                }
            try:
                info = pdfinfo_from_path(
                    path,
                    poppler_path=app_config.SETTINGS.poppler_folder or None,
                    **kwargs,
                )
            except TypeError:
                info = pdfinfo_from_path(
                    path,
                    poppler_path=app_config.SETTINGS.poppler_folder or None,
                )
            return int(info.get("Pages", 0))
        except Exception as e:  # pragma: no cover - log and continue
            logger.error("Błąd odczytu liczby stron dla %s: %s", path, e)
            return 0

    config = _build_config(config, psm, oem)
    total_pages = sum(_count_pages(path) for path in pdf_paths)

    results = [None] * len(pdf_paths)
    if cancel_event.is_set():
        return results, total_pages

    max_workers = app_config.SETTINGS.ocr_workers
    executor = ThreadPoolExecutor(max_workers=max_workers or os.cpu_count())
    futures = {
        executor.submit(
            extract_text_with_ocr,
            path,
            progress_queue,
            language,
            config,
            psm,
            oem,
        ): idx
        for idx, path in enumerate(pdf_paths)
    }

    try:
        for future in as_completed(futures):
            if cancel_event.is_set():
                break
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:  # pragma: no cover - defensive programming
                logger.error(f"Błąd równoległego OCR: {e}")
                results[idx] = (f"BŁĄD TECHNICZNY OCR: {e}", traceback.format_exc())
    finally:
        executor.shutdown(
            wait=not cancel_event.is_set(), cancel_futures=cancel_event.is_set()
        )

    return results, total_pages

