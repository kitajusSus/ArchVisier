"""Utilities submodule for openpyxl stub."""

import string

def get_column_letter(idx):
    """Return Excel-style column letter for 1-based index."""
    letters = ""
    while idx > 0:
        idx, remainder = divmod(idx - 1, 26)
        letters = string.ascii_uppercase[remainder] + letters
    return letters or "A"

__all__ = ["get_column_letter"]
