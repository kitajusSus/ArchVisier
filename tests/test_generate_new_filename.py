import runpy
import types
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna"

spacy_stub = types.ModuleType("spacy")
spacy_stub.load = lambda *a, **k: None
sys.modules["spacy"] = spacy_stub

smart_stub = types.ModuleType("SmartExtractor")
class DummySmartExtractor:
    def extract_info(self, text):
        return {}
smart_stub.SmartExtractor = DummySmartExtractor
sys.modules["SmartExtractor"] = smart_stub

tk_stub = types.ModuleType("tkinter")
tk_stub.messagebox = types.SimpleNamespace(showerror=lambda *a, **k: None)
sys.modules["tkinter"] = tk_stub

MODULE = runpy.run_path(str(BASE_DIR / "gui" / "processing_worker.py"))
generate_new_filename = MODULE["generate_new_filename"]

# Cleanup stubs to avoid affecting other tests
sys.modules.pop("spacy", None)
sys.modules.pop("SmartExtractor", None)
sys.modules.pop("tkinter", None)


def test_generate_new_filename_scheme():
    info = {
        "sygnatura_sprawy": "Sygnatura",
        "numer_dokumentu": "123",
        "nadawca_odbiorca": "Ministerstwo",
        "typ_dokumentu": "Umowa",
        "w_sprawie": "w sprawie",
    }
    counters = {}
    assert (
        generate_new_filename(info, "KP", counters)
        == "1_Sygnatura_123-MINISTERSTWO-UMOWA-w-sprawie.pdf"
    )


def test_generate_new_filename_increment():
    info = {
        "sygnatura_sprawy": "Sygnatura",
        "numer_dokumentu": "123",
        "nadawca_odbiorca": "Ministerstwo",
        "typ_dokumentu": "Umowa",
        "w_sprawie": "w sprawie",
    }
    counters = {}
    first = generate_new_filename(info, "KP", counters)
    second = generate_new_filename(info, "KP", counters)
    assert first.startswith("1_")
    assert second.startswith("2_")
