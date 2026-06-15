# HBM RTL vs Model Comparison Report

**Generated:** 2026-06-16T03:11:30.680457

**Comparison Type:** quick

**Overall Status:** MODEL_ONLY

## Execution Times

- Total: 2.38s
- RTL: 0.00s
- Model: 2.06s

## RTL Simulation Summary

| Metric | Value |
|--------|-------|
| Build Success | No |
| Sim Success | No |
| Error | Build reported success but binary not found - check GCC version (C++20 required) |

## Python Model Statistics

| Metric | Value |
|--------|-------|
| Total Cycles | 12,799 |
| Completed | 3,823 |
| Avg Latency | 29.9 cycles |
| Max Latency | 30 cycles |
| Row Hit Rate | 0.00% |
| Throughput | 48.938 GB/s |
| Efficiency | 29.96% |

## Metric Comparisons

| Metric | RTL | Model | Diff | %Diff | Status |
|--------|-----|-------|------|--------|--------|
| avg_latency_cycles | N/A | 29.913 | -29.913 | 100.0% | FAIL |
| row_hit_rate | N/A | N/A | N/A | N/A | PASS |
| throughput_gbps | N/A | 48.938 | -48.938 | 100.0% | FAIL |
| efficiency | N/A | 0.300 | -0.300 | 100.0% | N/A |

## Notes

Review individual metric comparisons for details.
