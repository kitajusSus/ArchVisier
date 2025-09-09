#!/usr/bin/env python3
"""Build standalone executable with a selectable compiler and PyInstaller.

This script compiles the C/C++ helpers using the Zig toolchain by default,
but it can also invoke ``clang++``/``clang-cl`` or MSVC ``cl.exe`` when
requested.  Afterwards the Python application is packaged into a single
directory using PyInstaller.  License files from this repository and bundled
tools are copied into the final distribution to satisfy commercial use
requirements.
"""

import argparse
import importlib
import pathlib
import shutil
import subprocess
import sys
import platform
import os

from fetch_tesseract import DEFAULT_URLS, download_and_extract

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "2_Aplikacja_Glowna"


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    """Run a subprocess command and echo it to the console."""
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, env=env)


def check_tool(tool_name: str) -> None:
    """Ensure required external tools or Python packages are available."""
    if tool_name == "pyinstaller":
        try:
            importlib.import_module("PyInstaller")
        except ModuleNotFoundError:
            print("Brak narzędzia 'pyinstaller' w systemie.")
            print("Zainstaluj PyInstaller: pip install pyinstaller")
            sys.exit(1)
        return

    if shutil.which(tool_name) is None:
        print(f"Brak narzędzia '{tool_name}' w systemie.")
        if tool_name == "zig":
            print("Zainstaluj zig: https://ziglang.org/download/")
        elif tool_name.startswith("clang"):
            print("Zainstaluj clang: https://clang.llvm.org/")
        elif tool_name == "cl":
            print("Uruchom wiersz poleceń Visual Studio lub zainstaluj MSVC.")
        sys.exit(1)


def check_resource(path: pathlib.Path) -> bool:
    """Return True if required resource directories exist under ``path``."""
    missing = [name for name in ("tesseract", "poppler") if not (path / name).exists()]
    if missing:
        print(
            "Brak wymaganych katalogów: "
            + ", ".join(missing)
            + f" w {path}."
        )
        return False
    return True


def compile_cpp(compiler: str = "zig") -> None:
    """Compile the C++ helper using the selected compiler."""
    output = SRC / "training_ocr"
    tesseract_dir = SRC / "tesseract"

    def ensure_tesseract() -> tuple[pathlib.Path | None, pathlib.Path | None]:
        """Ensure headers and static libs are present, downloading if necessary."""


        def find_libs() -> tuple[pathlib.Path | None, pathlib.Path | None]:
            patterns = [
                ("tesseract", ["tesseract*.lib", "libtesseract*.lib"]),
                ("leptonica", ["leptonica*.lib", "libleptonica*.lib"]),
            ]
            for sub in ("", "bin", "lib"):
                base = tesseract_dir / sub
                if not base.exists():
                    continue
                # tesseract
                tess = None
                for pat in patterns[0][1]:
                    tess = next(base.glob(pat), None) or tess
                # leptonica
                lept = None
                for pat in patterns[1][1]:
                    lept = next(base.glob(pat), None) or lept
                if tess and lept:
                    return tess, lept
            return None, None

        include_dir = tesseract_dir / "include"
        header = include_dir / "tesseract" / "version.h"
        tess_lib, lept_lib = find_libs()
        if include_dir.exists() and header.exists() and tess_lib and lept_lib:
            return tess_lib, lept_lib
        print("Brak kompletnej instalacji Tesseract. Próba pobrania...")
        system = platform.system().lower()
        url = DEFAULT_URLS.get(system)
        if not url:
            print(
                f"Brak domyślnego URL dla platformy {system}. Uruchom 'fetch_tesseract.py --url <adres>' ręcznie."
            )
            return None, None
        download_and_extract(url, tesseract_dir)
        include_dir = tesseract_dir / "include"
        header = include_dir / "tesseract" / "version.h"
        tess_lib, lept_lib = find_libs()
        if include_dir.exists() and header.exists() and tess_lib and lept_lib:
            return tess_lib, lept_lib
        print("Brak plików .lib bibliotek Tesseract i Leptonica.")
        return None, None

    tess_lib, lept_lib = ensure_tesseract()
    include_dir = tesseract_dir / "include"
    header = include_dir / "tesseract" / "version.h"
    if not include_dir.exists() or not header.exists():
        print("Pomiń kompilację lub doinstaluj pakiet deweloperski Tesseract.")
        return

    include_args = [f"-I{include_dir}"]

    link_args: list[str] = []
    if tess_lib and lept_lib:
        link_args = [
            f"-L{tess_lib.parent}",
            f"-L{lept_lib.parent}",
            f"-l:{tess_lib.name}",
            f"-l:{lept_lib.name}",
        ]
    else:
        so_tess = next(tesseract_dir.rglob("libtesseract*.so"), None)
        so_lept = next(tesseract_dir.rglob("libleptonica*.so"), None)
        if so_tess and so_lept:
            link_args = [
                f"-L{so_tess.parent}",
                f"-L{so_lept.parent}",
                f"-l:{so_tess.name}",
                f"-l:{so_lept.name}",
            ]
        else:
            dll_tess = next(tesseract_dir.rglob("libtesseract*.dll"), None)
            dll_lept = next(tesseract_dir.rglob("libleptonica*.dll"), None)
            if dll_tess and dll_lept:
                link_args = [
                    str(tess_lib),
                    str(lept_lib),
                ]
            else:
                print("Brak wymaganych bibliotek Tesseract i Leptonica.")
                return

    env = os.environ.copy()
    for var in ("INCLUDE", "LIB", "LIBPATH"):
        env.pop(var, None)

    src_file = str(SRC / "training_ocr.cpp")

    if compiler == "zig":
        cmd = [
            "zig",
            "c++",
            "-target",
            "x86_64-windows-msvc",
            src_file,
            "-std=c++17",
            "-fno-exceptions",
            "-fno-rtti",
            "-O3",
            *include_args,
            *link_args,
            "-o",
            str(output),
        ]
    elif compiler == "clang++":
        cmd = [
            "clang++",
            src_file,
            "-std=c++17",
            "-fno-exceptions",
            "-fno-rtti",
            "-O3",
            *include_args,
            *link_args,
            "-o",
            str(output),
        ]
    elif compiler in {"clang-cl", "cl"}:
        include_cl = [arg.replace("-I", "/I") for arg in include_args]
        lib_dirs = [arg[2:] for arg in link_args if arg.startswith("-L")]
        libs = []
        for arg in link_args:
            if arg.startswith("-l:"):
                libs.append(arg[3:])
            elif not arg.startswith("-L"):
                libs.append(arg)
        cmd = [
            compiler,
            src_file,
            "/std:c++17",
            "/EHsc-",
            "/GR-",
            "/O2",
            *include_cl,
            f"/Fe:{output}",
            *libs,
        ]
        if lib_dirs:
            cmd += ["/link", *[f"/LIBPATH:{d}" for d in lib_dirs]]
    else:
        raise ValueError(f"Nieobsługiwany kompilator: {compiler}")

    try:
        run(cmd, env=env)
    except TypeError:
        run(cmd)

# Copy dynamic libraries next to the executable for distribution
    for pat in [
        "tesseract*.dll",
        "leptonica*.dll",
        "libtesseract*.dll",
        "libleptonica*.dll",
        "libtesseract*.so",
        "libleptonica*.so",
    ]:
        for src in (tesseract_dir.glob(pat)):
            shutil.copy(src, SRC / src.name)


def build_fast_similarity(compiler: str = "zig") -> None:
    """Compile fast_similarity C helper into a shared library."""
    src = SRC / "fast_similarity.c"
    if not src.exists():
        return

    if platform.system().lower().startswith("win"):
        out = SRC / "fast_similarity.dll"
    else:
        out = SRC / "libfast_similarity.so"

    if compiler == "zig":
        cmd = ["zig", "cc", "-O3", "-shared", str(src), "-o", str(out)]
    elif compiler in {"clang++", "clang"}:
        cc = "clang"  # use the C driver
        cmd = [cc, "-O3", "-shared", str(src), "-o", str(out)]
    elif compiler in {"clang-cl", "cl"}:
        cmd = [compiler, "/O2", "/LD", str(src), f"/Fe:{out}"]
    else:
        raise ValueError(f"Nieobsługiwany kompilator: {compiler}")

    run(cmd)


def build_pyinstaller(mode: str) -> None:
    """Build application using PyInstaller in selected mode."""
    base_cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm"]
    if mode == "onefile":
        # Spec files already contain the bundle mode configuration.
        # When building a single executable we invoke PyInstaller with the
        # application entry point directly and pass ``--onefile``.  Passing
        # ``--onefile`` together with a spec file results in a PyInstaller
        # error ("option(s) not allowed"), so we avoid using the spec file
        # in this case.
        cmd = base_cmd + [str(SRC / "app.py"), "--onefile"]
    else:
        # The existing ``archiwizator.spec`` file already describes the
        # required onedir bundle, therefore no additional mode flags should
        # be supplied.
        cmd = base_cmd + ["archiwizator.spec"]
    run(cmd)


def copy_resources() -> None:
    """Copy additional resources to distribution directory."""
    dist = ROOT / "dist" / "Archiwizator"
    if not dist.exists():
        print("Brak folderu dist/Archiwizator.")
        return

    # Copy similarity library
    for lib in ("fast_similarity.dll", "libfast_similarity.so"):
        src = SRC / lib
        if src.exists():
            shutil.copy(src, dist / lib)

    # Copy context memory file
    mem_file = SRC / "document_context_memory.json"
    if mem_file.exists():
        shutil.copy(mem_file, dist / mem_file.name)

    # Copy NER models
    for model_dir in ["moj_model_ner", "custom_ner_model"]:
        src = SRC / model_dir
        if src.exists():
            shutil.copytree(src, dist / model_dir, dirs_exist_ok=True)

    # Copy LLM models
    for llm_dir in SRC.glob("llm_model*"):
        if llm_dir.is_dir():
            shutil.copytree(llm_dir, dist / llm_dir.name, dirs_exist_ok=True)


def copy_licenses() -> None:
    dist = ROOT / "dist" / "Archiwizator"
    if not dist.exists():
        print("Brak folderu dist/Archiwizator.")
        return
    if not check_resource(dist):
        print("Brakuje zasobów, kopiowanie licencji przerwane.")
        sys.exit(1)
    shutil.copy(ROOT / "LICENSE", dist / "LICENSE")
    tess_license = SRC / "tesseract" / "doc" / "LICENSE"
    if tess_license.exists():
        shutil.copy(tess_license, dist / "tesseract" / "LICENSE")
    poppler_license = SRC / "poppler" / "LICENSE"
    if poppler_license.exists():
        shutil.copy(poppler_license, dist / "poppler" / "LICENSE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Archiwizator executable")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--onefile", action="store_true", help="Build single executable")
    group.add_argument(
        "--onedir",
        "--onefolder",
        dest="onedir",
        action="store_true",
        help="Build directory with dependencies",
    )
    default_compiler = os.environ.get("ARCHIWIZATOR_COMPILER", "zig")
    parser.add_argument(
        "--compiler",
        choices=["zig", "clang++", "clang-cl", "cl"],
        default=default_compiler,
        help="Kompilator używany do budowania komponentów C/C++",
    )
    args = parser.parse_args()

    if args.onefile:
        mode = "onefile"
    else:
        mode = "onedir"

    compiler = args.compiler
    check_tool(compiler)
    check_tool("pyinstaller")
    build_fast_similarity(compiler)
    compile_cpp(compiler)
    build_pyinstaller(mode)
    if mode == "onedir":
        copy_resources()
        copy_licenses()
    print("Gotowe. Pliki w dist/Archiwizator/")


if __name__ == "__main__":
    main()
