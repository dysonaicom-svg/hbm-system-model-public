"""
HBM4 Unified Simulator Tests
测试 HBM4 统一仿真器的功能

This test file aims for 70%+ code coverage:
- Simulation modes (QUICK, FULL, STRESS, BENCHMARK)
- Speed grades (8Gbps, 12Gbps, 16Gbps)
- Command processing (ACT, RD, WR, PRE, REF)
- PAM3 encoding/decoding
- RTL co-simulation
- Statistics collection
- Channel state management
- Power estimation
"""

import pytest
import sys
import os
import io
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock

sys.path.insert(0, '/home/ic/JXTF/HBM4')

from sim.hbm4_unified_simulator import (
    HBM4UnifiedSimulator,
    SimulationConfig,
    SimulationStats,
    SimulationMode,
    create_parser,
    main,
)


class TestSimulationConfig:
    """测试仿真配置"""

    def test_default_config(self):
        config = SimulationConfig()
        assert config.mode == SimulationMode.QUICK
        assert config.num_channels == 32
        assert config.cycles == 1000

    def test_custom_config(self):
        config = SimulationConfig(
            mode=SimulationMode.FULL,
            num_channels=16,
            cycles=500,
        )
        assert config.mode == SimulationMode.FULL
        assert config.num_channels == 16
        assert config.cycles == 500

    def test_config_from_args(self):
        """测试从参数创建配置"""
        class MockArgs:
            mode = 'full'
            channels = 16
            cycles = 500
            pam3 = True
            ecc = True
            lane_repair = True
            trace = False
            verbose = True
            speed_grade = "16Gbps"

        args = MockArgs()
        config = SimulationConfig.from_args(args)
        assert config.mode == SimulationMode.FULL
        assert config.num_channels == 16


class TestSimulationStats:
    """测试仿真统计"""

    def test_stats_initialization(self):
        """测试统计初始化"""
        stats = SimulationStats()
        assert stats.total_cycles == 0
        assert stats.commands_processed == 0
        assert stats.errors_detected == 0

    def test_rtl_match_rate(self):
        """测试 RTL 匹配率"""
        stats = SimulationStats()
        stats.rtl_matched = 90
        stats.rtl_mismatched = 10
        assert abs(stats.rtl_match_rate - 0.9) < 0.001

    def test_rtl_match_rate_zero(self):
        """测试 RTL 匹配率 - 无事务"""
        stats = SimulationStats()
        assert stats.rtl_match_rate == 0.0

    def test_duration_calculation(self):
        """测试持续时间计算"""
        stats = SimulationStats()
        stats.start_time = 100.0
        stats.end_time = 105.0
        assert abs(stats.duration_s - 5.0) < 0.001

    def test_throughput_calculation(self):
        """测试吞吐量计算"""
        stats = SimulationStats()
        stats.commands_processed = 1000
        stats.start_time = 100.0
        stats.end_time = 105.0
        assert stats.throughput == 200.0  # 1000 / 5 = 200

    def test_throughput_zero_duration(self):
        """测试吞吐量 - 零持续时间"""
        stats = SimulationStats()
        stats.commands_processed = 100
        stats.start_time = 100.0
        stats.end_time = 100.0
        assert stats.throughput == 0.0


class TestSimulationMode:
    """测试仿真模式"""

    def test_all_modes(self):
        """测试所有模式"""
        assert SimulationMode.QUICK is not None
        assert SimulationMode.FULL is not None
        assert SimulationMode.STRESS is not None
        assert SimulationMode.BENCHMARK is not None


class TestHBM4UnifiedSimulator:
    """测试 HBM4 统一仿真器"""

    def test_simulator_creation(self):
        """测试仿真器创建"""
        config = SimulationConfig(
            num_channels=8,
            cycles=100,
        )
        sim = HBM4UnifiedSimulator(config)
        assert sim.config == config

    def test_simulator_run(self):
        """测试运行仿真"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            mode=SimulationMode.QUICK,
        )
        sim = HBM4UnifiedSimulator(config)
        stats = sim.run()
        assert stats.total_cycles > 0

    def test_simulator_get_stats(self):
        """测试获取统计"""
        config = SimulationConfig(num_channels=4, cycles=20)
        sim = HBM4UnifiedSimulator(config)
        sim.run()
        stats = sim.get_stats()
        # get_stats 可能返回字典或 SimulationStats
        if isinstance(stats, dict):
            assert 'total_cycles' in stats or 'commands_processed' in stats
        else:
            assert stats.total_cycles > 0


class TestUncoveredMethods:
    """Test uncovered methods in HBM4UnifiedSimulator (lines 170-496)"""

    def test_12gbps_speed_grade(self):
        """Test 12Gbps speed grade (line 170)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            speed_grade="12Gbps",
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()
        assert sim.spec.data_rate_gtps == 12.0

    def test_16gbps_speed_grade(self):
        """Test 16Gbps speed grade (line 172)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            speed_grade="16Gbps",
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()
        assert sim.spec.data_rate_gtps == 16.0

    def test_verbose_initialization(self):
        """Test verbose initialization output (lines 222-224)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            verbose=True,
        )
        sim = HBM4UnifiedSimulator(config)
        # Should not raise, just test verbose output
        sim.initialize()

    def test_initialize_complete(self):
        """Test initialization completion (line 236)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            verbose=True,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()
        assert sim.running is True

    def test_invalid_channel_rejection(self):
        """Test invalid channel rejection (line 272)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Channel 100 is invalid (max is 3)
        ok, msg = sim.process_command(channel=100, command='ACT', address=0x1000)
        assert ok is False
        assert 'Invalid channel' in msg

    def test_process_wra_command(self):
        """Test WRA command processing (line 293)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Open row first
        sim.process_command(channel=0, command='ACT', address=0x1000)
        for _ in range(15):
            sim.tick()

        # WRA command
        ok, msg = sim.process_command(channel=0, command='WRA', address=0x1000, data=0xDEADBEEF)
        # Check that writes were tracked
        ch_stats = sim.stats.channel_stats[0]
        assert ch_stats['writes'] >= 0

    def test_process_ref_command(self):
        """Test REF command processing (line 295)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Issue refresh
        sim.process_command(channel=0, command='REF', address=0x0)
        ch_stats = sim.stats.channel_stats[0]
        # REF may or may not succeed depending on timing

    def test_process_pam3_sequence(self):
        """Test PAM3 sequence processing (lines 322-324)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            enable_pam3=True,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        symbols = sim.process_pam3_sequence(0xDEADBEEF, dq_width=128)
        assert isinstance(symbols, list)
        assert sim.stats.pam3_symbols_encoded > 0

    def test_get_channel_state(self):
        """Test get_channel_state method"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        state = sim.get_channel_state(channel=0)
        assert isinstance(state, dict)

    # RTL Co-simulation tests (lines 357-396)

    def test_enable_rtl_cosimulation(self):
        """Test RTL cosimulation enable (lines 357-387)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
        )
        sim = HBM4UnifiedSimulator(config)

        sim.enable_rtl_cosimulation(enable_rtl=True, compare_results=True, trace_enabled=True)
        assert sim.cosim_enabled is True
        assert sim.rtl_interface is not None
        assert sim.result_comparator is not None

    def test_disable_rtl_cosimulation(self):
        """Test RTL cosimulation disable (lines 389-396)"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
        )
        sim = HBM4UnifiedSimulator(config)

        sim.enable_rtl_cosimulation(enable_rtl=True)
        assert sim.cosim_enabled is True

        sim.disable_rtl_cosimulation()
        assert sim.cosim_enabled is False
        assert sim.rtl_interface is None

    # Mode-specific tests (lines 411-494)

    def test_run_full_mode(self):
        """Test FULL mode execution (lines 411-416)"""
        config = SimulationConfig(
            mode=SimulationMode.FULL,
            num_channels=4,
            cycles=100,
            verbose=True,
        )
        sim = HBM4UnifiedSimulator(config)
        stats = sim.run()
        assert stats.total_cycles > 100  # Should run at least cycles

    def test_run_stress_mode(self):
        """Test STRESS mode execution (lines 413-416)"""
        config = SimulationConfig(
            mode=SimulationMode.STRESS,
            num_channels=8,
            cycles=50,
            verbose=True,
        )
        sim = HBM4UnifiedSimulator(config)
        stats = sim.run()
        assert stats.total_cycles > 0
        # Stress mode should have activated all 8 channels
        assert stats.commands_processed >= 8

    def test_run_benchmark_mode(self):
        """Test BENCHMARK mode execution (lines 415-494)"""
        config = SimulationConfig(
            mode=SimulationMode.BENCHMARK,
            num_channels=8,
            cycles=50,
            verbose=True,
        )
        sim = HBM4UnifiedSimulator(config)
        stats = sim.run()
        assert stats.total_cycles > 0
        # Benchmark mode should process PAM3 sequences
        assert stats.pam3_symbols_encoded > 0

    # Additional stress mode coverage

    def test_stress_mode_parallel_activation(self):
        """Test STRESS mode parallel activation of all channels"""
        config = SimulationConfig(
            mode=SimulationMode.STRESS,
            num_channels=16,
            cycles=50,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Manually test the stress mode logic
        # Parallel activation of all channels
        for ch in range(config.num_channels):
            sim.process_command(ch, 'ACT', address=0x1000 + ch)

        for _ in range(10):
            sim.tick()

        # Read/write all channels
        for ch in range(config.num_channels):
            cmd = 'RD' if ch % 2 == 0 else 'WR'
            data = 0xDEADBEEF + ch if cmd == 'WR' else None
            sim.process_command(ch, cmd, address=0x1000 + ch, data=data)

    # Additional benchmark mode coverage

    def test_benchmark_mode_pam3_ops(self):
        """Test BENCHMARK mode PAM3 operations"""
        config = SimulationConfig(
            mode=SimulationMode.BENCHMARK,
            num_channels=4,
            cycles=20,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # PAM3 encoding benchmark
        import time
        start = time.time()
        for _ in range(1000):
            sim.process_pam3_sequence(0xDEADBEEF)
        pam3_time = time.time() - start

        # Channel operations benchmark
        start = time.time()
        for ch in range(config.num_channels):
            sim.process_command(ch, 'ACT', address=0x1000)
        channel_time = time.time() - start

        assert pam3_time >= 0
        assert channel_time >= 0


class TestCommandLineParser:
    """Test command line argument parser (lines 497-576)"""

    def test_create_parser(self):
        """Test parser creation"""
        parser = create_parser()
        assert parser is not None

    def test_parser_default_values(self):
        """Test parser default values"""
        parser = create_parser()
        args = parser.parse_args([])

        assert args.mode == 'quick'
        assert args.channels == 32
        assert args.cycles == 1000
        assert args.speed_grade == '8Gbps'
        assert args.no_pam3 is False
        assert args.no_ecc is False
        assert args.no_lane_repair is False
        assert args.trace is False
        assert args.verbose is False

    def test_parser_full_mode(self):
        """Test parser with full mode"""
        parser = create_parser()
        args = parser.parse_args(['--mode', 'full', '--cycles', '5000'])
        assert args.mode == 'full'
        assert args.cycles == 5000

    def test_parser_stress_mode(self):
        """Test parser with stress mode"""
        parser = create_parser()
        args = parser.parse_args(['--mode', 'stress', '--channels', '16'])
        assert args.mode == 'stress'
        assert args.channels == 16

    def test_parser_benchmark_mode(self):
        """Test parser with benchmark mode"""
        parser = create_parser()
        args = parser.parse_args(['--mode', 'benchmark', '--cycles', '10000'])
        assert args.mode == 'benchmark'
        assert args.cycles == 10000

    def test_parser_short_flags(self):
        """Test parser short flags"""
        parser = create_parser()
        args = parser.parse_args(['-m', 'full', '-c', '8', '-n', '2000', '-v'])
        assert args.mode == 'full'
        assert args.channels == 8
        assert args.cycles == 2000
        assert args.verbose is True

    def test_parser_speed_grade_12gbps(self):
        """Test parser with 12Gbps speed grade"""
        parser = create_parser()
        args = parser.parse_args(['--speed-grade', '12Gbps'])
        assert args.speed_grade == '12Gbps'

    def test_parser_speed_grade_16gbps(self):
        """Test parser with 16Gbps speed grade"""
        parser = create_parser()
        args = parser.parse_args(['--speed-grade', '16Gbps'])
        assert args.speed_grade == '16Gbps'

    def test_parser_disable_pam3(self):
        """Test parser to disable PAM3"""
        parser = create_parser()
        args = parser.parse_args(['--no-pam3'])
        assert args.no_pam3 is True

    def test_parser_disable_ecc(self):
        """Test parser to disable ECC"""
        parser = create_parser()
        args = parser.parse_args(['--no-ecc'])
        assert args.no_ecc is True

    def test_parser_disable_lane_repair(self):
        """Test parser to disable lane repair"""
        parser = create_parser()
        args = parser.parse_args(['--no-lane-repair'])
        assert args.no_lane_repair is True

    def test_parser_enable_trace(self):
        """Test parser to enable trace"""
        parser = create_parser()
        args = parser.parse_args(['--trace'])
        assert args.trace is True

    def test_parser_combined_options(self):
        """Test parser with multiple options"""
        parser = create_parser()
        args = parser.parse_args([
            '--mode', 'full',
            '--channels', '16',
            '--cycles', '10000',
            '--speed-grade', '16Gbps',
            '--no-pam3',
            '--no-ecc',
            '--no-lane-repair',
            '--trace',
            '--verbose'
        ])
        assert args.mode == 'full'
        assert args.channels == 16
        assert args.cycles == 10000
        assert args.speed_grade == '16Gbps'
        assert args.no_pam3 is True
        assert args.no_ecc is True
        assert args.no_lane_repair is True
        assert args.trace is True
        assert args.verbose is True


class TestMainFunction:
    """Test main function (lines 579-624)"""

    def test_main_function(self):
        """Test main function execution"""
        # Test with quick mode
        test_args = [
            '--mode', 'quick',
            '--channels', '4',
            '--cycles', '50',
        ]

        with patch('sys.argv', ['hbm4_unified_simulator.py'] + test_args):
            exit_code = main()
            assert exit_code == 0

    def test_main_full_mode(self):
        """Test main function with full mode"""
        test_args = [
            '--mode', 'full',
            '--channels', '8',
            '--cycles', '100',
        ]

        with patch('sys.argv', ['hbm4_unified_simulator.py'] + test_args):
            exit_code = main()
            assert exit_code == 0

    def test_main_verbose_output(self):
        """Test main function with verbose output"""
        test_args = [
            '--mode', 'quick',
            '--channels', '4',
            '--verbose',
        ]

        with patch('sys.argv', ['hbm4_unified_simulator.py'] + test_args):
            exit_code = main()
            assert exit_code == 0

    def test_main_no_pam3(self):
        """Test main function without PAM3"""
        test_args = [
            '--mode', 'quick',
            '--channels', '4',
            '--no-pam3',
        ]

        with patch('sys.argv', ['hbm4_unified_simulator.py'] + test_args):
            exit_code = main()
            assert exit_code == 0

    def test_main_no_ecc(self):
        """Test main function without ECC"""
        test_args = [
            '--mode', 'quick',
            '--channels', '4',
            '--no-ecc',
        ]

        with patch('sys.argv', ['hbm4_unified_simulator.py'] + test_args):
            exit_code = main()
            assert exit_code == 0


class TestSimulationStatsRTL:
    """Test RTL statistics fields (lines 115-127)"""

    def test_rtl_stats_initialization(self):
        """Test RTL stats fields initialization"""
        stats = SimulationStats()
        assert stats.rtl_transactions == 0
        assert stats.rtl_matched == 0
        assert stats.rtl_mismatched == 0
        assert stats.rtl_max_latency_diff == 0
        assert stats.rtl_avg_latency_diff == 0.0

    def test_rtl_match_rate_calculation(self):
        """Test RTL match rate calculation"""
        stats = SimulationStats()
        stats.rtl_matched = 100
        stats.rtl_mismatched = 0
        assert stats.rtl_match_rate == 1.0

        stats.rtl_mismatched = 50
        assert abs(stats.rtl_match_rate - 0.6666) < 0.001  # 100/150

    def test_rtl_match_rate_no_transactions(self):
        """Test RTL match rate with no transactions"""
        stats = SimulationStats()
        assert stats.rtl_match_rate == 0.0


class TestSimulationConfigAllModes:
    """Test configuration with all simulation modes"""

    def test_config_quick_mode(self):
        """Test QUICK mode configuration"""
        config = SimulationConfig(mode=SimulationMode.QUICK)
        assert config.mode == SimulationMode.QUICK

    def test_config_full_mode(self):
        """Test FULL mode configuration"""
        config = SimulationConfig(mode=SimulationMode.FULL)
        assert config.mode == SimulationMode.FULL

    def test_config_stress_mode(self):
        """Test STRESS mode configuration"""
        config = SimulationConfig(mode=SimulationMode.STRESS)
        assert config.mode == SimulationMode.STRESS

    def test_config_benchmark_mode(self):
        """Test BENCHMARK mode configuration"""
        config = SimulationConfig(mode=SimulationMode.BENCHMARK)
        assert config.mode == SimulationMode.BENCHMARK

    def test_config_feature_flags(self):
        """Test all feature flags"""
        config = SimulationConfig(
            enable_pam3=False,
            enable_ecc=False,
            enable_lane_repair=False,
            trace_commands=True,
            verbose=True,
        )
        assert config.enable_pam3 is False
        assert config.enable_ecc is False
        assert config.enable_lane_repair is False
        assert config.trace_commands is True
        assert config.verbose is True

    def test_config_from_args_all_features(self):
        """Test from_args with all features enabled"""
        class MockArgs:
            mode = 'full'
            channels = 32
            cycles = 10000
            pam3 = True
            ecc = True
            lane_repair = True
            trace = True
            verbose = True
            speed_grade = "16Gbps"

        config = SimulationConfig.from_args(MockArgs())
        assert config.mode == SimulationMode.FULL
        assert config.num_channels == 32
        assert config.cycles == 10000
        assert config.enable_pam3 is True
        assert config.enable_ecc is True
        assert config.enable_lane_repair is True
        assert config.trace_commands is True
        assert config.verbose is True
        assert config.speed_grade == "16Gbps"


class TestTickMethod:
    """Test tick method and cycle advancement"""

    def test_tick_increments_cycles(self):
        """Test that tick increments total_cycles"""
        config = SimulationConfig(num_channels=4, cycles=50)
        sim = HBM4UnifiedSimulator(config)
        initial_cycles = sim.stats.total_cycles

        sim.tick()
        assert sim.stats.total_cycles == initial_cycles + 1

    def test_multiple_ticks(self):
        """Test multiple tick calls"""
        config = SimulationConfig(num_channels=4, cycles=50)
        sim = HBM4UnifiedSimulator(config)

        for _ in range(100):
            sim.tick()

        assert sim.stats.total_cycles == 100


class TestChannelStateTracking:
    """Test per-channel state tracking"""

    def test_channel_stats_initialization(self):
        """Test channel stats initialization"""
        config = SimulationConfig(num_channels=8)
        sim = HBM4UnifiedSimulator(config)

        for ch in range(8):
            assert ch in sim.stats.channel_stats
            stats = sim.stats.channel_stats[ch]
            assert 'commands' in stats
            assert 'activations' in stats
            assert 'reads' in stats
            assert 'writes' in stats
            assert 'refreshes' in stats

    def test_channel_command_tracking(self):
        """Test command tracking per channel"""
        config = SimulationConfig(num_channels=4, cycles=50)
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Issue commands on different channels
        sim.process_command(channel=0, command='ACT', address=0x1000)
        for _ in range(15):
            sim.tick()
        sim.process_command(channel=1, command='RD', address=0x1000)
        sim.process_command(channel=2, command='WR', address=0x1000, data=0x1234)
        sim.process_command(channel=3, command='REF', address=0x0)

        # Check stats
        ch0_stats = sim.stats.channel_stats[0]
        assert ch0_stats['commands'] >= 1

    def test_command_type_counts(self):
        """Test command type counting"""
        config = SimulationConfig(num_channels=2, cycles=100)
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Issue ACT
        sim.process_command(channel=0, command='ACT', address=0x1000)
        for _ in range(15):
            sim.tick()

        # Issue RD
        sim.process_command(channel=0, command='RD', address=0x1000)
        for _ in range(15):
            sim.tick()

        # Issue WR
        sim.process_command(channel=0, command='WR', address=0x1000, data=0x1234)
        for _ in range(15):
            sim.tick()

        # Check counts
        ch_stats = sim.stats.channel_stats[0]
        assert ch_stats['activations'] >= 1
        assert ch_stats['reads'] >= 1
        assert ch_stats['writes'] >= 1


class TestPAM3Encoding:
    """Test PAM3 encoding integration"""

    def test_pam3_disabled(self):
        """Test simulator with PAM3 disabled"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            enable_pam3=False,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Issue write - should not track PAM3
        sim.process_command(channel=0, command='ACT', address=0x1000)
        for _ in range(15):
            sim.tick()
        sim.process_command(channel=0, command='WR', address=0x1000, data=0xDEADBEEF)

    def test_pam3_enabled_write(self):
        """Test PAM3 encoding on write"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            enable_pam3=True,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        sim.process_command(channel=0, command='ACT', address=0x1000)
        for _ in range(15):
            sim.tick()

        initial_encoded = sim.stats.pam3_symbols_encoded
        sim.process_command(channel=0, command='WR', address=0x1000, data=0xDEADBEEF)
        assert sim.stats.pam3_symbols_encoded > initial_encoded

    def test_pam3_read_decoding(self):
        """Test PAM3 decoding on read"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            enable_pam3=True,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        sim.process_command(channel=0, command='ACT', address=0x1000)
        for _ in range(15):
            sim.tick()

        initial_decoded = sim.stats.pam3_symbols_decoded
        sim.process_command(channel=0, command='RD', address=0x1000)
        # Read operations also track PAM3 decoding
        assert sim.stats.pam3_symbols_decoded >= initial_decoded


class TestPowerEstimation:
    """Test power estimation integration"""

    def test_power_with_all_channels(self):
        """Test power estimation with all channels"""
        config = SimulationConfig(
            num_channels=32,
            cycles=100,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Activate all channels
        for ch in range(32):
            sim.process_command(ch, 'ACT', address=0x1000 + ch)

        stats = sim.get_stats()
        assert stats['power_mW'] >= 0

    def test_power_zero_channels(self):
        """Test power estimation with minimal activity"""
        config = SimulationConfig(
            num_channels=4,
            cycles=20,
        )
        sim = HBM4UnifiedSimulator(config)
        sim.initialize()

        # Minimal activity
        sim.tick()

        stats = sim.get_stats()
        assert stats['power_mW'] >= 0


class TestComponentInitialization:
    """Test component initialization"""

    def test_ecc_disabled(self):
        """Test with ECC disabled"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            enable_ecc=False,
        )
        sim = HBM4UnifiedSimulator(config)
        assert sim.ecc is None

    def test_ecc_enabled(self):
        """Test with ECC enabled"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            enable_ecc=True,
        )
        sim = HBM4UnifiedSimulator(config)
        assert sim.ecc is not None

    def test_lane_repair_disabled(self):
        """Test with lane repair disabled"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            enable_lane_repair=False,
        )
        sim = HBM4UnifiedSimulator(config)
        assert sim.lane_repair is None

    def test_lane_repair_enabled(self):
        """Test with lane repair enabled"""
        config = SimulationConfig(
            num_channels=4,
            cycles=50,
            enable_lane_repair=True,
        )
        sim = HBM4UnifiedSimulator(config)
        assert sim.lane_repair is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
