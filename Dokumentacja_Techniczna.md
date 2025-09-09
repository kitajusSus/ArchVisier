# Archiwizator - Dokumentacja Techniczna i Administratorska

## 1. Wprowadzenie

Niniejszy dokument opisuje techniczną stronę projektu "Archiwizator". Przeznaczony jest dla osób odpowiedzialnych za utrzymanie, rozwój oraz trenowanie modelu.

**Architektura:**
*   **Język:** Python 3.9+
*   **Interfejs graficzny:** Tkinter (standardowa biblioteka Pythona)
*   **Silnik OCR:** Tesseract-OCR
*   **Obsługa PDF:** `pdf2image` (interfejs do Poppler)
*   **Model NER:** `spaCy` (biblioteka do przetwarzania języka naturalnego)

## 2. Struktura Projektu

Projekt jest zorganizowany w sposób modułowy, aby oddzielić narzędzia deweloperskie od finalnej aplikacji.

```
archiwizacja-IGG-helper/
├── 1_Narzędzia_Treningowe/       # Skrypty i dane do trenowania modelu
│   ├── konwertuj_pdf_do_txt.py # Konwerter PDF -> TXT
│   ├── trenuj_model.py         # Główny skrypt trenujący
│   ├── base_config.cfg         # Szablon konfiguracji dla spaCy
│   └── README.md               # Instrukcja treningu
│
├── 2_Aplikacja_Główna/           # Kod źródłowy finalnej aplikacji
│   ├── app.py                  # Główny plik aplikacji
│   ├── moj_model_ner/          # Miejsce na wytrenowany model
│   ├── poppler/                # Biblioteka do obsługi PDF
│   └── tesseract/              # Silnik OCR
│
├── requirements.txt              # Lista zależności Python
├── Dokumentacja_Uzytkownika.md
└── Dokumentacja_Techniczna.md
```

## 3. Proces Trenowania Modelu

Model należy okresowo trenować na nowo, aby poprawić jego skuteczność lub dostosować do nowych typów dokumentów. Proces odbywa się w folderze `1_Narzędzia_Treningowe`.

### Faza 1: Przygotowanie Danych

1.  **Zgromadź dane:** Zbierz 50-100 reprezentatywnych plików PDF. Im większa różnorodność, tym lepiej.
2.  **Konwertuj do TXT:** Użyj skryptu `konwertuj_pdf_do_txt.py`, aby masowo przetworzyć pliki PDF na format tekstowy.
    ```bash
    # Będąc w folderze 1_Narzędzia_Treningowe/
    python konwertuj_pdf_do_txt.py "C:\Sciezka\Do\Twoich\PDFow" "dane_do_etykietowania"
    ```

### Faza 2: Etykietowanie (Annotacja) w Doccano

1.  **Uruchom Doccano:** Jest to webowe narzędzie do etykietowania danych.
    ```bash
    # W pierwszym terminalu
    pip install doccano
    doccano init
    doccano createuser --username admin --password twoje_haslo
    doccano webserver --port 8000

    # W drugim terminalu
    doccano task
    ```
2.  **Stwórz projekt:** W interfejsie webowym (`http://127.0.0.1:8000/`) stwórz projekt typu `Sequence Labeling`.
3.  **Zdefiniuj etykiety:** Dodaj etykiety, które model ma się nauczyć rozpoznawać. Zalecany, uniwersalny zestaw:
    *   `DATA` (Data dokumentu)
    *   `ORGANIZACJA` (Nazwa firmy, urzędu, sądu)
    *   `SYGNATURA_SPRAWY` (Sygnatura akt sprawy sądowej)
    *   `TYTUL_PISMA` (Temat, tytuł, np. "Wezwanie do zapłaty")
    *   `NR_DOKUMENTU` (Inne identyfikatory, np. L.dz.)
4.  **Importuj i etykietuj:** Zaimportuj pliki `.txt` i oznacz w nich fragmenty odpowiadające zdefiniowanym etykietom.
5.  **Eksportuj:** Po zakończeniu etykietowania, wyeksportuj dane w formacie **`JSONL (spaCy)`** i zapisz plik w folderze `dane_wyjściowe_z_doccano/`.

### Faza 3: Trening

1.  **Wygeneruj konfigurację:** Jeśli plik `config.cfg` nie istnieje, zostanie on stworzony na podstawie `base_config.cfg`.
    ```bash
    # (Opcjonalne, skrypt trenujący robi to automatycznie)
    python -m spacy init fill-config base_config.cfg config.cfg
    ```
2.  **Uruchom skrypt trenujący:**
    ```bash
    # Będąc w folderze 1_Narzędzia_Treningowe/
    python trenuj_model.py
    ```
    Skrypt automatycznie podzieli dane na zbiór treningowy i deweloperski, a następnie rozpocznie proces treningu.
3.  **Pobierz model:** Najlepsza wersja wytrenowanego modelu zostanie zapisana w folderze `model_wyjściowy/model-best/`.

## 4. Budowanie Aplikacji (.exe)

Po pomyślnym treningu można zbudować samodzielny plik wykonywalny.

**Wymagane narzędzia:**

- [Zig](https://ziglang.org/download/) – kompilator używany do budowy modułu OCR
- [PyInstaller](https://pyinstaller.org/en/stable/) – narzędzie do pakowania aplikacji

1.  **Skopiuj model:** Przenieś całą zawartość folderu `model_wyjściowy/model-best/` do `2_Aplikacja_Główna/moj_model_ner/`.
2.  **Uruchom PyInstaller:** Przejdź do folderu `2_Aplikacja_Główna/` i wykonaj polecenie:
    ```bash
      pyinstaller --noconsole --onefile --name "Archiwizator" --add-data "tesseract;tesseract" --add-data "poppler;poppler" --add-data "moj_model_ner;moj_model_ner" app.py
    ```
    *   `--noconsole`: Ukrywa czarne okno konsoli podczas działania aplikacji.
    *   `--onefile`: Tworzy jeden plik `.exe`.
    *   `--name`: Nadaje nazwę plikowi wynikowemu.
    *   `--add-data`: Dołącza do pliku `.exe` niezbędne foldery (Tesseract, Poppler i nasz model NER).

3.  **Znajdź aplikację:** Gotowy plik `Archiwizator.exe` będzie znajdował się w nowo utworzonym folderze `dist/`.

## 5. Środowisko deweloperskie i testy

1. Utwórz i aktywuj środowisko wirtualne:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```
2. Zainstaluj zależności i pakiety opcjonalne:
   ```bash
   pip install -r requirements.txt
   pip install -e .[ocr,training]
   ```
3. Zbuduj moduły natywne:
   ```bash
   cmake -S native_c -B native_c/build
   cmake --build native_c/build --config Release
   cd zig_modules/token_similarity
   zig build -Drelease-safe
   cd ../..
   ```
4. Uruchom testy jednostkowe:
   ```bash
   pytest
   ```

Pełniejsze wytyczne dla kontrybutorów znajdują się w [CONTRIBUTING.md](CONTRIBUTING.md).

## 6. Konfiguracja aplikacji

Parametry OCR oraz zachowanie aplikacji można dostosować w pliku `config.json`.
Nowa opcja `ocr_workers` określa liczbę wątków używanych do przetwarzania OCR.
Domyślna wartość `0` powoduje automatyczne wykorzystanie wszystkich dostępnych rdzeni CPU.
