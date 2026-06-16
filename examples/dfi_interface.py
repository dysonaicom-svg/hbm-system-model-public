"""
Example: DFI 5.0 Interface

This example demonstrates the DFI 5.0 interface between HBM4 controller and PHY:
- Command encoding and queueing
- Control update handshake
- Frequency change protocol
- Low power state management
- Power management signals
- Training sequences

DFI 5.0 Features:
- Command encoding (ACT, PRE, RD, WR, REFab, REFsb, etc.)
- Control update handshake (dfi_ctrlupd_req/ack)
- Frequency change protocol (dfi_freq_change_en/ack)
- Low power states (LP_IDLE, LP_CTRL, LP_DATA, LP_FREQ_CHANGE)
- Power management (dfi_pwr_up_done, dfi_pwr_down_ack)
- PHY Independent Mode for initialization/training

Run: python examples/dfi_interface.py
"""

from model.dram.dfi_interface import (
    DFI5Interface, DFICommand, DFILowPowerState,
    DFITimingParameters, DFIRequestQueueConfig
)


def main():
    print("=" * 60)
    print("DFI 5.0 Interface Example")
    print("=" * 60)

    # Create interface with default parameters
    print("\n1. Creating DFI 5.0 Interface...")
    dfi = DFI5Interface()
    print(f"   - Version: {dfi.version}")
    print(f"   - Supported commands: {[c.name for c in dfi.supported_commands]}")
    print(f"   - Current frequency: {dfi.frequency_mhz} MHz")
    print(f"   - Low power state: {dfi.lp_state.name}")

    # Show timing parameters
    print("\n2. DFI Timing Parameters:")
    timing = dfi.get_timing_parameters()
    print(f"   - PHY write latency: {timing.tPHY_wrlAT} cycles")
    print(f"   - PHY read latency: {timing.tPHY_rdLat} cycles")
    print(f"   - Frequency change latency: {timing.tFC_LATENCY} cycles")
    print(f"   - LP_CTRL enter/exit: {timing.tLP_CTRL_ENTER}/{timing.tLP_CTRL_EXIT} cycles")
    print(f"   - LP_DATA enter/exit: {timing.tLP_DATA_ENTER}/{timing.tLP_DATA_EXIT} cycles")
    print(f"   - Control update latency: {timing.tCTRLUPD_LATENCY} cycles")

    # Encode and queue commands
    print("\n3. Command Encoding and Queueing:")
    commands = [
        ('ACT', {'row': 100, 'bank': 0, 'channel': 0}, 8),
        ('RD', {'row': 0, 'bank': 0, 'channel': 0}, 8),
        ('WR', {'row': 0, 'bank': 1, 'channel': 0}, 12),
        ('PRE', {'row': 0, 'bank': 0, 'channel': 0}, 8),
    ]

    for cmd, addr_vec, priority in commands:
        dfi_req = dfi.encode_command(cmd, addr_vec, priority)
        dfi.queue_request(dfi_req)
        print(f"   - Queued: {cmd} addr_vec={addr_vec} priority={priority}")

    print(f"   - Queue size: {dfi.pending_request_count}")
    print(f"   - Available capacity: {dfi.queue_available_capacity}")

    # Dequeue and process commands
    print("\n4. Dequeuing Commands:")
    while not dfi.is_queue_full or dfi.pending_request_count > 0:
        req = dfi.get_next_request()
        if req is None:
            break
        print(f"   - Dequeued: {req.command.name} bank={req.bank} ch={req.channel} "
              f"priority={req.priority}")

    # Control update handshake
    print("\n5. Control Update Handshake:")
    print(f"   Initial state: ctrlupd_req={dfi.ctrlupd_req}, ctrlupd_ack={dfi.ctrlupd_ack}")

    success = dfi.request_ctrlupd()
    print(f"   After request_ctrlupd(): success={success}, ctrlupd_req={dfi.ctrlupd_req}")

    # Tick until acknowledged
    for cycle in range(10):
        dfi.tick()
        if dfi.ctrlupd_ack:
            print(f"   - Acknowledged at cycle {cycle + 1}")
            break

    # Frequency change protocol
    print("\n6. Frequency Change Protocol:")
    print(f"   Initial frequency: {dfi.frequency_mhz} MHz")

    success = dfi.request_freq_change(1200)
    print(f"   request_freq_change(1200): success={success}")

    dfi.enter_freq_change()
    print(f"   enter_freq_change(): FC state={dfi.get_freq_change_state().name}")

    # Complete frequency change
    for cycle in range(50):
        dfi.tick()
        if dfi.is_freq_change_complete():
            print(f"   - Frequency change complete at cycle {cycle + 1}")
            print(f"   - New frequency: {dfi.frequency_mhz} MHz")
            break

    # Low power state management
    print("\n7. Low Power State Management:")
    print(f"   Initial LP state: {dfi.lp_state.name}")

    # Enter LP_CTRL
    dfi.request_low_power(DFILowPowerState.LP_CTRL)
    print(f"   After request_low_power(LP_CTRL): lp_req={dfi.lp_req}")

    # Tick until acknowledged
    for cycle in range(10):
        dfi.tick()
        if dfi.lp_ack:
            print(f"   - LP_CTRL acknowledged at cycle {cycle + 1}")
            print(f"   - LP state: {dfi.lp_state.name}")
            break

    # Wakeup from low power
    print("\n8. Wakeup from Low Power:")
    dfi.dfi_wakeup()
    print(f"   After dfi_wakeup(): lp_wakeup={dfi._lp_wakeup}")

    for cycle in range(10):
        dfi.tick()
        if dfi.lp_state == DFILowPowerState.LP_IDLE:
            print(f"   - Back to LP_IDLE at cycle {cycle + 1}")
            break

    # Power management
    print("\n9. Power Management:")
    dfi.set_pwr_up_done(True)
    print(f"   set_pwr_up_done(True): pwr_up_done={dfi.pwr_up_done}")

    success = dfi.request_pwr_down()
    print(f"   request_pwr_down(): success={success}, pwr_down_req={dfi.pwr_down_req}")

    dfi.tick()
    print(f"   After tick: pwr_down_ack={dfi.pwr_down_ack}")

    # Training sequence
    print("\n10. PHY Training Sequence:")
    print(f"   Initial training state: complete={dfi.training_complete}, "
          f"in_progress={dfi.training_in_progress}")

    dfi.start_training()
    print(f"   After start_training(): in_progress={dfi.training_in_progress}")

    # Simulate training
    for cycle in range(100):
        dfi.tick()

    dfi.complete_training()
    print(f"   After complete_training(): complete={dfi.training_complete}, "
          f"in_progress={dfi.training_in_progress}")

    # Get signal states
    print("\n11. DFI Signal States:")
    signals = dfi.get_dfi_signals()
    print(f"   - ctrlupd_req: {signals.ctrlupd_req}")
    print(f"   - ctrlupd_ack: {signals.ctrlupd_ack}")
    print(f"   - freq_change_en: {signals.freq_change_en}")
    print(f"   - freq_change_ack: {signals.freq_change_ack}")
    print(f"   - lp_req: {signals.lp_req}")
    print(f"   - lp_ack: {signals.lp_ack}")
    print(f"   - lp_wakeup: {signals.lp_wakeup}")
    print(f"   - lp_state: {signals.lp_state.name}")
    print(f"   - phy_ready: {signals.phy_ready}")

    # Get statistics
    print("\n12. DFI Statistics:")
    stats = dfi.get_statistics()
    print(f"   - Commands sent: {stats['commands_sent']}")
    print(f"   - Frequency changes: {stats['freq_changes']}")
    print(f"   - LP transitions: {stats['lp_transitions']}")
    print(f"   - Control updates: {stats['ctrl_updates']}")
    print(f"   - Power cycles: {stats['power_cycles']}")
    print(f"   - Errors: {stats['errors']}")
    print(f"   - Queue utilization: {stats['queue_utilization_pct']:.1f}%")

    # Bandwidth calculation
    print("\n13. Theoretical Bandwidth:")
    bw_gbs = dfi.get_bandwidth_gbs()
    bw_tbs = dfi.get_bandwidth_tbs()
    print(f"   - At {dfi.frequency_mhz} MHz: {bw_gbs:.0f} GB/s ({bw_tbs:.2f} TB/s)")

    print("\n" + "=" * 60)
    print("DFI 5.0 interface example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()