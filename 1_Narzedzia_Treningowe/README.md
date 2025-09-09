# Training Tools

A set of scripts that assist with data preparation and training the NER model used in the Archiwizator application.

## PDF → TXT Conversion

`konwertuj_pdf_do_txt.py` — batch converts PDF files to plain text.

```bash
python konwertuj_pdf_do_txt.py <folder_z_pdfami> <folder_na_txt>
```

## Generating data from spreadsheets

`przygotuj_dane_z_rozpisek.py` — merges spreadsheet metadata with PDF content and creates a JSONL file for spaCy.

```bash
python przygotuj_dane_z_rozpisek.py <katalog_z_rozpiskami>
```

The resulting file is saved in `dane_wyjściowe_z_doccano/`.

## Model Training

`trenuj_model.py` — converts data from Doccano into spaCy format and starts the training process.

```bash
python trenuj_model.py
```

The output model can be found in `model_wyjściowy/model-best/`.

The scripts assume Tesseract and Poppler are present in the `2_Aplikacja_Glowna` directory. Detailed instructions are available in [Dokumentacja_Techniczna.md](../Dokumentacja_Techniczna.md).
