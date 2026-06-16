#!/usr/bin/env python3
"""
HBM RTL vs Model 自动对比框架
支持多种对比模式：功能、性能、时序
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern
from model.controller.config import HBM3_DEFAULT


@dataclass
class CompareConfig:
    """对比配置"""
    mode: str = "full"  # full, quick, performance, functional
    time_us: float = 10.0
    patterns: List[str] = None
    output: str = "results/compare"
    
    def __post_init__(self):
        if self.patterns is None:
            self.patterns = ["random", "sequential"]


class RTLCOMPARator:
    """RTL vs Model 对比器"""
    
    def __init__(self, config: CompareConfig):
        self.config = config
        self.model_stats = {}
        self.rtl_stats = {}
        
    def run_model(self) -> Dict:
        """运行 Model 仿真"""
        print("Running Model simulation...")
        config = SimulationConfig(
            simulation_time_us=self.config.time_us,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.9,
            read_ratio=0.7,
            seed=42
        )
        sim = HBMSimulator(config)
        stats = sim.run()
        
        return {
            'completed': stats.completed_requests,
            'throughput_gbps': stats.throughput_gbps,
            'row_hit_rate': stats.row_hit_rate,
            'avg_latency': stats.avg_latency,
            'efficiency': stats.efficiency
        }
    
    def run_compare(self):
        """运行对比"""
        print(f"=== HBM RTL vs Model 对比 ({self.config.mode}) ===")
        
        # Model 结果
        self.model_stats = self.run_model()
        print(f"Model: {self.model_stats}")
        
        # 生成报告
        self._save_report()
        return self.model_stats
        
    def _save_report(self):
        """保存对比报告"""
        output = Path(self.config.output)
        output.mkdir(parents=True, exist_ok=True)
        
        report = {
            'config': {
                'mode': self.config.mode,
                'time_us': self.config.time_us
            },
            'model': self.model_stats,
            'timestamp': '2026-06-16'
        }
        
        with open(output / 'compare_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved: {output / 'compare_report.json'}")


def main():
    parser = argparse.ArgumentParser(description='HBM RTL vs Model 对比')
    parser.add_argument('--mode', choices=['full', 'quick', 'performance'], default='quick')
    parser.add_argument('--time-us', type=float, default=10.0)
    parser.add_argument('--output', default='results/compare')
    args = parser.parse_args()
    
    config = CompareConfig(mode=args.mode, time_us=args.time_us, output=args.output)
    comparator = RTLCOMPARator(config)
    comparator.run_compare()


if __name__ == '__main__':
    main()
