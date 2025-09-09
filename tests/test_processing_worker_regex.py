import runpy
from pathlib import Path
import spacy
import pytest

BASE_DIR = Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna"
MODULE = runpy.run_path(str(BASE_DIR / "gui" / "processing_worker.py"))
extract_info_from_text = MODULE["extract_info_from_text"]

class DummyExtractor:
    def extract_info(self, text):
        return {
            "data": "",
            "nadawca_odbiorca": "",
            "w_sprawie": "",
            "numer_dokumentu": "",
            "typ_dokumentu": "",
        }


@pytest.fixture(autouse=True)
def stub_models(monkeypatch):
    module_globals = extract_info_from_text.__globals__
    module_globals["get_nlp_model"] = lambda: spacy.blank("pl")
    module_globals["get_smart_extractor"] = lambda: DummyExtractor()
    yield


def test_regex_date_numeric():
    text = "Dnia 12-05-2024 roku"
    info = extract_info_from_text(text, "test.pdf", "KP")
    assert info["data"] == "12-05-2024"


def test_regex_date_words():
    text = "Warszawa, 3 stycznia 2022"
    info = extract_info_from_text(text, "test.pdf", "KP")
    assert info["data"].lower() == "3 stycznia 2022"


def test_regex_sender_recipient():
    text = "Od: Jan Kowalski\nDo: Urząd Miasta"
    info = extract_info_from_text(text, "test.pdf", "KP")
    assert "Jan Kowalski" in info["nadawca_odbiorca"]
    assert "Urząd Miasta" in info["nadawca_odbiorca"]


def test_regex_number_and_signature():
    text = "Numer dokumentu: ABC-123/2024\nSygn. akt: VII K 123/20"
    info = extract_info_from_text(text, "test.pdf", "KP")
    assert info["numer_dokumentu"] == "ABC-123/2024"
    assert info["sygnatura_sprawy"] == "VII K 123/20"
