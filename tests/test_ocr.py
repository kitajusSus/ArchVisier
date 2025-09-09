from pathlib import Path
import runpy
import threading
import queue

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna" / "processing" / "ocr.py"))
extract_text_with_ocr = MODULE["extract_text_with_ocr"]
extract_texts_with_ocr_parallel = MODULE["extract_texts_with_ocr_parallel"]


def test_extract_text_with_ocr_basic(monkeypatch):
    from custom_pil import Image

    def fake_convert_from_path(pdf_path, dpi, poppler_path=None, fmt=None):
        return [Image.new("RGB", (10, 10), color="white")]
    called = {"median": False, "config": ""}

    def fake_medianBlur(image, ksize):
        called["median"] = True
        return image

    def fake_image_to_string(image, lang="pol", config=""):
        called["config"] = config
        return "teest" if called["median"] else "bad"

    MODULE["convert_from_path"] = fake_convert_from_path
    extract_text_with_ocr.__globals__["convert_from_path"] = fake_convert_from_path
    monkeypatch.setattr(MODULE["cv2"], "medianBlur", fake_medianBlur)
    extract_text_with_ocr.__globals__["cv2"] = MODULE["cv2"]
    monkeypatch.setattr(MODULE["pytesseract"], "image_to_string", fake_image_to_string)
    extract_text_with_ocr.__globals__["pytesseract"] = MODULE["pytesseract"]
    MODULE["POLISH_DICTIONARY"].add("test")
    MODULE["ENGLISH_DICTIONARY"].add("test")

    q = queue.Queue()
    text, status = extract_text_with_ocr("dummy.pdf", q, language="pol")
    assert called["median"]
    assert text.strip() == "test"
    assert status == "Sukces"
    assert q.get_nowait() == ("page_done", 1)
    assert called["config"] == "--psm 3 --oem 3"


def test_extract_text_with_ocr_tesseract_error(monkeypatch):
    from custom_pil import Image
    from pytesseract import TesseractError

    def fake_convert_from_path(pdf_path, dpi, poppler_path=None, fmt=None):
        return [Image.new("RGB", (10, 10), color="white")]

    def fake_image_to_string(image, lang="pol", config=""):
        raise TesseractError(1, "fake")

    MODULE["convert_from_path"] = fake_convert_from_path
    extract_text_with_ocr.__globals__["convert_from_path"] = fake_convert_from_path
    monkeypatch.setattr(MODULE["pytesseract"], "image_to_string", fake_image_to_string)
    extract_text_with_ocr.__globals__["pytesseract"] = MODULE["pytesseract"]

    text, status = extract_text_with_ocr("dummy.pdf", queue.Queue(), language="pol")
    assert text.startswith("BŁĄD TECHNICZNY OCR: fake")
    assert "Traceback" in status


def test_extract_texts_with_ocr_parallel_order_and_cancel(monkeypatch):
    def fake_extract(path, progress_queue=None, language="pol", config="", psm=3, oem=3):
        assert config == "--psm 3 --oem 3"
        if progress_queue:
            progress_queue.put(("page_done", 1))
        return f"text-{path}", "Sukces"

    def fake_pdfinfo(path, poppler_path=None):
        return {"Pages": 1}

    MODULE["extract_text_with_ocr"] = fake_extract
    extract_texts_with_ocr_parallel.__globals__["extract_text_with_ocr"] = fake_extract
    MODULE["pdfinfo_from_path"] = fake_pdfinfo
    extract_texts_with_ocr_parallel.__globals__["pdfinfo_from_path"] = fake_pdfinfo

    pdfs = ["a.pdf", "b.pdf", "c.pdf"]
    cancel_event = threading.Event()
    q = queue.Queue()

    results, total = extract_texts_with_ocr_parallel(pdfs, cancel_event, q, language="pol")
    assert [res[0] for res in results] == [f"text-{p}" for p in pdfs]
    assert total == len(pdfs)
    msgs = [q.get_nowait() for _ in pdfs]
    assert msgs == [("page_done", 1)] * len(pdfs)

    cancel_event.set()
    cancelled_results, total2 = extract_texts_with_ocr_parallel(
        pdfs, cancel_event, queue.Queue(), language="pol"
    )
    assert cancelled_results == [None, None, None]
    assert total2 == len(pdfs)


def test_extract_text_with_ocr_auto_language(monkeypatch):
    from custom_pil import Image

    def fake_convert_from_path(pdf_path, dpi, poppler_path=None, fmt=None):
        return [Image.new("RGB", (10, 10), color="white")]

    calls = []

    def fake_image_to_string(image, lang="pol", config=""):
        calls.append((lang, config))
        return "test"

    MODULE["convert_from_path"] = fake_convert_from_path
    extract_text_with_ocr.__globals__["convert_from_path"] = fake_convert_from_path
    monkeypatch.setattr(MODULE["pytesseract"], "image_to_string", fake_image_to_string)
    extract_text_with_ocr.__globals__["pytesseract"] = MODULE["pytesseract"]
    MODULE["detect"] = lambda text: "en"
    extract_text_with_ocr.__globals__["detect"] = MODULE["detect"]
    q = queue.Queue()
    text, status = extract_text_with_ocr("dummy.pdf", q, language="auto")
    assert calls[0] == ("pol+eng", "--psm 3 --oem 3")
    assert calls[1] == ("eng", "--psm 3 --oem 3")
    assert text.strip() == "test"
    assert status == "Sukces"


def test_psm_and_language_change_output(monkeypatch):
    from custom_pil import Image

    def fake_convert_from_path(pdf_path, dpi, poppler_path=None, fmt=None):
        return [Image.new("RGB", (10, 10), color="white")]

    import re

    def fake_image_to_string(image, lang="pol", config=""):
        match = re.search(r"--psm (\d+)", config)
        psm_val = match.group(1) if match else ""
        return f"{lang}{psm_val}"

    MODULE["convert_from_path"] = fake_convert_from_path
    extract_text_with_ocr.__globals__["convert_from_path"] = fake_convert_from_path
    monkeypatch.setattr(MODULE["pytesseract"], "image_to_string", fake_image_to_string)
    extract_text_with_ocr.__globals__["pytesseract"] = MODULE["pytesseract"]

    text1, _ = extract_text_with_ocr("dummy.pdf", queue.Queue(), language="pol", psm=3)
    text2, _ = extract_text_with_ocr("dummy.pdf", queue.Queue(), language="eng", psm=3)
    text3, _ = extract_text_with_ocr("dummy.pdf", queue.Queue(), language="pol", psm=4)

    assert text1.strip() == "pol3"
    assert text2.strip() == "eng3"
    assert text3.strip() == "pol4"
    assert text1 != text2
    assert text1 != text3
