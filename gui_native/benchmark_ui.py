import time
import os


def measure_tkinter():
    try:
        import tkinter as tk
        start = time.perf_counter()
        root = tk.Tk()
        root.update()
        elapsed = time.perf_counter() - start
        root.destroy()
        return elapsed
    except Exception as exc:  # pragma: no cover - environment-specific
        return f"Tkinter failed: {exc}"


def measure_pyside():
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication, QWidget
        import sys
        app = QApplication(sys.argv)
        start = time.perf_counter()
        w = QWidget()
        w.show()
        app.processEvents()
        elapsed = time.perf_counter() - start
        return elapsed
    except Exception as exc:  # pragma: no cover - environment-specific
        return f"Qt failed: {exc}"


if __name__ == "__main__":
    print("Tkinter:", measure_tkinter())
    print("Qt:", measure_pyside())
