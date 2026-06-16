"""
Unit Tests for HBM4 Traffic Generator

Tests all traffic patterns, configuration options, and integration points.
"""

import pytest
import random
import threading
import time
from typing import List

from model.traffic.traffic_generator import (
    # Enums
    TrafficPattern,
    DataPrecision,

    # Configuration
    TrafficConfig,
    AddressGenerator,

    # Traffic Patterns
    AITrainingPattern,
    WeightUpdatePattern,
    GradientComputationPattern,
    FeatureMapTransferPattern,
    AIInferencePattern,
    BurstReadPattern,
    WeightReusePattern,
    MixedPrecisionPattern,
    SyntheticPattern,
    FixedRatePattern,
    BurstPattern,
    RandomPattern,
    RampPattern,
    SinusoidalPattern,
    TraceReplayPattern,

    # Main Classes
    TrafficGenerator,
    TrafficGeneratorRunner,
    AddressPatternGenerator,

    # Factory
    create_traffic_generator,
)

from model.controller.request import HBMRequest


class TestTrafficConfig:
    """Tests for TrafficConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = TrafficConfig()
        assert config.read_write_ratio == 0.7
        assert config.request_rate == 1e6
        assert config.burst_size == 32
        assert config.base_address == 0x100000000
        assert config.channels == 32

    def test_custom_config(self):
        """Test custom configuration"""
        config = TrafficConfig(
            read_write_ratio=0.5,
            request_rate=2e6,
            burst_size=64,
            batch_size=32,
            precision=DataPrecision.INT8,
        )
        assert config.read_write_ratio == 0.5
        assert config.request_rate == 2e6
        assert config.burst_size == 64
        assert config.batch_size == 32
        assert config.precision == DataPrecision.INT8

    def test_qos_distribution(self):
        """Test QoS distribution configuration"""
        config = TrafficConfig()
        assert 15 in config.qos_distribution
        assert 0 in config.qos_distribution
        # Distribution should sum to ~1.0
        total = sum(config.qos_distribution.values())
        assert abs(total - 1.0) < 0.01


class TestAddressGenerator:
    """Tests for AddressGenerator"""

    def test_sequential_generation(self):
        """Test sequential address generation"""
        gen = AddressGenerator(base_address=0x1000, address_range=0x10000, stride=64)
        addrs = gen.sequential(10)
        assert len(addrs) == 10
        # Check sequential pattern
        for i in range(9):
            diff = addrs[i + 1] - addrs[i]
            assert diff == 64

    def test_random_generation(self):
        """Test random address generation"""
        gen = AddressGenerator(base_address=0x1000, address_range=0x10000)
        addrs = gen.random(100)
        assert len(addrs) == 100
        # All addresses should be within range
        for addr in addrs:
            assert 0x1000 <= addr < 0x1000 + 0x10000

    def test_stride_access(self):
        """Test strided address generation"""
        gen = AddressGenerator(base_address=0x1000, address_range=0x10000)
        addrs = gen.stride_access(5, stride=128)
        assert len(addrs) == 5
        for i in range(4):
            diff = addrs[i + 1] - addrs[i]
            assert diff == 128

    def test_bank_round_robin(self):
        """Test bank-level round-robin"""
        gen = AddressGenerator(base_address=0x1000, stride=64)
        addrs = gen.bank_round_robin(num_banks=4, count=8)
        assert len(addrs) == 8
        # Should cycle through banks 0,1,2,3,0,1,2,3
        for i in range(8):
            expected_bank = i % 4
            expected_addr = 0x1000 + (expected_bank * 64)
            assert addrs[i] == expected_addr

    def test_channel_round_robin(self):
        """Test channel-level round-robin"""
        gen = AddressGenerator(base_address=0x1000, address_range=0x1000)
        addrs = gen.channel_round_robin(num_channels=4, count=8)
        assert len(addrs) == 8
        # Should cycle through channels 0,1,2,3,0,1,2,3
        for i in range(8):
            expected_channel = i % 4
            expected_addr = 0x1000 + (expected_channel * 0x400)
            assert addrs[i] == expected_addr

    def test_reset(self):
        """Test generator reset"""
        gen = AddressGenerator(base_address=0x1000, stride=64)
        gen.sequential(5)
        gen.bank_round_robin(4, 3)
        gen.reset()
        # After reset, should start from base_address
        addrs = gen.sequential(3)
        assert addrs[0] == 0x1000  # Should be base_address + 0


class TestAITrainingPatterns:
    """Tests for AI Training Traffic Patterns"""

    def test_weight_update_pattern(self):
        """Test weight update pattern generates write requests"""
        pattern = WeightUpdatePattern()
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 10)

        assert len(requests) == 10
        for req in requests:
            assert isinstance(req, HBMRequest)
            assert req.is_read is False  # Weight updates are writes
            assert req.qos == 12  # High QoS for training
            assert req.length == 64

    def test_gradient_computation_pattern(self):
        """Test gradient computation pattern generates read requests"""
        pattern = GradientComputationPattern()
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 10)

        assert len(requests) == 10
        for req in requests:
            assert isinstance(req, HBMRequest)
            assert req.is_read is True  # Gradient reads
            assert req.qos == 12  # High QoS for training
            assert req.length == 64

    def test_feature_map_pattern(self):
        """Test feature map pattern generates mixed read/write"""
        pattern = FeatureMapTransferPattern()
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 10)

        assert len(requests) == 10
        # Should have mix of reads and writes
        read_count = sum(1 for r in requests if r.is_read)
        write_count = sum(1 for r in requests if not r.is_read)
        assert read_count > 0
        assert write_count > 0
        assert read_count + write_count == 10


class TestAIInferencePatterns:
    """Tests for AI Inference Traffic Patterns"""

    def test_burst_read_pattern(self):
        """Test burst read pattern generates read requests"""
        pattern = BurstReadPattern(burst_length=8)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 10)

        assert len(requests) == 10
        for req in requests:
            assert isinstance(req, HBMRequest)
            assert req.is_read is True
            assert req.qos == 15  # Critical QoS for inference latency
            assert req.burst_length == 8

    def test_weight_reuse_pattern(self):
        """Test weight reuse pattern reuses addresses"""
        pattern = WeightReusePattern()
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 50)

        assert len(requests) == 50
        # Addresses should show reuse behavior
        # Multiple requests to same address
        addr_counts = {}
        for req in requests:
            addr_counts[req.addr] = addr_counts.get(req.addr, 0) + 1
        max_reuse = max(addr_counts.values())
        assert max_reuse >= 10  # Should see significant reuse

    def test_mixed_precision_pattern(self):
        """Test mixed precision pattern adjusts request size"""
        pattern = MixedPrecisionPattern()

        # FP16
        config = TrafficConfig(precision=DataPrecision.FP16)
        requests = pattern.generate_requests(config, 5)
        for req in requests:
            assert req.length == 64

        # INT8
        config = TrafficConfig(precision=DataPrecision.INT8)
        requests = pattern.generate_requests(config, 5)
        for req in requests:
            assert req.length == 32

        # INT4
        config = TrafficConfig(precision=DataPrecision.INT4)
        requests = pattern.generate_requests(config, 5)
        for req in requests:
            assert req.length == 16


class TestSyntheticPatterns:
    """Tests for Synthetic Traffic Patterns"""

    def test_fixed_rate_pattern(self):
        """Test fixed rate pattern"""
        pattern = FixedRatePattern()
        config = TrafficConfig(read_write_ratio=0.7)
        requests = pattern.generate_requests(config, 100)

        assert len(requests) == 100
        # Should have mix of reads and writes based on ratio
        read_count = sum(1 for r in requests if r.is_read)
        write_count = sum(1 for r in requests if not r.is_read)
        assert read_count + write_count == 100
        # Should be roughly 70/30 split
        assert 0.6 < (read_count / 100) < 0.8

    def test_burst_pattern(self):
        """Test burst pattern"""
        pattern = BurstPattern(burst_requests=16, idle_ratio=0.5)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert len(requests) == 100
        # Should have some bursts and gaps
        # Note: burst pattern generates requests only during active periods

    def test_random_pattern(self):
        """Test random pattern"""
        pattern = RandomPattern()
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert len(requests) == 100
        # Addresses should be varied (not all sequential)
        addrs = [r.addr for r in requests]
        unique_addrs = len(set(addrs))
        assert unique_addrs > 50  # Should have good variety

    def test_ramp_pattern_up(self):
        """Test ramp up pattern"""
        pattern = RampPattern(ramp_up=True)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        # Ramp up should generate increasing number of requests
        # Early requests: fewer (rate starts at 10%)
        # Late requests: more (rate approaches 100%)
        assert len(requests) <= 100  # May be fewer due to rate limiting

    def test_ramp_pattern_down(self):
        """Test ramp down pattern"""
        pattern = RampPattern(ramp_up=False)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        # Ramp down should generate decreasing number of requests
        assert len(requests) <= 100

    def test_sinusoidal_pattern(self):
        """Test sinusoidal pattern"""
        pattern = SinusoidalPattern(period=100)
        config = TrafficConfig()
        requests = pattern.generate_requests(config, 100)

        assert len(requests) <= 100
        # Should vary with sine wave


class TestTraceReplayPattern:
    """Tests for Trace Replay Pattern"""

    def test_trace_replay(self):
        """Test trace replay"""
        pattern = TraceReplayPattern()

        # Create test trace
        trace_requests = [
            HBMRequest(addr=0x1000, length=64, is_read=True, qos=8),
            HBMRequest(addr=0x2000, length=64, is_read=False, qos=8),
            HBMRequest(addr=0x3000, length=64, is_read=True, qos=12),
        ]
        pattern.set_trace(trace_requests)

        config = TrafficConfig()
        requests = pattern.generate_requests(config, 6)

        assert len(requests) == 6
        # Should loop: req1, req2, req3, req1, req2, req3
        assert requests[0].addr == 0x1000
        assert requests[1].addr == 0x2000
        assert requests[2].addr == 0x3000
        assert requests[3].addr == 0x1000  # Looped


class TestTrafficGenerator:
    """Tests for TrafficGenerator"""

    def test_creation(self):
        """Test traffic generator creation"""
        config = TrafficConfig()
        tg = TrafficGenerator(config)
        assert tg.config == config
        assert tg._current_pattern == TrafficPattern.SYNTHETIC_FIXED_RATE

    def test_pattern_switching(self):
        """Test pattern switching"""
        tg = TrafficGenerator()
        tg.set_pattern(TrafficPattern.SYNTHETIC_RANDOM)
        assert tg._current_pattern == TrafficPattern.SYNTHETIC_RANDOM

        tg.set_pattern(TrafficPattern.SYNTHETIC_BURST)
        assert tg._current_pattern == TrafficPattern.SYNTHETIC_BURST

        stats = tg.get_stats()
        assert stats['pattern_switches'] == 2

    def test_generate_requests(self):
        """Test request generation"""
        tg = TrafficGenerator()
        tg.set_pattern(TrafficPattern.SYNTHETIC_FIXED_RATE)

        requests = tg.generate(count=50)
        assert len(requests) == 50
        for req in requests:
            assert isinstance(req, HBMRequest)

    def test_generate_ai_training(self):
        """Test AI training pattern generation"""
        tg = TrafficGenerator()

        # Weight update
        requests = tg.generate(count=10, pattern=TrafficPattern.TRAINING_WEIGHT_UPDATE)
        assert len(requests) == 10
        assert all(not r.is_read for r in requests)

        # Gradient computation
        requests = tg.generate(count=10, pattern=TrafficPattern.TRAINING_GRADIENT)
        assert len(requests) == 10
        assert all(r.is_read for r in requests)

        # Feature map
        requests = tg.generate(count=10, pattern=TrafficPattern.TRAINING_FEATURE_MAP)
        assert len(requests) == 10

    def test_generate_ai_inference(self):
        """Test AI inference pattern generation"""
        tg = TrafficGenerator()

        # Burst read
        requests = tg.generate(count=10, pattern=TrafficPattern.INFERENCE_BURST_READ)
        assert len(requests) == 10
        assert all(r.is_read for r in requests)
        assert all(r.qos == 15 for r in requests)

        # Weight reuse
        requests = tg.generate(count=50, pattern=TrafficPattern.INFERENCE_WEIGHT_REUSE)
        assert len(requests) == 50

        # Mixed precision
        tg.config.precision = DataPrecision.INT8
        requests = tg.generate(count=10, pattern=TrafficPattern.INFERENCE_MIXED_PRECISION)
        assert len(requests) == 10

    def test_statistics(self):
        """Test statistics tracking"""
        tg = TrafficGenerator()
        tg.generate(count=100)

        stats = tg.get_stats()
        assert stats['total_requests'] == 100
        assert stats['read_requests'] + stats['write_requests'] == 100
        assert stats['read_ratio'] + stats['write_ratio'] == 1.0

    def test_reset(self):
        """Test generator reset"""
        tg = TrafficGenerator()
        tg.generate(count=50)
        tg.reset()

        stats = tg.get_stats()
        assert stats['total_requests'] == 0

    def test_thread_safety(self):
        """Test thread-safe operation"""
        tg = TrafficGenerator()
        results = []

        def generate_in_thread(count):
            requests = tg.generate(count=count)
            results.append(len(requests))

        threads = [
            threading.Thread(target=generate_in_thread, args=(25,))
            for _ in range(4)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should complete without errors
        assert len(results) == 4
        assert sum(results) == 100


class TestTrafficGeneratorRunner:
    """Tests for TrafficGeneratorRunner"""

    def test_runner_creation(self):
        """Test runner creation"""
        tg = TrafficGenerator()
        submitted = []

        def mock_controller(req):
            submitted.append(req)

        runner = TrafficGeneratorRunner(tg, controller=mock_controller)
        assert runner.generator == tg
        assert runner.controller == mock_controller

    def test_rate_setting(self):
        """Test target rate setting"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.set_target_rate(1000)
        assert runner._target_rate == 1000

    def test_start_stop(self):
        """Test runner start/stop"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.start(pattern=TrafficPattern.SYNTHETIC_FIXED_RATE, batch_size=10)
        assert runner._running is True

        # Let it run briefly
        time.sleep(0.1)

        runner.stop()
        assert runner._running is False

    def test_pause_resume(self):
        """Test pause/resume"""
        tg = TrafficGenerator()
        runner = TrafficGeneratorRunner(tg)

        runner.start()
        runner.pause()
        assert runner._pause_event.is_set()

        runner.resume()
        assert not runner._pause_event.is_set()

        runner.stop()


class TestAddressPatternGenerator:
    """Tests for AddressPatternGenerator"""

    def test_creation(self):
        """Test address pattern generator creation"""
        config = TrafficConfig()
        gen = AddressPatternGenerator(config)
        assert gen.config == config
        assert gen._pattern_type == "sequential"

    def test_sequential_pattern(self):
        """Test sequential pattern"""
        config = TrafficConfig(base_address=0x1000, address_stride=64)
        gen = AddressPatternGenerator(config)
        gen.set_pattern("sequential")

        addrs = gen.next_batch(5)
        assert len(addrs) == 5
        for i in range(4):
            assert addrs[i + 1] - addrs[i] == 64

    def test_random_pattern(self):
        """Test random pattern"""
        config = TrafficConfig(base_address=0x1000, address_range=0x10000)
        gen = AddressPatternGenerator(config)
        gen.set_pattern("random")

        addrs = gen.next_batch(20)
        assert len(addrs) == 20

    def test_custom_pattern(self):
        """Test custom pattern"""
        config = TrafficConfig()
        gen = AddressPatternGenerator(config)
        custom_addrs = [0x1000, 0x2000, 0x3000, 0x4000]
        gen.set_pattern("custom", addresses=custom_addrs)

        for expected in custom_addrs:
            assert gen.next() == expected

        # Should loop
        assert gen.next() == 0x1000


class TestFactoryFunction:
    """Tests for create_traffic_generator factory function"""

    def test_create_default(self):
        """Test default factory creation"""
        tg = create_traffic_generator()
        assert isinstance(tg, TrafficGenerator)
        assert tg._current_pattern == TrafficPattern.SYNTHETIC_FIXED_RATE

    def test_create_with_params(self):
        """Test factory creation with parameters"""
        tg = create_traffic_generator(
            pattern=TrafficPattern.SYNTHETIC_RANDOM,
            read_write_ratio=0.8,
            request_rate=2e6,
        )
        assert isinstance(tg, TrafficGenerator)
        assert tg._current_pattern == TrafficPattern.SYNTHETIC_RANDOM
        assert tg.config.read_write_ratio == 0.8
        assert tg.config.request_rate == 2e6


class TestDataPrecision:
    """Tests for DataPrecision enum"""

    def test_precision_values(self):
        """Test precision enum values"""
        assert DataPrecision.FP32.value == 32
        assert DataPrecision.FP16.value == 16
        assert DataPrecision.BF16.value == 16
        assert DataPrecision.INT8.value == 8
        assert DataPrecision.INT4.value == 4


class TestTrafficPattern:
    """Tests for TrafficPattern enum"""

    def test_training_patterns(self):
        """Test training pattern values"""
        assert TrafficPattern.TRAINING_WEIGHT_UPDATE == 1
        assert TrafficPattern.TRAINING_GRADIENT == 2
        assert TrafficPattern.TRAINING_FEATURE_MAP == 3

    def test_inference_patterns(self):
        """Test inference pattern values"""
        assert TrafficPattern.INFERENCE_BURST_READ == 10
        assert TrafficPattern.INFERENCE_WEIGHT_REUSE == 11
        assert TrafficPattern.INFERENCE_MIXED_PRECISION == 12

    def test_synthetic_patterns(self):
        """Test synthetic pattern values"""
        assert TrafficPattern.SYNTHETIC_FIXED_RATE == 20
        assert TrafficPattern.SYNTHETIC_BURST == 21
        assert TrafficPattern.SYNTHETIC_RANDOM == 22
        assert TrafficPattern.SYNTHETIC_RAMP_UP == 23
        assert TrafficPattern.SYNTHETIC_RAMP_DOWN == 24
        assert TrafficPattern.SYNTHETIC_SINUSOIDAL == 25


if __name__ == '__main__':
    pytest.main([__file__, '-v'])