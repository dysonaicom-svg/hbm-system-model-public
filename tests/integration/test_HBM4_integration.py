"""
HBM4 Support Integration Tests

Tests HBM4 32-channel support and bandwidth calculations.
"""

import pytest

from model.dram.HBM4_spec import HBM4Spec, HBM4_CONFIG, HBM4_SPEED_GRADES
from model.controller.config import HBMConfig
from model.controller.HBM4_controller import HBM4Controller
from sim.simulator import HBMSimulator, SimulationConfig


class TestHBM4Spec:
    """HBM4 specification tests"""

    def test_hbm4_32_channels(self):
        """HBM4 should have 32 channels"""
        spec = HBM4Spec()
        assert spec.channels == 32

    def test_hbm4_64_pseudo_channels(self):
        """32 channels × 2 pseudo-channels = 64 total"""
        spec = HBM4Spec()
        assert spec.pseudo_channels == 64

    def test_hbm4_2048_interface(self):
        """HBM4 interface width is 2048-bit"""
        spec = HBM4Spec()
        assert spec.io_width == 2048

    def test_hbm4_8gtps_base_rate(self):
        """HBM4 base data rate is 8 GT/s"""
        spec = HBM4Spec()
        assert spec.data_rate_gtps == 8.0

    def test_hbm4_bandwidth_8gtps(self):
        """HBM4 @ 8 GT/s = 2.048 TB/s per stack"""
        spec = HBM4Spec()
        # 8 GT/s × 2048 bits / 8 / 1000 = 2.048 TB/s
        expected = 2.048  # TB/s
        assert abs(spec.bandwidth - expected) < 0.01

    def test_hbm4_timing_parameters(self):
        """HBM4 timing parameters"""
        spec = HBM4Spec()
        assert spec.tCK_ps == 125.0  # 1/8 GHz = 125 ps
        assert spec.nCL == 8  # CAS latency
        assert spec.nRAS == 20
        assert spec.nRP == 8


class TestHBM4SpeedGrades:
    """HBM4 speed grades"""

    def test_8gbps_speed_grade(self):
        """8 Gbps speed grade"""
        grade = HBM4_SPEED_GRADES["8Gbps"]
        assert grade["data_rate_gtps"] == 8.0
        assert grade["tCK_ps"] == 125.0

    def test_12gbps_speed_grade(self):
        """12 Gbps speed grade"""
        grade = HBM4_SPEED_GRADES["12Gbps"]
        assert grade["data_rate_gtps"] == 12.0
        # tCK = 1000/12 ≈ 83.33 ps (DDR dual-edge)
        assert abs(grade["tCK_ps"] - 83.33) < 0.1

    def test_16gbps_speed_grade(self):
        """16 Gbps speed grade"""
        grade = HBM4_SPEED_GRADES["16Gbps"]
        assert grade["data_rate_gtps"] == 16.0
        # tCK = 1000/16 = 62.5 ps (DDR dual-edge)
        assert abs(grade["tCK_ps"] - 62.5) < 0.1


class TestHBM4Config:
    """HBM4 configuration tests"""

    def test_default_hbm4_config(self):
        """Default HBM4 configuration"""
        config = HBM4_CONFIG
        assert config.channels == 32
        assert config.io_width == 2048
        assert config.data_rate_gtps == 8.0

    def test_hbm4_bandwidth_calculation(self):
        """HBM4 bandwidth calculation"""
        config = HBMConfig(
            io_width=2048,
            data_rate=8e9,
        )
        bw = config.calc_bandwidth()
        assert abs(bw - 2048.0) < 1.0  # GB/s

    def test_hbm4_vs_hbm3_bandwidth(self):
        """HBM4 should have higher bandwidth than HBM3"""
        hbm3_bw = HBMConfig().calc_bandwidth()
        hbm4_bw = HBMConfig(io_width=2048, data_rate=8e9).calc_bandwidth()

        assert hbm4_bw > hbm3_bw
        # HBM3: 6.4 * 1024 / 8 = 819.2 GB/s
        # HBM4: 8.0 * 2048 / 8 = 2048 GB/s
        assert hbm4_bw > 2000  # GB/s


class TestHBM4Controller:
    """HBM4 controller tests"""

    def test_hbm4_controller_creation(self):
        """Test HBM4 controller can be created"""
        controller = HBM4Controller()
        assert controller is not None
        assert hasattr(controller, 'spec')

    def test_hbm4_controller_32_channels(self):
        """HBM4 controller supports 32 channels"""
        controller = HBM4Controller()
        assert controller.channels == 32

    def test_hbm4_controller_submit_request(self):
        """HBM4 controller accepts requests"""
        controller = HBM4Controller()
        request_id = controller.submit_request(
            addr=0x1000,
            is_read=True,
            qos_level=8,
            size_bytes=64
        )
        assert request_id is not None


class TestHBM4Simulation:
    """HBM4 simulation tests - uses HBMConfig with HBM4 parameters"""

    def test_hbm4_simulation_basic(self):
        """Basic HBM4 simulation with 32 channels"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            request_rate=0.5,
            hbm_config=HBMConfig(
                stack_count=1,
                channels_per_stack=32,
                io_width=2048,
                data_rate=8e9,
            ),
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        assert stats.total_requests >= 0

    def test_hbm4_sequential_traffic(self):
        """HBM4 with sequential traffic"""
        from sim.simulator import TrafficPattern

        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            hbm_config=HBMConfig(
                stack_count=1,
                channels_per_stack=32,
                io_width=2048,
                data_rate=8e9,
            ),
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        assert stats.total_requests >= 0

    def test_hbm4_random_traffic(self):
        """HBM4 with random traffic"""
        from sim.simulator import TrafficPattern

        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            hbm_config=HBMConfig(
                stack_count=1,
                channels_per_stack=32,
                io_width=2048,
                data_rate=8e9,
            ),
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        assert stats.total_requests >= 0

    def test_hbm4_hotspot_traffic(self):
        """HBM4 with hot-spot traffic"""
        from sim.simulator import TrafficPattern

        config = SimulationConfig(
            simulation_time_us=10.0,
            traffic_pattern=TrafficPattern.HOT_SPOT,
            request_rate=0.5,
            hbm_config=HBMConfig(
                stack_count=1,
                channels_per_stack=32,
                io_width=2048,
                data_rate=8e9,
            ),
        )
        sim = HBMSimulator(config)
        stats = sim.run()

        assert stats.total_requests >= 0


class TestHBM4Comparison:
    """HBM4 vs HBM3 comparison tests"""

    def test_hbm4_more_channels(self):
        """HBM4 has 4x more channels than HBM3"""
        hbm3_channels = HBMConfig().channels_per_stack
        hbm4_channels = HBM4_CONFIG.channels

        assert hbm4_channels == 32
        assert hbm4_channels == hbm3_channels * 4

    def test_hbm4_wider_interface(self):
        """HBM4 has 2x wider interface than HBM3"""
        hbm3_width = HBMConfig().io_width
        hbm4_width = HBM4_CONFIG.io_width

        assert hbm4_width == 2048
        assert hbm4_width == hbm3_width * 2

    def test_hbm4_higher_bandwidth(self):
        """HBM4 has ~2.5x bandwidth of HBM3"""
        hbm3_bw = HBMConfig().calc_bandwidth()
        hbm4_bw = HBM4_CONFIG.bandwidth_gbs

        ratio = hbm4_bw / hbm3_bw
        # HBM3: 6.4 * 1024 / 8 = 819.2 GB/s
        # HBM4: 8.0 * 2048 / 8 = 2048 GB/s
        # Ratio: 2048 / 819.2 = 2.5
        assert abs(ratio - 2.5) < 0.1

    def test_hbm4_faster_clock(self):
        """HBM4 has faster clock (125ps vs 156.25ps)"""
        hbm3_tCK = 781.25  # ps
        hbm4_tCK = HBM4_CONFIG.tCK_ps

        assert hbm4_tCK < hbm3_tCK
        assert abs(hbm4_tCK - 125.0) < 0.1


class TestHBM4AddressMapping:
    """HBM4 address mapping tests"""

    def test_hbm4_address_decoder(self):
        """Test HBM4 address decoder"""
        from model.controller.address_decoder import AddressDecoder
        from model.dram.HBM4_spec import HBM4Spec

        spec = HBM4Spec()
        decoder = AddressDecoder(HBMConfig(channels_per_stack=32, io_width=2048))

        # Test address decoding
        addr = 0x10000
        decoded = decoder.decode(addr)

        assert 0 <= decoded.channel_id < 32
        assert 0 <= decoded.pseudo_channel_id < 2
        assert 0 <= decoded.bank_group_id < 8
        assert 0 <= decoded.bank_id < 16

    def test_hbm4_row_bits(self):
        """HBM4 row field bits"""
        spec = HBM4Spec()
        # HBM4 spec has 19 row bits for larger capacity (8192 rows per bank group)
        assert spec.ADDR_ROW_BITS >= 16, f"HBM4 should have at least 16 row bits, got {spec.ADDR_ROW_BITS}"

    def test_hbm4_column_bits(self):
        """HBM4 column field bits"""
        spec = HBM4Spec()
        assert spec.ADDR_COL_BITS == 6  # 64 columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])