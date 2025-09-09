import os
from datetime import datetime
import uuid

from .qt_safe import QtWidgets
from .constants import DOC_TYPE_LABELS


class SessionManagerUI:
    """Mixin odpowiedzialny za obsługę logiki sesji w interfejsie użytkownika."""

    def show_welcome_screen(self):
        """Wyświetla ekran powitalny z opcjami: nowa sesja lub wczytaj istniejącą."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Archiwizator - Start")
        dialog.resize(600, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Logo i tytuł
        layout.addWidget(QtWidgets.QLabel("Archiwizator"))
        layout.itemAt(0).widget().setStyleSheet("font-size:24pt; font-weight:bold;")
        layout.addWidget(QtWidgets.QLabel(f"Wersja 3.2 - {self.current_date}"))
        layout.addWidget(QtWidgets.QLabel(f"Użytkownik: {self.current_user}"))

        author_label = QtWidgets.QLabel(
            'Autor: <a href="https://github.com/kitajusSus">Link do Github KitajusSus</a>'
        )
        author_label.setOpenExternalLinks(True)
        layout.addWidget(author_label)

        buttons_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons_layout)

        new_btn = QtWidgets.QPushButton("Nowe archiwum")
        new_btn.clicked.connect(lambda: (dialog.accept(), self.start_new_session()))
        buttons_layout.addWidget(new_btn)

        cont_btn = QtWidgets.QPushButton("Kontynuuj pracę")
        cont_btn.clicked.connect(lambda: (dialog.accept(), self.load_existing_session()))
        buttons_layout.addWidget(cont_btn)

        if hasattr(self, "session_manager"):
            try:
                recent_sessions = self.session_manager.list_recent_sessions(5)
            except Exception:  # pragma: no cover - defensive
                recent_sessions = []
            if recent_sessions:
                recent_group = QtWidgets.QGroupBox("Ostatnie sesje")
                recent_layout = QtWidgets.QVBoxLayout(recent_group)
                for session_path in recent_sessions:
                    session_name = os.path.basename(session_path)
                    modified_time = datetime.fromtimestamp(
                        os.path.getmtime(session_path)
                    ).strftime("%Y-%m-%d %H:%M")
                    btn = QtWidgets.QPushButton(f"{session_name} ({modified_time})")
                    btn.clicked.connect(
                        lambda checked=False, p=session_path: (
                            dialog.accept(),
                            self.load_session_from_path(p),
                        )
                    )
                    recent_layout.addWidget(btn)
                layout.addWidget(recent_group)

        dialog.exec()

    def start_new_session(self, welcome_dialog=None):
        """Rozpoczyna nową sesję."""
        if welcome_dialog:
            welcome_dialog.close()

        # Wyczyść wszystkie dane
        try:
            self.tree.setRowCount(0)
        except Exception:  # pragma: no cover - defensive when tree is stubbed
            pass

        # Resetuj ustawienia i zaktualizuj pola UI
        self.input_dir = ""
        self.output_dir = ""
        self.case_signature = ""
        self.work_mode = "KP"
        try:
            self.input_edit.setText("")
            self.output_edit.setText("")
            self.case_edit.setText("")
            self.mode_combo.setCurrentText(DOC_TYPE_LABELS[self.work_mode])
            self.update_ui_for_mode()
        except Exception:  # pragma: no cover - defensive
            pass

        # Inicjalizuj nową sesję
        if hasattr(self, 'session_manager'):
            self.session_manager.session_id = str(uuid.uuid4())
            self.session_manager.current_session_path = None
        try:
            self._sync_number_edit()
        except Exception:
            pass

    def load_existing_session(self, welcome_dialog=None):
        """Wczytuje istniejącą sesję z pliku."""
        if not hasattr(self, "session_manager"):
            QtWidgets.QMessageBox.critical(self, "Błąd", "Menedżer sesji nie jest dostępny.")
            return

        directory = self.session_manager.session_folder if hasattr(self, "session_manager") else ""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Wybierz plik sesji",
            directory,
            "Pliki sesji Archiwizatora (*.arch);;Wszystkie pliki (*)",
        )

        if path:
            if welcome_dialog:
                welcome_dialog.close()
            self.load_session_from_path(path)

    def load_session_from_path(self, path=None):
        """Wczytuje sesję z podanej ścieżki."""
        if not path or not hasattr(self, "session_manager"):
            return

        success, message = self.session_manager.load_session(path)

        if not success and "hasłem" in message:
            password = self.ask_password("Sesja zabezpieczona", "Podaj hasło do pliku sesji:")
            if password:
                success, message = self.session_manager.load_session(path, password)

        if success:
            QtWidgets.QMessageBox.information(self, "Wczytywanie sesji", message)
        else:
            QtWidgets.QMessageBox.critical(self, "Błąd wczytywania sesji", message)

    def ask_password(self, title, prompt):
        """Wyświetla okno dialogowe z prośbą o hasło."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(title)

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(QtWidgets.QLabel(prompt))

        password_edit = QtWidgets.QLineEdit()
        password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(password_edit)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QtWidgets.QDialog.Accepted:
            return password_edit.text()
        return None

    def save_current_session(self):
        """Zapisuje bieżącą sesję."""
        if not hasattr(self, "session_manager"):
            QtWidgets.QMessageBox.critical(self, "Błąd", "Menedżer sesji nie jest dostępny.")
            return

        try:
            if self.tree.rowCount() == 0:
                QtWidgets.QMessageBox.warning(self, "Ostrzeżenie", "Brak danych do zapisania.")
                return
        except Exception:  # pragma: no cover - defensive
            return

        path = self.session_manager.current_session_path
        if not path:
            return self.save_session_as()

        try:
            saved_path = self.session_manager.save_session(path)
            QtWidgets.QMessageBox.information(
                self, "Zapisano", f"Sesja została zapisana:\n{saved_path}"
            )
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Błąd zapisu", f"Nie udało się zapisać sesji:\n{str(e)}"
            )
            return False

    def save_session_as(self):
        """Zapisuje bieżącą sesję pod nową nazwą."""
        if not hasattr(self, "session_manager"):
            QtWidgets.QMessageBox.critical(self, "Błąd", "Menedżer sesji nie jest dostępny.")
            return

        try:
            if self.tree.rowCount() == 0:
                QtWidgets.QMessageBox.warning(self, "Ostrzeżenie", "Brak danych do zapisania.")
                return
        except Exception:  # pragma: no cover - defensive
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"archiwizator_sesja_{timestamp}.arch"
        initial_path = os.path.join(self.session_manager.session_folder, default_filename)

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Zapisz sesję jako",
            initial_path,
            "Pliki sesji Archiwizatora (*.arch);;Wszystkie pliki (*)",
        )

        if not path:
            return False

        use_password = (
            QtWidgets.QMessageBox.question(
                self,
                "Zabezpieczenie hasłem",
                "Czy chcesz zabezpieczyć ten plik hasłem?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            == QtWidgets.QMessageBox.Yes
        )

        password = None
        if use_password:
            password = self.ask_password("Ustaw hasło", "Podaj hasło dla pliku sesji:")
            if not password:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Ostrzeżenie",
                    "Nie podano hasła. Sesja zostanie zapisana bez zabezpieczenia.",
                )

        try:
            saved_path = self.session_manager.save_session(path, password)
            QtWidgets.QMessageBox.information(
                self, "Zapisano", f"Sesja została zapisana:\n{saved_path}"
            )
            return True
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Błąd zapisu", f"Nie udało się zapisać sesji:\n{str(e)}"
            )
            return False
