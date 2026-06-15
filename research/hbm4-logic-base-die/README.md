# HBM4 Logic Base Die Research

This directory is an isolated research area for HBM4 logic-base-die modeling.
It is intentionally separate from the existing HBM3/Ramulator2 baseline under
`research/hbm-modeling/`.

## Current Status

**Date:** 2026-06-15

### Implementation Status: Phase 1 Complete

| Module | File | Tests | Status |
|--------|------|-------|--------|
| HBM4Spec | model/dram/hbm4_spec.py | - | Ready |
| HBM4AddressDecoder | model/controller/hbm4_address_decoder.py | - | Ready |
| HBM4Controller | model/controller/hbm4_controller.py | - | Ready |
| HBM4QoSScheduler | model/controller/hbm4_qos_scheduler.py | - | Ready |
| HBM4RefreshScheduler | model/controller/hbm4_refresh_scheduler.py | - | Ready |
| DFI Interface | model/dram/dfi_interface.py | 34 | Ready |
| HBM4ChannelModel | model/dram/hbm4_channel_model.py | - | Ready |
| LaneRepair | model/dram/lane_repair.py | 37 | Ready |
| PowerEstimator | model/hbm4/power/power_estimator.py | 39 | Ready |
| ThermalModel | model/hbm4/power/thermal_model.py | 51 | Ready |
| TSV PHY | model/hbm4/phy/tsv_phy.py | 42 | Ready |

**Total Tests: 385 passed** (HBM4 core modules + integration)

### Integration Tests

| Test Suite | File | Tests | Status |
|------------|------|-------|--------|
| HBM4 Integration | tests/hbm4/test_integration.py | - | Ready |
| Lane Repair | tests/hbm4/test_lane_repair.py | 37 | Ready |
| DFI Interface | tests/hbm4/test_dfi_interface.py | 34 | Ready |
| TSV PHY | tests/hbm4/test_tsv_phy.py | 42 | Ready |
| Power Estimator | tests/hbm4/test_power_estimator.py | 39 | Ready |
| Thermal Model | tests/hbm4/test_thermal_model.py | 51 | Ready |
| Controller Tests | tests/controller/test_hbm4*.py | 160 | Ready |

**Quick Test Command:**
```bash
python3 -m pytest tests/hbm4/ tests/controller/test_hbm4*.py tests/dram/test_hbm4*.py tests/dram/test_dfi_interface.py -v
```

## Directory Structure

```
research/hbm4-logic-base-die/
├── README.md                    # This file
├── sources/
│   └── source_index.md         # Public source index
├── requirements/
│   └── requirements_capture.md  # Requirements capture
├── notes/
│   └── logic_base_die_modeling_notes.md  # Modeling notes
├── docs/
│   ├── architecture.md          # Architecture overview
│   ├── workload_analysis.md    # AI traffic patterns
│   └── sv_uvm_migration_plan.md # RTL/UVM migration plan
└── implementation/
    └── plan.md                 # Implementation plan
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all HBM4 tests
python -m pytest tests/hbm4/ -v

# Run controller tests
python -m pytest tests/controller/test_hbm4*.py -v

# Run DRAM model tests
python -m pytest tests/dram/test_hbm4*.py -v
```

## Key Decisions (Confirmed)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Standard baseline | JEDEC JESD270-4A | Industry standard |
| Speed bin | 8 Gb/s class | JEDEC baseline |
| Controller placement | Full controller in base die | Synopsys/Cadence reference |
| Pseudo-channels | 2 per channel | JEDEC standard |
| Channels | 32 independent | HBM4 spec |
| Language | Python first | Architecture exploration |

## Architecture Layers

1. **Layer 0: Configuration** - HBM4Spec, speed bins
2. **Layer 1: Traffic** - TrafficGenerator, address mapping
3. **Layer 2: Controller** - HBM4Controller, schedulers
4. **Layer 3: PHY** - DFI, TSV, LaneRepair
5. **Layer 4: Power/Thermal** - PowerEstimator, ThermalModel

## Next Steps

1. **Workload Analysis** - Define AI training/inference profiles ✅
2. **Integration Tests** - End-to-end system test
3. **RTL Migration** - SystemVerilog implementation (see sv_uvm_migration_plan.md)
4. **UVM Verification** - UVM testbench development

## Key Questions Addressed

| Question | Answer |
|----------|--------|
| Sustained bandwidth? | 70-85% of peak (workload-dependent) |
| Controller placement? | Full controller in base die |
| Channel grouping? | 8-channel groups recommended |
| Queue depth? | 32-64 entries per channel |
| Refresh overhead? | 2-5% bandwidth reduction |

## Workload Profiles

| Profile | Use Case | Read/Write | Row Hit Rate |
|---------|----------|------------|--------------|
| A: AI Training | Large model training | 60:40 | 45% |
| B: AI Inference | Inference serving | 90:10 | 75% |
| C: Synthetic | Stress testing | 50:50 | 25% |

## Resources

- [JEDEC HBM4 (JESD270-4A)](https://www.jedec.org/standards-documents/docs/jesd270-4a)
- [Synopsys HBM4 Controller IP](https://www.synopsys.com/designware-ip/interface-ip/hbm/hbm4-controller.html)
- [Cadence HBM4E PHY](https://www.cadence.com/en_US/home/tools/silicon-solutions/design-ip/memory-interface-and-storage-ip/hbm-phy/hbm4e.html)
- [Samsung HBM4](https://semiconductor.samsung.com/dram/hbm/hbm4)
- [SK hynix HBM4](https://news.skhynix.com/sk-hynix-completes-worlds-first-hbm4-development-and-readies-mass-production)