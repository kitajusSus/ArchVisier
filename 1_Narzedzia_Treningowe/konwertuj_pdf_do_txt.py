"""Narzędzie do hurtowej konwersji plików PDF na zwykły tekst."""

import os
import sys
import traceback

from pdf2image import convert_from_path
import pytesseract

# Konfiguracja ścieżek względem struktury projektu
base_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_Aplikacja_Główna'))
tesseract_folder = os.path.join(base_app_path, "tesseract")
poppler_folder = os.path.join(base_app_path, "poppler", "bin")
tesseract_cmd = os.path.join(tesseract_folder, "tesseract.exe")
if os.path.exists(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    os.environ["TESSDATA_PREFIX"] = os.path.join(tesseract_folder, "tessdata")
if not os.path.isdir(poppler_folder):
    poppler_folder = None


def convert_pdfs_to_text(input_dir: str, output_dir: str) -> None:
    """Convert all PDF files from ``input_dir`` into text files.

    Args:
        input_dir (str): Directory containing PDF files.
        output_dir (str): Target directory where ``.txt`` files will be saved.

    Returns:
        None
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    print(f"Znaleziono {len(pdf_files)} plików PDF do konwersji.")

    for i, filename in enumerate(pdf_files):
        pdf_path = os.path.join(input_dir, filename)
        txt_filename = os.path.splitext(filename)[0] + '.txt'
        txt_path = os.path.join(output_dir, txt_filename)

        print(f"[{i+1}/{len(pdf_files)}] Przetwarzanie: {filename}...")

        try:
            images = convert_from_path(pdf_path, 300, poppler_path=poppler_folder)
            full_text = ""
            for image in images:
                full_text += pytesseract.image_to_string(image, lang="pol") + "\n"

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f" -> Zapisano do: {txt_path}")
        except Exception as e:
            print(f" !! Błąd podczas przetwarzania pliku {filename}: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Użycie: python konwertuj_pdf_do_txt.py <folder_z_pdfami> <folder_na_txt>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    if not os.path.isdir(input_folder):
        print(f"Błąd: Folder wejściowy '{input_folder}' nie istnieje.")
        sys.exit(1)

    convert_pdfs_to_text(input_folder, output_folder)
    print("\nKonwersja zakończona.")
