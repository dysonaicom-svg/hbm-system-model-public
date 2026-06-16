# HBM4 System Architecture

This document describes the overall system architecture of the HBM4 System Modeling Platform, covering both HBM3 and HBM4 specifications.

## System Overview

The HBM4 System is organized into 5 layers implementing a complete memory subsystem:

```
+----------------------------------------------------------------------+
|                    Layer 0: Traffic Generator                        |
|  +----------------------+  +----------------------+  +---------------+ |
|  | AI Training Patterns |  | AI Inference Patterns| | Synthetic    | |
|  | - Weight Update      |  | - Burst Read         | | - Random     | |
|  | - Gradient Compute   |  | - Weight Reuse       | | - Sequential | |
|  | - Feature Map        |  | - Mixed Precision   | | - Stride     | |
|  +----------------------+  +----------------------+  +---------------+ |
+----------------------------------------------------------------------+
                                    |
                                    v
+----------------------------------------------------------------------+
|                    Layer 1: Interconnect (NoC/AXI)                    |
|  +----------------------+  +----------------------+  +---------------+ |
|  | Crossbar            |  | Mesh                 | | Binary Tree   | |
|  | - O(1) routing      |  | - XY routing        | | - O(log N)    | |
|  | - Low latency       |  | - Good scalability  | | - Broadcast   | |
|  +----------------------+  +----------------------+  +---------------+ |
+----------------------------------------------------------------------+
                                    |
                                    v
+----------------------------------------------------------------------+
|                    Layer 2: HBM Controller (Phase A)                   |
|  +----------------------+  +----------------------+  +---------------+ |
|  | Address Decoder      |  | Request Queues       | | Scheduler     | |
|  | - RBC/BCR/CRB       |  | - Read Queue         | | - FR-FCFS     | |
|  | - HBM4 32-ch         |  | - Write Queue        | | - QoS Weighted| |
|  +----------------------+  +----------------------+  +---------------+ |
|  +----------------------+  +----------------------+  +---------------+ |
|  | Refresh Scheduler   |  | Command Sequencer    | | Command Pipe  | |
|  | - Per-bank REF      |  | - ACT/RD/WR/PRE     | | - Timing      | |
|  | - DRFM support       |  | - Auto-precharge    | | - Flow ctrl  | |
|  +----------------------+  +----------------------+  +---------------+ |
+----------------------------------------------------------------------+
                                    |
                                    v
+----------------------------------------------------------------------+
|                    Layer 3: HBM DRAM Model (Phase B)                 |
|  +----------------------+  +----------------------+  +---------------+ |
|  | Channel Model        |  | Bank State FSM      | | Stack Model   | |
|  | - 32 ch (HBM4)       |  | - IDLE/ACT/OPEN     | | - TSV array   | |
|  | - 2 pseudo-ch/ch     |  | - tRCD/tRP/tRAS     | | - 4 stacks    | |
|  +----------------------+  +----------------------+  +---------------+ |
|  +----------------------+  +----------------------+  +---------------+ |
|  | PHY Model            |  | Power Estimator     | | ECC/CRC       | |
|  | - Training seq       |  | - Dynamic power     | | - Error det   | |
|  | - DFI 5.1 interface  |  | - Thermal model     | | - Correction  | |
|  +----------------------+  +----------------------+  +---------------+ |
+----------------------------------------------------------------------+
                                    |
                                    v
+----------------------------------------------------------------------+
|                    Layer 4: Statistics & Verification                  |
|  - Bandwidth, latency, hit rate, efficiency                         |
|  - Per-channel statistics                                           |
|  - Power consumption & thermal                                       |
|  - RTL/Python model comparison                                      |
+----------------------------------------------------------------------+
```

## Module Hierarchy

### Layer 0: Traffic Generator

| Module | File | Description |
|--------|------|-------------|
| TrafficGenerator | `model/traffic/traffic_generator.py` | Main traffic generation engine |
| TrafficConfig | `model/traffic/traffic_generator.py` | Traffic configuration |
| AddressGenerator | `model/traffic/traffic_generator.py` | Address pattern generator |
| AITrainingPattern | `model/traffic/traffic_generator.py` | AI training patterns |
| AIInferencePattern | `model/traffic/traffic_generator.py` | AI inference patterns |
| SyntheticPattern | `model/traffic/traffic_generator.py` | Synthetic patterns |

### Layer 1: Interconnect

| Module | File | Description |
|--------|------|-------------|
| InterconnectBase | `model/interconnect/interconnect.py` | Base class for all interconnects |
| CrossbarInterconnect | `model/interconnect/interconnect.py` | Full NxM crossbar switch |
| MeshInterconnect | `model/interconnect/interconnect.py` | 2D mesh grid interconnect |
| BinaryTreeInterconnect | `model/interconnect/interconnect.py` | Hierarchical binary tree |
| InterconnectFactory | `model/interconnect/interconnect.py` | Factory for creating interconnects |

### Layer 2: HBM Controller (Phase A)

| Module | File | Description |
|--------|------|-------------|
| HBMController | `model/controller/controller.py` | Main controller |
| HBM4Controller | `model/controller/hbm4_controller.py` | HBM4-specific controller |
| HBMConfig | `model/controller/config.py` | Configuration class |
| HBM4Spec | `model/dram/hbm4_spec.py` | HBM4 specification constants |
| AddressDecoder | `model/controller/address_decoder.py` | Address mapping (HBM3) |
| HBM4AddressDecoder | `model/controller/hbm4_address_decoder.py` | HBM4 32-channel decoder |
| FRFCFSScheduler | `model/controller/scheduler.py` | FR-FCFS algorithm |
| HBM4QoSScheduler | `model/controller/hbm4_qos_scheduler.py` | HBM4 QoS with anti-starvation |
| HBM4RefreshScheduler | `model/controller/hbm4_refresh_scheduler.py` | Per-bank refresh |
| QueueManager | `model/controller/queue.py` | Request queue management |
| HBMRequest | `model/controller/request.py` | Request data structure |
| HBMResponse | `model/controller/request.py` | Response data structure |

### Layer 3: DRAM Model (Phase B)

| Module | File | Description |
|--------|------|-------------|
| DRAMModel | `model/dram/dram_model.py` | Complete DRAM model |
| HBM4Channel | `model/dram/hbm4_channel_model.py` | HBM4 channel with 32 ch |
| ChannelModel | `model/dram/channel_model.py` | HBM3 channel structure |
| BankStateMachine | `model/dram/bank_state_machine.py` | Bank FSM |
| DFIInterface | `model/dram/dfi_interface.py` | DFI 5.1 interface |
| PowerEstimator | `model/dram/power_estimator.py` | Power calculation |
| LaneRepair | `model/dram/lane_repair.py` | Redundancy repair |
| ECC_CRC | `model/dram/ecc_crc.py` | Error detection/correction |
| PHYTraining | `model/dram/phy_training.py` | PHY training sequences |

### Layer 4: Verification & Analysis

| Module | File | Description |
|--------|------|-------------|
| HBMSimulator | `sim/simulator.py` | Cycle-accurate simulator |
| BandwidthBenchmark | `model/benchmark/bandwidth_benchmark.py` | Bandwidth testing |
| LatencyBenchmark | `model/benchmark/latency_benchmark.py` | Latency testing |
| SchedulerBenchmark | `model/benchmark/scheduler_benchmark.py` | Scheduler comparison |

## HBM4 vs HBM3 Architecture Differences

| Feature | HBM3 | HBM4 |
|---------|------|------|
| Channels per stack | 8 | 32 |
| Total pseudo-channels | 16 | 64 |
| Interface width | 1024-bit | 2048-bit |
| Data rate | 6.4 GT/s | 8-16 GT/s |
| Peak bandwidth | 819 GB/s/stack | 2 TB/s/stack |
| Address bits (channel) | 3 bits | 5 bits |
| Banks per pseudo-channel | 16 | 16 |
| Bank groups per channel | 8 | 8 |
| Clock period | 781 ps | 125-62 ps |

## Data Flow

### Request Processing Pipeline

```
1. Traffic Generator creates HBMRequest
   ├─> addr: uint64
   ├─> length: int (bytes)
   ├─> is_read: bool
   ├─> qos: int (0-15)
   └─> burst_length: int

2. HBMController.submit_request()
   ├─> HBM4AddressDecoder.decode() extracts fields
   │   ├─> stack_id (Addr[47:46])     - 2 bits
   │   ├─> channel_id (Addr[45:41])   - 5 bits (HBM4)
   │   ├─> pseudo_channel_id (Addr[40]) - 1 bit
   │   ├─> bank_group_id (Addr[39:37]) - 3 bits
   │   ├─> bank_id (Addr[36:33])       - 4 bits
   │   ├─> row_id (Addr[32:17])        - 16 bits
   │   ├─> col_id (Addr[16:11])        - 6 bits
   │   └─> burst/offset (Addr[10:6])   - 5 bits
   │
   ├─> QueueManager.push_read/push_write()
   └─> Check row hit in bank_states

3. HBMController.tick() - one cycle
   ├─> RefreshScheduler.check_refresh()
   │   └─> Per-bank refresh rotation
   ├─> Scheduler.schedule()
   │   ├─> FR-FCFS: row-hit priority, age-based tiebreak
   │   └─> QoS: weighted by priority class (0-15)
   └─> returns (HBMRequest, HBMResponse)

4. CommandSequencer.generate_command_sequence()
   ├─> Row miss: ACT → RD/WR → PRE
   └─> Row hit: RD/WR (direct access)

5. CommandPipeline tracks timing
   └─> DRAMModel.execute_*()

6. HBMResponse returned with latency
```

### Refresh Flow

```
tREFI interval expires (3.9 us)
    │
    ▼
HBM4RefreshScheduler.needs_refresh()
    │
    ▼
HBM4RefreshScheduler.get_refresh_command()
    │
    ├─> Mode: PER_BANK (staggered refresh)
    │   ├─> Rotate through banks (16 per pseudo-channel)
    │   ├─> Issue REFsb command
    │   └─> Wait nRFC cycles (180 @ 8GT/s)
    │
    ├─> Mode: ALL_BANKS
    │   ├─> Issue REFab command
    │   └─> Wait nRFC cycles
    │
    └─> Mode: BANK_GROUP
        ├─> Refresh one bank group per interval
        └─> Distribute load across time

Resume normal traffic
```

## Address Mapping

### HBM4 Default (RBC - Row-Bank-Channel)

```
Bit positions:  [47:46] [45:41] [40]  [39:37] [36:33] [32:17]  [16:11] [10:9] [8:6]
                Stack    Channel  Pch   BG       Bank     Row       Col    Burst  Offset
                ID       (32)    (2)   (8)     (16)     (64K)    (64)   (4)    (8B)

Total address space: 2^48 = 256 TB
Effective per stack: 2^46 = 64 TB
```

### HBM4 Address Bit Fields

| Field | Bits | Range | Description |
|-------|------|-------|-------------|
| Stack ID | 2 | 0-3 | Stack selector (4 stacks) |
| Channel | 5 | 0-31 | Channel ID (32 channels) |
| Pseudo-channel | 1 | 0-1 | Sub-channel (2 per channel) |
| Bank group | 3 | 0-7 | Bank group (8 per pseudo-channel) |
| Bank | 4 | 0-15 | Bank within group (16 per group) |
| Row | 16 | 0-65535 | Row address (64K rows) |
| Column | 6 | 0-63 | Column address (64 per row) |
| Burst beat | 2 | 0-3 | Burst alignment (4-beat) |
| Byte offset | 3 | 0-7 | Byte offset within burst |

### Mapping Schemes

| Scheme | Description | Best for |
|--------|-------------|----------|
| `rbc` (default) | Row-Bank-Channel | Sequential access, row hits |
| `bcr` | Bank-Channel-Row | Maximize bank parallelism |
| `crb` | Channel-Row-Bank | Cross-channel random access |
| `hbm4` | HBM4 RBC variant | Same as RBC |

## Timing Parameters

### HBM3 (6.4 Gbps)

| Parameter | Value | Description |
|-----------|-------|-------------|
| tCK | 781.25 ps | Clock period |
| tRCD | 14 cycles | RAS to CAS delay |
| tCL | 14 cycles | CAS latency |
| tRP | 14 cycles | Precharge time |
| tRAS | 34 cycles | RAS active time |
| tRFC | 295 cycles | Refresh cycle time |
| tREFI | 3.9 us | Average refresh interval |
| tCCD | 4 cycles | CAS-to-CAS delay |

### HBM4 (8 Gbps baseline)

| Parameter | Value | Description |
|-----------|-------|-------------|
| tCK | 125 ps | Clock period (8 GHz DDR) |
| tRCD | 8 cycles | RAS to CAS delay |
| tCL | 8 cycles | CAS latency |
| tRP | 8 cycles | Precharge time |
| tRAS | 20 cycles | RAS active time |
| tRFC | 180 cycles | Refresh cycle time |
| tREFI | 3.9 us | Average refresh interval |
| tCCD | 4 cycles | CAS-to-CAS delay |
| tFAW | 16 cycles | Four-activate window |

### HBM4 Speed Grades

| Speed Grade | Data Rate | tCK | Target Application |
|-------------|-----------|-----|---------------------|
| 8 Gbps | 8 GT/s | 125 ps | JEDEC baseline |
| 12 Gbps | 12 GT/s | 83.3 ps | Extended rate |
| 16 Gbps | 16 GT/s | 62.5 ps | Maximum rate (HBM4E) |

## QoS Scheduler Architecture

### Priority Levels

| Level | Name | Bandwidth Guarantee | Typical Use |
|-------|------|---------------------|-------------|
| 15 | CRITICAL | 200 GB/s | Real-time, latency-critical |
| 12 | HIGH | 300 GB/s | High priority traffic |
| 8 | NORMAL | 200 GB/s | Normal workloads |
| 4 | LOW | 100 GB/s | Background/batch |
| 0 | IDLE | 0 GB/s | Idle/probe traffic |

### Anti-Starvation Policy

```
1. Track per-QoS bandwidth over 1ms window
2. Below guarantee: always schedule
3. Above cap: cannot schedule (prevents starvation)
4. Between guarantee/cap: fair round-robin
5. FR-FCFS within same priority (row hits first)
```

## DRAM Command Encoding

### HBM4 Commands (Numeric)

| Command | Value | Description |
|---------|-------|-------------|
| NOP | 0 | No operation |
| ACT | 1 | Activate row |
| READ | 2 | Read command |
| WRITE | 3 | Write command |
| PRE | 4 | Precharge single bank |
| PREA | 5 | Precharge all banks |
| REF | 6 | Refresh (all banks) |
| RFM | 7 | Row flash memory refresh |

### Command Sequences

```
Row Miss:
  ACT → tRCD → RD/WR → tRTPS → PRE → tRP (ready for next ACT)

Row Hit:
  RD/WR → tRTPS → PRE (optional) → tRP (if needed)

Refresh:
  REF (all banks) or REFsb (single bank) → tRFC → ready
```

## Bank State Machine

```
                    +--------+
                    | IDLE   |<----+
                    +--------+     |
                       |    PRE     |
                       v            |
                 +-----------+      |
                 | ACTIVATING|     |
                 | (tRCD)    |-----+
                 +-----------+
                       |
                       v
                 +-----------+
                 | ACTIVE    |----+
                 +-----------+    |
                    |    PRE     |
                    v            |
              +-----------+      |
              |PRECHARGING|------+
              | (tRP)     |
              +-----------+
```

## RTL/UVM Structure

```
rtl/
├── hbm_types.svh          # Type definitions
│   ├── addr_t             # 48-bit address
│   ├── req_type_t         # READ/WRITE/REFRESH
│   ├── cmd_t              # ACT/RD/WR/PRE/REF/MRS/ZQ
│   ├── bank_state_t       # IDLE/ACT/OPEN
│   └── timing_t           # Timing parameters
│
├── hbm_pkg.sv             # UVM package
│   ├── hbm_configuration  # Configuration class
│   └── hbm_transaction    # Transaction class
│
├── hbm_controller.sv      # Controller RTL
│   ├── addr_decoder       # Address decoder
│   ├── request_queue      # Request queues
│   ├── fr_fcfs_scheduler # FR-FCFS scheduler
│   └── command_fsm        # Command FSM
│
├── dram_model.sv          # DRAM behavioral model
│   ├── bank_fsm           # Bank state machine
│   ├── memory_array       # Memory array model
│   └── timing_checker     # Timing verification
│
└── hbm_controller_tb.cpp  # C++ testbench

verification/
├── reference_model/       # Reference models
│   ├── dram_ref_model.sv  # Performance reference
│   ├── addr_decoder_ref.sv # 6 mapping modes
│   ├── bandwidth_calc.sv   # Bandwidth calculator
│   └── timing_checker.sv   # Timing checker
│
└── uvm/                   # UVM environment
    ├── hbm_env_pkg.sv     # Environment package
    ├── hbm_test_pkg.sv     # Test package
    ├── hbm_tb.sv           # Testbench top
    └── Makefile            # Build system
```

## Key Data Structures

### HBMRequest

```python
@dataclass
class HBMRequest:
    addr: int              # 64-bit address
    length: int            # bytes
    is_read: bool          # True=read, False=write
    qos: int = 8           # 0-15 priority

    # Decoded fields
    stack_id: int
    channel_id: int
    pseudo_channel_id: int
    bank_group_id: int
    bank_id: int
    row_id: int
    col_id: int

    # State tracking
    state: RequestState    # PENDING/SCHEDULED/IN_PROGRESS/COMPLETED/FAILED
    row_hit: bool
    arrival_time: float
    completion_time: float
```

### DecodedAddress

```python
@dataclass
class DecodedAddress:
    stack_id: int = 0
    channel_id: int = 0
    pseudo_channel_id: int = 0
    bank_group_id: int = 0
    bank_id: int = 0
    row_id: int = 0
    col_id: int = 0
```

### HBM4Command

```python
class HBM4Command(IntEnum):
    NOP = 0      # No operation
    ACT = 1      # Activate
    READ = 2     # Read
    WRITE = 3    # Write
    PRE = 4      # Precharge
    PREA = 5     # Precharge all
    REF = 6      # Refresh
    RFM = 7      # Row flash memory
```

## Performance Metrics

| Metric | Formula | HBM3 Target | HBM4 Target |
|--------|---------|------------|-------------|
| Bandwidth | bytes / time | 819 GB/s/stack | 2 TB/s/stack |
| Efficiency | busy_cycles / total_cycles | > 80% | > 85% |
| Latency | completion - arrival | ~35 ns | ~25 ns |
| Row Hit Rate | row_hits / total | > 70% | > 70% |
| Bandwidth Efficiency | actual / peak | > 60% | > 65% |

## File Structure

```
/home/ic/JXTF/HBM/
├── model/
│   ├── controller/           # Phase A: Controller
│   │   ├── controller.py
│   │   ├── hbm4_controller.py
│   │   ├── hbm4_address_decoder.py
│   │   ├── hbm4_qos_scheduler.py
│   │   ├── hbm4_refresh_scheduler.py
│   │   ├── config.py
│   │   ├── request.py
│   │   ├── queue.py
│   │   ├── scheduler.py
│   │   ├── refresh_scheduler.py
│   │   └── ...
│   ├── dram/                # Phase B: DRAM Model
│   │   ├── dram_model.py
│   │   ├── hbm4_channel_model.py
│   │   ├── hbm4_spec.py
│   │   ├── bank_state_machine.py
│   │   ├── dfi_interface.py
│   │   ├── power_estimator.py
│   │   └── ...
│   ├── interconnect/       # Layer 1: Interconnect
│   │   └── interconnect.py
│   ├── traffic/            # Layer 0: Traffic Generator
│   │   └── traffic_generator.py
│   └── benchmark/          # Benchmarks
│       ├── bandwidth_benchmark.py
│       ├── latency_benchmark.py
│       └── scheduler_benchmark.py
├── sim/                     # Simulation
│   └── simulator.py
├── rtl/                     # RTL
│   ├── hbm_controller.sv
│   ├── hbm_types.svh
│   └── ...
├── tests/                   # Tests
│   ├── controller/
│   ├── dram/
│   ├── integration/
│   └── ...
└── docs/                    # Documentation
    ├── API.md
    ├── ARCHITECTURE.md
    ├── QUICKSTART.md
    └── design/
```

## Related Documents

- [API Documentation](API.md) - Complete API reference
- [Quick Start Guide](QUICKSTART.md) - Usage examples
- [Design Document](design/2026-06-15-hbm-system-model-design.md) - Complete design specification
- [HBM3 Spec](../research/hbm3_spec.md) - HBM3 parameter reference
- [Ramulator2](../research/ramulator2/) - Reference simulator