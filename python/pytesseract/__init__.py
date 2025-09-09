"""Minimal stub of :mod:`pytesseract` used in the tests."""


class TesseractError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


def image_to_string(image, lang="eng"):  # pragma: no cover - simple stub
    return ""


tesseract_cmd = ""


class _Namespace:
    def __init__(self):
        self.tesseract_cmd = tesseract_cmd


pytesseract = _Namespace()


__all__ = ["image_to_string", "TesseractError", "tesseract_cmd", "pytesseract"]

