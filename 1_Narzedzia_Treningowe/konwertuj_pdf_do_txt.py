"""Bulk conversion of PDF files to plain text."""

import os
import sys
import traceback

from pdf2image import convert_from_path
import pytesseract

# Configure paths relative to the project structure
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
    print(f"Found {len(pdf_files)} PDF files to convert.")

    for i, filename in enumerate(pdf_files):
        pdf_path = os.path.join(input_dir, filename)
        txt_filename = os.path.splitext(filename)[0] + '.txt'
        txt_path = os.path.join(output_dir, txt_filename)

        print(f"[{i+1}/{len(pdf_files)}] Processing: {filename}...")

        try:
            images = convert_from_path(pdf_path, 300, poppler_path=poppler_folder)
            full_text = ""
            for image in images:
                full_text += pytesseract.image_to_string(image, lang="pol") + "\n"

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f" -> Saved to: {txt_path}")
        except Exception as e:
            print(f" !! Error processing file {filename}: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python konwertuj_pdf_do_txt.py <pdf_folder> <txt_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    if not os.path.isdir(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        sys.exit(1)

    convert_pdfs_to_text(input_folder, output_folder)
    print("\nConversion complete.")
