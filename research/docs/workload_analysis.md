# HBM4 Workload Analysis

**Date:** 2026-06-15
**Purpose:** Analyze AI/HPC traffic patterns for HBM4 system modeling

## 1. Traffic Pattern Taxonomy

### 1.1 Sequential Streaming
- **Characteristics:** Large, contiguous memory accesses
- **Bandwidth-bound:** Optimized for peak bandwidth
- **Examples:** Weight loading, gradient accumulation
- **Channel utilization:** High, sequential channel traversal

### 1.2 Row-Local Tensor Tile
- **Characteristics:** Access within a tensor tile (e.g., 64x64, 128x128)
- **Spatial locality:** High row buffer hit rate
- **Examples:** Matrix multiplication, convolution
- **Channel utilization:** Moderate, locality-dependent

### 1.3 Random Gather/Scatter
- **Characteristics:** Disconnected address accesses
- **Latency-bound:** Optimized for low latency
- **Examples:** Index-based lookup, embedding table access
- **Channel utilization:** Low, random distribution

### 1.4 Mixed Read/Write Inference
- **Characteristics:** Read-heavy with occasional writes
- **Examples:** Inference with weight reuse
- **Channel utilization:** Variable

### 1.5 Refresh/Thermal Stress
- **Characteristics:** Periodic refresh commands
- **Impact:** Bandwidth reduction during refresh
- **Examples:** Sustained operation under thermal constraints

### 1.6 Multi-Tenant QoS
- **Characteristics:** Multiple traffic classes with priorities
- **Examples:** Inference server, training cluster
- **Channel utilization:** Traffic-dependent

## 2. AI Training Traffic Characteristics

### 2.1 Forward Pass
| Aspect | Value |
|--------|-------|
| Read/Write Ratio | 100:0 (read-only) |
| Request Size | 64B - 4KB (typical), up to 64B burst |
| Row Hit Rate | 60-80% (with blocking) |
| Channel Utilization | 70-90% |

### 2.2 Backward Pass (Gradient Computation)
| Aspect | Value |
|--------|-------|
| Read/Write Ratio | 80:20 |
| Request Size | 64B - 2KB |
| Row Hit Rate | 40-60% |
| Channel Utilization | 60-80% |

### 2.3 Weight Update
| Aspect | Value |
|--------|-------|
| Read/Write Ratio | 20:80 |
| Request Size | 64B - 1KB |
| Row Hit Rate | 30-50% |
| Channel Utilization | 50-70% |

### 2.4 Training Summary
- **Overall Read/Write Ratio:** ~60:40
- **Effective Bandwidth:** 70-85% of theoretical peak
- **Row Buffer Hit Rate:** 40-60% (depends on batch size)
- **Refresh Impact:** 2-5% bandwidth reduction

## 3. AI Inference Traffic Characteristics

### 3.1 Batch Inference
| Aspect | Value |
|--------|-------|
| Read/Write Ratio | 90:10 |
| Request Size | 64B - 256B |
| Row Hit Rate | 70-85% |
| Channel Utilization | 50-70% |

### 3.2 Online Inference
| Aspect | Value |
|--------|-------|
| Read/Write Ratio | 95:5 |
| Request Size | 64B - 128B |
| Row Hit Rate | 75-90% |
| Channel Utilization | 30-50% |

### 3.3 Inference Summary
- **Overall Read/Write Ratio:** ~90:10
- **Effective Bandwidth:** 50-70% of theoretical peak
- **Row Buffer Hit Rate:** 70-85% (good locality)
- **Refresh Impact:** 1-3% bandwidth reduction

## 4. Workload Profiles

### Profile A: AI Training (Heavy Sequential + Random Write)

| Parameter | Value |
|-----------|-------|
| **Primary Use** | Large model training (LLM, Vision) |
| **Read/Write Ratio** | 60:40 |
| **Request Size Distribution** | 64B (30%), 128B (40%), 256B (20%), 512B (10%) |
| **Address Pattern** | Sequential + strided (tensor access) |
| **Expected Channel Utilization** | 75% |
| **QoS Class** | 8 (high priority for reads) |
| **Row Buffer Hit Rate** | 45% |
| **Refresh Sensitivity** | Medium |

### Profile B: AI Inference (Read-Heavy, Small Requests)

| Parameter | Value |
|-----------|-------|
| **Primary Use** | Inference serving |
| **Read/Write Ratio** | 90:10 |
| **Request Size Distribution** | 64B (60%), 128B (30%), 256B (10%) |
| **Address Pattern** | Random + hotspot (20/80 rule) |
| **Expected Channel Utilization** | 55% |
| **QoS Class** | 4 (medium priority) |
| **Row Buffer Hit Rate** | 75% |
| **Refresh Sensitivity** | Low |

### Profile C: Synthetic Stress (Mixed, High Bandwidth)

| Parameter | Value |
|-----------|-------|
| **Primary Use** | Stress testing, thermal profiling |
| **Read/Write Ratio** | 50:50 |
| **Request Size Distribution** | 64B (20%), 128B (30%), 256B (30%), 512B (20%) |
| **Address Pattern** | Uniform random |
| **Expected Channel Utilization** | 90% |
| **QoS Class** | 15 (lowest priority) |
| **Row Buffer Hit Rate** | 25% |
| **Refresh Sensitivity** | High |

## 5. Recommended Test Traffic Patterns

### 5.1 Random Uniform
- Generate random addresses across full address space
- Equal probability for all channels/banks
- **Use:** Baseline performance measurement

### 5.2 Stride-Based (Tensor Access)
- Access pattern: addr += stride
- Common strides: 64, 128, 256, 1024
- **Use:** Tensor/matrix operation simulation

### 5.3 Hotspot (20/80 Rule)
- 80% of accesses to 20% of address space
- 20% of accesses to remaining 80%
- **Use:** Real-world workload approximation

### 5.4 Stream (Sequential)
- Sequential address increment
- Burst-aligned
- **Use:** Bandwidth measurement

### 5.5 Mixed Traffic
- Combine multiple patterns
- Configurable ratios
- **Use:** Multi-tenant simulation

## 6. Workload-to-Model-Questions Mapping

| Question | Profile A | Profile B | Profile C |
|----------|-----------|-----------|-----------|
| Sustained bandwidth? | 75% of peak | 55% of peak | 90% of peak |
| Latency from controller? | 15-25 ns | 10-20 ns | 20-30 ns |
| Channel grouping? | 8-channel groups | Independent | 16-channel groups |
| Queue depth? | 32-64 entries | 16-32 entries | 64-128 entries |
| Address mapping? | Row-column-bank-channel | Bank-row-column-channel | Channel-row-bank-column |

## 7. Refresh Impact Analysis

| Workload | Refresh Overhead | Recommended Refresh Mode |
|----------|------------------|--------------------------|
| AI Training | 3-5% | Autonomous (aggressive) |
| AI Inference | 1-3% | Per-bank (conservative) |
| Synthetic Stress | 5-8% | All-bank (periodic) |

## 8. Next Steps

1. Implement TrafficGenerator with workload profiles
2. Create trace-based traffic replay
3. Calibrate model against vendor benchmarks
4. Add AI-specific traffic patterns (transformer, convolution)