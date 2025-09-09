from logging_config import setup_logging
from gui.pdf_processor_app import PdfProcessorApp
from gui.qt_safe import QtWidgets, QT_AVAILABLE
from config import load_settings
from app_session_manager import SessionManager

if __name__ == "__main__":
    setup_logging()
    if not QT_AVAILABLE:
        raise RuntimeError(
            "Qt libraries are required to run the GUI. Install PySide6 and try again."
        )
    app_settings = load_settings()

    print("skibidi")
    app = QtWidgets.QApplication()
    window = PdfProcessorApp(app_settings)
    if not getattr(window, "session_manager", None):
        window.session_manager = SessionManager(window)
    window.show_welcome_screen()
    window.show()
    app.exec()
