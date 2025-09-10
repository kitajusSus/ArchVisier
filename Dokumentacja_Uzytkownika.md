# Archiwizator – User Guide

## 1. Introduction

Welcome to the user manual for **Archiwizator**. This program helps you quickly and neatly organize scanned documents. The application reads PDF files and automatically names and sorts them based on the information it finds.

## 2. Installation and Launch

### 2.1 Launching the packaged version

The application is distributed as an `Archiwizator.exe` file and requires no installation. Simply copy it to a convenient location and double-click to run.

### 2.2 Building your own package (advanced)

1. Install [Python 3.11+](https://www.python.org/downloads/), [Git](https://git-scm.com/) and [Zig](https://ziglang.org/download/).
2. Clone the repository and set up the environment:
   ```bash
   git clone https://github.com/kitajusSus/archiwizacja-IGG-helper.git
   cd archiwizacja-IGG-helper
   python -m venv venv
   venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. (Optional) Install `bitsandbytes` if you plan to use the text assistant mode:
   ```bash
   pip install bitsandbytes
   ```
4. Build the native components and prepare the distribution package:
   ```bash
   cd 2_Aplikacja_Glowna
   zig cc -O3 -shared fast_similarity.c -o fast_similarity.dll
   cd ..
   python build_exe.py
   ```
   The `dist/Archiwizator` folder will contain `Archiwizator.exe` along with the required resources.

## 3. Main Application Window

After launching the program, the main window is divided into several sections:

1. **Operating mode:** Choose what type of documents you want to organize.
2. **Input data:** Point the program to the folder with files to process and where to save the results.
3. **Actions:** The main button for starting the analysis.
4. **Results:** A table where processed documents appear. You can verify and correct data before saving.
5. **Saving and Exporting:** Buttons to finalize your work.

## 4. Using the Application Step by Step

### Step 1: Choose the operating mode

At the top, choose the mode that matches your task:
* **Incoming/Outgoing Correspondence:** Use this mode for standard letters, invoices, contracts, etc.
* **Arbitration Court:** Tailored for documents related to a single court case.

### Step 2: Specify input data

* **If you selected “Arbitration Court”:**
  1. An additional **“Case Number”** field will appear. Enter the case number you are working on (e.g., `I C 123/23`). This ensures all documents go into a single folder.
* **For all modes:**
  1. **Folder with PDF scans:** Click “Choose...” and select the folder containing the PDF files to organize.
  2. **Output folder:** Click “Choose...” and select the folder where the program should save the sorted and properly named files.

### Step 3: Scan and analyze

Click the large **“3. Scan files and analyze”** button. The program will start working, and the progress bar will show its current stage. This may take several minutes depending on the number and complexity of the documents.

### Step 4: Verify and edit data

After the analysis finishes, the results appear in the table at the bottom. Each row represents one document.
* **Check the data:** Ensure the program correctly recognized the date, sender, document title, etc.
* **Edit if necessary:** If something is incorrect, **double-click** the field. A small window opens where you can enter the correct value. After saving, the filename updates automatically.
* **Watch for errors:** If an entire row is highlighted in pink, an error occurred while reading the PDF. Such files should be checked manually.

### Step 5: Save the results OR export a spreadsheet

When the data in the table is correct, you have two options:

* **Option A: Save changes and move files**
    * Click this button to physically organize the files. The program copies them to the destination folder, gives them new names and creates subfolders (in court mode).
    * Use this option to finalize archiving.
* **Option B: Export the view to Excel**
    * Click this button to create an `.xlsx` file containing exactly what you see in the table.
    * The program will ask for a location and filename for the Excel file.
    * Use this option if you need a report or list of documents without moving the files themselves.

You can use both options: first export the spreadsheet, then save and move the files.

**Done! Your documents are now organized and the spreadsheet has been generated.**

## 5. Additional Tips and Support

- Make sure the document scans are of good quality; this improves OCR accuracy.
- If you encounter issues, consult the [Troubleshooting](README.md#troubleshooting) section of the README.
- Report bugs or suggestions through the [issue tracker](https://github.com/kitajusSus/archiwizacja-IGG-helper/issues).

**Thank you for using Archiwizator!**

Developers who want to extend the application can find additional guidance in [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

