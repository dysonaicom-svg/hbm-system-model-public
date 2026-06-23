# HBM4 Logic Base Die Architecture

## Overview

The HBM4 Logic Base Die serves as the intelligent control layer for High Bandwidth Memory Gen 4, integrating the memory controller, PHY interface, and thermal management within a single advanced package. This document describes the architecture of the Logic Base Die, which sits beneath the DRAM stacks in a 2.5D configuration.

## 1. Package Architecture

### 1.1 2.5D Integration

```
+------------------+     +------------------+
|   Host Interposer|     | Host Interposer  |
+------------------+     +------------------+
         |                        |
    +----v----+             +----v----+
    | HBM4    |             | HBM4    |
    | Stack 0 |             | Stack 1 |
    +----+----+             +----+----+
         |                        |
         |   +-----------+        |
         +---+Logic Base+---------+
             |   Die    |
             +----------+
```

### 1.2 Key Parameters

| Parameter | Value |
|-----------|-------|
| Number of HBM Stacks | 4-8 |
| Channels per Stack | 16 |
| Total Channels | 64-128 |
| Data Width per Channel | 256 bits (DQ128 + ECC) |
| Total IO Bandwidth | 2.5 TB/s @ 12.8 Gb/s/pin |
| PHY Interface | PAM3 (3-level signaling) |
| DFI Interface Version | 5.0 |

## 2. Functional Blocks

### 2.1 Controller Subsystem

```
+------------------------------------------------------------------+
|                        CONTROLLER SUBSYSTEM                       |
+------------------------------------------------------------------+
|  +------------------+  +------------------+  +------------------+ |
|  | AXI4 Master      |  | Address Decoder  |  | QoS Scheduler    | |
|  | Interface       |  |                  |  |                  | |
|  | (16/32 ports)   |  | Channel/Bank/Row  |  | Priority Queue   | |
|  |                  |  | Mapping          |  | Arbitration      | |
|  +--------+---------+  +--------+---------+  +--------+---------+ |
|           |                       |                       |      |
|           +----------+-------------+-----------------------+      |
|                      |              |                              |
|               +------v------+ +-----v------+                       |
|               | Request     | | Transaction |                       |
|               | Queue       | | Scheduler  |                       |
|               | (per-ch)    | |            |                       |
|               +-------------+ +------------+                       |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|                        DFI BRIDGE                                 |
+------------------------------------------------------------------+
|  +------------------+  +------------------+  +------------------+ |
|  | DFI Write Data   |  | DFI Read Data    |  | DFI Control      | |
|  | Packing         |  | Unpacking        |  | State Machine   | |
|  +------------------+  +------------------+  +------------------+ |
+------------------------------------------------------------------+
```

### 2.2 Address Mapping

The address decoder maps host addresses to HBM4 channel/bank/row structures:

```
Address[47:0] Layout (Host Physical Address):

Bits 47:42   - Reserved (64TB address space)
Bits 41:36   - Channel Select [5:0]    (64 channels max)
Bits 35:29   - Bank Group [6:0]        (8 bank groups per channel)
Bits 28:26   - Bank [2:0]              (8 banks per group)
Bits 25:17   - Row [8:0]               (16K rows per bank)
Bits 16:6    - Column [10:0]           (2K columns per row)
Bits 5:0     - Byte Select [5:0]       (64 bytes per beat)
```

**Key Characteristics:**
- Channel interleaving: 128B or 256B aligned
- Bank group parallelism: 2 bank groups active per channel
- Row buffer hit optimization: sequential access patterns preferred

### 2.3 QoS Scheduler

The Quality of Service scheduler implements multiple priority classes:

| Priority Class | Description | Latency Target |
|----------------|-------------|----------------|
| 0 (Critical) | Real-time, GPU compute | < 50 ns |
| 1 (High) | Accelerator DMA | < 200 ns |
| 2 (Medium) | General compute | < 500 ns |
| 3 (Low) | Background traffic | Best effort |

**Arbitration Policy:**
- Strict priority within class
- Round-robin among requests of same priority
- Bank conflict avoidance with look-ahead
- Starvation prevention via aging counters

## 3. PHY Subsystem

### 3.1 DFI 5.0 Interface

```
DFI Interface Signals:
+------------------+----------------------------------------+
| Signal Group     | Description                            |
+------------------+----------------------------------------+
| dfi_wrdata_cs[3] | Write data chip select (PAM3 levels)  |
| dfi_rddata_cs[3] | Read data chip select                  |
| dfi_addr[17:0]   | Row/column address                    |
| dfi_bankaddr[6:0]| Bank group/bank selection              |
| dfi_cs[3:0]      | Chip select per pseudo-channel         |
| dfi_cke[3:0]    | Clock enable                           |
| dfi_odt[3:0]    | On-die termination control              |
| dfi_reset_n     | DRAM reset                             |
| dfi_parity      | Address/command parity                 |
+------------------+----------------------------------------+
```

### 3.2 PAM3 Signaling

HBM4 introduces 3-level Pulse Amplitude Modulation (PAM3):

| Level | Voltage | Usage |
|-------|---------|-------|
| -1 | -V | Low data |
| 0 | 0V | Mid data |
| +1 | +V | High data |

**Encoding:** 2 PAM3 symbols = 3 bits (00, 01, 10, 11 encoded as -1/-1, -1/+1, +1/-1, +1/+1)

**Benefits:**
- 50% higher bandwidth per pin vs NRZ
- Reduced I/O power at 12.8 Gb/s
- Compatible with existing interposer channels

### 3.3 Channel PHY

Each HBM stack channel has dedicated PHY:

```
Per-Channel PHY:
+------------------+
| TX Elastic       |  +--------+
| Buffer           +-->+ Serializer +--> +--+  +--------+
+------------------+  +--------+       |PHY|  |  TSV   |
                                        |Pad|  |  Array |
+------------------+  +--------+       |   |  +--------+
| RX Elastic       |<--+Deserializer+<--+---+<--------+
| Buffer           |  +--------+
+------------------+
```

## 4. Refresh Management

### 4.1 Auto-Refresh

HBM4 refresh timing per JEDEC JESD335:

| Parameter | Value | Notes |
|-----------|-------|-------|
| tREFI | 1.95 us | Average refresh interval |
| tREFIpb | 3.9 us | Per-bank refresh interval |
| tRFC | 130 ns | Refresh-to-active delay |
| tREFW | 32 ms | Full array refresh window |

### 4.2 Self-Refresh

Enter self-refresh during low-power states:

```
State Machine:
+-------------+    +---------------+    +-------------+
| ACTIVE      +--->+ POWER_DOWN    +--->+ SELF_REFRESH|
| (Normal)    |    | (Fast exit)   |    | (Slow exit) |
+-------------+    +---------------+    +-------------+
      ^                  |                    |
      +------------------+--------------------+
```

**Self-Refresh Entry Conditions:**
- All channels idle for tCKE (min 5 cycles)
- No pending transactions
- DRAM temperature within operating range

## 5. Error Handling

### 5.1 ECC Support

Each 256-bit channel includes 32-bit ECC (single-error correct, double-error detect):

| ECC Mode | Data Width | Correction |
|----------|------------|------------|
| SECDED | 288b (256+32) | 1-bit correct, 2-bit detect |
| DECTED | 272b (256+16) | 2-bit detect only (reduced redundancy) |

### 5.2 Retry Mechanism

Transaction retry for uncorrectable errors:

```
+----------------+     +----------------+     +----------------+
| Error Detected |<----+ Log Error      +----->+ Notify Host    |
| (SECDED fail)  |     | (FIFO)         |     | (AXI DECERR)   |
+----------------+     +----------------+     +----------------+
                            |
                            +-----> +----------------+
                                    | Retry Queue   |
                                    | (max 4 retry) |
                                    +---------------+
```

## 6. Power Management

### 6.1 Power Domains

| Domain | Description | Typical Power |
|--------|-------------|---------------|
| PD_CONTROLLER | Controller logic | 50-100 mW |
| PD_PHY_TX | Transmit PHY | 200-400 mW |
| PD_PHY_RX | Receive PHY | 150-300 mW |
| PD_DRAM | DRAM arrays | 1-2 W per stack |

### 6.2 Clock Gating

- Fine-grained clock gating on idle logic
- PHY clock frequency scaling (0.5x to 1x)
- Retention registers in sleep state

## 7. Thermal Considerations

### 7.1 Thermal Throttling

The Logic Base Die operates in thermal proximity to DRAM stacks:

```
Temperature Zones:
+------------------+--------------------+--------------------+
| Zone             | Temperature        | Action             |
+------------------+--------------------+--------------------+
| Normal           | < 85C              | Full performance   |
| Throttle         | 85-100C            | Reduce bandwidth   |
| Critical         | > 100C             | Emergency throttle |
+------------------+--------------------+--------------------+
```

### 7.2 Thermal Sensors

- Per-channel thermal sensors (16 per stack)
- Aggregate temperature for throttle decision
- Thermal history for predictive throttling

## 8. Performance Monitoring

### 8.1 Counters

| Counter | Description | Width |
|---------|-------------|-------|
| tx_beat_cnt | Write beats transmitted | 48-bit |
| rx_beat_cnt | Read beats received | 48-bit |
| bank_conflict_cnt | Bank conflict stalls | 32-bit |
| refresh_overhead | Cycles spent in refresh | 32-bit |
| thermal_throttle_cycles | Throttle cycles | 16-bit |

### 8.2 Latency Measurement

- Per-transaction latency tracking
- Histogram bins: <100ns, 100-200ns, 200-500ns, >500ns
- Moving average and peak detection

## 9. Integration Checklist

- [ ] AXI4 interface integration
- [ ] DFI 5.0 compliance verification
- [ ] PAM3 eye diagram characterization
- [ ] Thermal throttling validation
- [ ] ECC correction verification
- [ ] Refresh timing compliance
- [ ] Power state transition verification
- [ ] Performance counter accuracy

## 10. References

- JEDEC JESD335: HBM4 Specification
- DFI 5.0 Specification
- HBM3 Compatibility Mode Requirements
- HBM4 Address Mapping Standard

---

*Document Version: 1.0*
*Last Updated: 2026-06-15*