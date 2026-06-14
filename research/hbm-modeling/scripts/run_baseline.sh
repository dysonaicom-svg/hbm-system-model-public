#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ic/JXTF/HBM"
RAMULATOR="$ROOT/research/ramulator2/ramulator2/build/ramulator2"
RESULTS="$ROOT/research/hbm-modeling/results"
RAMULATOR_DIR="$ROOT/research/ramulator2/ramulator2"

mkdir -p "$RESULTS"

cd "$RAMULATOR_DIR"
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_seq.yaml" > "$RESULTS/hbm3_seq.log" 2>&1
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_stride.yaml" > "$RESULTS/hbm3_stride.log" 2>&1
"$RAMULATOR" -f "$ROOT/research/hbm-modeling/configs/hbm3_random_rdwr.yaml" > "$RESULTS/hbm3_random_rdwr.log" 2>&1