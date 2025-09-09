
# Archiwizator

![Wersja](https://img.shields.io/badge/wersja-3.2-blue)
![Licencja](https://img.shields.io/badge/licencja-Apache%202.0-green)
[![CI](https://github.com/OWNER/archiwizacja-IGG-helper/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/archiwizacja-IGG-helper/actions/workflows/ci.yml)

**Autor:** kitajusSus  
**Data aktualizacji:** 2025-08-22

## Spis treści
1. [Wprowadzenie](#wprowadzenie)
2. [Funkcje](#funkcje)
3. [Wymagania systemowe](#wymagania-systemowe)
4. [Instalacja](#instalacja)
5. [Instrukcja obsługi](#instrukcja-obsługi)
   - [Trenowanie i aktualizacja modelu NER](#trenowanie-i-aktualizacja-modelu-ner)
6. [Tryby pracy](#tryby-pracy)
7. [Rozwiązywanie problemów](#rozwiązywanie-problemów)
8. [FAQ](#faq)
9. [Użyte technologie i licencje](#użyte-technologie-i-licencje)
10. [Licencja](#licencja)
11. [Standardy kodowania](#standardy-kodowania)
12. [Polityka licencyjna](#polityka-licencyjna)
13. [Przewodnik dla deweloperów](#przewodnik-dla-deweloperów)

## Wprowadzenie

**Archiwizator** to aplikacja desktopowa stworzona w celu automatyzacji procesu archiwizacji skanów dokumentów PDF. Program wykorzystuje silnik OCR (Tesseract) do odczytu treści dokumentów oraz model NER (oparty o bibliotekę spaCy) do rozpoznawania i ekstrakcji kluczowych informacji, takich jak daty, nazwy organizacji, tytuły pism czy sygnatury spraw sądowych. Projekt rozwijany jest z myślą o środowisku **Windows 11**.

Aplikacja pozwala na inteligentne sortowanie i nazywanie plików na podstawie ich treści, co znacząco przyspiesza i standaryzuje pracę z cyfrowym archiwum.

Pełny poradnik użytkownika wraz z instrukcjami krok po kroku znajduje się w pliku [Dokumentacja_Uzytkownika.md](Dokumentacja_Uzytkownika.md).

## Funkcje

- **Trzy tryby pracy:** Korespondencja Przychodząca, Korespondencja Wychodząca, Sąd Arbitrażowy
- **Automatyczne rozpoznawanie danych** za pomocą własnego, wytrenowanego modelu NER
- **Inteligentne sortowanie dokumentów** do folderów na podstawie sygnatury sprawy
- **Zaawansowany silnik OCR** z optymalizacją jakości obrazu dla lepszej dokładności odczytu
- **Wsparcie asystenta tekstowego** (Microsoft Phi-3 Mini) dla dokładniejszej analizy dokumentów
- **Interfejs graficzny** pozwalający na weryfikację i ręczną korektę danych przed zapisaniem
- **Eksport danych** do plików Excel

## Wymagania systemowe

- **System operacyjny:** Windows 11 (kompatybilny z Windows 10)
- **Minimalne wymagania sprzętowe:**
  - Procesor: Intel Core i3 / AMD Ryzen 3 lub nowszy
  - Pamięć RAM: 8 GB (16 GB zalecane przy używaniu asystenta tekstowego)
  - Wolne miejsce na dysku: 500 MB + dodatkowe 2 GB dla modułu asystenta (opcjonalnie)
- **Wymagane biblioteki** (już dołączone do aplikacji):
  - Tesseract OCR
  - Poppler
  - Model NER (spaCy)
  - Microsoft Phi-3 Mini (opcjonalnie)
  - bitsandbytes (wymagane do kwantyzacji 4-bitowej trybu asystenta tekstowego)

## Instalacja

### Instalacja z pliku .exe (zalecane)

1. Pobierz najnowszą wersję z [repozytorium projektu](https://github.com/kitajusSus/archiwizacja-IGG-helper/releases)
2. Rozpakuj archiwum do wybranego folderu (np. `C:\Program Files\Archiwizator`)
3. Uruchom plik `Archiwizator.exe`

### Instalacja ze źródeł (dla zaawansowanych)

**Wymagane narzędzia:**

- [Zig](https://ziglang.org/download/) – kompilator używany do zbudowania modułu `training_ocr`
- [PyInstaller](https://pyinstaller.org/en/stable/) – pakowanie aplikacji (instalacja: `pip install pyinstaller`)

1. Sklonuj repozytorium:
   ```
   git clone https://github.com/kitajusSus/archiwizacja-IGG-helper.git
   cd archiwizacja-IGG-helper
   ```

2. Utwórz środowisko wirtualne:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Zainstaluj zależności:
   ```
   pip install -r requirements.txt
   pip install bitsandbytes
   ```
   Pakiet `bitsandbytes` jest wymagany do obsługi kwantyzacji 4-bitowej trybu asystenta tekstowego.
4. Pobierz biblioteki Tesseract (nagłówki i dll):
   ```
   python fetch_tesseract.py
   ```
   Skrypt automatycznie pobiera i rozpakowuje prekompilowany pakiet Tesseract
   (domyślnie najnowszy build dla Windows lub archiwum 5.4.0 dla Linuksa) do
   katalogu `2_Aplikacja_Glowna/tesseract`, co zapewnia powtarzalność procesu
   budowania.  W razie potrzeby możesz wskazać własny link:

   ```
   python fetch_tesseract.py --url <link-do-archiwum>
   ```

 

5. Uruchom aplikację:
   ```
   python 2_Aplikacja_Glowna/app.py
   ```

6. Zbuduj samodzielną paczkę (opcjonalnie):
   ```
   python build_exe.py
   ```
   Skrypt domyślnie wykorzystuje kompilator `zig` do stworzenia pliku `training_ocr` oraz PyInstaller do wygenerowania katalogu `dist/Archiwizator` z dołączonymi licencjami.  Inny kompilator (np. `clang++` lub `clang-cl`) można wybrać poprzez opcję `--compiler` lub ustawienie zmiennej środowiskowej `ARCHIWIZATOR_COMPILER`.
### Uruchomienie interfejsu Tauri (React + Bun)

Front-end oparty o React i Tauri znajduje się w katalogu `gui_tauri/`.
Aby uruchomić tryb deweloperski:

```bash
cd gui_tauri
bun install
bunx tauri dev
```

Aby zbudować samodzielną aplikację:

```bash
bunx tauri build
```

Komponent `Ping` wykorzystuje endpoint `http://127.0.0.1:5000/ping` oraz wbudowany podgląd PDF.

### Skrypty uruchamiania GUI i testów

W katalogu `scripts/` dostępne są pomocnicze skrypty upraszczające pracę z interfejsami i testami:

```bash
# Qt/Native GUI
bash scripts/run_gui_native.sh

# Tauri/React GUI
bash scripts/run_gui_tauri.sh

# Testy backendu
bash scripts/run_tests.sh
```


### Benchmark interfejsów Tkinter vs PySide6

Do szybkiego porównania czasu startu interfejsów graficznych dostępny jest skrypt `gui_native/benchmark_ui.py`. Wymaga on zainstalowanego pakietu **PySide6** oraz standardowego `tkinter` (obecnego w Pythonie dla Windows).

```bash
pip install -r gui_native/requirements.txt
python gui_native/benchmark_ui.py
```



### Kompilacja modułu `fast_similarity`

Repozytorium nie zawiera prekompilowanych plików `fast_similarity.dll`,
`fast_similarity.lib` ani `fast_similarity.pdb`. Aby je odtworzyć, przejdź do
katalogu `2_Aplikacja_Glowna` i uruchom skrypt:

```
./build_fast_similarity.sh
```

W katalogu `2_Aplikacja_Glowna` znajduje się skrypt `build_fast_similarity.sh`,
który potrafi zbudować obie wersje biblioteki kosinusowego podobieństwa:
klasyczną implementację w C (`libfast_similarity.so` lub `fast_similarity.dll`)
oraz wariant w Zig wykorzystujący SIMD
(`libfast_similarity_zig.so` lub `fast_similarity_zig.dll`).

Dla systemu Windows można skompilować wersję w C poleceniem:

```
zig cc -O3 -shared fast_similarity.c -o fast_similarity.dll
```

Aby utworzyć szybką implementację w Zig (np. dla Linuksa), użyj:

```
zig build-lib fast_similarity.zig -O ReleaseFast -fPIC -dynamic -femit-bin=libfast_similarity_zig.so
```

Skrypt zapisuje biblioteki w tym samym katalogu, a moduł Pythona automatycznie
wykrywa je zarówno tutaj, jak i w podfolderze `native`.

### Kompilacja modułu `token_similarity`

Moduł obliczający podobieństwo tokenów napisany w Zig znajduje się w katalogu
`zig_modules/token_similarity`. Aby zbudować bibliotekę współdzieloną:

```bash
cd zig_modules/token_similarity
zig build -Doptimize=ReleaseFast
```

Po kompilacji plik `libtoken_similarity.so` będzie dostępny w
`zig_modules/token_similarity/zig-out/lib`. Pythonowy wrapper
`python/zig_token_similarity.py` udostępnia funkcję `token_similarity`, która
ładuje tę bibliotekę przy użyciu `ctypes`.

### Kompilacja modułu `token_similarity` (C)

W katalogu `native_c` znajduje się wersja tej samej funkcji napisana w C na
licencji MIT. Aby zbudować bibliotekę współdzieloną:

```bash
cd native_c
cmake -S . -B build
cmake --build build --config Release
```

Powstały plik `libtoken_similarity.so` będzie znajdował się w `native_c/build`.
Moduł Pythona `python/token_similarity.py` ładuje tę bibliotekę za pomocą
`ctypes` i udostępnia funkcję `token_similarity`.

## Instrukcja obsługi

### Pierwsze uruchomienie

Przy pierwszym uruchomieniu aplikacji:

1. Sprawdź czy model NER został poprawnie załadowany (brak komunikatów o błędach na dole okna)
2. Jeśli chcesz korzystać z asystenta tekstowego (Phi-3 Mini), wybierz z menu **Narzędzia > Pobierz/Zarządzaj modelem**
3. Poczekaj na pobranie modelu (zajmie to kilka minut, wymagane około 2 GB miejsca)

### Podstawowy proces pracy

1. **Wybierz tryb pracy** odpowiedni dla Twoich dokumentów

2. **Wskaż foldery:**
   - **Folder wejściowy**: katalog zawierający pliki PDF do przetworzenia
   - **Folder wyjściowy**: miejsce, gdzie zostaną zapisane przetworzone pliki

3. **Uruchom proces przetwarzania** klikając przycisk "Skanuj pliki i analizuj"

4. **Zweryfikuj i edytuj wyniki:**
   - Przejrzyj wykryte informacje w tabeli
   - W razie potrzeby kliknij dwukrotnie na komórkę, aby edytować wartość
   - Nowe nazwy plików są automatycznie generowane na podstawie edytowanych danych

5. **Zapisz zmiany i przenieś pliki** klikając odpowiedni przycisk
   - Pliki zostaną skopiowane do folderu wyjściowego z nowymi nazwami
   - W trybie "Sąd Arbitrażowy" pliki będą dodatkowo posortowane do folderów według sygnatur

### Trenowanie i aktualizacja modelu NER

1. W menu **Narzędzia** wybierz opcję **Trenuj nowy model AI**.
2. Wskaż folder z danymi treningowymi (PDF-y oraz arkusze Excel z opisem pól).
3. Rozpocznij trening i obserwuj postęp w logu okna.
4. Po zakończeniu treningu uruchom ponownie aplikację – nowy model zostanie automatycznie załadowany z katalogu `custom_ner_model`.
5. Stan paska na dole okna informuje, czy model NER działa poprawnie.

### Korzystanie z asystenta tekstowego

1. Zaznacz opcję "Użyj asystenta tekstowego" przed uruchomieniem analizy
2. Asystent pomoże w bardziej precyzyjnym rozpoznawaniu:
   - Typów dokumentów (umowa, pismo, protokół itp.)
   - Tematów/tytułów pism
   - Danych organizacji
   - Numerów i sygnatur

## Tryby pracy

### Korespondencja Przychodząca / Wychodząca

Ten tryb jest przeznaczony do archiwizacji standardowej korespondencji firmowej:
- **Format nazwy pliku:** `RRRR-MM-DD_TYP-DOKUMENTU_Temat_Nadawca-Odbiorca.pdf`
- **Rozpoznawane pola:** Data, Nadawca/Odbiorca, Temat, Typ Dokumentu, Numer Dokumentu

### Sąd Arbitrażowy

Ten tryb jest przeznaczony do archiwizacji dokumentów sądowych i prawnych:
- **Format nazwy pliku:** `RRRR-MM-DD_TYP-DOKUMENTU_[Sygnatura]_Tytuł-Pisma_Nadawca.pdf`
- **Struktura folderów:** Dokumenty są automatycznie sortowane do podfolderów według sygnatur spraw
- **Wymaga wprowadzenia:** Sygnatury sprawy w polu formularza

## Rozwiązywanie problemów

### Problem 1: Nie można załadować modelu NER

**Komunikat błędu:** "BŁĄD: Model NER niezaładowany!"

**Rozwiązanie:**
1. Sprawdź czy folder `moj_model_ner` znajduje się w tym samym katalogu co aplikacja
2. Upewnij się, że folder zawiera wszystkie wymagane pliki i podkatalogi (ner, tok2vec, vocab, morphology)
3. Jeśli brakuje katalogu `morphology`, użyj następującego skryptu:
   ```python
   import spacy
   import pl_core_news_md
   import os
   import shutil

   # Utwórz skrypt uzupełniający brakujące pliki
   model_wzorcowy = pl_core_news_md.load().path
   model_docelowy = os.path.join('2_Aplikacja_Glowna', 'moj_model_ner')
   
   for root, dirs, files in os.walk(model_wzorcowy):
       relative_path = os.path.relpath(root, model_wzorcowy)
       target_path = os.path.join(model_docelowy, relative_path) if relative_path != "." else model_docelowy
       
       # Utwórz brakujące katalogi
       for dir_name in dirs:
           source_dir = os.path.join(root, dir_name)
           dest_dir = os.path.join(target_path, dir_name)
           if not os.path.exists(dest_dir):
               print(f"Kopiuję katalog: {dest_dir}")
               shutil.copytree(source_dir, dest_dir)
   ```

Jeśli w logach aplikacji pojawia się komunikat "Nie udało się załadować modelu spaCy", zainstaluj domyślny model poleceniem:

```bash
python -m spacy download pl_core_news_sm
```

### Problem 2: Błąd OCR - "Poppler not installed"

**Komunikat błędu:** "Unable to get page count. Is poppler installed and in PATH?"

**Rozwiązanie:**
1. Sprawdź czy folder `poppler` z podkatalogiem `bin` znajduje się w tym samym katalogu co aplikacja
2. Pobierz Poppler dla Windows i umieść go w odpowiedniej lokalizacji:
   - https://github.com/oschwartz10612/poppler-windows/releases/

### Problem 3: Aplikacja działa wolno przy analizie dokumentów

**Rozwiązanie:**
1. Wyłącz opcję "Użyj asystenta tekstowego" - analiza będzie szybsza, choć mniej dokładna
2. Przetwarzaj mniejsze partie dokumentów naraz (max. 20-30 plików)
3. Zamknij inne wymagające zasobów aplikacje

### Problem 4: ImportError związany z pakietem `pydantic`

**Komunikat błędu:** `ImportError: cannot import name 'GetCoreSchemaHandler' from 'pydantic'`

**Rozwiązanie:**
1. Zaktualizuj pakiet `pydantic` do wersji 2 lub nowszej:
   ```bash
   pip install -U "pydantic>=2.0"
   ```
2. Jeśli używasz wirtualnego środowiska, upewnij się, że po aktualizacji ponownie zainstalujesz zależności:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

## FAQ

### Jak działa nadawanie nazw plikom?

Program automatycznie generuje nazwy plików na podstawie wykrytych metadanych. Format nazwy zależy od wybranego trybu pracy i zawiera datę, typ dokumentu oraz inne istotne informacje.

### Czy mogę edytować automatycznie wykryte dane?

Tak. Kliknij dwukrotnie na dowolną komórkę w tabeli wyników, aby edytować jej zawartość. Po zapisaniu zmian nowa nazwa pliku zostanie automatycznie zaktualizowana.

### Czy aplikacja modyfikuje oryginalne pliki PDF?

Nie. Aplikacja tworzy kopie plików z nowymi nazwami w folderze docelowym. Oryginalne pliki pozostają niezmienione.

### Czy mogę eksportować dane do innych formatów niż Excel?

Aktualnie aplikacja obsługuje tylko eksport do formatu Excel (.xlsx). W przyszłych wersjach planujemy dodać więcej formatów.

## Użyte technologie i licencje

| Biblioteka/Narzędzie | Licencja | Zastosowanie |
|----------------------|----------|--------------|
| spaCy                | MIT      | Silnik NER (Named Entity Recognition) |
| Pillow               | HPND     | Przetwarzanie obrazów |
| OpenCV               | Apache 2.0 | Przetwarzanie obrazów i optymalizacja dla OCR |
| pandas               | BSD      | Manipulacja danymi i eksport do Excela |
| openpyxl             | MIT      | Obsługa plików Excel |
| pdf2image            | MIT      | Konwersja PDF do obrazów |
| pytesseract          | Apache 2.0 | Silnik OCR |
| tkinter              | PSF      | Interfejs graficzny |
| torch                | BSD      | Obsługa modeli językowych |
| transformers         | Apache 2.0 | Obsługa modelu Phi-3 Mini |
| accelerate           | Apache 2.0 | Optymalizacja modeli językowych |
| safetensors          | Apache 2.0 | Bezpieczne przechowywanie tensorów |
| sentencepiece        | Apache 2.0 | Tokenizacja tekstu dla modeli językowych |
| cryptography		| nie wiem | kodowanie i haszowanie zapisów |

Wszystkie wymienione biblioteki są używane zgodnie z ich licencjami. Pełne teksty licencji są dostępne na stronach projektów lub w odpowiednich repozytoriach.

## Licencja

Archiwizator jest dystrybuowany na licencji Apache 2.0. Szczegóły znajdziesz w pliku [LICENSE](LICENSE) dołączonym do aplikacji.

---

**Wsparcie techniczne:**
W przypadku problemów technicznych, sugestii lub pytań, skontaktuj się z autorem projektu lub zgłoś problem poprzez [system issues](https://github.com/kitajusSus/archiwizacja-IGG-helper/issues) na GitHubie.
```

Ten plik README.md jest już gotowy do umieszczenia w Twoim projekcie. Zawiera kompletne informacje o aplikacji wraz z listą użytych technologii i ich licencji. Format Markdown jest kompatybilny z GitHub i będzie wyświetlany poprawnie w repozytorium projektu.

## Standardy kodowania

Projekt wykorzystuje następujące zasady stylu kodu:

* Wszystkie funkcje i metody posiadają adnotacje typów zgodnie z PEP 484.
* Docstringi są pisane w formacie Google i opisują argumenty oraz wartości zwracane.
* Spójność typów jest weryfikowana lokalnie narzędziem ``mypy``.
* Kod jest utrzymywany w stylu PEP 8.

Ten plik README.md jest już gotowy do umieszczenia w Twoim projekcie. Zawiera kompletne informacje o aplikacji wraz z listą użytych technologii i ich licencji. Format Markdown jest kompatybilny z GitHub i będzie wyświetlany poprawnie w repozytorium projektu.

## Polityka licencyjna

Projekt korzysta wyłącznie z bibliotek o licencjach zgodnych z Apache 2.0 lub MIT.
Pełna lista wykorzystywanych komponentów z ich licencjami znajduje się w pliku
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

Aby zaktualizować zestawienie licencji, uruchom skrypt audytu:

```bash
scripts/audit_licenses.sh
```

Skrypt pobiera informacje o pakietach Python oraz zależnościach front-endu i
uzupełnia plik `THIRD_PARTY_LICENSES.md` danymi o bibliotekach natywnych, takich
jak Qt czy Tesseract. Po każdej aktualizacji zależności plik należy ponownie
generować i dodać do repozytorium.

## Przewodnik dla deweloperów

1. Utwórz i aktywuj środowisko wirtualne:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```
2. Zainstaluj zależności wraz z pakietami opcjonalnymi:
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
5. Zbuduj pakiet instalacyjny (opcjonalnie):
   ```bash
   python build_exe.py
   ```
   Opcjonalnie możesz wskazać inny kompilator, np.:
   ```bash
   python build_exe.py --compiler clang++
   ```

Szczegółowe wskazówki znajdziesz w plikach [CONTRIBUTING.md](CONTRIBUTING.md) i [Dokumentacja_Techniczna.md](Dokumentacja_Techniczna.md).
