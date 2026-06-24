# HBM4 测试文档

> HBM 系统仿真平台测试指南

*版本: 2.2.0 | 更新日期: 2026-06-24*

---

## 目录

1. [测试概述](#1-测试概述)
2. [测试环境配置](#2-测试环境配置)
3. [测试执行指南](#3-测试执行指南)
4. [测试类别详解](#4-测试类别详解)
5. [测试文件参考](#5-测试文件参考)
6. [测试数据生成](#6-测试数据生成)
7. [覆盖率报告](#7-覆盖率报告)
8. [CI/CD 集成](#8-cicd-集成)
9. [常见问题排查](#9-常见问题排查)

---

## 1. 测试概述

### 1.1 测试统计

| 指标 | 数值 |
|------|------|
| 测试文件总数 | 153 |
| 测试用例总数 | 4,409+ |
| 代码覆盖率 | 持续提升中 |

### 1.2 测试覆盖范围

```
HBM4 测试平台
├── Controller Tests (360+)      - HBM4 控制器核心功能测试
├── DRAM Tests (1009+)          - DRAM 模型和时序测试
├── HBM4 Tests (650+)           - HBM4 特定功能测试
├── Integration Tests (827+)     - 模块集成测试
├── Simulation Tests (190+)      - 仿真器功能测试
├── Coverage Tests (362+)       - 代码覆盖率测试
├── Performance Tests (61+)      - 性能基准测试
├── Benchmark Tests (184+)       - 基准测试套件
├── Verification Tests (62+)     - 验证测试
├── RTL Verification (146+)      - RTL 协同仿真测试
├── Traffic Tests (117+)         - 流量生成测试
├── Interconnect Tests (129+)    - 互联测试
└── PHY Tests (178+)             - PHY 层测试
```

### 1.3 测试架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Test Framework                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              conftest.py (共享 Fixtures)             │   │
│  │  - HBM4 Specification Fixtures                       │   │
│  │  - Controller Fixtures                               │   │
│  │  - DRAM Model Fixtures                               │   │
│  │  - Channel Model Fixtures                            │   │
│  │  - Request/Response Fixtures                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐              │
│         ▼                 ▼                 ▼              │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐         │
│  │ Unit Tests │     │  Integr.  │     │   Bench.  │         │
│  │  Tests    │     │  Tests    │     │   Tests   │         │
│  └───────────┘     └───────────┘     └───────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 测试环境配置

### 2.1 环境要求

```bash
# Python 版本
Python >= 3.8

# 核心依赖
pytest >= 7.0.0
numpy >= 1.20.0
scipy >= 1.7.0
matplotlib >= 3.5.0
```

### 2.2 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/dysonaicom-svg/hbm-system-model-public.git
cd hbm-system-model-public

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装项目
pip install -e .

# 4. 验证安装
python -c "from model.controller.hbm4_controller import HBM4Controller; print('OK')"
```

### 2.3 pytest 配置

项目根目录的 `pytest.ini` 或 `pyproject.toml` 包含测试配置：

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

---

## 3. 测试执行指南

### 3.1 基本测试命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行所有测试 (静默模式)
pytest tests/ -q

# 运行测试并生成覆盖率报告
pytest tests/ --cov=model --cov=sim --cov-report=html

# 运行测试并生成 JUnit XML 报告 (CI/CD 使用)
pytest tests/ --junitxml=results.xml

# 运行测试并生成详细覆盖率
pytest tests/ --cov=model --cov-report=term-missing --cov-report=html
```

### 3.2 按类别运行测试

```bash
# Controller 测试 (360+)
pytest tests/controller/ -v

# DRAM 测试 (1009+)
pytest tests/dram/ -v

# HBM4 测试 (650+)
pytest tests/hbm4/ -v

# Integration 测试 (827+)
pytest tests/integration/ -v

# Simulation 测试 (190+)
pytest tests/sim/ -v

# Coverage 测试 (362+)
pytest tests/coverage/ -v

# Performance 测试 (61+)
pytest tests/performance/ -v

# Benchmark 测试 (184+)
pytest tests/benchmark/ -v

# Verification 测试 (62+)
pytest tests/verification/ -v

# RTL Verification 测试 (146+)
pytest tests/rtl_verification/ -v

# Traffic 测试 (117+)
pytest tests/traffic/ -v

# Interconnect 测试 (129+)
pytest tests/interconnect/ -v

# PHY 测试 (178+)
pytest tests/phy/ -v
```

### 3.3 运行特定测试文件

```bash
# 运行单个测试文件
pytest tests/controller/test_hbm4_controller.py -v

# 运行包含关键词的测试
pytest tests/ -k "test_controller" -v

# 运行包含多个关键词的测试
pytest tests/ -k "test_controller and test_qos" -v

# 排除特定测试
pytest tests/ -k "not test_slow"
```

### 3.4 调试模式

```bash
# 显示详细输出
pytest tests/controller/test_hbm4_controller.py -v -s

# 失败时停止
pytest tests/controller/test_hbm4_controller.py -x

# 失败时进入 PDB
pytest tests/controller/test_hbm4_controller.py --pdb

# 跟踪警告
pytest tests/ -W error
```

### 3.5 并行测试

```bash
# 使用 pytest-xdist 并行执行
pip install pytest-xdist
pytest tests/ -n auto

# 指定并行数
pytest tests/ -n 4

# 仅在多核机器上启用
pytest tests/ -n auto --maxprocesses 8
```

---

## 4. 测试类别详解

### 4.1 Controller Tests (360+)

**测试范围**: HBM4 控制器核心功能

```bash
pytest tests/controller/ -v
```

**测试文件**:
- `test_HBM4_controller.py` - 主控制器功能测试
- `test_HBM4_qos_scheduler.py` - QoS 调度器测试
- `test_HBM4_refresh_scheduler.py` - 刷新调度器测试
- `test_HBM4_address_decoder.py` - 地址解码器测试
- `test_hbm4_controller_command_handling.py` - 命令处理测试
- `test_hbm4_controller_error_handling.py` - 错误处理测试
- `test_hbm4_queue_operations.py` - 队列操作测试
- `test_dfi_encoder.py` - DFI 编码器测试

**测试覆盖**:
- 请求调度和优先级
- 银行冲突检测
- 刷新调度
- 地址解码
- 命令生成
- 错误处理和恢复

### 4.2 DRAM Tests (1009+)

**测试范围**: DRAM 模型和时序

```bash
pytest tests/dram/ -v
```

**测试覆盖**:
- HBM4 规格验证
- 通道模型
- 银行状态机
- 时序约束
- DFI 接口
- ECC/CRC 计算

### 4.3 HBM4 Tests (650+)

**测试范围**: HBM4 特定功能

```bash
pytest tests/hbm4/ -v
```

**测试覆盖**:
- Pseudo-channel 支持
- Bank group 组织
- 通道间调度
- 功耗管理
- 错误检测和纠正

### 4.4 Integration Tests (827+)

**测试范围**: 模块集成

```bash
pytest tests/integration/ -v
```

**测试覆盖**:
- 控制器-DRAM 集成
- 多通道协调
- 端到端事务处理
- 系统级验证

### 4.5 Simulation Tests (190+)

**测试范围**: 仿真器功能

```bash
pytest tests/sim/ -v
```

**测试文件**:
- `test_simulator.py` - 仿真器核心测试
- `test_trace_replayer.py` - Trace 回放测试
- `test_trace_parser.py` - Trace 解析器测试
- `test_benchmark.py` - 基准测试
- `test_comparison_framework.py` - 对比框架测试

### 4.6 Coverage Tests (362+)

**测试范围**: 代码覆盖率

```bash
pytest tests/coverage/ -v
```

**测试覆盖**:
- 地址解码覆盖率
- QoS 调度覆盖率
- 功耗估算覆盖率
- 时序边界覆盖率

### 4.7 Performance Tests (61+)

**测试范围**: 性能基准

```bash
pytest tests/performance/ -v
```

**性能指标**:
- 带宽测试
- 延迟测试
- 吞吐量测试
- 效率测试

### 4.8 Benchmark Tests (184+)

**测试范围**: 基准测试套件

```bash
pytest tests/benchmark/ -v
```

**测试模式**:
- Sequential 访问
- Random 访问
- Stride 访问
- Hotspot 访问

---

## 5. 测试文件参考

### 5.1 共享 Fixtures (conftest.py)

项目使用集中式的 `conftest.py` 提供共享 fixtures:

```python
# HBM4 规格 Fixtures
@pytest.fixture
def hbm4_spec() -> HBM4Spec:
    """默认 HBM4 规格"""
    return HBM4Spec()

@pytest.fixture
def hbm4_spec_8gbps() -> HBM4Spec:
    """8 Gbps 速度等级"""
    return create_hbm4_spec_from_speed_grade("8Gbps")

@pytest.fixture
def hbm4_spec_12gbps() -> HBM4Spec:
    """12 Gbps 速度等级"""
    return create_hbm4_spec_from_speed_grade("12Gbps")

@pytest.fixture
def hbm4_spec_16gbps() -> HBM4Spec:
    """16 Gbps 速度等级"""
    return create_hbm4_spec_from_speed_grade("16Gbps")

# 控制器 Fixtures
@pytest.fixture
def hbm4_controller(hbm4_spec) -> HBM4Controller:
    """默认 HBM4 控制器"""
    config = HBMConfig(num_channels=hbm4_spec.channels)
    return HBM4Controller(config, hbm4_spec)

# 通道模型 Fixtures
@pytest.fixture
def hbm4_channel(hbm4_spec) -> HBM4Channel:
    """默认 HBM4 通道"""
    return HBM4Channel(channel_id=0, spec=hbm4_spec)

# 请求/响应 Fixtures
@pytest.fixture
def sample_read_request() -> HBMRequest:
    """示例读请求"""
    return HBMRequest(
        request_id=0,
        addr=0x1000,
        size=64,
        is_write=False,
        priority=1
    )
```

### 5.2 测试数据生成

项目使用 `tests/data_generators.py` 生成测试数据:

```python
from tests.data_generators import (
    generate_address_sequence,
    generate_random_addresses,
    generate_bank_conflict_sequence,
    generate_refresh_windows
)
```

### 5.3 延迟框架

`tests/latency_framework.py` 提供延迟分析框架:

```python
from tests.latency_framework import (
    LatencyAnalyzer,
    BankConflictAnalyzer,
    RowMissAnalyzer
)
```

---

## 6. 测试数据生成

### 6.1 使用数据生成器

```python
from tests.data_generators import (
    generate_address_sequence,
    generate_random_addresses,
    generate_bank_conflict_sequence
)

# 生成顺序地址序列
addresses = generate_address_sequence(
    base=0x1000,
    count=100,
    stride=64
)

# 生成随机地址
addresses = generate_random_addresses(
    count=1000,
    max_addr=0xFFFFFFFF
)
```

### 6.2 延迟分析

```python
from tests.latency_framework import LatencyAnalyzer

analyzer = LatencyAnalyzer()
analyzer.add_request(request_id=1, submit_cycle=100, complete_cycle=120)
latency = analyzer.get_average_latency()
```

---

## 7. 覆盖率报告

### 7.1 生成覆盖率报告

```bash
# 生成 HTML 覆盖率报告
pytest tests/ --cov=model --cov=sim \
    --cov-report=html \
    --cov-report=term-missing

# 查看报告
open htmlcov/index.html
```

### 7.2 模块级覆盖率

```bash
# 仅测试 model 模块
pytest tests/ --cov=model --cov-report=term-missing

# 仅测试 sim 模块
pytest tests/ --cov=sim --cov-report=term-missing

# 测试特定子模块
pytest tests/controller/ --cov=model.controller \
    --cov-report=term-missing
```

### 7.3 覆盖率阈值

```ini
[coverage:report]
precision = 2
show_missing = True
skip_covered = False
fail_under = 70
```

---

## 8. CI/CD 集成

### 8.1 GitHub Actions 配置

项目包含多个 CI/CD 工作流:

```yaml
# .github/workflows/pytest.yml
name: pytest
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --junitxml=results.xml --cov=model --cov=sim
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: results.xml
```

### 8.2 本地 CI 模拟

```bash
# 模拟完整 CI 流程
./scripts/run_ci.sh

# 仅运行测试
./scripts/run_ci.sh --tests-only

# 仅运行覆盖率
./scripts/run_ci.sh --coverage-only
```

### 8.3 测试回归

```bash
# 运行回归测试套件
pytest tests/regression/ -v

# 添加新的回归测试
# 在 tests/regression/ 目录创建 test_regression_<feature>.py
```

---

## 9. 常见问题排查

### 9.1 测试失败排查

```bash
# 1. 查看详细错误信息
pytest tests/controller/test_hbm4_controller.py -v -s

# 2. 启用调试模式
pytest tests/ --pdb

# 3. 检查特定断言
pytest tests/ -v --tb=long

# 4. 运行单个测试
pytest tests/controller/test_hbm4_controller.py::test_specific_case -v
```

### 9.2 常见错误

#### 导入错误

```python
# 错误: ImportError
# 解决: 重新安装项目
pip uninstall hbm4-platform
pip install -e .
```

#### 队列溢出

```python
# 错误: QueueOverflow
# 解决: 增加队列深度或调整节流
from model.controller.config import HBMConfig
config = HBMConfig(queue_depth=512)
```

#### 时序违规

```python
# 错误: TimingViolation
# 解决: 检查时序参数配置
from model.dram.timing import get_timing_for_speed_grade
timing = get_timing_for_speed_grade("16Gbps")
```

### 9.3 性能问题

```bash
# 1. 检查测试执行时间
pytest tests/ --durations=10

# 2. 使用性能分析
pytest tests/ --profile

# 3. 并行执行加速
pytest tests/ -n auto
```

### 9.4 内存问题

```bash
# 使用内存分析运行测试
python -m pytest tests/ --track-memory

# 检查内存泄漏
pytest tests/ -v --leak-detection
```

---

## 附录 A: 测试命令速查

```bash
# 快速测试
pytest tests/ -q                    # 静默模式
pytest tests/ -v                    # 详细模式
pytest tests/ -x                    # 失败即停

# 按模块测试
pytest tests/controller/ -v        # 控制器
pytest tests/dram/ -v               # DRAM
pytest tests/hbm4/ -v               # HBM4
pytest tests/sim/ -v                # 仿真

# 覆盖率
pytest tests/ --cov                 # 覆盖率
pytest tests/ --cov-report=html     # HTML 报告

# 并行
pytest tests/ -n auto                # 自动并行
pytest tests/ -n 4                  # 4 进程

# 调试
pytest tests/ -s                    # 显示输出
pytest tests/ --pdb                # PDB 调试
pytest tests/ -x                    # 失败即停
```

---

## 附录 B: 测试文件位置

| 测试类别 | 目录 | 文件数 |
|----------|------|--------|
| Controller | `tests/controller/` | 15+ |
| DRAM | `tests/dram/` | 20+ |
| HBM4 | `tests/hbm4/` | 15+ |
| Integration | `tests/integration/` | 15+ |
| Simulation | `tests/sim/` | 10+ |
| Coverage | `tests/coverage/` | 10+ |
| Performance | `tests/performance/` | 5+ |
| Benchmark | `tests/benchmark/` | 10+ |
| Verification | `tests/verification/` | 10+ |
| RTL Verification | `tests/rtl_verification/` | 10+ |
| Traffic | `tests/traffic/` | 10+ |
| Interconnect | `tests/interconnect/` | 10+ |
| PHY | `tests/phy/` | 10+ |

---

*文档版本: 2.2.0 | 最后更新: 2026-06-24*
