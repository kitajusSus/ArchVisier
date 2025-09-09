"""Pobieranie modeli LLM z wykorzystaniem PySide6."""

from __future__ import annotations

import gc
import json
import logging
import os
import sys

from PySide6 import QtCore, QtWidgets, QtGui
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


logger = logging.getLogger(__name__)


class ModelDownloaderWorker(QtCore.QThread):
    """Wątek odpowiedzialny za pobieranie i zapisywanie modelu."""

    log_signal = QtCore.Signal(str, str)
    status_signal = QtCore.Signal(str)
    finished_signal = QtCore.Signal()
    error_signal = QtCore.Signal(str)

    def __init__(self, model_key: str, model_info: dict, model_dir: str, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.model_key = model_key
        self.model_info = model_info
        self.model_dir = model_dir

    def run(self) -> None:  # pragma: no cover - uruchamiane w wątku GUI
        try:
            self.status_signal.emit(
                f"Pobieranie modelu {self.model_info['name']}... (może potrwać kilka minut)"
            )
            self.log_signal.emit(
                f"Rozpoczynam pobieranie modelu: {self.model_info['name']}", "info"
            )
            self.log_signal.emit(
                f"Identyfikator modelu: {self.model_info['model_id']}", "info"
            )
            self.log_signal.emit(f"Ścieżka docelowa: {self.model_dir}", "info")

            os.makedirs(self.model_dir, exist_ok=True)

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.log_signal.emit("Pobieranie tokenizera...", "info")
            tokenizer = AutoTokenizer.from_pretrained(self.model_info["model_id"])
            self.log_signal.emit("Tokenizer pobrany pomyślnie.", "info")

            self.log_signal.emit(
                f"Pobieranie modelu (rozmiar: {self.model_info['size']})...", "info"
            )
            model = AutoModelForCausalLM.from_pretrained(
                self.model_info["model_id"],
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
                trust_remote_code=True,
                rope_scaling=None,
            )
            self.log_signal.emit("Model pobrany pomyślnie.", "success")

            self.log_signal.emit("Zapisywanie tokenizera na dysku...", "info")
            tokenizer.save_pretrained(self.model_dir)

            self.log_signal.emit(
                "Zapisywanie modelu na dysku (może potrwać chwilę)...", "info"
            )
            model.save_pretrained(self.model_dir, safe_serialization=False)

            with open(os.path.join(self.model_dir, "model_info.json"), "w") as f:
                json.dump(
                    {
                        "name": self.model_info["name"],
                        "description": self.model_info["description"],
                        "model_id": self.model_info["model_id"],
                        "download_date": "2025-08-18",
                        "model_key": self.model_key,
                    },
                    f,
                )

            self.status_signal.emit("Pobieranie zakończone pomyślnie!")
            self.log_signal.emit("Pobieranie zakończone pomyślnie!", "success")
            self.finished_signal.emit()
        except Exception as e:  # pragma: no cover - logowanie błędów
            import traceback

            error_msg = f"Błąd podczas pobierania modelu: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.error_signal.emit(error_msg)
            self.log_signal.emit(f"BŁĄD: {e}", "error")
            self.log_signal.emit(traceback.format_exc(), "error")


class ModelDownloaderApp(QtWidgets.QMainWindow):
    """Główne okno aplikacji do pobierania modeli LLM."""

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

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Archiwizator AI - Instalacja modelu LLM (2025)")
        self.resize(800, 600)

        self.selected_model = "phi-2"

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        self._create_widgets(central)

        self.update_model_info()

    def _create_widgets(self, central: QtWidgets.QWidget) -> None:
        main_layout = QtWidgets.QVBoxLayout(central)

        title = QtWidgets.QLabel("Instalator modeli LLM dla Archiwizatora AI")
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        main_layout.addWidget(title)

        model_group = QtWidgets.QGroupBox("1. Wybierz model LLM")
        model_layout = QtWidgets.QVBoxLayout(model_group)
        self.button_group = QtWidgets.QButtonGroup(self)
        for key, model in self.AVAILABLE_MODELS.items():
            radio = QtWidgets.QRadioButton(
                f"{model['name']} - {model['description']}"
            )
            radio.setProperty("model_key", key)
            if key == self.selected_model:
                radio.setChecked(True)
            self.button_group.addButton(radio)
            radio.toggled.connect(self._on_model_selected)
            model_layout.addWidget(radio)
        main_layout.addWidget(model_group)

        info_group = QtWidgets.QGroupBox("Informacje o wybranym modelu")
        info_layout = QtWidgets.QVBoxLayout(info_group)
        self.model_name_label = QtWidgets.QLabel("Model: ")
        info_layout.addWidget(self.model_name_label)
        self.model_desc_label = QtWidgets.QLabel("Opis: ")
        info_layout.addWidget(self.model_desc_label)
        self.model_size_label = QtWidgets.QLabel("Rozmiar: ")
        info_layout.addWidget(self.model_size_label)
        self.status_label = QtWidgets.QLabel("Status: Sprawdzanie...")
        info_layout.addWidget(self.status_label)
        main_layout.addWidget(info_group)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        main_layout.addWidget(self.progress)

        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text, 1)

        button_layout = QtWidgets.QHBoxLayout()
        self.download_button = QtWidgets.QPushButton("2. Pobierz model")
        self.download_button.clicked.connect(self.download_model)
        button_layout.addWidget(self.download_button)
        self.close_button = QtWidgets.QPushButton("Zamknij")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        system_info = (
            f"System: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}"
        )
        sys_label = QtWidgets.QLabel(system_info)
        sys_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(sys_label)

    def _on_model_selected(self) -> None:
        button = self.button_group.checkedButton()
        if button is not None:
            self.selected_model = button.property("model_key")
            self.update_model_info()

    def update_model_info(self) -> None:
        model_info = self.AVAILABLE_MODELS[self.selected_model]
        self.model_id = model_info["model_id"]
        self.model_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"llm_model_{self.selected_model}",
        )
        self.model_name_label.setText(f"Model: {model_info['name']}")
        self.model_desc_label.setText(f"Opis: {model_info['description']}")
        self.model_size_label.setText(f"Rozmiar: {model_info['size']}")
        self.check_model_exists()

    def log(self, message: str, tag: str = "info") -> None:
        color = {"info": "blue", "success": "green", "error": "red"}.get(tag, "black")
        self.log_text.append(f'<span style="color:{color}">{message}</span>')
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def check_model_exists(self) -> bool:
        required_files = ["config.json", "tokenizer.json", "model.safetensors"]
        if not os.path.exists(self.model_dir):
            self.status_label.setText("Status: Model nie jest zainstalowany")
            self.download_button.setEnabled(True)
            self.download_button.setText("Pobierz model")
            return False

        all_files_exist = all(
            os.path.exists(os.path.join(self.model_dir, f)) for f in required_files
        )
        if all_files_exist:
            self.status_label.setText("Status: Model jest już zainstalowany")
            self.download_button.setText("Ponownie pobierz model")
            return True

        self.status_label.setText("Status: Wykryto niekompletną instalację")
        self.download_button.setText("Dokończ pobieranie modelu")
        return False

    def download_model(self) -> None:
        self.download_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.progress.setRange(0, 0)
        self.log_text.clear()

        model_key = self.selected_model
        model_info = self.AVAILABLE_MODELS[model_key]
        self.worker = ModelDownloaderWorker(model_key, model_info, self.model_dir)
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self._on_download_finished)
        self.worker.error_signal.connect(self._on_download_error)
        self.worker.start()

    def _on_download_finished(self) -> None:
        self.progress.setRange(0, 100)
        self.download_button.setText("Pobrano pomyślnie")
        self.download_button.setEnabled(False)
        self.close_button.setEnabled(True)

    def _on_download_error(self, message: str) -> None:
        self.progress.setRange(0, 100)
        self.status_label.setText(message)
        self.download_button.setEnabled(True)
        self.close_button.setEnabled(True)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # pragma: no cover
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        super().closeEvent(event)


if __name__ == "__main__":  # pragma: no cover - wywołanie aplikacji
    qt_app = QtWidgets.QApplication(sys.argv)
    window = ModelDownloaderApp()
    window.show()
    sys.exit(qt_app.exec())

