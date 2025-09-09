"""Configure test environment to locate local stub packages."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUBS = ROOT / "tests" / "stubs"

sys.path.extend([str(ROOT), str(ROOT / "python")])
# Prepend stubs so they override real site-packages during tests
sys.path.insert(0, str(STUBS))
