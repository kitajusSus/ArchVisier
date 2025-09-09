# Narzędzia Treningowe

Zbiór skryptów wspierających przygotowanie danych i trenowanie modelu NER wykorzystywanego w aplikacji Archiwizator.

## Konwersja PDF → TXT

`konwertuj_pdf_do_txt.py` — masowo przetwarza pliki PDF na zwykły tekst.

```bash
python konwertuj_pdf_do_txt.py <folder_z_pdfami> <folder_na_txt>
```

## Generowanie danych z rozpisek

`przygotuj_dane_z_rozpisek.py` — łączy metadane z arkuszy kalkulacyjnych z treścią PDF i tworzy plik JSONL dla spaCy.

```bash
python przygotuj_dane_z_rozpisek.py <katalog_z_rozpiskami>
```

Wynikowy plik zostaje zapisany w `dane_wyjściowe_z_doccano/`.

## Trening modelu

`trenuj_model.py` — konwertuje dane z Doccano na format spaCy i uruchamia proces trenowania.

```bash
python trenuj_model.py
```

Model wyjściowy znajdziesz w katalogu `model_wyjściowy/model-best/`.

Skrypty zakładają obecność Tesseract i Popplera w katalogu `2_Aplikacja_Glowna`. Szczegóły procesu opisano w [Dokumentacja_Techniczna.md](../Dokumentacja_Techniczna.md).
