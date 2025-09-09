import runpy
from pathlib import Path

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna" / "config.py"))
coerce = MODULE["_coerce_odd"]


def test_coerce_odd():
    assert coerce(2, 3) == 3
    assert coerce(10, 11) == 11
    assert coerce(1, 3) == 3
