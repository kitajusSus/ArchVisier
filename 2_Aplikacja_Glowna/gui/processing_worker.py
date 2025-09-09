import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import logging
from functools import lru_cache
import threading
from queue import Queue, Empty

try:  # pragma: no cover - prefer real PySide6 when available
    from PySide6 import QtWidgets, QtCore
except Exception:  # pragma: no cover - fallback used in tests
    class _Dummy:
        def __getattr__(self, name):
            return type(name, (), {})

    QtWidgets = QtCore = _Dummy()
    QtCore.QThread = type(
        "QThread",
        (),
        {
            "__init__": lambda self, *a, **k: None,
            "start": lambda self: None,
            "isRunning": lambda self: False,
            "wait": lambda self: None,
        },
    )


class _DummySignal:  # pragma: no cover - simple stub used in tests
    def __init__(self) -> None:
        self._slots = []

    def connect(self, slot, *args, **kwargs):
        self._slots.append(slot)

    def emit(self, *args, **kwargs):
        for slot in list(self._slots):
            slot(*args, **kwargs)


import spacy
from pdf2image import pdfinfo_from_path
import types
try:  # pragma: no cover - allow running without config module
    import config
    from config import AppSettings
except Exception:  # pragma: no cover - simplified fallback for tests
    class AppSettings:  # type: ignore
        pass

    config = type("config", (), {"SETTINGS": None})()  # minimal namespace
try:  # pragma: no cover - when processing package not available
    from processing import ocr
except Exception:  # pragma: no cover - minimal stub
    ocr = types.SimpleNamespace()

logger = logging.getLogger(__name__)

# --- Konfiguracja Ścieżek (dla trybu normalnego i .exe) ---
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    # W trybie .exe, katalogiem nadrzędnym jest katalog, w którym znajduje się .exe
    app_dir = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = os.path.dirname(base_path)

# Upewnij się, że moduł SmartExtractor jest dostępny w ścieżce
if base_path not in sys.path:
    sys.path.insert(0, base_path)

@lru_cache(maxsize=1)
def get_smart_extractor():
    """Zwraca instancję SmartExtractor lub obiekt zastępczy."""
    try:
        from SmartExtractor import SmartExtractor

        logger.info("Moduł SmartExtractor znaleziony.")
        return SmartExtractor()
    except ImportError:
        logger.warning("Moduł SmartExtractor niedostępny.")

        class DummyExtractor:
            def extract_info(self, text):
                return {
                    "data": "",
                    "nadawca_odbiorca": "",
                    "w_sprawie": "",
                    "numer_dokumentu": "",
                    "typ_dokumentu": "",
                }

        return DummyExtractor()


def show_error(parent: QtWidgets.QWidget | None, title: str, message: str) -> None:
    """Wyświetla krytyczny komunikat o błędzie lub propaguje wyjątek.

    Jeśli przekazano obiekt ``parent``, używa ``QtWidgets.QMessageBox`` do
    wyświetlenia informacji. W przeciwnym razie podnosi ``RuntimeError``,
    aby warstwa GUI mogła przechwycić błąd i obsłużyć go według własnych
    potrzeb.
    """

    if parent is not None:
        QtWidgets.QMessageBox.critical(parent, title, message)
    else:
        raise RuntimeError(f"{title}: {message}")


def load_spacy_model(parent: QtWidgets.QWidget | None = None):
    """Ładuje model NER spaCy z odpowiedniej lokalizacji."""
    custom_model_path = os.path.join(app_dir, "custom_ner_model")
    default_model_path = os.path.join(base_path, "moj_model_ner")

    model_to_load = None
    if os.path.exists(custom_model_path) and os.listdir(custom_model_path):
        logger.info(
            f"Znaleziono niestandardowy model NER. Ładowanie z: {custom_model_path}"
        )
        model_to_load = custom_model_path
    elif os.path.exists(default_model_path) and os.listdir(default_model_path):
        logger.info(
            f"Brak modelu niestandardowego. Ładowanie domyślnego modelu z: {default_model_path}"
        )
        model_to_load = default_model_path

    if model_to_load:
        try:
            return spacy.load(model_to_load)
        except Exception as e:
            logger.error(f"Błąd ładowania modelu NER z '{model_to_load}': {e}")
            show_error(
                parent,
                "Błąd ładowania modelu NER",
                f"Wystąpił błąd podczas ładowania modelu:\n\n{e}",
            )
            return None
    else:
        logger.warning(
            "Nie znaleziono żadnego modelu NER (ani domyślnego, ani niestandardowego)."
        )
        logger.warning(
            "Ładowanie bazowego modelu 'pl_core_news_sm'. Rozpoznawanie encji będzie wyłączone."
        )
        try:
            # Upewnij się, że masz zainstalowany ten model: python -m spacy download pl_core_news_sm
            return spacy.load("pl_core_news_sm")
        except OSError as e:
            show_error(
                parent,
                "Krytyczny błąd - Brak modelu NER",
                (
                    "Nie znaleziono żadnego modelu NER i nie udało się załadować modelu bazowego 'pl_core_news_sm'.\n\n"
                    "Upewnij się, że model domyślny jest spakowany z aplikacją lub wytrenuj nowy model.\n"
                    "Możesz też zainstalować model bazowy komendą:\n"
                    "python -m spacy download pl_core_news_sm"
                ),
            )
            return None



@lru_cache(maxsize=1)
def get_nlp_model():
    """Zwraca załadowany model spaCy, inicjując go przy pierwszym wywołaniu."""
    return load_spacy_model()


def extract_info_from_text(
    text, original_filename, mode, case_signature_override="", llm_processor=None
):
    info = {
        "data": "",
        "nadawca_odbiorca": "",
        "w_sprawie": "",
        "numer_dokumentu": "",
        "sygnatura_sprawy": case_signature_override,
        "typ_dokumentu": "",
        "status": "OK",
    }

    # Krok 1: Analiza za pomocą modelu NER (spaCy)
    nlp_model = get_nlp_model()
    if nlp_model:
        doc = nlp_model(text)
        entities = {ent.label_.upper(): [] for ent in doc.ents}
        for ent in doc.ents:
            entities[ent.label_.upper()].append(ent.text.replace("\n", " ").strip())

        info["data"] = " ".join(entities.get("DATA", []))
        info["nadawca_odbiorca"] = " ".join(entities.get("ORGANIZACJA", []))
        info["w_sprawie"] = " ".join(entities.get("TYTUL_PISMA", []))
        info["numer_dokumentu"] = " ".join(entities.get("NR_DOKUMENTU", []))
        info["typ_dokumentu"] = " ".join(entities.get("TYP_DOKUMENTU", []))
        if not info["sygnatura_sprawy"]:
            info["sygnatura_sprawy"] = " ".join(
                entities.get("SYGNATURA_SPRAWY", [])
            )
    else:
        info["w_sprawie"] = "BŁĄD: Model NER nie jest załadowany."
        info["status"] = "BŁĄD"

    # Krok 2: Użycie SmartExtractor dla pól, które są puste
    smart_results = get_smart_extractor().extract_info(text)

    if not info["data"]:
        info["data"] = smart_results.get("data", "")
    if not info["nadawca_odbiorca"]:
        info["nadawca_odbiorca"] = smart_results.get("nadawca_odbiorca", "")
    if not info["w_sprawie"]:
        info["w_sprawie"] = smart_results.get("w_sprawie", "")
    if not info["numer_dokumentu"]:
        info["numer_dokumentu"] = smart_results.get("numer_dokumentu", "")
    if not info["typ_dokumentu"]:
        info["typ_dokumentu"] = smart_results.get("typ_dokumentu", "")

    # Krok 3: Proste wyrażenia regularne dla brakujących pól
    if not info["data"]:
        date_match = re.search(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}", text)
        if not date_match:
            date_match = re.search(
                r"\b\d{1,2}\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|wrze[sś]nia|października|listopada|grudnia)\s+\d{4}\b",
                text,
                flags=re.IGNORECASE,
            )
        if date_match:
            info["data"] = date_match.group(0)

    if not info["nadawca_odbiorca"]:
        senders = re.findall(
            r"^(?:Od|Nadawca)\s*:\s*(.+)$",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        recipients = re.findall(
            r"^(?:Do|Adresat)\s*:\s*(.+)$",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        combined = [s.strip() for s in senders + recipients]
        if combined:
            info["nadawca_odbiorca"] = " ".join(combined)

    if not info["numer_dokumentu"]:
        num_match = re.search(
            r"(?:nr|numer)(?:\s+dokumentu)?\s*[:\s-]+([A-Z0-9./\-]+)",
            text,
            flags=re.IGNORECASE,
        )
        if not num_match:
            num_match = re.search(
                r"(?:nr|numer)(?:\s+dokumentu)?\s+([A-Z0-9./\-]+)",
                text,
                flags=re.IGNORECASE,
            )
        if num_match:
            info["numer_dokumentu"] = num_match.group(1).strip()

    if not info["sygnatura_sprawy"]:
        sig_match = re.search(
            r"(?:sygn\.?\s*akt|sygnatura)\s*[:\s-]*([A-Z0-9./\- ]+)",
            text,
            flags=re.IGNORECASE,
        )
        if sig_match:
            info["sygnatura_sprawy"] = sig_match.group(1).strip()

    # Krok 4: Użycie asystenta LLM tylko jeśli jest dostępny i użytkownik go włączył
    if llm_processor:
        logger.info("Używanie asystenta Phi-3 Mini do wzbogacenia analizy...")
        try:
            llm_results = llm_processor.extract_smart_metadata(
                text, original_filename
            )

            if llm_results:
                if not info["typ_dokumentu"] and llm_results.get("typ_dokumentu"):
                    info["typ_dokumentu"] = llm_results["typ_dokumentu"]
                if not info["data"] and llm_results.get("data"):
                    info["data"] = llm_results["data"]
                if not info["w_sprawie"] and llm_results.get("temat"):
                    info["w_sprawie"] = llm_results["temat"]
                if (
                    not info["nadawca_odbiorca"]
                    and llm_results.get("nadawca_odbiorca")
                ):
                    info["nadawca_odbiorca"] = llm_results["nadawca_odbiorca"]
                if not info["numer_dokumentu"] and llm_results.get("numer_dokumentu"):
                    info["numer_dokumentu"] = llm_results["numer_dokumentu"]
                logger.info("Analiza LLM zakończona pomyślnie.")
        except Exception as e:
            logger.error(f"Problem z asystentem LLM: {e}", exc_info=False)

    # --- Walidacja pól ---
    colors: dict[str, str] = {}
    for key, value in info.items():
        if key != "status" and not value:
            colors[key] = "yellow"

    if colors:
        info["status"] = "DO UZUPEŁNIENIA"
    info["colors"] = colors

    return info


def generate_new_filename(info, doc_type, counters):
    """Build a new filename using the scheme
    ``lp_Sygnatura_numer-dokumentu-nadawca-Umowa-w-sprawie``.

    ``counters`` przechowuje licznik dokumentów dla danego trybu
    pracy ``doc_type``.  Każde wywołanie zwiększa licznik i zwraca
    nową nazwę pliku opartą na przekazanych metadanych.
    """

    key = doc_type or "LP"
    num = counters.get(key, 0) + 1
    counters[key] = num

    def _clean(text: str) -> str:
        return re.sub(r"[\\/*?:\"<>|]", "", text).strip()

    sygnatura = _clean(info.get("sygnatura_sprawy", "")).replace(" ", "_")
    numer = _clean(info.get("numer_dokumentu", "")).replace(" ", "-")
    nadawca = (
        _clean(info.get("nadawca_odbiorca", ""))
        .upper()
        .replace(" ", "-")[:30]
    )
    typ = _clean(info.get("typ_dokumentu", "")).upper().replace(" ", "-")
    w_sprawie = (
        _clean(info.get("w_sprawie", ""))
        .replace(" ", "-")[:50]
    )

    name = str(num)
    if sygnatura:
        name += f"_{sygnatura}"
    hyphen_parts = [p for p in [numer, nadawca, typ, w_sprawie] if p]
    if hyphen_parts:
        name += "_" + "-".join(hyphen_parts)

    if name == str(num):
        return f"dokument_do_weryfikacji_{num}.pdf"
    return f"{name}.pdf"


def process_files(
    input_dir: str,
    output_dir: str = "",
    work_mode: str = "KP",
    case_signature: str = "",
    llm_processor=None,
    counters=None,
    progress_cb=None,
    stop_cb=None,
) -> list[tuple[str, int, str, dict]]:
    """Process PDF files located in ``input_dir``.

    The function mirrors :meth:`PdfProcessorApp.process_files` but is placed
    here so it can be reused by :class:`ProcessingWorker` without creating a
    circular import.  ``progress_cb`` receives ``(current, total)`` updates and
    ``stop_cb`` may be supplied to allow early termination.  Each returned
    tuple contains the original filename, its index, the new filename and a
    dictionary with extracted metadata.
    """

    results: list[tuple[str, int, str, dict]] = []
    pdf_paths = sorted(Path(input_dir).glob("*.pdf"))
    total = len(pdf_paths)
    target_dir = Path(output_dir or input_dir)
    target_dir.mkdir(exist_ok=True)
    if counters is None:
        counters = {}
    for idx, path in enumerate(pdf_paths, 1):
        if stop_cb and stop_cb():
            break
        try:
            text = path.read_text("utf-8", errors="ignore")
        except Exception:
            text = ""
        info = extract_info_from_text(
            text, path.name, work_mode, case_signature, llm_processor
        )
        try:
            new_name = generate_new_filename(info, work_mode, counters)
        except ValueError:
            new_name = f"dokument_do_weryfikacji_{idx}.pdf"
        from .pdf_processor_app import handle_file_copy  # lazy import

        safe_name = handle_file_copy(str(path), str(target_dir), new_name)
        results.append((path.name, idx, safe_name or new_name, info))
        if progress_cb:
            progress_cb(idx, total)
    return results


class ProcessingWorker(QtCore.QThread):
    """Background thread processing PDF files and emitting Qt signals."""

    try:  # pragma: no cover - executed only when PySide6 is available
        progress = QtCore.Signal(int, int)
        finished = QtCore.Signal(list)
        error = QtCore.Signal(str)
    except Exception:  # pragma: no cover - fallback for tests
        progress = _DummySignal()
        finished = _DummySignal()
        error = _DummySignal()

    def __init__(
        self,
        input_dir: str,
        output_dir: str = "",
        work_mode: str = "KP",
        case_signature: str = "",
        llm_processor=None,
        counters=None,
        settings: AppSettings | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.work_mode = work_mode
        self.case_signature = case_signature
        self.llm_processor = llm_processor
        self.counters = counters if counters is not None else {}
        self.settings = settings or config.SETTINGS
        self._running = True

    def run(self) -> None:  # pragma: no cover - heavy IO logic
        try:
            config.SETTINGS = self.settings

            ocr._configure_pytesseract()

            pdf_paths = sorted(Path(self.input_dir).glob("*.pdf"))
            cancel_event = threading.Event()
            progress_queue: Queue = Queue()

            def _count_pages(path: Path) -> int:
                try:
                    kwargs = {}
                    if os.name == "nt":
                        kwargs["popen_kwargs"] = {
                            "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)
                        }
                    try:
                        info = pdfinfo_from_path(
                            str(path),
                            poppler_path=self.settings.poppler_folder or None,
                            **kwargs,
                        )
                    except TypeError:
                        info = pdfinfo_from_path(
                            str(path),
                            poppler_path=self.settings.poppler_folder or None,
                        )
                    return int(info.get("Pages", 0))
                except Exception:
                    return 0

            total_pages = sum(_count_pages(p) for p in pdf_paths)
            pages_done = 0
            results_holder: dict[str, list] = {}

            def ocr_task() -> None:
                res, _ = ocr.extract_texts_with_ocr_parallel(
                    [str(p) for p in pdf_paths],
                    cancel_event,
                    progress_queue,
                    language=self.settings.ocr_language,
                    psm=self.settings.ocr_psm,
                    oem=self.settings.ocr_oem,
                )
                results_holder["res"] = res

            thread = threading.Thread(target=ocr_task)
            thread.start()
            if self.progress:
                self.progress.emit(0, total_pages)
            while thread.is_alive() or not progress_queue.empty():
                try:
                    msg, inc = progress_queue.get(timeout=0.1)
                    if msg == "page_done":
                        pages_done += inc
                        if self.progress:
                            self.progress.emit(pages_done, total_pages)
                except Empty:
                    pass
                if not self._running:
                    cancel_event.set()
            thread.join()
            ocr_results = results_holder.get("res", [])
            target_dir = Path(self.output_dir or self.input_dir)
            target_dir.mkdir(exist_ok=True)

            results: list[tuple[str, int, str, dict]] = []
            for idx, (path, ocr_result) in enumerate(zip(pdf_paths, ocr_results), 1):
                text = ocr_result[0] if ocr_result else ""
                info = extract_info_from_text(
                    text,
                    path.name,
                    self.work_mode,
                    self.case_signature,
                    self.llm_processor,
                )
                try:
                    new_name = generate_new_filename(
                        info, self.work_mode, self.counters
                    )
                except ValueError:
                    new_name = f"dokument_do_weryfikacji_{idx}.pdf"
                from .pdf_processor_app import handle_file_copy  # lazy import

                safe_name = handle_file_copy(str(path), str(target_dir), new_name)
                results.append((path.name, idx, safe_name or new_name, info))
            self.finished.emit(results)
        except Exception as exc:  # pragma: no cover - defensive
            self.error.emit(str(exc))

    def stop(self) -> None:
        """Request the thread to terminate after the current file."""
        self._running = False

def open_pdf_file(filepath):
    """Otwiera plik PDF przy użyciu domyślnej aplikacji systemu."""
    try:
        no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if sys.platform == "win32":
            subprocess.Popen(
                ["cmd", "/c", "start", "", filepath],
                shell=True,
                creationflags=no_window,
            )
        elif sys.platform == "darwin":
            subprocess.Popen(["open", filepath], creationflags=no_window)
        else:
            subprocess.Popen(["xdg-open", filepath], creationflags=no_window)
        return True
    except Exception as e:
        logger.error(f"Błąd otwierania pliku PDF: {e}")
        show_error(None, "Błąd", f"Nie można otworzyć pliku PDF:\n{e}")
        return False


__all__ = [
    "extract_info_from_text",
    "generate_new_filename",
    "process_files",
    "ProcessingWorker",
    "open_pdf_file",
    "load_spacy_model",
    "get_nlp_model",
    "get_smart_extractor",
    "base_path",
    "app_dir",
]
