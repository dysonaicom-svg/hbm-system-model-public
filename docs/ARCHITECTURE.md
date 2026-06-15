# HBM System Architecture

This document describes the overall system architecture of the HBM System Modeling Platform.

## System Overview

```
+------------------+     +------------------+     +------------------+
| Traffic Generator|     |  Trace Reader    |     |  External AXI   |
| (Random/Seq/etc) |     |  (Ramulator2)    |     |  Master         |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         v                        v                        v
+----------------------------------------------------------------------+
|                        Interconnect (NoC/AXI)                        |
|                    Message formatting, routing, arbitration           |
+----------------------------------------------------------------------+
                                    |
                                    v
+----------------------------------------------------------------------+
|                      HBM Controller (Phase A)                         |
|  +------------------+  +------------------+  +------------------+    |
|  | Address Decoder  |  | Request Queues   |  | Scheduler        |    |
|  | - RBC/BCR/CRB    |  | - Read Queue     |  | - FR-FCFS        |    |
|  | - HBM3/HBM4      |  | - Write Queue    |  | - QoS Weighted   |    |
|  +------------------+  +------------------+  +------------------+    |
|  +------------------+  +------------------+  +------------------+    |
|  | Refresh Manager  |  | Command Sequencer|  | Command Pipeline |    |
|  | - tREFI/tRFC     |  | - ACT/RD/WR/PRE  |  | - Timing checks  |    |
|  +------------------+  +------------------+  +------------------+    |
+----------------------------------------------------------------------+
                                    |
                                    v
+----------------------------------------------------------------------+
|                      HBM DRAM Model (Phase B)                         |
|  +------------------+  +------------------+  +------------------+    |
|  | Channel Model    |  | Bank State FSM   |  | Stack Model      |    |
|  | - 8 ch per stack |  | - IDLE/ACT/OPEN  |  | - 2-4 stacks    |    |
|  | - Pseudo-ch      |  | - tRCD/tRP/tRAS  |  | - TSV array      |    |
|  +------------------+  +------------------+  +------------------+    |
|  +------------------+  +------------------+  +------------------+    |
|  | PHY Model        |  | Power Estimator  |  | ECC/CRC Engine  |    |
|  | - Training seq   |  | - Dynamic power  |  | - Error detect  |    |
|  | - Training state |  | - Leakage        |  | - Correction    |    |
|  +------------------+  +------------------+  +------------------+    |
+----------------------------------------------------------------------+
                                    |
                                    v
+----------------------------------------------------------------------+
|                      Statistics Collector                            |
|  - Bandwidth, latency, hit rate, efficiency                          |
|  - Per-channel statistics                                             |
|  - Power consumption                                                 |
+----------------------------------------------------------------------+
```

## Module Hierarchy

### Phase A: HBM Controller Model

| Module | File | Description |
|--------|------|-------------|
| Controller | `model/controller/controller.py` | Main controller integrating all Phase A components |
| Address Decoder | `model/controller/address_decoder.py` | Address mapping and decoding (RBC/BCR/CRB) |
| HBM4 Address Decoder | `model/controller/hbm4_address_decoder.py` | HBM4 32-channel address decoder |
| Scheduler | `model/controller/scheduler.py` | FR-FCFS scheduling algorithm |
| QoS Scheduler | `model/controller/qos_scheduler.py` | QoS-weighted scheduling |
| HBM4 QoS Scheduler | `model/controller/hbm4_qos_scheduler.py` | HBM4 enhanced QoS |
| Refresh Scheduler | `model/controller/refresh_scheduler.py` | Refresh management (tREFI/tRFC) |
| Request Queue | `model/controller/queue.py` | Read/write request queues |
| Request | `model/controller/request.py` | Request/response data structures |
| Command Sequencer | `model/controller/command_sequencer.py` | DRAM command sequence generation |
| Command Pipeline | `model/controller/command_pipeline.py` | Command timing and execution |

### Phase B: DRAM Timing Model

| Module | File | Description |
|--------|------|-------------|
| DRAM Model | `model/dram/dram_model.py` | Complete DRAM model integration |
| Channel Model | `model/dram/channel_model.py` | HBM3/HBM4 channel structure |
| Bank State Machine | `model/dram/bank_state_machine.py` | Bank FSM (IDLE/ACTIVATING/ACTIVE/PRECHARGING) |
| Timing Parameters | `model/dram/timing.py` | HBM2/HBM3/HBM4 timing specs |
| PHY Training | `model/dram/phy_training.py` | PHY training sequences |
| Power Estimator | `model/dram/power_estimator.py` | Dynamic/leakage power calculation |
| ECC/CRC | `model/dram/ecc_crc.py` | Error detection and correction |
| Lane Repair | `model/dram/lane_repair.py` | Redundancy repair logic |
| DFI Interface | `model/dram/dfi_interface.py` | DFI timing interface |

### Phase C: PHY Integration (Future)

- Signal integrity modeling
- Voltage/temperature compensation
- Read/write leveling

## Data Flow

### Request Processing Pipeline

```
1. Traffic Generator creates HBMRequest
   └─> addr: uint64
   └─> length: int (bytes)
   └─> is_read: bool
   └─> qos: int (0-15)

2. HBMController.submit_request()
   ├─> AddressDecoder.decode() extracts fields
   │   ├─> stack_id (Addr[47:46])
   │   ├─> channel_id (Addr[45:43])
   │   ├─> pseudo_channel_id (Addr[42])
   │   ├─> bank_group_id (Addr[41:39])
   │   ├─> bank_id (Addr[38:34])
   │   ├─> row_id (Addr[33:16])
   │   └─> col_id (Addr[15:3])
   │
   ├─> QueueManager.push_read/push_write()

3. HBMController.tick() - one cycle
   ├─> RefreshScheduler.check_refresh()
   ├─> Scheduler.schedule()
   │   ├─> FR-FCFS: row-hit priority, age-based tiebreak
   │   └─> QoS: weighted by priority class
   └─> returns (HBMRequest, HBMResponse)

4. CommandSequencer.generate_command_sequence()
   └─> ACT → RD/WR → PRE (for row miss)
   └─> RD/WR (for row hit)

5. CommandPipeline tracks timing
   └─> DRAMModel.execute_*()

6. HBMResponse returned with latency
```

### Refresh Flow

```
tREFI interval expires
    │
    ▼
RefreshScheduler.needs_refresh()
    │
    ▼
RefreshManager.schedule_refresh()
    │
    ├─> Suspend normal traffic
    ├─> Issue REF command
    └─> Wait tRFC cycles
    │
    ▼
Resume normal traffic
```

## Address Mapping

### HBM3 Default (RBC - Row-Bank-Channel)

```
Bit positions:  [47:46] [45:43] [42]  [41:39] [38:34] [33:16]  [15:3]   [2:0]
                Stack    Channel  PS    BG       Bank     Row       Col      Offset
                ID       (8)     (2)   (8)     (16)     (256K)    (8K)     (8B)

Total address space: 2^48 = 256 TB
Effective per stack: 2^46 = 64 TB
```

### Mapping Schemes

| Scheme | Description | Best for |
|--------|-------------|----------|
| RBC (default) | Row in lowest bits | Sequential access, row hits |
| BCR | Bank-Channel-Row | Maximize parallelism |
| CRB | Channel-Row-Bank | Cross-channel random |
| Custom | Configurable matrix | Application-specific |

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

### HBM4 (12.8 Gbps)

| Parameter | Value | Description |
|-----------|-------|-------------|
| tCK | 390.625 ps | Clock period |
| tRCD | 12 cycles | RAS to CAS delay |
| tCL | 12 cycles | CAS latency |
| tRP | 12 cycles | Precharge time |
| tRAS | 30 cycles | RAS active time |
| tRFC | 250 cycles | Refresh cycle time |
| tREFI | 3.9 us | Average refresh interval |
| tCCD | 4 cycles | CAS-to-CAS delay |

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

### DRAMCommand

```python
class DRAMCommand(Enum):
    NOP = 0      # No operation
    ACT = 1      # Activate
    READ = 2     # Read
    WRITE = 3    # Write
    PRE = 4      # Precharge
    REF = 5      # Refresh
    MRS = 6      # Mode Register Set
    ZQ = 7       # ZQ calibration
```

## Performance Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Bandwidth | bytes / time | Peak: 819.2 GB/s per stack (HBM3) |
| Efficiency | busy_cycles / total_cycles | > 80% |
| Latency | completion - arrival | HBM3: ~35 ns |
| Row Hit Rate | row_hits / total | > 70% for sequential |
| Bandwidth Efficiency | actual / peak | > 60% |

## Related Documents

- [Design Document](design/2026-06-15-hbm-system-model-design.md) - Complete design specification
- [HBM3 Spec](../research/hbm3_spec.md) - HBM3 parameter reference
- [Ramulator2](../research/ramulator2/) - Reference simulator