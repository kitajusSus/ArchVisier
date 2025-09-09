#!/usr/bin/env python3
"""Download prebuilt Tesseract libraries and headers.

The script fetches a precompiled Tesseract OCR package and extracts it into
``2_Aplikacja_Glowna/tesseract`` so that the application can be built without
manually installing the dependency.  The default URLs target official
pre-built archives for Windows and Linux.  The script supports overriding the
URL via the ``--url`` argument for custom mirrors.
"""
from __future__ import annotations

import argparse
import io
import os
import platform
import pathlib
import tarfile
import zipfile
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request


ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / "2_Aplikacja_Glowna" / "tesseract"

WINDOWS_API = "https://api.github.com/repos/UB-Mannheim/tesseract/releases/latest"

DEFAULT_URLS = {
    "windows": "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.4/tesseract-5.3.4.20240526-win64.zip",
    "linux": "https://github.com/tesseract-ocr/tesseract/releases/download/5.3.0/tesseract-5.3.0-linux-x86_64.tar.xz",
}


def resolve_default_url(system: str) -> str | None:
    """Return a default archive URL for the current platform."""
    if system == "windows":
        try:
            # Provide a User-Agent header to avoid GitHub API rejections
            req = Request(WINDOWS_API, headers={"User-Agent": "fetch_tesseract/1.0"})
            with urlopen(req) as resp:
                release = json.load(resp)
        except Exception:
            return None
        assets = release.get("assets", [])
        preferred = ("win64", "w64", "x64", "64")
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".zip") and any(p in name for p in preferred):
                return asset.get("browser_download_url")
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".zip"):
                return asset.get("browser_download_url")
        return None
    if system == "linux":
        try:
            # Provide a User-Agent header to avoid GitHub API rejections
            req = Request(
                "https://api.github.com/repos/tesseract-ocr/tesseract/releases/latest",
                headers={"User-Agent": "fetch_tesseract/1.0"}
            )
            with urlopen(req) as resp:
                release = json.load(resp)
        except Exception:
            return None
        assets = release.get("assets", [])
        preferred = ("linux", "x86_64", "amd64", "64")
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".tar.xz") and all(p in name for p in preferred):
                return asset.get("browser_download_url")
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".tar.xz"):
                return asset.get("browser_download_url")
        return None
    return None

    


def download_and_extract(url: str, dest: pathlib.Path) -> None:
    print(f"Pobieranie {url} ...")
    try:
        with urlopen(url) as response:
            data = response.read()
    except HTTPError as e:
        raise SystemExit(f"Błąd pobierania {url}: {e.code} {e.reason}")
    except URLError as e:
        raise SystemExit(f"Błąd pobierania {url}: {e.reason}")
    dest.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO(data)
    if url.endswith(".zip"):
        with zipfile.ZipFile(buffer) as zf:
            zf.extractall(dest)
    elif url.endswith(('.tar.gz', '.tar.xz', '.tgz', '.txz')):
        with tarfile.open(fileobj=buffer) as tf:
            tf.extractall(dest)
    else:
        raise RuntimeError(f"Nieobsługiwany format archiwum: {url}")
    print(f"Rozpakowano do {dest}")


def main() -> None:
    system = platform.system().lower()
    parser = argparse.ArgumentParser(description="Fetch Tesseract binaries")

    default_url = resolve_default_url(system)
    parser.add_argument(
        "--url",
        help="Custom URL to Tesseract archive (zip or tar.*)",
        default=default_url,
    )
    args = parser.parse_args()

    if not args.url:
        raise SystemExit(

            f"Brak zdefiniowanego URL dla platformy {system}. Użyj --url, aby podać ręcznie."
        )
    download_and_extract(args.url, DEST)


if __name__ == "__main__":
    main()
