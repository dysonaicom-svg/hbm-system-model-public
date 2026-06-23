"""
Example: HBM4 DRAM Features

This example demonstrates advanced HBM4 DRAM features:
- ECC/CRC error detection and correction
- Lane repair capabilities
- PHY training sequences
- Power estimation
- MBIST (Memory Built-In Self-Test)
- Loopback testing

Run: python examples/dram_features.py
"""

from model.dram.HBM4_spec import HBM4Spec
from model.dram.ecc_crc import HBM4ECC, HBM4CRC, ErrorType
from model.dram.lane_repair import HBM4LaneRepairModel, RepairStatus
from model.dram.phy_training import PHYInitializationStateMachine, PHYInitState
from model.dram.power_estimator import HBM4PowerEstimator, PowerState
from model.dram.mbist_controller import MBISTController, MBISTAlgorithm, MBISTState
from model.dram.loopback_controller import LoopbackController, LoopbackMode, LoopbackConfig, LoopbackState


def main():
    print("=" * 60)
    print("HBM4 DRAM Features Example")
    print("=" * 60)

    spec = HBM4Spec()

    # ECC/CRC
    print("\n1. ECC/CRC Error Detection and Correction:")
    ecc = HBM4ECC(data_width=64)
    crc = HBM4CRC()

    # Generate test data (64-bit integer)
    test_data = 0xDEADBEEFDEADBEEF
    print(f"   Test data: 0x{test_data:016X}")

    # Encode with ECC
    encoded = ecc.encode(test_data)
    print(f"   ECC encoded: 0x{encoded:016X}")

    # Generate CRC
    crc_value = crc.calculate_crc16(test_data)
    print(f"   CRC: 0x{crc_value:04X}")

    # Decode with ECC
    result = ecc.decode(encoded)
    print(f"   ECC decode status: {result.error_type.name}")
    print(f"   Decoded data: 0x{result.data:016X}")

    # Simulate error
    print("\n   Simulating single-bit error...")
    corrupted = encoded ^ 0x0001  # Flip one bit
    result = ecc.decode(corrupted)
    print(f"   Error type: {result.error_type.name}")
    print(f"   Corrected: {'Yes' if result.corrected else 'No'}")

    # Lane repair
    print("\n2. Lane Repair Capabilities:")
    repair_model = HBM4LaneRepairModel(num_channels=32, lanes_per_channel=spec.io_width)
    print(f"   - I/O width: {spec.io_width} bits")
    print(f"   - Total lanes per channel: {repair_model.lanes_per_channel}")
    print(f"   - Redundant lanes: {repair_model.spare_lanes_per_channel}")

    # Map a failed lane
    print("\n   Mapping failed lane 42 to redundant lane 0...")
    success = repair_model.add_failed_lane(0, 42)
    repair_model.allocate_spare(0, 42, 0)
    print(f"   - Success: {success}")
    failed_lanes = repair_model.get_all_failed_lanes(0)
    print(f"   - Failed lanes: {failed_lanes}")

    # Check lane status
    print("\n   Checking lane repair status...")
    status = repair_model.get_repair_status(0)
    print(f"   - Status: {status.name}")

    # PHY training
    print("\n3. PHY Training Sequences:")
    phy_init_sm = PHYInitializationStateMachine()
    print(f"   - Initial state: {phy_init_sm.status.state.name}")

    # Start initialization
    print("\n   Starting PHY initialization...")
    phy_init_sm.start_initialization()
    print(f"   - State: {phy_init_sm.status.state.name}")

    # Simulate initialization steps
    print("   Simulating initialization steps:")
    for step in range(5):
        phy_init_sm.tick()
        if phy_init_sm.status.state in [PHYInitState.INIT_CALIBRATE, PHYInitState.INIT_TRAINING]:
            print(f"   - Step {step}: {phy_init_sm.status.state.name}...")

    # Complete initialization
    if phy_init_sm.status.state != PHYInitState.INIT_COMPLETE:
        # Advance to complete state manually for demo
        print(f"   - Final state: {phy_init_sm.status.state.name}")
    else:
        print(f"   - Initialization complete")

    # Get initialization results
    print(f"   - Is initialized: {phy_init_sm.is_initialized}")

    # Power estimation
    print("\n4. Power Estimation:")
    power_est = HBM4PowerEstimator()
    print(f"   - Number of channels: {power_est.num_channels}")

    # Set different channel states and tick
    power_est.set_channel_state(0, PowerState.ACTIVE, 10)
    power_est.set_channel_state(1, PowerState.READ, 5)
    power_est.set_channel_state(2, PowerState.WRITE, 5)
    power_est.tick(10)

    # Get power stats
    total_power = power_est.get_total_power_mw()
    avg_power = power_est.get_average_power_mw()
    ch_power = power_est.get_channel_power_mw(0)

    print(f"   Power estimates:")
    print(f"   - Total power: {total_power:.2f} mW")
    print(f"   - Average power: {avg_power:.2f} mW")
    print(f"   - Channel 0 power: {ch_power:.2f} mW")

    # MBIST
    print("\n5. MBIST (Memory Built-In Self-Test):")
    mbist = MBISTController()
    print(f"   - Supported algorithms:")
    for algo in MBISTAlgorithm:
        print(f"     - {algo.name}")

    # Run March-C algorithm
    print("\n   Running March-C algorithm...")
    mbist.start_test("March-C")
    print(f"   - Initial state: {mbist.state.name}")

    # Execute MBIST steps
    steps = 0
    while mbist.state not in [MBISTState.COMPLETE, MBISTState.FAIL] and steps < 100:
        mbist.tick()
        steps += 1
        if mbist.state == MBISTState.RUNNING:
            faults = len(mbist.current_result.faults_found) if mbist.current_result else 0
            print(f"   - Running: faults={faults}")

    print(f"   - Final state: {mbist.state.name}")
    faults_found = len(mbist.current_result.faults_found) if mbist.current_result else 0
    print(f"   - Fault count: {faults_found}")
    passed = mbist.current_result.passed if mbist.current_result else False
    print(f"   - Pass: {passed}")

    # Loopback testing
    print("\n6. Loopback Testing:")
    loopback = LoopbackController()
    print(f"   - Supported modes:")
    for mode in LoopbackMode:
        print(f"     - {mode.name}")

    # Configure loopback
    print("\n   Configuring PRBS-7 loopback...")
    config = LoopbackConfig(mode=LoopbackMode.PRBS_7)
    success = loopback.configure(config)
    print(f"   - Configuration success: {success}")
    print(f"   - Current state: {loopback.state.name}")

    # Start loopback test
    print("\n   Starting loopback test...")
    success = loopback.start()
    print(f"   - Start success: {success}")
    print(f"   - State after start: {loopback.state.name}")

    # Run loopback test for a few cycles
    print("   Running loopback test...")
    for cycle in range(10):
        loopback.tick()
        if loopback.state == LoopbackState.RUNNING:
            pass

    print(f"   - Final state: {loopback.state.name}")
    print(f"   - Is complete: {loopback.is_complete()}")
    print(f"   - Is passed: {loopback.is_passed()}")

    print("\n" + "=" * 60)
    print("DRAM features example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()