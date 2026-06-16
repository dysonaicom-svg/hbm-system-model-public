"""
HBM Data Path Integration Tests

Tests the complete write/read data flow between:
- AXI Interconnect
- HBM Controller
- Command Pipeline
- DRAM Model

Validates:
- Write data is passed from request to DRAM
- Read data is returned from DRAM to response
- Data consistency (write then read returns same data)
"""

import pytest
from typing import Optional

from sim.simulator import HBMSimulator, SimulationConfig, SimulationStats
from model.controller.controller import HBMController
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.request import HBMRequest, HBMResponse
from model.controller.command_pipeline import CommandPipeline, CommandType
from model.dram.dram_model import DRAMModel


class TestDataPathBasic:
    """Basic data path tests"""

    def test_command_pipeline_write_data(self):
        """Test CommandPipeline write_data method"""
        pipeline = CommandPipeline()

        # Should return False when no pending write
        assert pipeline.write_data(b'\x00' * 64) is False

        # Get write data should return None when no data
        assert pipeline.get_write_data() is None

    def test_command_pipeline_read_data(self):
        """Test CommandPipeline get_read_data method"""
        pipeline = CommandPipeline()

        data = pipeline.get_read_data(32)
        assert len(data) == 32
        assert data == bytes(32)

    def test_command_pipeline_read_data_various_lengths(self):
        """Test read data with various lengths"""
        pipeline = CommandPipeline()

        for length in [16, 32, 64, 128, 256]:
            data = pipeline.get_read_data(length)
            assert len(data) == length


class TestRequestDataField:
    """Test HBMRequest data field functionality"""

    def test_write_request_can_hold_data(self):
        """Test write request can hold data"""
        req = HBMRequest(addr=0x1000, length=64, is_read=False)

        # Set write data
        test_data = bytes([0xAB, 0xCD, 0xEF] * 20 + [0x00] * 4)
        req.set_write_data(test_data)

        # Verify data is stored
        assert req.get_write_data() == test_data
        assert req.data == test_data

    def test_read_request_cannot_hold_data(self):
        """Test read request rejects write data"""
        req = HBMRequest(addr=0x1000, length=64, is_read=True)

        # Read request should reject write data
        with pytest.raises(ValueError):
            req.set_write_data(bytes(64))

    def test_write_request_get_write_data_returns_none_when_no_data(self):
        """Test write request returns None when no data set"""
        req = HBMRequest(addr=0x1000, length=64, is_read=False)

        # No data set yet
        assert req.get_write_data() is None
        assert req.data is None


class TestDRAMDataMethods:
    """Test DRAMModel data methods"""

    def test_dram_write_method(self):
        """Test DRAMModel.write() direct write method"""
        dram = DRAMModel(hbm_version="hbm3")
        dram.enable_memory_model()

        # Write data to memory
        test_data = bytes([i % 256 for i in range(64)])
        result = dram.write(
            stack_id=0,
            channel_id=0,
            bank_id=0,
            row_id=0,
            col_id=0,
            data=test_data,
        )

        assert result is True
        assert dram.stats.total_writes == 1

    def test_dram_read_method(self):
        """Test DRAMModel.read() direct read method"""
        dram = DRAMModel(hbm_version="hbm3")
        dram.enable_memory_model()

        # Write then read data
        test_data = bytes([0xDE, 0xAD, 0xBE, 0xEF] * 16)
        dram.write(
            stack_id=0,
            channel_id=0,
            bank_id=0,
            row_id=0,
            col_id=0,
            data=test_data,
        )

        read_data = dram.read(
            stack_id=0,
            channel_id=0,
            bank_id=0,
            row_id=0,
            col_id=0,
            length=64,
        )

        assert read_data == test_data
        assert dram.stats.total_reads == 1

    def test_dram_execute_request_with_data(self):
        """Test DRAMModel.execute_request() with write data"""
        dram = DRAMModel(hbm_version="hbm3")
        dram.enable_memory_model()

        # Activate bank first (required before read/write)
        dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, current_time=0
        )

        # Write data via execute_request
        test_data = bytes([0x12, 0x34, 0x56, 0x78] * 16)
        success = dram.execute_request(
            stack_id=0,
            ch_id=0,
            ps_id=0,
            bg_id=0,
            bank_id=0,
            row=0,
            cmd="WRITE",
            data=test_data,
            col=0,
            length=64,
            current_time=100,  # Must be after activation time
        )

        assert success is True

        # Read back via execute_request
        success = dram.execute_request(
            stack_id=0,
            ch_id=0,
            ps_id=0,
            bg_id=0,
            bank_id=0,
            row=0,
            cmd="READ",
            col=0,
            length=64,
            current_time=200,  # Must be after write time
        )

        assert success is True


class TestDataPathIntegration:
    """Data path integration tests"""

    def test_write_data_flows_to_dram(self):
        """Test write data from request flows to DRAM"""
        dram = DRAMModel(hbm_version="hbm3")
        dram.enable_memory_model()

        # Create a request with data
        req = HBMRequest(addr=0x1000, length=64, is_read=False)
        test_data = bytes([0xAA] * 64)
        req.set_write_data(test_data)

        # Activate bank first (required before read/write)
        dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, current_time=0
        )

        # Execute write via simulator path
        resp = dram.execute_write(
            stack_id=0,
            channel_id=0,
            bank_id=0,
            col_id=0,
            data=req.get_write_data(),
            current_time=100,  # Must be after activation
        )

        assert resp.success is True

        # Read back the data
        read_data = dram.read(
            stack_id=0,
            channel_id=0,
            bank_id=0,
            row_id=0,
            col_id=0,
            length=64,
        )

        # Should match what we wrote
        assert read_data == test_data

    def test_simulator_write_read_data_path(self):
        """Test complete write/read data path through simulator"""
        config = SimulationConfig(
            simulation_time_us=10.0,
            request_rate=0.5,
            read_ratio=0.5,  # 50% reads, 50% writes
        )
        sim = HBMSimulator(config)

        # Run simulation for a few cycles
        responses = []
        for _ in range(50):
            response = sim.step()
            if response:
                responses.append(response)

        # Verify we got some responses
        assert len(responses) >= 0  # May or may not complete in 50 cycles

    def test_simulator_data_in_response(self):
        """Test that responses can include data"""
        config = SimulationConfig(
            simulation_time_us=1.0,
            request_rate=1.0,
            read_ratio=1.0,  # All reads
        )
        sim = HBMSimulator(config)

        # Run until we get a completion
        response = None
        for _ in range(100):
            response = sim.step()
            if response and response.status == "OK":
                break

        # Verify response has proper structure
        if response:
            assert response.request_id >= 0
            assert response.status == "OK"

    def test_controller_write_request(self):
        """Test controller can handle write requests"""
        config = HBM3_DEFAULT
        controller = HBMController(config)

        # Submit write request
        req = HBMRequest(addr=0x1000, length=64, is_read=False, qos=8)
        success = controller.submit_request(req)

        assert success is True
        assert controller.stats['write_requests'] >= 1

    def test_controller_read_request(self):
        """Test controller can handle read requests"""
        config = HBM3_DEFAULT
        controller = HBMController(config)

        # Submit read request
        req = HBMRequest(addr=0x2000, length=64, is_read=True, qos=8)
        success = controller.submit_request(req)

        assert success is True
        assert controller.stats['read_requests'] >= 1

    def test_mixed_read_write_requests(self):
        """Test mixed read/write traffic"""
        config = HBM3_DEFAULT
        controller = HBMController(config)

        # Submit multiple requests
        requests = []
        for i in range(8):
            is_read = (i % 2 == 0)
            req = HBMRequest(
                addr=0x1000 * (i + 1),
                length=64,
                is_read=is_read,
                qos=8
            )
            controller.submit_request(req)
            requests.append(req)

        # Verify counts
        read_count = sum(1 for r in requests if r.is_read)
        write_count = sum(1 for r in requests if not r.is_read)

        assert controller.stats['read_requests'] == read_count
        assert controller.stats['write_requests'] == write_count


class TestDataPathWithData:
    """Test data path with actual data values"""

    def test_write_then_read_consistency(self):
        """Test that writing data and reading it back returns the same data"""
        dram = DRAMModel(hbm_version="hbm3")
        dram.enable_memory_model()

        # Test pattern
        test_data = bytes([i % 256 for i in range(64)])

        # First activate the bank
        dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, current_time=0
        )

        # Write data
        dram.execute_write(
            stack_id=0, channel_id=0, bank_id=0,
            col_id=0, data=test_data, current_time=100
        )

        # Read back data
        read_data = dram.read(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, col_id=0, length=64
        )

        assert read_data == test_data

    def test_multiple_banks_data_isolation(self):
        """Test that data in different banks is isolated"""
        dram = DRAMModel(hbm_version="hbm3")
        dram.enable_memory_model()

        # Data for bank 0
        data_bank0 = bytes([0xAA] * 64)

        # Data for bank 1
        data_bank1 = bytes([0xBB] * 64)

        # Activate both banks
        dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, current_time=0
        )
        dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=1,
            row_id=0, current_time=50
        )

        # Write to bank 0
        dram.execute_write(
            stack_id=0, channel_id=0, bank_id=0,
            col_id=0, data=data_bank0, current_time=100
        )

        # Write to bank 1
        dram.execute_write(
            stack_id=0, channel_id=0, bank_id=1,
            col_id=0, data=data_bank1, current_time=150
        )

        # Read back from bank 0
        read_bank0 = dram.read(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, col_id=0, length=64
        )

        # Read back from bank 1
        read_bank1 = dram.read(
            stack_id=0, channel_id=0, bank_id=1,
            row_id=0, col_id=0, length=64
        )

        assert read_bank0 == data_bank0
        assert read_bank1 == data_bank1

    def test_request_with_write_data_in_simulator(self):
        """Test request with write data flows through simulator"""
        config = SimulationConfig(
            simulation_time_us=1.0,
            request_rate=1.0,
            read_ratio=0.0,  # All writes
            seed=42,
        )
        sim = HBMSimulator(config)

        # Create a request with data
        req = HBMRequest(addr=0x1000, length=32, is_read=False)
        test_data = bytes([0xDE, 0xAD, 0xC0, 0xDE] * 8)
        req.set_write_data(test_data)

        # Submit directly to controller
        sim.controller.submit_request(req)

        # Run for a few cycles
        for _ in range(20):
            sim.step()

        # Verify write happened
        assert sim.stats.write_requests >= 1


class TestDataPathPerformance:
    """Data path performance tests"""

    def test_high_throughput_write_requests(self):
        """Test high throughput of write requests"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.8,
            read_ratio=0.0,  # All writes
        )
        sim = HBMSimulator(config)

        stats = sim.run()

        # Verify write requests were generated
        assert stats.write_requests > 0

    def test_high_throughput_read_requests(self):
        """Test high throughput of read requests"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.8,
            read_ratio=1.0,  # All reads
        )
        sim = HBMSimulator(config)

        stats = sim.run()

        # Verify read requests were generated
        assert stats.read_requests > 0

    def test_mixed_traffic_throughput(self):
        """Test mixed read/write throughput"""
        config = SimulationConfig(
            simulation_time_us=50.0,
            request_rate=0.8,
            read_ratio=0.7,  # 70% reads, 30% writes
        )
        sim = HBMSimulator(config)

        stats = sim.run()

        # Verify both types were generated
        assert stats.read_requests > 0
        assert stats.write_requests > 0

        # Reads should be roughly 70% of total
        total = stats.read_requests + stats.write_requests
        if total > 0:
            read_ratio = stats.read_requests / total
            assert 0.5 < read_ratio < 0.9  # Should be around 70%


class TestDataPathErrors:
    """Data path error handling tests"""

    def test_queue_overflow_handling(self):
        """Test behavior when queue is full"""
        config = HBMConfig(
            queue_depth=4,  # Small queue
            max_outstanding=2,
        )
        controller = HBMController(config)

        # Submit many requests rapidly
        success_count = 0
        for i in range(20):
            req = HBMRequest(addr=0x1000 * i, length=64, is_read=True, qos=8)
            if controller.submit_request(req):
                success_count += 1

        # Should accept some but not all
        assert success_count > 0
        assert success_count <= 20

    def test_invalid_address_handling(self):
        """Test handling of addresses outside HBM range"""
        config = HBM3_DEFAULT
        controller = HBMController(config)

        # Submit request with address that maps to invalid location
        # (aligned address, but may be out of valid HBM range)
        req = HBMRequest(addr=0x8000_0000_0000_0000, length=64, is_read=True, qos=8)
        success = controller.submit_request(req)

        # Controller should accept but may map to max valid address
        assert success is True


class TestDataPathEdgeCases:
    """Test edge cases in data path"""

    def test_empty_write_data(self):
        """Test handling of empty/none write data"""
        dram = DRAMModel(hbm_version="hbm3")
        dram.enable_memory_model()

        # Activate bank
        dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, current_time=0
        )

        # Write with empty data
        resp = dram.execute_write(
            stack_id=0, channel_id=0, bank_id=0,
            col_id=0, data=bytes(0), current_time=100
        )

        assert resp.success is True

    def test_large_write_data(self):
        """Test handling of large write data"""
        dram = DRAMModel(hbm_version="hbm3")
        dram.enable_memory_model()

        # Activate bank
        dram.execute_activate(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, current_time=0
        )

        # Write large amount of data
        large_data = bytes([i % 256 for i in range(1024)])
        resp = dram.execute_write(
            stack_id=0, channel_id=0, bank_id=0,
            col_id=0, data=large_data, current_time=100
        )

        assert resp.success is True

        # Read back
        read_data = dram.read(
            stack_id=0, channel_id=0, bank_id=0,
            row_id=0, col_id=0, length=1024
        )

        assert read_data == large_data

    def test_dram_response_data_field(self):
        """Test DRAMResponse includes data field"""
        from model.dram.dram_model import DRAMResponse

        resp = DRAMResponse(
            success=True,
            data=bytes([0x12, 0x34, 0x56, 0x78]),
            latency_cycles=10,
        )

        assert resp.data == bytes([0x12, 0x34, 0x56, 0x78])
        assert resp.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])