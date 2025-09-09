import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1] / "2_Aplikacja_Glowna"
sys.path.insert(0, str(BASE_DIR))

from gui.pdf_processor_app import handle_file_copy


def test_handle_file_copy_with_spaces(tmp_path):
    src = tmp_path / "source.txt"
    src.write_text("data")
    dest = tmp_path / "out"
    dest.mkdir()

    result = handle_file_copy(str(src), str(dest), "spaced name.txt")
    assert result == "spaced_name.txt"
    assert (dest / "spaced_name.txt").exists()


def test_handle_file_copy_with_newline(tmp_path):
    src = tmp_path / "orig.txt"
    src.write_text("data")
    dest = tmp_path / "out"
    dest.mkdir()

    result = handle_file_copy(str(src), str(dest), "bad\nname.txt")
    assert result == "bad_name.txt"
    assert (dest / "bad_name.txt").exists()


def test_handle_file_copy_disallowed(tmp_path, caplog):
    import logging

    src = tmp_path / "orig.txt"
    src.write_text("data")
    dest = tmp_path / "out"
    dest.mkdir()

    with caplog.at_level(logging.WARNING):
        result = handle_file_copy(str(src), str(dest), "bad\tname.txt")
        assert result == "bad_name.txt"
    assert (dest / "bad_name.txt").exists()


def test_handle_file_copy_non_ascii(tmp_path):
    src = tmp_path / "orig.txt"
    src.write_text("data")
    dest = tmp_path / "out"
    dest.mkdir()

    result = handle_file_copy(str(src), str(dest), "żółć.txt")
    assert result == "____.txt"
    assert (dest / "____.txt").exists()

