#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ic/JXTF/HBM"
RAMULATOR="$ROOT/research/ramulator2/build/ramulator2"
RESULTS="$ROOT/research/hbm-modeling/results"

mkdir -p "$RESULTS"

echo "Running HBM3 sequential read baseline..."
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_seq.yaml" > "$RESULTS/hbm3_seq.log" 2>&1

echo "Running HBM3 stride read baseline..."
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_stride.yaml" > "$RESULTS/hbm3_stride.log" 2>&1

echo "Running HBM3 random read/write baseline..."
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_random_rdwr.yaml" > "$RESULTS/hbm3_random_rdwr.log" 2>&1

echo "Done. Results in $RESULTS/"