# HBM System Modeling Platform

## Project Overview

HBM (High Bandwidth Memory) 系统仿真平台，支持芯片设计探索和验证对齐。

## Architecture

```
Traffic Generator / Trace Reader
        ↓
Interconnect (NoC / AXI)
        ↓
HBM Controller (Phase A)
        ↓
HBM DRAM Model (Phase B)
        ↓
Statistics Collector
```

## Key Phases

| Phase | Goal | Status |
|-------|------|--------|
| A | HBM Controller Model | Ready to start |
| B | DRAM Timing Model | Pending |
| C | PHY Integration | Future |

## Key Documents

- [Design Document](docs/design/2026-06-15-hbm-system-model-design.md) - 完整设计规范
- [HBM3 Spec](docs/specs/hbm3_spec.md) - HBM3 参数参考
- [Ramulator2](research/ramulator2/) - 参考模拟器

## Quick Start

```bash
# Setup
pip install -r requirements.txt

# Run basic simulation
python -m model.controller.controller --mode functional

# Run tests
pytest tests/ -v
```

## Development Model

- AI-driven development with subagent parallelization
- User reviews designs, AI implements
- Phased approach: Design → Phase A → Phase B → Phase C