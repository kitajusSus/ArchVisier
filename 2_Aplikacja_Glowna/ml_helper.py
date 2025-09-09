import os
import re
import json
try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - torch not available in tests
    torch = None  # type: ignore
import logging
import gc
from typing import Any, Dict, List, Optional, Union

# bitsandbytes i konfiguracja kwantyzacji są opcjonalne
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore
    BNB_AVAILABLE = True
    bnb_config = BitsAndBytesConfig(load_in_4bit=True)
except Exception:  # pragma: no cover - transformers unavailable
    BNB_AVAILABLE = False
    bnb_config = None
    try:  # provide minimal stubs if transformers itself is missing
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    except Exception:  # pragma: no cover - used only when transformers absent
        class AutoModelForCausalLM:  # type: ignore
            @classmethod
            def from_pretrained(cls, *_, **__):  # pragma: no cover - stub
                raise RuntimeError("transformers not installed")

        class AutoTokenizer:  # type: ignore
            @classmethod
            def from_pretrained(cls, *_, **__):  # pragma: no cover - stub
                raise RuntimeError("transformers not installed")

# Import analizatora kontekstowego
from context_analyzer import ContextAwareDocumentAnalyzer

# Konfiguracja logowania
logger = logging.getLogger(__name__)

# Proste cache modeli i tokenizerów
MODEL_CACHE: Dict[str, Any] = {}
TOKENIZER_CACHE: Dict[str, Any] = {}

# Domyślny prompt do sugerowania poprawek
DEFAULT_CORRECTION_PROMPT = (
    "<|system|>\n"
    "Jesteś ekspertem w analizie dokumentów i korekcie danych. Przeanalizuj podane informacje i zaproponuj poprawki, jeśli zauważysz błędy.\n\n"
    "Masz:\n"
    "1. Wyciągnięte metadane dokumentu, które mogą zawierać błędy\n"
    "2. Fragment oryginalnego tekstu dokumentu\n\n"
    "Twoim zadaniem jest:\n"
    "1. Sprawdzić, czy metadane są poprawne w kontekście oryginalnego tekstu\n"
    "2. Zaproponować poprawki do metadanych, jeśli są nieprawidłowe\n"
    "3. Zwrócić poprawione metadane\n\n"
    "Zwróć szczególną uwagę na:\n"
    "- Poprawność formatu daty (YYYY-MM-DD)\n"
    "- Precyzyjne określenie typu dokumentu\n"
    "- Właściwe zidentyfikowanie nadawcy/odbiorcy\n"
    "- Trafne określenie tematu dokumentu\n\n"
    "Zwróć odpowiedź TYLKO w formacie JSON:\n"
    "{{\n"
    "  \"typ_dokumentu\": \"SKORYGOWANY_TYP\",\n"
    "  \"data\": \"SKORYGOWANA_DATA\",\n"
    "  \"nadawca_odbiorca\": \"SKORYGOWANY_NADAWCA\",\n"
    "  \"temat\": \"SKORYGOWANY_TEMAT\",\n"
    "  \"numer_dokumentu\": \"SKORYGOWANY_NUMER\"\n"
    "}}\n"
    "<|user|>\n"
    "Wyciągnięte metadane:\n"
    "Typ dokumentu: {typ_dokumentu}\n"
    "Data: {data}\n"
    "Nadawca/Odbiorca: {nadawca_odbiorca}\n"
    "Temat: {w_sprawie}\n"
    "Numer dokumentu: {numer_dokumentu}\n\n"
    "Fragment oryginalnego tekstu:\n"
    "{ocr_text}\n"
    "<|assistant|>"
)

class DocumentLLMProcessor:
    """Klasa do inteligentnego przetwarzania treści dokumentów przy użyciu małych LLM"""
    
    AVAILABLE_MODELS = {
        "phi-3-mini": {
            "model_id": "microsoft/phi-3-mini-128k-instruct",
            "context_length": 128000,
            "name": "Microsoft Phi-3 Mini",
            "description": "Mały model generatywny z Microsoft AI (2024)"
        },
        "phi-2": {
            "model_id": "microsoft/phi-2",
            "context_length": 4096,
            "name": "Microsoft Phi-2", 
            "description": "Mniejszy i szybszy model Microsoft, lepszy na CPU (2023)"
        },
        "mistral-tiny": {
            "model_id": "mistralai/Mistral-7B-Instruct-v0.2",
            "context_length": 8192,
            "name": "Mistral 7B Instruct",
            "description": "Dobra równowaga między rozmiarem a wydajnością (2023)"
        }
    }
    
    def __init__(self, selected_model: str = "phi-2", use_quantization: Union[bool, str] = "auto") -> None:
        """Initialize the processor with a chosen LLM model.

        Args:
            selected_model: Key of the model to load.
            use_quantization: Whether to use 4-bit quantization (``True``/``False``)
                or ``"auto"`` to decide based on environment.
        """
        self.selected_model = selected_model if selected_model in self.AVAILABLE_MODELS else "phi-2"
        self.model_info = self.AVAILABLE_MODELS[self.selected_model]
        
        # Sprawdź zarówno nowy format ścieżki (llm_model_phi-2), jak i stary (llm_model)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_dir = os.path.join(base_dir, f"llm_model_{self.selected_model}")
        
        # Dla kompatybilności wstecznej - sprawdzenie starej lokalizacji dla phi-3-mini
        if selected_model == "phi-3-mini" and not os.path.exists(self.model_dir):
            legacy_dir = os.path.join(base_dir, "llm_model")
            if os.path.exists(legacy_dir):
                logger.info(f"Używanie modelu z lokalizacji starego typu: {legacy_dir}")
                self.model_dir = legacy_dir
        
        self.model_id = self.model_info["model_id"]
        self.model = None
        self.tokenizer = None
        if torch and getattr(torch, "cuda", None):
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = "cpu"
        # czy używać kwantyzacji: True/False/"auto"
        self.use_quantization = use_quantization
        self.loaded = False

        # Załaduj konfigurację promptów
        prompts_path = os.path.join(base_dir, "prompts.json")
        try:
            with open(prompts_path, "r", encoding="utf-8") as f:
                self.prompts = json.load(f)
        except Exception:
            self.prompts = {}

        # Inicjalizacja analizatora kontekstowego
        self.context_analyzer = ContextAwareDocumentAnalyzer(prompts=self.prompts)

        logger.info(f"Inicjalizacja asystenta LLM - model: {self.model_info['name']} (urządzenie: {self.device})")
    
    def is_model_downloaded(self) -> bool:
        """Check whether model files are present on disk."""
        required_files = ["config.json", "tokenizer.json", "tokenizer_config.json"]
        return os.path.exists(self.model_dir) and all(os.path.exists(os.path.join(self.model_dir, f)) for f in required_files)
        
    def load_model(self) -> bool:
        """Load the LLM into memory with CPU/GPU optimisations."""
        try:
            if torch is None:
                logger.warning("Torch not available; skipping model loading")
                return False
            if self.loaded:
                return True

            cache_key = f"{self.model_id}_{self.device}_{self.use_quantization}"
            if cache_key in MODEL_CACHE and cache_key in TOKENIZER_CACHE:
                self.model = MODEL_CACHE[cache_key]
                self.tokenizer = TOKENIZER_CACHE[cache_key]
                self.loaded = True
                logger.info(f"Model {self.model_info['name']} załadowany z cache")
                return True
                
            if not self.is_model_downloaded():
                logger.warning(f"Model {self.model_info['name']} nie jest pobrany. Należy najpierw go pobrać.")
                return False
            
            logger.info(f"Ładowanie modelu {self.model_info['name']}...")
            
            # Wymuś odzyskanie pamięci
            gc.collect()
            if torch and getattr(torch, "cuda", None):
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            # Załaduj tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)

            # Konfiguracja ładowania modelu
            load_kwargs = {
                "trust_remote_code": True,
                "rope_scaling": None,
                "device_map": "auto"
            }
            
            # Optymalizacje dla CPU (2025)
            if self.device == "cpu":
                # W 2025 roku mamy lepszą obsługę CPU przez modele
                load_kwargs.update({
                    "torch_dtype": torch.float32,
                    "low_cpu_mem_usage": True,
                    "use_flash_attention_2": False
                })
                
                # Sprawdź dostępną pamięć systemową i zastosuj dodatkowe optymalizacje jeśli potrzeba
                try:
                    import psutil
                    available_ram = psutil.virtual_memory().available / (1024**3)  # GB
                    if available_ram < 8.0:
                        # Dla systemów z małą ilością pamięci
                        logger.warning(f"Mało dostępnej pamięci: {available_ram:.1f} GB. Zastosowano dodatkowe optymalizacje.")
                        load_kwargs["max_memory"] = {0: f"{int(available_ram*0.8)}GB"}
                except ImportError:
                    logger.warning("Nie można zaimportować modułu psutil. Pomijanie optymalizacji pamięci.")
            else:
                # Na GPU używamy standardowych optymalizacji
                load_kwargs["torch_dtype"] = torch.float16
            
            # Określ, czy użyć kwantyzacji
            use_quant = self.use_quantization
            if use_quant == "auto":
                use_quant = BNB_AVAILABLE and self.device == "cuda"

            if use_quant and bnb_config is not None:
                load_kwargs["quantization_config"] = bnb_config

            # Załaduj model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_dir,
                **load_kwargs
            )

            MODEL_CACHE[cache_key] = self.model
            TOKENIZER_CACHE[cache_key] = self.tokenizer

            logger.info(f"Model {self.model_info['name']} załadowany pomyślnie!")
            self.loaded = True
            return True
        except Exception as e:
            logger.error(f"Błąd ładowania modelu {self.model_info['name']}: {e}")
            return False
    
    def extract_smart_metadata(self, text: str, filename: str = "") -> Optional[Dict[str, str]]:
        """Use the LLM to extract document metadata.

        Args:
            text: OCR text of the document.
            filename: Optional original filename for context.

        Returns:
            Dictionary with extracted metadata or ``None`` on failure.
        """
        if not self.loaded and not self.load_model():
            logger.error("Nie można użyć asystenta LLM - model nie jest załadowany")
            return None
        
        # Użyj analizatora kontekstowego do wygenerowania ulepszonego promptu
        prompt = self.context_analyzer.generate_enhanced_prompt(text, filename)

        try:
            # Przetwórz przez model LLM
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generowanie odpowiedzi z kontrolą parametrów
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_new_tokens=500,
                    temperature=0.2,  # Niska temperatura dla bardziej deterministycznych odpowiedzi
                    top_p=0.95,
                    do_sample=True
                )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Wyodrębnij część odpowiedzi asystenta (po <|assistant|>)
            assistant_response = response.split("<|assistant|>")[-1].strip()
            logger.info(f"Model odpowiedział: {assistant_response[:100]}...")
            
            # Wyodrębnij JSON z odpowiedzi
            try:
                json_pattern = re.search(r'(\{.*\})', assistant_response, re.DOTALL)
                if json_pattern:
                    json_text = json_pattern.group(1)
                    json_text = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', json_text)
                    metadata = json.loads(json_text)
                else:
                    metadata = json.loads(assistant_response)

                if isinstance(metadata, dict):
                    if 'temat' in metadata and 'w_sprawie' not in metadata:
                        metadata['w_sprawie'] = metadata.pop('temat')

                    if not self.validate_metadata(metadata):
                        logger.error("Walidacja metadanych nie powiodła się")
                        return None

                    logger.info("Pomyślnie wyodrębniono metadane z dokumentu")

                    self.context_analyzer.add_document_to_memory(text, metadata)
                    metadata = self.context_analyzer.apply_contextual_corrections(metadata, text)

                    score = self.calculate_quality_score(metadata)
                    logger.info(f"Wynik jakości ({self.model_info['name']}): {score:.2f}")
                    return metadata
                else:
                    logger.error("Zwrócone dane nie są słownikiem")
                    return None
            except json.JSONDecodeError as je:
                logger.error(f"Błąd parsowania JSON: {je}")
                return None

        except Exception as e:
            logger.error(f"Błąd podczas analizy LLM: {e}")
            return None

    def validate_metadata(self, metadata: Dict[str, str]) -> bool:
        """Validate structure and format of extracted metadata."""
        pattern_date = r"^\d{4}-\d{2}-\d{2}$"
        for key in ["typ_dokumentu", "data", "nadawca_odbiorca", "w_sprawie", "numer_dokumentu"]:
            value = metadata.get(key, "")
            if not isinstance(value, str):
                logger.warning(f"Pole {key} ma nieprawidłowy typ")
                return False
            if key == "data" and value and not re.match(pattern_date, value):
                logger.warning(f"Niepoprawny format daty: {value}")
                return False
        return True

    def calculate_quality_score(self, metadata: Dict[str, str]) -> float:
        """Return ratio of filled metadata fields."""
        keys = ["typ_dokumentu", "data", "nadawca_odbiorca", "w_sprawie", "numer_dokumentu"]
        filled = sum(1 for k in keys if metadata.get(k))
        return filled / len(keys)

    def suggest_corrections(self, ocr_text: str, extracted_info: Dict[str, str]) -> Dict[str, str]:
        """Use the LLM to suggest corrections for extracted metadata."""
        if not self.loaded and not self.load_model():
            return extracted_info
            
        # Zachowaj kopię oryginalnych informacji przed poprawkami
        original_info = extracted_info.copy()

        template = self.prompts.get("correction_prompt", DEFAULT_CORRECTION_PROMPT)
        prompt = template.format(
            typ_dokumentu=extracted_info.get('typ_dokumentu', ''),
            data=extracted_info.get('data', ''),
            nadawca_odbiorca=extracted_info.get('nadawca_odbiorca', ''),
            w_sprawie=extracted_info.get('w_sprawie', ''),
            numer_dokumentu=extracted_info.get('numer_dokumentu', ''),
            ocr_text=ocr_text[:800]
        )

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_new_tokens=500,
                    temperature=0.1,
                    top_p=0.9,
                    do_sample=False
                )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            assistant_response = response.split("<|assistant|>")[-1].strip()
            
            # Parsuj odpowiedź JSON
            json_pattern = re.search(r'(\{.*\})', assistant_response, re.DOTALL)
            if json_pattern:
                json_text = json_pattern.group(1)
                json_text = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', json_text)
                corrections = json.loads(json_text)
                
                # Przenieś poprawki do oryginalnego słownika
                if isinstance(corrections, dict):
                    if corrections.get('typ_dokumentu'):
                        extracted_info['typ_dokumentu'] = corrections['typ_dokumentu']
                    if corrections.get('data'):
                        extracted_info['data'] = corrections['data']
                    if corrections.get('nadawca_odbiorca'):
                        extracted_info['nadawca_odbiorca'] = corrections['nadawca_odbiorca']
                    if corrections.get('temat'):
                        extracted_info['w_sprawie'] = corrections['temat']
                    if corrections.get('numer_dokumentu'):
                        extracted_info['numer_dokumentu'] = corrections['numer_dokumentu']
                    
                    logger.info("Zastosowano poprawki sugerowane przez model LLM")
                    
                    # Zapisz poprawkę do pamięci kontekstowej
                    self.context_analyzer.add_correction_to_memory(original_info, extracted_info, ocr_text)
            
            return extracted_info
        except Exception as e:
            logger.error(f"Błąd podczas sugerowania poprawek: {e}")
            return extracted_info
            
    def get_available_models(self) -> List[str]:
        """Return names of locally available LLM models."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        available: List[str] = []
        
        # Sprawdź standardowe modele
        for model_key in self.AVAILABLE_MODELS.keys():
            model_dir = os.path.join(base_dir, f"llm_model_{model_key}")
            if os.path.exists(model_dir) and os.path.exists(os.path.join(model_dir, "config.json")):
                available.append(model_key)
        
        # Sprawdź starą lokalizację
        legacy_dir = os.path.join(base_dir, "llm_model")
        if os.path.exists(legacy_dir) and os.path.exists(os.path.join(legacy_dir, "config.json")):
            if "phi-3-mini" not in available:  # Dodaj tylko jeśli nie ma już w nowym formacie
                available.append("phi-3-mini")
        
        return available

