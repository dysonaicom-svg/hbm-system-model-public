# HBM3 Baseline Results

**更新时间**: 2026-06-15

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| DRAM Model | HBM3 |
| Organization | HBM3_2Gb preset, 1 channel, 2 pseudochannels |
| Timing | HBM3_2Gbps (2 Gbps/pin, tCK=1000ps) |
| Scheduler | FRFCFS |
| Row Policy | OpenRowPolicy (cap: 4) |
| Frontend | SimpleO3 + RandomTranslation |
| Clock Ratio | CPU:DRAM = 8:3 |

## Results Summary

### Sequential Read (seq_rd.trace, stride=64B)

| Metric | Value |
|--------|-------|
| Total Read Requests | 83,125 |
| Memory System Cycles | 249,452 |
| Avg Read Latency | 30.95 cycles |
| Row Hits | 72,728 (87.5%) |
| Row Misses | 32 |
| Row Conflicts | 10,359 |

### Stride Read (stride_rd.trace, stride=4KB)

| Metric | Value |
|--------|-------|
| Total Read Requests | 83,095 |
| Memory System Cycles | 596,348 |
| Avg Read Latency | 83.13 cycles |
| Row Hits | 18 (0.02%) |
| Row Misses | 5 |
| Row Conflicts | 83,064 (99.97%) |

### Random Read (random_rdwr.trace)

| Metric | Value |
|--------|-------|
| Total Read Requests | 83,380 |
| Memory System Cycles | 315,459 |
| Avg Read Latency | 42.46 cycles |
| Row Hits | 8 (0.01%) |
| Row Misses | 32 |
| Row Conflicts | 83,336 (99.99%) |

## Key Observations

1. **Sequential access is highly efficient**: Row hit rate 87.5%, lowest latency (30.95 cycles)
2. **Stride/Random access suffers from row conflicts**: Near 100% conflict rate
3. **Stride shows highest latency**: Despite similar row conflict rate as random, stride has ~2x higher latency
4. **OpenRowPolicy helps sequential**: Keeps rows open for consecutive accesses

## HBM3 Timing Parameters (HBM3_2Gbps)

| Parameter | Value |
|-----------|-------|
| nCL (CAS Latency) | 7 cycles |
| nBL (Burst Length) | 4 cycles |
| nRCDRD | 7 cycles |
| nRP | 7 cycles |
| nRAS | 17 cycles |
| nRC | 19 cycles |
| nRRDS | 3 cycles |
| nFAW | 15 cycles |
| nRFC | 160 cycles |

## Notes

- HBM3 requires OpenRowPolicy (ClosedRowPolicy incompatible due to missing rank level)
- SimpleO3 frontend includes LLC, so actual memory requests filtered by cache
- Address translation uses RandomTranslation (random VA→PA mapping)
- All traces generated with fixed seed (42) for reproducibility
