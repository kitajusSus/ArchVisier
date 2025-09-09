# Archiwizator - User Guide

## 1. Introduction

Welcome to the user manual for the **Archiwizator** application. This program was created to help you quickly and efficiently organize scanned documents. The application “reads” PDF files and then automatically names and sorts them based on the extracted information.

## 2. Installation and Launching

### 2.1 Running the packaged release

The application is distributed as `Archiwizator.exe` and requires no installation. Simply copy it to a convenient location and double-click to run.

### 2.2 Building your own package (advanced)

1. Install [Python 3.11+](https://www.python.org/downloads/), [Git](https://git-scm.com/), and [Zig](https://ziglang.org/download/).
2. Clone the repository and prepare the environment:
   ```bash
   git clone https://github.com/kitajusSus/archiwizacja-IGG-helper.git
   cd archiwizacja-IGG-helper
   python -m venv venv
   venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. (Optional) install `bitsandbytes` if you plan to use the text assistant mode:
   ```bash
   pip install bitsandbytes
   ```
4. Build native components and create the distribution package:
   ```bash
   cd 2_Aplikacja_Glowna
   zig cc -O3 -shared fast_similarity.c -o fast_similarity.dll
   cd ..
   python build_exe.py
   ```
   The resulting `dist/Archiwizator` directory contains `Archiwizator.exe` along with required resources.

## 3. Main Application Window

After launching, you will see the main program window consisting of several sections:

1.  **Operating mode:** Select the type of documents you want to organize.
2.  **Input data:** Specify where the input PDFs are located and where to save the results.
3.  **Actions:** The main button for starting the analysis.
4.  **Results:** A table displaying processed documents. Here you can verify and edit data before final saving.
5.  **Save and Export:** Buttons for completing your work.

## 4. Using the Application Step by Step

### Step 1: Choose the operating mode

At the top, select one of three options depending on your task:
*   **Incoming/Outgoing Correspondence:** For standard letters, invoices, contracts, etc.
*   **Arbitration Court:** Tailored for working with documents related to a single court case.

### Step 2: Provide input data

*   **If you chose the “Arbitration Court” mode:**
    1.  An additional field **“Case Number”** will appear. Enter the case number you are working on (e.g., `I C 123/23`). This ensures all documents go into one folder.
*   **For all modes:**
    1.  **Folder with PDF scans:** Click “Select...” and point to the folder containing the PDFs to organize.
    2.  **Output folder:** Click “Select...” and choose the folder where the program should save sorted and correctly named files.

### Step 3: Scan and analyze

Click the large **“3. Scan files and analyze”** button. The program will start working, and a progress bar will show the current stage. This may take a few minutes depending on the number and complexity of documents.

### Step 4: Verify and edit data

After analysis, the results appear in the bottom table, with each row representing one document.
*   **Check data accuracy:** Ensure the program correctly recognized the date, sender, document title, etc.
*   **Edit if needed:** If any information is incorrect, **double-click it**. A small window will open where you can enter the correct value. After saving, the file name updates automatically.
*   **Watch for errors:** If an entire row is highlighted in pink, an error occurred while reading the PDF. Such files should be checked manually.

### Step 5: Save results OR export a list

Once the table data is correct, you have two options:

*   **Option A: Save changes and move files**
    *   Click this button to physically organize the files. The program copies them to the destination folder, assigns new names, and creates subfolders (in court mode).
    *   Use this option to finalize archiving.

*   **Option B: Export view to Excel**
    *   Click this button to create an `.xlsx` file containing exactly what you see in the table.
    *   The program will ask where to save the Excel file and under what name.
    *   Use this option if you need a report or document list without moving the files themselves.

You can use both options—export the list first, then save and move the files.

**Done! Your documents are now organized, and the report has been generated.**

## 5. Additional Tips and Support

- Ensure your document scans are of good quality—this improves OCR accuracy.
- If you encounter issues, consult the troubleshooting section in `README.md`.
- Report bugs or suggestions via the [issues system](https://github.com/kitajusSus/archiwizacja-IGG-helper/issues).

**Thank you for using Archiwizator!**

Developers interested in extending the application can find a separate guide in [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
