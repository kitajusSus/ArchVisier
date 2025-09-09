from pathlib import Path
import sys
import types

import pytest


# Ensure the application package is importable
BASE_DIR = Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna"
sys.path.insert(0, str(BASE_DIR))

from gui import pdf_processor_app, processing_worker, training_window
from gui.pdf_processor_app import PdfProcessorApp, ProcessingWorker
from gui.training_window import TrainingWindow
from config import AppSettings


def _stub_processing(monkeypatch):
    """Patch processing functions to avoid heavy dependencies."""

    def fake_extract(text, filename, mode, case_signature_override="", llm_processor=None):
        return {"numer_dokumentu": filename.split(".")[0]}

    def fake_generate(info, mode, counters):
        return f"{info['numer_dokumentu']}_renamed.pdf"

    monkeypatch.setattr(
        pdf_processor_app.processing_worker, "extract_info_from_text", fake_extract
    )
    monkeypatch.setattr(
        pdf_processor_app.processing_worker, "generate_new_filename", fake_generate
    )

    def fake_ocr(paths, cancel_event, progress_queue=None, language="pol", config="", psm=3, oem=3):
        if progress_queue:
            for _ in paths:
                progress_queue.put(("page_done", 1))
        return [("text", "Sukces")] * len(paths), len(paths)

    def fake_pdfinfo(path, poppler_path=None, **kwargs):
        return {"Pages": 1}

    monkeypatch.setattr(
        pdf_processor_app.processing_worker.ocr,
        "extract_texts_with_ocr_parallel",
        fake_ocr,
    )
    monkeypatch.setattr(
        pdf_processor_app.processing_worker, "pdfinfo_from_path", fake_pdfinfo
    )


def test_process_files_passes_llm(tmp_path, monkeypatch):
    (tmp_path / "a.pdf").write_bytes(b"")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _stub_processing(monkeypatch)

    sentinel = object()
    captured = {}

    def tracker(text, filename, mode, case_signature_override="", llm_processor=None):
        captured["llm"] = llm_processor
        return {"numer_dokumentu": filename.split(".")[0]}

    monkeypatch.setattr(
        pdf_processor_app.processing_worker,
        "extract_info_from_text",
        tracker,
    )

    results = PdfProcessorApp.process_files(
        str(tmp_path), str(out_dir), llm_processor=sentinel
    )

    assert captured["llm"] is sentinel
    assert results[0][2] == "a_renamed.pdf"
    assert isinstance(results[0][3], dict)
    assert (out_dir / "a_renamed.pdf").exists()


def test_processing_worker_emits_results(tmp_path, monkeypatch):
    (tmp_path / "c.pdf").write_bytes(b"")
    out_dir = tmp_path / "out"
    _stub_processing(monkeypatch)

    # ensure generate_new_filename returns non-ASCII characters to test sanitisation
    monkeypatch.setattr(
        pdf_processor_app.processing_worker,
        "generate_new_filename",
        lambda info, mode, counters: "c ż.pdf",
    )

    worker = ProcessingWorker(str(tmp_path), str(out_dir))
    received = []
    worker.finished.connect(lambda res: received.extend(res))
    worker.run()  # run synchronously

    assert received[0][2] == "c__.pdf"
    assert isinstance(received[0][3], dict)
    assert (out_dir / "c__.pdf").exists()
    assert out_dir.exists()


def test_start_processing_warns_when_llm_missing(tmp_path, monkeypatch):
    (tmp_path / "a.pdf").write_bytes(b"")

    app = PdfProcessorApp()
    app.input_dir = str(tmp_path)
    app.output_dir = str(tmp_path)
    app.use_llm = True

    monkeypatch.setattr(app, "init_llm_processor", lambda: None)

    warned = {}

    def fake_warning(parent, title, text):
        warned["called"] = (title, text)

    dummy_widgets = types.SimpleNamespace(
        QMessageBox=types.SimpleNamespace(warning=fake_warning)
    )
    monkeypatch.setattr(pdf_processor_app, "QtWidgets", dummy_widgets)

    app.start_processing()

    assert "called" in warned


def test_process_files_generate_and_copy(tmp_path, monkeypatch):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    (in_dir / "doc.pdf").write_bytes(b"dummy")

    def fake_extract(text, filename, mode, case_signature_override="", llm_processor=None):
        return {"numer_dokumentu": "123"}

    def fake_generate(info, mode, counters):
        return "123_new.pdf"

    monkeypatch.setattr(
        pdf_processor_app.processing_worker, "extract_info_from_text", fake_extract
    )
    monkeypatch.setattr(
        pdf_processor_app.processing_worker, "generate_new_filename", fake_generate
    )

    results = PdfProcessorApp.process_files(str(in_dir))
    assert results[0][:3] == ("doc.pdf", 1, "123_new.pdf")
    assert isinstance(results[0][3], dict)
    assert results[0][3].get("numer_dokumentu") == "123"

    copied_name = pdf_processor_app.handle_file_copy(
        str(in_dir / "doc.pdf"), str(out_dir), results[0][2]
    )

    assert copied_name == "123_new.pdf"
    assert (out_dir / "123_new.pdf").exists()


def test_input_dir_change_updates_output(tmp_path):
    settings = AppSettings(default_output_subdir="wyniki")
    app = PdfProcessorApp(settings)

    class DummyEdit:
        def __init__(self, cb):
            self._text = ""
            self._cb = cb

        def setText(self, text):
            self._text = text
            self._cb(text)

        def text(self):
            return self._text

    app.output_edit = DummyEdit(app._on_output_dir_changed)
    app.output_dir = ""
    app._on_input_dir_changed(str(tmp_path))
    expected = str(tmp_path / "wyniki")
    assert app.output_dir == expected
    assert app.output_edit.text() == expected


def test_start_processing_passes_llm_to_worker(tmp_path, monkeypatch):
    (tmp_path / "a.pdf").write_bytes(b"")

    app = PdfProcessorApp()
    app.input_dir = str(tmp_path)
    app.use_llm = True
    app.start_btn = types.SimpleNamespace(setEnabled=lambda flag: None)
    app.tree = types.SimpleNamespace(clear=lambda: None)
    monkeypatch.setattr(app, "_on_processing_finished", lambda results: None)
    monkeypatch.setattr(app, "_on_processing_error", lambda msg: None)

    sentinel = object()
    monkeypatch.setattr(app, "init_llm_processor", lambda: sentinel)

    captured = {}

    class DummyWorker:
        def __init__(
            self,
            input_dir,
            output_dir="",
            work_mode="",
            case_signature="",
            llm_processor=None,
        ):
            captured["llm"] = llm_processor
            self.progress = pdf_processor_app._DummySignal()
            self.finished = pdf_processor_app._DummySignal()
            self.error = pdf_processor_app._DummySignal()

        def start(self):
            pass

        def stop(self):
            pass

        def isRunning(self):
            return False

        def wait(self):
            pass

    monkeypatch.setattr(pdf_processor_app, "ProcessingWorker", DummyWorker)

    app.start_processing()

    assert captured["llm"] is sentinel


def test_open_pdf_file_invokes_subprocess(monkeypatch):
    called = {}

    class DummyPopen:
        def __init__(self, cmd, creationflags=0, **kwargs):
            called["cmd"] = cmd
            called["flags"] = creationflags

    monkeypatch.setattr(processing_worker.subprocess, "Popen", DummyPopen)
    monkeypatch.setattr(processing_worker.sys, "platform", "linux")

    assert processing_worker.open_pdf_file("file.pdf")
    assert called["cmd"] == ["xdg-open", "file.pdf"]


def test_training_window_launches(monkeypatch):
    def fake_init(self, parent=None):
        self.data_folder = ""

    monkeypatch.setattr(TrainingWindow, "__init__", fake_init)
    called = {}

    def fake_critical(parent, title, text):
        called["args"] = (title, text)

    dummy_widgets = types.SimpleNamespace(
        QMessageBox=types.SimpleNamespace(critical=fake_critical)
    )
    monkeypatch.setattr(training_window, "QtWidgets", dummy_widgets)

    win = TrainingWindow()
    win.start_training_thread()

    assert "args" in called
