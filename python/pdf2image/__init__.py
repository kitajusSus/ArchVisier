"""Lightweight stub of :mod:`pdf2image` used in the tests."""


def convert_from_path(path, *args, **kwargs):  # pragma: no cover - simple stub
    return []


def pdfinfo_from_path(path, *args, **kwargs):  # pragma: no cover - simple stub
    return {"Pages": 0}


__all__ = ["convert_from_path", "pdfinfo_from_path"]

