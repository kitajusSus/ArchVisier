import os
import json
import logging
import gc
from datetime import datetime

import torch

from .qt_safe import QtWidgets, QtCore

logger = logging.getLogger(__name__)


class _DummySignal:
    """Fallback signal used when PySide6 is unavailable."""

    def __init__(self) -> None:  # pragma: no cover - simple stub
        self._slots = []

    def connect(self, slot, *args, **kwargs) -> None:  # pragma: no cover
        self._slots.append(slot)

    def emit(self, *args, **kwargs) -> None:  # pragma: no cover
        for slot in list(self._slots):
            slot(*args, **kwargs)


class DownloadWorker(QtCore.QObject):
    """Background worker downloading a selected LLM model."""

    try:  # pragma: no cover - executed when PySide6 is available
        progress = QtCore.Signal(str)
        status = QtCore.Signal(str)
        finished = QtCore.Signal(bool)
    except Exception:  # pragma: no cover - fallback without Qt
        progress = _DummySignal()
        status = _DummySignal()
        finished = _DummySignal()

    def __init__(self, model_key: str, info: dict, model_dir: str) -> None:
        super().__init__()
        self.model_key = model_key
        self.info = info
        self.model_dir = model_dir

    # ------------------------------------------------------------------
    def run(self) -> None:
        info = self.info
        model_dir = self.model_dir
        model_key = self.model_key
        self.status.emit(
            f"Pobieranie modelu {info['name']}... (może potrwać kilka minut)"
        )
        self.progress.emit(f"Rozpoczynam pobieranie modelu: {info['name']}")
        self.progress.emit(f"Identyfikator modelu: {info['model_id']}")
        self.progress.emit(f"Ścieżka docelowa: {model_dir}")

        try:
            os.makedirs(model_dir, exist_ok=True)
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.progress.emit("Pobieranie tokenizera...")
            from transformers import AutoTokenizer, AutoModelForCausalLM

            tokenizer = AutoTokenizer.from_pretrained(info["model_id"])
            self.progress.emit("Tokenizer pobrany pomyślnie.")

            self.progress.emit(f"Pobieranie modelu (rozmiar: {info['size']})...")
            model = AutoModelForCausalLM.from_pretrained(
                info["model_id"],
                torch_dtype=torch.float16
                if torch.cuda.is_available()
                else torch.float32,
                device_map="auto",
                trust_remote_code=True,
                rope_scaling=None,
            )
            self.progress.emit("Model pobrany pomyślnie.")

            self.progress.emit("Zapisywanie tokenizera na dysku...")
            tokenizer.save_pretrained(model_dir)

            self.progress.emit("Zapisywanie modelu na dysku (może potrwać chwilę)...")
            model.save_pretrained(model_dir, safe_serialization=False)

            with open(os.path.join(model_dir, "model_info.json"), "w") as f:
                json.dump(
                    {
                        "name": info["name"],
                        "description": info["description"],
                        "model_id": info["model_id"],
                        "download_date": datetime.now().strftime("%Y-%m-%d"),
                        "model_key": model_key,
                    },
                    f,
                )

            self.status.emit("Pobieranie zakończone pomyślnie!")
            self.progress.emit("Pobieranie zakończone pomyślnie!")
            self.finished.emit(True)
        except Exception as exc:  # pragma: no cover - logujemy błąd
            error_msg = f"Błąd podczas pobierania modelu: {exc}"
            logger.error(error_msg)
            self.status.emit(error_msg)
            self.progress.emit(f"BŁĄD: {exc}")
            self.finished.emit(False)


class ModelManager(QtWidgets.QDialog):
    """Okno do pobierania i weryfikacji modeli LLM."""

    AVAILABLE_MODELS = {
        "phi-3-mini": {
            "model_id": "microsoft/phi-3-mini-128k-instruct",
            "context_length": 128000,
            "name": "Microsoft Phi-3 Mini",
            "description": "Mały model generatywny z Microsoft AI (2024)",
            "size": "~1.5 GB",
        },
        "phi-2": {
            "model_id": "microsoft/phi-2",
            "context_length": 4096,
            "name": "Microsoft Phi-2",
            "description": "Mniejszy i szybszy model Microsoft, lepszy na CPU (2023)",
            "size": "~700 MB",
        },
        "mistral-tiny": {
            "model_id": "mistralai/Mistral-7B-Instruct-v0.2",
            "context_length": 8192,
            "name": "Mistral 7B Instruct",
            "description": "Dobra równowaga między rozmiarem a wydajnością (2023)",
            "size": "~3.5 GB",
        },
    }

    def __init__(self, parent: QtWidgets.QWidget | None = None, on_complete=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Instalator modeli LLM")
        self.resize(800, 600)

        self.on_complete = on_complete
        self.selected_model: str = "phi-2"
        self._thread: QtCore.QThread | None = None
        self._worker: DownloadWorker | None = None

        self._build_ui()
        self._update_model_info()

    # ------------------------------------------------------------------ UI ----
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel("Instalator modeli LLM dla Archiwizatora IGG")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        model_group = QtWidgets.QGroupBox("1. Wybierz model LLM")
        layout.addWidget(model_group)
        model_layout = QtWidgets.QVBoxLayout(model_group)
        self.button_group = QtWidgets.QButtonGroup(self)
        for key, model in self.AVAILABLE_MODELS.items():
            rb = QtWidgets.QRadioButton(
                f"{model['name']} - {model['description']}"
            )
            # Selecting the default radio button triggers the ``toggled`` signal
            # immediately.  The connected handler expects the info labels to be
            # already created, so we set the default selection **before**
            # connecting the signal.  This prevents ``_update_model_info`` from
            # being called early during UI construction, which previously led to
            # ``AttributeError`` when the labels were not yet defined.
            if key == self.selected_model:
                rb.setChecked(True)
            rb.toggled.connect(
                lambda checked, k=key: checked and self._on_model_selected(k)
            )
            self.button_group.addButton(rb)
            model_layout.addWidget(rb)

        info_group = QtWidgets.QGroupBox("Informacje o wybranym modelu")
        layout.addWidget(info_group)
        info_layout = QtWidgets.QVBoxLayout(info_group)
        self.model_name_label = QtWidgets.QLabel()
        self.model_desc_label = QtWidgets.QLabel()
        self.model_size_label = QtWidgets.QLabel()
        self.status_label = QtWidgets.QLabel("Status: Sprawdzanie...")
        status_font = self.status_label.font()
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        info_layout.addWidget(self.model_name_label)
        info_layout.addWidget(self.model_desc_label)
        info_layout.addWidget(self.model_size_label)
        info_layout.addWidget(self.status_label)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.hide()
        layout.addWidget(self.progress)

        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text, 1)

        button_layout = QtWidgets.QHBoxLayout()
        self.download_button = QtWidgets.QPushButton("2. Pobierz model")
        self.download_button.clicked.connect(self._start_download)
        self.close_button = QtWidgets.QPushButton("Zamknij")
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        system_info = (
            f"System: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}"
        )
        layout.addWidget(QtWidgets.QLabel(system_info))

    # ----------------------------------------------------------------- Helpers
    def _on_model_selected(self, key: str) -> None:
        self.selected_model = key
        self._update_model_info()

    def _model_dir(self) -> str:
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"llm_model_{self.selected_model}",
        )

    def _log(self, message: str) -> None:
        self.log_text.append(message)

    def _check_model_exists(self) -> bool:
        required_files = ["config.json", "tokenizer.json", "model.safetensors"]
        model_dir = self._model_dir()
        if not os.path.exists(model_dir):
            self.status_label.setText("Status: Model nie jest zainstalowany")
            self.download_button.setText("Pobierz model")
            self.download_button.setEnabled(True)
            return False
        all_files = all(
            os.path.exists(os.path.join(model_dir, f)) for f in required_files
        )
        if all_files:
            self.status_label.setText("Status: Model jest już zainstalowany")
            self.download_button.setText("Ponownie pobierz model")
            self.download_button.setEnabled(True)
            return True
        self.status_label.setText("Status: Wykryto niekompletną instalację")
        self.download_button.setText("Dokończ pobieranie modelu")
        self.download_button.setEnabled(True)
        return False

    def _update_model_info(self) -> None:
        info = self.AVAILABLE_MODELS[self.selected_model]
        self.model_name_label.setText(f"Model: {info['name']}")
        self.model_desc_label.setText(f"Opis: {info['description']}")
        self.model_size_label.setText(f"Rozmiar: {info['size']}")
        self._check_model_exists()

    # --------------------------------------------------------------- Download
    def _start_download(self) -> None:
        self.download_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.log_text.clear()
        self.progress.show()

        model_key = self.selected_model
        info = self.AVAILABLE_MODELS[model_key]
        model_dir = self._model_dir()

        self._thread = QtCore.QThread(self)
        self._worker = DownloadWorker(model_key, info, model_dir)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._log)
        self._worker.status.connect(self.status_label.setText)
        self._worker.finished.connect(self._on_download_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_download_finished(self, success: bool) -> None:
        self.progress.hide()
        self.close_button.setEnabled(True)
        if success:
            self.download_button.setText("Pobrano pomyślnie")
            self.download_button.setEnabled(False)
        else:
            self.download_button.setEnabled(True)
        self._check_model_exists()
        if self.on_complete:
            try:
                self.on_complete(success)
            except Exception:  # pragma: no cover - bezpieczeństwo callbacku
                logger.exception("Błąd w callbacku on_complete")
