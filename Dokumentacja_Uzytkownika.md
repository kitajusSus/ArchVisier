# Archiwizator - Dokumentacja Użytkownika

## 1. Wprowadzenie

Witaj w instrukcji obsługi aplikacji **Archiwizator**. Ten program został stworzony, aby pomóc Ci w szybkim i zorganizowanym porządkowaniu skanów dokumentów. Aplikacja "czyta" pliki PDF, a następnie automatycznie je nazywa i sortuje na podstawie odnalezionych informacji.

## 2. Instalacja i uruchomienie

### 2.1 Uruchomienie gotowej paczki

Aplikacja jest dostarczana jako plik `Archiwizator.exe` i nie wymaga instalacji. Wystarczy skopiować go w dogodne miejsce i uruchomić dwuklikiem.

### 2.2 Budowa własnej paczki (dla zaawansowanych)

1. Zainstaluj [Python 3.11+](https://www.python.org/downloads/), [Git](https://git-scm.com/) oraz [Zig](https://ziglang.org/download/).
2. Sklonuj repozytorium i przygotuj środowisko:
   ```bash
   git clone https://github.com/kitajusSus/archiwizacja-IGG-helper.git
   cd archiwizacja-IGG-helper
   python -m venv venv
   venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. (Opcjonalnie) zainstaluj `bitsandbytes`, jeśli planujesz korzystać z trybu asystenta tekstowego:
   ```bash
   pip install bitsandbytes
   ```
4. Zbuduj komponenty natywne i przygotuj pakiet dystrybucyjny:
   ```bash
   cd 2_Aplikacja_Glowna
   zig cc -O3 -shared fast_similarity.c -o fast_similarity.dll
   cd ..
   python build_exe.py
   ```
   Gotowy katalog `dist/Archiwizator` zawiera plik `Archiwizator.exe` wraz z wymaganymi zasobami.

## 3. Główne Okno Aplikacji

Po uruchomieniu zobaczysz główne okno programu, które składa się z kilku sekcji:

1.  **Tryb pracy:** Tutaj wybierasz, jaki rodzaj dokumentów będziesz porządkować.
2.  **Dane wejściowe:** W tym miejscu wskazujesz programowi, gdzie znajdują się pliki do przetworzenia i gdzie zapisać wyniki.
3.  **Akcje:** Główny przycisk do uruchamiania analizy.
4.  **Wyniki:** Tabela, w której pojawią się przetworzone dokumenty. Możesz tu zweryfikować i poprawić dane przed finalnym zapisem.
5.  **Zapis i Eksport:** Przyciski do finalizowania pracy.

## 4. Praca z Aplikacją Krok po Kroku

### Krok 1: Wybierz tryb pracy

Na samej górze wybierz jedną z trzech opcji, w zależności od zadania:
*   **Korespondencja Przychodząca / Wychodząca:** Użyj tego trybu dla standardowych pism, faktur, umów itp.
*   **Sąd Arbitrażowy:** Ten tryb jest specjalnie przystosowany do pracy z dokumentami w ramach jednej sprawy sądowej.

### Krok 2: Wskaż dane wejściowe

*   **Jeśli wybrałeś tryb "Sąd Arbitrażowy":**
    1.  Pojawi się dodatkowe pole **"Sygnatura Akt Sprawy"**. Wpisz tutaj sygnaturę sprawy, którą się zajmujesz (np. `I C 123/23`). Jest to kluczowe, aby wszystkie dokumenty trafiły do jednego folderu.
*   **Dla wszystkich trybów:**
    1.  **Folder ze skanami PDF:** Kliknij "Wybierz..." i wskaż folder, w którym znajdują się pliki PDF do uporządkowania.
    2.  **Folder na wyniki:** Kliknij "Wybierz..." i wskaż folder, gdzie program ma zapisać posortowane i poprawnie nazwane pliki.

### Krok 3: Skanuj i analizuj

Kliknij duży przycisk **"3. Skanuj pliki i analizuj"**. Program rozpocznie pracę, a pasek postępu pokaże, na jakim jest etapie. Może to potrwać kilka minut, w zależności od liczby i złożoności dokumentów.

### Krok 4: Weryfikuj i edytuj dane

Po zakończeniu analizy, w dolnej tabeli pojawią się wyniki. Każdy wiersz to jeden dokument.
*   **Sprawdź poprawność danych:** Zobacz, czy program dobrze rozpoznał datę, nadawcę, tytuł pisma itp.
*   **Edytuj w razie potrzeby:** Jeśli jakaś informacja jest błędna, **kliknij na nią dwukrotnie**. Otworzy się małe okienko, w którym możesz wpisać poprawną wartość. Po zapisaniu, nowa nazwa pliku zostanie automatycznie zaktualizowana.
*   **Zwróć uwagę na błędy:** Jeśli cały wiersz jest podświetlony na różowo, oznacza to, że wystąpił błąd podczas odczytu pliku PDF. Taki plik należy zweryfikować ręcznie.

### Krok 5: Zapisz wyniki LUB wyeksportuj rozpiskę

Gdy dane w tabeli są już poprawne, masz dwie możliwości:

*   **Opcja A: Zapisz zmiany i przenieś pliki**
    *   Kliknij ten przycisk, aby fizycznie uporządkować pliki. Program skopiuje je do folderu docelowego, nadając im nowe nazwy i tworząc podfoldery (w trybie sądowym).
    *   Użyj tej opcji, aby sfinalizować archiwizację.

*   **Opcja B: Eksportuj widok do Excela**
    *   Kliknij ten przycisk, aby stworzyć plik `.xlsx` (rozpiskę) zawierający dokładnie to, co widzisz w tabeli.
    *   Program poprosi o wskazanie miejsca i nazwy dla pliku Excel.
    *   Użyj tej opcji, jeśli potrzebujesz raportu lub spisu dokumentów bez przenoszenia samych plików.

Możesz użyć obu opcji - najpierw wyeksportować rozpiskę, a następnie zapisać i przenieść pliki.

**Gotowe! Twoje dokumenty są teraz uporządkowane, a rozpiska wygenerowana.**

## 5. Dodatkowe wskazówki i wsparcie

- Upewnij się, że skany dokumentów są dobrej jakości – ułatwia to skuteczność OCR.
- W przypadku problemów skorzystaj z sekcji rozwiązywania problemów w pliku `README.md`.
- Błędy lub sugestie zgłaszaj poprzez [system issues](https://github.com/kitajusSus/archiwizacja-IGG-helper/issues).

**Dziękujemy za korzystanie z Archiwizatora!**

Dla deweloperów chcących rozwijać aplikację przygotowano oddzielny przewodnik w plikach [README.md](README.md) oraz [CONTRIBUTING.md](CONTRIBUTING.md).
