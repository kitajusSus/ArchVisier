from pathlib import Path

import pytest
import runpy

# Load module dynamically since package name starts with a digit
MODULE = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna" / "context_analyzer.py")
)
ContextAwareDocumentAnalyzer = MODULE["ContextAwareDocumentAnalyzer"]
fast_cosine = MODULE["fast_cosine"]
SentenceTransformer = MODULE["SentenceTransformer"]


@pytest.fixture(scope="module")
def embedding_model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


@pytest.fixture
def analyzer(tmp_path, embedding_model):
    memory_file = tmp_path / "memory.json"
    return ContextAwareDocumentAnalyzer(
        memory_file=str(memory_file), embedding_model=embedding_model
    )


def test_context_analyzer_add_and_find(analyzer):
    analyzer.add_document_to_memory("dokument o jabłkach", {"id": 1})
    analyzer.add_document_to_memory("dokument o pomarańczach", {"id": 2})
    results = analyzer.find_similar_documents("dokument o jabłkach", top_n=1)
    assert results
    assert results[0]["document"]["metadata"]["id"] == 1


def test_context_analyzer_corrections(analyzer):
    original = {"pole": "stara"}
    corrected = {"pole": "nowa"}
    analyzer.add_correction_to_memory(original, corrected, "tekst przykładowy")
    found = analyzer.find_relevant_corrections("tekst przykładowy", "pole")
    assert found == "nowa"


def test_context_analyzer_fuzzy_match(analyzer):
    original = {"pole": "stara"}
    corrected = {"pole": "nowa"}
    analyzer.add_correction_to_memory(original, corrected, "dokument o jabłkach i gruszkach")

    # Similar text should be matched
    similar = analyzer.find_relevant_corrections(
        "dokument o jablkach i gruszkach", "pole"
    )
    assert similar == "nowa"

    # Dissimilar text should not meet threshold
    dissimilar = analyzer.find_relevant_corrections("zupełnie inny tekst", "pole")
    assert dissimilar is None


def test_embedding_model_loaded(analyzer):
    vector = analyzer.embedding_model.encode(["Hello world"])[0]
    assert len(vector) == analyzer.embedding_model.get_sentence_embedding_dimension()


def test_semantic_similarity_with_embeddings(analyzer):
    analyzer.add_document_to_memory("I enjoy walking with my dog", {"id": 1})
    analyzer.add_document_to_memory("The city bus was late today", {"id": 2})
    results = analyzer.find_similar_documents(
        "I love taking my dog for a walk", top_n=1
    )
    assert results
    assert results[0]["document"]["metadata"]["id"] == 1


