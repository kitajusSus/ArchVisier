import re
import logging
from datetime import datetime
from typing import Any, Dict

try:
    import spacy
except Exception:  # pragma: no cover - spaCy is optional
    spacy = None

logger = logging.getLogger(__name__)

class SmartExtractor:
    """
    Klasa do inteligentnej ekstrakcji danych z tekstu przy użyciu prostych metod opartych na regułach.
    Służy jako rozwiązanie uzupełniające lub awaryjne gdy NER lub LLM nie są dostępne.
    """
    
    def __init__(self, nlp_model: Any = None) -> None:
        """Create a new smart extractor instance.

        Args:
            nlp_model: Optional spaCy model used for fallback NER.
        """
        # Słowniki typów dokumentów do rozpoznawania (z wariantami wielojęzycznymi)
        self.document_types = {
            "umowa": "UMOWA",
            "porozumienie": "POROZUMIENIE",
            "aneks": "ANEKS",
            "appendix": "ANEKS",
            "agreement": "UMOWA",
            "contract": "UMOWA",
            "protokół": "PROTOKÓŁ",
            "protokol": "PROTOKÓŁ",
            "protocol": "PROTOKÓŁ",
            "faktura": "FAKTURA",
            "invoice": "FAKTURA",
            "rechnung": "FAKTURA",
            "rachunek": "RACHUNEK",
            "bill": "RACHUNEK",
            "paragon": "PARAGON",
            "wezwanie": "WEZWANIE",
            "zaświadczenie": "ZAŚWIADCZENIE",
            "zaswiadczenie": "ZAŚWIADCZENIE",
            "certificate": "ZAŚWIADCZENIE",
            "decyzja": "DECYZJA",
            "decision": "DECYZJA",
            "postanowienie": "POSTANOWIENIE",
            "resolution": "UCHWAŁA",
            "uchwała": "UCHWAŁA",
            "request": "WNIOSEK",
            "wniosek": "WNIOSEK",
            "appeal": "ODWOŁANIE",
            "odwołanie": "ODWOŁANIE",
            "odwolanie": "ODWOŁANIE",
            "complaint": "SKARGA",
            "skarga": "SKARGA",
            "letter": "PISMO",
            "pismo": "PISMO",
            "memo": "NOTATKA",
            "notatka": "NOTATKA",
            "report": "SPRAWOZDANIE",
            "sprawozdanie": "SPRAWOZDANIE",
            "statement": "OŚWIADCZENIE",
            "oświadczenie": "OŚWIADCZENIE",
            "oswiadczenie": "OŚWIADCZENIE",
        }

        # Inicjalizacja wzorców dla różnych typów informacji
        self._init_patterns()

        # Opcjonalny model spaCy do fallbacku NER
        self.nlp = nlp_model
        if self.nlp is None and spacy is not None:
            try:
                self.nlp = spacy.load("pl_core_news_sm")
            except Exception:
                logger.warning("Nie udało się załadować modelu spaCy. Fallback NER będzie niedostępny.")
                self.nlp = None
        
    def _init_patterns(self) -> None:
        """Initialize regular expressions for various pieces of information."""
        # Wzorce dat
        self.date_patterns = [
            re.compile(r"\b(\d{4})[/\.\-](\d{1,2})[/\.\-](\d{1,2})\b"),
            re.compile(r"\b(\d{1,2})[/\.\-](\d{1,2})[/\.\-](\d{4})\b"),
            re.compile(r"\b(\d{1,2})[ \.](?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)[ \.](\d{4})\b", re.IGNORECASE),
            re.compile(r"\b(\d{1,2})[ \.](?:styczeń|luty|marzec|kwiecień|maj|czerwiec|lipiec|sierpień|wrzesień|październik|listopad|grudzień)[ \.](\d{4})\b", re.IGNORECASE),
            re.compile(r"\b(\d{1,2})[ \.](?:january|february|march|april|may|june|july|august|september|october|november|december)[ \.](\d{4})\b", re.IGNORECASE),
        ]

        # Wzorce numerów dokumentów
        self.document_number_patterns = [
            re.compile(r"\b(?:nr|numer|znak|sygn\.?|l\.dz\.?)[ :]*([A-Za-z0-9\.\-/]+)\b", re.IGNORECASE),
            re.compile(r"\b(?:no\.|number)[ :]*([A-Za-z0-9\.\-/]+)\b", re.IGNORECASE),
            re.compile(r"\bFV[ :]*([A-Za-z0-9\.\-/]+)\b", re.IGNORECASE),
            re.compile(r"\bfaktura[ :]*(?:nr|numer|no\.|number)?[ :]*([A-Za-z0-9\.\-/]+)\b", re.IGNORECASE),
            re.compile(r"\binvoice[ :]*(?:nr|numer|no\.|number)?[ :]*([A-Za-z0-9\.\-/]+)\b", re.IGNORECASE),
            re.compile(r"\bumowa[ :]*(?:nr|numer|no\.|number)?[ :]*([A-Za-z0-9\.\-/]+)\b", re.IGNORECASE),
        ]

        # Wzorce sygnatur sądowych
        self.court_signature_patterns = [
            re.compile(r"\b(?:sygn\.?|sygnatura)[ :]*(?:akt)?[ :]*([A-Za-z0-9\.\-/]+)\b", re.IGNORECASE),
            re.compile(r"\b([A-Z]{2,4}[ /][A-Za-z0-9]{1,4}[ /][0-9]{1,5}[ /][0-9]{1,5})\b"),
        ]

        # Wzorce nadawcy/odbiorcy
        self.sender_recipient_patterns = [
            re.compile(r"(?:od|nadawca|wykonawca|zleceniobiorca|usługodawca)[:\s]+([A-ZŻŹĆĄŚĘŁÓŃ][^\.]{5,50})", re.IGNORECASE),
            re.compile(r"(?:do|odbiorca|zamawiający|zleceniodawca|usługobiorca)[:\s]+([A-ZŻŹĆĄŚĘŁÓŃ][^\.]{5,50})", re.IGNORECASE),
            re.compile(r"\b([A-ZŻŹĆĄŚĘŁÓŃ][A-ZŻŹĆĄŚĘŁÓŃ\s]{2,}(?:SP\.|SP\.\sZ\sO\.O\.|S\.A\.|Z\sO\.O\.))", re.IGNORECASE),
            re.compile(r"\b((?:spółka|przedsiębiorstwo|firma|zakład|centrum|biuro)[^\n\.]{5,50})", re.IGNORECASE),
        ]
        self.address_pattern = re.compile(r"(?:ul\.|ulica|al\.|aleja)[^\n,]{2,30},[^\n]{2,30}\d{2}-\d{3}", re.IGNORECASE)

        # Wzorce tematu pisma
        self.subject_patterns = [
            re.compile(r"(?:dotyczy|dot\.|w sprawie|temat|przedmiot|sprawa)[:\s]+([^\n\.]{10,100})", re.IGNORECASE),
            re.compile(r"(?:sprawa|dot\.):[^\n\.]{5,100}", re.IGNORECASE),
            re.compile(r"(?:subject|regarding|re)[:\s]+([^\n\.]{5,100})", re.IGNORECASE),
        ]
        
    def _find_document_type(self, text: str) -> str:
        """Return document type based on keywords."""
        text_lower = text.lower()
        # Sprawdź pierwsze 500 znaków (nagłówek dokumentu)
        header = text_lower[:500] if len(text_lower) > 500 else text_lower
        
        # Sprawdź najpierw wzorce w nagłówku
        for keyword, doc_type in self.document_types.items():
            if keyword in header:
                # Zweryfikuj, czy słowo występuje samodzielnie, a nie jako część innego słowa
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, header):
                    return doc_type
        
        # Jeśli nie znaleziono w nagłówku, sprawdź cały tekst
        for keyword, doc_type in self.document_types.items():
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                return doc_type
                
        return ""
    
    def _extract_date(self, text: str) -> str:
        """Extract a date from the text."""
        for pattern in self.date_patterns:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # YYYY-MM-DD lub DD-MM-YYYY
                    if len(groups[0]) == 4:  # YYYY-MM-DD
                        return f"{groups[0]}-{int(groups[1]):02d}-{int(groups[2]):02d}"
                    else:  # DD-MM-YYYY
                        return f"{groups[2]}-{int(groups[1]):02d}-{int(groups[0]):02d}"
                elif len(groups) == 2:  # Format słowny, np. 10 maja 2023
                    month_names = {
                        'stycznia': 1, 'lutego': 2, 'marca': 3, 'kwietnia': 4, 'maja': 5,
                        'czerwca': 6, 'lipca': 7, 'sierpnia': 8, 'września': 9,
                        'października': 10, 'listopada': 11, 'grudnia': 12,
                        'styczeń': 1, 'luty': 2, 'marzec': 3, 'kwiecień': 4, 'maj': 5,
                        'czerwiec': 6, 'lipiec': 7, 'sierpień': 8, 'wrzesień': 9,
                        'październik': 10, 'listopad': 11, 'grudzień': 12,
                        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5,
                        'june': 6, 'july': 7, 'august': 8, 'september': 9,
                        'october': 10, 'november': 11, 'december': 12
                    }
                    day = int(groups[0])
                    # Znajdź nazwę miesiąca w dopasowaniu
                    for month_name, month_num in month_names.items():
                        if month_name in match.group(0):
                            month = month_num
                            year = int(groups[1])
                            return f"{year}-{month:02d}-{day:02d}"
        return ""
    
    def _extract_document_number(self, text: str) -> str:
        """Extract document number from text."""
        for pattern in self.document_number_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_sender_recipient(self, text: str) -> str:
        """Extract sender or recipient using simple patterns."""
        # Sprawdź wzorce dla nadawcy/odbiorcy
        for pattern in self.sender_recipient_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()

        # Sprawdź dane adresowe (często zawierają nazwę firmy)
        address_match = self.address_pattern.search(text)
        if address_match:
            # Sprawdź linię przed adresem - często zawiera nazwę firmy
            text_before = text[:address_match.start()].strip()
            lines = text_before.split('\n')
            if lines:
                last_line = lines[-1].strip()
                if len(last_line) > 3 and len(last_line) < 60:
                    return last_line
        
        return ""
    
    def _extract_subject(self, text: str) -> str:
        """Extract the subject of the document."""
        for pattern in self.subject_patterns:
            match = pattern.search(text)
            if match:
                subject = match.group(0).replace('dotyczy:', '').replace('dot.:', '').replace('w sprawie:', '').replace('temat:', '').replace('przedmiot:', '').strip()
                return subject[:100]  # Ogranicz długość
        
        # Jeśli nie znaleziono tematu, spróbuj znaleźć treść po tytule dokumentu
        if self._find_document_type(text):
            doc_type = self._find_document_type(text).lower()
            pattern = rf'{doc_type}[:\s]+([^\n\.]{10,100})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return ""
    
    def extract_info(self, text: str) -> Dict[str, str]:
        """Extract all relevant metadata from ``text``.

        Args:
            text: Document text to analyse.

        Returns:
            Dictionary with extracted information.
        """
        # Jeśli tekst jest pusty, zwróć pusty słownik
        if not text:
            return {
                "data": "",
                "nadawca_odbiorca": "",
                "w_sprawie": "",
                "numer_dokumentu": "",
                "typ_dokumentu": ""
            }
            
        try:
            # Znajdź datę
            date = self._extract_date(text)

            # Znajdź typ dokumentu
            doc_type = self._find_document_type(text)

            # Znajdź numer dokumentu
            doc_number = self._extract_document_number(text)

            # Znajdź nadawcę/odbiorcę
            sender_recipient = self._extract_sender_recipient(text)

            # Znajdź temat (w sprawie)
            subject = self._extract_subject(text)

            # Fallback do modelu NER jeśli pewne pola są puste
            if self.nlp:
                doc = self.nlp(text)
                entities = {ent.label_.upper(): [] for ent in doc.ents}
                for ent in doc.ents:
                    entities[ent.label_.upper()].append(ent.text.replace("\n", " ").strip())

                if not date:
                    date = " ".join(entities.get("DATA", []))
                if not sender_recipient:
                    sender_recipient = " ".join(entities.get("ORGANIZACJA", []))
                if not subject:
                    subject = " ".join(entities.get("TYTUL_PISMA", []))
                if not doc_number:
                    doc_number = " ".join(entities.get("NR_DOKUMENTU", []))
                if not doc_type:
                    doc_type = " ".join(entities.get("TYP_DOKUMENTU", []))

            return {
                "data": date,
                "nadawca_odbiorca": sender_recipient,
                "w_sprawie": subject,
                "numer_dokumentu": doc_number,
                "typ_dokumentu": doc_type
            }
            
        except Exception as e:
            logger.error(f"Błąd podczas ekstrakcji informacji z tekstu: {e}")
            # Zwróć pusty słownik w przypadku błędu
            return {
                "data": "",
                "nadawca_odbiorca": "",
                "w_sprawie": "",
                "numer_dokumentu": "",
                "typ_dokumentu": ""
            }

