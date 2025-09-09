#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
cd "$ROOT_DIR"

OUTFILE="THIRD_PARTY_LICENSES.md"

echo "# Third-party licenses" > "$OUTFILE"

echo -e "\n## Python packages\n" >> "$OUTFILE"
if command -v pip-licenses >/dev/null 2>&1; then
  pip-licenses --format=markdown >> "$OUTFILE"
else
  echo "pip-licenses not installed" >> "$OUTFILE"
fi

echo -e "\n## Node packages\n" >> "$OUTFILE"
if command -v npx >/dev/null 2>&1; then
  npx --yes license-checker --summary >> "$OUTFILE" || echo "license-checker failed" >> "$OUTFILE"
else
  echo "npx not available" >> "$OUTFILE"
fi

echo -e "\n## Native libraries\n" >> "$OUTFILE"
cat <<'EONATIVE' >> "$OUTFILE"
- Qt 6 — LGPL-3.0 or commercial license
- Zig standard library — MIT
- Tesseract OCR — Apache-2.0
EONATIVE
