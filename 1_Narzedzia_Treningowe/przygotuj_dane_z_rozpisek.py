"""Generate NER training data from spreadsheets and PDF files."""

import os
import sys
from typing import Iterator

import pandas as pd
import json
import re
import traceback
from pdf2image import convert_from_path
import pytesseract

# --- Path Configuration ---
# Assume Tesseract and Poppler are in the main application folder
base_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_Aplikacja_Główna'))
tesseract_folder = os.path.join(base_app_path, "tesseract")
poppler_folder = os.path.join(base_app_path, "poppler", "bin")
tesseract_cmd = os.path.join(tesseract_folder, 'tesseract.exe')
if os.path.exists(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    os.environ['TESSDATA_PREFIX'] = os.path.join(tesseract_folder, "tessdata")
if not os.path.isdir(poppler_folder):
    poppler_folder = None

# --- Column Mapping Configuration ---
# Adjust your Excel column names to the labels the model should learn
# Key: Column name in the XLSX file (case-sensitive!)
# Value: Label that the spaCy model should recognize
KOLUMNY_MAPOWANIE = {
    "Data": "DATA",
    "Nadawca": "ORGANIZACJA",
    "Odbiorca": "ORGANIZACJA",  # Sender and Recipient are the same category for the model
    "W sprawie": "TYTUL_PISMA",
    "Numer Dokumentu": "NR_DOKUMENTU",
    "Sygnatura Sprawy": "SYGNATURA_SPRAWY",
    # Add more mappings here if needed
}

# Name of the Excel column containing the PDF file name
KOLUMNA_Z_NAZWA_PLIKU = "Nazwa Pliku"

def find_all_occurrences(text: str, sub: str) -> Iterator[int]:
    """Yield starting indices of all occurrences of ``sub`` within ``text``.

    Args:
        text (str): Source string to search.
        sub (str): Substring to look for.

    Yields:
        Iterator[int]: Positions where ``sub`` appears in ``text``.
    """
    start = 0
    while True:
        start = text.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)

def process_directory(input_dir: str, output_file: str) -> None:
    """Traverse ``input_dir`` and build spaCy training data from spreadsheets and PDFs.

    Args:
        input_dir (str): Root directory containing subfolders with spreadsheets and PDFs.
        output_file (str): Path where the resulting JSONL file will be saved.

    Returns:
        None
    """
    training_data: list[dict[str, object]] = []

    for root, _, files in os.walk(input_dir):
        # Look for an Excel file in the current folder
        xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
        if not xlsx_files:
            continue  # Skip to the next folder if no spreadsheet is found

        xlsx_path = os.path.join(root, xlsx_files[0])
        print(f"\n--- Processing spreadsheet: {xlsx_path} ---")

        try:
            df = pd.read_excel(xlsx_path)
        except Exception as e:
            print(f"!! Error reading Excel file: {e}")
            continue

        for _, row in df.iterrows():
            pdf_filename = row.get(KOLUMNA_Z_NAZWA_PLIKU)
            if not pdf_filename or not isinstance(pdf_filename, str):
                continue

            pdf_path = os.path.join(root, pdf_filename)
            if not os.path.exists(pdf_path):
                print(f"!! Warning: PDF file '{pdf_filename}' not found.")
                continue

            print(f"  -> Processing file: {pdf_filename}")

            # Step 1: OCR – read full PDF content
            try:
                images = convert_from_path(pdf_path, 300, poppler_path=poppler_folder)
                full_text = "".join(pytesseract.image_to_string(img, lang='pol') for img in images)
            except Exception as e:
                print(f"  !! OCR error for file {pdf_filename}: {e}")
                traceback.print_exc()
                continue

            # Step 2: Search for Excel metadata in OCR text
            entities: list[list[object]] = []
            for col_name, label in KOLUMNY_MAPOWANIE.items():
                if col_name in row and pd.notna(row[col_name]):
                    metadata_text = str(row[col_name]).strip()
                    if not metadata_text:
                        continue

                    for start_index in find_all_occurrences(full_text, metadata_text):
                        end_index = start_index + len(metadata_text)
                        entities.append([start_index, end_index, label])
                        print(f"    Found label '{label}': '{metadata_text}'")

            if entities:
                training_data.append({"text": full_text, "label": entities})

    # Save training data to a JSONL file
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in training_data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
    print(f"\n>>> Done! Saved {len(training_data)} training records to file: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python przygotuj_dane_z_rozpisek.py <training_data_folder>")
        print("\nExample: python przygotuj_dane_z_rozpisek.py \"C:/My Documents/Old Archive\"")
        sys.exit(1)

    input_data_folder = sys.argv[1]
    output_jsonl_file = os.path.join("dane_wyjściowe_z_doccano", "trening_z_rozpisek.jsonl")

    if not os.path.isdir(input_data_folder):
        print(f"Error: Input folder '{input_data_folder}' does not exist.")
        sys.exit(1)
        
    if not os.path.exists("dane_wyjściowe_z_doccano"):
        os.makedirs("dane_wyjściowe_z_doccano")

    process_directory(input_data_folder, output_jsonl_file)

