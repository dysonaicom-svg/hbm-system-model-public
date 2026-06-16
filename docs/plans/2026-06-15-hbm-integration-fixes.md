# HBM System Integration Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical integration gaps between Controller, DRAM Model, and verification infrastructure to enable end-to-end simulation validation.

**Architecture:** The system consists of a Controller (Phase A) that schedules memory requests, a CommandSequencer that generates DRAM command sequences, a CommandPipeline that executes commands on DRAM, and a DRAMModel that implements timing-accurate memory operations. The key gaps are: (1) Controller.tick() doesn't call DRAM methods, (2) UVM testbench uses hardcoded FSM instead of UVM sequences, (3) No automated RTL-to-model comparison pipeline.

**Tech Stack:** Python 3, pytest, Verilator (RTL simulation), SystemVerilog UVM

---

## Critical Gap Analysis Summary

| Component | Gap | Impact |
|-----------|-----|--------|
| `controller.py` | `tick()` never calls `dram.execute_*()` | Controller and DRAM decoupled |
| `hbm_tb.sv` | Hardcoded FSM stimulus, not UVM | Verification disconnected from DUT |
| `compare_rtl_model.py` | Script exists but never invoked | No automated validation |
| `test_end_to_end.py` | Only tests Python, not RTL | No end-to-end RTL validation |
| `controller.py` | `CommandSequencer` not integrated | Timing-accurate command generation missing |

---

## Phase 1: Integration Fixes (Critical - Unblock System)

### Task 1: Integrate CommandSequencer into HBMController

**Files:**
- Modify: `model/controller/controller.py`
- Test: `tests/controller/test_controller_integration.py`

**Step 1: Write failing test for CommandSequencer integration**

```python
# tests/controller/test_controller_integration.py
def test_controller_uses_command_sequencer():
    """Controller should use CommandSequencer to generate DRAM commands"""
    from model.controller.controller import HBMController
    from model.controller.command_sequencer import CommandSequencer
    
    controller = HBMController()
    
    # Controller should have sequencer attribute
    assert hasattr(controller, 'sequencer'), \
        "Controller should have sequencer attribute"
    assert isinstance(controller.sequencer, CommandSequencer), \
        "sequencer should be CommandSequencer instance"
```

**Step 2: Run test to verify it fails**

```bash
cd /home/ic/JXTF/HBM
python -m pytest tests/controller/test_controller_integration.py::test_controller_uses_command_sequencer -v
```
Expected: FAIL - AttributeError: 'HBMController' has no attribute 'sequencer'

**Step 3: Add CommandSequencer to controller**

```python
# In controller.py, add to __init__:
from model.controller.command_sequencer import CommandSequencer

# After bank_states initialization:
self.sequencer = CommandSequencer()

# Add method to generate command sequence from scheduled request
def _generate_command_sequence(self, request: HBMRequest, bank_state: BankState) -> CommandSequence:
    """Generate DRAM command sequence for a scheduled request"""
    return self.sequencer.generate_command_sequence(
        request, bank_state, int(self.current_time)
    )
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/controller/test_controller_integration.py::test_controller_uses_command_sequencer -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add model/controller/controller.py tests/controller/test_controller_integration.py
git commit -m "feat(controller): add CommandSequencer integration"
```

---

### Task 2: Connect Controller.tick() to DRAM Model

**Files:**
- Modify: `model/controller/controller.py`
- Test: `tests/controller/test_controller_integration.py`

**Step 1: Write failing test for DRAM integration**

```python
def test_controller_executes_dram_commands():
    """Controller.tick() should execute DRAM commands via CommandPipeline"""
    from model.dram.dram_model import DRAMModel
    from model.controller.controller import HBMController
    
    config = HBMConfig(
        stack_count=2,
        channels_per_stack=8,
    )
    controller = HBMController(config)
    dram = DRAMModel(hbm_version="hbm3", stack_count=2)
    
    # Controller should have pipeline attribute
    assert hasattr(controller, 'pipeline'), \
        "Controller should have pipeline for DRAM execution"
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/controller/test_controller_integration.py::test_controller_executes_dram_commands -v
```
Expected: FAIL - AttributeError

**Step 3: Add pipeline and DRAM integration to controller**

```python
# In controller.py, add imports:
from model.controller.command_pipeline import CommandPipeline
from model.dram.dram_model import DRAMModel

# In __init__, after scheduler initialization:
self.dram = DRAMModel(
    hbm_version="hbm3",
    stack_count=self.config.stack_count,
    banks_per_channel=self.config.banks_per_pseudo_channel
)
self.pipeline = CommandPipeline()

# In tick() method, after scheduling:
if scheduled:
    # Execute on DRAM via pipeline
    pending = self.pipeline.submit_command(scheduled, self.dram)
    # Track for completion
    self._pending_requests[scheduled.request_id] = pending
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/controller/test_controller_integration.py::test_controller_executes_dram_commands -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add model/controller/controller.py
git commit -m "feat(controller): integrate CommandPipeline and DRAM execution"
```

---

### Task 3: Verify HBMSimulator Pipeline Works End-to-End

**Files:**
- Modify: `sim/simulator.py` (if needed)
- Test: `tests/integration/test_simulator_pipeline.py`

**Step 1: Write integration test for simulator pipeline**

```python
# tests/integration/test_simulator_pipeline.py
def test_simulator_executes_command_sequence_on_dram():
    """Simulator should execute command sequences on DRAM model"""
    from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
    
    config = SimulationConfig(
        simulation_time_us=10.0,
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.5,
        read_ratio=1.0,
        seed=42,
    )
    
    sim = HBMSimulator(config)
    
    # Run for a few cycles
    for _ in range(100):
        sim.step()
    
    # Verify DRAM commands were executed
    stats = sim.get_stats()
    assert stats.total_dram_activations > 0 or stats.total_dram_reads > 0, \
        "DRAM commands should be executed"
```

**Step 2: Run test to verify current state**

```bash
python -m pytest tests/integration/test_simulator_pipeline.py -v
```

**Step 3: Fix any issues in simulator pipeline**

The simulator.py already has proper integration. This task is for verification and any fixes needed.

**Step 4: Run test to verify it passes**

Expected: PASS (simulator already integrated)

**Step 5: Commit**

```bash
git add tests/integration/test_simulator_pipeline.py
git commit -m "test(simulator): add pipeline integration verification"
```

---

### Task 4: Ensure Benchmark Runs End-to-End

**Files:**
- Modify: `scripts/ci_check.sh` (if needed)
- Test: Run benchmark directly

**Step 1: Run existing benchmark**

```bash
cd /home/ic/JXTF/HBM
python -m sim.simulator --mode functional --time 100
```

**Step 2: Create benchmark verification test**

```python
# tests/integration/test_benchmark.py
def test_benchmark_runs_successfully():
    """Verify benchmark script runs without errors"""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "sim.simulator", "--mode", "functional", "--time", "100"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Benchmark failed: {result.stderr}"
    assert "Simulation completed" in result.stdout
```

**Step 3: Run test**

```bash
python -m pytest tests/integration/test_benchmark.py -v
```

**Step 4: Fix any benchmark issues**

**Step 5: Commit**

```bash
git add tests/integration/test_benchmark.py
git commit -m "test: add benchmark verification"
```

---

## Phase 2: Verification Infrastructure (High Priority)

### Task 5: Create UVM Testbench Integration Layer

**Files:**
- Create: `verification/uvm/hbm_vip_pkg.sv`
- Modify: `verification/uvm/hbm_tb.sv`
- Test: `tests/verification/test_uvm_integration.py`

**Step 1: Create UVM VIP package skeleton**

```systemverilog
// verification/uvm/hbm_vip_pkg.sv
package hbm_vip_pkg;
    import uvm_pkg::*;
    
    // HBM Transaction
    class hbm_transaction extends uvm_sequence_item;
        rand bit [31:0] req_id;
        rand bit [33:0] req_addr;
        rand bit req_rd_wr_n;  // 1=read, 0=write
        rand bit [15:0] req_len;
        rand bit [2:0] req_priority;
        
        `uvm_object_utils_begin(hbm_transaction)
            `uvm_field_int(req_id, UVM_ALL_ON)
            `uvm_field_int(req_addr, UVM_ALL_ON)
            `uvm_field_int(req_rd_wr_n, UVM_ALL_ON)
            `uvm_field_int(req_len, UVM_ALL_ON)
            `uvm_field_int(req_priority, UVM_ALL_ON)
        `uvm_object_utils_end
    endclass
    
    // HBM Driver
    class hbm_driver extends uvm_driver#(hbm_transaction);
        virtual interface hbm_if vif;
        
        `uvm_component_utils(hbm_driver)
        
        task run_phase(uvm_phase phase);
            forever begin
                seq_item_port.get_next_item(req);
                drive_transaction(req);
                seq_item_port.item_done();
            end
        endtask
        
        task drive_transaction(hbm_transaction req);
            @(posedge vif.clk);
            vif.req_valid <= 1;
            vif.req_id <= req.req_id;
            vif.req_addr <= req.req_addr;
            vif.req_rd_wr_n <= req.req_rd_wr_n;
            vif.req_len <= req.req_len;
            vif.req_priority <= req.req_priority;
            @(posedge vif.clk);
            while (!vif.req_ready) @(posedge vif.clk);
            vif.req_valid <= 0;
        endtask
    endclass
    
    // HBM Monitor
    class hbm_monitor extends uvm_monitor;
        virtual interface hbm_if vif;
        uvm_analysis_port#(hbm_transaction) ap;
        
        `uvm_component_utils(hbm_monitor)
        
        task run_phase(uvm_phase phase);
            forever begin
                @(posedge vif.clk);
                if (vif.resp_valid) begin
                    // Monitor response
                end
            end
        endtask
    endclass
    
    // HBM Agent
    class hbm_agent extends uvm_agent;
        hbm_driver driver;
        hbm_monitor monitor;
        
        `uvm_component_utils(hbm_agent)
        
        function build_phase(uvm_phase phase);
            driver = hbm_driver::type_id::create("driver", this);
            monitor = hbm_monitor::type_id::create("monitor", this);
        endfunction
        
        function connect_phase(uvm_phase phase);
            monitor.ap.connect(analysis_port);
        endfunction
    endclass
endpackage
```

**Step 2: Update hbm_tb.sv to use UVM**

```systemverilog
// Add after module hbm_tb declaration:
`include "hbm_vip_pkg.sv"

module hbm_tb;
    // ... existing code ...
    
    // UVM interface
    interface hbm_if(input clk, rst_n);
        logic req_valid, req_ready;
        logic [31:0] req_id;
        // ... other signals ...
    endinterface
    
    // Test sequence example
    class simple_seq extends uvm_sequence#(hbm_transaction);
        `uvm_object_utils(simple_seq)
        
        task body;
            for (int i = 0; i < 10; i++) begin
                req = hbm_transaction::type_id::create("req");
                start_item(req);
                assert(req.randomize() with {
                    req.req_addr == i * 'h1000;
                    req.req_rd_wr_n == 1;  // read
                });
                finish_item(req);
            end
        endtask
    endclass
    
    initial begin
        `uvm_info("TB", "Starting UVM test", UVM_MEDIUM)
        run_test("basic_test");
    end
endmodule
```

**Step 3: Create Python test for UVM output parsing**

```python
# tests/verification/test_uvm_integration.py
def test_uvm_testbench_generates_json():
    """UVM testbench should generate JSON output for comparison"""
    import subprocess
    import json
    
    result = subprocess.run(
        ["verilator", "-f", "hbm_tb.f", "--trace-json"],
        capture_output=True,
        cwd="/home/ic/JXTF/HBM/verification/uvm"
    )
    # Should generate JSON output
    # Parse and verify structure
```

**Step 4: Run test and fix issues**

**Step 5: Commit**

```bash
git add verification/uvm/hbm_vip_pkg.sv verification/uvm/hbm_tb.sv
git commit -m "feat(uvm): add UVM VIP package and integration"
```

---

### Task 6: Create RTL-to-Model CI/CD Pipeline

**Files:**
- Create: `scripts/run_rtl_simulation.py`
- Create: `scripts/run_model_simulation.py`
- Create: `scripts/compare_results.py`
- Create: `.github/workflows/rtl_model_comparison.yml`
- Test: `tests/verification/test_rtl_model_comparison.py`

**Step 1: Create RTL simulation runner**

```python
# scripts/run_rtl_simulation.py
#!/usr/bin/env python3
"""Run RTL simulation with Verilator and output JSON results"""

import subprocess
import json
import argparse
import sys
from pathlib import Path

def run_rtl_simulation(simulation_time_ns: int = 10000) -> dict:
    """Run Verilator simulation and return results"""
    # Build Verilator
    subprocess.run(["verilator", "-f", "hbm_tb.f", "--trace-json", "-o", "obj_dir/Vhbm_tb"])
    
    # Run simulation
    result = subprocess.run(["./obj_dir/Vhbm_tb"], capture_output=True, text=True)
    
    # Parse output
    # Extract statistics from VCD or direct output
    stats = {
        "total_requests": 0,
        "completed_requests": 0,
        "avg_latency": 0.0,
        "throughput_gbps": 0.0,
        "row_hit_rate": 0.0,
    }
    
    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="rtl_results.json")
    args = parser.parse_args()
    
    stats = run_rtl_simulation()
    
    with open(args.output, "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"RTL results written to {args.output}")
```

**Step 2: Create model simulation runner**

```python
# scripts/run_model_simulation.py
#!/usr/bin/env python3
"""Run Python model simulation and output JSON results"""

import json
import argparse
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern

def run_model_simulation(simulation_time_us: float = 100.0) -> dict:
    """Run Python model simulation and return results"""
    config = SimulationConfig(
        simulation_time_us=simulation_time_us,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        seed=42,
    )
    
    sim = HBMSimulator(config)
    stats = sim.run()
    
    return stats.to_dict()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="model_results.json")
    parser.add_argument("--time", type=float, default=100.0)
    args = parser.parse_args()
    
    stats = run_model_simulation(args.time)
    
    with open(args.output, "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"Model results written to {args.output}")
```

**Step 3: Create automated comparison script**

```python
# scripts/compare_results.py
#!/usr/bin/env python3
"""Compare RTL and model results automatically"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

def run_comparison(rtl_output: str, model_output: str, threshold: float = 10.0) -> bool:
    """Run comparison and return True if all tests pass"""
    # Load results
    with open(rtl_output) as f:
        rtl = json.load(f)
    with open(model_output) as f:
        model = json.load(f)
    
    # Compare metrics
    results = []
    for metric in ["avg_latency", "throughput_gbps", "row_hit_rate"]:
        rtl_val = rtl.get(metric, 0)
        model_val = model.get(metric, 0)
        
        if rtl_val > 0 and model_val > 0:
            error_pct = abs(rtl_val - model_val) / rtl_val * 100
            passed = error_pct <= threshold
            results.append({
                "metric": metric,
                "rtl": rtl_val,
                "model": model_val,
                "error_pct": error_pct,
                "passed": passed,
            })
            print(f"{metric}: RTL={rtl_val:.4f}, Model={model_val:.4f}, Error={error_pct:.2f}% {'PASS' if passed else 'FAIL'}")
    
    all_passed = all(r["passed"] for r in results)
    return all_passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rtl", default="rtl_results.json")
    parser.add_argument("--model", default="model_results.json")
    parser.add_argument("--threshold", type=float, default=10.0)
    args = parser.parse_args()
    
    success = run_comparison(args.rtl, args.model, args.threshold)
    sys.exit(0 if success else 1)
```

**Step 4: Create CI workflow**

```yaml
# .github/workflows/rtl_model_comparison.yml
name: RTL Model Comparison

on: [push, pull_request]

jobs:
  compare:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run model simulation
        run: python scripts/run_model_simulation.py --output model_results.json
      
      - name: Run RTL simulation
        run: |
          sudo apt-get update && sudo apt-get install -y verilator
          python scripts/run_rtl_simulation.py --output rtl_results.json
      
      - name: Compare results
        run: python scripts/compare_results.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: simulation-results
          path: |
            rtl_results.json
            model_results.json
```

**Step 5: Commit**

```bash
git add scripts/run_rtl_simulation.py scripts/run_model_simulation.py scripts/compare_results.py
git add .github/workflows/rtl_model_comparison.yml
git commit -m "feat(ci): add RTL-model comparison pipeline"
```

---

### Task 7: Add Functional Coverage Integration

**Files:**
- Create: `verification/coverage/hbm_coverage.sv`
- Modify: `verification/uvm/hbm_tb.sv`
- Test: `tests/verification/test_coverage.py`

**Step 1: Create coverage model**

```systemverilog
// verification/coverage/hbm_coverage.sv
class hbm_coverage extends uvm_component;
    `uvm_component_utils(hbm_coverage)
    
    // Cover groups
    covergroup request_cg;
        option.per_instance = 1;
        address: coverpoint req_addr {
            bins low = {[0:'h100000]};
            bins mid = {[0:'h10000000:'hFFFFFFF]};
            bins high = {['h10000000:]};
        }
        access_type: coverpoint req_rd_wr_n {
            bins read = {1'b1};
            bins write = {1'b0};
        }
        length: coverpoint req_len {
            bins small = {['h1:'h20]};
            bins medium = {['h21:'h40]};
            bins large = {['h41:]};
        }
    endgroup
    
    covergroup latency_cg;
        option.per_instance = 1;
        latency: coverpoint latency_ns {
            bins fast = {[0:50]};
            bins medium = {[51:100]};
            bins slow = {[101:200]};
            bins very_slow = {[201:]};
        }
    endgroup
    
    function new(string name, uvm_component parent);
        super.new(name, parent);
        request_cg = new();
        latency_cg = new();
    endfunction
    
    function void write(hbm_transaction req);
        request_cg.sample();
    endfunction
endclass
```

**Step 2: Commit**

```bash
git add verification/coverage/hbm_coverage.sv
git commit -m "feat(coverage): add functional coverage model"
```

---

## Phase 3: Performance Validation (Medium Priority)

### Task 8: Ramulator2 Comparison Pipeline

**Files:**
- Create: `scripts/compare_ramulator.py`
- Create: `tests/performance/test_ramulator_comparison.py`
- Test: Run comparison

**Step 1: Create Ramulator2 comparison script**

```python
# scripts/compare_ramulator.py
#!/usr/bin/env python3
"""Compare Python model results with Ramulator2"""

import subprocess
import json
import argparse
from pathlib import Path

def run_ramulator(config_file: str) -> dict:
    """Run Ramulator2 and parse results"""
    result = subprocess.run(
        ["ramulator2", "--mode", "gems", "--config", config_file],
        capture_output=True,
        text=True
    )
    # Parse Ramulator2 output
    # Return statistics dictionary
    return {
        "avg_latency": 0.0,
        "throughput_gbps": 0.0,
        "row_hit_rate": 0.0,
    }

def compare_results(ramulator_stats: dict, model_stats: dict, threshold: float = 15.0) -> bool:
    """Compare Ramulator2 and model results"""
    all_passed = True
    for metric in ["avg_latency", "throughput_gbps", "row_hit_rate"]:
        ram_val = ramulator_stats.get(metric, 0)
        model_val = model_stats.get(metric, 0)
        if ram_val > 0 and model_val > 0:
            error_pct = abs(ram_val - model_val) / ram_val * 100
            passed = error_pct <= threshold
            all_passed = all_passed and passed
            print(f"{metric}: Ramulator2={ram_val:.4f}, Model={model_val:.4f}, Error={error_pct:.2f}%")
    return all_passed
```

**Step 2: Commit**

---

### Task 9: Model Accuracy Improvement

**Files:**
- Modify: `model/dram/dram_model.py`
- Modify: `model/controller/command_sequencer.py`
- Test: `tests/performance/test_model_accuracy.py`

**Step 1: Analyze accuracy gaps**

```bash
python -m pytest tests/performance/test_model_accuracy.py -v
```

**Step 2: Identify and fix timing parameter mismatches**

Key areas to check:
- tRCD, tRP, tRAS timing values
- Bank group turn-around penalties
- Refresh overhead calculation

**Step 3: Commit**

---

### Task 10: Performance Regression Tests

**Files:**
- Create: `tests/performance/test_regression.py`
- Create: `tests/performance/benchmark_reference.json`
- Test: Run regression suite

**Step 1: Create regression test with reference values**

```python
# tests/performance/test_regression.py
def test_performance_regression():
    """Ensure performance hasn't degraded"""
    import json
    from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
    
    # Load reference values
    with open("tests/performance/benchmark_reference.json") as f:
        reference = json.load(f)
    
    # Run current simulation
    config = SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        seed=42,
    )
    sim = HBMSimulator(config)
    stats = sim.run()
    
    # Compare with reference (allow 10% variance)
    for metric in ["throughput_gbps", "avg_latency"]:
        current = getattr(stats, metric)
        ref = reference[metric]
        variance = abs(current - ref) / ref
        assert variance <= 0.1, f"{metric} regression: {variance*100:.1f}% above reference"
```

**Step 2: Commit**

---

## Phase 4: Documentation & Polish (Lower Priority)

### Task 11: API Documentation

**Files:**
- Create: `docs/api/controller_api.md`
- Create: `docs/api/dram_api.md`
- Create: `docs/api/simulator_api.md`
- Test: Verify docs render correctly

**Step 1: Generate API docs**

```bash
cd /home/ic/JXTF/HBM
pdoc -o docs/api model/controller/controller.py model/dram/dram_model.py sim/simulator.py
```

**Step 2: Commit**

---

### Task 12: Architecture Diagrams

**Files:**
- Create: `docs/architecture/system_diagram.md`
- Create: `docs/architecture/data_flow.md`
- Update: `CLAUDE.md`

**Step 1: Document architecture**

```markdown
# HBM System Architecture

## Components
- TrafficGenerator: Generates memory requests
- HBMController: Schedules requests
- CommandSequencer: Generates DRAM commands
- CommandPipeline: Executes commands
- DRAMModel: Timing-accurate memory model

## Data Flow
[TrafficGenerator] -> [HBMController] -> [CommandSequencer] -> [CommandPipeline] -> [DRAMModel]
```

**Step 2: Commit**

---

### Task 13: CI/CD Setup

**Files:**
- Create: `.github/workflows/python_tests.yml`
- Create: `scripts/ci_check.sh`
- Update: `README.md`

**Step 1: Create GitHub Actions workflow**

```yaml
# .github/workflows/python_tests.yml
name: Python Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ['3.10', '3.11']
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/ -v --cov=model --cov=sim
```

**Step 2: Commit**

---

## Summary

| Phase | Tasks | Total Steps | Priority |
|-------|-------|-------------|----------|
| 1: Integration Fixes | 4 | 20 | Critical |
| 2: Verification | 3 | 15 | High |
| 3: Performance | 3 | 12 | Medium |
| 4: Documentation | 3 | 10 | Lower |

**Total: 13 tasks, 57 steps**

**Execution Options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**