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

## HBM3 Configuration Notes

After extensive testing, the following configuration works with the local Ramulator2 build:

1. **HBM3 requires `nRREFD` timing parameter** - The preset-based configuration works but certain timing parameters must be specified explicitly
2. **RowPolicy is required** - Either `OpenRowPolicy` or `ClosedRowPolicy` must be specified in the Controller section
3. **Address Mapper** - `ChRaBaRoCo` is the standard address mapper for HBM configurations

## Integration Path Decision

**Recommended:** `gem5`

**Rationale:** This HBM modeling baseline is part of a chip design project (HBM Controller + DRAM Model). The next logical step is to:
1. Integrate with gem5 to model CPU/NPU/GPU traffic generators
2. Add cache hierarchy effects on memory access patterns
3. Support full-system software workloads

gem5 is chosen over DRAMSys because:
- gem5 supports HBM2Stack/HBMCtrl natively
- Better for chip-level performance analysis
- Active maintenance and community support

**DRAMSys** would be the choice if:
- SystemC/TLM virtual platform integration is needed
- Transaction-level SoC modeling is the goal
- Faster DRAM-centric design-space exploration