"""Trening modelu NER spaCy na podstawie eksportu z Doccano."""

import json
import os
import random
import subprocess
import sys

import spacy
from spacy.cli.train import train
from spacy.tokens import DocBin


def convert_doccano_to_spacy(input_path: str, output_path: str) -> None:
    """Convert annotated JSONL from Doccano to spaCy's binary format.

    Args:
        input_path (str): Path to the ``.jsonl`` file exported from Doccano.
        output_path (str): Destination path for the generated ``.spacy`` file.

    Returns:
        None
    """
    nlp = spacy.blank("pl")
    db = DocBin()

    with open(input_path, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f]

    for item in data:
        text = item["text"]
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in item["label"]:
            span = doc.char_span(start, end, label=label)
            if span is None:
                print(f"Pominięto encję (problem z dopasowaniem): '{text[start:end]}'")
            else:
                ents.append(span)
        try:
            doc.ents = ents
            db.add(doc)
        except ValueError as e:
            print(f"Błąd przy ustawianiu encji dla dokumentu: {text[:50]}... - {e}")

    db.to_disk(output_path)
    print(f"Pomyślnie przekonwertowano dane do formatu spaCy: {output_path}")


def main() -> None:
    """Run the full training pipeline based on Doccano annotations."""
    doccano_output_dir = "dane_wyjściowe_z_doccano"
    training_data_dir = "dane_treningowe_spacy"
    model_output_dir = "model_wyjściowy"
    config_path = "config.cfg"
    base_config_path = "base_config.cfg"

    jsonl_files = [f for f in os.listdir(doccano_output_dir) if f.endswith(".jsonl")]
    if not jsonl_files:
        print(f"Błąd: Nie znaleziono plików .jsonl w '{doccano_output_dir}'.")
        return

    doccano_file = os.path.join(doccano_output_dir, jsonl_files[0])
    print(f"Używam pliku z danymi: {doccano_file}")

    if not os.path.exists(training_data_dir):
        os.makedirs(training_data_dir)

    with open(doccano_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    random.shuffle(lines)
    split_point = int(len(lines) * 0.8)
    train_lines = lines[:split_point]
    dev_lines = lines[split_point:]

    with open("train.jsonl", "w", encoding="utf-8") as f:
        f.writelines(train_lines)
    with open("dev.jsonl", "w", encoding="utf-8") as f:
        f.writelines(dev_lines)

    convert_doccano_to_spacy("train.jsonl", os.path.join(training_data_dir, "train.spacy"))
    convert_doccano_to_spacy("dev.jsonl", os.path.join(training_data_dir, "dev.spacy"))

    os.remove("train.jsonl")
    os.remove("dev.jsonl")

    if not os.path.exists(config_path):
        print("Generowanie pliku konfiguracyjnego `config.cfg`...")
        try:
            subprocess.run(
                [
                    "python",
                    "-m",
                    "spacy",
                    "init",
                    "fill-config",
                    base_config_path,
                    config_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout).strip()
            print(f"Błąd podczas generowania pliku konfiguracyjnego: {err}")
            sys.exit(1)

    print("\nRozpoczynanie treningu modelu spaCy...")
    train(
        config_path,
        model_output_dir,
        overrides={
            "paths.train": os.path.join(training_data_dir, "train.spacy"),
            "paths.dev": os.path.join(training_data_dir, "dev.spacy"),
        },
    )
    print(
        f"\nTrening zakończony! Najlepszy model zapisano w: {os.path.join(model_output_dir, 'model-best')}"
    )


if __name__ == "__main__":
    if not os.path.exists("base_config.cfg"):
        with open("base_config.cfg", "w") as f:
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
[corpora]
[corpora.dev]
@readers = "spacy.Corpus.v1"
path = ${paths.dev}
[corpora.train]
@readers = "spacy.Corpus.v1"
path = ${paths.train}
[training]
dev_corpus = "corpora.dev"
train_corpus = "corpora.train"
[training.optimizer]
@optimizers = "Adam.v1"
[training.batcher]
@batchers = "spacy.batch_by_words.v1"
size = 1000
tolerance = 0.2
            """)
    main()

