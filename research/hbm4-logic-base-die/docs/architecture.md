# HBM4 Logic Base Die Architecture

**Date:** 2026-06-15
**Purpose:** High-level architecture documentation

## 1. Layer Model Overview

The HBM4 logic base die system is organized into 5 layers:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Power, Thermal, and Package                       │
│  ├── PowerEstimator                                         │
│  ├── ThermalModel                                          │
│  └── PDN modeling                                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: PHY, TSV, and Repair                             │
│  ├── TSV PHY                                               │
│  ├── D2D PHY (Host-facing)                                 │
│  ├── LaneRepair                                            │
│  └── Training state machine                                │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Logic Base Die Controller                        │
│  ├── HBM4Controller                                        │
│  ├── HBM4QoSScheduler                                     │
│  ├── HBM4RefreshScheduler                                 │
│  └── HBM4ChannelScheduler                                 │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Transaction and Workload                         │
│  ├── TrafficGenerator                                     │
│  ├── Address mapping                                      │
│  └── QoS classes                                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Public Configuration                             │
│  ├── HBM4Spec (JEDEC parameters)                         │
│  ├── HBM4Config (runtime config)                          │
│  └── Speed bin selection                                   │
└─────────────────────────────────────────────────────────────┘
```

## 2. Module Hierarchy

```
HBM4System
├── HBM4Spec (configuration)
├── HBM4Controller (integration)
│   ├── HBM4AddressDecoder
│   ├── HBM4QoSScheduler
│   ├── HBM4RefreshScheduler
│   ├── QueueManager
│   │   ├── ReadQueue (per channel)
│   │   └── WriteQueue (per channel)
│   └── ChannelScheduler (per channel)
│       └── CommandQueue
├── DFIInterface
│   ├── PhyController
│   └── FrequencyManager
├── TSVPHY
│   ├── TSVGroup
│   ├── TrainingFSM
│   └── LaneMapper
├── LaneRepair
├── HBM4ChannelModel (per channel)
│   ├── BankState[]
│   └── TimingEngine
├── PowerEstimator
│   ├── CommandEnergy
│   ├── PhyPower
│   └── ControllerPower
└── ThermalModel
    ├── HotspotTracker
    └── ThrottlingPolicy
```

## 3. Key Interfaces

### 3.1 Host to Controller Interface

```python
class HBM4Controller:
    def submit_request(addr, is_read, qos_level, size_bytes) -> request_id
    def tick() -> List[HBMResponse]
    def get_stats() -> HBM4ControllerStats
```

### 3.2 Controller to DRAM Interface

```python
class DFIInterface:
    def send_command(cmd, channel, bank, row, col)
    def send_data(data, channel)
    def receive_data(channel) -> data
    def get_phy_status(channel) -> PhyStatus
```

### 3.3 Configuration Interface

```python
class HBM4Spec:
    channels: int = 32
    pseudo_channels: int = 64
    data_width_per_channel: int = 64
    speed_bin_gbps: float = 8.0
    tCK_ps: float = 125.0
    # ... timing parameters
```

## 4. Data Flow

### 4.1 Read Request Flow

```
1. Host issues read request
       ↓
2. HBM4AddressDecoder maps address
   (channel, pseudo_channel, bank, row, col)
       ↓
3. HBM4QoSScheduler assigns priority
       ↓
4. QueueManager enqueues to channel queue
       ↓
5. ChannelScheduler selects next request
       ↓
6. DFIInterface sends ACT command
       ↓
7. DFIInterface sends RD command
       ↓
8. DFIInterface receives data
       ↓
9. LaneRepair checks ECC/CRC
       ↓
10. HBMResponse returned to host
```

### 4.2 Write Request Flow

```
1. Host issues write request + data
       ↓
2. HBM4AddressDecoder maps address
       ↓
3. LaneRepair adds ECC/CRC
       ↓
4. QueueManager enqueues to channel queue
       ↓
5. ChannelScheduler selects next request
       ↓
6. DFIInterface sends ACT command
       ↓
7. DFIInterface sends WR command + data
       ↓
8. HBMResponse returned to host
```

### 4.3 Refresh Flow

```
1. HBM4RefreshScheduler timer expires
       ↓
2. Scheduler selects refresh mode
   (REFpb or REFab)
       ↓
3. ChannelScheduler pauses traffic
       ↓
4. DFIInterface sends REF command
       ↓
5. DRAM performs refresh
       ↓
6. Traffic resumes
       ↓
7. ThermalModel updates temperature
```

## 5. Configuration Options

### 5.1 Speed Bin Selection

| Speed Bin | Data Rate | tCK | Notes |
|-----------|-----------|-----|-------|
| JEDEC Base | 8 Gb/s | 125 ps | Standard |
| Over-speed 1 | 10 Gb/s | 100 ps | Vendor |
| Over-speed 2 | 11 Gb/s | 91 ps | Vendor |
| Over-speed 3 | 12 Gb/s | 83 ps | Vendor |

### 5.2 Queue Depths

| Queue | Default | Min | Max |
|-------|---------|-----|-----|
| Read Queue | 32 | 8 | 128 |
| Write Queue | 32 | 8 | 128 |
| Command Queue | 16 | 4 | 64 |
| Response Queue | 64 | 16 | 256 |

### 5.3 QoS Levels

| Level | Priority | Use Case |
|-------|----------|----------|
| 0 | Highest | Critical interrupt |
| 1-3 | High | Real-time |
| 4-7 | Medium | Normal traffic |
| 8-11 | Low | Background |
| 12-15 | Lowest | Background |

## 6. State Machines

### 6.1 Controller State Machine

```
        ┌──────────┐
        │   IDLE   │
        └────┬─────┘
             │ init_complete
        ┌────▼─────┐
        │  READY   │◄─────────────────┐
        └────┬─────┘                  │
             │                        │
    ┌────────┼────────┐               │
    │        │        │               │
┌───▼──┐ ┌───▼──┐ ┌───▼──┐           │
│ READ │ │WRITE │ │REFRESH│           │
└──┬──┘ └──┬──┘ └───┬───┘           │
   │       │        │                │
   └───────┴────────┘               │
        │ process_complete          │
        └───────────────────────────┘
```

### 6.2 Channel Scheduler State

```
┌────────┐    ┌──────────┐    ┌──────────┐
│  IDLE  │───▶│ SCHEDULING│───▶│ ACTIVE   │
└────────┘    └──────────┘    └──────────┘
                   ▲               │
                   │               │ done
                   └───────────────┘
```

### 6.3 TSV PHY Training State

```
IDLE → WCK_CAL → DQ_CAL → RDDQ_CAL → WR_DQ_CAL → MARGIN → COMPLETE
                  │           │         │          │
                  └───────────┴─────────┴──────────┘
                              │ error
                              ▼
                           FAILED
```

## 7. Statistics Collection Points

| Module | Statistics |
|--------|------------|
| HBM4Controller | Total requests, latency histogram, throughput |
| QueueManager | Queue fill levels, overflow count |
| ChannelScheduler | Command count per type, row hit rate |
| HBM4QoSScheduler | Request count per QoS level |
| HBM4RefreshScheduler | Refresh count, refresh overhead |
| DFIInterface | PHY state time, frequency change count |
| TSVPHY | Training count, BER estimate |
| LaneRepair | Spare usage, remap count |
| PowerEstimator | Total power, per-component power |
| ThermalModel | Temperature, throttle events |

## 8. File Structure

```
model/hbm4/
├── __init__.py
├── power/
│   ├── __init__.py
│   ├── power_estimator.py
│   └── thermal_model.py
├── phy/
│   ├── __init__.py
│   └── tsv_phy.py
└── (controller modules in model/controller/)

model/dram/
├── hbm4_spec.py
├── hbm4_channel_model.py
├── dfi_interface.py
└── lane_repair.py

model/controller/
├── hbm4_controller.py
├── hbm4_address_decoder.py
├── hbm4_qos_scheduler.py
└── hbm4_refresh_scheduler.py
```

## 9. Integration Points

### 9.1 With Host Traffic Generator
- Interface: `submit_request()` API
- Protocol: Request/Response
- Synchronization: `tick()` driven

### 9.2 With DRAM Model
- Interface: DFI 5.1
- Protocol: DDR command/address/data
- Timing: HBM4 specification

### 9.3 With System Power/Thermal
- Interface: Observer pattern
- Updates: Per-cycle power, periodic thermal
- Control: Throttling signals