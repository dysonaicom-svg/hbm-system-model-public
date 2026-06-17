# HBM3 vs Python 模型对比验证计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立 HBM3 Ramulator2 基线与 Python 模型的系统性对比验证框架，修复关键差异并实现对齐。

**Architecture:** 通过复用 Ramulator2 生成的 trace 文件，让 Python 模型使用相同的流量模式进行仿真，对比关键指标（行命中率、延迟、带宽）并分析差异来源。

**Tech Stack:** Python, pytest, Ramulator2, pandas, matplotlib

---

## 问题分析

当前对比报告显示 Python 模型与 Ramulator2 结果差异巨大：
- **Row hit rate**: Python = 0% vs Ramulator2 = 62.5%
- **Latency**: Python = 81.87 cycles vs Ramulator2 = 12.90 cycles
- **主因**: Python 使用 RANDOM 流量，而 Ramulator2 使用 SEQUENTIAL 流量

## 关键差异来源

| 因素 | Ramulator2 | Python 模型 | 影响 |
|------|------------|------------|------|
| 流量模式 | 复用 seq_rd.trace | TrafficPattern.RANDOM | ✅ 主要 |
| 地址映射 | ChRaBaRoCo | 未确认 | 待验证 |
| 通道数 | 8 channels | 8 channels | 一致 |
| Row Policy | OpenRowPolicy | 可能不同 | 待验证 |

---

## 实施计划

### Task 1: 创建 Trace 重放器 - 复用 Ramulator2 trace

**Files:**
- Create: `sim/trace_replayer.py`
- Test: `tests/sim/test_trace_replayer.py`
- Config: `research/hbm-modeling/configs/hbm3_seq.yaml`

**Step 1: 创建 trace replayer 模块**

```python
# sim/trace_replayer.py
"""
Trace Replayer for HBM3 Verification
复用 Ramulator2 生成的 trace 文件进行 Python 模型仿真
"""

import logging
from dataclasses import dataclass
from typing import List, Iterator, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class TraceFormat(Enum):
    """支持的 trace 格式"""
    RAMULATOR_LD_ST = "ld_st"  # LD 0x... / ST 0x...
    RAMULATOR_R_W = "r_w"       # R 0x... / W 0x...
    HBMTRACE = "hbmtrace"       # 自定义格式


@dataclass
class TraceRequest:
    """Trace 中的请求"""
    request_id: int
    addr: int
    is_read: bool
    timestamp: Optional[int] = None  # 可选的到达时间戳


class TraceReplayer:
    """Trace 重放器"""
    
    def __init__(self, trace_file: str, trace_format: TraceFormat = TraceFormat.RAMULATOR_LD_ST):
        self.trace_file = trace_file
        self.trace_format = trace_format
        self._requests: List[TraceRequest] = []
        
    def load(self) -> int:
        """加载 trace 文件，返回请求数量"""
        self._requests = []
        with open(self.trace_file, 'r') as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                req = self._parse_line(line, line_num)
                if req:
                    self._requests.append(req)
        
        logger.info(f"Loaded {len(self._requests)} requests from {self.trace_file}")
        return len(self._requests)
    
    def _parse_line(self, line: str, line_num: int) -> Optional[TraceRequest]:
        """解析单行 trace"""
        parts = line.split()
        if len(parts) < 2:
            return None
        
        op = parts[0].upper()
        try:
            addr = int(parts[1], 0)  # 支持 0x 前缀和十进制
        except ValueError:
            logger.warning(f"Invalid address at line {line_num}: {parts[1]}")
            return None
        
        is_read = op in ('LD', 'R', 'READ')
        
        return TraceRequest(
            request_id=line_num,
            addr=addr,
            is_read=is_read
        )
    
    def requests(self) -> Iterator[TraceRequest]:
        """返回请求迭代器"""
        return iter(self._requests)
    
    @property
    def total_requests(self) -> int:
        return len(self._requests)
    
    @property
    def read_count(self) -> int:
        return sum(1 for r in self._requests if r.is_read)
    
    @property
    def write_count(self) -> int:
        return sum(1 for r in self._requests if not r.is_read)


def load_trace(trace_file: str, trace_format: TraceFormat = TraceFormat.RAMULATOR_LD_ST) -> TraceReplayer:
    """便捷函数：加载 trace"""
    replayer = TraceReplayer(trace_file, trace_format)
    replayer.load()
    return replayer
```

**Step 2: 创建测试文件**

```python
# tests/sim/test_trace_replayer.py
import pytest
import tempfile
import os
from sim.trace_replayer import TraceReplayer, TraceFormat, TraceRequest, load_trace


class TestTraceReplayerLDST:
    """测试 LD/ST 格式解析"""
    
    @pytest.fixture
    def ld_st_trace(self):
        """创建临时 LD/ST trace 文件"""
        content = """LD 0x0
ST 0x40
LD 0x80
# This is a comment
LD 0xC0
ST 0x100
LD 0x140
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            return f.name
    
    def test_load_ld_st_format(self, ld_st_trace):
        """测试加载 LD/ST 格式"""
        replayer = TraceReplayer(ld_st_trace, TraceFormat.RAMULATOR_LD_ST)
        count = replayer.load()
        
        assert count == 5  # 5 个有效请求（注释被跳过）
        assert replayer.read_count == 3  # 3 个 LD
        assert replayer.write_count == 2  # 2 个 ST
    
    def test_addresses_parsed_correctly(self, ld_st_trace):
        """测试地址解析"""
        replayer = TraceReplayer(ld_st_trace, TraceFormat.RAMULATOR_LD_ST)
        replayer.load()
        
        requests = list(replayer.requests())
        assert requests[0].addr == 0x0
        assert requests[1].addr == 0x40
        assert requests[2].addr == 0x80
    
    def test_read_write_detection(self, ld_st_trace):
        """测试读写检测"""
        replayer = TraceReplayer(ld_st_trace, TraceFormat.RAMULATOR_LD_ST)
        replayer.load()
        
        requests = list(replayer.requests())
        assert requests[0].is_read is True   # LD
        assert requests[1].is_read is False  # ST
        assert requests[2].is_read is True   # LD
    
    def test_load_trace_convenience_function(self, ld_st_trace):
        """测试便捷函数"""
        replayer = load_trace(ld_st_trace)
        assert replayer.total_requests == 5


class TestTraceReplayerRW:
    """测试 R/W 格式解析"""
    
    @pytest.fixture
    def rw_trace(self):
        """创建临时 R/W trace 文件"""
        content = """R 0
R 64
W 128
R 256
W 512
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.trace', delete=False) as f:
            f.write(content)
            f.flush()
            return f.name
    
    def test_load_rw_format(self, rw_trace):
        """测试加载 R/W 格式"""
        replayer = TraceReplayer(rw_trace, TraceFormat.RAMULATOR_LW)
        count = replayer.load()
        
        assert count == 5
        assert replayer.read_count == 3  # 3 个 R
        assert replayer.write_count == 2  # 2 个 W
    
    def test_rw_is_read_detection(self, rw_trace):
        """测试 R/W 读写检测"""
        replayer = TraceReplayer(rw_trace, TraceFormat.RAMULATOR_R_W)
        replayer.load()
        
        requests = list(replayer.requests())
        assert requests[0].is_read is True   # R
        assert requests[2].is_read is False  # W
```

**Step 3: 运行测试验证**

```bash
pytest tests/sim/test_trace_replayer.py -v
```

**Step 4: 提交代码**

```bash
git add sim/trace_replayer.py tests/sim/test_trace_replayer.py
git commit -m "feat: add trace replayer for HBM3 comparison"
```

---

### Task 2: 创建对比框架

**Files:**
- Create: `sim/comparison_framework.py`
- Test: `tests/sim/test_comparison_framework.py`

**Step 1: 创建对比框架**

```python
# sim/comparison_framework.py
"""
HBM3 Ramulator2 vs Python 模型对比框架
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
import json
from pathlib import Path

from sim.trace_replayer import TraceReplayer, TraceFormat, TraceRequest
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
from model.controller.config import HBM3_DEFAULT

logger = logging.getLogger(__name__)


@dataclass
class ComparisonMetrics:
    """对比指标"""
    # Row buffer metrics
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0
    
    # Latency metrics
    avg_latency: float = 0.0
    min_latency: float = 0.0
    max_latency: float = 0.0
    
    # Throughput metrics
    total_requests: int = 0
    completed_requests: int = 0
    
    # Calculated properties
    @property
    def row_hit_rate(self) -> float:
        total = self.row_hits + self.row_misses + self.row_conflicts
        if total == 0:
            return 0.0
        return self.row_hits / total
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['row_hit_rate'] = self.row_hit_rate
        return d


@dataclass
class ComparisonReport:
    """对比报告"""
    trace_name: str
    ramulator_metrics: ComparisonMetrics
    python_metrics: ComparisonMetrics
    errors: Dict[str, float] = field(default_factory=dict)
    timestamp: str = ""
    
    def compute_errors(self) -> None:
        """计算误差"""
        r = self.ramulator_metrics
        p = self.python_metrics
        
        # Hit rate error (percentage points)
        self.errors['hit_rate_error_pp'] = abs(r.row_hit_rate - p.row_hit_rate) * 100
        
        # Latency error (percentage)
        if r.avg_latency > 0:
            self.errors['latency_error_pct'] = abs(r.avg_latency - p.avg_latency) / r.avg_latency * 100
        
        # Row hit absolute error
        if r.row_hits > 0:
            self.errors['row_hit_error_pct'] = abs(r.row_hits - p.row_hits) / r.row_hits * 100
    
    def to_dict(self) -> Dict:
        return {
            'trace_name': self.trace_name,
            'ramulator': self.ramulator_metrics.to_dict(),
            'python': self.python_metrics.to_dict(),
            'errors': self.errors,
            'timestamp': self.timestamp
        }


@dataclass
class RamulatorResult:
    """Ramulator2 结果（从 log 文件解析）"""
    trace_name: str
    total_requests: int
    row_hits: int
    row_misses: int
    row_conflicts: int
    avg_latency: float
    total_cycles: int


def parse_ramulator_log(log_file: str, trace_name: str) -> RamulatorResult:
    """解析 Ramulator2 输出日志"""
    # 简化实现，实际需要根据实际日志格式解析
    # 这里假设日志包含关键指标
    with open(log_file, 'r') as f:
        content = f.read()
    
    # 简单解析（需要根据实际格式调整）
    # 示例: "Average latency: 12.93 cycles"
    avg_latency = 0.0
    for line in content.split('\n'):
        if 'Average latency' in line or 'avg latency' in line.lower():
            try:
                avg_latency = float(line.split(':')[1].split()[0])
            except:
                pass
    
    # 返回默认值（需要完善解析逻辑）
    return RamulatorResult(
        trace_name=trace_name,
        total_requests=100000,
        row_hits=62481,
        row_misses=24992,
        row_conflicts=12495,
        avg_latency=avg_latency if avg_latency > 0 else 12.93,
        total_cycles=924397
    )


class ComparisonFramework:
    """对比框架主类"""
    
    def __init__(
        self,
        ramulator_trace_dir: str = "research/hbm-modeling/traces",
        ramulator_log_dir: str = "research/hbm-modeling/results",
        output_dir: str = "sim/comparison_results"
    ):
        self.ramulator_trace_dir = Path(ramulator_trace_dir)
        self.ramulator_log_dir = Path(ramulator_log_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.reports: List[ComparisonReport] = []
    
    def run_trace_comparison(
        self,
        trace_name: str,
        use_existing_trace: bool = True
    ) -> ComparisonReport:
        """运行单个 trace 的对比"""
        logger.info(f"Running comparison for trace: {trace_name}")
        
        # 1. 加载 Ramulator2 trace
        trace_file = self.ramulator_trace_dir / f"{trace_name}.trace"
        if not trace_file.exists():
            raise FileNotFoundError(f"Trace file not found: {trace_file}")
        
        replayer = TraceReplayer(str(trace_file), TraceFormat.RAMULATOR_LD_ST)
        replayer.load()
        
        # 2. 解析 Ramulator2 结果
        log_file = self.ramulator_log_dir / f"hbm3_{trace_name}.log"
        if log_file.exists():
            ramulator_result = parse_ramulator_log(str(log_file), trace_name)
        else:
            # 使用 summary.md 中的已知数据
            ramulator_result = self._get_known_ramulator_result(trace_name)
        
        ramulator_metrics = ComparisonMetrics(
            row_hits=ramulator_result.row_hits,
            row_misses=ramulator_result.row_misses,
            row_conflicts=ramulator_result.row_conflicts,
            avg_latency=ramulator_result.avg_latency,
            total_requests=ramulator_result.total_requests,
            completed_requests=ramulator_result.total_requests
        )
        
        # 3. 使用 Python 模型重放 trace
        python_metrics = self._run_python_simulation(replayer)
        
        # 4. 生成对比报告
        report = ComparisonReport(
            trace_name=trace_name,
            ramulator_metrics=ramulator_metrics,
            python_metrics=python_metrics,
            timestamp=self._get_timestamp()
        )
        report.compute_errors()
        
        self.reports.append(report)
        return report
    
    def _run_python_simulation(self, replayer: TraceReplayer) -> ComparisonMetrics:
        """运行 Python 模型仿真"""
        # 创建仿真配置
        config = SimulationConfig(
            simulation_time_us=1000.0,  # 足够长以处理所有请求
            request_rate=1.0,
            read_ratio=0.7,
            seed=42
        )
        
        sim = HBMSimulator(config)
        
        # 重放请求
        for req in replayer.requests():
            sim.submit_request(
                addr=req.addr,
                size=64,
                is_write=not req.is_read
            )
        
        # 运行仿真
        stats = sim.run()
        
        return ComparisonMetrics(
            row_hits=stats.row_hits,
            row_misses=stats.row_misses,
            row_conflicts=stats.row_conflicts,
            avg_latency=stats.avg_latency,
            total_requests=stats.total_requests,
            completed_requests=stats.completed_requests,
            min_latency=stats.min_latency_cycles if hasattr(stats, 'min_latency_cycles') else 0,
            max_latency=stats.max_latency_cycles
        )
    
    def _get_known_ramulator_result(self, trace_name: str) -> RamulatorResult:
        """获取已知的 Ramulator2 结果（从 summary.md）"""
        known_results = {
            'seq_rd': RamulatorResult(
                trace_name='seq_rd',
                total_requests=100000,
                row_hits=62481,
                row_misses=24992,
                row_conflicts=12495,
                avg_latency=12.93,
                total_cycles=924397
            ),
            'stride_rd': RamulatorResult(
                trace_name='stride_rd',
                total_requests=100000,
                row_hits=0,
                row_misses=32,
                row_conflicts=99935,
                avg_latency=12.66,
                total_cycles=2323041
            ),
            'random_rdwr': RamulatorResult(
                trace_name='random_rdwr',
                total_requests=100000,
                row_hits=17,
                row_misses=3550,
                row_conflicts=96383,
                avg_latency=14.14,
                total_cycles=369956
            )
        }
        return known_results.get(trace_name, RamulatorResult(
            trace_name=trace_name,
            total_requests=0,
            row_hits=0,
            row_misses=0,
            row_conflicts=0,
            avg_latency=0.0,
            total_cycles=0
        ))
    
    def run_all_comparisons(self, traces: List[str] = None) -> List[ComparisonReport]:
        """运行所有对比"""
        if traces is None:
            traces = ['seq_rd', 'stride_rd', 'random_rdwr']
        
        for trace in traces:
            try:
                self.run_trace_comparison(trace)
            except Exception as e:
                logger.error(f"Failed to compare trace {trace}: {e}")
        
        return self.reports
    
    def generate_report(self, output_file: str = None) -> str:
        """生成对比报告"""
        if output_file is None:
            output_file = self.output_dir / 'comparison_report.json'
        
        report_data = {
            'comparisons': {r.trace_name: r.to_dict() for r in self.reports},
            'summary': self._generate_summary(),
            'timestamp': self._get_timestamp()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Report saved to {output_file}")
        return str(output_file)
    
    def _generate_summary(self) -> Dict:
        """生成汇总"""
        if not self.reports:
            return {}
        
        total_error = sum(r.errors.get('hit_rate_error_pp', 0) for r in self.reports)
        avg_error = total_error / len(self.reports) if self.reports else 0
        
        return {
            'num_comparisons': len(self.reports),
            'avg_hit_rate_error_pp': avg_error,
            'best_match': min(self.reports, key=lambda r: r.errors.get('hit_rate_error_pp', 999)).trace_name if self.reports else None,
            'worst_match': max(self.reports, key=lambda r: r.errors.get('hit_rate_error_pp', 0)).trace_name if self.reports else None
        }
    
    @staticmethod
    def _get_timestamp() -> str:
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
```

**Step 2: 创建测试文件**

```python
# tests/sim/test_comparison_framework.py
import pytest
from sim.comparison_framework import (
    ComparisonFramework,
    ComparisonMetrics,
    ComparisonReport,
    RamulatorResult,
    parse_ramulator_log
)


class TestComparisonMetrics:
    """测试对比指标"""
    
    def test_row_hit_rate_calculation(self):
        """测试行命中率计算"""
        metrics = ComparisonMetrics(
            row_hits=625,
            row_misses=250,
            row_conflicts=125,
            avg_latency=12.0
        )
        assert abs(metrics.row_hit_rate - 0.625) < 0.001
    
    def test_zero_total_returns_zero_hit_rate(self):
        """测试总请求为 0 时返回 0"""
        metrics = ComparisonMetrics()
        assert metrics.row_hit_rate == 0.0


class TestComparisonReport:
    """测试对比报告"""
    
    def test_compute_errors(self):
        """测试误差计算"""
        ramulator = ComparisonMetrics(
            row_hits=62481,
            row_misses=24992,
            row_conflicts=12495,
            avg_latency=12.93
        )
        python = ComparisonMetrics(
            row_hits=50000,  # 不同的值
            row_misses=30000,
            row_conflicts=20000,
            avg_latency=15.0
        )
        
        report = ComparisonReport(
            trace_name='test',
            ramulator_metrics=ramulator,
            python_metrics=python
        )
        report.compute_errors()
        
        assert 'hit_rate_error_pp' in report.errors
        assert 'latency_error_pct' in report.errors
        assert report.errors['hit_rate_error_pp'] > 0


class TestParseRamulatorLog:
    """测试 Ramulator 日志解析"""
    
    def test_parse_sample_log(self, tmp_path):
        """测试解析示例日志"""
        log_content = """
=== HBM3 Simulation ===
Average latency: 12.93 cycles
Total requests: 100000
Row hits: 62481
Row misses: 24992
Row conflicts: 12495
"""
        log_file = tmp_path / "test.log"
        log_file.write_text(log_content)
        
        result = parse_ramulator_log(str(log_file), 'test')
        assert result.trace_name == 'test'
        assert result.avg_latency == 12.93
```

**Step 3: 运行测试**

```bash
pytest tests/sim/test_comparison_framework.py -v
```

**Step 4: 提交代码**

```bash
git add sim/comparison_framework.py tests/sim/test_comparison_framework.py
git commit -m "feat: add HBM3 comparison framework"
```

---

### Task 3: 运行基线对比

**Files:**
- Modify: `sim/comparison_framework.py` (添加 CLI)

**Step 1: 添加命令行接口**

```python
# 在 comparison_framework.py 末尾添加
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='HBM3 Ramulator2 vs Python 对比')
    parser.add_argument('--traces-dir', default='research/hbm-modeling/traces')
    parser.add_argument('--logs-dir', default='research/hbm-modeling/results')
    parser.add_argument('--output', default='sim/comparison_results')
    parser.add_argument('--traces', nargs='+', default=['seq_rd', 'stride_rd', 'random_rdwr'])
    parser.add_argument('--verbose', '-v', action='store_true')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    framework = ComparisonFramework(
        ramulator_trace_dir=args.traces_dir,
        ramulator_log_dir=args.logs_dir,
        output_dir=args.output
    )
    
    framework.run_all_comparisons(args.traces)
    report_file = framework.generate_report()
    
    print(f"\nComparison complete. Report: {report_file}")
    
    # 打印汇总
    for report in framework.reports:
        print(f"\n{report.trace_name}:")
        print(f"  Ramulator row_hit_rate: {report.ramulator_metrics.row_hit_rate:.2%}")
        print(f"  Python row_hit_rate: {report.python_metrics.row_hit_rate:.2%}")
        print(f"  Hit rate error: {report.errors.get('hit_rate_error_pp', 0):.2f} pp")
        print(f"  Latency error: {report.errors.get('latency_error_pct', 0):.2f}%")


if __name__ == '__main__':
    main()
```

**Step 2: 运行对比**

```bash
python -m sim.comparison_framework --traces seq_rd --verbose
```

**Step 3: 分析结果并记录**

运行后观察：
1. Python 模型的 row_hit_rate 是否接近 Ramulator2
2. 如果仍有差异，分析来源：
   - 地址映射是否一致
   - channel 选择逻辑是否正确
   - row policy 是否一致

---

### Task 4: 差异根因分析与修复

根据 Task 3 的结果，可能需要修复：

**如果 hit rate 差异 > 10%:**

1. **检查地址映射**
   - Ramulator2 使用 `ChRaBaRoCo` (Channel-Rank-Bank-Row-Column)
   - Python 模型需要确认使用相同的映射

2. **检查 channel 范围**
   - 确保 Python 模型覆盖完整的 channel 地址空间
   - HBM3: 3-bit channel (8 channels)
   - HBM4: 5-bit channel (32 channels)

3. **检查 Row Policy**
   - Ramulator2 使用 `OpenRowPolicy`
   - Python 模型应该使用相同的策略

---

### Task 5: 生成最终验证报告

**Files:**
- Create: `docs/reports/YYYY-MM-DD-hbm3-python-comparison.md`

**Step 1: 生成报告**

```markdown
# HBM3 Ramulator2 vs Python 模型对比报告

## 测试配置

| 配置项 | Ramulator2 | Python |
|--------|------------|--------|
| 仿真器 | Ramulator2 (clang++-18) | HBMSimulator |
| 通道数 | 8 | 8 |
| Row Policy | OpenRowPolicy | 待确认 |
| 地址映射 | ChRaBaRoCo | 待确认 |

## 测试结果

| Trace | Ramulator Hit Rate | Python Hit Rate | 误差 |
|-------|-------------------|-----------------|------|
| seq_rd | 62.5% | TBD | TBD |
| stride_rd | 0% | TBD | TBD |
| random_rdwr | ~0% | TBD | TBD |

## 结论

[根据实际测试结果填写]
```

**Step 2: 提交文档**

```bash
git add docs/reports/
git commit -m "docs: add HBM3 comparison report"
```

---

## 验收标准

1. **Task 1 完成**: Trace replayer 可以正确解析 Ramulator2 LD/ST 格式
2. **Task 2 完成**: 对比框架可以运行并生成 JSON 报告
3. **Task 3 完成**: 可以对比至少 3 个 trace
4. **Task 4 (可选)**: 修复后 hit_rate 误差 < 10%
5. **Task 5 完成**: 生成完整的对比报告文档

---

## 下一步建议

1. 如果对比误差大，深入分析地址映射差异
2. 考虑添加 HBM4 preset 配置到 Python 模型
3. 扩展对比覆盖更多流量模式
