"""
HBM 性能回归测试
验证性能指标在合理范围内
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern


class TestPerformanceRegression:
    """性能回归测试"""
    
    @pytest.fixture
    def sim_config(self):
        return SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.9,
            read_ratio=0.7,
            seed=42
        )
    
    def test_bandwidth_above_baseline(self, sim_config):
        """带宽应高于基准线"""
        sim = HBMSimulator(sim_config)
        stats = sim.run()
        
        # 基准线: 300 GB/s (优化后应达到)
        assert stats.throughput_gbps > 300, f"Bandwidth {stats.throughput_gbps:.2f} below baseline 300 GB/s"
    
    def test_efficiency_above_baseline(self, sim_config):
        """效率应高于基准"""
        sim = HBMSimulator(sim_config)
        stats = sim.run()
        
        # 基准: 20% 效率
        assert stats.efficiency > 0.2, f"Efficiency {stats.efficiency:.2%} below 20%"
    
    def test_no_queue_overflow(self, sim_config):
        """队列不应溢出"""
        sim = HBMSimulator(sim_config)
        stats = sim.run()
        
        # 队列溢出应为 0
        assert stats.reject_count == 0, f"Queue rejected {stats.reject_count} requests"
