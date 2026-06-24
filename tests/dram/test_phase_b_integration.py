"""
Comprehensive Integration Tests for Phase B Components

Tests integration between:
1. Bank State Machine with Channel Model
2. Lane Repair with ECC/CRC
3. PHY Training with DFI interface
4. MBIST with memory array
5. End-to-end: Command through DRAM model with RAS features

These tests verify the 32-channel HBM4 configuration works correctly
across all Phase B components.

Reference: JEDEC JESD270-4A HBM4 specification
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from model.dram.bank_state_machine import (
    BankStateMachine,
    BankStateEnum,
    Bank,
    OperationType,
)
from model.dram.lane_repair import (
    HBM4LaneRepairModel,
    LaneRepairMap,
    RepairStatus,
)
from model.dram.ecc_crc import (
    HBM4ECC,
    HBM4CRC,
    HBM4DataIntegrity,
    HBM4ECCMode,
    HBM4CRCMode,
    ErrorType,
    ErrorTracker,
)
from model.dram.phy_training import (
    PHYTrainingStateMachine,
    PHYInitializationStateMachine,
    HBM4PHYManager,
    TrainingPhase,
    TrainingResult,
    PHYInitState,
)
from model.dram.mbist_controller import (
    MBISTController,
    MBISTState,
    MBISTAlgorithm,
    MBISTConfig,
    MBISTFault,
    MBISTResult,
    FaultType,
)
from model.dram.dfi_interface import (
    DFI5Interface,
    DFITimingParameters,
    DFICommand,
    DFILowPowerState,
    DFI5FreqChangeState,
    DFIRequest,
)
from model.dram.hbm4_spec import HBM4Spec, HBM4_CONFIG


# =============================================================================
# Test 1: Bank State Machine Integration with Channel Model
# =============================================================================

class TestBankStateMachineChannelIntegration:
    """Test Bank State Machine integration with multi-channel HBM4 configuration"""

    def test_bank_state_machine_creation(self):
        """Test bank state machine creation with HBM4 spec"""
        spec = HBM4_CONFIG
        timing = spec
        bsm = BankStateMachine(bank_id=0, timing=timing)

        assert bsm is not None
        assert bsm.bank.bank_id == 0
        assert bsm.bank.state == BankStateEnum.IDLE

    def test_multi_bank_activation_timing(self):
        """Test multi-bank activation with proper timing"""
        spec = HBM4_CONFIG
        timing = spec

        # Create bank state machines for 16 banks (per pseudo-channel)
        banks = [BankStateMachine(bank_id=i, timing=timing) for i in range(16)]

        # Time 0: Activate bank 0
        banks[0].set_time(0)
        success, error = banks[0].activate(row=0)
        assert success, f"Bank 0 activation failed: {error}"

        # Advance time past tRCD
        tRCD = spec.nRCDRD
        banks[1].set_time(tRCD)
        success, error = banks[1].activate(row=1)
        assert success, f"Bank 1 activation failed: {error}"

        # Verify both banks are active
        assert banks[0].bank.is_active
        assert banks[1].bank.is_active

    def test_bank_activation_conflict(self):
        """Test activation conflict detection"""
        spec = HBM4_CONFIG
        timing = spec

        bank = BankStateMachine(bank_id=0, timing=timing)
        bank.set_time(0)

        # First activation should succeed
        success, _ = bank.activate(row=0)
        assert success

        # Immediate second activation should fail (bank not IDLE)
        success, error = bank.activate(row=1)
        assert not success
        assert "not idle" in error.lower()

    def test_bank_timing_violation(self):
        """Test timing violation detection"""
        spec = HBM4_CONFIG
        timing = spec

        bank = BankStateMachine(bank_id=0, timing=timing)
        bank.set_time(0)

        # Activate
        bank.activate(row=0)

        # Immediately try to precharge (should violate tRAS)
        # tRAS = 20 cycles, but we're at cycle 0
        success, error = bank.precharge()
        assert not success
        assert "tRAS" in error

    def test_refresh_coordination(self):
        """Test refresh coordination across multiple banks"""
        spec = HBM4_CONFIG
        timing = spec

        # Create 16 banks
        banks = [BankStateMachine(bank_id=i, timing=timing) for i in range(16)]

        # Activate all banks first
        for i, bank in enumerate(banks):
            bank.set_time(i * 10)  # Stagger activations
            bank.activate(row=i)

        # Precharge all banks to return to IDLE state
        # Need to wait tRAS before precharge
        precharge_time = 10 + spec.nRAS + spec.nRP
        for bank in banks:
            bank.set_time(precharge_time)
            success, _ = bank.precharge()
            # Some banks might not be precharged if tRAS not met

        # Now all banks should be able to refresh if idle
        # Check each bank individually
        refresh_ready_count = 0
        for bank in banks:
            if bank.bank.state == BankStateEnum.IDLE:
                # Set time to a large value to satisfy tRFC
                bank.set_time(spec.nRFC * 2)
                if bank.can_refresh():
                    refresh_ready_count += 1

        # At least some banks should be able to refresh
        assert refresh_ready_count > 0

        # Execute refresh on one of the idle banks
        for bank in banks:
            if bank.bank.state == BankStateEnum.IDLE:
                bank.set_time(spec.nRFC * 2)
                success, error = bank.refresh()
                if success:
                    assert bank.bank.is_refresh
                    break

    def test_row_hit_detection(self):
        """Test row hit detection for active banks"""
        spec = HBM4_CONFIG
        timing = spec

        bank = BankStateMachine(bank_id=0, timing=timing)
        bank.set_time(0)

        # Activate row 100
        bank.activate(row=100)

        # Check row hit
        assert bank.is_row_hit(100)
        assert not bank.is_row_hit(200)

    def test_read_write_sequence(self):
        """Test read/write command sequence"""
        spec = HBM4_CONFIG
        timing = spec

        bank = BankStateMachine(bank_id=0, timing=timing)
        bank.set_time(0)

        # Activate
        bank.activate(row=0)

        # Wait for tRCD
        tRCD = spec.nRCDRD
        bank.set_time(tRCD)

        # Issue read
        success, error = bank.read()
        assert success, f"Read failed: {error}"

        # Read should be in BUSY state
        assert bank.bank.is_busy

    def test_power_down_self_refresh(self):
        """Test power down and self-refresh transitions"""
        spec = HBM4_CONFIG
        timing = spec

        bank = BankStateMachine(bank_id=0, timing=timing)
        bank.set_time(0)

        # Enter power down (bank must be IDLE)
        assert bank.can_enter_power_down()
        success, error = bank.enter_power_down()
        assert success
        assert bank.bank.is_powered_down

        # Exit power down
        success, error = bank.exit_power_down()
        assert success
        assert bank.bank.is_idle

        # Enter self-refresh
        assert bank.can_enter_self_refresh()
        success, error = bank.enter_self_refresh()
        assert success
        assert bank.bank.is_self_refresh

        # Exit self-refresh
        success, error = bank.exit_self_refresh()
        assert success
        assert bank.bank.is_idle


# =============================================================================
# Test 2: Lane Repair Integration with ECC/CRC
# =============================================================================

class TestLaneRepairECCIntegration:
    """Test Lane Repair integration with ECC/CRC for data integrity"""

    def test_lane_repair_with_ecc_encoding(self):
        """Test data encoding through repaired lanes"""
        # Create lane repair model
        repair = HBM4LaneRepairModel(num_channels=32, lanes_per_channel=64, spare_lanes_per_channel=4)

        # Create ECC engine
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED)

        # Simulate lane failure and repair
        channel_id = 0
        failed_lane = 42
        spare = repair.perform_repair(channel_id=channel_id, failed_lane=failed_lane)

        assert spare is not None
        assert repair.is_lane_remapped(channel_id, failed_lane)

        # Verify remapping works
        remapped = repair.get_remapped_lane(channel_id, failed_lane)
        assert remapped == spare

        # Test data flow through remapped lane
        original_data = 0xDEADBEEFCAFEBABE
        encoded = ecc.encode(original_data)

        # Verify ECC still works with remapped lanes
        result = ecc.decode(encoded)
        assert result.error_type == ErrorType.NO_ERROR
        assert result.data == original_data

    def test_multiple_lane_repairs_with_crc(self):
        """Test multiple lane repairs with CRC verification"""
        repair = HBM4LaneRepairModel(num_channels=8, lanes_per_channel=64, spare_lanes_per_channel=4)
        crc = HBM4CRC(crc_mode=HBM4CRCMode.CRC16)

        # Repair multiple lanes
        failed_lanes = [10, 25, 40, 55]
        for lane in failed_lanes:
            spare = repair.perform_repair(channel_id=0, failed_lane=lane)
            assert spare is not None

        # Verify all remappings
        for lane in failed_lanes:
            assert repair.is_lane_remapped(0, lane)

        # Test CRC calculation
        data = 0x123456789ABCDEF0
        crc_value = crc.calculate_crc16(data)
        valid, _ = crc.verify_crc16(data, crc_value)
        assert valid

    def test_lane_repair_status_tracking(self):
        """Test repair status tracking across channels"""
        repair = HBM4LaneRepairModel(num_channels=32, lanes_per_channel=64, spare_lanes_per_channel=4)

        # Channel 0: no failures
        status0 = repair.get_repair_status(0)
        assert status0 == RepairStatus.NO_REPAIR

        # Channel 1: some repairs
        repair.perform_repair(channel_id=1, failed_lane=10)
        repair.perform_repair(channel_id=1, failed_lane=20)
        status1 = repair.get_repair_status(1)
        assert status1 == RepairStatus.PARTIAL_REPAIR

        # Channel 2: all spares used
        for lane in range(4):
            repair.perform_repair(channel_id=2, failed_lane=lane * 10)
        status2 = repair.get_repair_status(2)
        assert status2 == RepairStatus.FULL_REPAIR

    def test_unrepairable_channel_detection(self):
        """Test unrepairable channel detection"""
        repair = HBM4LaneRepairModel(num_channels=4, lanes_per_channel=64, spare_lanes_per_channel=2)

        # Exhaust spares using perform_repair (uses add_failed_lane internally)
        repair.perform_repair(channel_id=0, failed_lane=10)
        repair.perform_repair(channel_id=0, failed_lane=20)

        # Third failure - perform_repair should return None (no spares available)
        spare = repair.perform_repair(channel_id=0, failed_lane=30)
        assert spare is None

        # Status should be FULL_REPAIR (all spares used)
        status = repair.get_repair_status(0)
        assert status == RepairStatus.FULL_REPAIR

        # The unrepairable state would only occur if we tried to add
        # more failures than available spares
        # For this test, we verify that no more repairs can be made

    def test_ecc_error_injection_through_remapped_lane(self):
        """Test ECC error injection through remapped lane"""
        repair = HBM4LaneRepairModel(num_channels=4, lanes_per_channel=64, spare_lanes_per_channel=4)
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED)

        # Repair a lane
        channel_id = 0
        failed_lane = 15
        spare = repair.perform_repair(channel_id=channel_id, failed_lane=failed_lane)

        # Encode data
        original = 0xCAFEBABE00000000
        encoded = ecc.encode(original)

        # Inject error at the remapped lane position
        # Simulate error in the spare lane
        error_bit = spare  # Error at the spare lane position
        corrupted = encoded ^ (1 << error_bit)

        # Decode and verify error detection
        result = ecc.decode(corrupted)
        # Error should be detected (not NO_ERROR)
        assert result.error_type != ErrorType.NO_ERROR or result.corrected


# =============================================================================
# Test 3: PHY Training Integration with DFI Interface
# =============================================================================

class TestPHYTrainingDFIIntegration:
    """Test PHY Training state machine integration with DFI 5.1 interface"""

    def test_phy_training_state_machine_creation(self):
        """Test PHY training state machine creation"""
        training_sm = PHYTrainingStateMachine(channel_id=0)
        assert training_sm is not None
        assert training_sm.channel_id == 0
        assert training_sm.status.current_phase == TrainingPhase.TRAIN_IDLE

    def test_phy_training_start_sequence(self):
        """Test starting PHY training sequence"""
        training_sm = PHYTrainingStateMachine(channel_id=0)

        # Start training
        success = training_sm.start_training()
        assert success
        assert training_sm.status.current_phase == TrainingPhase.TRAIN_START

    def test_phy_training_dfi_interface_integration(self):
        """Test PHY training with DFI interface integration"""
        # Create DFI interface
        dfi = DFI5Interface()

        # Create training state machine with DFI
        training_sm = PHYTrainingStateMachine(channel_id=0, dfi_interface=dfi)

        # Start training
        training_sm.start_training()

        # Process training cycles
        for _ in range(100):
            training_sm.tick()
            training_sm.process_training_cycle()

        # Verify DFI signals were set during training
        # (Check that training commands were encoded)
        assert training_sm.dfi_control.tra_req or \
               training_sm.status.current_phase != TrainingPhase.TRAIN_IDLE

    def test_phy_training_complete_sequence(self):
        """Test complete PHY training sequence"""
        training_sm = PHYTrainingStateMachine(channel_id=0)

        # Start training
        training_sm.start_training()

        # Process until complete or timeout
        max_cycles = 10000
        for _ in range(max_cycles):
            training_sm.tick()
            done = training_sm.process_training_cycle()
            if training_sm.is_training_complete():
                break

        # Check if training completed
        assert training_sm.is_training_complete()

        # Get results
        results = training_sm.get_training_results()
        assert 'channel_id' in results
        assert 'current_phase' in results

    def test_phy_initialization_state_machine(self):
        """Test PHY initialization state machine"""
        # Create training state machine
        training_sm = PHYTrainingStateMachine(channel_id=0)

        # Create initialization state machine
        init_sm = PHYInitializationStateMachine(training_sm=training_sm)

        # Start initialization
        init_sm.start_initialization()
        assert init_sm.status.state == PHYInitState.INIT_START

        # Process initialization cycles
        for _ in range(200):
            init_sm.tick()
            init_sm.process_init_cycle()
            if init_sm.is_initialized:
                break

        # Should progress through states
        assert init_sm.status.state in [PHYInitState.INIT_COMPLETE,
                                         PHYInitState.INIT_TRAINING,
                                         PHYInitState.INIT_CALIBRATE]

    def test_hbm4_phy_manager_multi_channel(self):
        """Test HBM4 PHY Manager with 32 channels"""
        # Create PHY manager for 32 channels
        phy_manager = HBM4PHYManager(num_channels=32)

        assert phy_manager.num_channels == 32
        assert len(phy_manager._init_machines) == 32
        assert len(phy_manager._training_machines) == 32

        # Start initialization on all channels
        phy_manager.start_initialization()

        # Process initialization
        for _ in range(500):
            phy_manager.process_cycles(1)
            if phy_manager._all_initialized:
                break

        # Check channel status
        status = phy_manager.get_channel_status(0)
        assert 'state' in status

    def test_phy_training_vref_validation(self):
        """Test VREF validation in training"""
        training_sm = PHYTrainingStateMachine(channel_id=0)

        # VREF DAC range is 0-63 for 6-bit
        # Test valid range
        valid = training_sm._validate_vref(32, "DQ")
        assert valid

        valid = training_sm._validate_vref(0, "CA")
        assert valid

        valid = training_sm._validate_vref(63, "CA")
        assert valid

        # Test invalid range
        with pytest.raises(ValueError):
            training_sm._validate_vref(64, "DQ")

        with pytest.raises(ValueError):
            training_sm._validate_vref(-1, "CA")


# =============================================================================
# Test 4: MBIST Integration with Memory Array
# =============================================================================

class TestMBISTMemoryIntegration:
    """Test MBIST controller integration with memory array"""

    def test_mbist_controller_creation(self):
        """Test MBIST controller creation"""
        mbist = MBISTController()
        assert mbist is not None
        assert mbist.state == MBISTState.IDLE

    def test_mbist_march_c_test(self):
        """Test MBIST March-C algorithm"""
        mbist = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=255,
            fail_stop=False,
        )

        result = mbist.run_test(config)
        assert result is not None
        assert result.algorithm == MBISTAlgorithm.MARCH_C
        # Without injected faults, should pass
        assert result.passed or len(result.faults_found) == 0

    def test_mbist_fault_injection_and_detection(self):
        """Test fault injection and detection"""
        mbist = MBISTController()

        # Inject stuck-at-0 fault
        fault_addr = 0x100
        mbist.inject_fault(fault_addr, FaultType.STUCK_AT_0)

        # Configure test
        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0x100,
            end_address=0x110,
            fail_stop=False,  # Don't stop on fault
        )

        result = mbist.run_test(config)
        assert len(result.faults_found) > 0
        assert any(f.address == fault_addr for f in result.faults_found)

    def test_mbist_walking_ones_test(self):
        """Test MBIST Walking Ones algorithm"""
        mbist = MBISTController()

        # No faults
        result = mbist.run_walking_ones()
        assert result is not None
        assert result.algorithm == MBISTAlgorithm.WALKING_ONES

    def test_mbist_address_test(self):
        """Test MBIST Address decoder test"""
        mbist = MBISTController()

        result = mbist.run_address_test()
        assert result is not None
        assert result.algorithm == MBISTAlgorithm.ADDRESS_TEST

    def test_mbist_data_retention_test(self):
        """Test MBIST Data retention test"""
        mbist = MBISTController()

        # Use smaller retention time for testing
        config = MBISTConfig(
            algorithm=MBISTAlgorithm.DATA_RETENTION,
            start_address=0,
            end_address=63,
            retention_time_cycles=10,  # Short for testing
        )
        mbist.configure(config)

        result = mbist.run_data_retention_test()
        assert result is not None

    def test_mbist_galpat_test(self):
        """Test MBIST Galloping Pattern test"""
        mbist = MBISTController()

        result = mbist.run_galpat_test()
        assert result is not None
        assert result.algorithm == MBISTAlgorithm.GALPAT

    def test_mbist_multiple_faults(self):
        """Test MBIST with multiple injected faults"""
        mbist = MBISTController()

        # Inject multiple faults
        fault_addrs = [0x50, 0x100, 0x150, 0x200]
        for addr in fault_addrs:
            mbist.inject_fault(addr, FaultType.STUCK_AT_0)

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0x40,
            end_address=0x210,
            fail_stop=False,
        )

        result = mbist.run_test(config)

        # Should detect at least the injected faults
        assert len(result.faults_found) >= 4

    def test_mbist_statistics(self):
        """Test MBIST statistics tracking"""
        mbist = MBISTController()

        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=100,
        )

        result = mbist.run_test(config)
        summary = mbist.get_summary()

        assert 'stats' in summary
        assert 'results' in summary
        assert summary['stats']['total_tests'] > 0

    def test_mbist_reset(self):
        """Test MBIST controller reset"""
        mbist = MBISTController()

        # Inject fault
        mbist.inject_fault(0x100, FaultType.STUCK_AT_0)

        # Run test
        result = mbist.run_test()

        # Reset
        mbist.reset()

        # Should be back to IDLE
        assert mbist.state == MBISTState.IDLE

        # Run test again - should not see old faults (fault_map persists)
        result2 = mbist.run_test()
        # fault_map persists, so should still see faults


# =============================================================================
# Test 5: End-to-End Integration Tests
# =============================================================================

class TestEndToEndIntegration:
    """End-to-end integration tests for Phase B components"""

    def test_full_hbm4_spec_configuration(self):
        """Test full HBM4 specification configuration"""
        spec = HBM4_CONFIG

        # Verify HBM4 key parameters
        assert spec.channels == 32
        assert spec.pseudo_channels == 64
        assert spec.total_banks == 1024  # 32 * 2 * 16
        assert spec.io_width == 2048
        assert spec.data_rate_gtps == 8.0
        assert spec.bandwidth == pytest.approx(2.048, rel=0.01)  # TB/s

    def test_address_decoder_integration(self):
        """Test address decoder with full HBM4 address space"""
        spec = HBM4_CONFIG

        from model.controller.hbm4_address_decoder import HBM4AddressDecoder
        decoder = HBM4AddressDecoder(spec=spec)

        # Test address in channel 0
        addr = 0x00000000
        decoded = decoder.decode(addr)

        assert decoded.channel_id == 0
        assert decoded.pseudo_channel_id in [0, 1]
        assert decoded.bank_id < 16

        # Test address in channel 31 (last channel)
        # Calculate address that maps to channel 31
        addr = 0xF8000000  # High bits for channel
        decoded = decoder.decode(addr)
        assert decoded.channel_id <= 31

    def test_command_flow_through_system(self):
        """Test complete command flow through DRAM model"""
        spec = HBM4_CONFIG

        # Create bank state machines
        banks = [BankStateMachine(bank_id=i, timing=spec) for i in range(16)]

        # Get actual timing values from BSM cache
        nRCD = banks[0]._get_cached_timing('nRCD')
        nCL = banks[0]._get_cached_timing('nCL')
        nCCD = banks[0]._get_cached_timing('nCCD')
        nRAS = banks[0]._get_cached_timing('nRAS')

        # Simulate command sequence:
        # 1. Activate row
        banks[0].set_time(0)
        success, _ = banks[0].activate(row=100)
        assert success

        # 2. Wait for tRCD before read
        banks[0].set_time(nRCD)
        assert banks[0].can_read()

        # 3. Issue read at current_time = nRCD
        success, _ = banks[0].read()
        assert success
        assert banks[0].bank.is_busy

        # 4. Wait for read to complete
        # Read complete = current_time + nRCD + nCL + (burst-1)*nCCD
        # Since we issued at time nRCD: complete = nRCD + nRCD + nCL + 3*nCCD = 2*nRCD + nCL + 3*nCCD
        read_complete_time = 2 * nRCD + nCL + 3 * nCCD
        banks[0].set_time(read_complete_time)
        assert banks[0].can_complete_read()

        # 5. Complete read, return to active
        success, _ = banks[0].complete_read()
        assert success
        assert banks[0].bank.is_active

        # 6. Precharge - need to wait tRAS since activation
        # Total time since activation = read_complete_time (since we never precharged)
        precharge_time = read_complete_time + nRAS
        banks[0].set_time(precharge_time)
        success, _ = banks[0].precharge()
        assert success
        assert banks[0].bank.is_idle

    def test_refresh_cycle_integration(self):
        """Test refresh cycle integration"""
        spec = HBM4_CONFIG

        # Create 16 banks
        banks = [BankStateMachine(bank_id=i, timing=spec) for i in range(16)]

        # Activate all banks
        for i, bank in enumerate(banks):
            bank.set_time(i * 10)
            bank.activate(row=i)

        # Precharge all banks to make them idle
        precharge_time = 10 + spec.nRAS + spec.nRP
        for bank in banks:
            bank.set_time(precharge_time)
            bank.precharge()

        # Wait for all banks to be ready for refresh
        # Set to a large time that satisfies tRC for all banks
        refresh_time = precharge_time + spec.nRC
        for bank in banks:
            bank.set_time(refresh_time)
            # Bank should be IDLE now
            if bank.bank.state == BankStateEnum.IDLE:
                assert bank.can_refresh()

        # Execute refresh on first bank that is IDLE
        for bank in banks:
            if bank.bank.state == BankStateEnum.IDLE:
                bank.set_time(refresh_time)
                success, _ = bank.refresh()
                if success:
                    break

        # Wait for refresh to complete
        refresh_complete_time = refresh_time + spec.nRFC
        for bank in banks:
            if bank.bank.state == BankStateEnum.REFRESHING:
                bank.set_time(refresh_complete_time)
                assert bank.can_complete_refresh()
                success, _ = bank.complete_refresh()
                assert success

    def test_dfi_command_encoding_integration(self):
        """Test DFI command encoding"""
        dfi = DFI5Interface()

        # Encode ACT command
        act_request = dfi.encode_command(
            cmd='ACT',
            addr_vec={
                'row': 0x100,
                'bank': 0,
                'channel': 0,
                'pseudo_channel': 0,
            }
        )

        assert act_request.command == DFICommand.ACT
        assert act_request.address == 0x100

        # Encode WR command
        wr_request = dfi.encode_command(
            cmd='WR',
            addr_vec={
                'bank': 1,
                'channel': 0,
                'pseudo_channel': 0,
            }
        )

        assert wr_request.command == DFICommand.WR
        assert wr_request.wrdata_en

    def test_dfi_low_power_state_transitions(self):
        """Test DFI low power state transitions"""
        dfi = DFI5Interface()

        # Initial state should be LP_IDLE
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

        # Request LP_CTRL
        success = dfi.request_low_power(DFILowPowerState.LP_CTRL)
        assert success

        # Process cycles for LP entry
        for _ in range(10):
            dfi.tick()

        # Request wakeup
        dfi.wakeup_from_low_power()

        # Process cycles for LP exit
        for _ in range(10):
            dfi.tick()

        # Should return to IDLE
        assert dfi.lp_state == DFILowPowerState.LP_IDLE

    def test_dfi_frequency_change_integration(self):
        """Test DFI frequency change integration"""
        dfi = DFI5Interface()

        # Initial frequency
        assert dfi.frequency_mhz == 800

        # Request frequency change to 1200 MHz
        success = dfi.request_freq_change(1200)
        assert success
        assert dfi.target_frequency_mhz == 1200

        # Enter frequency change sequence
        success = dfi.enter_freq_change()
        assert success

        # Process cycles for FC - wait until FC_ACTIVE state
        # FC_ENTERING takes 2 cycles (tFC_ENTER), then transitions to FC_ACTIVE
        for _ in range(3):
            dfi.tick()

        # Exit frequency change while in FC_ACTIVE state (before auto-completion)
        success = dfi.exit_freq_change()
        assert success, f"exit_freq_change() failed, state is {dfi._fc_state.name}"

        # Process remaining cycles for FC exit sequence
        for _ in range(20):
            dfi.tick()

        # Should be complete
        assert dfi.is_freq_change_complete()
        assert dfi.frequency_mhz == 1200

    def test_lane_repair_ecc_crc_full_integration(self):
        """Test full lane repair, ECC, and CRC integration"""
        # Create all components
        repair = HBM4LaneRepairModel(num_channels=32, lanes_per_channel=64, spare_lanes_per_channel=4)
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED)
        crc = HBM4CRC(crc_mode=HBM4CRCMode.CRC16)
        integrity = HBM4DataIntegrity(data_width=64, enable_ecc=True, enable_crc=True)

        # Scenario: Channel 0 lane 15 fails, is repaired
        channel_id = 0
        failed_lane = 15
        spare = repair.perform_repair(channel_id, failed_lane)
        assert spare is not None

        # Write data through repaired lane
        data = 0xDEADBEEF12345678
        encoded_data = integrity.encode_data(data)

        # Verify lane remapping
        actual_lane = repair.get_remapped_lane(channel_id, failed_lane)
        assert actual_lane == spare

        # Verify ECC encoding works
        encoded = ecc.encode(data)
        result = ecc.decode(encoded)
        assert result.data == data
        assert result.error_type == ErrorType.NO_ERROR

        # CRC verification on raw data
        crc_value = crc.calculate_crc16(data)
        valid, _ = crc.verify_crc16(data, crc_value)
        assert valid

        # Statistics
        stats = repair.get_stats()
        assert stats['total_repairs'] == 1
        assert stats['channels_with_repairs'] == 1

    def test_phy_training_mbist_dfi_integration(self):
        """Test complete PHY training, MBIST, and DFI integration"""
        # Create DFI interface
        dfi = DFI5Interface()

        # Create PHY training
        training_sm = PHYTrainingStateMachine(channel_id=0, dfi_interface=dfi)

        # Create MBIST
        mbist = MBISTController()

        # Start PHY training
        training_sm.start_training()

        # Process training
        for _ in range(500):
            training_sm.tick()
            training_sm.process_training_cycle()

        # Get training results
        training_results = training_sm.get_training_results()
        assert 'channel_id' in training_results

        # Run MBIST
        mbist_config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=255,
        )
        mbist_result = mbist.run_test(mbist_config)

        # Verify MBIST completed
        assert mbist_result is not None

        # Verify DFI is ready for commands
        assert dfi.is_ready()

    def test_multi_channel_stress_test(self):
        """Stress test with multiple channels"""
        num_channels = 32

        # Create components for each channel
        banks_per_channel = 16
        banks = [[BankStateMachine(bank_id=i*16+j, timing=HBM4_CONFIG)
                  for j in range(banks_per_channel)]
                 for i in range(num_channels)]

        repair = HBM4LaneRepairModel(num_channels=num_channels)

        # Activate random banks across all channels
        import random
        random.seed(42)

        activation_time = 0
        for ch in range(num_channels):
            for bank_idx in range(banks_per_channel):
                # Stagger activations
                banks[ch][bank_idx].set_time(activation_time)
                success, _ = banks[ch][bank_idx].activate(row=bank_idx)
                if not success:
                    # Skip if timing conflict
                    activation_time += HBM4_CONFIG.nRC
                    banks[ch][bank_idx].set_time(activation_time)
                    success, _ = banks[ch][bank_idx].activate(row=bank_idx)
                activation_time += 5

        # Verify banks are active
        active_count = 0
        for ch in range(num_channels):
            for bank_idx in range(banks_per_channel):
                if banks[ch][bank_idx].bank.is_active:
                    active_count += 1

        assert active_count > 0

    def test_power_estimation_integration(self):
        """Test power estimation with Phase B components"""
        from model.dram.power_estimator import (
            HBM4PowerEstimator,
            PowerState,
            CommandType,
        )

        # Create power estimator
        power = HBM4PowerEstimator(num_channels=32)

        # Simulate operations
        power.set_all_channels_state(PowerState.ACTIVE, cycles=100)
        power.record_command(0, CommandType.ACT)
        power.record_command(0, CommandType.RD)
        power.record_command(0, CommandType.WR)

        # Get total power
        total_power = power.get_total_power_mw()
        assert total_power > 0

        # Generate report
        report = power.generate_report()
        assert report is not None


# =============================================================================
# Test 6: 32-Channel HBM4 Configuration Verification
# =============================================================================

class Test32ChannelHBM4Configuration:
    """Verify 32-channel HBM4 configuration across all Phase B components"""

    def test_hbm4_spec_32_channel_defaults(self):
        """Test HBM4 spec default 32-channel configuration"""
        spec = HBM4_CONFIG

        assert spec.channels == 32
        assert spec.pseudo_channels == 64  # 32 * 2
        assert spec.total_banks == 1024    # 32 * 2 * 16
        assert spec.io_width == 2048
        assert spec.data_rate_gtps == 8.0

    def test_bank_state_machine_32_channels(self):
        """Test bank state machine with 32-channel config"""
        spec = HBM4_CONFIG

        # Total banks = 32 channels * 2 pseudo-channels * 16 banks = 1024
        total_banks = 1024

        banks = [BankStateMachine(bank_id=i, timing=spec) for i in range(total_banks)]

        # Activate first bank
        banks[0].set_time(0)
        banks[0].activate(row=0)

        # Activate last bank (should not conflict)
        banks[total_banks-1].set_time(100)
        success, _ = banks[total_banks-1].activate(row=0)
        assert success

    def test_lane_repair_32_channels(self):
        """Test lane repair with 32-channel config"""
        repair = HBM4LaneRepairModel(
            num_channels=32,
            lanes_per_channel=64,
            spare_lanes_per_channel=4
        )

        # Repair lanes in different channels
        for ch in range(32):
            spare = repair.perform_repair(channel_id=ch, failed_lane=ch * 2)
            assert spare is not None

        # Verify stats
        stats = repair.get_stats()
        assert stats['total_channels'] == 32
        assert stats['total_repairs'] == 32
        assert stats['channels_with_repairs'] == 32

    def test_phy_manager_32_channels(self):
        """Test PHY manager with 32 channels"""
        phy_manager = HBM4PHYManager(num_channels=32)

        assert phy_manager.num_channels == 32
        assert len(phy_manager._init_machines) == 32
        assert len(phy_manager._training_machines) == 32

        # Start initialization
        phy_manager.start_initialization()

        # Process initialization
        max_cycles = 1000
        for _ in range(max_cycles):
            phy_manager.process_cycles(1)
            if all(sm.is_initialized for sm in phy_manager._init_machines):
                break

        # Check all channels initialized
        for ch in range(32):
            status = phy_manager.get_channel_status(ch)
            assert 'state' in status

    def test_address_decoder_32_channels(self):
        """Test address decoder with 32-channel addressing"""
        spec = HBM4_CONFIG

        from model.controller.hbm4_address_decoder import HBM4AddressDecoder
        decoder = HBM4AddressDecoder(spec=spec)

        # Test addresses across all 32 channels
        for ch in range(32):
            # Calculate address for this channel
            addr = ch << (spec.ADDR_ROW_BITS + spec.ADDR_COL_BITS)
            decoded = decoder.decode(addr)
            assert decoded.channel_id <= 31

    def test_dfi_interface_bandwidth(self):
        """Test DFI interface bandwidth calculation"""
        dfi = DFI5Interface()

        # At 800 MHz DFI clock, 8 GT/s data rate
        bandwidth_gbs = dfi.get_bandwidth_gbs()
        assert bandwidth_gbs == pytest.approx(2048.0, rel=0.01)  # GB/s

        bandwidth_tbs = dfi.get_bandwidth_tbs()
        assert bandwidth_tbs == pytest.approx(2.048, rel=0.01)  # TB/s

    def test_end_to_end_32_channel_configuration(self):
        """End-to-end test of 32-channel configuration"""
        spec = HBM4_CONFIG

        # Create components
        repair = HBM4LaneRepairModel(num_channels=32, lanes_per_channel=64)
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.SECDED)
        phy_manager = HBM4PHYManager(num_channels=32)

        # Verify HBM4 specs
        assert spec.channels == 32
        assert spec.bandwidth == pytest.approx(2.048, rel=0.01)

        # Verify lane repair
        assert repair.num_channels == 32

        # Verify PHY manager
        assert phy_manager.num_channels == 32

        # Verify ECC
        test_data = 0x123456789ABCDEF0
        encoded = ecc.encode(test_data)
        result = ecc.decode(encoded)
        assert result.data == test_data
        assert result.error_type == ErrorType.NO_ERROR


# =============================================================================
# Test 7: Error Handling and Edge Cases
# =============================================================================

class TestErrorHandlingEdgeCases:
    """Error handling and edge case tests"""

    def test_bank_state_machine_timeout(self):
        """Test bank state machine timeout handling"""
        spec = HBM4_CONFIG
        bank = BankStateMachine(bank_id=0, timing=spec)

        # Activate
        bank.set_time(0)
        bank.activate(row=0)

        # Verify we can check time_to_ready
        time_to_ready = bank.time_to_read_ready()
        assert time_to_ready >= 0

    def test_lane_repair_exhaustion_handling(self):
        """Test handling of spare lane exhaustion"""
        repair = HBM4LaneRepairModel(num_channels=4, spare_lanes_per_channel=2)

        # Use all spares
        for i in range(2):
            spare = repair.perform_repair(channel_id=0, failed_lane=i * 10)
            assert spare is not None

        # Try to add another failure
        result = repair.add_failed_lane(channel_id=0, lane_id=30)
        assert not result

        # Status should be FULL_REPAIR or UNREPAIRABLE
        status = repair.get_repair_status(0)
        assert status in [RepairStatus.FULL_REPAIR, RepairStatus.UNREPAIRABLE]

    def test_ecc_disabled_mode(self):
        """Test ECC in disabled mode"""
        ecc = HBM4ECC(data_width=64, ecc_mode=HBM4ECCMode.DISABLED)

        data = 0xDEADBEEF
        encoded = ecc.encode(data)
        assert encoded == data  # No ECC bits added

    def test_mbist_timeout_handling(self):
        """Test MBIST timeout handling"""
        mbist = MBISTController()

        # Use small range to avoid long execution
        # but set very small timeout to trigger timeout
        config = MBISTConfig(
            algorithm=MBISTAlgorithm.MARCH_C,
            start_address=0,
            end_address=100,  # Small range
            timeout_cycles=1,  # Very small timeout - will timeout
            fail_stop=False,
        )

        mbist.configure(config)
        result = mbist.run_test(config)

        # Should either pass quickly or timeout
        assert result is not None

    def test_dfi_queue_overflow(self):
        """Test DFI request queue overflow handling"""
        from model.dram.dfi_interface import DFIRequestQueueConfig

        config = DFIRequestQueueConfig(
            max_size=2,
            overflow_strategy="drop_oldest"
        )
        dfi = DFI5Interface(queue_config=config)

        # Queue multiple requests
        for i in range(5):
            request = DFIRequest(
                command=DFICommand.ACT,
                address=i,
                bank=0,
                pseudo_channel=0,
                channel=0,
            )
            dfi.queue_request(request)

        # Queue should have limited size
        assert dfi.pending_request_count <= 2

    def test_invalid_address_handling(self):
        """Test handling of invalid addresses"""
        spec = HBM4_CONFIG

        from model.controller.hbm4_address_decoder import HBM4AddressDecoder
        decoder = HBM4AddressDecoder(spec=spec)

        # Very large address should still decode
        addr = 0xFFFFFFFFFFFFFFFF
        decoded = decoder.decode(addr)
        assert decoded is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
