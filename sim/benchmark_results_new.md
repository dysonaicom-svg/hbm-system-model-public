# HBM Performance Benchmark Results

**Generated:** 2026-06-16 02:12:46

## Summary

| Metric | Value |
|--------|-------|
| Total completed requests | 12,850 |
| Average throughput | 0.082 GB/s |
| Peak throughput | 0.082 GB/s |
| Average row hit rate | 0.00% |
| Total benchmarks | 1 |

## Detailed Results

| Pattern | Rate | Throughput | Hit Rate | Latency | P99 Latency | Efficiency |
|---------|------|------------|---------|---------|-------------|------------|
| sequential | 0.5 | 0.082 GB/s | 0.0% | 2.4 cyc | 3.5 cyc | 50.2% |

## Multi-Channel Bandwidth Analysis

| Pattern | Active Ch | Total Ch | Balance Score | Avg BW/Channel |
|---------|-----------|----------|---------------|----------------|
| sequential | 1 | 16 | 100.00% | 164.4928 GB/s |

## Row Buffer Analysis

| Pattern | Hit Rate | Miss Rate | Latency Savings |
|---------|----------|-----------|----------------|
| sequential | 0.0% | 0.0% | 0 cycles |

## QoS Scheduling Efficiency

| Pattern | Fairness | High Prio Lat | Low Prio Lat |
|---------|----------|--------------|-------------|
| sequential | 0.00% | 2.1 cyc | 2.8 cyc |

## Test Configuration

- HBM Version: hbm3
- Channels per stack: 8
- Stack count: 2
- Total channels: 16
- Peak bandwidth: 1638.4 GB/s
- Data rate: 6.4 Gb/s/pin
