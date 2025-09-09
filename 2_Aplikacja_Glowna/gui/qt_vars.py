class Var:
    """Lightweight container with get/set semantics for PySide-based UIs."""
    def __init__(self, value=None):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class StringVar(Var):
    pass


class BooleanVar(Var):
    pass
