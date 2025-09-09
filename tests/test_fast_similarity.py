"""Tests for the native cosine similarity implementations.

The C and Zig libraries located in ``2_Aplikacja_Glowna/native`` expose
``cosine_similarity`` for both ``double`` and ``float`` arrays.  These tests
verify that the results match NumPy's calculation for random vectors and that
the native implementations are significantly faster than a pure Python
baseline.  If the Zig compiler is not available the Zig specific checks are
skipped.
"""

from __future__ import annotations

from pathlib import Path
import ctypes
import subprocess
import shutil
from timeit import timeit

import numpy as np
import pytest


# Paths ----------------------------------------------------------------------

NATIVE_DIR = Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna" / "native"
C_LIB = NATIVE_DIR / "libfast_similarity.so"
ZIG_LIB = NATIVE_DIR / "libfast_similarity_zig.so"


# Building the libraries ------------------------------------------------------

def _build_c() -> None:
    subprocess.run(
        [
            "gcc",
            "-O3",
            "-fPIC",
            "-shared",
            "fast_similarity.c",
            "-o",
            C_LIB.name,
            "-lm",
            "-fopenmp",
        ],
        cwd=NATIVE_DIR,
        check=True,
    )


def _build_zig() -> None:
    subprocess.run(
        [
            "zig",
            "build-lib",
            "fast_similarity.zig",
            "-O",
            "ReleaseFast",
            "-fPIC",
            "-dynamic",
            "-femit-bin=" + ZIG_LIB.name,
        ],
        cwd=NATIVE_DIR,
        check=True,
    )


if not C_LIB.exists():
    _build_c()

zig_available = shutil.which("zig") is not None
if zig_available and not ZIG_LIB.exists():
    try:  # pragma: no cover - only run when zig is available
        _build_zig()
    except Exception:  # pragma: no cover - safety if zig build fails
        zig_available = False


# Loading the libraries -------------------------------------------------------

def _load_library(path: Path) -> ctypes.CDLL:
    lib = ctypes.CDLL(str(path))
    lib.cosine_similarity.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
    ]
    lib.cosine_similarity.restype = ctypes.c_double
    lib.cosine_similarityf.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
    ]
    lib.cosine_similarityf.restype = ctypes.c_float
    return lib


c_lib = _load_library(C_LIB)
zig_lib = _load_library(ZIG_LIB) if zig_available else None


def _cosine_from(lib: ctypes.CDLL, a, b):
    a_arr = np.asarray(a)
    b_arr = np.asarray(b)
    if a_arr.size != b_arr.size:
        raise ValueError("Vectors must have the same length")
    if a_arr.dtype == np.float32 and b_arr.dtype == np.float32:
        return lib.cosine_similarityf(
            a_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            b_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            a_arr.size,
        )
    a_arr = a_arr.astype(np.float64, copy=False)
    b_arr = b_arr.astype(np.float64, copy=False)
    return lib.cosine_similarity(
        a_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        b_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        a_arr.size,
    )


def c_cosine_similarity(a, b):
    return _cosine_from(c_lib, a, b)


def zig_cosine_similarity(a, b):  # pragma: no cover - depends on zig availability
    if zig_lib is None:
        raise RuntimeError("Zig library not available")
    return _cosine_from(zig_lib, a, b)


def python_cosine_similarity(a, b):
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    return 0.0 if na == 0.0 or nb == 0.0 else dot / ((na ** 0.5) * (nb ** 0.5))


# Tests -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "func",
    [c_cosine_similarity] + ([zig_cosine_similarity] if zig_lib is not None else []),
)
def test_cosine_similarity_matches_numpy(func):
    rng = np.random.default_rng(0)
    for dtype in (np.float64, np.float32):
        a = rng.random(1024, dtype=dtype)
        b = rng.random(1024, dtype=dtype)
        expected = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        result = func(a, b)
        tol = 1e-6 if dtype == np.float64 else 1e-5
        assert abs(result - expected) <= tol


@pytest.mark.skipif(
    not hasattr(np, "__version__"),
    reason="NumPy stub provides slower C conversions",
)
def test_benchmark_native_vs_python():
    rng = np.random.default_rng(1)
    a = rng.random(10000).astype(np.float64)
    b = rng.random(10000).astype(np.float64)
    a_list = a.tolist()
    b_list = b.tolist()

    t_c = timeit(lambda: c_cosine_similarity(a, b), number=100)
    if zig_lib is not None:
        t_zig = timeit(lambda: zig_cosine_similarity(a, b), number=100)
    t_python = timeit(lambda: python_cosine_similarity(a_list, b_list), number=10)

    assert t_c * 5 < t_python
    if zig_lib is not None:
        assert t_zig * 5 < t_python

