import argparse
import threading
from typing import List

from archiwizator_core.processing.ocr import extract_texts_with_ocr_parallel


def run_process_command(pdf_paths: List[str], language: str) -> None:
    """Run OCR processing for the provided PDF paths.

    Args:
        pdf_paths: list of paths to PDF files.
        language: language code for OCR (``pol``, ``eng`` or ``auto``).
    """
    cancel_event = threading.Event()
    results, total_pages = extract_texts_with_ocr_parallel(
        pdf_paths, cancel_event, language=language
    )
    for path, result in zip(pdf_paths, results):
        if result is None:
            print(f"{path}: brak wyniku")
            continue
        text, status = result
        print(f"== {path} ==")
        print(status)
        if text:
            print(text)
    print(f"Przetworzono stron: {total_pages}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Archiwizator CLI")
    subparsers = parser.add_subparsers(dest="command")

    process_parser = subparsers.add_parser(
        "process", help="Wykonaj OCR na plikach PDF"
    )
    process_parser.add_argument(
        "pdf_paths", nargs="+", help="Ścieżki do plików PDF do przetworzenia"
    )
    process_parser.add_argument(
        "-l",
        "--language",
        default="pol",
        choices=["pol", "eng", "auto"],
        help="Język OCR (pol, eng, auto)",
    )

    args = parser.parse_args()
    if args.command == "process":
        run_process_command(args.pdf_paths, args.language)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
