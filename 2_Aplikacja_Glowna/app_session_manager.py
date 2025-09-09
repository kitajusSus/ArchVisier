import json
import os
import base64
import hashlib
import datetime
import getpass
from typing import Any, Dict, List, Optional, Tuple

try:  # pragma: no cover - allow running as package or module
    from .gui.qt_safe import QtWidgets, QtCore
    from .gui.constants import DOC_TYPE_LABELS
except Exception:  # pragma: no cover - fallback for top-level imports
    from gui.qt_safe import QtWidgets, QtCore
    from gui.constants import DOC_TYPE_LABELS

from cryptography.fernet import Fernet
import uuid
import sys

class SessionManager:
    """Klasa obsługująca zapisywanie i wczytywanie sesji pracy z aplikacją."""
    
    def __init__(self, app_instance: Any) -> None:
        """Initialize the session manager.

        Args:
            app_instance: Reference to the main application instance
                providing access to GUI state.
        """
        self.app = app_instance
        
        # Zmiana lokalizacji zapisu sesji na katalog, gdzie znajduje się plik .exe
        if getattr(sys, 'frozen', False):
            # Jeśli aplikacja jest w wersji .exe (frozen)
            base_dir = os.path.dirname(sys.executable)
        else:
            # W trybie rozwojowym - katalog z plikiem app.py
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.session_folder = os.path.join(base_dir, 'sessions')
        self.current_session_path = None
        self.session_id = str(uuid.uuid4())
        self.counters: dict[str, int] = {}
        # osobny licznik dla dokumentów SA
        self.sa_counters: dict[str, int] = {}
        
        # Klucz szyfrowania generowany na podstawie identyfikatora maszyny i użytkownika
        self._generate_encryption_key()
        
        # Utworzenie folderu sesji jeśli nie istnieje
        if not os.path.exists(self.session_folder):
            os.makedirs(self.session_folder, exist_ok=True)
    
    def _generate_encryption_key(self) -> None:
        """Generate the encryption key based on system-specific values."""
        # Pobranie informacji o maszynie i użytkowniku
        machine_info = os.environ.get('COMPUTERNAME', '') + getpass.getuser()
        app_salt = "ArchiwizatorIGG_v3.2_2025"  # Stała sól specyficzna dla aplikacji
        
        # Generowanie klucza z użyciem hashowania
        key_material = machine_info + app_salt
        key_hash = hashlib.sha256(key_material.encode()).digest()
        self.key = base64.urlsafe_b64encode(key_hash)
        self.cipher = Fernet(self.key)
    
    def save_session(self, path: Optional[str] = None, password: Optional[str] = None) -> str:
        """Persist the current session to disk.

        Args:
            path: Optional path for the session file. Generated automatically
                when omitted.
            password: Optional password for additional encryption.

        Returns:
            Path to the saved session file.
        """
        if not path:
            # Automatyczna generacja nazwy pliku z datą i ID sesji
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"archiwizator_sesja_{timestamp}.arch"
            path = os.path.join(self.session_folder, filename)
        
        # Przygotowanie danych sesji
        session_data = {
            'session_id': self.session_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'user': getpass.getuser(),
            'work_mode': self.app.work_mode,
            'input_dir': self.app.input_dir,
            'output_dir': self.app.output_dir,
            'case_signature': self.app.case_signature,
            'files_data': [],
            'current_row': -1,
            'pdf_path': getattr(self.app, '_current_pdf_path', ''),
            'counters': self.counters,
            'sa_counters': self.sa_counters,
        }

        # Zapisz dane tabeli z QTableWidget
        row_count = 0
        try:
            row_count = self.app.tree.rowCount()
        except Exception:
            row_count = 0

        for row in range(row_count):
            row_values: List[str] = []
            for col in range(self.app.tree.columnCount()):
                item = self.app.tree.item(row, col)
                row_values.append(item.text() if item else "")

            name_item = self.app.tree.item(row, 0)
            original_path = ""
            if name_item is not None:
                data = None
                try:
                    data = name_item.data(QtCore.Qt.UserRole)
                except Exception:
                    data = None
                if data:
                    if os.path.isabs(str(data)):
                        original_path = str(data)
                    else:
                        original_path = os.path.join(session_data['input_dir'], str(data))
                else:
                    original_path = os.path.join(session_data['input_dir'], name_item.text())

            session_data['files_data'].append(
                {
                    'original_path': original_path,
                    'values': row_values,
                }
            )

        try:
            session_data['current_row'] = self.app.tree.currentRow()
        except Exception:
            pass
        
        # Szyfrowanie danych
        session_json = json.dumps(session_data, indent=2)
        
        # Dodatkowe zabezpieczenie hasłem jeśli podane
        if password:
            password_hash = hashlib.sha256(password.encode()).digest()[:16]
            extra_key = base64.urlsafe_b64encode(password_hash + password_hash)
            extra_cipher = Fernet(extra_key)
            encrypted_data = extra_cipher.encrypt(session_json.encode())
        else:
            encrypted_data = self.cipher.encrypt(session_json.encode())
            
        # Dodanie nagłówka identyfikującego plik
        header = b'ARCHIWIZATOR_SESSION_V1'
        
        with open(path, 'wb') as f:
            f.write(header + b'\n')
            f.write(encrypted_data)
            
        self.current_session_path = path
        return path
    
    def load_session(self, path: str, password: Optional[str] = None) -> Tuple[bool, str]:
        """Load a previously saved session file.

        Args:
            path: Path to the encrypted session file.
            password: Optional password if the session was additionally
                encrypted.

        Returns:
            Tuple of success flag and message.
        """
        try:
            with open(path, 'rb') as f:
                # Weryfikacja nagłówka
                header = f.readline().strip()
                if header != b'ARCHIWIZATOR_SESSION_V1':
                    return False, "To nie jest prawidłowy plik sesji Archiwizatora."
                
                # Odczyt zaszyfrowanych danych
                encrypted_data = f.read()
            
            # Próba odszyfrowania
            try:
                if password:
                    # Próba odszyfrowania z hasłem
                    password_hash = hashlib.sha256(password.encode()).digest()[:16]
                    extra_key = base64.urlsafe_b64encode(password_hash + password_hash)
                    extra_cipher = Fernet(extra_key)
                    session_json = extra_cipher.decrypt(encrypted_data).decode()
                else:
                    # Próba standardowego odszyfrowania
                    session_json = self.cipher.decrypt(encrypted_data).decode()
                    
                session_data = json.loads(session_json)
            except Exception:
                # Jeśli standardowe odszyfrowanie nie zadziałało, może być zaszyfrowane hasłem
                if not password:
                    return False, "Ten plik sesji jest zabezpieczony hasłem. Proszę podać hasło."
                else:
                    return False, "Nieprawidłowe hasło lub uszkodzony plik sesji."
            
            # Przywrócenie stanu aplikacji
            self.session_id = session_data['session_id']
            self.counters = session_data.get('counters', {})
            self.sa_counters = session_data.get('sa_counters', {})

            # Aktualizacja podstawowych ustawień
            self.app.work_mode = session_data.get('work_mode', 'KP')
            self.app.input_dir = session_data.get('input_dir', '')
            self.app.output_dir = session_data.get('output_dir', '')
            self.app.case_signature = session_data.get('case_signature', '')

            try:
                self.app.mode_combo.setCurrentText(
                    DOC_TYPE_LABELS.get(self.app.work_mode, self.app.work_mode)
                )
                self.app.input_edit.setText(self.app.input_dir)
                self.app.output_edit.setText(self.app.output_dir)
                self.app.case_edit.setText(self.app.case_signature)
                try:
                    self.app._sync_number_edit()
                except Exception:
                    pass
            except Exception:
                pass

            try:
                self.app.update_ui_for_mode()
            except Exception:
                pass

            # Czyszczenie obecnych danych w tabeli
            try:
                self.app.tree.setRowCount(0)
            except Exception:
                pass

            # Wczytanie plików
            files_loaded = 0
            for row, file_entry in enumerate(session_data.get('files_data', [])):
                values = file_entry.get('values', [])
                try:
                    self.app.tree.insertRow(row)
                except Exception:
                    continue

                for col, value in enumerate(values):
                    item = QtWidgets.QTableWidgetItem(value)
                    if col == 0:
                        try:
                            original_path = file_entry.get('original_path', value)
                            name = os.path.basename(original_path)
                            item.setText(name)
                            item.setData(QtCore.Qt.UserRole, original_path)
                        except Exception:
                            pass
                    self.app.tree.setItem(row, col, item)
                files_loaded += 1

            try:
                current_row = session_data.get('current_row', -1)
                if current_row >= 0 and self.app.tree.rowCount() > current_row:
                    self.app.tree.setCurrentCell(current_row, 0)
                pdf_path = session_data.get('pdf_path', '')
                if pdf_path:
                    self.app._current_pdf_path = pdf_path
                    self.app._load_pdf(pdf_path)
            except Exception:
                pass

            self.current_session_path = path
            return True, f"Wczytano sesję: {files_loaded} plików załadowanych."
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Błąd wczytywania sesji: {str(e)}"

    def reset_counters(self) -> None:
        """Resetuje liczniki numeracji dokumentów."""
        self.counters.clear()
        self.sa_counters.clear()

    def list_recent_sessions(self, limit: int = 10) -> List[str]:
        """Return a list of recently used session files.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of file paths ordered from newest to oldest.
        """
        if not os.path.exists(self.session_folder):
            return []
            
        sessions = []
        for file in os.listdir(self.session_folder):
            if file.endswith('.arch'):
                full_path = os.path.join(self.session_folder, file)
                modified_time = os.path.getmtime(full_path)
                sessions.append((full_path, modified_time))
        
        # Sortowanie po czasie modyfikacji (od najnowszych)
        sessions.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in sessions[:limit]]

