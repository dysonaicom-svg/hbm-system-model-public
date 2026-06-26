# HBM4 性能调优设计文档

**日期**: 2026-06-26
**状态**: 设计阶段
**目标**: 提升带宽利用率到峰值 50%+

---

## 1. 问题分析

### 1.1 性能基准现状

| 指标 | 当前值 | 目标值 | 差距 |
|------|--------|--------|------|
| 带宽效率 | 0.01% | 50%+ | 5000x |
| 行命中率 | 0.7% | 62%+ | 88x |
| 通道利用率 | Ch0 100%, 其他 0% | 均衡分布 | 严重倾斜 |

### 1.2 根本原因

```
问题: ChannelSelector 总是返回 0
├── 原因: AdaptiveChannelSelector 选择逻辑错误
├── 影响: 所有请求路由到 Ch0，其他 31 通道闲置
└── 结果: 有效带宽 = 单通道带宽 = 64 GB/s (理论 2 TB/s 的 3%)
```

---

## 2. 解决方案设计

### 2.1 方案 A: 修复通道选择器 (推荐)

**策略**: 实现真正的轮询 + 负载均衡

```python
# 核心修复: AdaptiveChannelSelector
class AdaptiveChannelSelector:
    def select(self, request, available_channels):
        # 方案 A: 基于负载的轮询
        loads = [ch_stats[ch].pending for ch in available_channels]
        min_load_ch = available_channels[np.argmin(loads)]
        return min_load_ch

        # 方案 B: 纯轮询 (简单但有效)
        self._round_robin_idx = (self._round_robin_idx + 1) % len(available_channels)
        return available_channels[self._round_robin_idx]
```

**优点**:
- 实现简单，改动最小
- 立即解决通道倾斜问题
- 可预测的性能提升

**预期效果**:
- 32 通道均衡负载
- 带宽提升 ~32 倍 (64 GB/s → 2 TB/s)

### 2.2 方案 B: 地址感知调度

**策略**: 利用地址局部性选择通道

```python
def select_by_address(request, available_channels):
    # 高位地址位决定通道
    channel = (request.addr >> 12) % len(available_channels)
    return channel if channel in available_channels else 0
```

**优点**:
- 保持地址局部性
- 顺序访问自然分布到不同通道

**缺点**:
- 可能产生热点通道

### 2.3 方案 C: QoS 感知的动态调度

**策略**: 根据 QoS 级别和通道负载动态分配

```python
class QoSAwareChannelSelector:
    def select(self, request, available_channels):
        if request.qos >= QoSLevel.CRITICAL:
            # 关键流量: 选择负载最低通道
            return min(available_channels, key=lambda ch: ch.load)
        else:
            # 普通流量: 轮询
            return self.round_robin_select(available_channels)
```

---

## 3. 实现计划

### 3.1 Phase 1: 修复通道选择 (1-2 天)

| 任务 | 负责人 | 优先级 |
|------|--------|--------|
| 修复 AdaptiveChannelSelector | AI | P0 |
| 添加 RoundRobinChannelSelector | AI | P0 |
| 验证通道均衡分布 | 测试 | P0 |
| 运行基准测试确认提升 | 验证 | P0 |

### 3.2 Phase 2: 地址解码优化 (2-3 天)

| 任务 | 负责人 | 优先级 |
|------|--------|--------|
| 优化 Row-Rank-Bank 映射 | AI | P1 |
| 添加行缓冲区模拟 | AI | P1 |
| 提升行命中率到 50%+ | 验证 | P1 |

### 3.3 Phase 3: 命令流水线优化 (3-5 天)

| 任务 | 负责人 | 优先级 |
|------|--------|--------|
| 命令合并优化 | AI | P2 |
| Bank Group 并行调度 | AI | P2 |
| 延迟隐藏优化 | AI | P2 |

---

## 4. 验收标准

| Milestone | 指标 | 当前 | 目标 |
|-----------|------|------|------|
| M1 | 带宽效率 | 0.01% | 10% |
| M2 | 通道利用率 | 1/32 | 32/32 |
| M3 | 行命中率 | 0.7% | 50% |
| M4 | 吞吐量 | 0.16 GB/s | 100+ GB/s |

---

## 5. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 通道竞争 | 中 | 添加 bank 冲突避免 |
| 测试回归 | 高 | 完整测试套件验证 |
| 性能抖动 | 中 | 添加性能监控 |

---

## 6. 推荐实施路径

1. **立即修复**: ChannelSelector 问题 (方案 A)
2. **短期优化**: 地址解码和行缓冲
3. **中期增强**: 命令流水线优化

**预计提升**: 0.01% → 10-30% (100-3000 倍)
