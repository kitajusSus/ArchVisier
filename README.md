# Archiwizator

![Version](https://img.shields.io/badge/version-3.2-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
[![CI](https://github.com/OWNER/archiwizacja-IGG-helper/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/archiwizacja-IGG-helper/actions/workflows/ci.yml)

**Author:** kitajusSus  
**Last updated:** 2025-08-22

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [User Guide](#user-guide)
   - [Training and Updating the NER Model](#training-and-updating-the-ner-model)
6. [Operating Modes](#operating-modes)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)
9. [Used Technologies and Licenses](#used-technologies-and-licenses)
10. [License](#license)
11. [Coding Standards](#coding-standards)
12. [Licensing Policy](#licensing-policy)
13. [Developer Guide](#developer-guide)

## Introduction

**Archiwizator** is a desktop application designed to automate the archiving of scanned PDF documents. The program uses an OCR engine (Tesseract) to read document content and a NER model (based on the spaCy library) to recognize and extract key information such as dates, organization names, document titles, or court case numbers. The project is developed with **Windows 11** in mind.

The application enables intelligent sorting and naming of files based on their contents, significantly speeding up and standardizing work with a digital archive.

A full user guide with step-by-step instructions is available in [Dokumentacja_Uzytkownika.md](Dokumentacja_Uzytkownika.md).

## Features

- **Three modes:** Incoming Correspondence, Outgoing Correspondence, Arbitration Court
- **Automatic data recognition** using a custom-trained NER model
- **Intelligent document sorting** into folders based on case numbers
- **Advanced OCR engine** with image quality optimization for better recognition accuracy
- **Text assistant support** (Microsoft Phi-3 Mini) for more accurate document analysis
- **Graphical interface** allowing verification and manual correction of data before saving
- **Data export** to Excel files

## System Requirements

- **Operating system:** Windows 11 (compatible with Windows 10)
- **Minimum hardware:**
  - Processor: Intel Core i3 / AMD Ryzen 3 or newer
  - RAM: 8 GB (16 GB recommended when using the text assistant)
  - Free disk space: 500 MB + an additional 2 GB for the assistant module (optional)
- **Required libraries** (already bundled with the application):
  - Tesseract OCR
  - Poppler
  - NER model (spaCy)
  - Microsoft Phi-3 Mini (optional)
  - bitsandbytes (required for 4-bit quantization of the text assistant mode)

## Installation

### Installation from .exe (recommended)

1. Download the latest release from the [project repository](https://github.com/kitajusSus/archiwizacja-IGG-helper/releases)
2. Extract the archive to a chosen folder (e.g., `C:\Program Files\Archiwizator`)
3. Run `Archiwizator.exe`

### Installation from source (advanced)

**Required tools:**

- [Zig](https://ziglang.org/download/) – compiler used to build the `training_ocr` module
- [PyInstaller](https://pyinstaller.org/en/stable/) – packages the application (`pip install pyinstaller`)

1. Clone the repository:
   ```
   git clone https://github.com/kitajusSus/archiwizacja-IGG-helper.git
   cd archiwizacja-IGG-helper
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   pip install bitsandbytes
   ```
   The `bitsandbytes` package is required to support 4-bit quantization of the text assistant mode.
4. Download Tesseract libraries (headers and dlls):
   ```
   python fetch_tesseract.py
   ```
   The script automatically downloads and extracts a precompiled Tesseract package
   (by default the latest build for Windows or the 5.4.0 archive for Linux) into
   `2_Aplikacja_Glowna/tesseract`, ensuring a reproducible build process. If needed you can specify a custom link:

   ```
   python fetch_tesseract.py --url <archive-link>
   ```

5. Run the application:
   ```
   python 2_Aplikacja_Glowna/app.py
   ```

6. Build a standalone package (optional):
   ```
   python build_exe.py
   ```
   The script uses the `zig` compiler by default to create the `training_ocr` binary and PyInstaller to generate the
   `dist/Archiwizator` folder with included licenses. Another compiler (e.g., `clang++` or `clang-cl`) can be selected via the
   `--compiler` option or the `ARCHIWIZATOR_COMPILER` environment variable.

### Launching the Tauri interface (React + Bun)

The front end built with React and Tauri is located in `gui_tauri/`.
To start development mode:

```bash
cd gui_tauri
bun install
bunx tauri dev
```

To build a standalone application:

```bash
bunx tauri build
```

The `Ping` component uses the `http://127.0.0.1:5000/ping` endpoint and includes a built-in PDF preview.

### GUI and test launch scripts

Helper scripts simplifying work with the interfaces and tests are available in the `scripts/` directory:

```bash
# Qt/Native GUI
bash scripts/run_gui_native.sh

# Tauri/React GUI
bash scripts/run_gui_tauri.sh

# Backend tests
bash scripts/run_tests.sh
```

### Tkinter vs PySide6 interface benchmark

For a quick comparison of GUI start-up times there is a `gui_native/benchmark_ui.py` script. It requires the **PySide6** package and the standard `tkinter` (available in Python for Windows).

```bash
pip install -r gui_native/requirements.txt
python gui_native/benchmark_ui.py
```

### Compiling the `fast_similarity` module

The repository does not contain precompiled `fast_similarity.dll`,
`fast_similarity.lib`, or `fast_similarity.pdb` files. To recreate them, go to
the `2_Aplikacja_Glowna` directory and run:

```
./build_fast_similarity.sh
```

The `build_fast_similarity.sh` script in `2_Aplikacja_Glowna` can build both versions of the cosine similarity library:
the classic C implementation (`libfast_similarity.so` or `fast_similarity.dll`) and the Zig variant using SIMD
(`libfast_similarity_zig.so` or `fast_similarity_zig.dll`).

For Windows, compile the C version with:

```
zig cc -O3 -shared fast_similarity.c -o fast_similarity.dll
```

To create the fast Zig implementation (e.g., for Linux), use:

```
zig build-lib fast_similarity.zig -O ReleaseFast -fPIC -dynamic -femit-bin=libfast_similarity_zig.so
```

The script stores the libraries in the same directory, and the Python module automatically detects them here and in the `native` subfolder.

### Compiling the `token_similarity` module

The token similarity module written in Zig is located in
`zig_modules/token_similarity`. To build the shared library:

```bash
cd zig_modules/token_similarity
zig build -Doptimize=ReleaseFast
```

After compilation the `libtoken_similarity.so` file will be available in
`zig_modules/token_similarity/zig-out/lib`. The Python wrapper
`python/zig_token_similarity.py` exposes the `token_similarity` function by
loading this library with `ctypes`.

### Compiling the `token_similarity` module (C)

The `native_c` directory contains a version of the same function written in C under the MIT license. To build the shared library:

```bash
cd native_c
cmake -S . -B build
cmake --build build --config Release
```

The resulting `libtoken_similarity.so` file will be located in `native_c/build`.
The Python module `python/token_similarity.py` loads this library via
`ctypes` and provides the `token_similarity` function.

## User Guide

### First Run

On the first launch of the application:

1. Check that the NER model loaded correctly (no error messages at the bottom of the window)
2. If you want to use the text assistant (Phi-3 Mini), select **Tools > Download/Manage Model**
3. Wait for the model to download (this takes a few minutes and requires about 2 GB of space)

### Basic Workflow

1. **Choose the operating mode** appropriate for your documents

2. **Select folders:**
   - **Input folder**: the directory containing the PDF files to process
   - **Output folder**: where processed files will be saved

3. **Start processing** by clicking the “Scan files and analyze” button

4. **Verify and edit results:**
   - Review the detected information in the table
   - Double-click a cell to edit its value if needed
   - New filenames are automatically generated based on the edited data

5. **Save changes and move files** by clicking the appropriate button
   - Files will be copied to the output folder with new names
   - In “Arbitration Court” mode, files are additionally sorted into folders by case number

### Training and Updating the NER Model

1. In the **Tools** menu select **Train a new AI model**
2. Point to a folder with training data (PDF files and Excel sheets describing fields)
3. Start training and monitor the progress in the log window
4. After training finishes, restart the application – the new model will be automatically loaded from the `custom_ner_model` directory
5. The status bar at the bottom of the window indicates whether the NER model is functioning properly

### Using the Text Assistant

1. Check the “Use text assistant” option before starting analysis
2. The assistant helps more accurately recognize:
   - Document types (agreement, letter, protocol, etc.)
   - Document subjects/titles
   - Organization data
   - Numbers and case identifiers

## Operating Modes

### Incoming / Outgoing Correspondence

This mode is intended for archiving standard company correspondence:
- **Filename format:** `YYYY-MM-DD_DOCUMENT-TYPE_Subject_Sender-Recipient.pdf`
- **Recognized fields:** Date, Sender/Recipient, Subject, Document Type, Document Number

### Arbitration Court

This mode is intended for archiving court and legal documents:
- **Filename format:** `YYYY-MM-DD_DOCUMENT-TYPE_[CaseNumber]_Document-Title_Sender.pdf`
- **Folder structure:** Documents are automatically sorted into subfolders based on case numbers
- **Requires:** entering the case number in the form field

## Troubleshooting

### Problem 1: Cannot load NER model

**Error message:** “ERROR: NER model not loaded!”

**Solution:**
1. Make sure the `moj_model_ner` folder is in the same directory as the application
2. Ensure the folder contains all required files and subdirectories (ner, tok2vec, vocab, morphology)
3. If the `morphology` directory is missing, use the following script:
```python
import spacy
import pl_core_news_md
import os
import shutil

# Script to create missing files
source_model = pl_core_news_md.load().path
target_model = os.path.join('2_Aplikacja_Glowna', 'moj_model_ner')

for root, dirs, files in os.walk(source_model):
    relative_path = os.path.relpath(root, source_model)
    target_path = os.path.join(target_model, relative_path) if relative_path != "." else target_model

    # Create missing directories
    for dir_name in dirs:
        source_dir = os.path.join(root, dir_name)
        dest_dir = os.path.join(target_path, dir_name)
        if not os.path.exists(dest_dir):
            print(f"Copying directory: {dest_dir}")
            shutil.copytree(source_dir, dest_dir)
```

If the application logs show “Failed to load spaCy model,” install the default model with:

```bash
python -m spacy download pl_core_news_sm
```

### Problem 2: OCR error - “Poppler not installed”

**Error message:** “Unable to get page count. Is poppler installed and in PATH?”

**Solution:**
1. Check that the `poppler` folder with a `bin` subdirectory is in the same location as the application
2. Download Poppler for Windows and place it in the proper location:
   - https://github.com/oschwartz10612/poppler-windows/releases/

### Problem 3: The application is slow when analyzing documents

**Solution:**
1. Disable the “Use text assistant” option – analysis will be faster but less accurate
2. Process smaller batches of documents at once (max 20–30 files)
3. Close other resource-intensive applications

### Problem 4: ImportError related to `pydantic`

**Error message:** `ImportError: cannot import name 'GetCoreSchemaHandler' from 'pydantic'`

**Solution:**
1. Upgrade `pydantic` to version 2 or newer:
   ```bash
   pip install -U "pydantic>=2.0"
   ```
2. If you use a virtual environment, reinstall the dependencies after upgrading:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

## FAQ

### How does the application name files?

The program automatically generates filenames based on detected metadata. The format depends on the selected mode and includes the date, document type, and other relevant information.

### Can I edit automatically detected data?

Yes. Double-click any cell in the results table to edit its contents. After saving changes, the new filename is automatically updated.

### Does the application modify original PDF files?

No. The application creates copies of files with new names in the destination folder. Original files remain unchanged.

### Can I export data to formats other than Excel?

Currently the application only supports exporting to Excel (.xlsx). Additional formats are planned for future versions.

## Used Technologies and Licenses

| Library/Tool | License | Usage |
|--------------|---------|-------|
| spaCy | MIT | NER engine (Named Entity Recognition) |
| Pillow | HPND | Image processing |
| OpenCV | Apache 2.0 | Image processing and optimization for OCR |
| pandas | BSD | Data manipulation and export to Excel |
| openpyxl | MIT | Handling Excel files |
| pdf2image | MIT | Converting PDF to images |
| pytesseract | Apache 2.0 | OCR engine |
| tkinter | PSF | Graphical interface |
| torch | BSD | Language model support |
| transformers | Apache 2.0 | Handling the Phi-3 Mini model |
| accelerate | Apache 2.0 | Optimization of language models |
| safetensors | Apache 2.0 | Safe tensor storage |
| sentencepiece | Apache 2.0 | Text tokenization for language models |
| cryptography | Unknown | Encoding and hashing records |

All listed libraries are used in accordance with their licenses. Full texts are available on the project pages or in the respective repositories.

## License

Archiwizator is distributed under the Apache 2.0 license. See the [LICENSE](LICENSE) file included with the application for details.

---

## Developer Guide

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```
2. Install dependencies including optional packages:
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
5. Build an installer package (optional):
   ```bash
   python build_exe.py
   ```
   Optionally specify a different compiler, e.g.:
   ```bash
   python build_exe.py --compiler clang++
   ```

Detailed guidelines can be found in [CONTRIBUTING.md](CONTRIBUTING.md) and the technical documentation [Dokumentacja_Techniczna.md](Dokumentacja_Techniczna.md).

