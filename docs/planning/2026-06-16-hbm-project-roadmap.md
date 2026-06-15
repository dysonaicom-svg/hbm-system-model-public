# HBM 项目后续规划
**Date**: 2026-06-16
**Status**: Ready for Implementation

## 当前完成状态

### Phase A: HBM Controller (98%)
- [x] Address Decoder (6种映射模式)
- [x] QoS Scheduler (16级优先级 + 带宽保证)
- [x] Refresh Scheduler (All-bank/Per-bank/Bank-group)
- [x] Read/Write Queues
- [x] FR-FCFS Scheduler
- [x] Command Pipeline
- [x] Command Sequencer
- [ ] **待完成**: AXI4 接口完整集成

### Phase B: DRAM Timing Model (95%)
- [x] HBM4 Spec (32通道, 8/12/16Gbps)
- [x] Bank State Machine
- [x] Channel Model
- [x] Stack Model
- [x] DFI Interface
- [x] ECC/CRC
- [x] Lane Repair
- [x] Power Estimator
- [ ] **待完成**: PHY Training Model

### Phase C: PHY Integration (30%)
- [x] DFI PHY Interface
- [ ] Signal Integrity Model
- [ ] IBIS Integration (可选)
- [ ] Pre-emphasis/CTLE/DFE

## 待实现功能

### 高优先级
1. **gem5 集成**
   - 创建 gem5 HBM4 控制器模型
   - 实现内存端口接口
   - 支持 CPU/NPU/GPU traffic generators
   - 文档: research/hbm-modeling/README.md

2. **端到端集成测试**
   - Controller → DRAM → Statistics 完整链路
   - 性能回归测试
   - RTL 对齐验证

3. **性能可视化**
   - 带宽利用率图
   - 延迟分布直方图
   - 通道热力图

### 中优先级
4. **更多流量模式**
   - 矩阵乘法
   - 卷积神经网络
   - Transformer attention

5. **功耗优化分析**
   - 基于流量的功耗预测
   - 刷新策略优化

6. **时序验证增强**
   - 更多边界条件测试
   - 协议一致性测试

### 低优先级
7. **SystemC 移植**
   -  cycle-accurate SystemC 模型
   - RTL 协同仿真

8. **文档完善**
   - API 文档
   - 使用教程

## 测试覆盖目标

| 组件 | 当前覆盖率 | 目标 |
|------|----------|------|
| Address Decoder | 95% | 98% |
| Scheduler | 85% | 95% |
| DRAM Model | 90% | 95% |
| Power Model | 80% | 90% |
| DFI Interface | 75% | 90% |

## 性能基准

| 指标 | 当前 | 目标 |
|------|------|------|
| L0 (Functional) | - | > 10M req/s |
| L1 (Transaction) | - | > 1M req/s |
| L2 (Timing-approx) | - | > 100K req/s |
| L3 (Timing-accurate) | - | > 10K req/s |

## 下一步行动

### 立即行动
1. 等待当前 coverage 测试完成
2. 运行完整测试套件
3. 生成测试报告

### 本周目标
1. 完成 gem5 集成设计
2. 实现 AXI4 接口
3. 端到端集成测试

### 本月目标
1. gem5 集成完成
2. 性能可视化上线
3. 文档完善