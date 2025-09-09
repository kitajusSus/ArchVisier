#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
cd "${ROOT_DIR}/gui_native"

cmake -S . -B build
cmake --build build

# start python server in background
python server.py &
SERVER_PID=$!
trap "kill $SERVER_PID" EXIT

# run the compiled Qt application
"build/gui_native"
