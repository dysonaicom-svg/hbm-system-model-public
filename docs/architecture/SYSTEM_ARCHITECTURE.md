# HBM4 System Architecture

## System Overview

```
+---------------------------------------------------------------------------------------+
|                              HBM4 SYSTEM ARCHITECTURE                                 |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   +------------------+         +-------------------+        +-------------------+    |
|   | Traffic Generator |         |  AXI/NoC Interconnect  |      | Trace Replayer   |    |
|   +--------+---------+         +---------+---------+        +---------+---------+    |
|            |                             |                              |             |
|            v                             v                              v             |
|   +------------------------------------------------------------------------------------+|
|   |                           HBM4 CONTROLLER (Phase A)                                ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+  ||
|   |  | Address   |  |  QoS     |  | Refresh   |  |  Request |  |   DFI Encoder    |  ||
|   |  | Decoder   |  | Scheduler|  | Scheduler |  |  Queue   |  |                  |  ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+  ||
|   +------------------------------------------------------------------------------------+|
|                                      |                                                   |
|                                      v                                                   |
|   +------------------------------------------------------------------------------------+|
|   |                          DFI 5.0 INTERFACE (Phase C)                              ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+   ||
|   |  | Command   |  | Low Power|  | Frequency |  | Control  |  |   Training      |   ||
|   |  | Encoding  |  | Manager  |  | Change    |  | Update   |  |   Interface     |   ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+   ||
|   +------------------------------------------------------------------------------------+|
|                                      |                                                   |
|                                      v                                                   |
|   +------------------------------------------------------------------------------------+|
|   |                     LOGIC BASE DIE (Phase G)                                       ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+  ||
|   |  | PAM3      |  | Lane     |  | ECC/CRC   |  | Thermal  |  |  Per-Channel    |  ||
|   |  | Encoder   |  | Repair   |  |           |  | Manager  |  |  Timing         |  ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+  ||
|   +------------------------------------------------------------------------------------+|
|                                      |                                                   |
|                                      v                                                   |
|   +------------------------------------------------------------------------------------+|
|   |                     DRAM TIMING MODEL (Phase B)                                     ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+  ||
|   |  | Bank State |  | Channel  |  | PHY       |  | Power    |  |  Timing          |  ||
|   |  | Machine    |  | Model    |  | Training  |  | Estimator|  |  Validation      |  ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+  ||
|   +------------------------------------------------------------------------------------+|
|                                      |                                                   |
|                                      v                                                   |
|   +------------------------------------------------------------------------------------+|
|   |                    RTL VERIFICATION (Phase D)                                       ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+  ||
|   |  | Controller |  | DRAM     |  | Testbench |  | Coverage |  |  UVM             |  ||
|   |  | RTL        |  | Model    |  |           |  | Analysis |  |  Environment     |  ||
|   |  +-----------+  +----------+  +-----------+  +----------+  +------------------+  ||
|   +------------------------------------------------------------------------------------+|
|                                                                                       |
+---------------------------------------------------------------------------------------+
```

## Component Hierarchy

```
HBM4 System
|
+-- Controller (model/controller/)
|   +-- HBM4Controller        # Main controller
|   +-- HBM4AddressDecoder    # Address translation
|   +-- HBM4QoSScheduler     # QoS scheduling
|   +-- HBM4RefreshScheduler # Refresh management
|   +-- RequestQueue         # Request buffering
|   +-- CommandPipeline      # Command sequencing
|   +-- DFIEncoder           # DFI protocol encoding
|
+-- DFI Interface (model/dram/)
|   +-- DFI5Interface        # DFI 5.0/5.1 protocol
|   +-- DFIPhyIF            # PHY interface
|   +-- DFITimingParameters # Timing parameters
|
+-- DRAM Model (model/dram/)
|   +-- HBM4Channel         # Channel model
|   +-- HBM4ChannelArray    # Channel array
|   +-- HBM4BankStateMachine # Bank state
|   +-- HBM4Spec            # HBM4 specification
|   +-- HBM4Timing          # Timing parameters
|
+-- Logic Base Die (model/dram/)
|   +-- HBM4LogicBaseDie    # LBD controller
|   +-- HBM4PAM3Encoder     # PAM3 encoding
|   +-- HBM4LaneRepairModel # Lane repair
|   +-- HBM4ECC            # ECC handling
|   +-- HBM4PowerEstimator  # Power modeling
|
+-- Simulator (sim/)
|   +-- HBMSimulator        # Main simulator
|   +-- HBM4UnifiedSimulator # Unified simulator
|   +-- RTLInterface        # RTL co-simulation
|   +-- TraceReplayer      # Trace replay
```

## Data Flow Diagram

```
Request Flow
=============

1. User Request
   |
   v
2. Traffic Generator / AXI Request
   |
   v
3. HBM4Controller
   |  +-- Address Decoder (translate to channel/bank/row/col)
   |  +-- QoS Scheduler (prioritize requests)
   |  +-- Request Queue (buffer pending requests)
   |
   v
4. DFI 5.0 Interface
   |  +-- Command Encoding
   |  +-- Low Power Management
   |  +-- Frequency Change Protocol
   |
   v
5. Logic Base Die
   |  +-- PAM3 Encoder (for 8+ GT/s)
   |  +-- Lane Repair Logic
   |  +-- ECC Insertion
   |
   v
6. DRAM Timing Model
   |  +-- Bank State Machine
   |  +-- Timing Validation
   |  +-- Command Scheduling
   |
   v
7. Response Flow
   |  +-- ECC Check
   |  +-- Lane Repair Decode
   |  +-- PAM3 Decoder
   |
   v
8. Completion
```

## Channel Architecture (HBM4)

```
32 Channels
===========

Channel 0                           Channel 31
+-----------+                       +-----------+
| PseudoCh0 |                       | PseudoCh0 |
+-----------+                       +-----------+
| BG0 | BG1 | BG2 | BG3 | BG4 |...| BG0 | BG1 |
| BK0 BK1|BK0 BK1|BK0 BK1|...|...|BK0 BK1|
+-----------+                       +-----------+
| PseudoCh1 |                       | PseudoCh1 |
+-----------+                       +-----------+
| BG0 | BG1 | BG2 | BG3 | BG4 |...| BG0 | BG1 |
| BK0 BK1|BK0 BK1|BK0 BK1|...|...|BK0 BK1|
+-----------+                       +-----------+

Each Channel:
- 2 Pseudo-Channels (64 total)
- 8 Bank Groups per Pseudo-Channel
- 2 Banks per Bank Group
- Total: 32 channels x 2 x 8 x 2 = 1024 banks

Addressing:
- Channel:   [31:27] (5 bits)
- PseudoCh:  [26:26] (1 bit)
- BankGroup: [25:23] (3 bits)
- Bank:      [22:21] (2 bits)
- Row:       [20:05] (16 bits)
- Column:    [04:00] (5 bits)
```

## Timing Domains

```
Independent Channel Timing (JEDEC Requirement)
============================================

Each channel has independent timing domain:

Channel 0         Channel 1         Channel 31
    |                |                |
    v                v                v
 +------+          +------+          +------+
 | tRCD |          | tRCD |          | tRCD |
 +------+          +------+          +------+
 | tCL  |          | tCL  |          | tCL  |
 +------+          +------+          +------+
 | tRP  |          | tRP  |          | tRP  |
 +------+          +------+          +------+

Key Timing Parameters (16 GT/s):
- tCK:     62.5 ps
- tRCD:    12 cycles (750 ps)
- tCL:     16 cycles (1000 ps)
- tCWL:    12 cycles (750 ps)
- tRP:     12 cycles (750 ps)
- tRAS:    28 cycles (1750 ps)
- tRC:     40 cycles (2500 ps)
- tRRDS:   3 cycles
- tRRDL:   4 cycles
- tFAW:    16 cycles
- tRREFI:  1950 cycles (7.8 us)
```

## State Machines

```
Controller State Machine
========================

     +--------+
     |  IDLE  |<--------------------+
     +--------+                     |
          |                         |
          | submit_request()        |
          v                         |
     +--------+                     |
     | ACTIVE |                     |
     +--------+                     |
          |                         |
          | requests pending        |
          v                         |
     +--------+                     |
     |BUSY   |---------------------+
     +--------+

DRAM Bank State Machine
=======================

     +-------+
     |CLOSED|<---------------------+
     +-------+                      |
          |                         |
          | ACT(row)                | PRECHARGE
          v                         |
     +-------+                      |
     |OPEN   |----------------------+
     +-------+
          |
          | READ/WRITE
          v
     +-------+
     |BUSY   |---------------------+
     +-------+                      |
                                      

DFI Low Power State Machine
===========================

     +--------+
     | LP_IDLE|<------------------+
     +--------+                   |
          |                       |
          | LP_REQ                |
          v                       |
     +--------+     +--------+    |
     |LP_CTRL |<--->|LP_DATA |    |
     +--------+     +--------+    |
          |                       |
          | LP_REQ                 |
          v                       |
     +--------+                   |
     |LP_SREF |<------------------+
     +--------+
```

## Signal Interface

```
DFI 5.0 Interface Signals
=========================

Controller                    PHY
    |                          |
    |--- cmd -------------------->
    |--- cmd_en ---------------->
    |--- address --------------->
    |--- bank ------------------->
    |                          |
    |                          |
    |<-- rddata_en ------------|
    |<-- wrdata_en ------------|
    |<-- ctrlupd_ack ----------|
    |<-- freq_change_ack ------|
    |<-- lp_ack ---------------|
    |<-- pwr_up_done ----------|
```

## Performance Optimization Path

```
Architecture -> Implementation -> Verification -> Optimization
     |               |                |               |
     v               v                v               v
  Phase A       Phase B           Phase D        Phase I
  Design        Implementation     RTL-Python    Performance
                (Code)             Alignment     Tuning
```

## Reference Standards

- JEDEC JESD270-4A: HBM4 Specification
- DFI 5.0/5.1: DDR PHY Interface Specification
- Synopsys DesignWare HBM4/4E Controller IP
- Ramulator 2.0: HBM3 Implementation
