# HBM Modeling Baseline

This directory contains local HBM modeling experiments built around the existing Ramulator2 checkout at `../ramulator2/ramulator2`.

## First Goal

Run trace-driven HBM3 timing experiments in Ramulator2 and collect bandwidth, latency, row-buffer behavior, queue pressure, and address-mapping effects.

## Directory Layout

- `configs/`: project-owned Ramulator2 YAML configs
- `traces/`: synthetic memory traces
- `scripts/`: trace generators and run scripts
- `results/`: run output and summaries

## Toolchain

Ramulator2 requires a C++20-capable compiler. The upstream README lists `g++-12` and `clang++-15` as tested compilers.
