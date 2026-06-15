# HBM Model vs Ramulator2 Comparison Analysis

## Summary

This document analyzes the differences between our Python HBM model and Ramulator2 cycle-accurate simulations.

## Test Results

| Trace | Model Hit Rate | Sim Hit Rate | Error | Status |
|-------|---------------|--------------|-------|--------|
| seq_rd | 0.00% | 62.49% | 62.49 pp | NEEDS IMPROVEMENT |

## Key Findings

### 1. Row Hit Rate Discrepancy
- **Model prediction**: 0% row hit rate for sequential access
- **Ramulator2 actual**: 62.49% row hit rate
- **Root cause**: Simplified address mapping in `sim/trace/parser.py`

### 2. Latency Mismatch
- **Model prediction**: 81.9 cycles
- **Ramulator2 actual**: 12.9 cycles (average)
- **Root cause**: Model uses fixed timing estimates instead of actual HBM3 timing

### 3. Address Mapping Differences
The TraceParser uses a simplified address mapping:
```python
channel = (address >> (addr_bits - channel_bits)) % channels
```

Ramulator2 uses HBM3's ChRaBaRoCo (Channel-Row-Bank-Row-Column) mapper which has different bit ordering.

## Recommendations

### High Priority
1. **Improve address decoder** - Implement proper HBM3 ChRaBaRoCo address mapping
2. **Calibrate timing parameters** - Use actual HBM3 tRCD, tRP, tRAS values

### Medium Priority
3. **Add queue modeling** - TraceParser doesn't model read/write queues
4. **Implement FR-FCFS scheduling** - Current model uses simplified scheduling

### Low Priority
5. **Support pseudo-channels** - HBM3 has 2 pseudo-channels per channel
6. **Add bank group awareness** - HBM3 has 8 bank groups

## Files Involved

| File | Purpose |
|------|---------|
| `sim/trace/parser.py` | Trace parser with address decoding |
| `model/controller/address_decoder.py` | HBM address decoder |
| `model/dram/timing.py` | HBM3 timing parameters |

## Next Steps

1. Review address mapping algorithm in `TraceParser`
2. Compare with Ramulator2 ChRaBaRoCo implementation
3. Update model to match Ramulator2 behavior
4. Re-run comparison tests

## References

- Ramulator2: `research/hbm-modeling/scripts/parse_ramulator_log.py`
- Comparison report: `research/hbm-modeling/results/comparison_report.txt`
- Ramulator2 logs: `research/hbm-modeling/results/*.log`

---

*Generated: 2026-06-15*
