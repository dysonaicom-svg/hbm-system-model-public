# HBM Modeling Baseline

基于 Ramulator2 的 HBM3 trace-driven 内存系统建模 baseline。

## 目录结构

```
research/hbm-modeling/
├── configs/              # HBM3 YAML 配置文件
│   ├── hbm3_seq.yaml     # 顺序访问配置
│   ├── hbm3_stride.yaml  # stride 访问配置
│   └── hbm3_random_rdwr.yaml  # 随机访问配置
├── traces/               # 内存访问 traces (100K 操作/文件)
│   ├── seq_rd.trace
│   ├── stride_rd.trace
│   └── random_rdwr.trace
├── scripts/
│   ├── gen_trace.py     # trace 生成器
│   └── run_baseline.sh   # 实验运行脚本
└── results/              # 实验结果
    ├── hbm3_seq.log
    ├── hbm3_stride.log
    ├── hbm3_random_rdwr.log
    └── summary.md        # 结果汇总
```

## 快速开始

### 1. 生成 traces
```bash
python3 scripts/gen_trace.py --out traces/test.trace --pattern seq --count 100000
```

### 2. 运行实验
```bash
./scripts/run_baseline.sh
```

### 3. 查看结果
```bash
cat results/summary.md
```

## 当前结果

| 模式 | 行命中率 | 平均延迟 |
|------|----------|----------|
| Sequential | 87.5% | 30.95 cycles |
| Stride | 0.02% | 83.13 cycles |
| Random | 0.01% | 42.46 cycles |

## 技术细节

- **DRAM**: HBM3, HBM3_2Gbps timing, 2 Gbps/pin
- **组织**: 1 channel, 2 pseudochannels
- **调度**: FRFCFS
- **行策略**: OpenRowPolicy
- **前端**: SimpleO3 + RandomTranslation

## 已知问题

- HBM3 不支持 ClosedRowPolicy（缺少 rank 级别）
- 使用 preset 而非手动配置以避免密度计算问题

## 参考

- Ramulator2: `research/ramulator2/README.md`
- HBM3 Spec: `research/hbm3_spec.md`
