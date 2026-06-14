#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ic/JXTF/HBM"
RAMULATOR_DIR="$ROOT/research/ramulator2"
RAMULATOR="$ROOT/research/ramulator2/build/ramulator2"
RESULTS="$ROOT/research/hbm-modeling/results"

mkdir -p "$RESULTS"

if [ ! -f "$RAMULATOR" ]; then
    echo "ERROR: Ramulator2 executable not found at $RAMULATOR"
    echo "Please build Ramulator2 first with:"
    echo "  cd $RAMULATOR_DIR"
    echo "  cmake -S . -B build -DCMAKE_CXX_COMPILER=/usr/bin/clang++-18"
    echo "  cmake --build build -j"
    exit 1
fi

cd "$ROOT/research/ramulator2"
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_seq.yaml" > "$RESULTS/hbm3_seq.log" 2>&1
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_stride.yaml" > "$RESULTS/hbm3_stride.log" 2>&1
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_random_rdwr.yaml" > "$RESULTS/hbm3_random_rdwr.log" 2>&1
