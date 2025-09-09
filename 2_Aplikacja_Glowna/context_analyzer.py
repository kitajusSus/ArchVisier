import os
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import logging
import random

try:
    # Prefer szybkie i dokładne porównanie z biblioteki rapidfuzz
    from rapidfuzz.distance import JaroWinkler

    def fuzzy_similarity(a: str, b: str) -> float:
        """Calculate normalized similarity using Jaro-Winkler from rapidfuzz."""
        return JaroWinkler.normalized_similarity(a, b)
except Exception:
    try:  # Fallback do biblioteki python-Levenshtein
        import Levenshtein

        def fuzzy_similarity(a: str, b: str) -> float:
            return Levenshtein.ratio(a, b)
    except Exception:  # Ostateczny prosty fallback
        def fuzzy_similarity(a: str, b: str) -> float:
            if a == b:
                return 1.0
            if not a or not b:
                return 0.0
            m, n = len(a), len(b)
            dp = list(range(n + 1))
            for i in range(1, m + 1):
                prev = i - 1
                dp[0] = i
                for j in range(1, n + 1):
                    cur = dp[j]
                    if a[i - 1] == b[j - 1]:
                        dp[j] = prev
                    else:
                        dp[j] = 1 + min(prev, dp[j], dp[j - 1])
                    prev = cur
            distance = dp[n]
            return 1 - distance / max(m, n)

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - fallback stub
    class SentenceTransformer:  # type: ignore[override]
        def __init__(self, model: str | None = None) -> None:
            self._dim = 3

        def encode(self, texts, convert_to_numpy: bool = False):
            if isinstance(texts, str):
                texts = [texts]
            vectors = []
            for text in texts:
                rng = random.Random(sum(ord(ch) for ch in text))
                vec = [rng.random() for _ in range(self._dim)]
                vectors.append(vec)
            return vectors

        def get_sentence_embedding_dimension(self) -> int:
            return self._dim

# Opcjonalna szybka implementacja podobieństwa kosinusowego
try:
    from fast_similarity import cosine_similarity as fast_cosine
except Exception:  # pragma: no cover - pure Python fallback
    def fast_cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        return 0.0 if na == 0.0 or nb == 0.0 else dot / (na * nb)

# Konfiguracja logowania
logger = logging.getLogger(__name__)

class ContextAwareDocumentAnalyzer:
    """System analizy dokumentów z uwzględnieniem kontekstu i historii poprawek"""

    SIMILARITY_THRESHOLD = 0.7

    DEFAULT_METADATA_PROMPT = (
        "<|system|>\n"
        "Jesteś ekspertem w analizie dokumentów prawnych i biznesowych. Twoim zadaniem jest szczegółowa analiza fragmentu dokumentu i wyciągnięcie z niego najważniejszych metadanych.\n\n"
        "Przeanalizuj dokument i wyciągnij następujące informacje:\n"
        "1. TYP DOKUMENTU (np. umowa, faktura, protokół, porozumienie, odbiór, aneks, wezwanie, oświadczenie)\n"
        "2. DATA dokumentu (w formacie YYYY-MM-DD kiedy został wystawiony lub podpisany, jeśli jest podana w różnych formatach, wybierz najbardziej prawdopodobną)\n"
        "3. NADAWCA/ODBIORCA (nazwa firmy lub instytucji lub osoby fizycznej, która wystawia lub otrzymuje dokument)\n"
        "4. TEMAT dokumentu (krótki opis czego dotyczy)\n"
        "5. NUMER DOKUMENTU (np. nr umowy, nr faktury, sygnatura) jeśli występuje"
        "{similar_examples}\n\n"
        "Zwróć wyniki WYŁĄCZNIE w formacie JSON, nic poza tym. Format:\n"
        "{{\n"
        "  \"typ_dokumentu\": \"OKREŚLONY_TYP\",\n"
        "  \"data\": \"YYYY-MM-DD\",\n"
        "  \"nadawca_odbiorca\": \"NAZWA\",\n"
        "  \"temat\": \"OPIS\",\n"
        "  \"numer_dokumentu\": \"NR/SYG\"\n"
        "}}\n\n"
        "Analizując dokument:\n"
        "- Zwracaj szczególną uwagę na kontekst i znaczenie treści\n"
        "- Zrozum cel i charakter dokumentu\n"
        "- Postaraj się zidentyfikować kluczowe informacje nawet jeśli są sformułowane nietypowo\n"
        "- Znajdź datę w różnych formatach i przekształć ją do formatu YYYY-MM-DD\n"
        "- Określ typ dokumentu na podstawie jego struktury i treści\n"
        "- Jeśli dokument zawiera wiele dat, wybierz tę, która najprawdopodobniej jest datą dokumentu\n\n"
        "Jeśli jakaś informacja nie występuje w tekście, użyj pustego ciągu \"\" dla danego pola.\n"
        "<|user|>\n"
        "{document_text}\n"
        "<|assistant|>"
    )

    def __init__(
        self,
        memory_file: Optional[str] = None,
        prompts: Optional[Dict[str, str]] = None,
        embedding_model: Optional[SentenceTransformer] = None,
    ) -> None:
        """Initialize the contextual analyzer.

        Args:
            memory_file: Optional path to a JSON file with stored context.
            prompts: Optional mapping with custom prompt templates.
            embedding_model: Optional preloaded SentenceTransformer instance.
        """
        if memory_file is None:
            # Domyślnie zapisujemy w tym samym katalogu co aplikację
            app_dir = os.path.dirname(os.path.abspath(__file__))
            self.memory_file = os.path.join(app_dir, "document_context_memory.json")
        else:
            self.memory_file = memory_file

        self.prompts = prompts or {}

        self.document_memory = []  # Przechowuje analizowane dokumenty
        self.corrections_memory = []  # Przechowuje poprawki użytkownika
        # Model embeddingów do porównywania dokumentów
        self.embedding_model = embedding_model or SentenceTransformer(
            'sentence-transformers/all-MiniLM-L6-v2'
        )

        # Załaduj istniejącą pamięć, jeśli istnieje
        self.load_memory()
        
    def load_memory(self) -> None:
        """Load stored contextual data from ``memory_file``."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.document_memory = data.get('documents', [])
                    self.corrections_memory = data.get('corrections', [])
                logger.info(
                    f"Załadowano pamięć kontekstową: {len(self.document_memory)} dokumentów i {len(self.corrections_memory)} poprawek"
                )
            except Exception as e:
                logger.error(f"Błąd ładowania pamięci kontekstowej: {e}")
    
    def save_memory(self) -> None:
        """Persist contextual data to ``memory_file``."""
        data = {
            'documents': self.document_memory[-100:],  # Zachowaj tylko ostatnie 100 dokumentów
            'corrections': self.corrections_memory[-200:]  # Zachowaj tylko ostatnie 200 poprawek
        }
        
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Zapisano pamięć kontekstową: {len(self.document_memory)} dokumentów i {len(self.corrections_memory)} poprawek")
        except Exception as e:
            logger.error(f"Błąd zapisywania pamięci kontekstowej: {e}")
    
    def add_document_to_memory(self, text_fragment: str, metadata: Dict[str, str]) -> bool:
        """Store a document fragment and its metadata in memory.

        Args:
            text_fragment: Text excerpt from the document.
            metadata: Extracted metadata dictionary.

        Returns:
            ``True`` if the document was stored.
        """
        self.document_memory.append({
            'timestamp': datetime.now().isoformat(),
            'text_fragment': text_fragment[:2000],  # Ogranicz do 2000 znaków
            'metadata': metadata.copy()
        })
        
        self.save_memory()
        return True
    
    def add_correction_to_memory(
        self,
        original_metadata: Dict[str, str],
        corrected_metadata: Dict[str, str],
        text_fragment: str,
    ) -> bool:
        """Record a user-provided correction for later suggestions.

        Args:
            original_metadata: Metadata before modification.
            corrected_metadata: Metadata after user correction.
            text_fragment: Document fragment used for context.

        Returns:
            ``True`` if the correction was recorded.
        """
        # Znajdź, które pola zostały poprawione
        changed_fields = {}
        for key in corrected_metadata:
            if key in original_metadata and original_metadata[key] != corrected_metadata[key]:
                # Ignoruj puste wartości
                if original_metadata[key] or corrected_metadata[key]:
                    changed_fields[key] = {
                        'original': original_metadata[key],
                        'corrected': corrected_metadata[key]
                    }
        
        if changed_fields:
            self.corrections_memory.append({
                'timestamp': datetime.now().isoformat(),
                'text_fragment': text_fragment[:1000],  # Mały fragment dla kontekstu
                'changed_fields': changed_fields
            })
            self.save_memory()
            logger.info(f"Zapisano poprawkę użytkownika dla pól: {list(changed_fields.keys())}")
            return True
        return False
    
    def find_similar_documents(self, text: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """Find documents in memory similar to the provided text."""
        if not self.document_memory or len(self.document_memory) < 2:
            return []
            
        # Przygotuj wektor dla nowego tekstu
        try:
            all_texts = [doc['text_fragment'] for doc in self.document_memory]
            all_texts.append(text[:2000])  # Dodaj nowy tekst

            # Oblicz embeddingi dla wszystkich tekstów
            embeddings = self.embedding_model.encode(all_texts)

            new_doc_vector = embeddings[-1]
            existing_docs_vectors = embeddings[:-1]

            similarities = [
                fast_cosine(new_doc_vector, vec) for vec in existing_docs_vectors
            ]

            similar_indices = sorted(
                range(len(similarities)), key=lambda i: similarities[i], reverse=True
            )[:top_n]
            
            similar_docs = []
            for idx in similar_indices:
                if similarities[idx] > 0.2:  # Minimalny próg podobieństwa
                    similar_docs.append({
                        'document': self.document_memory[idx],
                        'similarity': float(similarities[idx])
                    })
            
            return similar_docs
        except Exception as e:
            logger.error(f"Błąd podczas szukania podobnych dokumentów: {e}")
            return []
    
    def find_relevant_corrections(self, text: str, metadata_key: str) -> Optional[str]:
        """Return a suggested value for ``metadata_key`` based on past corrections."""
        if not self.corrections_memory:
            return None
            
        relevant_corrections = []
        for correction in self.corrections_memory:
            if metadata_key in correction['changed_fields']:
                relevant_corrections.append(correction)
        
        if not relevant_corrections:
            return None
            
        # Znajdź najbardziej podobną poprawkę na podstawie fuzzy match
        max_similarity = -1.0
        most_similar_correction = None

        for correction in relevant_corrections:
            similarity = fuzzy_similarity(correction['text_fragment'], text)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_correction = correction

        if max_similarity >= self.SIMILARITY_THRESHOLD:  # Minimalny próg podobieństwa 70%
            return most_similar_correction['changed_fields'][metadata_key]['corrected']

        return None
    
    def generate_enhanced_prompt(self, text: str, original_filename: str = "") -> str:
        """Generate a prompt for the LLM enriched with contextual examples."""
        similar_docs = self.find_similar_documents(text)

        similar_section = ""
        if similar_docs:
            similar_section += "\n\nDla lepszego zrozumienia kontekstu, oto jak przeanalizowano podobne dokumenty wcześniej:"
            for i, sim_doc in enumerate(similar_docs[:2]):
                doc = sim_doc['document']
                similar_section += f"\n\nPrzykład {i+1} (podobieństwo: {sim_doc['similarity']:.2f}):"
                similar_section += f"\nFragment tekstu: {doc['text_fragment'][:200]}..."
                similar_section += f"\nWynik analizy:"
                similar_section += f"\n- Typ dokumentu: {doc['metadata'].get('typ_dokumentu', 'nie określono')}"
                similar_section += f"\n- Data: {doc['metadata'].get('data', 'nie określono')}"
                similar_section += f"\n- Nadawca/Odbiorca: {doc['metadata'].get('nadawca_odbiorca', 'nie określono')}"
                similar_section += f"\n- Temat: {doc['metadata'].get('w_sprawie', 'nie określono')}"
                if 'numer_dokumentu' in doc['metadata']:
                    similar_section += f"\n- Numer dokumentu: {doc['metadata'].get('numer_dokumentu', '')}"

        template = self.prompts.get("metadata_prompt", self.DEFAULT_METADATA_PROMPT)
        prompt = template.format(similar_examples=similar_section, document_text=text[:1500])
        return prompt
    
    def apply_contextual_corrections(self, extracted_info: Dict[str, str], text: str) -> Dict[str, str]:
        """Apply corrections based on previously stored user adjustments."""
        # Dla każdego pola metadanych
        for key in extracted_info:
            # Jeśli pole jest puste, poszukaj wskazówek w historii poprawek
            if not extracted_info[key] or len(extracted_info[key]) < 3:
                suggested_value = self.find_relevant_corrections(text, key)
                if suggested_value:
                    extracted_info[key] = suggested_value
                    logger.info(f"Zastosowano sugestię z historii poprawek dla pola {key}: {suggested_value}")
        
        return extracted_info

