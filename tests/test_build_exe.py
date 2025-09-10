from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_compile_cpp_links_and_copies(monkeypatch, tmp_path):
    module = runpy.run_path(str(ROOT / "build_exe.py"))
    compile_cpp = module["compile_cpp"]

    cmds = []

    def fake_run(cmd):
        cmds.append(cmd)

    module["run"] = fake_run
    compile_cpp.__globals__["run"] = fake_run
    module["SRC"] = tmp_path
    compile_cpp.__globals__["SRC"] = tmp_path

    tesseract_dir = tmp_path / "tesseract"
    tesseract_dir.mkdir()
    for lib in [
        "libtesseract-5.dll",
        "libleptonica-6.dll",
        "libtesseract.lib",
        "libleptonica.lib",
    ]:
        (tesseract_dir / lib).write_text("dummy")
    # build_exe.compile_cpp expects headers in an include directory
    include_dir = tesseract_dir / "include" / "tesseract"
    include_dir.mkdir(parents=True)
    (include_dir / "version.h").write_text("dummy")

    compile_cpp()
    compile_cmd = cmds[0]
    assert "-l:libtesseract.lib" in compile_cmd
    assert "-l:libleptonica.lib" in compile_cmd

    for lib in ["libtesseract-5.dll", "libleptonica-6.dll"]:
        assert (tmp_path / lib).exists()

    fake_bin = tmp_path / "training_ocr"
    fake_bin.write_text("")
    module["run"]([str(fake_bin)])
    assert cmds[-1] == [str(fake_bin)]


def test_compile_cpp_missing_header(monkeypatch, tmp_path, capsys):
    module = runpy.run_path(str(ROOT / "build_exe.py"))
    compile_cpp = module["compile_cpp"]

    module["SRC"] = tmp_path
    compile_cpp.__globals__["SRC"] = tmp_path

    tesseract_dir = tmp_path / "tesseract"
    (tesseract_dir / "include" / "tesseract").mkdir(parents=True)

    called = {}

    def fake_download(url, dest):
        called["url"] = url

    compile_cpp.__globals__["download_and_extract"] = fake_download

    compile_cpp()
    captured = capsys.readouterr()
    assert "Incomplete Tesseract installation" in captured.out
    assert "Skip compilation" in captured.out
    assert "url" in called
