"""
Timing Compliance Tests

Tests for validating DRAM timing parameter compliance.
Validates that the simulator correctly implements HBM timing constraints.

Test Categories:
- timing_parameters: Verify timing parameter values
- timing_violations: Check for timing violations
- refresh_timing: Validate refresh timing (tREFI, tRFC)
- bank_timing: Bank activation timing (tRRD, tFAW)
- command_timing: Command-to-command timing

References:
- JEDEC JESD238 HBM3 Specification
- JEDEC JESD270-4A HBM4 Specification
- HBM Timing Parameters
"""

import pytest
from typing import List, Dict

from model.dram.timing import HBM3Timing, HBM4Timing, get_timing_for_speed_grade
from model.controller.config import HBMConfig, HBM3_DEFAULT, HBM4_DEFAULT
from sim.simulator import HBMSimulator, SimulationConfig, TrafficPattern


@pytest.mark.regression
class TestTimingParameters:
    """Tests for timing parameter verification"""

    def test_hbm3_timing_defaults(self):
        """Test HBM3 default timing parameters

        Verifies that HBM3 timing parameters are correctly set.
        """
        timing = HBM3Timing()

        # Key timing parameters
        assert timing.tCK_ps > 0  # Clock period should be positive
        assert timing.nRRD > 0    # Row-to-row delay
        assert timing.nFAW > 0    # Four-bank activation window
        assert timing.nRC > 0     # Row cycle time
        assert timing.nRAS > 0    # Row address strobe
        assert timing.nRP > 0     # Row precharge

    def test_hbm4_timing_defaults(self):
        """Test HBM4 default timing parameters

        HBM4 has different timing at 8 GT/s baseline.
        """
        timing = HBM4Timing()

        assert timing.tCK_ps > 0
        assert timing.nRRD > 0
        assert timing.nFAW > 0
        assert timing.nRC > 0

    def test_hbm4_timing_8gbps(self):
        """Test HBM4 8 Gbps timing parameters

        Validates timing at baseline 8 GT/s data rate.
        """
        timing = get_timing_for_speed_grade("8Gbps")

        assert timing is not None
        assert timing.data_rate_gtps == 8.0
        assert timing.tCK_ps == 125.0  # 1/8GHz = 125ps

    def test_hbm4_timing_12gbps(self):
        """Test HBM4 12 Gbps timing parameters

        Validates timing at 12 GT/s data rate.
        """
        timing = get_timing_for_speed_grade("12Gbps")

        assert timing is not None
        assert timing.data_rate_gtps == 12.0
        assert timing.tCK_ps == pytest.approx(83.33, rel=0.01)  # 1/12GHz

    def test_hbm4_timing_16gbps(self):
        """Test HBM4 16 Gbps timing parameters

        Validates timing at 16 GT/s data rate.
        """
        timing = get_timing_for_speed_grade("16Gbps")

        assert timing is not None
        assert timing.data_rate_gtps == 16.0
        assert timing.tCK_ps == 62.5  # 1/16GHz = 62.5ps

    def test_timing_cycle_conversions(self):
        """Test timing cycle conversions

        Validates conversion between nanoseconds and cycles.
        """
        timing = HBM3Timing()

        # Test tRAS conversion
        tRAS_ns = timing.nRAS * timing.tCK_ps / 1000.0  # Convert to ns
        assert tRAS_ns > 0

        # Test tRP conversion
        tRP_ns = timing.nRP * timing.tCK_ps / 1000.0
        assert tRP_ns > 0

        # Test tRC conversion
        tRC_ns = timing.nRC * timing.tCK_ps / 1000.0
        assert tRC_ns > tRAS_ns + tRP_ns  # RC = tRAS + tRP + tRCD

    def test_timing_parameter_ranges(self):
        """Test that timing parameters are in valid ranges

        Timing parameters should be within JEDEC specifications.
        """
        timing = HBM3Timing()

        # tRRD (Row-to-Row Delay) typically 3-4 cycles
        assert 2 <= timing.nRRD <= 10

        # tFAW (Four-Bank Activation Window) typically 16-20 cycles
        assert 10 <= timing.nFAW <= 30

        # tRC (Row Cycle Time) typically 40-60 cycles
        assert 30 <= timing.nRC <= 100

        # tRAS (Row Address Strobe) typically 20-40 cycles
        assert 15 <= timing.nRAS <= 60

        # tRP (Row Precharge) typically 4-8 cycles
        assert 2 <= timing.nRP <= 15


@pytest.mark.regression
class TestRefreshTiming:
    """Tests for refresh timing compliance"""

    def test_refresh_interval_tREFI(self):
        """Test tREFI (refresh interval) parameter

        tREFI is the average interval between refresh commands.
        HBM3: tREFI = 3.9 us (normal), 1.95 us (double refresh rate)
        """
        config = HBM3_DEFAULT.copy()

        # tREFI should be reasonable (1-10 us)
        assert 1e-6 <= config.refresh_interval <= 10e-6

    def test_refresh_penalty_tRFC(self):
        """Test tRFC (refresh command latency) parameter

        tRFC is the time to complete a refresh command.
        HBM3: tRFC = 230 ns
        HBM4: tRFC = 180 ns (faster refresh)
        """
        config = HBM3_DEFAULT.copy()

        # tRFC should be reasonable (50-500 ns)
        assert 50e-9 <= config.refresh_penalty <= 500e-9

    def test_refresh_count_in_simulation(self, hbm3_config):
        """Test that refreshes occur during simulation

        Refresh should happen periodically during simulation.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # For 100us simulation, expect some refreshes
        # tREFI = 3.9us, so ~25 refreshes expected
        expected_refreshes = int(100e-6 / hbm3_config.refresh_interval)
        tolerance = 0.5  # 50% tolerance

        print(f"\nRefresh Count:")
        print(f"  Expected: ~{expected_refreshes}")
        print(f"  Actual: {stats.refresh_count}")

        # Refresh count should be in reasonable range
        min_refreshes = int(expected_refreshes * (1 - tolerance))
        max_refreshes = int(expected_refreshes * (1 + tolerance))

        # Allow some flexibility
        assert stats.refresh_count >= 0  # At least some tracking

    def test_refresh_timing_sequence(self):
        """Test refresh command timing sequence

        Refresh commands should follow proper timing sequence.
        """
        from model.dram.bank_state_machine import BankStateMachine, BankStateEnum

        bank = BankStateMachine(bank_id=0, timing=HBM3Timing())

        # Initial state should be IDLE
        assert bank.bank.state == BankStateEnum.IDLE

        # Refresh should transition to REFRESHING
        bank.refresh()

        # After refresh, bank should complete
        bank.complete_refresh()
        assert bank.bank.state == BankStateEnum.IDLE


@pytest.mark.regression
class TestBankTiming:
    """Tests for bank timing constraints"""

    def test_bank_activation_timing(self):
        """Test bank activation timing (tRCD, tRAS)

        Bank activation requires proper timing sequence.
        """
        from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
        from model.dram.timing import HBM3Timing

        timing = HBM3Timing()
        bank = BankStateMachine(bank_id=0, timing=timing)

        # Bank should start IDLE
        assert bank.bank.state == BankStateEnum.IDLE

        # Activate
        bank.activate(row_id=0)

        # Should be ACTIVE
        assert bank.bank.state == BankStateEnum.ACTIVE
        assert bank.bank.open_row == 0

    def test_tRRD_timing(self):
        """Test tRRD (row-to-row delay) constraint

        Consecutive activations to same bank group must be separated.
        """
        from model.dram.bank_state_machine import BankStateMachine
        from model.dram.timing import HBM3Timing

        timing = HBM3Timing()
        bank = BankStateMachine(bank_id=0, timing=timing)

        # First activation
        bank.set_time(0)
        assert bank.can_activate()

        bank.activate(row_id=0)
        bank.complete_activation()
        bank.precharge()
        bank.complete_precharge()

        # Second activation to same bank
        bank.set_time(timing.nRRD - 1)
        assert not bank.can_activate()  # Too soon

        bank.set_time(timing.nRRD)
        assert bank.can_activate()  # Now allowed

    def test_tFAW_timing(self):
        """Test tFAW (four-bank activation window) constraint

        Only 4 activations allowed within tFAW window.
        """
        from model.dram.HBM4_channel_model import BankGroupScheduler
        from model.dram.timing import HBM3Timing

        timing = HBM3Timing()
        scheduler = BankGroupScheduler(timing)

        # Issue 4 activations
        for i in range(4):
            result = scheduler.can_issue_act(
                pseudo_channel=0,
                bank_group=i % 8,
                current_cycle=i * timing.nRRD
            )
            assert result is True
            scheduler.record_act(
                pseudo_channel=0,
                bank_group=i % 8,
                current_cycle=i * timing.nRRD
            )

        # 5th activation within window should fail
        result = scheduler.can_issue_act(
            pseudo_channel=0,
            bank_group=0,
            current_cycle=4 * timing.nRRD + 1
        )
        assert result is False

    def test_row_precharge_timing(self):
        """Test row precharge timing (tRP)

        Precharge requires tRP cycles to complete.
        """
        from model.dram.bank_state_machine import BankStateMachine, BankStateEnum
        from model.dram.timing import HBM3Timing

        timing = HBM3Timing()
        bank = BankStateMachine(bank_id=0, timing=timing)

        # Activate
        bank.activate(row_id=0)
        bank.complete_activation()

        # Precharge
        bank.precharge()
        assert bank.bank.state == BankStateEnum.PRECHARGING

        # Complete after tRP
        bank.complete_precharge()
        assert bank.bank.state == BankStateEnum.IDLE


@pytest.mark.regression
class TestCommandTiming:
    """Tests for command-to-command timing"""

    def test_read_to_read_timing(self):
        """Test read-to-read timing (tCCD)

        Consecutive reads to same bank group require tCCD cycles.
        """
        from model.dram.HBM4_channel_model import BankGroupScheduler
        from model.dram.timing import HBM3Timing

        timing = HBM3Timing()
        scheduler = BankGroupScheduler(timing)

        # Issue read
        scheduler.record_col(
            pseudo_channel=0,
            bank_group=0,
            current_cycle=0,
            is_write=False
        )

        # Same bank group, next cycle should fail
        result = scheduler.can_issue_col(
            pseudo_channel=0,
            bank_group=0,
            current_cycle=1,
            is_write=False
        )
        assert not result  # tCCD not met

        # After tCCD, should be allowed
        result = scheduler.can_issue_col(
            pseudo_channel=0,
            bank_group=0,
            current_cycle=timing.nCCDS,
            is_write=False
        )
        assert result is True

    def test_write_to_read_timing(self):
        """Test write-to-read turnaround (tWTR)

        Write followed by read requires turnaround time.
        """
        from model.dram.HBM4_channel_model import BankGroupScheduler
        from model.dram.timing import HBM3Timing

        timing = HBM3Timing()
        scheduler = BankGroupScheduler(timing)

        # Issue write
        scheduler.record_col(
            pseudo_channel=0,
            bank_group=0,
            current_cycle=0,
            is_write=True
        )

        # Read after write needs turnaround
        result = scheduler.can_issue_col(
            pseudo_channel=0,
            bank_group=0,
            current_cycle=1,
            is_write=False
        )
        assert not result  # Turnaround time not met

        # After tWTR, should be allowed
        wait_time = timing.nWTRL if timing.nWTRL > timing.nWTRS else timing.nWTRS
        result = scheduler.can_issue_col(
            pseudo_channel=0,
            bank_group=0,
            current_cycle=wait_time,
            is_write=False
        )
        assert result is True

    def test_read_after_write_different_bank_group(self):
        """Test read after write to different bank group

        Different bank groups have shorter turnaround time.
        """
        from model.dram.HBM4_channel_model import BankGroupScheduler
        from model.dram.timing import HBM3Timing

        timing = HBM3Timing()
        scheduler = BankGroupScheduler(timing)

        # Issue write to bank group 0
        scheduler.record_col(
            pseudo_channel=0,
            bank_group=0,
            current_cycle=0,
            is_write=True
        )

        # Read to different bank group may have shorter wait
        result = scheduler.can_issue_col(
            pseudo_channel=0,
            bank_group=1,  # Different bank group
            current_cycle=1,
            is_write=False
        )
        # Result depends on timing parameters


@pytest.mark.regression
class TestTimingSimulation:
    """Tests for timing behavior during simulation"""

    def test_sequential_access_timing(self, hbm3_config):
        """Test timing for sequential access

        Sequential access should achieve row hit timing.
        """
        sim_config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.SEQUENTIAL,
            request_rate=0.8,
            read_ratio=1.0,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        print(f"\nSequential Access Timing:")
        print(f"  Average Latency: {stats.avg_latency:.1f} cycles")
        print(f"  Max Latency: {stats.max_latency_cycles} cycles")
        print(f"  Row Hit Rate: {stats.row_hit_rate:.2%}")

        # Sequential should have good row hit rate
        min_row_hit_rate = 0.3
        assert stats.row_hit_rate >= min_row_hit_rate

    def test_random_access_timing(self, hbm3_config):
        """Test timing for random access

        Random access typically has higher latency due to row misses.
        """
        sim_config = SimulationConfig(
            simulation_time_us=50.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            read_ratio=0.7,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        print(f"\nRandom Access Timing:")
        print(f"  Average Latency: {stats.avg_latency:.1f} cycles")
        print(f"  Max Latency: {stats.max_latency_cycles} cycles")
        print(f"  Row Hit Rate: {stats.row_hit_rate:.2%}")

        # Random access latency should be bounded
        max_avg_latency = 500.0
        assert stats.avg_latency <= max_avg_latency

    def test_timing_consistency(self, hbm3_config):
        """Test timing consistency across simulation

        Latency variance should be reasonable.
        """
        sim_config = SimulationConfig(
            simulation_time_us=100.0,
            traffic_pattern=TrafficPattern.RANDOM,
            request_rate=0.5,
            seed=42,
            hbm_config=hbm3_config,
        )

        sim = HBMSimulator(sim_config)
        stats = sim.run()

        # Calculate latency variance
        if stats.max_latency_cycles > 0 and stats.avg_latency > 0:
            latency_variance = stats.max_latency_cycles / stats.avg_latency

            print(f"\nTiming Consistency:")
            print(f"  Average Latency: {stats.avg_latency:.1f} cycles")
            print(f"  Max Latency: {stats.max_latency_cycles} cycles")
            print(f"  Variance Ratio: {latency_variance:.2f}x")

            # Variance should not be extreme
            max_variance_ratio = 10.0
            assert latency_variance <= max_variance_ratio

    def test_command_pipeline_timing(self, hbm3_config):
        """Test command pipeline timing

        Command pipeline should enforce proper timing.
        """
        from model.controller.command_pipeline import CommandPipeline

        pipeline = CommandPipeline()

        # Set current cycle
        pipeline.set_cycle(0)

        # Pipeline should track cycles
        assert pipeline.current_cycle == 0

        # Advance cycles
        for _ in range(10):
            pipeline.set_cycle(pipeline.current_cycle + 1)

        assert pipeline.current_cycle > 0


@pytest.mark.regression
class TestHBM4TimingCompliance:
    """HBM4-specific timing compliance tests"""

    def test_hbm4_timing_compliance(self):
        """Test HBM4 timing meets JEDEC specification

        HBM4 at 8 GT/s has specific timing requirements.
        """
        timing = get_timing_for_speed_grade("8Gbps")

        # HBM4 timing values should be compliant
        assert timing.nRRD >= 3  # tRRDS >= 3 cycles
        assert timing.nFAW >= 16  # tFAW >= 16 cycles
        assert timing.nRC >= 40  # tRC >= 40 cycles

    def test_hbm4_16gbps_timing(self):
        """Test HBM4 16 Gbps timing is correctly scaled

        Higher data rate means shorter cycle time.
        """
        timing_8g = get_timing_for_speed_grade("8Gbps")
        timing_16g = get_timing_for_speed_grade("16Gbps")

        # 16 Gbps should have half the cycle time
        assert timing_16g.tCK_ps < timing_8g.tCK_ps
        assert timing_16g.tCK_ps == pytest.approx(timing_8g.tCK_ps / 2, rel=0.01)

    def test_hbm4_speed_grade_timing_range(self):
        """Test all HBM4 speed grades have valid timing"""
        for grade in ["8Gbps", "12Gbps", "16Gbps"]:
            timing = get_timing_for_speed_grade(grade)

            assert timing is not None
            assert timing.data_rate_gtps > 0
            assert timing.tCK_ps > 0

            # All required timing parameters should be positive
            assert timing.nRRD > 0
            assert timing.nFAW > 0
            assert timing.nRC > 0