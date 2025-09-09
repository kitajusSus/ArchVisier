from pathlib import Path
import sys

import pytest

spacy = pytest.importorskip("spacy")
EntityRuler = pytest.importorskip("spacy.pipeline").EntityRuler

BASE_DIR = Path(__file__).resolve().parents[1]
SMART_DIR = BASE_DIR / "2_Aplikacja_Glowna" / "SmartExtractor"
sys.path.insert(0, str(SMART_DIR))
from smart_extractor import SmartExtractor


def test_document_type_multilingual():
    extractor = SmartExtractor(nlp_model=None)
    text = "Invoice No. 12345"  # English variant
    info = extractor.extract_info(text)
    assert info["typ_dokumentu"] == "FAKTURA"


def test_ner_fallback_when_rules_fail():
    nlp = spacy.blank("en")
    ruler: EntityRuler = nlp.add_pipe("entity_ruler")
    ruler.add_patterns(
        [
            {"label": "DATA", "pattern": "June 15, 2024"},
            {"label": "ORGANIZACJA", "pattern": "ACME Corp"},
            {"label": "TYTUL_PISMA", "pattern": "Test Document"},
            {"label": "NR_DOKUMENTU", "pattern": "123"},
            {"label": "TYP_DOKUMENTU", "pattern": "Minutes"},
        ]
    )
    extractor = SmartExtractor(nlp_model=nlp)
    text = (
        "ACME Corp\n" "June 15, 2024\n" "Subject: Test Document\n" "Number 123\n" "Minutes of meeting"
    )
    info = extractor.extract_info(text)
    assert info["data"] == "June 15, 2024"
    assert info["typ_dokumentu"] == "Minutes"
