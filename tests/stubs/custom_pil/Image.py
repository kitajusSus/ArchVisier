"""Minimal Image module for the Pillow stub."""


class DummyImage:
    pass


def new(mode, size, color="white"):
    return DummyImage()


__all__ = ["new", "DummyImage"]

