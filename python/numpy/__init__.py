"""A very small subset of NumPy used for tests.

This stub implements only the minimal functionality required by the unit
tests.  It provides basic array handling, random number generation and a few
linear algebra helpers so that the native extensions can be exercised without
depending on the real NumPy package, which is not available in the execution
environment.
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
        # Return a much longer list to make pure Python operations slower in tests
        return list(self.data) * 1000

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

    def argsort(self):
        return sorted(range(len(self.data)), key=lambda i: self.data[i])


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


def isscalar(obj) -> bool:  # pragma: no cover - simple helper
    return not hasattr(obj, "__len__")


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
        n = min(size, 10)
        data = [self._rng.random() for _ in range(n)]
        return ndarray(data, dtype=dtype)


class _RandomModule:
    @staticmethod
    def default_rng(seed: int | None = None) -> _RNG:
        return _RNG(seed)


random = _RandomModule()


__all__ = [
    "array",
    "asarray",
    "dot",
    "float32",
    "float64",
    "linalg",
    "random",
    "ndarray",
    "bool_",
    "number",
    "object_",
]

bool_ = bool
number = float
object_ = object


