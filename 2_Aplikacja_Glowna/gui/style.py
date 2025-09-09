"""Qt style sheet definitions for light and dark themes."""
from __future__ import annotations

LIGHT_THEME = """
/* Light theme */
QWidget {
    background-color: #f5f5f5;
    color: #202020;
}
QPushButton {
    background-color: #e0e0e0;
    padding: 5px;
}
QLineEdit, QComboBox, QTreeWidget, QTableWidget {
    background-color: #ffffff;
    selection-background-color: #3875d6;
}
"""

DARK_THEME = """
/* Dark theme */
QWidget {
    background-color: #2b2b2b;
    color: #eeeeee;
}
QPushButton {
    background-color: #444444;
    padding: 5px;
}
QLineEdit, QComboBox, QTreeWidget, QTableWidget {
    background-color: #3c3c3c;
    selection-background-color: #555555;
}
"""

def get_qss(theme: str) -> str:
    """Return QSS string for the given theme name."""
    return DARK_THEME if theme == "dark" else LIGHT_THEME
