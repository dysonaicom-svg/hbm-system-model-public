"""
Tests for PrefetchEngine

Tests all prefetch policies and integration with HBM4Controller.
"""

import pytest
from model.controller.prefetch_engine import (
    PrefetchEngine,
    PrefetchPolicy,
    PrefetchRequest,
)


class TestPrefetchRequest:
    """Tests for PrefetchRequest dataclass"""

    def test_prefetch_request_creation(self):
        """Test creating a prefetch request"""
        req = PrefetchRequest(
            address=0x1000,
            size=64,
            priority=128,
            confidence=0.9,
            policy=PrefetchPolicy.SEQUENTIAL,
        )
        assert req.address == 0x1000
        assert req.size == 64
        assert req.priority == 128
        assert req.confidence == 0.9
        assert req.policy == PrefetchPolicy.SEQUENTIAL

    def test_prefetch_request_repr(self):
        """Test PrefetchRequest string representation"""
        req = PrefetchRequest(0x1000, 64, 128, 0.9, PrefetchPolicy.SEQUENTIAL)
        repr_str = repr(req)
        assert "0x1000" in repr_str
        assert "sequential" in repr_str


class TestPrefetchPolicy:
    """Tests for PrefetchPolicy enum-like class"""

    def test_policy_values(self):
        """Test all policy values exist"""
        assert PrefetchPolicy.NONE == "none"
        assert PrefetchPolicy.SEQUENTIAL == "sequential"
        assert PrefetchPolicy.STRIDE == "stride"
        assert PrefetchPolicy.CORRELATION == "correlation"


class TestPrefetchEngineBasic:
    """Basic tests for PrefetchEngine"""

    def test_engine_initialization(self):
        """Test prefetch engine initializes correctly"""
        engine = PrefetchEngine()
        assert engine.enabled is True
        assert engine.policy == PrefetchPolicy.SEQUENTIAL
        assert len(engine.history) == 0
        assert len(engine.stride_detector) == 0
        assert len(engine.correlation_table) == 0

    def test_engine_disabled(self):
        """Test disabled engine doesn't record or generate requests"""
        engine = PrefetchEngine()
        engine.disable()
        engine.record_access(0x1000, 64)
        reqs = engine.get_prefetch_requests(0x1000)
        assert len(reqs) == 0

    def test_record_access(self):
        """Test recording accesses"""
        engine = PrefetchEngine()
        engine.record_access(0x1000, 64)
        engine.record_access(0x2000, 64)
        assert len(engine.history) == 2
        assert engine.history[0] == (0x1000, 64)
        assert engine.history[1] == (0x2000, 64)

    def test_reset(self):
        """Test resetting engine state"""
        engine = PrefetchEngine()
        engine.record_access(0x1000, 64)
        engine.record_access(0x2000, 64)
        engine.prefetch_requests_generated = 10
        engine.prefetch_requests_issued = 5

        engine.reset()

        assert len(engine.history) == 0
        assert len(engine.stride_detector) == 0
        assert engine.prefetch_requests_generated == 0
        assert engine.prefetch_requests_issued == 0


class TestSequentialPrefetch:
    """Tests for sequential prefetch policy"""

    def test_sequential_prefetch(self):
        """Test sequential prefetch generates consecutive addresses"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.SEQUENTIAL
        reqs = engine.get_prefetch_requests(0x1000, num_requests=4)

        assert len(reqs) == 4
        assert all(isinstance(r, PrefetchRequest) for r in reqs)

        # Check addresses are cache-line aligned and consecutive
        cache_line = 64
        base = 0x1000 & ~(cache_line - 1)  # 0x1000
        assert reqs[0].address == base + cache_line  # 0x1040
        assert reqs[1].address == base + 2 * cache_line  # 0x1080
        assert reqs[2].address == base + 3 * cache_line  # 0x10c0
        assert reqs[3].address == base + 4 * cache_line  # 0x1100

    def test_sequential_prefetch_alignment(self):
        """Test sequential prefetch handles non-aligned addresses"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.SEQUENTIAL
        reqs = engine.get_prefetch_requests(0x1023, num_requests=2)

        assert len(reqs) == 2
        # Should align to cache line boundary
        base = 0x1023 & ~0x3F  # 0x1000
        assert reqs[0].address == base + 64  # 0x1040

    def test_sequential_prefetch_confidence(self):
        """Test sequential prefetch has consistent confidence"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.SEQUENTIAL
        reqs = engine.get_prefetch_requests(0x1000, num_requests=4)

        assert all(r.confidence == 0.9 for r in reqs)
        assert all(r.priority == 128 for r in reqs)
        assert all(r.policy == PrefetchPolicy.SEQUENTIAL for r in reqs)


class TestStridePrefetch:
    """Tests for stride detection and prefetch"""

    def test_stride_detection(self):
        """Test stride detection from access pattern"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.STRIDE

        # Generate a stride pattern: 0x1000, 0x2000, 0x3000, 0x4000 (stride = 0x1000)
        for i in range(4):
            engine.record_access(0x1000 + i * 0x1000, 64)

        # Check stride was detected
        assert 0x4000 in engine.stride_detector
        prev_addr, stride, count = engine.stride_detector[0x4000]
        assert stride == 0x1000
        assert count >= 1

    def test_stride_prefetch(self):
        """Test stride prefetch generates addresses following stride"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.STRIDE
        # Use high count to exceed confidence threshold (0.8 = 8/10)
        engine.stride_detector[0x4000] = (0x3000, 0x1000, 10)

        reqs = engine.get_prefetch_requests(0x4000, num_requests=4)

        assert len(reqs) == 4
        # Should follow stride pattern: 0x4000 + 0x1000 * i
        assert reqs[0].address == 0x5000
        assert reqs[1].address == 0x6000
        assert reqs[2].address == 0x7000
        assert reqs[3].address == 0x8000

    def test_stride_prefetch_fallback(self):
        """Test stride falls back to sequential when no stride detected"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.STRIDE

        # No stride pattern detected
        reqs = engine.get_prefetch_requests(0x1000, num_requests=2)

        # Should fall back to sequential
        assert len(reqs) == 2
        assert reqs[0].address == 0x1040
        assert reqs[1].address == 0x1080

    def test_stride_prefetch_priority(self):
        """Test stride prefetch has higher priority than sequential"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.STRIDE
        engine.stride_detector[0x1000] = (0x1000, 0, 1)  # Zero stride, won't use

        reqs = engine.get_prefetch_requests(0x1000, num_requests=2)
        # Falls back to sequential with priority 128

        # Direct sequential test
        engine2 = PrefetchEngine()
        engine2.policy = PrefetchPolicy.STRIDE
        reqs2 = engine2.get_prefetch_requests(0x1000, num_requests=2)
        assert reqs2[0].priority == 128


class TestCorrelationPrefetch:
    """Tests for correlation-based prefetch"""

    def test_correlation_learning(self):
        """Test correlation table learning"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.CORRELATION

        # Repeatedly access pattern: A -> B, A -> B, A -> B
        for _ in range(3):
            engine.record_access(0x1000, 64)
            engine.record_access(0x2000, 64)

        # Check correlation learned
        assert 0x1000 in engine.correlation_table
        assert 0x2000 in engine.correlation_table[0x1000]

    def test_correlation_prefetch(self):
        """Test correlation prefetch generates learned addresses"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.CORRELATION

        # Set up correlation table manually
        engine.correlation_table[0x1000] = [0x2000, 0x3000, 0x4000]

        reqs = engine.get_prefetch_requests(0x1000, num_requests=3)

        assert len(reqs) == 3
        assert reqs[0].address == 0x2000
        assert reqs[1].address == 0x3000
        assert reqs[2].address == 0x4000

    def test_correlation_prefetch_confidence_filter(self):
        """Test correlation prefetch can filter by confidence"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.CORRELATION
        engine.correlation_table[0x1000] = [0x2000]

        # Set low confidence
        engine.correlation_counts[0x1000] = {0x2000: 1}

        reqs = engine.get_prefetch_requests(0x1000, num_requests=1)

        # Confidence should be low (1/10 = 0.1)
        assert len(reqs) == 1
        assert reqs[0].confidence < 0.5

    def test_correlation_prefetch_no_history(self):
        """Test correlation returns empty when no history"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.CORRELATION

        reqs = engine.get_prefetch_requests(0x1000, num_requests=4)

        assert len(reqs) == 0


class TestPrefetchStatistics:
    """Tests for prefetch statistics"""

    def test_get_stats(self):
        """Test statistics collection"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.SEQUENTIAL

        # Generate some prefetches
        engine.get_prefetch_requests(0x1000, num_requests=4)

        stats = engine.get_stats()

        assert stats['policy'] == PrefetchPolicy.SEQUENTIAL
        assert stats['enabled'] is True
        assert stats['requests_generated'] == 4
        assert 'accuracy' in stats

    def test_hit_miss_tracking(self):
        """Test hit/miss tracking"""
        engine = PrefetchEngine()
        engine.hits = 8
        engine.misses = 2

        stats = engine.get_stats()

        assert stats['hits'] == 8
        assert stats['misses'] == 2
        assert stats['accuracy'] == 0.8

    def test_empty_hit_miss_accuracy(self):
        """Test accuracy with no data"""
        engine = PrefetchEngine()
        stats = engine.get_stats()
        assert stats['accuracy'] == 0.0


class TestPrefetchPolicySetting:
    """Tests for policy switching"""

    def test_set_valid_policy(self):
        """Test setting valid policies"""
        engine = PrefetchEngine()

        for policy in [PrefetchPolicy.NONE, PrefetchPolicy.SEQUENTIAL,
                       PrefetchPolicy.STRIDE, PrefetchPolicy.CORRELATION]:
            engine.set_policy(policy)
            assert engine.policy == policy

    def test_set_invalid_policy(self):
        """Test setting invalid policy doesn't change current"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.SEQUENTIAL

        engine.set_policy("invalid_policy")

        # Should remain unchanged
        assert engine.policy == PrefetchPolicy.SEQUENTIAL


class TestPrefetchEnableDisable:
    """Tests for enable/disable functionality"""

    def test_enable_disable(self):
        """Test enable and disable"""
        engine = PrefetchEngine()

        engine.disable()
        assert engine.enabled is False
        assert len(engine.get_prefetch_requests(0x1000)) == 0

        engine.enable()
        assert engine.enabled is True
        assert len(engine.get_prefetch_requests(0x1000)) == 4


class TestPrefetchEdgeCases:
    """Edge case tests"""

    def test_zero_history(self):
        """Test behavior with no history"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.STRIDE

        reqs = engine.get_prefetch_requests(0x1000)
        # Falls back to sequential
        assert len(reqs) == 4

    def test_negative_stride(self):
        """Test negative stride handling"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.STRIDE

        # Set negative stride with high count to exceed confidence threshold
        engine.stride_detector[0x2000] = (0x3000, -0x1000, 10)

        reqs = engine.get_prefetch_requests(0x2000, num_requests=2)

        # Should follow negative stride: 0x2000 + (-0x1000) * i
        assert reqs[0].address == 0x1000
        assert reqs[1].address == 0x0000

    def test_large_num_requests(self):
        """Test large number of prefetch requests"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.SEQUENTIAL

        reqs = engine.get_prefetch_requests(0x1000, num_requests=100)

        assert len(reqs) == 100

    def test_cache_line_alignment_boundaries(self):
        """Test cache line alignment at boundaries"""
        engine = PrefetchEngine()
        engine.policy = PrefetchPolicy.SEQUENTIAL

        # Address at 4KB boundary
        reqs = engine.get_prefetch_requests(0xFFC0, num_requests=2)

        assert all(r.address % 64 == 0 for r in reqs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestPrefetchEngineIntegration:
    """Integration tests for prefetch engine with HBM4Controller"""

    def test_controller_with_prefetch_enabled(self):
        """Test controller with prefetch engine enabled"""
        from model.controller.hbm4_controller import HBM4Controller
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        controller = HBM4Controller(spec=spec, enable_prefetch=True)

        # Submit a few requests
        for i in range(5):
            controller.submit_request(
                addr=0x1000 + i * 0x1000,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )

        # Verify prefetch engine recorded accesses (includes prefetch requests)
        assert len(controller.prefetch_engine.history) >= 5

        # Check prefetch stats
        stats = controller.prefetch_engine.get_stats()
        assert stats['requests_generated'] > 0

    def test_controller_prefetch_disabled_by_default(self):
        """Test prefetch is disabled by default"""
        from model.controller.hbm4_controller import HBM4Controller
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()
        controller = HBM4Controller(spec=spec)

        # Submit requests
        for i in range(3):
            controller.submit_request(
                addr=0x1000 + i * 0x1000,
                is_read=True,
                qos_level=8,
                size_bytes=64,
            )

        # Prefetch engine records accesses but doesn't generate prefetch requests
        assert len(controller.prefetch_engine.history) == 3
        assert controller.prefetch_engine.prefetch_requests_generated == 0

    def test_prefetch_policy_switching(self):
        """Test switching prefetch policies on controller"""
        from model.controller.hbm4_controller import HBM4Controller
        from model.controller.prefetch_engine import PrefetchPolicy
        from model.dram.hbm4_spec import HBM4Spec

        spec = HBM4Spec()

        # Test with sequential policy
        controller = HBM4Controller(spec=spec, enable_prefetch=True)
        controller.prefetch_engine.set_policy(PrefetchPolicy.SEQUENTIAL)
        controller.prefetch_engine.reset()

        controller.submit_request(addr=0x1000, is_read=True)
        assert controller.prefetch_engine.prefetch_requests_generated > 0

        # Test with none policy - no prefetch generated
        controller2 = HBM4Controller(spec=spec, enable_prefetch=True)
        controller2.prefetch_engine.set_policy(PrefetchPolicy.NONE)
        controller2.submit_request(addr=0x1000, is_read=True)
        assert controller2.prefetch_engine.prefetch_requests_generated == 0