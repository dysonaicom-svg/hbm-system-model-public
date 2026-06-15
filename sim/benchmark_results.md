# HBM Performance Benchmark Results

**Generated:** 2026-06-16 02:14:02

## Summary

| Metric | Value |
|--------|-------|
| Total completed requests | 76,775 |
| Average throughput | 0.082 GB/s |
| Peak throughput | 0.082 GB/s |
| Average row hit rate | 0.01% |
| Total benchmarks | 4 |

## Detailed Results

| Pattern | Rate | Throughput | Hit Rate | Latency | P99 Latency | Efficiency |
|---------|------|------------|---------|---------|-------------|------------|
| sequential | 0.5 | 0.082 GB/s | 0.0% | 2.4 cyc | 3.5 cyc | 50.2% |
| random | 0.5 | 0.082 GB/s | 0.0% | 29.9 cyc | 30.0 cyc | 49.9% |
| stride | 0.5 | 0.082 GB/s | 0.1% | 28.1 cyc | 30.0 cyc | 50.2% |
| hot_spot | 0.5 | 0.082 GB/s | 0.0% | 29.3 cyc | 30.0 cyc | 49.9% |

## Multi-Channel Bandwidth Analysis

| Pattern | Active Ch | Total Ch | Balance Score | Avg BW/Channel |
|---------|-----------|----------|---------------|----------------|
| sequential | 1 | 16 | 100.00% | 164.3264 GB/s |
| random | 1 | 16 | 100.00% | 163.3237 GB/s |
| stride | 1 | 16 | 100.00% | 164.2581 GB/s |
| hot_spot | 1 | 16 | 100.00% | 163.4304 GB/s |

## Row Buffer Analysis

| Pattern | Hit Rate | Miss Rate | Latency Savings |
|---------|----------|-----------|----------------|
| sequential | 0.0% | 0.0% | 0 cycles |
| random | 0.0% | 0.0% | 0 cycles |
| stride | 0.1% | 0.0% | 28 cycles |
| hot_spot | 0.0% | 0.0% | 0 cycles |

## QoS Scheduling Efficiency

| Pattern | Fairness | High Prio Lat | Low Prio Lat |
|---------|----------|--------------|-------------|
| sequential | 0.00% | 2.1 cyc | 2.8 cyc |
| random | 0.00% | 25.4 cyc | 34.4 cyc |
| stride | 0.00% | 23.9 cyc | 32.4 cyc |
| hot_spot | 0.00% | 24.9 cyc | 33.6 cyc |

## Test Configuration

- HBM Version: hbm3
- Channels per stack: 8
- Stack count: 2
- Total channels: 16
- Peak bandwidth: 1638.4 GB/s
- Data rate: 6.4 Gb/s/pin
