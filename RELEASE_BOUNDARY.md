# HBM4 System Modeling Platform - Release Boundary

**Version**: 1.0.0
**Date**: 2026-06-16
**Purpose**: Define clear boundaries for what goes into releases vs. what stays as development-only files

---

## Release Boundary Philosophy

This document defines what is included in a distribution package (source code release, pip install, etc.) versus what is development-only content that should remain in the repository but excluded from releases.

**Core Principle**: Users need everything needed to **use**, **understand**, and **test** the HBM4 platform. Development tools, internal workflows, and research materials are excluded.

---

## INCLUDE: Files for Release

### Root-Level Essential Files
```
README.md              # Project overview and quick start
CHANGELOG.md           # Version history
LICENSE                # Apache 2.0 license
requirements.txt       # Core Python dependencies
requirements-optional.txt  # Optional dependencies (visualization, etc.)
setup.py               # Package setup script
pyproject.toml         # Modern Python packaging config
Makefile               # Build automation
MANIFEST.in            # Package file manifest
QUICKSTART.md          # Quick start guide
QUICKREF.md            # Quick reference card
EXAMPLES.md            # Examples documentation
RELEASE.md             # Release notes
```

### Core Model Code (`model/`)
```
model/__init__.py
model/multi_channel.py

model/controller/           # HBM Controller
  __init__.py
  address_decoder.py
  command_pipeline.py
  command_sequencer.py
  config.py
  controller.py
  exceptions.py
  hbm4_address_decoder.py
  hbm4_controller.py
  hbm4_qos_scheduler.py
  hbm4_refresh_scheduler.py
  qos_scheduler.py
  queue.py
  refresh_scheduler.py
  request.py
  scheduler.py

model/dram/                  # DRAM Model
  __init__.py
  bank_state_machine.py
  channel_model.py
  channel_timing.py
  dfi_interface.py
  dram_model.py
  ecc_crc.py
  hbm4_channel_model.py
  hbm4_spec.py
  lane_repair.py
  logic_base_die.py
  loopback_controller.py
  mbist_controller.py
  phy_signal.py
  phy_training.py
  power_estimator.py
  stack_model.py
  thermal_controller.py
  thermal_management.py
  thermal_model.py
  thermal_sensor.py
  timing.py

model/hbm4/                  # HBM4 Specific
  __init__.py
  phy/
    __init__.py
    tsv_phy.py
  power/
    power_estimator.py
    thermal_model.py

model/phy/                   # PHY/Channel Models
  __init__.py
  channel_model.py
  eye_analyzer.py
  ibis_model.py
  ibis_parser.py
  ibis_simulator.py
  signal_integrity.py

model/interconnect/           # Interconnect
  __init__.py
  interconnect.py

model/traffic/               # Traffic Generator
  __init__.py
  traffic_generator.py

model/rtl_verification.py    # RTL Verification Interface
```

### Simulation Infrastructure (`sim/`)
```
sim/__init__.py
sim/simulator.py
sim/unified_simulator.py
sim/benchmark.py
sim/hbm4_benchmark.py
sim/hbm4_unified_benchmarks.py
sim/hbm4_unified_simulator.py
sim/report_generator.py

sim/interconnect/
  __init__.py
  axi.py
  gem5_bridge.py
  gem5_types.py

sim/trace/
  __init__.py
  parser.py
```

### Configuration Files (`config/`)
```
config/default.yaml
config/hbm4_16gbps.yaml
config/simulation.yaml
```

### Example Scripts (`examples/`)
```
examples/__init__.py
examples/address_decoding.py
examples/bandwidth_benchmark.py
examples/basic_controller.py
examples/basic_read_write.py
examples/benchmark_example.py
examples/dfi_interface.py
examples/dram_features.py
examples/hbm4_logic_base_die_example.py
examples/logic_base_die_example.py
examples/multi_channel.py
examples/multi_channel_access.py
examples/qos_priority.py
examples/qos_scheduling.py
examples/refresh_control.py
examples/refresh_scheduling.py
```

### Utility Scripts (`scripts/`)
```
scripts/auto_compare.py
scripts/compare_rtl_model.py
scripts/coverage_collector.py
scripts/hbm4_integration_demo.py
scripts/quickstart_verify.py
scripts/run_rtl_benchmark.sh
scripts/run_comprehensive_benchmark.sh

scripts/comparison/
  compare_model_ramulator.py
  compare_rtl_model.py
```

### RTL Source Code (`rtl/`)
```
rtl/hbm_types.svh            # Type definitions
rtl/hbm_pkg.sv              # Package definitions
rtl/dram_model.sv           # DRAM model
rtl/hbm_controller.sv       # Main controller RTL
rtl/hbm_controller_tb.sv    # Testbench
rtl/hbm_controller_tb_main.cpp  # C++ testbench main
rtl/Makefile               # RTL build makefile
rtl/filelist.f             # Verilog file list
rtl/build_rtl.sh           # Build script
rtl/README.md              # RTL documentation
```

### UVM Verification (`verification/`)
```
verification/docs/
  verification_plan.md

verification/reference_model/
  __init__.py
  addr_decoder_ref.sv
  bandwidth_calc.sv
  dram_ref_model.sv
  hbm_controller_stub.sv
  timing_checker.sv

verification/uvm/
  __init__.py
  hbm4_vip_pkg.sv
  hbm_coverage.sv
  hbm_env_pkg.sv
  hbm_tb.sv
  hbm_test_pkg.sv
  Makefile
  README.md
  simple.f
  uvm.f
  uvm_stub/src/uvm.svh
  uvm_stub/src/uvm_macros.svh
  
  tests/
    hbm_bank_contention_test_pkg.sv
    hbm_boundary_test_pkg.sv
    hbm_coverage_pkg.sv
    hbm_new_tests_pkg.sv
    hbm_qos_test_pkg.sv
    hbm_refresh_test_pkg.sv
    hbm_test_pkg_list.sv
    test_bank_activation_conflict_seq.sv
    test_bank_conflict_seq.sv
    test_bank_group_conflict_seq.sv
    test_burst_pattern_seq.sv
    test_coverage_extended.sv
    test_multi_bank_round_robin_seq.sv
    test_multi_channel_seq.sv
    test_per_bank_refresh_seq.sv
    test_priority_inversion_seq.sv
    test_qos_deadline_violation_seq.sv
    test_queue_starvation_seq.sv
    test_read_seq.sv
    test_refresh_collision_seq.sv
    test_refresh_during_active_seq.sv
    test_refresh_seq.sv
    test_stress_seq.sv
    test_timing_violation_seq.sv
    test_write_seq.sv
  
  scripts/
    gen_coverage_report.py
  
  reports/
    coverage_summary.json
```

### Test Suite (`tests/`)
```
tests/__init__.py
tests/conftest.py

tests/benchmark/
tests/controller/
tests/coverage/
tests/dram/
tests/hbm4/
tests/integration/
tests/interconnect/
tests/performance/
tests/phy/
tests/regression/
tests/rtl_verification/
tests/sim/
tests/simulation/
tests/traffic/
tests/verification/
```

### Documentation (`docs/`) - User-Facing Only
```
docs/ARCHITECTURE.md
docs/API.md
docs/API_REFERENCE.md
docs/BENCHMARK_RESULTS.md
docs/PERFORMANCE_REPORT.md
docs/PROGRESS.md
docs/PROJECT_REPORT.md
docs/PROJECT_STATUS.md
docs/QUICKSTART.md
docs/RTL_INTEGRATION.md
docs/RTL_PYTHON_ALIGNMENT.md
docs/RTL_VERIFICATION.md
docs/SIGNING_CHECKLIST.md
docs/USER_GUIDE.md
docs/VERIFICATION_PLAN.md
docs/VERIFICATION_REPORT.md

docs/api/
  controller/
    README.md
    hbm4_controller.md
  dram/
    README.md
    dfi_interface.md
  phy/
    README.md
    signal_integrity.md
  sim/
    README.md
    simulator.md

docs/specs/
  hbm3_spec.md

docs/tutorials/
  advanced_features.md
  getting_started.md
  performance_tuning.md
```

### Integration (`integration/`)
```
integration/gem5/
  __init__.py
  bridge.py
  gem5_hbm4_example.py
  hbm4_config.py
  python_model_integration.py
  README.md
```

### Testbenches (`tb/`)
```
tb/hbm_controller_tb.cpp
tb/hbm_rtl_tb.sv
```

---

## EXCLUDE: Development-Only Files

### Claude Code Development Files
```
.claude/                     # Claude Code settings (local development)
.claude/settings.json
.claude/settings.local.json
.claude/settings.local.json.example
.claude/skills/             # Development skills
.claude/workflows/          # Workflow automation
.claude/mcp-servers/        # MCP server implementations
.claude/scheduled_tasks.lock
```

### CI/CD Configuration
```
.github/                    # GitHub workflows and actions
.github/workflows/
```

### Research and Reference Materials
```
research/                   # Research materials (NOT user-facing)
research/hbm4-logic-base-die/
research/hbm4-modeling/
research/ramulator2/
research/hbm3_spec.md
```

### Build Tools and External Dependencies
```
tools/                      # External build tools (zstd, nvc compiler)
tools/libzstd/
tools/nvc/
nvc_build/                  # NVC compilation output
nvc_out_of_tree/            # NVC external builds
```

### Development Documentation
```
docs/design/                # Internal design documents
  2026-06-15-hbm-system-model-design.md
  architecture/

docs/plans/                 # Implementation plans
  2026-06-15-hbm4-phase-a-implementation.md
  2026-06-15-hbm-ABCD-implementation.md
  2026-06-15-hbm-integration-fixes.md
  2026-06-16-hbm4-logic-base-die-implementation.md
  2026-06-16-hbm-integration-fixes-phase-c.md

docs/superpowers/          # Development superpowers (internal)
  plans/

docs/research/             # Research documentation
  HBM4_IMPLEMENTATION_PLAN.md
  HBM4_RESEARCH_REPORT.md
  NEW_TASKS.md
  QUICK_START_CHECKLIST.md
  SPEC_ALIGNMENT_REPORT.md

docs/planning/              # Project planning
  2026-06-16-hbm-project-roadmap.md
```

### Project Development Instructions
```
CLAUDE.md                   # AI development instructions
```

### Build Artifacts and Generated Files
```
obj_dir/                    # Verilator compilation output
*.vcd                       # Waveform files
*.fsdb                      # Signal databases
*.wlf                       # Waveform log files
sim/results/               # Simulation results
sim/build/                 # Build artifacts
benchmark_results.json     # Generated benchmark data
seq_rd_comparison.json     # Comparison results
hbm_controller.vcd         # RTL simulation waveform

rtl/logs/                   # Build logs
rtl/obj_dir/               # RTL compilation artifacts

scripts/comparison_report.json
scripts/comparison_report.md
```

### Backup and Temporary Files
```
*.bak                       # Backup files
*.tmp                       # Temporary files
tmp/
temp/
__pycache__/
*.pyc
*.pyo
*.egg-info/
```

### CI Scripts (Internal Use)
```
scripts/ci_check.sh
scripts/ci_test.sh
```

---

## Summary Statistics

| Category | Files | Status |
|----------|-------|--------|
| Core Model Code | ~75 | Included |
| Simulation | ~20 | Included |
| Examples | 16 | Included |
| Scripts | 12 | Included |
| RTL | 10 | Included |
| UVM Verification | ~35 | Included |
| Tests | 130+ | Included |
| Documentation | ~40 | Included |
| **Total Included** | **~350** | |
| | | |
| Development Files | ~3000+ | Excluded |
| Research Materials | ~3500+ | Excluded |
| Build Artifacts | ~100+ | Excluded |
| **Total Excluded** | **~6500+** | |

---

## Creating a Release

To create a clean release package:

```bash
# Clone the repository
git clone https://github.com/example/hbm-system.git
cd hbm-system

# Apply release boundary filter
git filter-branch --prune-empty --subdirectory-filter model
git filter-branch --prune-empty --subdirectory-filter sim
# ... (repeat for each included directory)

# Or use .releaseignore with your release tool
rsync -av --exclude-from=.releaseignore . /path/to/release/
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-16 | Initial release boundary definition |