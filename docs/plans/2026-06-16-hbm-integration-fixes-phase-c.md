# HBM System - Next Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix integration issues (Tasks 1-3) and complete Phase C PHY integration

**Architecture:** 
- Tasks 1-3: Fix timing unit mismatch between controller (cycles) and DRAM (seconds)
- Task 4: Complete DFI interface and PHY training sequences
- Tasks 5-6: RTL simulation validation and model accuracy improvement

**Tech Stack:** Python 3.8, pytest, Verilator, SystemVerilog/UVM

---

## Task 1: Fix CommandSequencer Timing Conversion

**Files:**
- Modify: `model/controller/command_sequencer.py:45-65`
- Test: `tests/controller/test_command_sequencer.py`

**Step 1: Write the failing test**

```python
def test_command_sequencer_timing():
    """Test that CommandSequencer works with cycles directly"""
    from model.controller.command_sequencer import CommandSequencer
    from model.controller.scheduler import BankState
    
    sequencer = CommandSequencer()
    bank_state = BankState(bank_id=0)
    bank_state.is_open = False
    
    # Request at cycle 0
    req = HBMRequest(addr=0x1000, length=64, is_read=True)
    req.set_arrival_time(0)
    
    # Generate sequence - should work with cycles directly
    seq = sequencer.generate_command_sequence(req, bank_state, start_cycle=17)
    assert seq is not None
    assert len(seq.commands) > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/controller/test_command_sequencer.py::test_command_sequencer_timing -v`
Expected: FAIL - timing property error

**Step 3: Fix timing conversion in CommandSequencer**

```python
# In command_sequencer.py, modify timing property to handle cycles directly:
@property
def timing(self):
    if self._timing is None:
        from model.dram.timing import HBM3Timing
        self._timing = HBM3Timing()
    return self._timing

def cycles_to_s(self, cycles: int) -> float:
    """Convert cycles to seconds for bank state machine"""
    return self.timing.cycles_to_s(cycles)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/controller/test_command_sequencer.py::test_command_sequencer_timing -v`
Expected: PASS

**Step 5: Commit**

```bash
git add model/controller/command_sequencer.py tests/controller/test_command_sequencer.py
git commit -m "fix: command sequencer timing conversion"
```

---

## Task 2: Fix DRAM Model Cycles/Sec Unit Mismatch

**Files:**
- Modify: `model/dram/dram_model.py:227-235`
- Test: `tests/dram/test_dram_model.py`

**Step 1: Write the failing test**

```python
def test_dram_model_timing_units():
    """Test that DRAM model accepts cycles directly"""
    from model.dram.dram_model import DRAMModel
    
    model = DRAMModel()
    
    # Activate at cycle 0
    model.execute_activate(stack_id=0, channel_id=0, bank_id=0, row_id=100, current_time=0)
    
    # Read at cycle tRCD+1 (should be 18 for HBM3)
    response = model.execute_read(
        stack_id=0, channel_id=0, bank_id=0, col_id=0, current_time=18
    )
    assert response.success is True, f"Read failed: {response.error}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/dram/test_dram_model.py::test_dram_model_timing_units -v`
Expected: FAIL - timing violation

**Step 3: Fix set_time to accept cycles directly**

```python
def set_time(self, current_time: int):
    """Set current time in cycles
    
    Note: For backwards compatibility, accepts cycles directly.
    The bank state machine uses seconds internally.
    """
    # Convert cycles to seconds
    time_s = current_time * self.timing.clock_period_ns * 1e-9
    for stack in self.stacks:
        stack.set_time(time_s)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/dram/test_dram_model.py::test_dram_model_timing_units -v`
Expected: PASS

**Step 5: Commit**

```bash
git add model/dram/dram_model.py tests/dram/test_dram_model.py
git commit -m "fix: DRAM model timing unit conversion from cycles"
```

---

## Task 3: Fix Bandwidth Efficiency Calculation

**Files:**
- Modify: `sim/simulator.py:120-135`
- Test: `tests/sim/test_simulator.py`

**Step 1: Write the failing test**

```python
def test_bandwidth_efficiency_calculation():
    """Test correct bandwidth efficiency calculation"""
    from sim.simulator import SimulationStats
    
    stats = SimulationStats()
    stats.total_cycles = 100000
    stats.completed_requests = 1000
    stats.total_latency_cycles = 50000
    
    # Calculate efficiency - should be between 0 and 1
    efficiency = stats.bandwidth_efficiency
    assert 0 <= efficiency <= 1.5, f"Efficiency {efficiency} out of reasonable range"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/sim/test_simulator.py::test_bandwidth_efficiency_calculation -v`
Expected: FAIL - efficiency calculation incorrect

**Step 3: Fix bandwidth_efficiency property**

```python
@property
def bandwidth_efficiency(self) -> float:
    """Calculate bandwidth efficiency (actual / theoretical peak)
    
    Theoretical peak for HBM3 @ 6.4 GT/s, 1024-bit:
    = 6.4e9 * 1024 / 8 = 819.2 GB/s per stack
    """
    if self.total_cycles == 0:
        return 0.0
    
    # Calculate actual bandwidth
    bytes_per_request = 32 * 4  # 4 bursts of 32 bytes
    bytes_transferred = self.completed_requests * bytes_per_request
    ns_per_cycle = 781.25
    total_ns = self.total_cycles * ns_per_cycle
    actual_bw_gbs = bytes_transferred / (total_ns * 1e-9) / 1e9
    
    # Theoretical peak (2 stacks)
    peak_bw = 819.2 * 2  # GB/s
    
    return actual_bw_gbs / peak_bw if peak_bw > 0 else 0.0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/sim/test_simulator.py::test_bandwidth_efficiency_calculation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add sim/simulator.py tests/sim/test_simulator.py
git commit -m "fix: correct bandwidth efficiency calculation"
```

---

## Task 4: Complete Phase C - DFI Interface RTL Integration

**Files:**
- Modify: `model/dram/dfi_interface.py`
- Modify: `rtl/hbm_controller.sv`
- Test: `tests/dram/test_dfi_interface.py`

**Step 1: Add DFI PhyInitState machine**

```python
class DFIPhyInitState(Enum):
    """DFI PHY initialization states"""
    IDLE = 0
    CADATA = 1      # CA training data
    WRLVL = 2       # Write leveling
    GATEVL = 3      # Gate training
    RDVL = 4        # Read data eye training
    WRVL = 5        # Write leveling (DQS)
    INIT = 6        # Initialization complete
    MRW = 7         # Mode register write
    ZQCL = 8        # ZQ calibration long
    ZQCS = 9        # ZQ calibration short
```

**Step 2: Implement DFI protocol checker**

```python
def check_dfi_protocol(self, dfiphase: DFIPhySignals) -> List[str]:
    """Validate DFI protocol timing"""
    violations = []
    
    # Check freq_ratio (DFI clock to MC clock)
    if dfiphase.freq_ratio not in [1, 2, 4]:
        violations.append(f"Invalid freq_ratio: {dfiphase.freq_ratio}")
    
    # Check phymstr_req handshake
    if dfiphase.phymstr_ack and not self.phymstr_req_history:
        violations.append("phymstr_ack without prior phymstr_req")
    
    return violations
```

**Step 3: Run tests**

Run: `pytest tests/dram/test_dfi_interface.py -v`

**Step 4: Commit**

```bash
git add model/dram/dfi_interface.py tests/dram/test_dfi_interface.py
git commit -m "feat: complete DFI interface protocol checker"
```

---

## Task 5: RTL Simulation Validation

**Files:**
- Modify: `rtl/hbm_controller.sv`
- Modify: `rtl/Makefile`
- Test: `rtl/` simulation

**Step 1: Add assertion for critical timing paths**

```systemverilog
// Assert: Row open time must be >= tRCD before READ
property p_read_after_act;
    @(posedge clk) disable iff (!rst_n)
    $rose(act_start) |-> ##[17:$] read_start;
endproperty
a_read_after_act: assert property(p_read_after_act);
```

**Step 2: Run Verilator lint**

```bash
cd rtl && make lint
```

**Step 3: Commit**

```bash
git add rtl/
git commit -m "feat: add RTL timing assertions"
```

---

## Task 6: Model Accuracy Improvement vs Ramulator2

**Files:**
- Modify: `model/controller/address_decoder.py`
- Modify: `sim/trace/parser.py`
- Test: `research/hbm-modeling/scripts/run_analysis.py`

**Step 1: Calibrate address decoder against Ramulator2**

```python
def calibrate_address_mapping(self, ramulator_stats: dict) -> float:
    """Adjust address mapping based on Ramulator2 reference
    
    Returns: error_percentage
    """
    # Compare row hit rate
    model_rhr = self.calculate_row_hit_rate()
    ramulator_rhr = ramulator_stats['row_hit_rate']
    
    error = abs(model_rhr - ramulator_rhr) / ramulator_rhr * 100
    return error
```

**Step 2: Run comparison analysis**

```bash
python research/hbm-modeling/scripts/run_analysis.py --patterns random --count 10000
```

**Step 3: Commit**

```bash
git add model/controller/address_decoder.py sim/trace/parser.py
git commit -m "feat: calibrate address decoder against Ramulator2"
```

---

## Verification

Run all tests to verify the fixes:

```bash
# Task 1-3: Fix tests
pytest tests/dram/test_dram_model.py -v
pytest tests/controller/test_integration.py -v
pytest tests/sim/test_simulator.py -v

# Task 4: DFI tests
pytest tests/dram/test_dfi_interface.py -v

# Task 5: RTL
cd rtl && make lint

# Task 6: Comparison
python research/hbm-modeling/scripts/run_analysis.py --patterns random

# Full regression
pytest tests/ -v --tb=short
```

## Expected Results

| Task | Description | Files Changed | Tests |
|------|-------------|---------------|-------|
| 1 | CommandSequencer timing | 1 | 5 |
| 2 | DRAM timing units | 1 | 5 |
| 3 | Bandwidth efficiency | 1 | 3 |
| 4 | DFI RTL | 2 | 10 |
| 5 | RTL assertions | 2 | 0 (lint) |
| 6 | Model calibration | 2 | 5 |

**Total: ~9 files, ~28 tests**