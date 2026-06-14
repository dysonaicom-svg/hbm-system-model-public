# Ramulator2 Usage Guide

## 基本用法

### 运行仿真
```bash
cd research/ramulator2
./build/ramulator2 -f <config.yaml>
```

### 命令行选项
```bash
-f, --config_file    YAML 配置文件路径
-p, --param         覆盖配置参数: KEY=VALUE
-c, --config         内联 YAML 配置字符串
```

### 示例
```bash
./build/ramulator2 -f configs/hbm3_seq.yaml
./build/ramulator2 -f configs/hbm3.yaml -p MemorySystem.DRAM.org.channel=2
```

## 配置结构

### Frontend
```yaml
Frontend:
  impl: SimpleO3           # 或 BHO3
  clock_ratio: 8          # CPU:DRAM 时钟比
  num_expected_insts: 500000
  traces:
    - path/to/trace.trace
```

### MemorySystem
```yaml
MemorySystem:
  impl: GenericDRAM       # 或 BHDRAMSystem
  clock_ratio: 3

  DRAM:
    impl: HBM3           # DDR4, DDR5, HBM, HBM2, HBM3
    org:
      channel: 1
      pseudochannel: 2
      bankgroup: 4
      bank: 4
      row: 8192
      column: 64
    timing:
      preset: HBM3_2Gbps  # 或 DDR4_2400R, DDR5_3200AN

  Controller:
    impl: Generic
    Scheduler:
      impl: FRFCFS
```

## 支持的 DRAM 类型

| 类型 | impl 值 | 说明 |
|------|---------|------|
| DDR4 | DDR4 | 标准 DDR4 |
| DDR5 | DDR5-VRR | DDR5 with VRR |
| HBM | HBM | 第一代 HBM |
| HBM2 | HBM2 | 第二代 HBM |
| HBM3 | HBM3 | 第三代 HBM (当前基线) |

## 输出指标

### Frontend 指标
- `memory_access_cycles_recorded_core_0`
- `llc_read_misses`, `llc_read_access`
- `llc_write_misses`, `llc_write_access`

### MemorySystem 指标
- `total_num_read_requests`
- `total_num_write_requests`
- `memory_system_cycles`

### Controller 指标
- `avg_read_latency_0`
- `read_queue_len_avg_0`
- `row_hits_0`, `row_misses_0`
- `row_conflicts_0`

## Trace 格式

### SimpleO3 Frontend
```
bubble_count load_address [store_address]
```
- bubble_count: 指令间隔周期数
- load_address: 十进制加载地址
- store_address: 可选，十进制存储地址

### ReadWriteTrace Frontend
```
address operation
```
- address: 十六进制
- operation: `R` 或 `W`

## 编译

### 依赖
- CMake 3.14+
- C++20 编译器 (clang++-18 或 g++-12)
- yaml-cpp
- spdlog

### 构建命令
```bash
cd research/ramulator2
cmake -S . -B build -DCMAKE_CXX_COMPILER=/usr/bin/clang++-18
cmake --build build -j
```
