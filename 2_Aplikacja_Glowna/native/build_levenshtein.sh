#!/bin/sh
# Compile Levenshtein distance library
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$OS" = "Windows_NT" ]; then
    zig cc -O3 -shared "$DIR/levenshtein.c" -fopenmp -o "$DIR/liblevenshtein.dll"
else
    gcc -O3 -fPIC -shared "$DIR/levenshtein.c" -o "$DIR/liblevenshtein.so" -fopenmp
fi
