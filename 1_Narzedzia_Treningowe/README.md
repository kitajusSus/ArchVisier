# Training Tools

Collection of scripts that support preparing data and training the NER model used in the Archiwizator application.

## PDF → TXT Conversion

`konwertuj_pdf_do_txt.py` — converts PDF files to plain text in batch.

```bash
python konwertuj_pdf_do_txt.py <pdf_folder> <txt_folder>
```

## Generating Data from Spreadsheets

`przygotuj_dane_z_rozpisek.py` — merges spreadsheet metadata with PDF content and creates a JSONL file for spaCy.

```bash
python przygotuj_dane_z_rozpisek.py <spreadsheets_folder>
```

The resulting file is saved in `dane_wyjściowe_z_doccano/`.

## Model Training

`trenuj_model.py` — converts Doccano data to spaCy format and launches the training process.

```bash
python trenuj_model.py
```

The trained model will be located in `model_wyjściowy/model-best/`.

These scripts assume that Tesseract and Poppler are available in the `2_Aplikacja_Glowna` directory. Details of the process are described in [Dokumentacja_Techniczna.md](../Dokumentacja_Techniczna.md).
