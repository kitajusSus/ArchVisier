"""Qt-based dialog for training a new NER model.

This module replaces the previous Tkinter implementation with a
:class:`QtWidgets.QDialog` version.  The window allows selecting a folder
with training data and displays log output from a background process that
invokes ``training_worker.py``.  The subprocess is executed within a
``QThread`` and progress is reported using Qt signals.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from .processing_worker import base_path, app_dir
from .qt_safe import QtWidgets, QtCore


class _DummySignal:
    """Fallback signal used when PySide6 is unavailable."""

    def __init__(self) -> None:  # pragma: no cover - simple stub
        self._slots = []

    def connect(self, slot, *args, **kwargs) -> None:  # pragma: no cover
        self._slots.append(slot)

    def emit(self, *args, **kwargs) -> None:  # pragma: no cover
        for slot in list(self._slots):
            slot(*args, **kwargs)


class TrainingWorker(QtCore.QObject):
    """Execute the training script in a worker thread."""

    try:  # pragma: no cover - executed only when PySide6 is available
        progress = QtCore.Signal(str)
        finished = QtCore.Signal(bool)
    except Exception:  # pragma: no cover - fallback when Qt is missing
        progress = _DummySignal()
        finished = _DummySignal()

    def __init__(self, cmd: list[str]) -> None:
        super().__init__()
        self.cmd = cmd

    def run(self) -> None:
        """Run the external training script and emit progress lines."""
        try:
            process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            assert process.stdout
            for line in process.stdout:
                self.progress.emit(line.rstrip())
            process.stdout.close()
            returncode = process.wait()
            self.finished.emit(returncode == 0)
        except Exception as exc:  # pragma: no cover - defensive
            self.progress.emit(f"Błąd uruchamiania treningu: {exc}")
            self.finished.emit(False)


class TrainingWindow(QtWidgets.QDialog):
    """Dialog providing UI for training a new model."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Trening nowego modelu AI")
        self.resize(800, 600)

        self.data_folder: str = ""
        self.output_model_dir: str = ""
        self._thread: QtCore.QThread | None = None
        self._worker: TrainingWorker | None = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # --- Folder selection ---
        folder_group = QtWidgets.QGroupBox(
            "1. Wskaż folder z danymi treningowymi (zawierający podfoldery z PDF i Excel)"
        )
        layout.addWidget(folder_group)
        folder_layout = QtWidgets.QHBoxLayout(folder_group)
        self.folder_edit = QtWidgets.QLineEdit()
        self.folder_edit.textChanged.connect(self._on_folder_changed)
        folder_layout.addWidget(self.folder_edit, 1)
        browse_btn = QtWidgets.QPushButton("Wybierz…")
        browse_btn.clicked.connect(self.select_data_folder)
        folder_layout.addWidget(browse_btn)

        # --- Start button ---
        self.train_button = QtWidgets.QPushButton("2. Rozpocznij trening")
        self.train_button.clicked.connect(self.start_training_thread)
        layout.addWidget(self.train_button)

        # --- Log output ---
        log_group = QtWidgets.QGroupBox("Log treningu")
        layout.addWidget(log_group, 1)
        log_layout = QtWidgets.QVBoxLayout(log_group)
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

    # ------------------------------------------------------------------
    # UI callbacks
    def _on_folder_changed(self, text: str) -> None:
        self.data_folder = text

    def select_data_folder(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Wybierz folder główny z danymi treningowymi"
        )
        if path:
            self.folder_edit.setText(path)

    def log_message(self, message: str) -> None:
        self.log_text.append(message)

    # ------------------------------------------------------------------
    # Training handling
    def start_training_thread(self) -> None:
        if not self.data_folder:
            QtWidgets.QMessageBox.critical(
                self,
                "Błąd",
                "Wybierz folder z danymi treningowymi.",
            )
            return

        self.train_button.setEnabled(False)
        self.log_text.clear()

        self.output_model_dir = os.path.join(app_dir, "temp_model_output")
        cmd = [
            sys.executable,
            os.path.join(base_path, "training_worker.py"),
            self.data_folder,
            self.output_model_dir,
        ]

        self._thread = QtCore.QThread(self)
        self._worker = TrainingWorker(cmd)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.log_message)
        self._worker.finished.connect(self._on_training_complete)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_training_complete(self, success: bool) -> None:
        if success:
            final_model_path = os.path.join(app_dir, "custom_ner_model")
            if os.path.exists(final_model_path):
                shutil.rmtree(final_model_path)
            shutil.move(
                os.path.join(self.output_model_dir, "model-best"), final_model_path
            )
            shutil.rmtree(self.output_model_dir, ignore_errors=True)
            self.log_message("\n>>> SUKCES! Model został wytrenowany i zapisany.")
            self.log_message(">>> Zrestartuj aplikację, aby załadować nowy model.")
            QtWidgets.QMessageBox.information(
                self,
                "Trening zakończony",
                "Nowy model został pomyślnie wytrenowany.\n\nUruchom ponownie aplikację, aby zacząć go używać.",
            )
        else:
            self.log_message(
                "\n>>> BŁĄD! Trening nie powiódł się. Sprawdź logi powyżej."
            )
            QtWidgets.QMessageBox.critical(
                self,
                "Błąd treningu",
                "Wystąpił błąd podczas trenowania modelu. Sprawdź logi w oknie treningu.",
            )

        self.train_button.setEnabled(True)
