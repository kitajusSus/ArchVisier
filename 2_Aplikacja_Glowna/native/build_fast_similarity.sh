#!/bin/sh
# Compile cosine similarity library.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$1"

if [ -z "$TARGET" ]; then
  TARGET="all"
fi

build_c() {
  gcc -O3 -march=native -fPIC -shared "$DIR/fast_similarity.c" -o "$DIR/libfast_similarity.so" -fopenmp -DUSE_BLAS -lopenblas
}

build_zig() {
  zig build-lib "$DIR/fast_similarity.zig" -O ReleaseFast -fPIC -dynamic -femit-bin="$DIR/libfast_similarity_zig.so"
}

case "$TARGET" in
  c) build_c ;;
  zig) build_zig ;;
  all) build_c && build_zig ;;
  *) echo "Usage: $0 [c|zig|all]" >&2; exit 1 ;;
esac
