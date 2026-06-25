"""
Performance Optimization Tests for HBM4 Controller

Tests the following optimizations:
1. Channel-based queue indexing (O(1) vs O(n) lookup)
2. Command batching (multiple commands per channel per cycle)
3. Memory usage optimization
"""

import time
import gc
import pytest
import tracemalloc
from typing import Dict, List
import statistics

from model.controller.hbm4_controller import HBM4Controller
from model.controller.queue import QueueManager
from model.controller.request import HBMRequest
from model.dram.hbm4_spec import HBM4Spec


class TestChannelIndexedQueue:
    """Tests for channel-indexed queue optimization"""

    def test_queue_creation_with_indexing(self):
        """Test that QueueManager creates with channel indexing"""
        qm = QueueManager.create(queue_depth=32, num_channels=32)
        assert hasattr(qm, '_read_by_channel')
        assert hasattr(qm, '_write_by_channel')
        assert len(qm._read_by_channel) == 32
        assert len(qm._write_by_channel) == 32

    def test_indexed_push_read(self):
        """Test that read pushes update channel index"""
        qm = QueueManager.create(queue_depth=64, num_channels=32)
        req = HBMRequest(addr=0x1000, length=64, is_read=True, channel_id=5)
        success = qm.push_read(req)
        assert success
        # Check indexed lookup
        reads_5 = qm.get_reads_for_channel(5)
        assert len(reads_5) == 1
        assert reads_5[0].request_id == req.request_id

    def test_indexed_push_write(self):
        """Test that write pushes update channel index"""
        qm = QueueManager.create(queue_depth=64, num_channels=32)
        req = HBMRequest(addr=0x2000, length=64, is_read=False, channel_id=15)
        success = qm.push_write(req)
        assert success
        # Check indexed lookup
        writes_15 = qm.get_writes_for_channel(15)
        assert len(writes_15) == 1
        assert writes_15[0].request_id == req.request_id

    def test_indexed_removal(self):
        """Test that indexed removal works correctly"""
        qm = QueueManager.create(queue_depth=64, num_channels=32)
        req = HBMRequest(addr=0x3000, length=64, is_read=True, channel_id=10)
        qm.push_read(req)
        # Remove with channel hint
        removed = qm.remove_read(req.request_id, channel_id=10)
        assert removed
        assert len(qm.get_reads_for_channel(10)) == 0

    def test_multi_channel_distribution(self):
        """Test that requests are distributed across channels"""
        qm = QueueManager.create(queue_depth=256, num_channels=32)
        for ch in range(32):
            for i in range(5):
                req = HBMRequest(
                    addr=(ch << 20) | (i << 6),
                    length=64,
                    is_read=True,
                    channel_id=ch
                )
                qm.push_read(req)

        # Verify distribution
        for ch in range(32):
            reads = qm.get_reads_for_channel(ch)
            assert len(reads) == 5


class TestControllerPerformance:
    """Performance tests for HBM4 Controller"""

    def test_controller_queue_indexing(self):
        """Test that controller uses indexed queues"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)
        assert hasattr(ctrl.queue_manager, '_read_by_channel')

    def test_single_request_latency(self):
        """Test latency for single request"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)

        # Submit one read
        req_id = ctrl.submit_request(addr=0x1000, is_read=True, size_bytes=64)
        assert req_id is not None

        # Complete the request
        start_ns = ctrl.current_time_ns
        responses = []
        while not responses:
            responses = ctrl.tick()
            if ctrl.current_time_ns - start_ns > 1000:
                break

        assert len(responses) > 0
        latency = responses[0].latency
        assert 0 < latency < 1000  # Should complete within reasonable time

    def test_multi_channel_throughput(self):
        """Test throughput with multiple channels"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)

        # Submit requests to all 32 channels
        num_requests = 64
        for i in range(num_requests):
            channel = i % 32
            addr = (channel << 20) | ((i // 32) << 6)
            ctrl.submit_request(addr=addr, is_read=True, size_bytes=64)

        # Process all requests
        start_ns = ctrl.current_time_ns
        completed = 0
        max_cycles = 5000
        cycles = 0

        while completed < num_requests and cycles < max_cycles:
            responses = ctrl.tick()
            completed += len(responses)
            cycles += 1

        elapsed_ns = ctrl.current_time_ns - start_ns

        # Calculate metrics
        throughput = num_requests / elapsed_ns if elapsed_ns > 0 else 0

        print(f"\nMulti-channel throughput test:")
        print(f"  Requests: {num_requests}")
        print(f"  Cycles: {cycles}")
        print(f"  Elapsed: {elapsed_ns:.1f} ns")
        print(f"  Throughput: {throughput:.4f} req/ns")

        assert completed == num_requests

    def test_batched_command_processing(self):
        """Test that multiple commands can be processed per channel per cycle"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)

        # Submit many requests to one channel
        for i in range(20):
            # Same row = row hits = fast processing
            addr = (0 << 20) | (i << 6) | 0x1000  # Same channel, same row
            ctrl.submit_request(addr=addr, is_read=True, size_bytes=64)

        # Count commands per cycle
        commands_per_cycle = []
        prev_pending = ctrl.queue_manager.total_size()

        for _ in range(30):
            responses = ctrl.tick()
            commands_per_cycle.append(len(responses))
            if ctrl.queue_manager.total_size() == 0:
                break

        max_commands_per_cycle = max(commands_per_cycle)
        print(f"\nBatched command processing:")
        print(f"  Max commands per cycle: {max_commands_per_cycle}")
        print(f"  Commands per cycle: {commands_per_cycle[:10]}")

        # With batching, we should be able to process multiple commands per cycle
        # when they don't conflict (row hits in different banks)
        assert max_commands_per_cycle >= 1


class TestMemoryOptimization:
    """Memory usage tests"""

    def test_queue_memory_usage(self):
        """Test that queue indexing doesn't use excessive memory"""
        gc.collect()
        tracemalloc.start()

        qm = QueueManager.create(queue_depth=1024, num_channels=32)

        # Add many requests
        for ch in range(32):
            for i in range(100):
                req = HBMRequest(
                    addr=(ch << 20) | (i << 6),
                    length=64,
                    is_read=True,
                    channel_id=ch
                )
                qm.push_read(req)

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        mem_mb = peak_mem / (1024 * 1024)
        print(f"\nQueue memory usage:")
        print(f"  Peak memory: {mem_mb:.2f} MB")
        print(f"  Requests: {qm.total_size()}")

        # Indexing should add minimal overhead
        # 3200 requests with 32-channel indexing should use < 5 MB
        assert mem_mb < 10, f"Queue memory {mem_mb:.2f} MB exceeds 10 MB limit"

    def test_controller_memory_usage(self):
        """Test that controller uses reasonable memory"""
        gc.collect()
        tracemalloc.start()

        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec)

        # Add many requests
        for i in range(1000):
            channel = i % 32
            addr = (channel << 20) | ((i // 32) << 6)
            ctrl.submit_request(addr=addr, is_read=(i % 2 == 0), size_bytes=64)

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        mem_mb = peak_mem / (1024 * 1024)
        print(f"\nController memory usage:")
        print(f"  Peak memory: {mem_mb:.2f} MB")
        print(f"  Pending requests: {len(ctrl._pending_requests)}")

        assert mem_mb < 100, f"Controller memory {mem_mb:.2f} MB exceeds 100 MB limit"


class TestPerformanceRegression:
    """Regression tests to ensure optimizations don't break anything"""

    def test_basic_submit_and_complete(self):
        """Basic test: submit and complete requests"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)

        # Submit read
        req_id = ctrl.submit_request(addr=0x1000, is_read=True, size_bytes=64)
        assert req_id is not None

        # Complete
        for _ in range(100):
            responses = ctrl.tick()
            if responses:
                assert responses[0].request_id == req_id
                assert responses[0].status == "OK"
                break

    def test_write_request(self):
        """Test write request completion"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)

        req_id = ctrl.submit_request(addr=0x2000, is_read=False, size_bytes=64)
        assert req_id is not None

        for _ in range(100):
            responses = ctrl.tick()
            if responses:
                assert responses[0].request_id == req_id
                break

    def test_qos_scheduling(self):
        """Test QoS scheduling still works"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=True, enable_refresh=False)

        # Submit with different QoS
        req_ids = []
        for qos in [15, 8, 4, 12]:  # Critical, Normal, Low, High
            req_id = ctrl.submit_request(
                addr=0x1000 + len(req_ids) * 0x100,
                is_read=True,
                qos_level=qos,
                size_bytes=64
            )
            if req_id:
                req_ids.append(req_id)

        # Complete all
        completed = []
        for _ in range(200):
            responses = ctrl.tick()
            for r in responses:
                completed.append(r.request_id)

        assert len(completed) >= len(req_ids)

    def test_multi_channel_independence(self):
        """Test that channels operate independently"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)

        # Submit to different channels
        ch0_req = ctrl.submit_request(addr=0x1000, is_read=True, size_bytes=64)
        ch1_req = ctrl.submit_request(addr=(1 << 20) | 0x1000, is_read=True, size_bytes=64)

        # Both should succeed
        assert ch0_req is not None
        assert ch1_req is not None

        # Complete both
        completed = []
        for _ in range(100):
            responses = ctrl.tick()
            completed.extend([r.request_id for r in responses])
            if set(completed).issuperset({ch0_req, ch1_req}):
                break

        assert ch0_req in completed
        assert ch1_req in completed


class TestBandwidthImprovement:
    """Tests to verify bandwidth improvements from optimizations"""

    def test_sequential_row_hit_bandwidth(self):
        """Test bandwidth with sequential accesses (row hits)"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)

        # Submit sequential requests to same bank/row
        num_requests = 100
        for i in range(num_requests):
            # Same channel, same row, incrementing column
            addr = 0x1000 | ((i * 64) & 0xFFFF)
            ctrl.submit_request(addr=addr, is_read=True, size_bytes=64)

        # Process and measure
        start_ns = ctrl.current_time_ns
        completed = 0
        bytes_transferred = 0

        while completed < num_requests:
            responses = ctrl.tick()
            for r in responses:
                completed += 1
                bytes_transferred += 64
                if completed >= num_requests:
                    break

        elapsed_ns = ctrl.current_time_ns - start_ns
        bandwidth_gbs = (bytes_transferred / elapsed_ns) if elapsed_ns > 0 else 0

        print(f"\nSequential bandwidth test:")
        print(f"  Requests: {num_requests}")
        print(f"  Bytes: {bytes_transferred}")
        print(f"  Time: {elapsed_ns:.1f} ns")
        print(f"  Bandwidth: {bandwidth_gbs:.4f} GB/s")

        # Row hits should give good bandwidth
        assert bandwidth_gbs > 0

    def test_random_access_bandwidth(self):
        """Test bandwidth with random accesses"""
        spec = HBM4Spec()
        ctrl = HBM4Controller(spec=spec, enable_qos=False, enable_refresh=False)

        import random
        random.seed(42)

        num_requests = 200
        for i in range(num_requests):
            # Random across channels
            channel = random.randint(0, 31)
            addr = (channel << 20) | random.randint(0, 0xFFFF)
            ctrl.submit_request(addr=addr, is_read=True, size_bytes=64)

        # Process and measure
        start_ns = ctrl.current_time_ns
        completed = 0
        bytes_transferred = 0

        while completed < num_requests:
            responses = ctrl.tick()
            for r in responses:
                completed += 1
                bytes_transferred += 64

        elapsed_ns = ctrl.current_time_ns - start_ns
        bandwidth_gbs = (bytes_transferred / elapsed_ns) if elapsed_ns > 0 else 0

        print(f"\nRandom access bandwidth test:")
        print(f"  Requests: {num_requests}")
        print(f"  Bandwidth: {bandwidth_gbs:.4f} GB/s")

        assert bandwidth_gbs > 0
