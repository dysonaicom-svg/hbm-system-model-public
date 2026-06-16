# HBM4 Usage Examples

This document provides comprehensive usage examples for the HBM4 System Modeling Platform. Each example demonstrates a specific feature or use case.

## Table of Contents

1. [Basic Controller Usage](#example-1-basic-controller-usage)
2. [Address Decoding](#example-2-address-decoding)
3. [QoS Scheduling](#example-3-qos-scheduling)
4. [Refresh Scheduling](#example-4-refresh-scheduling)
5. [DFI 5.0 Interface](#example-5-dfi-50-interface)
6. [Bandwidth Benchmarking](#example-6-bandwidth-benchmarking)
7. [Multi-Channel Simulation](#example-7-multi-channel-simulation)
8. [DRAM Features](#example-8-dram-features)
9. [Logic Base Die](#example-9-logic-base-die)

---

## Example 1: Basic Controller Usage

**File**: `examples/basic_controller.py`

Demonstrates basic HBM4 controller operations:
- Creating a controller instance
- Submitting read/write requests
- Running simulation cycles
- Retrieving statistics

```python
from model.dram.hbm4_spec import HBM4Spec
from model.controller.hbm4_controller import HBM4Controller

# Create controller with default HBM4 spec
controller = HBM4Controller()
print(f"Channels: {controller.channels}")
print(f"Pseudo-channels: {controller.pseudo_channels}")

# Create controller with custom speed grade
spec_16g = HBM4Spec(data_rate_gtps=16.0)
controller_fast = HBM4Controller(spec=spec_16g)
print(f"Peak bandwidth: {controller_fast.spec.bandwidth_gbs:.0f} GB/s")

# Submit read requests
read_addresses = [0x0001_0000_0000_0000, 0x0002_0000_0000_0000]
for addr in read_addresses:
    request_id = controller.submit_request(addr=addr, is_read=True, qos_level=8)
    print(f"Read request submitted: id={request_id}")

# Submit write requests
write_addresses = [0x0011_0000_0000_0000, 0x0012_0000_0000_0000]
for addr in write_addresses:
    request_id = controller.submit_request(addr=addr, is_read=False, qos_level=12)
    print(f"Write request submitted: id={request_id}")

# Run simulation
for cycle in range(500):
    responses = controller.tick()
    for resp in responses:
        print(f"Cycle {cycle}: Completed {resp.request_id}, latency={resp.latency}ns")

# Get statistics
stats = controller.get_stats()
print(f"Total requests: {stats['controller']['total_requests']}")
print(f"Row hit rate: {stats['controller']['row_hit_rate']:.2%}")
print(f"Average latency: {stats['controller']['average_latency_ns']:.1f}ns")

# Bandwidth measurement
bandwidth = controller.get_bandwidth_gbs()
print(f"Effective bandwidth: {bandwidth:.2f} GB/s")
```

**Run**: `python examples/basic_controller.py`

---

## Example 2: Address Decoding

**File**: `examples/address_decoding.py`

Demonstrates address decoding in HBM4:
- Creating address decoders with different mapping schemes
- Decoding addresses into component fields
- Extracting individual fields directly
- Validating addresses

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.hbm4_spec import HBM4Spec

# Create decoder with default RBC mapping
decoder = HBM4AddressDecoder()
print(f"Total address bits: {decoder.TOTAL_ADDR_BITS}")
print(f"Channels: {2 ** decoder.CHANNEL_BITS}")
print(f"Bank groups: {2 ** decoder.BG_BITS}")
print(f"Banks per group: {2 ** decoder.BANK_BITS}")
print(f"Rows per bank: {2 ** decoder.ROW_BITS}")

# Create decoders with different mapping schemes
for scheme in ["rbc", "bcr", "crb"]:
    decoder_s = HBM4AddressDecoder(mapping_scheme=scheme)
    print(f"Scheme {scheme.upper()}: {decoder_s._mapping_scheme}")

# Decode example address
addr = 0x0001_2345_6789_ABC0
decoded = decoder.decode(addr)
print(f"Address: 0x{addr:016X}")
print(f"  Channel: {decoded.channel_id}")
print(f"  Pseudo-channel: {decoded.pseudo_channel_id}")
print(f"  Bank group: {decoded.bank_group_id}")
print(f"  Bank: {decoded.bank_id}")
print(f"  Row: 0x{decoded.row_id:04X}")
print(f"  Column: {decoded.col_id}")

# Extract individual fields directly
print(f"Channel ID: {decoder.get_channel_id(addr)}")
print(f"Row ID: 0x{decoder.get_row_id(addr):04X}")
print(f"Bank ID: {decoder.get_bank_id(addr)}")

# Calculate address ranges
for ch in [0, 1, 15, 31]:
    start, end = decoder.get_address_range(channel=ch)
    print(f"Channel {ch:2d}: 0x{start:016X} - 0x{end:016X}")

# Address validation
valid_addrs = [0x0000_0000_0000_0000, 0x0000_0000_0000_0008]
invalid_addrs = [0x0000_0000_0000_0001, 0x0000_0000_0000_0005]
for addr in valid_addrs:
    print(f"0x{addr:016X}: {'Valid' if decoder.validate_address(addr) else 'Invalid'}")
for addr in invalid_addrs:
    print(f"0x{addr:016X}: {'Valid' if decoder.validate_address(addr) else 'Invalid'}")
```

**Run**: `python examples/address_decoding.py`

---

## Example 3: QoS Scheduling

**File**: `examples/qos_scheduling.py`

Demonstrates QoS scheduling features:
- 16-level priority scheduling
- Anti-starvation guarantees
- Bandwidth guarantees and caps
- FR-FCFS selection within same priority

```python
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel
from model.dram.hbm4_spec import HBM4Spec

# Create scheduler
scheduler = HBM4QoSScheduler()
print(f"Priority levels: {scheduler.priority_levels}")
print(f"QoS levels: CRITICAL={scheduler.QOS_CRITICAL}, HIGH={scheduler.QOS_HIGH}, "
      f"NORMAL={scheduler.QOS_NORMAL}, LOW={scheduler.QOS_LOW}")

# Bandwidth configuration
print("\nQoS Level | Guarantee (GB/s) | Cap (GB/s)")
print("-" * 40)
for qos in [scheduler.QOS_CRITICAL, scheduler.QOS_HIGH, 
            scheduler.QOS_NORMAL, scheduler.QOS_LOW]:
    guarantee = scheduler.bw_guarantee.get(qos, 0)
    cap = scheduler.bw_cap.get(qos, 0)
    print(f"{qos:10d} | {guarantee:14.1f} | {cap:10.1f}")

# Submit requests with different priorities
test_cases = [
    (QoSLevel.LOW, "Background traffic"),
    (QoSLevel.NORMAL, "Normal access"),
    (QoSLevel.HIGH, "High priority access"),
    (QoSLevel.CRITICAL, "Real-time critical"),
]

request_id = 1
for qos, description in test_cases:
    scheduler.submit_request(
        request_id=request_id,
        addr=0x1000 + request_id * 0x100,
        qos=qos,
        is_read=True,
        channel=request_id % 32,
        row_hit=(request_id % 3 == 0),
    )
    print(f"Request {request_id}: {description} (QoS={qos})")
    request_id += 1

# Schedule requests (selects highest priority first)
for i in range(6):
    scheduled = scheduler.schedule()
    if scheduled:
        print(f"Scheduled {i+1}: id={scheduled.request_id}, "
              f"QoS={scheduled.qos}, row_hit={scheduled.row_hit}")

# FR-FCFS within same priority
selected = scheduler2.select_next(mock_requests)
print(f"First selected: id={selected.request_id}, QoS={selected.qos}")

# Get statistics
stats = scheduler2.get_stats()
print(f"Total scheduled: {stats['total_scheduled']}")
print(f"Requests by QoS: {stats['by_qos']}")

# Modify bandwidth settings
scheduler.set_bandwidth_guarantee(15, 400.0)
print(f"CRITICAL guarantee: {scheduler.bw_guarantee[15]:.1f} GB/s")
```

**Run**: `python examples/qos_scheduling.py`

---

## Example 4: Refresh Scheduling

**File**: `examples/refresh_scheduling.py`

Demonstrates refresh scheduling features:
- All-bank refresh mode
- Per-bank refresh mode (default for HBM4)
- Bank group refresh mode
- DRFM (Direct Refresh Management) for row-hammer mitigation
- Staggered refresh for reduced peak power

```python
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.dram.hbm4_spec import HBM4Spec

# Create scheduler
scheduler = HBM4RefreshScheduler()
print(f"Default mode: {scheduler.mode.value}")
print(f"Refresh interval (tREFI): {scheduler.tREFI} cycles")
print(f"Refresh duration (tRFC): {scheduler.tRFC} cycles")
print(f"Per-bank interval (nRREFD): {scheduler.nRREFD} cycles")

# All-bank refresh mode
scheduler.set_mode(RefreshMode.ALL_BANKS)
print(f"Mode set to: {scheduler.mode.value}")

# Simulate until refresh is needed
for cycle in range(scheduler.tREFI - 5):
    scheduler.tick()

cmd = scheduler.get_refresh_command()
if cmd:
    cmd_name, ch, pch, bank = cmd
    print(f"Refresh command: {cmd_name}")

# Per-bank refresh mode
scheduler.set_mode(RefreshMode.PER_BANK)
print(f"Mode set to: {scheduler.mode.value}")

# Execute per-bank refreshes
for i in range(10):
    scheduler.tick()
    if scheduler.can_refresh():
        cmd = scheduler.get_refresh_command()
        if cmd:
            cmd_name, ch, pch, bank = cmd
            print(f"Refresh {i+1}: {cmd_name} ch={ch} pch={pch} bank={bank}")

# DRFM (Direct Refresh Management)
scheduler.enable_drfm(enabled=True, threshold=100)
print(f"DRFM enabled: {scheduler.drfm_enabled}")
print(f"Row-hammer threshold: {scheduler.drfm_rowhammer_threshold} cycles")

# Simulate row-hammer conditions
for cycle in range(200):
    scheduler.tick()

banks_needing_refresh = scheduler.get_banks_needing_refresh()
print(f"Banks needing refresh: {len(banks_needing_refresh)}")

# Get statistics
stats = scheduler.get_stats()
print(f"Total refreshes: {stats['total_refreshes']}")
print(f"Per-bank refreshes: {stats['per_bank_refreshes']}")
```

**Run**: `python examples/refresh_scheduling.py`

---

## Example 5: DFI 5.0 Interface

**File**: `examples/dfi_interface.py`

Demonstrates the DFI 5.0 interface between HBM4 controller and PHY:
- Command encoding and queueing
- Control update handshake
- Frequency change protocol
- Low power state management
- Power management signals
- Training sequences

```python
from model.dram.dfi_interface import (
    DFI5Interface, DFICommand, DFILowPowerState,
    DFITimingParameters, DFIRequestQueueConfig
)

# Create interface
dfi = DFI5Interface()
print(f"Version: {dfi.version}")
print(f"Supported commands: {[c.name for c in dfi.supported_commands]}")
print(f"Current frequency: {dfi.frequency_mhz} MHz")

# Timing parameters
timing = dfi.get_timing_parameters()
print(f"PHY write latency: {timing.tPHY_wrlAT} cycles")
print(f"PHY read latency: {timing.tPHY_rdLat} cycles")
print(f"Frequency change latency: {timing.tFC_LATENCY} cycles")

# Encode and queue commands
commands = [
    ('ACT', {'row': 100, 'bank': 0, 'channel': 0}, 8),
    ('RD', {'row': 0, 'bank': 0, 'channel': 0}, 8),
    ('WR', {'row': 0, 'bank': 1, 'channel': 0}, 12),
]

for cmd, addr_vec, priority in commands:
    dfi_req = dfi.encode_command(cmd, addr_vec, priority)
    dfi.queue_request(dfi_req)
    print(f"Queued: {cmd}")

# Dequeue and process
while dfi.pending_request_count > 0:
    req = dfi.get_next_request()
    if req:
        print(f"Processing: {req.command.name} bank={req.bank} ch={req.channel}")

# Control update handshake
dfi.request_ctrlupd()
for cycle in range(10):
    dfi.tick()
    if dfi.ctrlupd_ack:
        print(f"Acknowledged at cycle {cycle + 1}")
        break

# Frequency change protocol
dfi.request_freq_change(1200)
dfi.enter_freq_change()

for cycle in range(50):
    dfi.tick()
    if dfi.is_freq_change_complete():
        print(f"Complete at cycle {cycle + 1}, frequency: {dfi.frequency_mhz} MHz")
        break

# Low power state management
dfi.request_low_power(DFILowPowerState.LP_CTRL)
for cycle in range(10):
    dfi.tick()
    if dfi.lp_ack:
        print(f"LP_CTRL acknowledged at cycle {cycle + 1}")
        break

# Wakeup
dfi.dfi_wakeup()
for cycle in range(10):
    dfi.tick()
    if dfi.lp_state == DFILowPowerState.LP_IDLE:
        print(f"Back to LP_IDLE at cycle {cycle + 1}")
        break

# Power management
dfi.set_pwr_up_done(True)
dfi.request_pwr_down()

# Training sequence
dfi.start_training()
for cycle in range(100):
    dfi.tick()
dfi.complete_training()

# Get statistics
stats = dfi.get_statistics()
print(f"Commands sent: {stats['commands_sent']}")
print(f"Frequency changes: {stats['freq_changes']}")
print(f"LP transitions: {stats['lp_transitions']}")
```

**Run**: `python examples/dfi_interface.py`

---

## Example 6: Bandwidth Benchmarking

**File**: `examples/bandwidth_benchmark.py`

Demonstrates bandwidth measurement in HBM4:
- Sequential access pattern (optimal row hit rate)
- Random access pattern (worst case)
- Mixed access patterns
- Different channel configurations
- Speed grade comparisons

```python
from model.dram.hbm4_spec import HBM4Spec, HBM4_SPEED_GRADES
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

# Show speed grades
print("\nHBM4 Speed Grades:")
print("Speed Grade | Data Rate | Peak BW | tCK")
for grade, (rate, bw, tck) in HBM4_SPEED_GRADES.items():
    print(f"{grade:11s} | {rate:8.1f} GT/s | {bw:7.0f} GB/s | {tck:4.0f} ps")

# Create controller
controller = HBM4Controller()
spec = controller.spec
decoder = HBM4AddressDecoder()

def run_sequential_access(controller, base_addr, num_requests):
    """Sequential access (same row, different columns)"""
    addr = base_addr
    for i in range(num_requests):
        controller.submit_request(addr=addr, is_read=True)
        addr += 64  # 64-byte column increment

    start_time = controller.current_time_ns
    while len(controller._pending_requests) > 0:
        controller.tick()
    end_time = controller.current_time_ns

    elapsed_us = (end_time - start_time) / 1000
    bytes_transferred = num_requests * 64
    bandwidth_gbs = bytes_transferred / elapsed_us / 1e6
    return bandwidth_gbs, elapsed_us

def run_row_hammer_access(controller, base_addr, num_requests):
    """Row hammer pattern (alternating between two rows)"""
    row_a = base_addr
    row_b = base_addr + 0x10000

    for i in range(num_requests):
        addr = row_a if (i % 2 == 0) else row_b
        controller.submit_request(addr=addr, is_read=True)

    start_time = controller.current_time_ns
    while len(controller._pending_requests) > 0:
        controller.tick()
    end_time = controller.current_time_ns

    elapsed_us = (end_time - start_time) / 1000
    bytes_transferred = num_requests * 64
    bandwidth_gbs = bytes_transferred / elapsed_us / 1e6
    return bandwidth_gbs, elapsed_us

# Sequential access benchmark
base_addr = 0x0001_0000_0000_0000
bw, time_us = run_sequential_access(controller, base_addr, 1000)
print(f"\nSequential Access: {bw:.2f} GB/s, {time_us:.2f} us")
print(f"Efficiency: {(bw / spec.bandwidth_gbs) * 100:.1f}%")

# Row hammer benchmark
controller = HBM4Controller()  # Reset
bw, time_us = run_row_hammer_access(controller, base_addr, 1000)
print(f"\nRow Hammer: {bw:.2f} GB/s, {time_us:.2f} us")
print(f"Efficiency: {(bw / spec.bandwidth_gbs) * 100:.1f}%")

# Speed grade comparison
print("\nSpeed Grade Comparison (Sequential, 500 requests):")
for grade_name in ['HBM4_8GT', 'HBM4_12GT', 'HBM4_16GT']:
    rate, expected_bw, _ = HBM4_SPEED_GRADES[grade_name]
    spec_grade = HBM4Spec(data_rate_gtps=rate)
    controller = HBM4Controller(spec=spec_grade)
    bw, _ = run_sequential_access(controller, base_addr, 500)
    efficiency = (bw / spec_grade.bandwidth_gbs) * 100
    print(f"{grade_name:12s}: {bw:10.2f} GB/s, {efficiency:9.1f}%")
```

**Run**: `python examples/bandwidth_benchmark.py`

---

## Example 7: Multi-Channel Simulation

**File**: `examples/multi_channel.py`

Demonstrates multi-channel operations in HBM4:
- 32 independent channels
- 64 pseudo-channels (2 per channel)
- Per-channel request submission
- Channel-level scheduling
- Multi-channel statistics

```python
from model.dram.hbm4_spec import HBM4Spec
from model.dram.hbm4_channel_model import HBM4ChannelArray
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.dram.dfi_interface import DFI5Interface

# Create HBM4 spec
spec = HBM4Spec()
print(f"Channels: {spec.channels}")
print(f"Pseudo-channels: {spec.pseudo_channels}")
print(f"Total banks: {spec.total_banks}")

# Create channel array model
channel_array = HBM4ChannelArray(spec=spec)
print(f"Channel array: {channel_array.num_channels} channels")

# Get channel 0
ch0 = channel_array.get_channel(0)
print(f"Channel 0 pseudo-channels: {len(ch0.pseudo_channels)}")

# Issue commands
result = ch0.issue_command('ACT', pseudo_channel=0, bank=0, row=100)
print(f"ACT result: {'Success' if result else 'Failed'}")

# Check bank state
pc0 = ch0.pseudo_channels[0]
bank0 = pc0.banks[0]
print(f"Bank 0 state: {bank0.bank.state}")

# Issue READ
ch0.issue_command('RD', pseudo_channel=0, bank=0, row=100, col=0)

# Precharge after tRAS
for _ in range(25):
    ch0.tick()
ch0.issue_command('PRE', pseudo_channel=0, bank=0, row=0)

# Address decoding across channels
decoder = HBM4AddressDecoder()
for ch in [0, 1, 8, 15, 31]:
    addr = ((ch & 0x1F) << 41) | 0x8
    decoded = decoder.decode(addr)
    print(f"Channel {ch}: Row 0x{decoded.row_id:04X}")

# DFI interface with multiple channels
dfi = DFI5Interface()
for ch in range(4):
    req = dfi.encode_command(
        'ACT',
        {'row': 100, 'bank': ch % 16, 'channel': ch, 'pseudo_channel': ch % 2},
        priority=8
    )
    dfi.queue_request(req)

print(f"Queued {dfi.pending_request_count} commands")

# Channel timing parameters
print(f"tCK: {spec.tCK} ps")
print(f"tRCD: {spec.nRCDRD} cycles")
print(f"tCL: {spec.nCL} cycles")
print(f"tRAS: {spec.nRAS} cycles")
print(f"tRP: {spec.nRP} cycles")
```

**Run**: `python examples/multi_channel.py`

---

## Example 8: DRAM Features

**File**: `examples/dram_features.py`

Demonstrates advanced HBM4 DRAM features:
- ECC/CRC error detection and correction
- Lane repair capabilities
- PHY training sequences
- Power estimation
- MBIST (Memory Built-In Self-Test)
- Loopback testing

```python
from model.dram.hbm4_spec import HBM4Spec
from model.dram.ecc_crc import ECCEngine, CRCGenerator
from model.dram.lane_repair import LaneRepairMapper
from model.dram.phy_training import PHYTrainer, PHYInitState
from model.dram.power_estimator import PowerEstimator, PowerState
from model.dram.mbist_controller import MBISTController, MBISTAlgorithm, MBISTState
from model.dram.loopback_controller import LoopbackController, LoopbackMode, LoopbackLevel

# ECC/CRC
spec = HBM4Spec()
ecc = ECCEngine(spec)
crc_gen = CRCGenerator(spec)

test_data = bytes([0xDE, 0xAD, 0xBE, 0xEF] * 16)
encoded, ecc_bits = ecc.encode(test_data)
print(f"ECC encoded: {len(encoded)} bytes + {len(ecc_bits)} ECC bits")

crc = crc_gen.calculate(test_data)
print(f"CRC: 0x{crc:08X}")

decoded_data, status = ecc.decode(encoded, ecc_bits)
print(f"ECC decode status: {status}")

# Lane repair
repair_mapper = LaneRepairMapper(spec)
print(f"Total lanes: {repair_mapper.total_lanes}")
print(f"Redundant lanes: {repair_mapper.redundant_lanes}")

success = repair_mapper.map_lane(42, 0)
print(f"Lane repair success: {success}")
print(f"Repair coverage: {repair_mapper.get_coverage():.1%}")

# PHY training
trainer = PHYTrainer(spec)
trainer.start_training('WRLvl')
for step in range(10):
    trainer.step()
trainer.complete_training()
print(f"Training state: {trainer.state.name}")

# Power estimation
power_est = PowerEstimator(spec)
power, energy = power_est.measure_power()
print(f"Idle power: {power:.2f} mW")

power_est.set_state(PowerState.ACTIVE)
power, energy = power_est.measure_power()
print(f"Active power: {power:.2f} mW")

# MBIST
mbist = MBISTController(spec)
mbist.start(MBISTAlgorithm.MARCH_C)
while mbist.state != MBISTState.DONE:
    mbist.step()
print(f"MBIST passed: {mbist.passed}")
print(f"Failure count: {mbist.failure_count}")

# Loopback testing
loopback = LoopbackController(spec)
loopback.enable_loopback(LoopbackMode.DQ, LoopbackLevel.DQ)
test_pattern = 0xDEADBEEF
result = loopback.test_pattern(test_pattern)
print(f"Loopback match: {result == test_pattern}")
```

**Run**: `python examples/dram_features.py`

---

## Example 9: Logic Base Die

**File**: `examples/logic_base_die_example.py`

Demonstrates the HBM4 Logic Base Die model:
- Initialization and configuration
- Command enqueuing and processing
- DFI interface integration
- Bank state tracking
- PAM3 signal encoding
- Command buffer management
- Statistics collection

```python
from model.dram.logic_base_die import HBM4LogicBaseDie, LogicBaseDieConfig

# Default configuration
lbd = HBM4LogicBaseDie()
print(f"Channels: {lbd.config.num_channels}")
print(f"Channel width: {lbd.config.channel_width} bits")
print(f"PAM3 enabled: {lbd.config.pam3_enabled}")

# Custom configuration
custom_config = LogicBaseDieConfig(
    num_channels=16,
    pam3_enabled=True,
    ecc_enabled=True,
    command_buffer_depth=128,
    symbol_rate_gbaud=12.0,
)
lbd_custom = HBM4LogicBaseDie(config=custom_config)

# Initialize
lbd.initialize()
print(f"Initialized: {lbd.is_initialized}")

# Enqueue commands
cmd_id = lbd.enqueue_command('ACT', channel=0, address=0x1000, priority=5)
print(f"Command ID: {cmd_id}")
print(f"Buffer size: {lbd.command_buffer_size}")

# DFI interface
lbd.submit_dfi_act(channel=0, bank=0, row=0x1000)
lbd.submit_dfi_read(channel=0, bank=0, column=0x100)
print(f"DFI pending: {lbd.dfi_pending_count}")

# Bank state tracking
can_act = lbd.can_activate_bank(channel_id=0, bank_id=0)
print(f"Can activate: {can_act}")

lbd.activate_bank(channel_id=0, bank_id=0, row=0x1000)
state = lbd.get_bank_state(channel_id=0, bank_id=0)
print(f"Bank state: {state}")

# Timing waits
for _ in range(20):
    lbd.tick()

can_read = lbd.can_read_bank(channel_id=0, bank_id=0)
print(f"Can read: {can_read}")

# Statistics
stats = lbd.get_stats()
print(f"Total commands: {stats['total_commands']}")
print(f"Channels ready: {stats['channels_ready']}/{stats['channels_total']}")
```

**Run**: `python examples/logic_base_die_example.py`

---

## Running All Examples

To run all examples at once:

```bash
# Run each example individually
python examples/basic_controller.py
python examples/address_decoding.py
python examples/qos_scheduling.py
python examples/refresh_scheduling.py
python examples/dfi_interface.py
python examples/bandwidth_benchmark.py
python examples/multi_channel.py
python examples/dram_features.py
python examples/logic_base_die_example.py

# Or run via pytest
pytest examples/ -v
```

## Additional Resources

- [README.md](README.md) - Complete project documentation
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes
- [tests/](tests/) - Comprehensive test suite
- [docs/](docs/) - Design documents and specifications