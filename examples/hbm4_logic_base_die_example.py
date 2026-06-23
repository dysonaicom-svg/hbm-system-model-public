#!/usr/bin/env python3
"""
HBM4 Logic Base Die Comprehensive Usage Example

This example demonstrates the complete usage of the HBM4 Logic Base Die model,
focusing on practical integration patterns and common use cases.

KEY FEATURES COVERED:
1. HBM4LogicBaseDie initialization and configuration
2. PAM3 encoding configuration and signal analysis
3. Independent channel timing operations
4. DFI 5.0 interface integration
5. Command sequences: ACT -> RD -> PRE and ACT -> WR -> PRE

Run with: python examples/hbm4_logic_base_die_example.py

Based on JEDEC JESD270-4A HBM4 specification
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# SECTION 1: HBM4LogicBaseDie Initialization and Configuration
# =============================================================================
"""
The HBM4LogicBaseDie is the unified model integrating all Logic Base Die
functionality. It provides:
- Per-channel independent operation (JEDEC requirement for HBM4)
- DFI 5.0 interface support
- PAM3 signal encoding
- ECC/CRC error handling
- Lane repair capabilities
- Cycle-accurate timing model
"""

def section_1_initialization():
    """Demonstrate Logic Base Die initialization and configuration."""
    print("\n" + "=" * 70)
    print("SECTION 1: HBM4LogicBaseDie Initialization")
    print("=" * 70)

    # ----- Import the Logic Base Die module -----
    from model.dram.logic_base_die import (
        HBM4LogicBaseDie,
        LogicBaseDieConfig,
        ChannelContext,
        ChannelState,
    )

    # ----- Default Configuration -----
    # Uses sensible defaults for HBM4 at 8 GT/s
    print("\n--- Default Configuration ---")
    lbd = HBM4LogicBaseDie()
    print(f"  Created HBM4LogicBaseDie with defaults:")
    print(f"    - Num channels: {lbd.config.num_channels} (JEDEC standard)")
    print(f"    - Channel width: {lbd.config.channel_width} bits")
    print(f"    - PAM3 enabled: {lbd.config.pam3_enabled}")
    print(f"    - ECC enabled: {lbd.config.ecc_enabled}")
    print(f"    - CRC enabled: {lbd.config.crc_enabled}")
    print(f"    - Symbol rate: {lbd.config.symbol_rate_gbaud} Gbaud")
    print(f"    - Command buffer depth: {lbd.config.command_buffer_depth}")

    # ----- Custom Configuration -----
    # Configure for different speed grades or testing scenarios
    print("\n--- Custom Configuration for 12 Gbps Speed Grade ---")
    config_12g = LogicBaseDieConfig(
        num_channels=32,
        pam3_enabled=True,
        ecc_enabled=True,
        crc_enabled=True,
        command_buffer_depth=128,
        symbol_rate_gbaud=12.0,      # 12 Gbps speed grade
        tCK_ps=83.33,                 # Clock period: 1000/12 = 83.33 ps
    )
    lbd_12g = HBM4LogicBaseDie(config=config_12g)
    print(f"  Configured for 12 Gbps:")
    print(f"    - Symbol rate: {lbd_12g.config.symbol_rate_gbaud} Gbaud")
    print(f"    - tCK: {lbd_12g.config.tCK_ps:.2f} ps")

    # ----- Initialize the Model -----
    print("\n--- Initialization Sequence ---")
    lbd.initialize()
    print(f"  Initialized: {lbd.is_initialized}")

    # ----- Component Access -----
    print("\n--- Component Access ---")
    print(f"  PAM3 encoder: {lbd.pam3_encoder is not None}")
    print(f"  DFI interface: {lbd.dfi is not None}")
    print(f"  PHY manager: {lbd.phy_manager is not None}")
    print(f"  Lane repair: {lbd.lane_repair is not None}")
    print(f"  Data integrity (ECC/CRC): {lbd.data_integrity is not None}")

    # ----- Per-Channel Contexts -----
    # JEDEC requires independent per-channel operation
    print("\n--- Per-Channel Contexts (32 channels) ---")
    print(f"  Total channels: {len(lbd._channels)}")
    print(f"  Channel 0 state: {lbd._channels[0].state.value}")
    print(f"  Channel 15 state: {lbd._channels[15].state.value}")
    print(f"  Channel 31 state: {lbd._channels[31].state.value}")

    return lbd


# =============================================================================
# SECTION 2: PAM3 Encoding Configuration
# =============================================================================
"""
PAM3 (3-level Pulse Amplitude Modulation) is used in HBM4 for high-speed data
transmission. PAM3 encodes ~1.585 bits per symbol using three voltage levels.

Symbol encoding:
  - Bits 00 -> Level -1 (negative)
  - Bits 01 -> Level 0  (zero)
  - Bits 10 -> Level 0  (zero)
  - Bits 11 -> Level +1 (positive)

This provides better bandwidth efficiency than NRZ (1 bit/symbol) while
maintaining signal integrity at high data rates (8+ Gb/s).
"""

def section_2_pam3_encoding(lbd):
    """Demonstrate PAM3 encoding configuration and usage."""
    print("\n" + "=" * 70)
    print("SECTION 2: PAM3 Encoding Configuration")
    print("=" * 70)

    if lbd.pam3_encoder is None:
        print("  PAM3 encoder not enabled - enabling with config")
        lbd.pam3_encoder = lbd.pam3_encoder  # Already enabled by default
        return

    encoder = lbd.pam3_encoder
    signal_model = encoder.signal_model

    # ----- PAM3 Signal Model Parameters -----
    print("\n--- PAM3 Signal Model Parameters ---")
    print(f"  Symbol rate: {signal_model.symbol_rate / 1e9:.1f} Gbaud")
    print(f"  Unit interval: {signal_model.ui_ps:.2f} ps")
    print(f"  Voltage swing: {signal_model.voltage_swing:.2f} V")
    print(f"  Noise std dev: {signal_model.noise_std:.3f}")
    print(f"  Level voltages:")
    for level in [-1, 0, 1]:
        print(f"    Level {level:+d}: {signal_model.level_voltage[level]:+.2f} V")

    # ----- Encoding Data -----
    # PAM3 encodes 2 bits per symbol, so 16 bits -> 8 symbols
    print("\n--- Encoding Data Bits ---")
    test_data = 0xDEADBEEF  # 32 bits of test data
    num_bits = 32
    symbols = signal_model.encode(test_data, num_bits)

    print(f"  Input data: 0x{test_data:08X} ({num_bits} bits)")
    print(f"  Output symbols: {len(symbols)}")
    print(f"  Bits per symbol: {num_bits / len(symbols):.2f}")

    level_names = {-1: '-', 0: '0', 1: '+'}
    print(f"  Symbol sequence:")
    for i, sym in enumerate(symbols[:12]):
        print(f"    [{i:2d}] {level_names[sym.level]} ({sym.level:+.0f}) @ {sym.amplitude:+.2f}V")

    # ----- Decoding Symbols -----
    print("\n--- Decoding Symbols Back to Data ---")
    decoded_data, decoded_bits = signal_model.decode(symbols)
    print(f"  Decoded data: 0x{decoded_data:08X} ({decoded_bits} bits)")
    print(f"  Round-trip: {'SUCCESS' if decoded_data == test_data else 'MISMATCH'}")

    # ----- Eye Diagram Analysis -----
    # Eye diagram metrics assess signal integrity
    print("\n--- Eye Diagram Analysis ---")
    eye = signal_model.compute_eye_diagram(num_symbols=500)
    print(f"  Eye height: {eye.eye_height:.4f} V")
    print(f"  Eye width: {eye.eye_width:.4f} UI")
    print(f"  Level spacing: {eye.level_spacing:.4f} V")
    print(f"  SNR estimate: {eye.snr_db:.2f} dB")
    print(f"  BER estimate: {eye.ber_estimate:.2e}")

    # ----- Training Patterns -----
    # PAM3 uses special training patterns for PHY calibration
    print("\n--- Training Patterns ---")
    patterns = {
        'balanced': 'Alternating -1, 0, +1 for equal level distribution',
        'all_positive': 'All +1 level for DC balance testing',
        'all_negative': 'All -1 level',
        'prbs': 'Pseudo-random binary sequence',
    }

    for name, desc in patterns.items():
        pattern = encoder.insert_training_pattern(name, length=16)
        levels = [p.level for p in pattern]
        print(f"  '{name}': {levels[:8]}... ({desc})")

    # ----- Command/Address Encoding -----
    # Commands and addresses are also encoded with PAM3
    print("\n--- Command Encoding ---")
    cmd_bits = 0x0C3A  # 16-bit command/address value
    cmd_symbols = encoder.encode_command(cmd_bits, 16)
    print(f"  Command bits: 0b{cmd_bits:016b}")
    print(f"  Encoded symbols: {len(cmd_symbols)}")

    level_counts = {-1: 0, 0: 0, 1: 0}
    for sym in cmd_symbols:
        level_counts[sym.level] += 1
    print(f"  Level distribution: {level_counts}")

    # ----- Bandwidth Efficiency -----
    print("\n--- Bandwidth Efficiency Comparison ---")
    pam3_efficiency = signal_model.get_bandwidth_efficiency()
    print(f"  PAM3 bits/symbol: {pam3_efficiency:.4f}")
    print(f"  NRZ bits/symbol: 1.0000")
    print(f"  Improvement: {pam3_efficiency:.2f}x over NRZ")


# =============================================================================
# SECTION 3: Independent Channel Timing
# =============================================================================
"""
JEDEC HBM4 specification requires independent per-channel operation.
Each channel has its own:
- Local cycle counter
- Timing state
- Bank state machines
- Command queue

This enables true parallel operation across all 32 channels.
"""

def section_3_independent_channel_timing(lbd):
    """Demonstrate independent per-channel timing operations."""
    print("\n" + "=" * 70)
    print("SECTION 3: Independent Channel Timing")
    print("=" * 70)

    from model.dram.bank_state_machine import BankStateEnum

    # ----- Per-Channel Cycle Tracking -----
    print("\n--- Per-Channel Cycle Tracking ---")
    initial_cycles = [lbd._channels[ch].local_cycle for ch in range(0, 32, 8)]
    print(f"  Initial local cycles (ch 0,8,16,24): {initial_cycles}")

    # Advance some channels independently
    print("\n  Advancing Channel 0 by 100 cycles...")
    for _ in range(100):
        lbd.tick()

    final_cycles = [lbd._channels[ch].local_cycle for ch in range(0, 32, 8)]
    print(f"  Final local cycles (ch 0,8,16,24): {final_cycles}")
    print(f"  Channel 0 advanced: {final_cycles[0] > initial_cycles[0]}")
    print(f"  Other channels advanced: {final_cycles[1] > initial_cycles[1]}")

    # ----- Independent Bank Operations -----
    print("\n--- Independent Bank Operations ---")

    # Activate different banks on different channels simultaneously
    channel_bank_pairs = [
        (0, 0, 0x1000),
        (8, 1, 0x2000),
        (16, 2, 0x3000),
        (24, 3, 0x4000),
    ]

    for ch, bank, row in channel_bank_pairs:
        success = lbd.activate_bank(channel_id=ch, bank_id=bank, row=row)
        print(f"  Activate ch={ch:2d} bank={bank} row=0x{row:04X}: {'OK' if success else 'FAIL'}")

    # Wait for tRCD on each channel independently
    print("\n  Waiting for tRCD (8 cycles) on each channel...")
    for _ in range(8):
        lbd.tick()

    # Check bank states across channels
    print("\n--- Bank States After Independent Activation ---")
    for ch, bank, _ in channel_bank_pairs:
        state = lbd.get_bank_state(ch, bank)
        is_active = state == BankStateEnum.ACTIVE if state else False
        print(f"  Channel {ch:2d} Bank {bank}: {state} ({'ACTIVE' if is_active else 'NOT ACTIVE'})")

    # ----- Channel Context Tracking -----
    print("\n--- Channel Context Tracking ---")
    for ch in [0, 8, 16, 24]:
        ctx = lbd._channels[ch]
        print(f"  Channel {ch}:")
        print(f"    State: {ctx.state.value}")
        print(f"    Local cycle: {ctx.local_cycle}")
        print(f"    Last ACT cycle: {ctx.last_act_cycle}")
        print(f"    Open row: 0x{ctx.open_row:04X}" if ctx.open_row else "    Open row: None")

    # ----- Row Hit Detection Per Channel -----
    print("\n--- Row Hit Detection ---")
    for ch, bank, expected_row in channel_bank_pairs:
        hit = lbd.is_row_hit(ch, bank, expected_row)
        miss = lbd.is_row_hit(ch, bank, expected_row + 1)
        print(f"  Channel {ch}: row=0x{expected_row:04X} hit={hit}, different row miss={miss}")

    # ----- Timing Constraint Validation -----
    print("\n--- Timing Constraint Validation ---")

    # tRC is the minimum time between activations
    print(f"  tRC constraint (min cycles between ACT on same bank): {lbd.spec.nRC}")

    # Check if we can activate same bank again (tRC not satisfied yet)
    for ch, bank, _ in channel_bank_pairs[:1]:
        can_act = lbd.can_activate_bank(ch, bank)
        print(f"  Can re-activate ch={ch} bank={bank}: {can_act} (tRC not satisfied)")

    # Wait for tRC
    print("\n  Waiting for tRC...")
    for _ in range(lbd.spec.nRC):
        lbd.tick()

    can_act = lbd.can_activate_bank(0, 0)
    print(f"  Can re-activate ch=0 bank=0 after tRC: {can_act}")


# =============================================================================
# SECTION 4: DFI 5.0 Interface Integration
# =============================================================================
"""
DFI 5.0 (DDR PHY Interface) is the standard interface between memory controller
and PHY. The HBM4LogicBaseDie integrates DFI 5.0 for:

- Command encoding (ACT, PRE, RD, WR, REFab, etc.)
- Control update handshake (dfi_ctrlupd_req/ack)
- Frequency change protocol (dfi_freq_change_en/ack)
- Low power state management (LP_IDLE, LP_CTRL, LP_DATA)
- Power management (dfi_pwr_up_done, dfi_pwr_down_ack)

DFI 5.0 signals:
- dfi_ctrlupd_req/ack: Control parameter update handshake
- dfi_freq_change_en/ack: Frequency change protocol
- lp_req/lp_ack: Low power entry/exit
- dfi_pwr_up_done: Power-up completion indicator
"""

def section_4_dfi_interface(lbd):
    """Demonstrate DFI 5.0 interface integration."""
    print("\n" + "=" * 70)
    print("SECTION 4: DFI 5.0 Interface Integration")
    print("=" * 70)

    from model.dram.dfi_interface import (
        DFI5Interface,
        DFICommand,
        DFIRequest,
        DFILowPowerState,
    )

    # Reset for clean test
    lbd.reset()
    lbd.initialize()

    # ----- DFI Interface Access -----
    print("\n--- DFI Interface Properties ---")
    print(f"  DFI version: {lbd.dfi.version}")
    print(f"  Low-power state: {lbd.dfi.lp_state.value}")
    print(f"  Frequency: {lbd.dfi.frequency_mhz} MHz")
    print(f"  Is ready: {lbd.dfi.is_ready()}")

    # ----- DFI Timing Parameters -----
    print("\n--- DFI Timing Parameters ---")
    timing = lbd.dfi.get_timing_parameters()
    print(f"  tPHY_wrlAT: {timing.tPHY_wrlAT} cycles")
    print(f"  tPHY_rdLat: {timing.tPHY_rdLat} cycles")
    print(f"  tFC_LATENCY: {timing.tFC_LATENCY} cycles")
    print(f"  tLP_CTRL_ENTER: {timing.tLP_CTRL_ENTER} cycles")
    print(f"  tLP_DATA_ENTER: {timing.tLP_DATA_ENTER} cycles")

    # ----- Submit Commands via DFI -----
    print("\n--- Submitting Commands via DFI ---")

    # ACT command
    success = lbd.submit_dfi_act(channel=0, bank=0, row=0x1000)
    print(f"  Submit ACT (ch=0, bank=0, row=0x1000): {'OK' if success else 'FAIL'}")

    # READ command
    success = lbd.submit_dfi_read(channel=0, bank=0, column=0x100)
    print(f"  Submit READ (ch=0, bank=0, col=0x100): {'OK' if success else 'FAIL'}")

    # WRITE command
    success = lbd.submit_dfi_write(channel=1, bank=1, column=0x200)
    print(f"  Submit WRITE (ch=1, bank=1, col=0x200): {'OK' if success else 'FAIL'}")

    # PRECHARGE command
    success = lbd.submit_dfi_pre(channel=0, bank=0)
    print(f"  Submit PRE (ch=0, bank=0): {'OK' if success else 'FAIL'}")

    # REFRESH command
    success = lbd.submit_dfi_refresh(channel=2)
    print(f"  Submit REFRESH (ch=2): {'OK' if success else 'FAIL'}")

    print(f"  Pending DFI requests: {lbd.dfi_pending_count}")

    # ----- Retrieve and Process Requests -----
    print("\n--- Retrieving DFI Requests ---")
    while lbd.dfi_pending_count > 0:
        request = lbd.get_next_dfi_request()
        if request:
            print(f"  Request: {request.command.name:8s} "
                  f"ch={request.channel:2d} "
                  f"bank={request.bank:2d} "
                  f"addr=0x{request.address:04X}")
            print(f"           timestamp={request.timestamp}")

    # ----- DFI Signal States -----
    print("\n--- DFI Signal States ---")
    signals = lbd.get_dfi_signals()
    print(f"  ctrlupd_req: {signals.ctrlupd_req}")
    print(f"  ctrlupd_ack: {signals.ctrlupd_ack}")
    print(f"  freq_change_en: {signals.freq_change_en}")
    print(f"  freq_change_ack: {signals.freq_change_ack}")
    print(f"  pwr_up_done: {signals.pwr_up_done}")
    print(f"  lp_req: {signals.lp_req}")
    print(f"  lp_ack: {signals.lp_ack}")
    print(f"  lp_state: {signals.lp_state}")
    print(f"  phy_ready: {signals.phy_ready}")

    # ----- Control Update Handshake -----
    print("\n--- Control Update Handshake ---")
    print(f"  Initial ctrlupd_req: {lbd.dfi.ctrlupd_req}")

    success = lbd.dfi.request_ctrlupd()
    print(f"  Request ctrlupd: {'OK' if success else 'FAIL'}")
    print(f"  ctrlupd_req asserted: {lbd.dfi.ctrlupd_req}")

    # Advance cycles to complete handshake
    for _ in range(10):
        lbd.tick()

    print(f"  After 10 cycles ctrlupd_ack: {lbd.dfi.ctrlupd_ack}")

    # ----- Low Power State Transitions -----
    print("\n--- Low Power State Transitions ---")
    print(f"  Current state: {lbd.dfi.lp_state}")

    # Request LP_CTRL
    print("\n  Requesting LP_CTRL state...")
    try:
        success = lbd.dfi.request_low_power(DFILowPowerState.LP_CTRL)
        print(f"  Request LP_CTRL: {'OK' if success else 'FAIL'}")
        print(f"  lp_req asserted: {lbd.dfi.lp_req}")

        # Advance cycles
        for _ in range(10):
            lbd.tick()

        print(f"  lp_ack: {lbd.dfi.lp_ack}")
    except Exception as e:
        print(f"  Exception: {e}")

    # ----- DFI Queue Statistics -----
    print("\n--- DFI Queue Statistics ---")
    stats = lbd.dfi.get_statistics()
    print(f"  Commands sent: {stats['commands_sent']}")
    print(f"  Commands completed: {stats['commands_completed']}")
    print(f"  Frequency changes: {stats['freq_changes']}")
    print(f"  LP transitions: {stats['lp_transitions']}")
    print(f"  Errors: {stats['errors']}")


# =============================================================================
# SECTION 5: Command Sequences (ACT -> RD/WR -> PRE)
# =============================================================================
"""
Complete command sequences for memory operations:

READ SEQUENCE:
1. ACT (Activate) - Opens a row in a bank
2. Wait tRCD (RAS to CAS delay)
3. RD (Read) - Read data from open row
4. Wait tRTPS (Read to precharge)
5. PRE (Precharge) - Close the row

WRITE SEQUENCE:
1. ACT (Activate) - Opens a row in a bank
2. Wait tRCD (RAS to CAS delay)
3. WR (Write) - Write data to open row
4. Wait tWTR (Write to read turnaround)
5. PRE (Precharge) - Close the row

HBM4 Timing Parameters (@ 8 GT/s, tCK = 125 ps):
- tRCD: 8 cycles (RAS to CAS delay)
- tCL: 8 cycles (CAS latency)
- tCWL: 3 cycles (CAS write latency)
- tRTPS: 2 cycles (Read to precharge)
- tRP: 8 cycles (Precharge)
- tRAS: 20 cycles (Row active time)
- tRC: 22 cycles (Row cycle time)
"""

def section_5_command_sequences(lbd):
    """Demonstrate complete command sequences."""
    print("\n" + "=" * 70)
    print("SECTION 5: Command Sequences (ACT -> RD/WR -> PRE)")
    print("=" * 70)

    from model.dram.bank_state_machine import BankStateEnum

    # Reset for clean test
    lbd.reset()
    lbd.initialize()

    # ----- READ SEQUENCE -----
    print("\n" + "-" * 60)
    print("READ SEQUENCE: ACT -> RD -> PRE")
    print("-" * 60)

    channel = 0
    bank = 0
    row = 0x1000
    column = 0x100

    print(f"\n  Initial state (ch={channel}, bank={bank}):")
    print(f"  Bank state: {lbd.get_bank_state(channel, bank)}")

    # Step 1: ACT (Activate)
    print(f"\n  [Step 1] ACTIVATE")
    print(f"    Command: ACT ch={channel} bank={bank} row=0x{row:04X}")
    success = lbd.activate_bank(channel, bank, row)
    print(f"    Result: {'SUCCESS' if success else 'FAILED'}")

    for _ in range(lbd.spec.nRCDRD):
        lbd.tick()
    print(f"    Waited tRCD={lbd.spec.nRCDRD} cycles")

    bank_state = lbd.get_bank_state(channel, bank)
    print(f"    Bank state: {bank_state}")

    # Step 2: RD (Read)
    print(f"\n  [Step 2] READ")
    print(f"    Command: RD ch={channel} bank={bank} col=0x{column:04X}")
    can_read = lbd.can_read_bank(channel, bank)
    print(f"    Can read: {can_read}")

    if can_read:
        success = lbd.read_bank(channel, bank)
        print(f"    Result: {'SUCCESS' if success else 'FAILED'}")

    # Advance for CAS latency
    for _ in range(lbd.spec.nCL):
        lbd.tick()
    print(f"    Waited tCL={lbd.spec.nCL} cycles (CAS latency)")

    # Complete the read operation
    lbd.complete_bank_read(channel, bank)

    for _ in range(lbd.spec.nRTPS):
        lbd.tick()
    print(f"    Waited tRTPS={lbd.spec.nRTPS} cycles (read to precharge)")

    # Step 3: PRE (Precharge)
    print(f"\n  [Step 3] PRECHARGE")
    print(f"    Command: PRE ch={channel} bank={bank}")
    can_pre = lbd.can_precharge_bank(channel, bank)
    print(f"    Can precharge: {can_pre}")

    if can_pre:
        success = lbd.precharge_bank(channel, bank)
        print(f"    Result: {'SUCCESS' if success else 'FAILED'}")

    for _ in range(lbd.spec.nRP):
        lbd.tick()
    print(f"    Waited tRP={lbd.spec.nRP} cycles (precharge)")

    print(f"\n  Final state (ch={channel}, bank={bank}):")
    print(f"  Bank state: {lbd.get_bank_state(channel, bank)}")
    ctx = lbd._channels[channel]
    print(f"  Channel cycle: {ctx.local_cycle}")

    # ----- WRITE SEQUENCE -----
    print("\n" + "-" * 60)
    print("WRITE SEQUENCE: ACT -> WR -> PRE")
    print("-" * 60)

    channel = 1
    bank = 1
    row = 0x2000
    column = 0x200
    write_data = 0xDEADBEEF

    print(f"\n  Initial state (ch={channel}, bank={bank}):")
    print(f"  Bank state: {lbd.get_bank_state(channel, bank)}")

    # Step 1: ACT (Activate)
    print(f"\n  [Step 1] ACTIVATE")
    print(f"    Command: ACT ch={channel} bank={bank} row=0x{row:04X}")
    success = lbd.activate_bank(channel, bank, row)
    print(f"    Result: {'SUCCESS' if success else 'FAILED'}")

    for _ in range(lbd.spec.nRCDRD):
        lbd.tick()
    print(f"    Waited tRCD={lbd.spec.nRCDRD} cycles")

    bank_state = lbd.get_bank_state(channel, bank)
    print(f"    Bank state: {bank_state}")

    # Step 2: WR (Write)
    print(f"\n  [Step 2] WRITE")
    print(f"    Command: WR ch={channel} bank={bank} col=0x{column:04X} data=0x{write_data:08X}")
    can_write = lbd.can_write_bank(channel, bank)
    print(f"    Can write: {can_write}")

    if can_write:
        # Use process_command for data handling with ECC
        ok, msg = lbd.process_command(channel, 'WR', column, write_data)
        print(f"    Result: {'SUCCESS' if ok else 'FAILED'}")
        if not ok:
            print(f"    Message: {msg}")

    # Advance for CWL
    for _ in range(lbd.spec.nCWL):
        lbd.tick()
    print(f"    Waited tCWL={lbd.spec.nCWL} cycles (CAS write latency)")

    # Complete the write
    lbd.complete_bank_write(channel, bank)

    for _ in range(lbd.spec.nWR):
        lbd.tick()
    print(f"    Waited tWR={lbd.spec.nWR} cycles (write recovery)")

    # Step 3: PRE (Precharge)
    print(f"\n  [Step 3] PRECHARGE")
    print(f"    Command: PRE ch={channel} bank={bank}")
    can_pre = lbd.can_precharge_bank(channel, bank)
    print(f"    Can precharge: {can_pre}")

    if can_pre:
        success = lbd.precharge_bank(channel, bank)
        print(f"    Result: {'SUCCESS' if success else 'FAILED'}")

    for _ in range(lbd.spec.nRP):
        lbd.tick()
    print(f"    Waited tRP={lbd.spec.nRP} cycles (precharge)")

    print(f"\n  Final state (ch={channel}, bank={bank}):")
    print(f"  Bank state: {lbd.get_bank_state(channel, bank)}")
    ctx = lbd._channels[channel]
    print(f"  Channel cycle: {ctx.local_cycle}")

    # ----- REFRESH SEQUENCE -----
    print("\n" + "-" * 60)
    print("REFRESH SEQUENCE: REFab")
    print("-" * 60)

    channel = 2

    print(f"\n  [Step 1] REFRESH ALL BANKS")
    print(f"    Command: REFab ch={channel}")
    success = lbd.refresh_bank(channel, 0)
    print(f"    Result: {'SUCCESS' if success else 'FAILED'}")

    ctx = lbd._channels[channel]
    print(f"    Channel state: {ctx.state.value}")

    # Advance for RFC
    for _ in range(lbd.spec.nRFC):
        lbd.tick()
    print(f"    Waited tRFC={lbd.spec.nRFC} cycles (refresh cycle time)")

    # Complete refresh
    lbd.complete_bank_refresh(channel, 0)

    ctx = lbd._channels[channel]
    print(f"    Channel state after refresh: {ctx.state.value}")

    # ----- Timing Summary -----
    print("\n" + "-" * 60)
    print("TIMING SUMMARY (HBM4 @ 8 GT/s, tCK = 125 ps)")
    print("-" * 60)
    print(f"  tRCDRD: {lbd.spec.nRCDRD} cycles = {lbd.spec.nRCDRD * lbd.spec.tCK_ps} ps")
    print(f"  tCL:    {lbd.spec.nCL} cycles = {lbd.spec.nCL * lbd.spec.tCK_ps} ps")
    print(f"  tCWL:   {lbd.spec.nCWL} cycles = {lbd.spec.nCWL * lbd.spec.tCK_ps} ps")
    print(f"  tRTPS:  {lbd.spec.nRTPS} cycles = {lbd.spec.nRTPS * lbd.spec.tCK_ps} ps")
    print(f"  tWR:    {lbd.spec.nWR} cycles = {lbd.spec.nWR * lbd.spec.tCK_ps} ps")
    print(f"  tRP:    {lbd.spec.nRP} cycles = {lbd.spec.nRP * lbd.spec.tCK_ps} ps")
    print(f"  tRAS:   {lbd.spec.nRAS} cycles = {lbd.spec.nRAS * lbd.spec.tCK_ps} ps")
    print(f"  tRC:    {lbd.spec.nRC} cycles = {lbd.spec.nRC * lbd.spec.tCK_ps} ps")
    print(f"  tRFC:   {lbd.spec.nRFC} cycles = {lbd.spec.nRFC * lbd.spec.tCK_ps} ps")


# =============================================================================
# SECTION 6: Complete Workflow Example
# =============================================================================

def section_6_complete_workflow():
    """Demonstrate a complete workflow with multiple channels."""
    print("\n" + "=" * 70)
    print("SECTION 6: Complete Workflow Example")
    print("=" * 70)

    from model.dram.logic_base_die import HBM4LogicBaseDie, LogicBaseDieConfig

    # Create Logic Base Die
    config = LogicBaseDieConfig(
        num_channels=8,      # Use 8 channels for demonstration
        pam3_enabled=True,
        ecc_enabled=True,
        crc_enabled=True,
    )
    lbd = HBM4LogicBaseDie(config=config)

    # Initialize
    print("\n--- Initialize ---")
    lbd.initialize()
    print(f"  Initialized: {lbd.is_initialized}")

    # Simulate traffic pattern on multiple channels
    print("\n--- Traffic Pattern Simulation ---")

    # Define traffic pattern
    traffic = [
        # (channel, bank, row, operation, data)
        (0, 0, 0x1000, 'RD', None),
        (1, 0, 0x2000, 'WR', 0x12345678),
        (2, 1, 0x3000, 'RD', None),
        (3, 1, 0x4000, 'WR', 0xABCDEF00),
        (4, 2, 0x5000, 'RD', None),
        (5, 2, 0x6000, 'WR', 0xDEADBEEF),
        (6, 3, 0x7000, 'RD', None),
        (7, 3, 0x8000, 'WR', 0xCAFEBABE),
    ]

    print("\n  Issuing ACT commands...")
    for ch, bank, row, op, data in traffic:
        if op == 'RD':
            lbd.activate_bank(ch, bank, row)
            for _ in range(lbd.spec.nRCDRD):
                lbd.tick()
            lbd.read_bank(ch, bank)
        else:
            lbd.activate_bank(ch, bank, row)
            for _ in range(lbd.spec.nRCDRD):
                lbd.tick()
            lbd.process_command(ch, 'WR', 0x100, data)

    print(f"  Commands issued. Current cycle: {lbd.cycle}")

    # Advance for data transfer
    print("\n  Advancing for data transfer...")
    for _ in range(50):
        lbd.tick()

    print("\n  Issuing PRE commands...")
    for ch, bank, row, op, data in traffic:
        lbd.precharge_bank(ch, bank)

    # Get final statistics
    print("\n--- Final Statistics ---")
    stats = lbd.get_stats()
    print(f"  Global cycle: {stats['global_cycle']}")
    print(f"  Total commands: {stats['total_commands']}")
    print(f"  Total errors: {stats['total_errors']}")

    status = lbd.get_status()
    print(f"  DFI pending requests: {status['dfi']['pending_requests']}")
    print(f"  Command buffer size: {status['command_buffer']['size']}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run all HBM4 Logic Base Die examples."""
    print("\n" + "=" * 70)
    print("HBM4 Logic Base Die Comprehensive Usage Example")
    print("=" * 70)
    print("\nThis example demonstrates practical usage of HBM4 Logic Base Die:")
    print("  1. HBM4LogicBaseDie initialization and configuration")
    print("  2. PAM3 encoding configuration and signal analysis")
    print("  3. Independent per-channel timing operations")
    print("  4. DFI 5.0 interface integration")
    print("  5. Command sequences (ACT -> RD/WR -> PRE)")
    print("  6. Complete workflow example")
    print("\nBased on JEDEC JESD270-4A HBM4 Specification")

    try:
        # Section 1: Initialization
        lbd = section_1_initialization()

        # Section 2: PAM3 Encoding
        section_2_pam3_encoding(lbd)

        # Section 3: Independent Channel Timing
        section_3_independent_channel_timing(lbd)

        # Section 4: DFI Interface
        section_4_dfi_interface(lbd)

        # Section 5: Command Sequences
        section_5_command_sequences(lbd)

        # Section 6: Complete Workflow
        section_6_complete_workflow()

        # ----- Final Summary -----
        print("\n" + "=" * 70)
        print("EXAMPLE COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nThis example covered:")
        print("  1. HBM4LogicBaseDie initialization and configuration")
        print("     - Default and custom configurations")
        print("     - 32-channel architecture")
        print("  2. PAM3 encoding configuration")
        print("     - 3-level signal encoding (-1, 0, +1)")
        print("     - ~1.585 bits per symbol efficiency")
        print("     - Eye diagram analysis")
        print("     - Training patterns")
        print("  3. Independent channel timing")
        print("     - Per-channel local cycle counters")
        print("     - Independent bank operations")
        print("     - Row hit detection per channel")
        print("  4. DFI 5.0 interface integration")
        print("     - Command submission (ACT, RD, WR, PRE, REF)")
        print("     - Control update handshake")
        print("     - Low power state management")
        print("  5. Command sequences")
        print("     - READ: ACT -> tRCD -> RD -> tRTPS -> PRE")
        print("     - WRITE: ACT -> tRCD -> WR -> tWR -> PRE")
        print("     - REFRESH: REFab -> tRFC")
        print("  6. Complete workflow")
        print("     - Multi-channel traffic simulation")
        print("     - Statistics collection")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\nError during example execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())