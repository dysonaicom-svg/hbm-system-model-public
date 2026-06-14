# HBM Modeling Workflow

HBM 内存系统建模的标准工作流。

## 工作流程

### 1. 环境准备
- [ ] 确认 Ramulator2 已构建: `research/ramulator2/build/ramulator2`
- [ ] 确认 C++20 编译器可用: `clang++-18`
- [ ] 确认 Python 3 可用: `python3`

### 2. Trace 生成
```bash
python3 research/hbm-modeling/scripts/gen_trace.py \
  --out research/hbm-modeling/traces/<name>.trace \
  --pattern <seq|stride|random> \
  --count 100000
```

**Trace 格式**: `bubble_count load_address` (十进制，非十六进制)

### 3. HBM3 配置
配置文件位置: `research/hbm-modeling/configs/`

关键参数:
```yaml
MemorySystem:
  DRAM:
    impl: HBM3
    org:
      channel: 1
      pseudochannel: 2
      bankgroup: 4
      bank: 4
      row: 8192
      column: 64
      dq: 128
    timing:
      preset: HBM3_2Gbps
```

### 4. 运行实验
```bash
research/hbm-modeling/scripts/run_baseline.sh
```

### 5. 结果分析
```bash
grep -E "avg_read_latency|bandwidth|row_hit" results/*.log
```

## 目录结构
```
research/hbm-modeling/
├── configs/          # YAML 配置文件
├── traces/           # 内存访问 traces
├── scripts/          # 脚本
│   ├── gen_trace.py # trace 生成器
│   └── run_baseline.sh
└── results/          # 实验结果
```

## 常见问题

| 问题 | 解决 |
|------|------|
| Trace 格式错误 | 确保是 `bubble_count address` 格式，不是 `R 0x...` |
| HBM3 密度不匹配 | bank * row * col * dq >> 20 = density |
| 工作目录问题 | 需要 cd 到 ramulator2 目录运行 |

## 参考
- HBM3 Spec: research/hbm3_spec.md
- Ramulator2 README: research/ramulator2/README.md
