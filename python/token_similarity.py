"""Wrapper for the C token similarity library using ctypes."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "native_c"
BUILD_DIR = SRC_DIR / "build"
if sys.platform.startswith("win"):
    LIB_NAME = "token_similarity.dll"
else:
    LIB_NAME = "libtoken_similarity.so"
LIB_PATH = BUILD_DIR / LIB_NAME


def _build_lib() -> None:
    """Build the native token similarity library with gcc if missing."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    if sys.platform.startswith("win"):
        cmd = ["gcc", "-O3", "-shared", "token_similarity.c", "-o", str(LIB_PATH)]
    else:
        cmd = [
            "gcc",
            "-O3",
            "-fPIC",
            "-shared",
            "token_similarity.c",
            "-o",
            str(LIB_PATH),
        ]
    subprocess.run(cmd, cwd=SRC_DIR, check=True)


if not LIB_PATH.exists():
    _build_lib()

_lib = ctypes.CDLL(str(LIB_PATH))

_lib.token_similarity.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
_lib.token_similarity.restype = ctypes.c_double


def token_similarity(a: str, b: str) -> float:
    """Return similarity score between two strings."""
    return round(
        _lib.token_similarity(a.encode("utf-8"), b.encode("utf-8")), 6
    )
