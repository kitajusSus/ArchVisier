# Contributing

This project uses Python with native modules written in C and Zig. Follow the steps below to set up your environment, build the
components and run the tests.

## Development environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
pip install -e .[ocr,training]
```

## Building the C library

```bash
cmake -S native_c -B native_c/build
cmake --build native_c/build --config Release
```

## Building the Zig library

```bash
cd zig_modules/token_similarity
zig build -Drelease-safe
cd ../..
```

Both commands place the resulting shared libraries in the directories expected by the Python wrappers.

## Running the full test suite

```bash
pytest
```

Run tests after any change to ensure functionality. The CI workflow caches the `native_c/build` and `zig_modules/token_similarity/zig-out`
folders to speed up subsequent builds and uploads the produced libraries as build artifacts for inspection.

## Packaging check

Changes to packaging or dependency logic must keep the standalone executable buildable. Before pushing such changes, run the PyInstaller build locally:

```bash
python build_exe.py --compiler=clang++ --onefile
```

The CI workflow runs the same command and fails if the build step exits with a non-zero status.

## Code style

The codebase targets PEP 8 and uses type hints checked with `mypy`. Please format your changes accordingly and document public functions.
