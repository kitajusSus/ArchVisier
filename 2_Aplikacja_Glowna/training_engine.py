import os
import sys
from typing import Callable, Iterator, List, Optional, Tuple

import pandas as pd
import json
import re
import traceback
import spacy
from spacy.tokens import DocBin
from spacy.cli.train import train
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
import logging
import shutil

# Konfiguracja logowania
logger = logging.getLogger(__name__)

# --- Konfiguracja Ścieżek ---
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

tesseract_folder = os.path.join(base_path, "tesseract")
poppler_folder = os.path.join(base_path, "poppler", "bin")
tesseract_cmd = os.path.join(tesseract_folder, 'tesseract.exe')
if os.path.exists(tesseract_cmd):
    os.environ['TESSDATA_PREFIX'] = os.path.join(tesseract_folder, "tessdata")
    os.environ['TESSERACT_CMD'] = tesseract_cmd
if os.path.isdir(poppler_folder):
    os.environ['POPPLER_PATH'] = poppler_folder

# --- Konfiguracja Mapowania Kolumn ---
KOLUMNY_MAPOWANIE = {
    "Data": "DATA", "Nadawca": "ORGANIZACJA", "Odbiorca": "ORGANIZACJA",
    "W sprawie": "TYTUL_PISMA", "Numer Dokumentu": "NR_DOKUMENTU",
    "Sygnatura Sprawy": "SYGNATURA_SPRAWY", "Typ Dokumentu": "TYP_DOKUMENTU"
}
KOLUMNA_Z_NAZWA_PLIKU = "Nazwa Pliku"
TYPY_DOKUMENTOW = {
    "UMOWA": ["umowa", "umowy"], "POROZUMIENIE": ["porozumienie"],
    "PROTOKÓŁ": ["protokół", "protokołu"], "ODBIÓR": ["odbiór", "odbioru"]
}

def find_all_occurrences(text: str, sub: str) -> Iterator[int]:
    """Yield indices of all occurrences of ``sub`` in ``text``."""
    start = 0
    while True:
        start = text.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)

def detect_document_type(text: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """Detect document type using simple keyword matching."""
    text_lower = text.lower()
    for doc_type, keywords in TYPY_DOKUMENTOW.items():
        for keyword in keywords:
            match = re.search(r'\b' + re.escape(keyword) + r'\b', text_lower)
            if match:
                return doc_type, match.start(), match.end()
    return None, None, None


def run_cpp_ocr(pdf_paths: List[str]) -> List[str]:
    """Wywołuje moduł C++ do równoległego OCR."""
    exe_path = os.path.join(base_path, "training_ocr")

    def _worker(paths):
        cmd = [exe_path] + paths
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            creationflags=creationflags,
        )
        return json.loads(result.stdout or "[]")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_worker, pdf_paths)
        return future.result()

def create_training_data_from_sheets(input_dir: str, log_callback: Callable[[str], None]) -> Optional[str]:
    """Krok 1: Przetwarza foldery z rozpiskami i PDF-ami na plik JSONL."""
    log_callback("Rozpoczynanie przygotowania danych treningowych...")
    training_data = []

    for root, _, files in os.walk(input_dir):
        xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
        if not xlsx_files:
            continue

        xlsx_path = os.path.join(root, xlsx_files[0])
        log_callback(f"\n--- Przetwarzanie rozpiski: {os.path.basename(xlsx_path)} ---")
        try:
            df = pd.read_excel(xlsx_path)
        except Exception as e:
            log_callback(f"!! Błąd odczytu pliku Excel: {e}")
            continue

        pdf_entries = []
        for index, row in df.iterrows():
            pdf_filename = row.get(KOLUMNA_Z_NAZWA_PLIKU)
            if not pdf_filename or not isinstance(pdf_filename, str):
                continue

            pdf_path = os.path.join(root, pdf_filename)
            if not os.path.exists(pdf_path):
                log_callback(f"!! Ostrzeżenie: Plik PDF '{pdf_filename}' nie został znaleziony.")
                continue

            pdf_entries.append((row, pdf_filename, pdf_path))

        pdf_paths = [p for (_, _, p) in pdf_entries]
        texts = []
        if pdf_paths:
            try:
                texts = run_cpp_ocr(pdf_paths)
            except Exception as e:
                log_callback(f"  !! Błąd OCR w module C++: {e}")
                texts = ["" for _ in pdf_paths]

        for (row, pdf_filename, pdf_path), full_text in zip(pdf_entries, texts):
            log_callback(f"  -> Przetwarzanie pliku: {pdf_filename}")

            entities = []
            # Wyszukiwanie na podstawie Excela
            for col_name, label in KOLUMNY_MAPOWANIE.items():
                if col_name in row and pd.notna(row[col_name]):
                    metadata_text = str(row[col_name])
                    if not metadata_text:
                        continue
                    for start_index in find_all_occurrences(full_text, metadata_text):
                        entities.append([start_index, start_index + len(metadata_text), label])

            # Automatyczne wykrywanie typu dokumentu
            doc_type, start, end = detect_document_type(full_text)
            if doc_type:
                entities.append([start, end, "TYP_DOKUMENTU"])

            if entities:
                training_data.append({"text": full_text, "label": entities})

    if not training_data:
        log_callback("Nie znaleziono żadnych danych do treningu.")
        return None

    # Zapisz do tymczasowego pliku JSONL
    output_jsonl_file = os.path.join(os.path.dirname(base_path), "temp_training_data.jsonl")
    with open(output_jsonl_file, 'w', encoding='utf-8') as f:
        for entry in training_data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
    
    log_callback(f"\n>>> Zakończono! Zapisano {len(training_data)} rekordów treningowych.")
    return output_jsonl_file

def convert_to_spacy_format(jsonl_path: str, train_path: str, dev_path: str) -> None:
    """Krok 2: Konwertuje plik JSONL na format .spacy."""
    nlp = spacy.blank("pl")
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    random.shuffle(lines)
    split_point = int(len(lines) * 0.8)
    
    for dataset_type, dataset_lines in [("train", lines[:split_point]), ("dev", lines[split_point:])]:
        db = DocBin()
        for line in dataset_lines:
            item = json.loads(line)
            text = item['text']
            doc = nlp.make_doc(text)
            ents = []
            for start, end, label in item['label']:
                span = doc.char_span(start, end, label=label)
                if span is not None:
                    ents.append(span)
            try:
                doc.ents = ents
                db.add(doc)
            except ValueError:
                pass # Ignoruj błędy, jeśli encje się nakładają
        
        output_path = train_path if dataset_type == "train" else dev_path
        db.to_disk(output_path)

def run_training_pipeline(data_folder_path: str, output_model_path: str, log_callback: Callable[[str], None]) -> bool:
    """Główna funkcja uruchamiająca cały proces treningu."""
    try:
        # Krok 1: Przygotuj dane
        jsonl_file = create_training_data_from_sheets(data_folder_path, log_callback)
        if not jsonl_file:
            return False

        # Krok 2: Przygotuj pliki .spacy
        temp_dir = os.path.join(os.path.dirname(base_path), "temp_spacy_data")
        os.makedirs(temp_dir, exist_ok=True)
        train_spacy_path = os.path.join(temp_dir, "train.spacy")
        dev_spacy_path = os.path.join(temp_dir, "dev.spacy")
        
        log_callback("\nKonwertowanie danych do formatu spaCy...")
        convert_to_spacy_format(jsonl_file, train_spacy_path, dev_spacy_path)
        log_callback("Konwersja zakończona.")

        # Krok 3: Przygotuj plik konfiguracyjny
        config_path = os.path.join(temp_dir, "config.cfg")
        base_config_path = os.path.join(temp_dir, "base_config.cfg")
        
        # Tworzenie base_config.cfg
        with open(base_config_path, "w", encoding="utf-8") as f:
            f.write("""
[paths]
train = null
dev = null
vectors = null
[system]
gpu_allocator = null
[nlp]
lang = "pl"
pipeline = ["tok2vec", "ner"]
batch_size = 1000
[components]
[components.ner]
factory = "ner"
[components.ner.model]
@architectures = "spacy.TransitionBasedParser.v2"
state_type = "ner"
extra_state_tokens = false
hidden_width = 64
maxout_pieces = 2
use_upper = true
n_tok2vec_features = 1
[components.ner.model.tok2vec]
@architectures = "spacy.Tok2Vec.v2"
[components.ner.model.tok2vec.embed]
@architectures = "spacy.MultiHashEmbed.v2"
width = 64
rows = [2000, 2000, 1000, 1000, 1000, 1000]
attrs = ["ORTH", "LOWER", "PREFIX", "SUFFIX", "SHAPE", "ID"]
include_static_vectors = false
[components.ner.model.tok2vec.encode]
@architectures = "spacy.MaxoutWindowEncoder.v2"
width = 64
window_size = 1
maxout_pieces = 3
depth = 2
[training]
dev_corpus = "corpora.dev"
train_corpus = "corpora.train"
[training.optimizer]
@optimizers = "Adam.v1"
[training.batcher]
@batchers = "spacy.batch_by_words.v1"
size = 1000
tolerance = 0.2
[corpora]
[corpora.dev]
@readers = "spacy.Corpus.v1"
path = ${paths.dev}
[corpora.train]
@readers = "spacy.Corpus.v1"
path = ${paths.train}
""")
        
        # Inicjalizacja config.cfg
        spacy.cli.init_fill_config(config_path, base_config_path)
        
        # Krok 4: Uruchom trening
        log_callback("\nRozpoczynanie treningu modelu spaCy...")
        os.makedirs(output_model_path, exist_ok=True)
        
        train(config_path, output_model_path, overrides={
            "paths.train": train_spacy_path,
            "paths.dev": dev_spacy_path,
        })
        
        log_callback(f"\nTrening zakończony! Najlepszy model zapisano w: {os.path.join(output_model_path, 'model-best')}")
        
        # Sprzątanie plików tymczasowych
        os.remove(jsonl_file)
        shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        log_callback(f"\nKRYTYCZNY BŁĄD TRENINGU: {e}\n{traceback.format_exc()}")
        return False

