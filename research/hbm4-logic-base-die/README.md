# HBM4 Logic Base Die

HBM4 Logic Base Die 是本仓库中面向 HBM4 架构探索的子项目。当前重点是建立可运行的 Python 功能/性能模型，用于验证 32-channel HBM4 组织、地址映射、QoS 调度、refresh、DFI/PHY 抽象、lane repair、功耗和热模型的系统级行为。

RTL/UVM 迁移已经启动，但仍处于修复和对齐阶段；不要把当前 RTL 当作最终可综合交付。

## Current Status

Date: 2026-06-15

| Area | Status | Notes |
|------|--------|-------|
| Python HBM4 model | Active prototype | Controller、address decoder、QoS、refresh、DFI、channel、lane repair、power、thermal、TSV PHY 已有测试覆盖 |
| System tests | Passing | Full local test suite currently has 635 tests passing |
| RTL controller | Work in progress | Verilator lint still reports latch/width/combinational-loop issues |
| UVM flow | Work in progress | Makefile and documentation are being prepared |
| Public research capture | Available | Requirements, sources, and architecture notes are tracked under this directory |

## Repository Map

```text
model/
  controller/
    hbm4_address_decoder.py      # HBM4 address decode and mapping schemes
    hbm4_controller.py           # Integrated HBM4 controller prototype
    hbm4_qos_scheduler.py        # QoS-aware request selection
    hbm4_refresh_scheduler.py    # Per-bank/all-bank refresh scheduling
  dram/
    hbm4_spec.py                 # HBM4 parameters and speed-grade helpers
    hbm4_channel_model.py        # Channel and pseudo-channel model
    dfi_interface.py             # DFI 5.x-style controller/PHY abstraction
    ecc_crc.py                   # ECC/CRC modeling
    lane_repair.py               # Lane repair and spare-lane remapping
  hbm4/
    phy/tsv_phy.py               # TSV PHY abstraction
    power/power_estimator.py     # Power estimation
    power/thermal_model.py       # Thermal model

tests/
  controller/test_hbm4*.py       # HBM4 controller/address/QoS/refresh tests
  dram/test_hbm4*.py             # HBM4 DRAM/channel/spec tests
  dram/test_dfi_interface.py     # DFI tests
  hbm4/                          # HBM4 integration, PHY, power, thermal tests

rtl/
  hbm_controller.sv              # RTL controller under active repair
  hbm_types.svh                  # SystemVerilog HBM type definitions

verification/uvm/                # UVM/Verilator verification flow

research/hbm4-logic-base-die/
  README.md                      # This file
  sources/source_index.md        # Public source index
  requirements/                  # Requirements capture
  notes/                         # Modeling notes
  docs/                          # Architecture and quick-start docs
  implementation/                # Implementation planning artifacts
```

## Quick Start

Run commands from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest tests -q
```

Run only the HBM4-focused Python tests:

```bash
python3 -m pytest \
  tests/hbm4 \
  tests/controller/test_hbm4_address_decoder.py \
  tests/controller/test_hbm4_controller.py \
  tests/controller/test_hbm4_qos_scheduler.py \
  tests/controller/test_hbm4_refresh_scheduler.py \
  tests/dram/test_hbm4_spec.py \
  tests/dram/test_hbm4_channel_model.py \
  tests/dram/test_dfi_interface.py \
  tests/dram/test_ecc_crc.py \
  tests/dram/test_lane_repair.py \
  -q
```

Check RTL lint status:

```bash
verilator --lint-only -Wall rtl/hbm_controller.sv
```

At the time of this README update, the Python tests pass but RTL lint is expected to fail until the controller RTL repair is completed.

## Core Model Concepts

| Concept | Current Model |
|---------|---------------|
| Channels | 32 HBM4 channels per stack model |
| Pseudo-channels | 2 pseudo-channels per channel |
| Interface width | 2048-bit aggregate HBM4 interface model |
| Baseline speed | 8 GT/s class parameters under review |
| Scheduling | QoS priority plus FR-FCFS-style row-hit preference |
| Refresh | Per-bank default mode with all-bank and bank-group modes available |
| PHY abstraction | DFI-style command/data/control model plus TSV PHY abstraction |
| Reliability | ECC/CRC and lane repair models |
| Power/thermal | Transaction-level power estimation and thermal trend modeling |

## Example Usage

```python
from model.controller.hbm4_controller import HBM4Controller

controller = HBM4Controller()

req_id = controller.submit_request(
    addr=0x0000_0000_0000_0000,
    is_read=True,
    qos_level=15,
    size_bytes=64,
)

for _ in range(20):
    responses = controller.tick()
    if any(resp.request_id == req_id for resp in responses):
        break

print(controller.get_stats())
```

Address decoding example:

```python
from model.controller.hbm4_address_decoder import HBM4AddressDecoder

decoder = HBM4AddressDecoder(mapping_scheme="rbc")
decoded = decoder.decode(0x0000_0200_0002_0000)

print(decoded.channel_id, decoded.pseudo_channel_id, decoded.bank_id, decoded.row_id)
```

## Validation Snapshot

Recent local checks:

```text
python3 -m pytest tests -q
635 passed

verilator --lint-only -Wall rtl/hbm_controller.sv
fails: RTL lint still reports known controller issues
```

Use the Python test suite as the current source of truth for functional model behavior. Use RTL lint failures as active repair targets.

## Known Gaps

- HBM4 address bitfield definitions still need one canonical spec shared by `HBM4Spec`, `HBM4AddressDecoder`, docs, and RTL.
- Speed-grade timing presets need a final unit audit, especially tCK values.
- Refresh response naming should distinguish physical channel, pseudo-channel, and global bank IDs.
- The SystemVerilog controller still needs lint cleanup before synthesis-oriented review.
- UVM collateral is being prepared but is not yet the primary verification path.

## Research Sources

Public-source notes are tracked under:

- `research/hbm4-logic-base-die/sources/source_index.md`
- `research/hbm4-logic-base-die/requirements/requirements_capture.md`
- `research/hbm4-logic-base-die/notes/logic_base_die_modeling_notes.md`

The project intentionally avoids reconstructing NDA-only JEDEC tables. Values not available from public sources should remain marked as assumptions or model parameters.
