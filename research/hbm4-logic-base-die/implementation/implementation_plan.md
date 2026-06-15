# HBM4 Logic Base Die - Implementation Plan

Date: 2026-06-15
Status: Ready for Implementation

## Phase Overview

```
Phase A: Controller Model (Python)     ← Current Focus
Phase B: DRAM Timing Model
Phase C: PHY Integration (SystemVerilog)
```

## Phase A Implementation Tasks

### Task Group 1: Core Infrastructure (已完成 ✅)

- [x] HBM4Spec with 32-channel constants
- [x] HBM4AddressDecoder
- [x] HBM4Controller integration
- [x] 基础测试套件 (252 tests)

### Task Group 2: RAS Features (待实现)

| Task | Description | Priority | Effort |
|------|-------------|----------|--------|
| 2.1 | Lane Repair Model | CRITICAL | 3 days |
| 2.2 | ECC Encoder/Decoder | High | 2 days |
| 2.3 | CRC16/CRC15 Calculator | High | 1 day |
| 2.4 | Error Counter & Status | Medium | 1 day |

### Task Group 3: Advanced Scheduling (待优化)

| Task | Description | Priority | Effort |
|------|-------------|----------|--------|
| 3.1 | CAM-based Request Table | Medium | 3 days |
| 3.2 | FR-FCFS Scheduling | Medium | 2 days |
| 3.3 | Anti-starvation Guarantee | Medium | 1 day |

### Task Group 4: Power & Thermal (待实现)

| Task | Description | Priority | Effort |
|------|-------------|----------|--------|
| 4.1 | Per-command Energy Model | High | 2 days |
| 4.2 | PHY/TSV Energy Model | Medium | 2 days |
| 4.3 | Thermal Throttling Policy | Medium | 3 days |
| 4.4 | PDN Operating Points | Medium | 2 days |

### Task Group 5: Training & Maintenance (待实现)

| Task | Description | Priority | Effort |
|------|-------------|----------|--------|
| 5.1 | PHY Training State Machine | High | 3 days |
| 5.2 | MBIST Interface | Medium | 2 days |
| 5.3 | Loopback Test Mode | Medium | 1 day |
| 5.4 | DFI PHY Independent Mode | Medium | 2 days |

## Phase B: DRAM Timing Model

| Task | Description | Priority |
|------|-------------|----------|
| B.1 | HBM4BankStateMachine | High |
| B.2 | Channel-level timing closure | High |
| B.3 | Row-hammer mitigation timing | High |
| B.4 | Refresh timing impact | Medium |

## Phase C: SystemVerilog/UVM

| Task | Description | Priority |
|------|-------------|----------|
| C.1 | RTL Controller | High |
| C.2 | UVM Verification Environment | High |
| C.3 | PHY Interface Transactor | Medium |

## Implementation Order

```
Week 1-2: Lane Repair + ECC (CRITICAL features)
Week 3-4: Power Model + Training SM
Week 5-6: Advanced Scheduling
Week 7-8: Integration + Verification
```

## Critical Path

```
Lane Repair → ECC/CRC → Training SM → Power Model → Integration
     ↓            ↓           ↓            ↓           ↓
  RAS Layer    Data Int    PHY Abst    Thermal     Full Model
```

## Dependencies

- Lane Repair 依赖: HBM4AddressDecoder, channel state
- ECC/CRC 依赖: HBM4Request, HBM4Response
- Training SM 依赖: DFI Interface
- Power Model 依赖: timing parameters

## Test Coverage Targets

| Module | Target Coverage | Current |
|--------|----------------|---------|
| Controller | 90% | 85% |
| Address Decoder | 95% | 92% |
| QoS Scheduler | 90% | 88% |
| Refresh Scheduler | 95% | 90% |
| Lane Repair | 90% | 0% |
| ECC/CRC | 95% | 0% |

## Success Criteria

Phase A 完成条件:
- [ ] Lane Repair 模型完成并测试
- [ ] ECC/CRC 实现完成并测试
- [ ] Power Model 完成并测试
- [ ] 测试覆盖率 > 90%
- [ ] 与商业 VIP 对比验证（如果可用）