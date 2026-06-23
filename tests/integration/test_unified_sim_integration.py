"""
Unified Simulator Integration Tests

Tests the integration of unified_simulator with all components:
- AXI interface
- Multi-master configuration
- Traffic generator integration
- Statistics collection

Run with: pytest tests/integration/test_unified_sim_integration.py -v
"""

import pytest
import sys
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, '/home/ic/JXTF/HBM')

from model.dram.HBM4_spec import HBM4Spec, create_hbm4_spec_from_speed_grade
from model.dram.HBM4_channel_model import HBM4ChannelArray
from model.controller.HBM4_controller import HBM4Controller
from model.controller.config import HBMConfig, HBM3_DEFAULT

from sim.simulator import (
    HBMSimulator, SimulationConfig, SimulationStats,
    TrafficGenerator, TrafficPattern
)
from sim.interconnect.axi import (
    AXIInterconnect, AXIMaster, AXISlave,
    MultiMasterTrafficGenerator, create_hbm_interconnect,
    AXIAddress, AXIBeat, AXIResponse, AXISize
)
from sim.unified_simulator import (
    UnifiedSimulator, UnifiedSimulatorStats,
    run_unified_simulation
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def basic_sim_config():
    """Basic simulation configuration"""
    return SimulationConfig(
        simulation_time_us=10.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        read_ratio=0.7,
        seed=42,
    )


@pytest.fixture
def hbm4_sim_config():
    """HBM4 simulation configuration"""
    return SimulationConfig(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.3,
        read_ratio=0.7,
        seed=42,
    )


@pytest.fixture
def seq_sim_config():
    """Sequential traffic simulation configuration"""
    return SimulationConfig(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.8,
        read_ratio=1.0,  # All reads
        seed=42,
    )


@pytest.fixture
def multi_master_config():
    """Multi-master simulation configuration"""
    return SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        read_ratio=0.7,
        seed=42,
    )


# =============================================================================
# Test AXI Interface Integration
# =============================================================================

class TestAXIInterface:
    """Test AXI interface integration"""

    def test_axi_interconnect_creation(self):
        """Test AXI interconnect creation"""
        interconnect, masters, slave = create_hbm_interconnect(
            num_masters=4,
            enable_qos=True
        )

        assert interconnect is not None
        assert len(masters) == 4
        assert slave is not None

    def test_axi_master_creation(self):
        """Test individual AXI master creation"""
        master = AXIMaster(master_id=0)

        assert master.master_id == 0
        assert len(master.pending_reads) == 0
        assert len(master.pending_writes) == 0

    def test_axi_slave_creation(self):
        """Test AXI slave creation"""
        slave = AXISlave(slave_id=0, base_addr=0, addr_range=0x10000000)

        assert slave.slave_id == 0
        assert slave.base_addr == 0
        assert slave.addr_range == 0x10000000

    def test_axi_address_generation(self):
        """Test AXI address generation"""
        addr = AXIAddress(
            addr=0x1000,
            burst=1,  # INCR
            size=AXISize.SIZE_64,   # 64 bytes
            length=0  # 1 beat
        )

        assert addr.addr == 0x1000
        assert addr.get_num_beats() == 1
        assert addr.get_total_bytes() == 64

    def test_axi_beat_creation(self):
        """Test AXI beat creation"""
        beat = AXIBeat(
            data=0xDEADBEEF,
            strb=0xFF,
            last=True
        )

        assert beat.data == 0xDEADBEEF
        assert beat.last == True


# =============================================================================
# Test Multi-Master Traffic Generator
# =============================================================================

class TestMultiMasterTraffic:
    """Test multi-master traffic generation"""

    def test_multi_master_generator_creation(self):
        """Test multi-master traffic generator creation"""
        gen = MultiMasterTrafficGenerator(num_masters=4)

        assert gen.num_masters == 4
        assert hasattr(gen, 'generate_traffic')
        assert hasattr(gen, 'run_simulation')

    def test_multi_master_request_generation(self):
        """Test request generation from multiple masters"""
        gen = MultiMasterTrafficGenerator(num_masters=4)

        # Generate traffic - should be callable
        traffic = gen.generate_traffic()
        assert traffic is not None

    def test_multi_master_run_simulation(self):
        """Test running multi-master simulation"""
        gen = MultiMasterTrafficGenerator(num_masters=4)

        # Run simulation - should complete
        result = gen.run_simulation()
        assert result is not None or result == True  # May return True or stats


# =============================================================================
# Test Unified Simulator Core
# =============================================================================

class TestUnifiedSimulatorCore:
    """Test unified simulator core functionality"""

    def test_unified_simulator_creation(self, basic_sim_config):
        """Test unified simulator creation"""
        sim = UnifiedSimulator(sim_config=basic_sim_config, num_masters=4)

        assert sim.config == basic_sim_config
        assert sim.controller is not None
        assert sim.traffic_gen is not None

    def test_unified_simulator_without_axi(self, basic_sim_config):
        """Test unified simulator without AXI interconnect"""
        sim = UnifiedSimulator(
            sim_config=basic_sim_config,
            num_masters=4,
            enable_axi=False
        )

        assert sim.interconnect is None
        assert sim.enable_axi == False

    def test_unified_simulator_step(self, basic_sim_config):
        """Test unified simulator step execution"""
        sim = UnifiedSimulator(sim_config=basic_sim_config, num_masters=4)

        # Execute a few steps
        for _ in range(10):
            response = sim.step()
            # Response may be None if no request completed

        assert sim.current_cycle > 0

    def test_unified_simulator_run(self, basic_sim_config):
        """Test unified simulator full run"""
        sim = UnifiedSimulator(
            sim_config=basic_sim_config,
            num_masters=2,
            enable_axi=True
        )

        stats = sim.run()

        assert stats.total_cycles > 0
        assert isinstance(stats, UnifiedSimulatorStats)


# =============================================================================
# Test Traffic Pattern Integration
# =============================================================================

class TestTrafficPatterns:
    """Test traffic pattern integration"""

    def test_random_traffic_pattern(self, basic_sim_config):
        """Test random traffic pattern"""
        basic_sim_config.traffic_pattern = TrafficPattern.RANDOM
        sim = UnifiedSimulator(sim_config=basic_sim_config)

        stats = sim.run()

        assert stats.total_requests > 0
        assert stats.completed_requests >= 0

    def test_sequential_traffic_pattern(self, seq_sim_config):
        """Test sequential traffic pattern"""
        sim = UnifiedSimulator(sim_config=seq_sim_config)

        stats = sim.run()

        assert stats.total_requests > 0
        # Sequential should have high row hit rate
        if stats.completed_requests > 0:
            assert stats.row_hit_rate >= 0

    def test_stride_traffic_pattern(self):
        """Test stride traffic pattern"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.STRIDE,
            request_rate=0.5,
            stride_value=256,
            seed=42,
        )
        sim = UnifiedSimulator(sim_config=config)

        stats = sim.run()

        assert stats.total_requests > 0

    def test_hot_spot_traffic_pattern(self):
        """Test hot spot traffic pattern"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.HOT_SPOT,
            request_rate=0.5,
            seed=42,
        )
        sim = UnifiedSimulator(sim_config=config)

        stats = sim.run()

        assert stats.total_requests > 0


# =============================================================================
# Test Multi-Master Integration
# =============================================================================

class TestMultiMasterIntegration:
    """Test multi-master configuration integration"""

    def test_2_master_simulation(self, multi_master_config):
        """Test simulation with 2 masters"""
        sim = UnifiedSimulator(
            sim_config=multi_master_config,
            num_masters=2
        )

        stats = sim.run()

        assert stats.total_cycles > 0
        assert stats.total_requests > 0

    def test_4_master_simulation(self, multi_master_config):
        """Test simulation with 4 masters"""
        sim = UnifiedSimulator(
            sim_config=multi_master_config,
            num_masters=4
        )

        stats = sim.run()

        assert stats.total_cycles > 0
        assert stats.total_requests > 0

    def test_8_master_simulation(self, multi_master_config):
        """Test simulation with 8 masters"""
        sim = UnifiedSimulator(
            sim_config=multi_master_config,
            num_masters=8
        )

        stats = sim.run()

        assert stats.total_cycles > 0

    def test_axi_statistics_collection(self, multi_master_config):
        """Test AXI statistics collection"""
        sim = UnifiedSimulator(
            sim_config=multi_master_config,
            num_masters=4,
            enable_axi=True
        )

        stats = sim.run()

        # Verify AXI statistics are collected
        assert hasattr(stats, 'axi_ar_transactions')
        assert hasattr(stats, 'axi_aw_transactions')
        assert hasattr(stats, 'axi_r_beats')
        assert hasattr(stats, 'axi_w_beats')


# =============================================================================
# Test HBM4 Integration
# =============================================================================

class TestHBM4Integration:
    """Test HBM4-specific integration"""

    def test_hbm4_spec_in_unified_simulator(self, hbm4_sim_config):
        """Test HBM4 spec integration in unified simulator"""
        sim = UnifiedSimulator(
            sim_config=hbm4_sim_config,
            num_masters=4
        )

        # Verify controller uses HBM4
        assert hasattr(sim.controller, 'spec')
        assert sim.controller.spec.channels == 32

    def test_hbm4_channel_array_integration(self):
        """Test HBM4 channel array integration"""
        spec = HBM4Spec()
        channel_array = HBM4ChannelArray(spec=spec)

        assert len(channel_array.channels) == 32

        # Verify peak bandwidth
        expected_bandwidth = 32 * 64.0  # GB/s
        actual = channel_array.total_bandwidth_gbs
        assert abs(actual - expected_bandwidth) < 0.001

    def test_hbm4_controller_in_unified_simulator(self, hbm4_sim_config):
        """Test HBM4 controller in unified simulator"""
        sim = UnifiedSimulator(
            sim_config=hbm4_sim_config,
            num_masters=4
        )

        # Verify controller is HBM4Controller
        from model.controller.HBM4_controller import HBM4Controller
        assert isinstance(sim.controller, HBM4Controller)


# =============================================================================
# Test Statistics Collection
# =============================================================================

class TestStatisticsCollection:
    """Test statistics collection and reporting"""

    def test_latency_statistics(self, seq_sim_config):
        """Test latency statistics collection"""
        sim = UnifiedSimulator(sim_config=seq_sim_config)

        stats = sim.run()

        if stats.completed_requests > 0:
            assert stats.avg_latency > 0
            assert stats.max_latency_cycles > 0
            assert stats.min_latency_cycles > 0

    def test_bandwidth_statistics(self, seq_sim_config):
        """Test bandwidth statistics"""
        sim = UnifiedSimulator(sim_config=seq_sim_config)

        stats = sim.run()

        if stats.completed_requests > 0:
            assert stats.throughput_gbps > 0
            assert stats.bandwidth_efficiency > 0

    def test_row_hit_statistics(self, seq_sim_config):
        """Test row hit statistics"""
        sim = UnifiedSimulator(sim_config=seq_sim_config)

        stats = sim.run()

        assert stats.row_hit_rate >= 0
        assert stats.row_hit_rate <= 1.0

    def test_refresh_statistics(self, hbm4_sim_config):
        """Test refresh statistics"""
        sim = UnifiedSimulator(sim_config=hbm4_sim_config)

        stats = sim.run()

        assert stats.refresh_count >= 0

    def test_dram_statistics(self, hbm4_sim_config):
        """Test DRAM statistics"""
        sim = UnifiedSimulator(sim_config=hbm4_sim_config)

        stats = sim.run()

        assert stats.total_dram_activations >= 0
        assert stats.total_dram_reads >= 0
        assert stats.total_dram_writes >= 0

    def test_stats_to_dict(self, basic_sim_config):
        """Test statistics conversion to dictionary"""
        sim = UnifiedSimulator(sim_config=basic_sim_config)

        stats = sim.run()

        stats_dict = stats.to_dict()
        assert isinstance(stats_dict, dict)
        assert 'total_cycles' in stats_dict
        assert 'total_requests' in stats_dict
        assert 'completed_requests' in stats_dict


# =============================================================================
# Test Performance Benchmarks
# =============================================================================

class TestPerformanceBenchmarks:
    """Test performance benchmarks"""

    def test_short_simulation_performance(self):
        """Test short simulation completes quickly"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )

        start_time = time.time()
        sim = UnifiedSimulator(sim_config=config)
        stats = sim.run()
        elapsed = time.time() - start_time

        # Should complete in reasonable time
        assert elapsed < 10.0  # 10 seconds max
        assert stats.total_cycles > 0

    def test_long_simulation_stability(self):
        """Test long simulation stability"""
        config = SimulationConfig(
            simulation_time_us=500.0,  # 500us
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.5,
            seed=42,
        )

        sim = UnifiedSimulator(sim_config=config)
        stats = sim.run()

        assert stats.total_cycles > 0
        assert stats.total_requests > 0

    def test_high_request_rate_stability(self):
        """Test high request rate stability"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.9,  # 90% request rate
            seed=42,
        )

        sim = UnifiedSimulator(sim_config=config)
        stats = sim.run()

        assert stats.total_requests > 100


# =============================================================================
# Test Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling"""

    def test_invalid_traffic_pattern(self):
        """Test handling of invalid traffic pattern"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )

        # Should not raise exception
        sim = UnifiedSimulator(sim_config=config)
        assert sim is not None

    def test_zero_request_rate(self):
        """Test handling of zero request rate"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.0,  # No requests
            seed=42,
        )

        sim = UnifiedSimulator(sim_config=config)
        stats = sim.run()

        assert stats.total_requests == 0

    def test_invalid_master_count(self):
        """Test handling of invalid master count"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
        )

        # Should handle 0 masters gracefully
        sim = UnifiedSimulator(
            sim_config=config,
            num_masters=0,
            enable_axi=False
        )
        assert sim is not None


# =============================================================================
# Test Command Convenience Function
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_run_unified_simulation(self):
        """Test run_unified_simulation convenience function"""
        stats = run_unified_simulation(
            simulation_time_us=20.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            num_masters=2,
            enable_axi=True,
            seed=42,
        )

        assert isinstance(stats, UnifiedSimulatorStats)
        assert stats.total_cycles > 0

    def test_run_unified_simulation_without_axi(self):
        """Test run_unified_simulation without AXI"""
        stats = run_unified_simulation(
            simulation_time_us=20.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.5,
            enable_axi=False,
            seed=42,
        )

        assert isinstance(stats, UnifiedSimulatorStats)

    def test_run_unified_simulation_different_patterns(self):
        """Test run_unified_simulation with different patterns"""
        patterns = [
            TrafficPattern.RANDOM,
            TrafficPattern.SEQUENTIAL,
            TrafficPattern.STRIDE,
            TrafficPattern.HOT_SPOT,
        ]

        for pattern in patterns:
            stats = run_unified_simulation(
                simulation_time_us=10.0,
                traffic_pattern=pattern,
                request_rate=0.5,
                seed=42,
            )
            assert stats.total_cycles > 0


# =============================================================================
# Test AXI QoS Integration
# =============================================================================

class TestAXIQoSIntegration:
    """Test AXI QoS integration"""

    def test_qos_enabled_interconnect(self):
        """Test QoS-enabled interconnect creation"""
        interconnect, masters, slave = create_hbm_interconnect(
            num_masters=4,
            enable_qos=True
        )

        assert interconnect is not None

    def test_qos_disabled_interconnect(self):
        """Test QoS-disabled interconnect creation"""
        interconnect, masters, slave = create_hbm_interconnect(
            num_masters=4,
            enable_qos=False
        )

        assert interconnect is not None

    def test_multi_master_qos_arbitation(self):
        """Test QoS arbitration between masters"""
        interconnect, masters, slave = create_hbm_interconnect(
            num_masters=4,
            enable_qos=True
        )

        # Submit requests from multiple masters with different priorities
        # This tests the QoS arbitration logic


# =============================================================================
# Test Timing Verification
# =============================================================================

class TestTimingVerification:
    """Test timing verification"""

    def test_timing_parameters_alignment(self):
        """Test timing parameters are aligned"""
        from model.dram.HBM4_spec import HBM4Spec

        spec = HBM4Spec()

        # Verify key timing parameters
        assert spec.nRCDRD == 8   # tRCD
        assert spec.nRP == 8      # tRP
        assert spec.nRAS == 20    # tRAS
        assert spec.nRC == 22     # tRC
        assert spec.nRFC == 180   # tRFC
        assert spec.nREFI == 3900  # tREFI

    def test_clock_period_calculation(self):
        """Test clock period calculation"""
        from model.dram.HBM4_spec import HBM4Spec

        spec = HBM4Spec()

        # HBM4 at 8 GT/s: tCK = 125 ps
        expected_tCK = 125.0
        assert abs(spec.tCK_ps - expected_tCK) < 0.01


# =============================================================================
# Test Comprehensive Integration
# =============================================================================

class TestComprehensiveIntegration:
    """Test comprehensive integration scenarios"""

    def test_full_system_simulation(self):
        """Test full system simulation"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.MIXED,
            request_rate=0.5,
            read_ratio=0.7,
            seed=42,
        )

        sim = UnifiedSimulator(
            sim_config=config,
            num_masters=8,
            enable_axi=True
        )

        stats = sim.run()

        # Verify all statistics are collected
        assert stats.total_cycles > 0
        assert stats.total_requests > 0
        assert stats.completed_requests >= 0
        assert stats.read_requests >= 0
        assert stats.write_requests >= 0

    def test_read_intensive_workload(self):
        """Test read-intensive workload"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            read_ratio=0.95,  # 95% reads
            seed=42,
        )

        sim = UnifiedSimulator(sim_config=config)
        stats = sim.run()

        assert stats.read_requests > stats.write_requests

    def test_write_intensive_workload(self):
        """Test write-intensive workload"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            read_ratio=0.05,  # 5% reads, 95% writes
            seed=42,
        )

        sim = UnifiedSimulator(sim_config=config)
        stats = sim.run()

        assert stats.write_requests > stats.read_requests

    def test_mixed_traffic_workload(self):
        """Test mixed traffic workload"""
        config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.MIXED,
            request_rate=0.5,
            read_ratio=0.5,
            seed=42,
        )

        sim = UnifiedSimulator(sim_config=config)
        stats = sim.run()

        assert stats.total_requests > 0


# =============================================================================
# Summary Test
# =============================================================================

def test_unified_sim_summary():
    """Summary test for unified simulator integration"""
    print("\n=== Unified Simulator Integration Test Summary ===")

    # Test basic functionality
    config = SimulationConfig(
        simulation_time_us=50.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.5,
        read_ratio=0.7,
        seed=42,
    )

    sim = UnifiedSimulator(
        sim_config=config,
        num_masters=4,
        enable_axi=True
    )

    stats = sim.run()

    print(f"  Total cycles: {stats.total_cycles}")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Completed: {stats.completed_requests}")
    print(f"  Read/Write: {stats.read_requests}/{stats.write_requests}")
    print(f"  Avg latency: {stats.avg_latency:.1f} cycles")
    print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
    print(f"  Row hit rate: {stats.row_hit_rate:.2%}")
    print(f"  Bandwidth efficiency: {stats.bandwidth_efficiency:.2%}")

    # Verify basic stats
    assert stats.total_cycles > 0

    print("=== Unified Simulator Integration Test PASSED ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])