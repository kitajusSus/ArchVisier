"""Wrapper for the Zig token similarity library using ctypes."""
from __future__ import annotations
import ctypes
from pathlib import Path
import sys

_LIB_DIR = (
    Path(__file__).resolve().parent.parent
    / "zig_modules"
    / "token_similarity"
    / "zig-out"
    / "lib"
)
if sys.platform.startswith("win"):
    _LIB_PATH = _LIB_DIR / "token_similarity.dll"
else:
    _LIB_PATH = _LIB_DIR / "libtoken_similarity.so"

if not _LIB_PATH.exists():
    raise FileNotFoundError(f"Zig library not found: {_LIB_PATH}")

_lib = ctypes.CDLL(str(_LIB_PATH))

_lib.token_similarity.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
_lib.token_similarity.restype = ctypes.c_double

def token_similarity(a: str, b: str) -> float:
    """Return similarity score between two strings."""
    return _lib.token_similarity(a.encode("utf-8"), b.encode("utf-8"))
