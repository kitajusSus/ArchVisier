"""Generowanie danych treningowych NER na podstawie rozpisek i plików PDF."""

import os
import sys
from typing import Iterator

import pandas as pd
import json
import re
import traceback
from pdf2image import convert_from_path
import pytesseract

# --- Konfiguracja Ścieżek ---
# Zakładamy, że Tesseract i Poppler są w folderze z aplikacją główną
base_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_Aplikacja_Główna'))
tesseract_folder = os.path.join(base_app_path, "tesseract")
poppler_folder = os.path.join(base_app_path, "poppler", "bin")
tesseract_cmd = os.path.join(tesseract_folder, 'tesseract.exe')
if os.path.exists(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    os.environ['TESSDATA_PREFIX'] = os.path.join(tesseract_folder, "tessdata")
if not os.path.isdir(poppler_folder):
    poppler_folder = None

# --- Konfiguracja Mapowania Kolumn ---
# Dostosuj nazwy kolumn w Twoim Excelu do etykiet, których ma się uczyć model
# Klucz: Nazwa kolumny w pliku XLSX (wielkość liter ma znaczenie!)
# Wartość: Etykieta, którą ma rozpoznać model spaCy
KOLUMNY_MAPOWANIE = {
    "Data": "DATA",
    "Nadawca": "ORGANIZACJA",
    "Odbiorca": "ORGANIZACJA", # Nadawca i Odbiorca to ta sama kategoria dla modelu
    "W sprawie": "TYTUL_PISMA",
    "Numer Dokumentu": "NR_DOKUMENTU",
    "Sygnatura Sprawy": "SYGNATURA_SPRAWY",
    # Dodaj tutaj inne mapowania, jeśli potrzebujesz
}

# Nazwa kolumny w Excelu, która zawiera nazwę pliku PDF
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
        # Szukamy pliku Excel w bieżącym folderze
        xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
        if not xlsx_files:
            continue  # Przechodzimy do następnego folderu, jeśli nie ma tu rozpiski

        xlsx_path = os.path.join(root, xlsx_files[0])
        print(f"\n--- Przetwarzanie rozpiski: {xlsx_path} ---")

        try:
            df = pd.read_excel(xlsx_path)
        except Exception as e:
            print(f"!! Błąd odczytu pliku Excel: {e}")
            continue

        for _, row in df.iterrows():
            pdf_filename = row.get(KOLUMNA_Z_NAZWA_PLIKU)
            if not pdf_filename or not isinstance(pdf_filename, str):
                continue

            pdf_path = os.path.join(root, pdf_filename)
            if not os.path.exists(pdf_path):
                print(f"!! Ostrzeżenie: Plik PDF '{pdf_filename}' nie został znaleziony.")
                continue

            print(f"  -> Przetwarzanie pliku: {pdf_filename}")

            # Krok 1: OCR - odczytanie pełnej treści PDF
            try:
                images = convert_from_path(pdf_path, 300, poppler_path=poppler_folder)
                full_text = "".join(pytesseract.image_to_string(img, lang='pol') for img in images)
            except Exception as e:
                print(f"  !! Błąd OCR dla pliku {pdf_filename}: {e}")
                traceback.print_exc()
                continue

            # Krok 2: Wyszukiwanie metadanych z Excela w tekście z OCR
            entities: list[list[object]] = []
            for col_name, label in KOLUMNY_MAPOWANIE.items():
                if col_name in row and pd.notna(row[col_name]):
                    metadata_text = str(row[col_name]).strip()
                    if not metadata_text:
                        continue

                    for start_index in find_all_occurrences(full_text, metadata_text):
                        end_index = start_index + len(metadata_text)
                        entities.append([start_index, end_index, label])
                        print(f"    Znaleziono etykietę '{label}': '{metadata_text}'")

            if entities:
                training_data.append({"text": full_text, "label": entities})

    # Zapisz dane treningowe do pliku JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in training_data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
    print(f"\n>>> Zakończono! Zapisano {len(training_data)} rekordów treningowych do pliku: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Użycie: python przygotuj_dane_z_rozpisek.py <folder_z_danymi_treningowymi>")
        print("\nPrzykład: python przygotuj_dane_z_rozpisek.py \"C:\\Moje Dokumenty\\Stare Archiwum\"")
        sys.exit(1)

    input_data_folder = sys.argv[1]
    output_jsonl_file = os.path.join("dane_wyjściowe_z_doccano", "trening_z_rozpisek.jsonl")

    if not os.path.isdir(input_data_folder):
        print(f"Błąd: Folder wejściowy '{input_data_folder}' nie istnieje.")
        sys.exit(1)
        
    if not os.path.exists("dane_wyjściowe_z_doccano"):
        os.makedirs("dane_wyjściowe_z_doccano")

    process_directory(input_data_folder, output_jsonl_file)

