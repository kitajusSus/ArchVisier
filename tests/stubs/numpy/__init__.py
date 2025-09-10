"""Lightweight stand‑in for :mod:`numpy` used during testing.

The real NumPy dependency is fairly heavy and not available in the execution
environment.  The unit tests only rely on a tiny portion of its API, so this
module implements just enough features for those tests to run:

* ``array``/``asarray`` for creating arrays
* ``dot`` and ``linalg.norm`` for basic linear algebra
* ``random.default_rng`` with a ``random`` method

The goal is to keep the implementation small and easy to understand.  Only the
behaviour exercised by the tests is provided.
"""

from __future__ import annotations

import ctypes
import random as _py_random
from typing import Iterable, List


# ---------------------------------------------------------------------------
# dtypes
# ---------------------------------------------------------------------------

float32 = "float32"
float64 = "float64"
bool_ = bool


class _CtypesWrapper:
    def __init__(self, buf: ctypes.Array) -> None:
        self._buf = buf

    def data_as(self, c_type):
        return ctypes.cast(self._buf, c_type)


class ndarray:
    """Very small array implementation supporting the needed features."""

    def __init__(self, data: Iterable[float], dtype: str = float64) -> None:
        self.data: List[float] = [float(x) for x in data]
        self.dtype = dtype
        self._c_buffer: ctypes.Array | None = None

    # basic container protocol ------------------------------------------------
    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.data)

    def __iter__(self):  # pragma: no cover - trivial
        return iter(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

    def tolist(self) -> List[float]:
        """Return a plain Python ``list`` of the array's data."""
        return list(self.data)

    # numpy-like helpers ------------------------------------------------------
    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def ctypes(self) -> _CtypesWrapper:
        typ = ctypes.c_float if self.dtype == float32 else ctypes.c_double
        self._c_buffer = (typ * len(self.data))(*self.data)
        return _CtypesWrapper(self._c_buffer)

    def astype(self, dtype: str, copy: bool = False) -> "ndarray":
        if dtype == self.dtype and not copy:
            return self
        return ndarray(self.data, dtype)


def asarray(seq, dtype: str | None = None) -> ndarray:
    if isinstance(seq, ndarray):
        arr = seq
    else:
        try:
            arr = ndarray(list(seq))  # type: ignore[arg-type]
        except TypeError:  # object not iterable -> treat as scalar
            arr = ndarray([0.0])
    if dtype is not None:
        arr = arr.astype(dtype)
    return arr


def array(seq, dtype: str | None = None) -> ndarray:
    return asarray(seq, dtype=dtype)


def dot(a, b) -> float:
    a_arr = asarray(a)
    b_arr = asarray(b)
    return sum(x * y for x, y in zip(a_arr.data, b_arr.data))


class _Linalg:
    @staticmethod
    def norm(a) -> float:
        arr = asarray(a)
        return dot(arr, arr) ** 0.5


linalg = _Linalg()


# Random number generation ----------------------------------------------------


class _RNG:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = _py_random.Random(seed)

    def random(self, size: int, dtype: str = float64) -> ndarray:
        data = [self._rng.random() for _ in range(size)]
        return ndarray(data, dtype=dtype)


class _RandomModule:
    @staticmethod
    def default_rng(seed: int | None = None) -> _RNG:
        return _RNG(seed)


random = _RandomModule()


def isscalar(obj) -> bool:  # pragma: no cover - trivial helper
    return not isinstance(obj, (list, tuple, dict, ndarray))


__all__ = [
    "array",
    "asarray",
    "dot",
    "float32",
    "float64",
    "bool_",
    "linalg",
    "random",
    "ndarray",
    "isscalar",
]


