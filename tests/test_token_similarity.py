import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "python"))
from token_similarity import token_similarity as c_token_similarity

try:
    from zig_token_similarity import token_similarity as zig_token_similarity
    HAVE_ZIG = True
except (OSError, FileNotFoundError):
    HAVE_ZIG = False


def test_c_token_similarity():
    assert c_token_similarity("one two", "one three") == pytest.approx(0.333333, rel=1e-6)


@pytest.mark.skipif(not HAVE_ZIG, reason="Zig library not built")
def test_zig_token_similarity():
    assert zig_token_similarity("one two", "one three") == pytest.approx(0.333333, rel=1e-6)
