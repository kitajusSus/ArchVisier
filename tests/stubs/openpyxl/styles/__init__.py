"""Styles submodule for openpyxl stub."""


class Font:  # pragma: no cover - simple container
    def __init__(self, *args, **kwargs):
        pass


class Alignment:  # pragma: no cover - simple container
    def __init__(self, *args, **kwargs):
        pass


class PatternFill:  # pragma: no cover - simple container
    def __init__(self, *args, **kwargs):
        self.start_color = kwargs.get("start_color")
        self.end_color = kwargs.get("end_color")
        self.fill_type = kwargs.get("fill_type")


class Side:  # pragma: no cover - simple container
    def __init__(self, *args, **kwargs):
        self.style = kwargs.get("style")
        self.color = kwargs.get("color")


class Border:  # pragma: no cover - simple container
    def __init__(self, *args, **kwargs):
        self.left = kwargs.get("left")
        self.right = kwargs.get("right")
        self.top = kwargs.get("top")
        self.bottom = kwargs.get("bottom")


__all__ = ["Font", "Alignment", "PatternFill", "Border", "Side"]

