# DRAM Timing Analysis

## HBM3 关键时序参数

### 基础参数
| 参数 | 含义 | HBM3_2Gbps 值 |
|------|------|---------------|
| tCK | 时钟周期 | 1000 ps (2 Gbps) |
| nCL | CAS 延迟 | 7 cycles |
| nRCDRD | RAS to CAS | 7 cycles |
| nRP | 行预充电 | 7 cycles |
| nRAS | 行访问 | 17 cycles |
| nRC | 行周期 | 19 cycles |

### 数据传输
| 参数 | 含义 | 值 |
|------|------|-----|
| nBL | 突发长度 | 4 |
| nCWL | 写 CAS 延迟 | 2 |
| nCCD | CAS to CAS | 1 cycle |

### 刷新和功耗
| 参数 | 含义 | 值 |
|------|------|-----|
| nRFC | 刷新命令间隔 | 160 cycles |
| nREFI | 刷新间隔 | 3900 cycles |
| nRRD | 行到行延迟 | 3 cycles |
| nFAW | 四个激活窗口 | 15 cycles |

## 延迟计算

### 读延迟
```
tRCDRD + tCL + tRP + tRAS = 7 + 7 + 7 + 17 = 38 cycles
```

### 写延迟
```
tCWL + tWP + tRAS = 2 + 8 + 17 = 27 cycles
```

### 行命中 vs 行缺失
- **行命中**: ACT + RD = 1 + 4 = 5 cycles
- **行缺失**: ACT + RD + PRE + ACT = 1 + 4 + 7 + 1 = 13 cycles

## 带宽计算

### 峰值带宽 (单通道)
```
BW = Rate × Channel_Width / 8
   = 2 Gbps × 128 bit / 8
   = 32 GB/s per pseudochannel
```

### 有效带宽
```
实际带宽 = 峰值带宽 × 命中率 × 利用率
```

## 行缓冲行为

### Row Buffer Hit Rate
```yaml
row_hits / (row_hits + row_misses + row_conflicts)
```

### 影响因素
1. **访问模式**:
   - Sequential: 高命中率 (>90%)
   - Strided: 中等命中率
   - Random: 低命中率 (<10%)

2. **Row Policy**:
   - ClosedRowPolicy: 访问后关闭行
   - OpenRowPolicy: 保持行打开
   - AutoPrecharge: 自动预充电

### 优化建议
| 模式 | 策略 | 预期效果 |
|------|------|----------|
| Sequential | OpenRowPolicy | +30% 带宽 |
| Random | ClosedRowPolicy | -10% 带宽，但减少冲突 |
| Mixed | ClosedRowPolicy + larger queue | 平衡 |

## 队列分析

### 队列长度指标
- `read_queue_len_avg_0`: 平均读队列长度
- `write_queue_len_0`: 写队列长度
- `priority_queue_len_0`: 优先级队列长度

### 队列饱和
```yaml
queue_utilization = queue_len / queue_capacity
```
- < 50%: 正常
- 50-80%: 中等拥塞
- > 80%: 严重拥塞，需要优化

## HBM3 vs 其他 DRAM

| 指标 | DDR4-2400 | HBM2 | HBM3 |
|------|-----------|------|------|
| 峰值带宽/通道 | 19.2 GB/s | 32 GB/s | 32 GB/s |
| 功耗 | 更高 | 中等 | 最低 |
| 行命中延迟 | 较高 | 低 | 最低 |
| 刷新开销 | 高 | 中等 | 低 |

## 性能优化方向

### 1. 访问模式优化
- 批量顺序访问
- 避免跨行随机访问
- 利用软件预取

### 2. 地址映射优化
- Row → Bank → Rank → Channel 映射
- 减少行冲突
- 增加 bank 并行度

### 3. 控制器优化
- FRFCFS 调度
- 写屏障管理
- 刷新策略调优
