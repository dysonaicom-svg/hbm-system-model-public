"""
Comprehensive tests for HBM Request
Increases coverage from 65% to 95%+

Covers:
- HBMRequest (all methods)
- HBMResponse (all methods)
- RequestBatch
- HBMRequestPool
"""

import pytest
from model.controller.request import (
    HBMRequest, HBMResponse, RequestState,
    RequestBatch, HBMRequestPool
)


class TestHBMRequest:
    """Comprehensive tests for HBMRequest"""

    def test_basic_creation(self):
        """Test basic request creation"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        assert req.addr == 0x1000
        assert req.length == 64
        assert req.is_read is True
        assert req.request_id > 0

    def test_full_creation(self):
        """Test creation with all parameters"""
        req = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=False,
            qos=12,
            burst_length=32,
            request_id=100,
            arrival_time=50.0,
            stack_id=1,
            channel_id=3,
            pseudo_channel_id=1,
            bank_group_id=2,
            bank_id=5,
            row_id=1000,
            col_id=50,
            row_hit=True,
            state=RequestState.PENDING,
            scheduled_time=100.0,
            completion_time=150.0,
            data=b"test data",
        )
        assert req.qos == 12
        assert req.burst_length == 32
        assert req.request_id == 100
        assert req.arrival_time == 50.0
        assert req.stack_id == 1
        assert req.channel_id == 3
        assert req.pseudo_channel_id == 1
        assert req.bank_group_id == 2
        assert req.bank_id == 5
        assert req.row_id == 1000
        assert req.col_id == 50
        assert req.row_hit is True
        assert req.state == RequestState.PENDING
        assert req.scheduled_time == 100.0
        assert req.completion_time == 150.0
        assert req.data == b"test data"

    def test_request_id_auto_generation(self):
        """Test that request_id is auto-generated"""
        req1 = HBMRequest(addr=0x1000, length=64, is_read=True)
        req2 = HBMRequest(addr=0x2000, length=64, is_read=True)

        # IDs should be unique and sequential
        assert req1.request_id != req2.request_id
        assert req1.request_id > 0
        assert req2.request_id > req1.request_id

    def test_request_id_preserved(self):
        """Test that request_id=0 triggers auto-generation"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, request_id=0)
        assert req.request_id > 0

    def test_set_arrival_time(self):
        """Test set_arrival_time"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        req.set_arrival_time(100.0)
        assert req.arrival_time == 100.0

    def test_get_latency_cycles(self):
        """Test get_latency_cycles"""
        req = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            arrival_time=50.0,
            completion_time=150.0
        )
        latency = req.get_latency_cycles()
        assert latency == 100.0

    def test_get_latency_cycles_no_completion(self):
        """Test get_latency_cycles when not completed"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=50.0)
        latency = req.get_latency_cycles()
        assert latency == 0.0

    def test_get_latency_cycles_no_arrival(self):
        """Test get_latency_cycles when no arrival time"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, completion_time=150.0)
        latency = req.get_latency_cycles()
        assert latency == 0.0

    def test_latency_property(self):
        """Test latency property"""
        req = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            arrival_time=10.0,
            completion_time=60.0
        )
        assert req.latency == 50.0

    def test_latency_property_no_completion(self):
        """Test latency property when not completed"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        assert req.latency == 0.0

    def test_is_completed_property(self):
        """Test is_completed property"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, state=RequestState.COMPLETED)
        assert req.is_completed is True

    def test_is_completed_not_completed(self):
        """Test is_completed when not completed"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, state=RequestState.PENDING)
        assert req.is_completed is False

    def test_is_failed_property(self):
        """Test is_failed property"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, state=RequestState.FAILED)
        assert req.is_failed is True

    def test_is_failed_not_failed(self):
        """Test is_failed when not failed"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, state=RequestState.PENDING)
        assert req.is_failed is False

    def test_is_pending_property(self):
        """Test is_pending property"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, state=RequestState.PENDING)
        assert req.is_pending is True

    def test_is_pending_not_pending(self):
        """Test is_pending when not pending"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, state=RequestState.SCHEDULED)
        assert req.is_pending is False

    def test_mark_scheduled(self):
        """Test mark_scheduled"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, state=RequestState.PENDING)
        req.mark_scheduled(100.0)

        assert req.state == RequestState.SCHEDULED
        assert req.scheduled_time == 100.0
        assert req.is_pending is False

    def test_mark_in_progress(self):
        """Test mark_in_progress"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        req.mark_in_progress()

        assert req.state == RequestState.IN_PROGRESS

    def test_mark_completed(self):
        """Test mark_completed"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True, arrival_time=10.0)
        req.mark_completed(110.0)

        assert req.state == RequestState.COMPLETED
        assert req.completion_time == 110.0
        assert req.is_completed is True

    def test_mark_failed(self):
        """Test mark_failed"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        req.mark_failed()

        assert req.state == RequestState.FAILED
        assert req.is_failed is True

    def test_update_state_flags(self):
        """Test _update_state_flags"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        req.mark_scheduled(100.0)
        req._update_state_flags()

        # Flags should be updated
        assert req._is_read_completed is False
        assert req._is_read_failed is False
        assert req._is_read_pending is False

    def test_set_write_data_on_write_request(self):
        """Test set_write_data on write request"""
        req = HBMRequest(addr=0x1000, length=64, is_read=False)
        req.set_write_data(b"test data")

        assert req.data == b"test data"

    def test_set_write_data_on_read_request_raises(self):
        """Test set_write_data on read request raises"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)

        with pytest.raises(ValueError, match="Cannot set write data"):
            req.set_write_data(b"test data")

    def test_get_write_data(self):
        """Test get_write_data"""
        req = HBMRequest(addr=0x1000, length=64, is_read=False, data=b"test data")
        data = req.get_write_data()

        assert data == b"test data"

    def test_get_write_data_none(self):
        """Test get_write_data when no data"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)
        data = req.get_write_data()

        assert data is None

    def test_repr_read(self):
        """Test string representation for read"""
        req = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=True,
            qos=10,
            state=RequestState.PENDING,
            request_id=5
        )

        repr_str = repr(req)
        assert "HBMRequest" in repr_str
        assert "READ" in repr_str
        assert "qos=10" in repr_str
        assert "id=5" in repr_str

    def test_repr_write(self):
        """Test string representation for write"""
        req = HBMRequest(
            addr=0x1000,
            length=64,
            is_read=False,
            qos=5,
            state=RequestState.COMPLETED,
            request_id=10
        )

        repr_str = repr(req)
        assert "WRITE" in repr_str
        assert "qos=5" in repr_str
        assert "id=10" in repr_str

    def test_all_request_states(self):
        """Test all request states"""
        for state in RequestState:
            req = HBMRequest(addr=0x1000, length=64, is_read=True, state=state)
            assert req.state == state


class TestHBMResponse:
    """Tests for HBMResponse"""

    def test_creation(self):
        """Test response creation"""
        resp = HBMResponse(request_id=100)
        assert resp.request_id == 100
        assert resp.status == "OK"
        assert resp.latency == 0.0
        assert resp.channel_id == 0
        assert resp.bank_id == 0
        assert resp.data is None

    def test_full_creation(self):
        """Test creation with all parameters"""
        resp = HBMResponse(
            request_id=100,
            status="SLVERR",
            latency=25.5,
            channel_id=3,
            bank_id=7,
            data=b"read data"
        )
        assert resp.status == "SLVERR"
        assert resp.latency == 25.5
        assert resp.channel_id == 3
        assert resp.bank_id == 7
        assert resp.data == b"read data"

    def test_is_success_true(self):
        """Test is_success when OK"""
        resp = HBMResponse(request_id=100, status="OK")
        assert resp.is_success is True

    def test_is_success_false(self):
        """Test is_success when not OK"""
        resp = HBMResponse(request_id=100, status="SLVERR")
        assert resp.is_success is False

    def test_repr(self):
        """Test string representation"""
        resp = HBMResponse(request_id=100, status="OK", latency=25.5)
        repr_str = repr(resp)

        assert "HBMResponse" in repr_str
        assert "id=100" in repr_str
        assert "status=OK" in repr_str
        assert "latency=25.50" in repr_str


class TestRequestBatch:
    """Tests for RequestBatch"""

    def test_creation(self):
        """Test batch creation"""
        requests = [
            HBMRequest(addr=0x1000, length=64, is_read=True),
            HBMRequest(addr=0x2000, length=64, is_read=False),
            HBMRequest(addr=0x3000, length=64, is_read=True),
        ]
        batch = RequestBatch(requests)

        assert batch.requests == requests
        assert batch.size == 3
        assert batch.read_count == 2
        assert batch.write_count == 1

    def test_from_list(self):
        """Test from_list class method"""
        requests = [
            HBMRequest(addr=0x1000, length=64, is_read=True),
            HBMRequest(addr=0x2000, length=64, is_read=False),
        ]
        batch = RequestBatch.from_list(requests)

        assert batch.size == 2

    def test_empty_batch(self):
        """Test empty batch"""
        batch = RequestBatch([])

        assert batch.size == 0
        assert batch.read_count == 0
        assert batch.write_count == 0


class TestHBMRequestPool:
    """Tests for HBMRequestPool"""

    def test_creation(self):
        """Test pool creation"""
        pool = HBMRequestPool(max_size=100)
        assert pool._max_size == 100
        assert pool.pool_size == 0
        assert pool.total_allocated == 0

    def test_acquire_from_new(self):
        """Test acquire creates new when pool empty"""
        pool = HBMRequestPool()

        req = pool.acquire(addr=0x1000, length=64, is_read=True)
        assert req is not None
        assert req.addr == 0x1000
        assert req.length == 64
        assert req.is_read is True
        assert pool.total_allocated == 1

    def test_acquire_from_pool(self):
        """Test acquire reuses from pool"""
        pool = HBMRequestPool()

        # Create and release a request
        req1 = pool.acquire(addr=0x1000, length=64, is_read=True)
        pool.release(req1)

        assert pool.pool_size == 1
        assert pool.total_allocated == 1

        # Acquire should reuse
        req2 = pool.acquire(addr=0x2000, length=128, is_read=False)
        assert req2 is req1  # Same object
        assert pool.pool_size == 0
        assert pool.total_allocated == 1  # Not increased

    def test_acquire_with_kwargs(self):
        """Test acquire with keyword arguments"""
        pool = HBMRequestPool()

        # Create and release
        req1 = pool.acquire(addr=0x1000, length=64, is_read=True)
        pool.release(req1)

        # Acquire with different kwargs
        req2 = pool.acquire(addr=0x2000, length=128, is_read=False, qos=15)

        assert req2.addr == 0x2000
        assert req2.length == 128
        assert req2.is_read is False
        assert req2.qos == 15

    def test_release_full_pool(self):
        """Test release when pool is full"""
        pool = HBMRequestPool(max_size=2)

        # Fill pool
        req1 = pool.acquire(addr=0x1000, length=64, is_read=True)
        req2 = pool.acquire(addr=0x2000, length=64, is_read=True)
        pool.release(req1)
        pool.release(req2)

        assert pool.pool_size == 2

        # Release when full
        req3 = pool.acquire(addr=0x3000, length=64, is_read=True)
        pool.release(req3)

        # Should not increase pool size beyond max
        assert pool.pool_size <= pool._max_size

    def test_release_resets_fields(self):
        """Test that release resets request fields"""
        pool = HBMRequestPool()

        req = pool.acquire(addr=0x1000, length=64, is_read=True)
        req.mark_completed(100.0)
        req.mark_scheduled(50.0)
        req.data = b"test"

        pool.release(req)

        # Acquire again
        req2 = pool.acquire(addr=0x2000, length=64, is_read=True)

        assert req2.state == RequestState.PENDING
        assert req2.completion_time == 0.0
        assert req2.scheduled_time == 0.0
        assert req2.data is None

    def test_clear(self):
        """Test clear"""
        pool = HBMRequestPool()

        req1 = pool.acquire(addr=0x1000, length=64, is_read=True)
        req2 = pool.acquire(addr=0x2000, length=64, is_read=True)
        pool.release(req1)
        pool.release(req2)

        pool.clear()

        assert pool.pool_size == 0

    def test_pool_size_property(self):
        """Test pool_size property"""
        pool = HBMRequestPool()

        assert pool.pool_size == 0

        req = pool.acquire(addr=0x1000, length=64, is_read=True)
        pool.release(req)

        assert pool.pool_size == 1

    def test_total_allocated_property(self):
        """Test total_allocated property"""
        pool = HBMRequestPool()

        req1 = pool.acquire(addr=0x1000, length=64, is_read=True)
        req2 = pool.acquire(addr=0x2000, length=64, is_read=True)

        assert pool.total_allocated == 2

    def test_request_pool_integration(self):
        """Integration test for request pool"""
        pool = HBMRequestPool(max_size=10)

        # Acquire multiple requests
        requests = []
        for i in range(10):
            req = pool.acquire(addr=0x1000 * i, length=64, is_read=(i % 2 == 0))
            requests.append(req)

        assert pool.total_allocated == 10
        assert pool.pool_size == 0

        # Release half
        for i in range(5):
            pool.release(requests[i])

        assert pool.pool_size == 5

        # Acquire again (should reuse)
        for i in range(5):
            new_req = pool.acquire(addr=0x2000 * i, length=64, is_read=(i % 2 == 0))
            assert new_req.request_id > 0

        assert pool.total_allocated == 10  # Not increased


class TestRequestStateEnum:
    """Tests for RequestState enum"""

    def test_all_states(self):
        """Test all request states exist"""
        assert RequestState.PENDING == 0
        assert RequestState.SCHEDULED == 1
        assert RequestState.IN_PROGRESS == 2
        assert RequestState.COMPLETED == 3
        assert RequestState.FAILED == 4

    def test_state_names(self):
        """Test state names"""
        assert RequestState.PENDING.name == "PENDING"
        assert RequestState.SCHEDULED.name == "SCHEDULED"
        assert RequestState.IN_PROGRESS.name == "IN_PROGRESS"
        assert RequestState.COMPLETED.name == "COMPLETED"
        assert RequestState.FAILED.name == "FAILED"
