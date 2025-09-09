# Archiwizator - Technical and Administrative Documentation

## 1. Introduction

This document describes the technical aspects of the "Archiwizator" project. It is intended for those responsible for maintaining, developing, and training the model.

**Architecture:**
*   **Language:** Python 3.9+
*   **Graphical interface:** Tkinter (standard Python library)
*   **OCR engine:** Tesseract-OCR
*   **PDF handling:** `pdf2image` (interface to Poppler)
*   **NER model:** `spaCy` (natural language processing library)

## 2. Project Structure

The project is organized in a modular manner to separate development tools from the final application.

```
archiwizacja-IGG-helper/
├── 1_Narzędzia_Treningowe/       # Scripts and data for training the model
│   ├── konwertuj_pdf_do_txt.py # PDF -> TXT converter
│   ├── trenuj_model.py         # Main training script
│   ├── base_config.cfg         # spaCy configuration template
│   └── README.md               # Training instructions
│
├── 2_Aplikacja_Główna/           # Source code of the final application
│   ├── app.py                  # Main application file
│   ├── moj_model_ner/          # Location for the trained model
│   ├── poppler/                # Library for PDF handling
│   └── tesseract/              # OCR engine
│
├── requirements.txt              # List of Python dependencies
├── Dokumentacja_Uzytkownika.md
└── Dokumentacja_Techniczna.md
```

## 3. Model Training Process

The model should be retrained periodically to improve its effectiveness or adapt to new document types. The process takes place in the `1_Narzędzia_Treningowe` folder.

### Phase 1: Data Preparation

1.  **Collect data:** Gather 50–100 representative PDF files. The more variety, the better.
2.  **Convert to TXT:** Use the `konwertuj_pdf_do_txt.py` script to batch convert PDFs into plain text.
    ```bash
    # Będąc w folderze 1_Narzędzia_Treningowe/
    python konwertuj_pdf_do_txt.py "C:\Sciezka\Do\Twoich\PDFow" "dane_do_etykietowania"
    ```

### Phase 2: Annotation in Doccano

1.  **Start Doccano:** A web-based data labeling tool.
    ```bash
    # W pierwszym terminalu
    pip install doccano
    doccano init
    doccano createuser --username admin --password twoje_haslo
    doccano webserver --port 8000

    # W drugim terminalu
    doccano task
    ```
2.  **Create a project:** In the web interface (`http://127.0.0.1:8000/`), create a `Sequence Labeling` project.
3.  **Define labels:** Add the labels the model should learn to recognize. Recommended, universal set:
    *   `DATA` (document date)
    *   `ORGANIZACJA` (company, office, or court name)
    *   `SYGNATURA_SPRAWY` (court case number)
    *   `TYTUL_PISMA` (subject or title, e.g., "Payment Demand")
    *   `NR_DOKUMENTU` (other identifiers, e.g., reference number)
4.  **Import and label:** Import `.txt` files and mark the spans corresponding to the defined labels.
5.  **Export:** After labeling, export the data in **`JSONL (spaCy)`** format and save the file in the `dane_wyjściowe_z_doccano/` folder.

### Phase 3: Training

1.  **Generate configuration:** If `config.cfg` does not exist, it will be created from `base_config.cfg`.
    ```bash
    # (Opcjonalne, skrypt trenujący robi to automatycznie)
    python -m spacy init fill-config base_config.cfg config.cfg
    ```
2.  **Run the training script:**
    ```bash
    # Będąc w folderze 1_Narzędzia_Treningowe/
    python trenuj_model.py
    ```
    The script automatically splits the data into training and development sets and then starts the training process.
3.  **Retrieve the model:** The best version of the trained model is saved in `model_wyjściowy/model-best/`.

## 4. Building the Application (.exe)

After successful training, you can build a standalone executable.

**Required tools:**

- [Zig](https://ziglang.org/download/) – compiler used to build the OCR module
- [PyInstaller](https://pyinstaller.org/en/stable/) – tool for packaging the application

1.  **Copy the model:** Move the entire contents of `model_wyjściowy/model-best/` to `2_Aplikacja_Główna/moj_model_ner/`.
2.  **Run PyInstaller:** Navigate to the `2_Aplikacja_Główna/` folder and execute:
    ```bash
      pyinstaller --noconsole --onefile --name "Archiwizator" --add-data "tesseract;tesseract" --add-data "poppler;poppler" --add-data "moj_model_ner;moj_model_ner" app.py
    ```
    *   `--noconsole`: hides the console window during application runtime
    *   `--onefile`: creates a single `.exe` file
    *   `--name`: sets the output file name
    *   `--add-data`: bundles necessary folders (Tesseract, Poppler, and our NER model) into the `.exe`

3.  **Locate the application:** The generated `Archiwizator.exe` will appear in the newly created `dist/` folder.

## 5. Development Environment and Tests

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```
2. Install dependencies and optional packages:
   ```bash
   pip install -r requirements.txt
   pip install -e .[ocr,training]
   ```
3. Build native modules:
   ```bash
   cmake -S native_c -B native_c/build
   cmake --build native_c/build --config Release
   cd zig_modules/token_similarity
   zig build -Drelease-safe
   cd ../..
   ```
4. Run unit tests:
   ```bash
   pytest
   ```

More detailed contributor guidelines can be found in [CONTRIBUTING.md](CONTRIBUTING.md).

## 6. Application Configuration

OCR parameters and application behavior can be adjusted in the `config.json` file. The new `ocr_workers` option sets the number of threads used for OCR processing. The default value `0` automatically uses all available CPU cores.
