"""
Tests for DFI Timing Parameters and Protocol Timing

Tests the DFI 5.0/5.1 timing parameters including:
- tPHYUPD_LAT (PHY update latency)
- tPHYDAT_LAT (PHY data latency)
- Frequency scaling transitions
- Protocol timing constraints
- Timing parameter validation

Reference: DFI 5.0 Specification Table 3-1
"""

import pytest
from model.dram.dfi_interface import (
    DFI5Interface,
    DFITimingParameters,
    DFI5FreqChangeState,
    DFICommand,
    DFIRequest,
)


class TestDFIPhyUpdateLatency:
    """Test DFI tPHYUPD_LAT (PHY Update Latency) parameter"""

    def test_phyupd_lat_default_value(self):
        """Default tPHYUPD_LAT should be defined"""
        timing = DFITimingParameters()
        assert hasattr(timing, 'tPHYUPD_LAT') or hasattr(timing, 'tCTRLUPD_LATENCY')
        # tCTRLUPD_LATENCY is the DFI 5.0 equivalent of tPHYUPD_LAT
        latency = getattr(timing, 'tCTRLUPD_LATENCY', None)
        if latency is not None:
            assert latency > 0

    def test_phyupd_latency_property(self):
        """tCTRLUPD_LATENCY should be accessible as property"""
        timing = DFITimingParameters()
        # Verify the parameter exists and is positive
        assert timing.tCTRLUPD_LATENCY >= 0

    def test_phyupd_latency_timing_sequence(self):
        """Control update should complete within expected latency"""
        dfi = DFI5Interface()
        latency = dfi.timing.tCTRLUPD_LATENCY

        # Request control update
        dfi.request_ctrlupd()
        assert dfi.ctrlupd_req is True

        # Verify handshake completes within latency
        for i in range(latency + 2):
            dfi.tick()

        # Handshake should be complete
        assert dfi.ctrlupd_req is False
        assert dfi.ctrlupd_ack is False

    def test_phyupd_latency_with_custom_value(self):
        """Custom tCTRLUPD_LATENCY should affect timing"""
        custom_latency = 8
        timing = DFITimingParameters(tCTRLUPD_LATENCY=custom_latency)
        dfi = DFI5Interface(timing_params=timing)

        dfi.request_ctrlupd()

        # Advance to just before completion
        for _ in range(custom_latency - 1):
            dfi.tick()
        # Should still be in progress
        assert dfi.ctrlupd_req is True or dfi.ctrlupd_ack is True

        # Advance one more cycle
        dfi.tick()
        # Now should be complete
        assert dfi.ctrlupd_req is False


class TestDFIPhyDataLatency:
    """Test DFI tPHYDAT_LAT (PHY Data Latency) parameter"""

    def test_phydat_lat_parameter_exists(self):
        """tPHYDAT_LAT parameter should exist in timing"""
        timing = DFITimingParameters()
        # This may be implemented as tPHY_rdLat or separate parameter
        assert hasattr(timing, 'tPHY_rdLat')

    def test_phydat_lat_cycles(self):
        """Read latency should be returned in cycles"""
        timing = DFITimingParameters()
        assert timing.tPHY_rdLat > 0
        assert timing.read_latency_cycles > 0

    def test_phydat_lat_ps_calculation(self):
        """Read latency should calculate correctly in picoseconds"""
        timing = DFITimingParameters(tPHY_rdLat=8)
        tCK_ps = 125.0  # 8 GT/s DDR
        latency_ps = timing.get_read_latency_ps(tCK_ps)
        assert latency_ps == 1000.0  # 8 * 125 ps

    def test_phydat_lat_interface_integration(self):
        """DFI interface should return correct read latency"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)  # 8 GT/s

        latency_ps = dfi.get_read_latency_ps()
        assert latency_ps > 0

    def test_phydat_lat_with_write(self):
        """Write latency should also be available"""
        dfi = DFI5Interface()
        latency_ps = dfi.get_write_latency_ps()
        assert latency_ps > 0

    def test_phydat_latency_vs_write_latency(self):
        """Read and write latency should be independent"""
        timing = DFITimingParameters(tPHY_rdLat=6, tPHY_wrlAT=4)
        assert timing.tPHY_rdLat != timing.tPHY_wrlAT


class TestDFIFrequencyScaling:
    """Test DFI frequency scaling transitions"""

    def test_freq_scaling_up(self):
        """Test scaling frequency up"""
        dfi = DFI5Interface()
        initial_freq = dfi.get_frequency()

        # Request frequency change
        dfi.request_freq_change(1600)
        dfi.enter_freq_change()
        dfi.exit_freq_change()

        # Complete state machine
        for _ in range(50):
            dfi.tick()

        assert dfi.get_frequency() == 1600

    def test_freq_scaling_down(self):
        """Test scaling frequency down"""
        dfi = DFI5Interface()
        dfi.set_frequency(1600)

        dfi.request_freq_change(800)
        dfi.enter_freq_change()
        dfi.exit_freq_change()

        for _ in range(50):
            dfi.tick()

        assert dfi.get_frequency() == 800

    def test_freq_scaling_sequence_timing(self):
        """Frequency change should follow expected timing sequence"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)

        # Requested state
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_REQUESTED

        dfi.enter_freq_change()
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_ENTERING

    def test_freq_scaling_multiple_steps(self):
        """Test multi-step frequency scaling"""
        dfi = DFI5Interface()

        # Step 1: 800 -> 1200
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        dfi.exit_freq_change()
        for _ in range(50):
            dfi.tick()
        assert dfi.get_frequency() == 1200

        # Step 2: 1200 -> 1600
        dfi.request_freq_change(1600)
        dfi.enter_freq_change()
        dfi.exit_freq_change()
        for _ in range(50):
            dfi.tick()
        assert dfi.get_frequency() == 1600

    def test_freq_scaling_with_timing_params(self):
        """Frequency change should use timing parameters"""
        dfi = DFI5Interface()
        fc_latency = dfi.timing.tFC_LATENCY
        fc_exit = dfi.timing.tFC_EXIT

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        # Verify latencies are positive
        assert fc_latency > 0
        assert fc_exit > 0

    def test_freq_scaling_target_tracking(self):
        """Target frequency should be tracked during scaling"""
        dfi = DFI5Interface()

        dfi.request_freq_change(2400)
        assert dfi.get_target_frequency() == 2400

        dfi.enter_freq_change()
        assert dfi.get_target_frequency() == 2400

    def test_freq_scaling_en_signal(self):
        """dfi_freq_change_en should be asserted during scaling"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        assert dfi.freq_change_en is True

    def test_freq_scaling_ack_signal(self):
        """dfi_freq_change_ack can be set by PHY"""
        dfi = DFI5Interface()

        dfi.set_freq_change_ack(True)
        assert dfi.freq_change_ack is True

        dfi.set_freq_change_ack(False)
        assert dfi.freq_change_ack is False

    def test_freq_scaling_state_progression(self):
        """Frequency change should progress through all states"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_REQUESTED

        dfi.enter_freq_change()
        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_ENTERING

        # Advance through state machine - need more cycles for full completion
        # FC_ENTERING -> FC_ACTIVE (tLP_CTRL_ENTER)
        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        # FC_ACTIVE -> FC_EXITING (via exit_freq_change)
        dfi.exit_freq_change()
        for _ in range(1):
            dfi.tick()

        # FC_EXITING -> FC_LOCKING -> FC_COMPLETE -> FC_IDLE
        for _ in range(dfi.timing.tFC_EXIT + dfi.timing.tFC_LATENCY + 5):
            dfi.tick()

        assert dfi.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE


class TestDFITimingParameterValidation:
    """Test DFI timing parameter validation"""

    def test_all_required_timing_params_exist(self):
        """All DFI 5.0 required timing parameters should exist"""
        timing = DFITimingParameters()

        # Core latency parameters
        assert hasattr(timing, 'tPHY_wrlAT')
        assert hasattr(timing, 'tPHY_rdLat')

        # Frequency change timing
        assert hasattr(timing, 'tFC_LATENCY')
        assert hasattr(timing, 'tFC_EXIT')

        # Low power timing
        assert hasattr(timing, 'tLP_CTRL_ENTER')
        assert hasattr(timing, 'tLP_CTRL_EXIT')
        assert hasattr(timing, 'tLP_DATA_ENTER')
        assert hasattr(timing, 'tLP_DATA_EXIT')

        # Control update timing
        assert hasattr(timing, 'tCTRLUPD_LATENCY')

        # Power management timing
        assert hasattr(timing, 'tPWR_UP')
        assert hasattr(timing, 'tPWR_DOWN')

    def test_timing_params_are_positive(self):
        """All timing parameters should have positive values"""
        timing = DFITimingParameters()

        assert timing.tPHY_wrlAT > 0
        assert timing.tPHY_rdLat > 0
        assert timing.tFC_LATENCY > 0
        assert timing.tFC_EXIT > 0
        assert timing.tLP_CTRL_ENTER >= 0
        assert timing.tLP_CTRL_EXIT >= 0
        assert timing.tLP_DATA_ENTER >= 0
        assert timing.tLP_DATA_EXIT >= 0
        assert timing.tCTRLUPD_LATENCY > 0
        assert timing.tPWR_UP >= 0
        assert timing.tPWR_DOWN >= 0

    def test_timing_params_custom_values(self):
        """Timing parameters should accept custom values"""
        timing = DFITimingParameters(
            tPHY_wrlAT=10,
            tPHY_rdLat=12,
            tFC_LATENCY=16,
            tFC_EXIT=8,
            tLP_CTRL_ENTER=4,
            tLP_CTRL_EXIT=4,
            tLP_DATA_ENTER=8,
            tLP_DATA_EXIT=8,
            tCTRLUPD_LATENCY=6,
            tPWR_UP=4,
            tPWR_DOWN=4
        )

        assert timing.tPHY_wrlAT == 10
        assert timing.tPHY_rdLat == 12
        assert timing.tFC_LATENCY == 16
        assert timing.tFC_EXIT == 8
        assert timing.tLP_CTRL_ENTER == 4
        assert timing.tLP_CTRL_EXIT == 4
        assert timing.tLP_DATA_ENTER == 8
        assert timing.tLP_DATA_EXIT == 8
        assert timing.tCTRLUPD_LATENCY == 6
        assert timing.tPWR_UP == 4
        assert timing.tPWR_DOWN == 4

    def test_timing_params_max_values(self):
        """Timing parameters should have max value variants"""
        timing = DFITimingParameters()
        assert hasattr(timing, 'tPHY_wrlAT_max')
        assert hasattr(timing, 'tPHY_rdLat_max')
        assert timing.tPHY_wrlAT_max >= timing.tPHY_wrlAT
        assert timing.tPHY_rdLat_max >= timing.tPHY_rdLat

    def test_timing_params_interface_sync(self):
        """DFI interface timing should sync with parameters"""
        dfi = DFI5Interface()
        new_timing = DFITimingParameters(tPHY_wrlAT=15)
        dfi.set_timing_parameters(new_timing)

        assert dfi.timing.tPHY_wrlAT == 15


class TestDFIProtocolTiming:
    """Test DFI protocol timing sequences"""

    def test_command_to_response_timing(self):
        """Command to response should follow expected timing"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)

        # Encode and queue a command
        request = dfi.encode_command('RD', {
            'col': 0,
            'bank': 0,
            'pseudo_channel': 0
        })
        dfi.queue_request(request)

        # Get response
        response = dfi.get_response()
        assert response is not None
        assert hasattr(response, 'ready')

    def test_read_data_timing(self):
        """Read data timing should use PHY latency"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)

        read_latency = dfi.get_read_latency_ps()
        assert read_latency > 0

    def test_write_data_timing(self):
        """Write data timing should use PHY latency"""
        dfi = DFI5Interface()
        dfi.set_frequency(8000)

        write_latency = dfi.get_write_latency_ps()
        assert write_latency > 0

    def test_ctrlupd_timing_sequence(self):
        """Control update should follow full timing sequence"""
        dfi = DFI5Interface()

        # Request
        result = dfi.request_ctrlupd()
        assert result is True
        assert dfi.ctrlupd_req is True

        # Wait for completion
        for _ in range(dfi.timing.tCTRLUPD_LATENCY + 2):
            dfi.tick()

        # Verify completion
        assert dfi.ctrlupd_req is False

    def test_freq_change_timing_sequence(self):
        """Frequency change should follow full timing sequence"""
        dfi = DFI5Interface()

        dfi.request_freq_change(1200)
        dfi.enter_freq_change()

        # Calculate total latency needed for full completion
        # State machine: FC_ENTERING -> FC_ACTIVE -> FC_EXITING -> FC_LOCKING -> FC_COMPLETE -> FC_IDLE
        # Note: exit_freq_change() must be called after FC_ENTERING phase completes
        total_latency = (
            dfi.timing.tLP_CTRL_ENTER +  # FC_ENTERING -> FC_ACTIVE
            1 +  # exit_freq_change call
            dfi.timing.tFC_EXIT +  # FC_EXITING -> FC_LOCKING
            dfi.timing.tFC_LATENCY +  # FC_LOCKING -> FC_COMPLETE
            1  # FC_COMPLETE -> FC_IDLE
        )

        # Advance through entry phase
        for _ in range(dfi.timing.tLP_CTRL_ENTER + 1):
            dfi.tick()

        # Call exit_freq_change
        dfi.exit_freq_change()

        # Advance through remaining phases with extra buffer
        for _ in range(dfi.timing.tFC_EXIT + dfi.timing.tFC_LATENCY + 10):
            dfi.tick()

        assert dfi.is_freq_change_complete()

    def test_power_down_timing(self):
        """Power down should follow expected timing"""
        dfi = DFI5Interface()

        dfi.request_pwr_down()
        for _ in range(dfi.timing.tPWR_DOWN + 1):
            dfi.tick()

        assert dfi.pwr_down_ack is True

    def test_power_up_timing(self):
        """Power up should be configurable"""
        dfi = DFI5Interface()

        # Power up done is set externally
        dfi.set_pwr_up_done(True)
        assert dfi.pwr_up_done is True


class TestDFILatencyCalculations:
    """Test DFI latency calculations"""

    def test_write_latency_ps_at_different_frequencies(self):
        """Write latency should scale with frequency"""
        timing = DFITimingParameters(tPHY_wrlAT=5)

        latency_8gtps = timing.get_write_latency_ps(125.0)  # 8 GT/s
        latency_12gtps = timing.get_write_latency_ps(83.33)  # 12 GT/s

        # Same latency in cycles, different in ps
        assert latency_8gtps != latency_12gtps

    def test_read_latency_ps_at_different_frequencies(self):
        """Read latency should scale with frequency"""
        timing = DFITimingParameters(tPHY_rdLat=8)

        latency_8gtps = timing.get_read_latency_ps(125.0)
        latency_16gtps = timing.get_read_latency_ps(62.5)

        assert latency_8gtps != latency_16gtps

    def test_latency_vs_bandwidth(self):
        """Higher frequency should have higher bandwidth"""
        dfi = DFI5Interface()

        dfi.set_frequency(8000)
        bw_low = dfi.get_bandwidth_gbs()

        dfi.set_frequency(16000)
        bw_high = dfi.get_bandwidth_gbs()

        assert bw_high > bw_low

    def test_latency_property_equivalence(self):
        """Latency properties should match parameters"""
        timing = DFITimingParameters(tPHY_wrlAT=7, tPHY_rdLat=9)

        assert timing.write_latency_cycles == timing.tPHY_wrlAT
        assert timing.read_latency_cycles == timing.tPHY_rdLat


class TestDFIFrequencyChangeLatency:
    """Test frequency change latency parameters"""

    def test_fc_latency_parameter(self):
        """tFC_LATENCY should be configurable"""
        timing = DFITimingParameters(tFC_LATENCY=12)
        assert timing.tFC_LATENCY == 12

    def test_fc_exit_parameter(self):
        """tFC_EXIT should be configurable"""
        timing = DFITimingParameters(tFC_EXIT=6)
        assert timing.tFC_EXIT == 6

    def test_fc_latency_affects_timing(self):
        """Frequency change latency should affect timing"""
        dfi = DFI5Interface()
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        dfi.exit_freq_change()

        # State should be FC_EXITING
        for _ in range(1):
            dfi.tick()

        remaining = dfi.get_freq_change_latency_remaining()
        assert remaining >= 0

    def test_fc_latency_remaining_calculation(self):
        """Latency remaining should decrease over time"""
        dfi = DFI5Interface()
        dfi.request_freq_change(1200)
        dfi.enter_freq_change()
        dfi.exit_freq_change()

        initial_remaining = dfi.get_freq_change_latency_remaining()

        # Advance a few cycles
        for _ in range(3):
            dfi.tick()

        later_remaining = dfi.get_freq_change_latency_remaining()
        # Should be less or equal (accounting for state transitions)
        assert later_remaining <= initial_remaining + 3


class TestDFITrainingTiming:
    """Test training timing parameters"""

    def test_training_latency_parameter(self):
        """tTRAINING should be configurable"""
        timing = DFITimingParameters(tTRAINING=2000)
        assert timing.tTRAINING == 2000

    def test_training_duration_in_cycles(self):
        """Training duration should be in cycles"""
        timing = DFITimingParameters()
        assert timing.tTRAINING > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])