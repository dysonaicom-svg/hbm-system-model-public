# HBM3 Baseline Results

**Date:** 2026-06-15  
**Toolchain:** Ramulator2 built with clang++-18 (C++20)  
**DRAM Model:** HBM3 with HBM3_2Gb org and HBM3_2Gbps timing  
**Scheduler:** FRFCFS, OpenRowPolicy

## Experiment Summary

| Experiment | Traces | Memory Cycles | Avg Latency | Row Hits | Row Misses | Row Conflicts |
|------------|--------|--------------|-------------|----------|------------|---------------|
| Sequential Read | 100,000 LD | 924,397 | 12.93 | 62,481 | 24,992 | 12,495 |
| Stride Read | 100,000 LD (stride=4KB) | 2,323,041 | 12.66 | 0 | 32 | 99,935 |
| Random Read/Write | 69,816 LD + 30,184 ST | 369,956 | 14.14 | 17 | 3,550 | 96,383 |

## Key Observations

### Sequential Read (Best Case)
- **62.5% row hit rate** - Most accesses hit open rows
- Lowest memory cycles (924K) due to row locality
- Good candidate for streaming workloads

### Stride Read (Worst Case)
- **0% row hit rate** - Every access is to a different row
- Highest memory cycles (2.3M) due to constant row conflicts
- 99,935 row conflicts out of 100,000 accesses
- Expected behavior for stride patterns that exceed row buffer size

### Random Read/Write (Mixed)
- 70/30 read/write ratio as configured
- Higher latency (14.14) due to write queue pressure
- Write queue avg length: 15.77
- 28,736 write row conflicts showing write locality issues

## HBM3 Configuration Notes

The following configuration parameters are required for successful HBM3 execution:
- `DRAM.impl: HBM3`
- `DRAM.org.preset: HBM3_2Gb` (or HBM3_4Gb/HBM3_8Gb)
- `DRAM.timing.preset: HBM3_2Gbps` (or HBM3_4Gbps)
- `Controller.RowPolicy.impl: OpenRowPolicy` (or ClosedRowPolicy)
- `AddrMapper.impl: ChRaBaRoCo`

## Files Generated

- `configs/hbm3_seq.yaml` - Sequential read configuration
- `configs/hbm3_stride.yaml` - Stride read configuration
- `configs/hbm3_random_rdwr.yaml` - Mixed read/write configuration
- `traces/seq_rd.trace` - 100K sequential addresses
- `traces/stride_rd.trace` - 100K stride addresses (4KB stride)
- `traces/random_rdwr.trace` - 100K random addresses (30% writes)
- `results/hbm3_seq.log` - Sequential read output
- `results/hbm3_stride.log` - Stride read output
- `results/hbm3_random_rdwr.log` - Mixed read/write output