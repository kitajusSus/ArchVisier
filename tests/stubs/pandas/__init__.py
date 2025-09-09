"""Minimal stub of the pandas package used in tests."""

class DataFrame:
    def __init__(self, data, columns=None):
        self._data = list(data)
        self.columns = columns or []

    def __getitem__(self, key):  # pragma: no cover - simplified
        return [row[self.columns.index(key)] for row in self._data if key in self.columns]

    def __setitem__(self, key, value):  # pragma: no cover - simplified
        pass

    def to_excel(self, writer, sheet_name=None, index=False, startrow=0):  # pragma: no cover
        pass


class ExcelWriter:
    def __init__(self, path, engine=None):
        self.path = path
        self.sheets = {"Archiwum Dokumentów": Worksheet()}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # pragma: no cover - simplified
        return False


class Worksheet:
    def merge_cells(self, _range):  # pragma: no cover - simplified
        pass

    def cell(self, row, column):  # pragma: no cover - simplified
        return type("Cell", (), {"value": None, "font": None, "alignment": None})()


def to_datetime(values, errors="coerce"):  # pragma: no cover - simplified
    class _DT:
        def __init__(self, vals):
            self._vals = vals

        def strftime(self, fmt):
            return self._vals

    return type("DTWrapper", (), {"dt": _DT(values)})()


__all__ = ["DataFrame", "ExcelWriter", "to_datetime"]

