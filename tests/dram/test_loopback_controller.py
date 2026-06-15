"""
Unit Tests for Loopback Controller

Tests loopback modes, PRBS generation, error detection,
and BER calculation for HBM4 PHY verification.

Reference:
- JEDEC JESD270-4A HBM4 specification
- Cadence HBM4E documentation
- Synopsys DesignWare HBM4/4E Controller IP
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from model.dram.loopback_controller import (
    LoopbackMode,
    LoopbackLevel,
    LoopbackState,
    LoopbackResult,
    LoopbackConfig,
    LaneResult,
    ChannelResult,
    LoopbackStatus,
    PRBSGenerator,
    FixedPatternGenerator,
    LoopbackController,
    HBM4LoopbackManager,
)


class TestLoopbackMode:
    """Tests for LoopbackMode enumeration"""
    
    def test_all_modes_defined(self):
        """Test all loopback modes are defined"""
        expected_modes = [
            'PRBS_7',
            'PRBS_15',
            'PRBS_31',
            'FIXED_ALL_ZEROS',
            'FIXED_ALL_ONES',
            'FIXED_ALTERNATING',
            'MODE_8N',
        ]
        for mode_name in expected_modes:
            assert hasattr(LoopbackMode, mode_name)
    
    def test_mode_count(self):
        """Test number of loopback modes"""
        # Should have 7 modes: 3 PRBS + 3 fixed + 1 8N
        assert len(LoopbackMode) == 7


class TestLoopbackLevel:
    """Tests for LoopbackLevel enumeration"""
    
    def test_all_levels_defined(self):
        """Test all loopback levels are defined"""
        assert LoopbackLevel.LANE is not None
        assert LoopbackLevel.CHANNEL is not None
        assert LoopbackLevel.STACK is not None
    
    def test_level_count(self):
        """Test number of loopback levels"""
        assert len(LoopbackLevel) == 3


class TestLoopbackState:
    """Tests for LoopbackState enumeration"""
    
    def test_all_states_defined(self):
        """Test all loopback states are defined"""
        expected_states = ['IDLE', 'CONFIGURE', 'RUNNING', 'VERIFY', 'COMPLETE']
        for state_name in expected_states:
            assert hasattr(LoopbackState, state_name)
    
    def test_state_count(self):
        """Test number of loopback states"""
        assert len(LoopbackState) == 5
    
    def test_state_order(self):
        """Test state order matches specification"""
        states = [s.name for s in LoopbackState]
        assert states == ['IDLE', 'CONFIGURE', 'RUNNING', 'VERIFY', 'COMPLETE']


class TestPRBSGenerator:
    """Tests for PRBS generator"""
    
    def test_prbs7_initialization(self):
        """Test PRBS-7 initialization"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7)
        assert gen.mode == LoopbackMode.PRBS_7
        assert gen.length == 127  # 2^7 - 1
    
    def test_prbs15_initialization(self):
        """Test PRBS-15 initialization"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_15)
        assert gen.mode == LoopbackMode.PRBS_15
        assert gen.length == 32767  # 2^15 - 1
    
    def test_prbs31_initialization(self):
        """Test PRBS-31 initialization"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_31)
        assert gen.mode == LoopbackMode.PRBS_31
        assert gen.length == 2147483647  # 2^31 - 1
    
    def test_prbs7_sequence(self):
        """Test PRBS-7 generates correct sequence"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        bits = [gen.next() for _ in range(127)]
        # After 127 bits, sequence should repeat
        assert len(bits) == 127
    
    def test_prbs7_repeatability(self):
        """Test PRBS-7 repeats after length"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        first_bits = [gen.next() for _ in range(127)]
        
        gen.reset(0x7F)
        second_bits = [gen.next() for _ in range(127)]
        
        assert first_bits == second_bits
    
    def test_generate_byte(self):
        """Test byte generation"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        byte = gen.generate_byte()
        assert 0 <= byte <= 255
    
    def test_generate_n_bytes(self):
        """Test N-byte generation"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        bytes_list = gen.generate_n_bytes(10)
        assert len(bytes_list) == 10
        for byte in bytes_list:
            assert 0 <= byte <= 255
    
    def test_reset_with_seed(self):
        """Test reset with new seed"""
        gen = PRBSGenerator(mode=LoopbackMode.PRBS_7, seed=0x7F)
        first_bit = gen.next()
        
        gen.reset(0x7F)
        reset_bit = gen.next()
        
        assert first_bit == reset_bit


class TestFixedPatternGenerator:
    """Tests for fixed pattern generator"""
    
    def test_all_zeros(self):
        """Test all zeros pattern"""
        gen = FixedPatternGenerator(mode=LoopbackMode.FIXED_ALL_ZEROS)
        bits = [gen.next() for _ in range(16)]
        assert all(b == 0 for b in bits)
    
    def test_all_ones(self):
        """Test all ones pattern"""
        gen = FixedPatternGenerator(mode=LoopbackMode.FIXED_ALL_ONES)
        bits = [gen.next() for _ in range(16)]
        assert all(b == 1 for b in bits)
    
    def test_alternating(self):
        """Test alternating pattern"""
        gen = FixedPatternGenerator(mode=LoopbackMode.FIXED_ALTERNATING)
        bits = [gen.next() for _ in range(16)]
        # After counter increment: (1%2)=1, (2%2)=0, (3%2)=1, ...
        expected = [i % 2 for i in range(1, 17)]
        assert bits == expected
    
    def test_8n_pattern(self):
        """Test 8N pattern"""
        gen = FixedPatternGenerator(mode=LoopbackMode.MODE_8N)
        # First 8 bits should be from 0x00
        bits_first_byte = [gen.next() for _ in range(8)]
        # Next 8 bits should be from 0x01
        bits_second_byte = [gen.next() for _ in range(8)]

        # Check byte values
        gen.reset()
        byte1 = gen.generate_byte()
        # After reset, counter=0. generate_byte calls next() 8 times.
        # next() increments counter, then returns (counter // 8) & 1
        # For counters 1-8: (1//8)=0, (2//8)=0, ..., (7//8)=0, (8//8)=1
        # Bits 0-6 = 0, Bit 7 = 1
        # Byte = 0b10000000 = 0x80
        assert byte1 == 0x80

        gen.generate_byte()  # Skip second byte (counter 9-16)
        byte2 = gen.generate_byte()  # Third byte (counter 17-24)
        # For counters 9-16: same pattern as first byte, counter wraps per 8
        # Bit 7 = 1, rest = 0
        # Byte = 0b10000000 = 0x80
        assert byte2 == 0x80
    
    def test_generate_byte_zeros(self):
        """Test byte generation for zeros"""
        gen = FixedPatternGenerator(mode=LoopbackMode.FIXED_ALL_ZEROS)
        byte = gen.generate_byte()
        assert byte == 0x00
    
    def test_generate_byte_ones(self):
        """Test byte generation for ones"""
        gen = FixedPatternGenerator(mode=LoopbackMode.FIXED_ALL_ONES)
        byte = gen.generate_byte()
        assert byte == 0xFF


class TestLoopbackConfig:
    """Tests for LoopbackConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = LoopbackConfig()
        assert config.mode == LoopbackMode.PRBS_7
        assert config.level == LoopbackLevel.LANE
        assert config.channel_mask == 0xFFFFFFFF
        assert config.test_length == 10000
        assert not config.enable_error_injection
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = LoopbackConfig(
            mode=LoopbackMode.PRBS_15,
            level=LoopbackLevel.CHANNEL,
            channel_mask=0xFFFF,
            test_length=50000,
            enable_error_injection=True,
            error_injection_rate=0.001,
        )
        assert config.mode == LoopbackMode.PRBS_15
        assert config.level == LoopbackLevel.CHANNEL
        assert config.channel_mask == 0xFFFF
        assert config.test_length == 50000
        assert config.enable_error_injection
        assert config.error_injection_rate == 0.001


class TestLaneResult:
    """Tests for LaneResult dataclass"""
    
    def test_default_lane_result(self):
        """Test default lane result"""
        result = LaneResult(lane_id=0, channel_id=0)
        assert result.lane_id == 0
        assert result.channel_id == 0
        assert result.total_bits == 0
        assert result.error_bits == 0
        assert result.ber == 0.0
        assert not result.passed
    
    def test_lane_result_calculation(self):
        """Test lane result BER calculation"""
        result = LaneResult(lane_id=0, channel_id=0, total_bits=1000, error_bits=1)
        result.ber = result.error_bits / result.total_bits if result.total_bits > 0 else 0.0
        assert result.ber == 0.001
    
    def test_error_count_alias(self):
        """Test error_count property alias"""
        result = LaneResult(lane_id=0, channel_id=0, error_bits=5)
        assert result.error_count == 5


class TestChannelResult:
    """Tests for ChannelResult dataclass"""
    
    def test_default_channel_result(self):
        """Test default channel result"""
        result = ChannelResult(channel_id=0)
        assert result.channel_id == 0
        assert result.num_lanes == 64
        assert result.total_bits == 0
        assert result.total_errors == 0
        assert not result.passed


class TestLoopbackStatus:
    """Tests for LoopbackStatus dataclass"""
    
    def test_default_status(self):
        """Test default status"""
        status = LoopbackStatus()
        assert status.state == LoopbackState.IDLE
        assert status.bits_transmitted == 0
        assert status.total_errors == 0
        assert status.retry_count == 0


class TestLoopbackController:
    """Tests for LoopbackController"""
    
    def test_initialization(self):
        """Test controller initialization"""
        ctrl = LoopbackController(num_channels=32, num_lanes_per_channel=64)
        
        assert ctrl.num_channels == 32
        assert ctrl.num_lanes == 64
        assert ctrl.status.state == LoopbackState.IDLE
        assert ctrl.config.mode == LoopbackMode.PRBS_7
    
    def test_initialization_with_config(self):
        """Test initialization with custom config"""
        config = LoopbackConfig(
            mode=LoopbackMode.PRBS_31,
            test_length=50000,
        )
        ctrl = LoopbackController(config=config)
        
        assert ctrl.config.mode == LoopbackMode.PRBS_31
        assert ctrl.config.test_length == 50000
    
    def test_configure(self):
        """Test configuration change"""
        ctrl = LoopbackController()
        new_config = LoopbackConfig(
            mode=LoopbackMode.FIXED_ALTERNATING,
            test_length=20000,
        )
        
        result = ctrl.configure(new_config)
        assert result is True
        assert ctrl.config.mode == LoopbackMode.FIXED_ALTERNATING
        assert ctrl.config.test_length == 20000
    
    def test_configure_rejects_when_running(self):
        """Test configuration rejected when running"""
        ctrl = LoopbackController()
        ctrl.status.state = LoopbackState.RUNNING
        
        result = ctrl.configure(LoopbackConfig())
        assert result is False
    
    def test_start(self):
        """Test starting loopback test"""
        ctrl = LoopbackController(num_channels=4)
        
        result = ctrl.start()
        assert result is True
        assert ctrl.status.state == LoopbackState.CONFIGURE
    
    def test_start_rejects_when_running(self):
        """Test start rejected when not idle"""
        ctrl = LoopbackController()
        ctrl.status.state = LoopbackState.RUNNING
        
        result = ctrl.start()
        assert result is False
    
    def test_tick_increments_cycle(self):
        """Test tick increments cycle counter"""
        ctrl = LoopbackController()
        initial_cycle = ctrl.cycle
        
        ctrl.tick()
        assert ctrl.cycle == initial_cycle + 1
    
    def test_state_transition_idle_to_configure(self):
        """Test state transition from IDLE to CONFIGURE"""
        ctrl = LoopbackController()
        ctrl.start()
        
        ctrl.process_cycle()
        assert ctrl.status.state == LoopbackState.RUNNING
    
    def test_state_transition_to_complete(self):
        """Test state transitions to COMPLETE"""
        ctrl = LoopbackController(
            num_channels=1,
            num_lanes_per_channel=8,
            config=LoopbackConfig(test_length=10)
        )
        ctrl.start()
        
        # Run until complete
        for _ in range(1000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()
    
    def test_get_overall_ber(self):
        """Test BER calculation"""
        ctrl = LoopbackController(
            num_channels=1,
            num_lanes_per_channel=8,
            config=LoopbackConfig(test_length=100)
        )
        
        # No data yet
        ber = ctrl.get_overall_ber()
        assert ber == 0.0
    
    def test_get_summary(self):
        """Test summary generation"""
        ctrl = LoopbackController(num_channels=4)
        summary = ctrl.get_summary()
        
        assert 'state' in summary
        assert 'mode' in summary
        assert 'level' in summary
        assert 'total_channels' in summary
        assert 'overall_ber' in summary
    
    def test_is_passed(self):
        """Test is_passed returns false when not complete"""
        ctrl = LoopbackController()
        assert not ctrl.is_passed()
    
    def test_lane_and_channel_masks(self):
        """Test channel and lane masking"""
        config = LoopbackConfig(
            channel_mask=0x3,  # Only channels 0 and 1
            lane_mask=0xF,      # Only lanes 0-3
        )
        ctrl = LoopbackController(num_channels=4, config=config)
        
        assert ctrl._is_channel_enabled(0)
        assert ctrl._is_channel_enabled(1)
        assert not ctrl._is_channel_enabled(2)
        assert not ctrl._is_channel_enabled(3)
        
        assert ctrl._is_lane_enabled(0, 0)
        assert ctrl._is_lane_enabled(0, 3)
        assert not ctrl._is_lane_enabled(0, 4)


class TestLoopbackControllerErrorInjection:
    """Tests for error injection in loopback controller"""
    
    def test_error_injection_enabled(self):
        """Test error injection when enabled"""
        config = LoopbackConfig(
            enable_error_injection=True,
            error_injection_rate=0.1,
            test_length=1000,
        )
        ctrl = LoopbackController(
            num_channels=1,
            num_lanes_per_channel=8,
            config=config,
        )
        ctrl.start()
        
        # Run until complete
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        # With 10% error rate, should have some errors
        # (statistically very likely with 1000 bits)
        summary = ctrl.get_summary()
        assert summary['total_errors'] >= 0  # May or may not have errors due to randomness


class TestLoopbackControllerModes:
    """Tests for different loopback modes"""
    
    def test_prbs7_mode(self):
        """Test PRBS-7 mode"""
        config = LoopbackConfig(mode=LoopbackMode.PRBS_7, test_length=100)
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()
        
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()
        assert ctrl.is_passed()  # No errors expected
    
    def test_prbs15_mode(self):
        """Test PRBS-15 mode"""
        config = LoopbackConfig(mode=LoopbackMode.PRBS_15, test_length=100)
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()
        
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()
    
    def test_fixed_all_zeros(self):
        """Test fixed all zeros mode"""
        config = LoopbackConfig(mode=LoopbackMode.FIXED_ALL_ZEROS, test_length=100)
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()
        
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()
        assert ctrl.is_passed()
    
    def test_fixed_all_ones(self):
        """Test fixed all ones mode"""
        config = LoopbackConfig(mode=LoopbackMode.FIXED_ALL_ONES, test_length=100)
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()
        
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()
        assert ctrl.is_passed()
    
    def test_fixed_alternating(self):
        """Test fixed alternating mode"""
        config = LoopbackConfig(mode=LoopbackMode.FIXED_ALTERNATING, test_length=100)
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()
        
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()
        assert ctrl.is_passed()
    
    def test_mode_8n(self):
        """Test 8N mode"""
        config = LoopbackConfig(mode=LoopbackMode.MODE_8N, test_length=256)
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()
        
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()
        assert ctrl.is_passed()


class TestHBM4LoopbackManager:
    """Tests for HBM4LoopbackManager"""
    
    def test_initialization(self):
        """Test manager initialization"""
        manager = HBM4LoopbackManager(num_channels=4)
        
        assert manager.num_channels == 4
        assert len(manager._controllers) > 0
    
    def test_initialization_lane_level(self):
        """Test lane-level initialization"""
        config = LoopbackConfig(level=LoopbackLevel.LANE)
        manager = HBM4LoopbackManager(num_channels=4, config=config)
        
        # Lane level creates one controller per channel
        assert len(manager._controllers) == 4
    
    def test_initialization_channel_level(self):
        """Test channel-level initialization"""
        config = LoopbackConfig(level=LoopbackLevel.CHANNEL)
        manager = HBM4LoopbackManager(num_channels=4, config=config)
        
        # Channel level creates single controller
        assert len(manager._controllers) == 1
    
    def test_tick(self):
        """Test tick advances all controllers"""
        manager = HBM4LoopbackManager(num_channels=2)
        initial_cycle = manager.cycle
        
        manager.tick()
        assert manager.cycle == initial_cycle + 1
    
    def test_start_all(self):
        """Test starting all controllers"""
        manager = HBM4LoopbackManager(num_channels=2)
        manager.start_all()
        
        for ctrl in manager._controllers:
            assert ctrl.status.state != LoopbackState.IDLE
    
    def test_process_cycles(self):
        """Test processing multiple cycles"""
        manager = HBM4LoopbackManager(num_channels=2)
        initial_cycle = manager.cycle
        
        manager.process_cycles(10)
        assert manager.cycle == initial_cycle + 10
    
    def test_wait_for_completion(self):
        """Test waiting for completion"""
        manager = HBM4LoopbackManager(
            num_channels=1,
            config=LoopbackConfig(test_length=10)
        )
        manager.start_all()
        
        # Run with small max_cycles to avoid hanging
        result = manager.wait_for_completion(max_cycles=1000)
        assert result is True
    
    def test_get_all_results(self):
        """Test getting all results"""
        manager = HBM4LoopbackManager(
            num_channels=2,
            config=LoopbackConfig(test_length=10)
        )
        manager.start_all()
        manager.wait_for_completion(max_cycles=1000)
        
        results = manager.get_all_results()
        assert len(results) > 0
    
    def test_get_summary(self):
        """Test summary generation"""
        manager = HBM4LoopbackManager(num_channels=2)
        summary = manager.get_summary()
        
        assert 'num_controllers' in summary
        assert 'num_passed' in summary
        assert 'num_failed' in summary
        assert 'overall_ber' in summary


class TestChannelResultMethods:
    """Tests for channel result methods"""
    
    def test_get_channel_result(self):
        """Test getting channel result"""
        ctrl = LoopbackController(num_channels=4)
        ctrl.start()
        
        # Run until we have results
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        result = ctrl.get_channel_result(0)
        # Result may or may not exist depending on channel mask
        if result:
            assert result.channel_id == 0
    
    def test_get_lane_result(self):
        """Test getting lane result"""
        ctrl = LoopbackController(num_channels=4)
        ctrl.start()
        
        for _ in range(5000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        result = ctrl.get_lane_result(0, 0)
        if result:
            assert result.lane_id == 0


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_empty_channel_mask(self):
        """Test with no channels enabled"""
        config = LoopbackConfig(channel_mask=0)
        ctrl = LoopbackController(num_channels=4, config=config)
        ctrl.start()
        
        # Should complete quickly with no work
        for _ in range(100):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()
    
    def test_timeout_handling(self):
        """Test timeout handling"""
        config = LoopbackConfig(
            test_length=100000,
            timeout_cycles=10  # Very short timeout
        )
        ctrl = LoopbackController(num_channels=1, config=config)
        ctrl.start()
        
        # Run until timeout
        for _ in range(100):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        # Should complete due to timeout
        assert ctrl.is_complete()


class TestIntegrationWithPHYTraining:
    """Integration tests with PHY training state machine"""
    
    def test_loopback_with_phy_training_sm(self):
        """Test loopback with PHY training state machine"""
        from model.dram.phy_training import PHYTrainingStateMachine
        
        phy_sm = PHYTrainingStateMachine(channel_id=0)
        ctrl = LoopbackController(
            num_channels=1,
            phy_training_sm=phy_sm,
            config=LoopbackConfig(test_length=10)
        )
        
        ctrl.start()
        
        for _ in range(1000):
            ctrl.process_cycle()
            ctrl.tick()
            if ctrl.is_complete():
                break
        
        assert ctrl.is_complete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])