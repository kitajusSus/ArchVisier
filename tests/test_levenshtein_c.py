"""Tests for the native Levenshtein distance library."""
from __future__ import annotations

from pathlib import Path
import ctypes
import subprocess
import sys
import shutil

NATIVE_DIR = Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna" / "native"
LIB_NAME = f"liblevenshtein.{ 'dll' if sys.platform.startswith('win') else 'so'}"
LIB = NATIVE_DIR / LIB_NAME


def _build_lib() -> None:
    if shutil.which("zig"):
        cmd = [
            "zig",
            "cc",
            "-O3",
            "-shared",
            "levenshtein.c",
            "-fopenmp",
            "-o",
            LIB.name,
        ]
    elif shutil.which("gcc"):
        cmd = [
            "gcc",
            "-O3",
            "-fPIC",
            "-shared",
            "levenshtein.c",
            "-o",
            LIB.name,
            "-fopenmp",
        ]
    else:
        raise RuntimeError("No suitable C compiler found")
    subprocess.run(cmd, cwd=NATIVE_DIR, check=True)


if not LIB.exists():
    _build_lib()

lib = ctypes.CDLL(str(LIB))
lib.levenshtein_distance.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lib.levenshtein_distance.restype = ctypes.c_int


def _python_lev(a: str, b: str) -> int:
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


def test_c_matches_python():
    samples = [
        ("kitten", "sitting"),
        ("flaw", "lawn"),
        ("", "test"),
        ("archiwizator", "archiwizacja"),
    ]
    for a, b in samples:
        expected = _python_lev(a, b)
        result = lib.levenshtein_distance(a.encode(), b.encode())
        assert result == expected
