"""Very small stub of OpenCV used in tests."""

COLOR_BGR2GRAY = 0
ADAPTIVE_THRESH_GAUSSIAN_C = 0
THRESH_BINARY = 0


def cvtColor(image, code):  # pragma: no cover - trivial
    return image


def medianBlur(image, ksize):  # pragma: no cover - trivial
    return image


def adaptiveThreshold(image, max_value, method, threshold_type, block_size, C):  # pragma: no cover - trivial
    return image


__all__ = [
    "COLOR_BGR2GRAY",
    "ADAPTIVE_THRESH_GAUSSIAN_C",
    "THRESH_BINARY",
    "cvtColor",
    "medianBlur",
    "adaptiveThreshold",
]

