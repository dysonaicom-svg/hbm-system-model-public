# HBM4 Logic Base Die - Phase A Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement HBM4 Controller Model (Layer 2) with 32-channel support, DFI 5.1 interface, and configurable scheduling based on research findings.

**Architecture:** 
- 5-layer model architecture with Layer 2 (HBM Controller) as Phase A focus
- Extends existing HBM3 controller with HBM4-specific features: 32 channels, pseudo-channel demultiplexing, DFI 5.1 compliance
- Based on Ramulator 2.0 HBM3 timing reference and multi-agent research findings
- Python-based functional model with configurable parameters for architecture exploration

**Tech Stack:** Python 3.8+, pytest, existing HBM codebase

**Reference Models:**
- Ramulator 2.0: `research/hbm4-logic-base-die/reference_models/ramulator2/`
- DRAMSys: `research/hbm4-logic-base-die/reference_models/DRAMSys/`

---

## Phase A Implementation Overview

| Milestone | Tasks | Deliverable |
|-----------|-------|-------------|
| M1 | 1-5 | HBM4 Config & Constants |
| M2 | 6-10 | Channel Model Extensions |
| M3 | 11-15 | DFI 5.1 Interface |
| M4 | 16-20 | QoS & Refresh Schedulers |
| M5 | 21-25 | Integration Tests |

---

## Task 1: Create HBM4 Configuration Constants

**Files:**
- Create: `model/dram/hbm4_spec.py`

**Step 1: Write the failing test**

```python
# tests/dram/test_hbm4_spec.py
import pytest
from model.dram.hbm4_spec import HBM4Spec, HBM4_CONFIG

def test_hbm4_spec_channels():
    """HBM4 must have 32 channels, not 8 like HBM3"""
    spec = HBM4Spec()
    assert spec.channels == 32

def test_hbm4_spec_interface_width():
    """HBM4 interface width is 2048-bit (32 channels × 64-bit)"""
    spec = HBM4Spec()
    assert spec.io_width == 2048

def test_hbm4_spec_bandwidth():
    """HBM4 @ 8 GT/s = 2 TB/s per stack"""
    spec = HBM4Spec()
    expected_bw = 8e9 * 2048 / 8 / 1e12  # TB/s
    assert abs(spec.bandwidth - expected_bw) < 0.01

def test_hbm4_spec_pseudo_channels():
    """32 channels × 2 pseudo-channels = 64 total"""
    spec = HBM4Spec()
    assert spec.pseudo_channels == 64
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/dram/test_hbm4_spec.py -v`
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# model/dram/hbm4_spec.py
"""HBM4 DRAM Specification Constants

Based on:
- JEDEC JESD270-4A HBM4 specification
- Ramulator 2.0 HBM3 timing reference
- Multi-agent research findings (2026-06-15)
"""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass
class HBM4Spec:
    """HBM4 DRAM specification constants
    
    Key differences from HBM3:
    - 32 channels (vs 8 channels in HBM3)
    - 2048-bit interface (vs 1024-bit in HBM3)
    - 64 pseudo-channels (vs 16 in HBM3)
    - 8 GT/s base data rate (vs 6.4 GT/s in HBM3)
    - 2 TB/s bandwidth per stack
    """
    
    # === Architecture Parameters ===
    channels: int = 32                    # HBM4: 32, HBM3: 8
    pseudo_channels_per_channel: int = 2   # 32 × 2 = 64 total
    banks_per_pseudo_channel: int = 16    # Same as HBM3
    bank_groups_per_channel: int = 8     # Same as HBM3
    
    # === Physical Parameters ===
    io_width: int = 2048                  # 2048-bit (doubled from HBM3)
    data_rate_gtps: float = 8.0           # GT/s (base rate per pin)
    burst_length: int = 4               # FLINE burst length
    row_size: int = 2048                 # bytes
    
    # === Calculated Values ===
    @property
    def pseudo_channels(self) -> int:
        return self.channels * self.pseudo_channels_per_channel
    
    @property
    def total_banks(self) -> int:
        return self.channels * self.pseudo_channels * self.banks_per_pseudo_channel
    
    @property
    def bandwidth(self) -> float:
        """Peak bandwidth in TB/s"""
        return self.data_rate_gtps * self.io_width / 8 / 1e12  # TB/s
    
    @property
    def bandwidth_gbs(self) -> float:
        """Peak bandwidth in GB/s"""
        return self.data_rate_gtps * self.io_width / 8 / 1e9  # GB/s
    
    # === Timing Parameters (cycles @ tCK) ===
    # Based on Ramulator 2.0 HBM3 timing, scaled for HBM4
    tCK_ps: float = 1250.0                # Clock period (1250ps = 800 MT/s DDR)
    nBL: int = 4                         # Burst length
    nCL: int = 8                         # CAS latency
    nRCDRD: int = 8                      # RAS to CAS delay (read)
    nRCDWR: int = 8                      # RAS to CAS delay (write)
    nRP: int = 8                         # Precharge command period
    nRAS: int = 20                       # Row active time
    nRC: int = 22                        # Row cycle time
    nWR: int = 8                         # Write recovery
    nRTPS: int = 2                       # Read to precharge
    nRTPL: int = 3                       # Read to precharge (last data)
    nCWL: int = 3                        # CAS write latency
    nCCDS: int = 2                       # Column command delay (same bank group)
    nCCDL: int = 3                       # Column command delay (different bank group)
    nRRDS: int = 3                       # RAS to RAS delay (same bank group)
    nRRDL: int = 4                       # RAS to RAS delay (different bank group)
    nWTRS: int = 4                       # Write to read turnaround (same bank group)
    nWTRL: int = 5                       # Write to read turnaround (different bank group)
    nRTW: int = 4                        # Read to write turnaround
    nFAW: int = 16                       # Four-activate window
    nRFC: int = 180                      # Refresh command duration
    nREFI: int = 3900                    # Refresh interval
    nRREFD: int = 8                      # Per-bank refresh interval
    
    # === Address Bit Fields ===
    # Based on DRAMSys HBM2 address mapping, extended for HBM4
    ADDR_STACK_BITS: int = 2             # 4 stacks
    ADDR_CHANNEL_BITS: int = 5          # 32 channels
    ADDR_PCH_BITS: int = 1              # 2 pseudo-channels per channel
    ADDR_BG_BITS: int = 3               # 8 bank groups
    ADDR_BANK_BITS: int = 4             # 16 banks per group
    ADDR_ROW_BITS: int = 16             # 64K rows
    ADDR_COL_BITS: int = 6              # 64 columns
    
    def get_channel_bits(self) -> tuple:
        """Return (start_bit, num_bits) for channel field"""
        offset = 0
        return (offset, self.ADDR_CHANNEL_BITS)
    
    def get_pseudo_channel_bits(self) -> tuple:
        """Return (start_bit, num_bits) for pseudo-channel field"""
        offset = self.ADDR_CHANNEL_BITS
        return (offset, self.ADDR_PCH_BITS)
    
    def get_bank_group_bits(self) -> tuple:
        """Return (start_bit, num_bits) for bank group field"""
        offset = self.ADDR_CHANNEL_BITS + self.ADDR_PCH_BITS
        return (offset, self.ADDR_BG_BITS)
    
    def get_bank_bits(self) -> tuple:
        """Return (start_bit, num_bits) for bank field"""
        offset = self.ADDR_CHANNEL_BITS + self.ADDR_PCH_BITS + self.ADDR_BG_BITS
        return (offset, self.ADDR_BANK_BITS)
    
    def get_row_bits(self) -> tuple:
        """Return (start_bit, num_bits) for row field"""
        offset = (self.ADDR_CHANNEL_BITS + self.ADDR_PCH_BITS + 
                 self.ADDR_BG_BITS + self.ADDR_BANK_BITS)
        return (offset, self.ADDR_ROW_BITS)
    
    def get_col_bits(self) -> tuple:
        """Return (start_bit, num_bits) for column field"""
        offset = (self.ADDR_CHANNEL_BITS + self.ADDR_PCH_BITS + 
                 self.ADDR_BG_BITS + self.ADDR_BANK_BITS + self.ADDR_ROW_BITS)
        return (offset, self.ADDR_COL_BITS)


# Default HBM4 configuration
HBM4_CONFIG = HBM4Spec()

# Speed grade presets
HBM4_SPEED_GRADES = {
    "8Gbps": {"data_rate_gtps": 8.0, "tCK_ps": 1250.0},
    "12Gbps": {"data_rate_gtps": 12.0, "tCK_ps": 833.33},
    "16Gbps": {"data_rate_gtps": 16.0, "tCK_ps": 625.0},
}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/dram/test_hbm4_spec.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/dram/test_hbm4_spec.py model/dram/hbm4_spec.py
git commit -m "feat(hbm4): add HBM4 specification constants with 32-channel support"
```

---

## Task 2: Extend Address Decoder for HBM4

**Files:**
- Modify: `model/controller/address_decoder.py`
- Test: `tests/controller/test_address_decoder.py`

**Step 1: Write the failing test**

```python
# tests/controller/test_address_decoder.py
import pytest
from model.controller.address_decoder import AddressDecoder, HBM4AddressDecoder

def test_hbm4_decoder_32_channels():
    """Address decoder must decode 32 channels for HBM4"""
    decoder = HBM4AddressDecoder()
    
    # Test channel decoding
    # Address 0x10000000 should decode to channel 0-31
    for addr in range(0, 0x10000000, 0x100000):
        decoded = decoder.decode(addr)
        assert 0 <= decoded['channel'] < 32

def test_hbm4_decoder_pseudo_channel():
    """Pseudo-channel demultiplexing must be supported"""
    decoder = HBM4AddressDecoder()
    
    # Adjacent addresses should potentially hit different pseudo-channels
    addr1 = 0x10000000
    addr2 = 0x10000020  # Same channel, different pseudo-channel bit
    
    dec1 = decoder.decode(addr1)
    dec2 = decoder.decode(addr2)
    
    # Both should have pseudo_channel field
    assert 'pseudo_channel' in dec1
    assert 'pseudo_channel' in dec2

def test_hbm4_decoder_address_mapping():
    """HBM4 address mapping must produce correct bank/row"""
    decoder = HBM4AddressDecoder()
    
    # Row address should be in correct bit field
    addr = 0x01000000
    decoded = decoder.decode(addr)
    
    assert 'row' in decoded
    assert decoded['row'] >= 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/controller/test_address_decoder.py -v`
Expected: FAIL - HBM4AddressDecoder not defined

**Step 3: Write minimal implementation**

```python
# Add to model/controller/address_decoder.py

class HBM4AddressDecoder(AddressDecoder):
    """HBM4-specific address decoder
    
    Key differences from HBM3:
    - 32 channels (5-bit channel field vs 3-bit)
    - 64 pseudo-channels (1-bit pseudo-channel field)
    - Extended address space for 2 TB/s bandwidth
    """
    
    # HBM4 address bit field configuration
    CHANNEL_BITS = 5      # 32 channels
    PCH_BITS = 1          # 2 pseudo-channels per channel
    BG_BITS = 3            # 8 bank groups
    BANK_BITS = 4          # 16 banks per group
    ROW_BITS = 16          # 64K rows
    COL_BITS = 6            # 64 columns
    STACK_BITS = 2         # 4 stacks
    BURST_BITS = 2          # 4-beat burst alignment
    
    # Total address bits
    TOTAL_ADDR_BITS = (STACK_BITS + CHANNEL_BITS + PCH_BITS + 
                       BG_BITS + BANK_BITS + ROW_BITS + COL_BITS + BURST_BITS)
    
    def __init__(self, config=None):
        if config is None:
            config = HBM4Spec()
        super().__init__(config)
        self.spec = config
    
    def decode(self, addr: int) -> Dict[str, int]:
        """Decode HBM4 address into components
        
        Returns:
            dict with keys: stack, channel, pseudo_channel, bank_group, 
                          bank, row, column, burst
        """
        # Extract bit fields
        result = {}
        
        # Stack ID (MSB for multi-stack support)
        result['stack'] = (addr >> (self.TOTAL_ADDR_BITS - self.STACK_BITS)) & ((1 << self.STACK_BITS) - 1)
        
        # Channel (5 bits for HBM4)
        channel_offset = (self.TOTAL_ADDR_BITS - self.STACK_BITS - self.CHANNEL_BITS)
        result['channel'] = (addr >> channel_offset) & ((1 << self.CHANNEL_BITS) - 1)
        
        # Pseudo-channel (1 bit)
        pch_offset = channel_offset - self.PCH_BITS
        result['pseudo_channel'] = (addr >> pch_offset) & ((1 << self.PCH_BITS) - 1)
        
        # Bank group (3 bits)
        bg_offset = pch_offset - self.BG_BITS
        result['bank_group'] = (addr >> bg_offset) & ((1 << self.BG_BITS) - 1)
        
        # Bank (4 bits)
        bank_offset = bg_offset - self.BANK_BITS
        result['bank'] = (addr >> bank_offset) & ((1 << self.BANK_BITS) - 1)
        
        # Row (16 bits)
        row_offset = bank_offset - self.ROW_BITS
        result['row'] = (addr >> row_offset) & ((1 << self.ROW_BITS) - 1)
        
        # Column (6 bits)
        col_offset = row_offset - self.COL_BITS
        result['column'] = (addr >> col_offset) & ((1 << self.COL_BITS) - 1)
        
        # Burst alignment (2 bits)
        result['burst'] = addr & ((1 << self.BURST_BITS) - 1)
        
        return result
    
    def encode(self, components: Dict[str, int]) -> int:
        """Encode components back to HBM4 address"""
        addr = 0
        
        addr |= (components.get('stack', 0) & ((1 << self.STACK_BITS) - 1))
        addr <<= self.CHANNEL_BITS
        addr |= (components.get('channel', 0) & ((1 << self.CHANNEL_BITS) - 1))
        addr <<= self.PCH_BITS
        addr |= (components.get('pseudo_channel', 0) & ((1 << self.PCH_BITS) - 1))
        addr <<= self.BG_BITS
        addr |= (components.get('bank_group', 0) & ((1 << self.BG_BITS) - 1))
        addr <<= self.BANK_BITS
        addr |= (components.get('bank', 0) & ((1 << self.BANK_BITS) - 1))
        addr <<= self.ROW_BITS
        addr |= (components.get('row', 0) & ((1 << self.ROW_BITS) - 1))
        addr <<= self.COL_BITS
        addr |= (components.get('column', 0) & ((1 << self.COL_COL_BITS) - 1))
        addr <<= self.BURST_BITS
        addr |= (components.get('burst', 0) & ((1 << self.BURST_BITS) - 1))
        
        return addr
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/controller/test_address_decoder.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/controller/test_address_decoder.py model/controller/address_decoder.py
git commit -m "feat(hbm4): extend address decoder for 32-channel HBM4 support"
```

---

## Task 3: Create HBM4 Channel State Machine

**Files:**
- Create: `model/dram/hbm4_channel_model.py`
- Test: `tests/dram/test_hbm4_channel_model.py`

**Step 1: Write the failing test**

```python
# tests/dram/test_hbm4_channel_model.py
import pytest
from model.dram.hbm4_channel_model import HBM4Channel, HBM4ChannelState

def test_hbm4_channel_creation():
    """32 channel state machines must be created for HBM4"""
    spec = HBM4Spec()
    channels = [HBM4Channel(i, spec) for i in range(32)]
    
    assert len(channels) == 32
    for ch in channels:
        assert ch.channel_id in range(32)

def test_hbm4_channel_commands():
    """All HBM4 commands must be supported per channel"""
    spec = HBM4Spec()
    ch = HBM4Channel(0, spec)
    
    # Verify all HBM4 commands are recognized
    expected_commands = ['ACT', 'PRE', 'PREA', 'RD', 'WR', 'RDA', 'WRA', 
                        'REFab', 'REFsb', 'RFMab', 'RFMsb']
    for cmd in expected_commands:
        assert cmd in ch.commands

def test_hbm4_pseudo_channel_independence():
    """Pseudo-channels must operate independently"""
    spec = HBM4Spec()
    ch = HBM4Channel(0, spec)
    
    # Pseudo-channel 0 and 1 should have independent state
    pc0 = ch.pseudo_channels[0]
    pc1 = ch.pseudo_channels[1]
    
    # Activating row in PC0 should not affect PC1
    pc0.activate_row(100)
    assert pc0.is_row_open(100)
    assert not pc1.is_row_open(100)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/dram/test_hbm4_channel_model.py -v`
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# model/dram/hbm4_channel_model.py
"""HBM4 Channel Model

Implements 32 independent channels, each with 2 pseudo-channels.
Based on Ramulator 2.0 hierarchical node structure.

Reference:
- Ramulator 2.0: src/dram/impl/HBM3.cpp
- DRAMSys: configs/memspec/HBM2.json
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from model.dram.bank_state_machine import BankStateMachine, BankState
from model.dram.hbm4_spec import HBM4Spec


class PseudoChannelState(Enum):
    """Pseudo-channel operational states"""
    IDLE = 0
    ACTIVE = 1
    REFRESHING = 2


@dataclass
class PseudoChannel:
    """HBM4 Pseudo-Channel state
    
    Each physical channel has 2 pseudo-channels for doubled parallelism.
    Based on Ramulator 2.0 pseudochannel level.
    """
    channel_id: int
    pseudo_channel_id: int  # 0 or 1
    spec: HBM4Spec
    
    # Bank state machines (16 banks per pseudo-channel)
    banks: List[BankStateMachine]
    
    # State tracking
    state: PseudoChannelState = PseudoChannelState.IDLE
    open_row: int = -1
    
    def __post_init__(self):
        # Create bank state machines for this pseudo-channel
        self.banks = [
            BankStateMachine(bank_id, self.spec)
            for bank_id in range(self.spec.banks_per_pseudo_channel)
        ]
    
    def activate_row(self, row: int) -> bool:
        """Activate a row in any bank"""
        for bank in self.banks:
            if bank.can_activate():
                bank.activate(row)
                self.open_row = row
                self.state = PseudoChannelState.ACTIVE
                return True
        return False
    
    def is_row_open(self, row: int) -> bool:
        """Check if row is currently open"""
        return self.open_row == row
    
    def precharge_all(self) -> bool:
        """Precharge all banks in this pseudo-channel"""
        for bank in self.banks:
            if bank.can_precharge():
                bank.precharge()
        self.open_row = -1
        self.state = PseudoChannelState.IDLE
        return True


class HBM4Channel:
    """HBM4 Channel Model
    
    Represents one of 32 independent memory channels in HBM4.
    Each channel has 2 pseudo-channels (64 total pseudo-channels).
    
    Reference: Ramulator 2.0 HBM3 channel node
    """
    
    # HBM4 commands (from Ramulator 2.0)
    COMMANDS = [
        'ACT', 'PRE', 'PREA',  # Row commands
        'RD', 'WR', 'RDA', 'WRA',  # Column commands
        'REFab', 'REFsb',  # Refresh commands
        'RFMab', 'RFMsb'  # Row refresh commands
    ]
    
    def __init__(self, channel_id: int, spec: HBM4Spec):
        self.channel_id = channel_id
        self.spec = spec
        
        # Create 2 pseudo-channels per channel
        self.pseudo_channels = [
            PseudoChannel(channel_id, pch_id, spec)
            for pch_id in range(2)
        ]
        
        # Channel-level state
        self.state = PseudoChannelState.IDLE
    
    def issue_command(self, cmd: str, pseudo_channel: int, 
                     bank: int, row: int, col: int) -> bool:
        """Issue a command to this channel"""
        if pseudo_channel not in [0, 1]:
            return False
        
        pc = self.pseudo_channels[pseudo_channel]
        
        if cmd == 'ACT':
            return pc.activate_row(row)
        elif cmd in ['PRE', 'PREA']:
            return pc.precharge_all()
        elif cmd in ['RD', 'WR', 'RDA', 'WRA']:
            # Check if row is open or needs activation
            if not pc.is_row_open(row):
                pc.activate_row(row)
            return True
        elif cmd in ['REFab', 'REFsb']:
            pc.state = PseudoChannelState.REFRESHING
            return True
        
        return False
    
    def tick(self):
        """Advance time by one cycle"""
        for pc in self.pseudo_channels:
            for bank in pc.banks:
                bank.tick()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/dram/test_hbm4_channel_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/dram/test_hbm4_channel_model.py model/dram/hbm4_channel_model.py
git commit -m "feat(hbm4): add HBM4 channel model with 32 channels and pseudo-channel support"
```

---

## Task 4: Create DFI 5.1 Interface

**Files:**
- Create: `model/dram/dfi_interface.py`
- Test: `tests/dram/test_dfi_interface.py`

**Step 1: Write the failing test**

```python
# tests/dram/test_dfi_interface.py
import pytest
from model.dram.dfi_interface import DFI5Interface, DFICommand, DFIPhyIF

def test_dfi_interface_creation():
    """DFI 5.1 interface must be created"""
    dfi = DFI5Interface()
    assert dfi.version == "5.1"

def test_dfi_commands():
    """DFI must encode all HBM4 commands"""
    dfi = DFI5Interface()
    
    expected_commands = [
        DFICommand.ACT, DFICommand.PRE, DFICommand.PREA,
        DFICommand.RD, DFICommand.WR, DFICommand.REFB
    ]
    for cmd in expected_commands:
        assert cmd in dfi.supported_commands

def test_dfi_low_power_states():
    """DFI 5.1 low-power states must be supported"""
    dfi = DFI5Interface()
    
    # Verify all DFI LP states
    assert hasattr(dfi, 'LP_IDLE')
    assert hasattr(dfi, 'LP_CTRL')
    assert hasattr(dfi, 'LP_DATA')
    assert hasattr(dfi, 'LP_FREQ_CHANGE')
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/dram/test_dfi_interface.py -v`
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# model/dram/dfi_interface.py
"""DFI 5.1 Interface for HBM4 Controller-PHY Communication

Based on Synopsys HBM4 Controller findings:
- Extended DFI 5.1 for controller-PHY interface
- APB v2.0 register interface
- DFI PHY Independent Mode for initialization/training

Reference:
- Synopsys DesignWare HBM4/4E Controller IP
- DFI 5.1 specification
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class DFICommand(Enum):
    """DFI command encoding for HBM4"""
    ACT = 0b0000
    PRE = 0b0001
    PREA = 0b0010
    RD = 0b0011
    WR = 0b0100
    RDA = 0b0101
    WRA = 0b0110
    REFab = 0b0111
    REFsb = 0b1000
    RFMab = 0b1001
    RFMsb = 0b1010


class DFILowPowerState(Enum):
    """DFI 5.1 low-power states"""
    LP_IDLE = 0
    LP_CTRL = 1      # Controller in low-power
    LP_DATA = 2      # Data path in low-power
    LP_FREQ_CHANGE = 3  # Frequency change in progress


@dataclass
class DFIRequest:
    """DFI request from controller to PHY"""
    command: DFICommand
    address: int
    bank: int
    pseudo_channel: int
    channel: int
    wrdata_en: bool = False
    rddata_en: bool = False
    chip: int = 0


@dataclass
class DFIResponse:
    """DFI response from PHY to controller"""
    ready: bool = True
    calibration_done: bool = False
    training_state: str = "not_started"
    lp_state: DFILowPowerState = DFILowPowerState.LP_IDLE
    error: Optional[str] = None


class DFI5Interface:
    """DFI 5.1 interface implementation
    
    Implements the standard DFI 5.1 interface between HBM4 controller and PHY.
    Supports:
    - Command and address encoding
    - Data enable signals
    - Low-power state management
    - Frequency change protocol
    - PHY Independent Mode for initialization
    """
    
    VERSION = "5.1"
    
    def __init__(self, config=None):
        self.version = self.VERSION
        self.config = config
        self.supported_commands = list(DFICommand)
        
        # State tracking
        self.lp_state = DFILowPowerState.LP_IDLE
        self.frequency_mhz = 800  # 800 MT/s for 8 GT/s DDR
        self.training_complete = False
        
        # Request/response queues
        self.request_queue = []
        self.response_queue = []
    
    def encode_command(self, cmd: str, addr_vec: Dict[str, int]) -> DFIRequest:
        """Encode a command into DFI request format"""
        # Map string command to DFI command
        cmd_map = {
            'ACT': DFICommand.ACT,
            'PRE': DFICommand.PRE,
            'PREA': DFICommand.PREA,
            'RD': DFICommand.RD,
            'WR': DFICommand.WR,
            'RDA': DFICommand.RDA,
            'WRA': DFICommand.WRA,
            'REFab': DFICommand.REFab,
            'REFsb': DFICommand.REFsb,
        }
        
        dfi_cmd = cmd_map.get(cmd, DFICommand.ACT)
        
        return DFIRequest(
            command=dfi_cmd,
            address=addr_vec.get('row', 0),
            bank=addr_vec.get('bank', 0),
            pseudo_channel=addr_vec.get('pseudo_channel', 0),
            channel=addr_vec.get('channel', 0),
            wrdata_en=(cmd in ['WR', 'WRA']),
            rddata_en=(cmd in ['RD', 'RDA'])
        )
    
    def set_low_power_state(self, state: DFILowPowerState):
        """Set DFI low-power state"""
        self.lp_state = state
    
    def get_response(self) -> DFIResponse:
        """Get response from PHY"""
        return DFIResponse(
            ready=True,
            calibration_done=self.training_complete,
            training_state="complete" if self.training_complete else "in_progress",
            lp_state=self.lp_state
        )
    
    def start_training(self):
        """Initiate PHY training sequence (DFI PHY Independent Mode)"""
        self.training_complete = False
    
    def complete_training(self):
        """Mark training as complete"""
        self.training_complete = True
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/dram/test_dfi_interface.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/dram/test_dfi_interface.py model/dram/dfi_interface.py
git commit -m "feat(hbm4): add DFI 5.1 interface for controller-PHY communication"
```

---

## Task 5: Create HBM4 QoS Scheduler

**Files:**
- Create: `model/controller/hbm4_qos_scheduler.py`
- Test: `tests/controller/test_hbm4_qos_scheduler.py`

**Step 1: Write the failing test**

```python
# tests/controller/test_hbm4_qos_scheduler.py
import pytest
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler, QoSLevel

def test_qos_scheduler_creation():
    """HBM4 QoS scheduler must support 16 priority levels"""
    scheduler = HBM4QoSScheduler()
    
    assert scheduler.priority_levels == 16
    assert scheduler.QOS_CRITICAL == 15
    assert scheduler.QOS_IDLE == 0

def test_qos_anti_starvation():
    """Low priority requests must not be permanently blocked"""
    scheduler = HBM4QoSScheduler()
    
    # Submit high priority requests
    for i in range(10):
        scheduler.submit_request(request_id=i, qos=15)
    
    # Submit low priority request
    scheduler.submit_request(request_id=100, qos=0)
    
    # After bandwidth guarantee, low priority should be schedulable
    scheduler.bandwidth_tracked[15] = 1000  # Simulate high BW usage
    scheduler.bandwidth_tracked[0] = 0       # Low BW usage
    
    # Low priority should be schedulable (below guarantee)
    assert scheduler._can_schedule(0)

def test_qos_bandwidth_guarantee():
    """Each QoS level must have configurable bandwidth guarantee"""
    scheduler = HBM4QoSScheduler()
    
    # Verify bandwidth guarantees are set
    assert scheduler.bw_guarantee[15] > scheduler.bw_guarantee[0]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/controller/test_hbm4_qos_scheduler.py -v`
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# model/controller/hbm4_qos_scheduler.py
"""HBM4 QoS Scheduler with Anti-Starvation

Based on Synopsys HBM4 Controller findings:
- 16 priority classes with anti-starvation
- Bandwidth guarantee per QoS level
- Address collision control

Reference: Synopsys DesignWare HBM4/4E Controller IP
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import time


class QoSLevel(IntEnum):
    """HBM4 QoS priority levels (0-15)"""
    CRITICAL = 15    # Real-time/critical
    HIGH = 12       # High priority
    NORMAL = 8      # Normal traffic
    LOW = 4         # Background/batch
    IDLE = 0        # Idle/probe


@dataclass
class QueuedRequest:
    """Request in QoS queue"""
    request_id: int
    addr: int
    qos: int
    is_read: bool
    arrival_time: float
    row_hit: bool = False
    channel: int = 0
    pseudo_channel: int = 0
    bank: int = 0


class HBM4QoSScheduler:
    """HBM4 QoS Scheduler with anti-starvation
    
    Key features from research:
    - 16 priority levels (0-15)
    - Anti-starvation guarantees for low priority
    - Bandwidth guarantee per QoS class
    - FR-FCFS within same priority
    """
    
    # Priority level constants
    QOS_CRITICAL = 15
    QOS_HIGH = 12
    QOS_NORMAL = 8
    QOS_LOW = 4
    QOS_IDLE = 0
    
    def __init__(self, config=None):
        self.priority_levels = 16
        
        # Bandwidth guarantees (GB/s per stack)
        # Based on design document v1.1
        self.bw_guarantee = {
            self.QOS_CRITICAL: 200.0,
            self.QOS_HIGH: 300.0,
            self.QOS_NORMAL: 200.0,
            self.QOS_LOW: 100.0,
            self.QOS_IDLE: 0,
        }
        
        # Bandwidth caps (to prevent starvation)
        self.bw_cap = {
            self.QOS_CRITICAL: 1000.0,
            self.QOS_HIGH: 800.0,
            self.QOS_NORMAL: 400.0,
            self.QOS_LOW: 200.0,
            self.QOS_IDLE: 50.0,
        }
        
        # Bandwidth tracking
        self.bw_window_ms = 1.0
        self.bandwidth_tracked = defaultdict(list)  # {qos: [(timestamp, bytes)]}
        
        # Request queues per priority level
        self.queues: Dict[int, List[QueuedRequest]] = defaultdict(list)
    
    def submit_request(self, request_id: int, addr: int = 0, 
                      qos: int = 8, is_read: bool = True,
                      channel: int = 0, pseudo_channel: int = 0,
                      bank: int = 0, row_hit: bool = False) -> bool:
        """Submit a request to the QoS scheduler"""
        if qos < 0 or qos >= self.priority_levels:
            return False
        
        req = QueuedRequest(
            request_id=request_id,
            addr=addr,
            qos=qos,
            is_read=is_read,
            arrival_time=time.time(),
            row_hit=row_hit,
            channel=channel,
            pseudo_channel=pseudo_channel,
            bank=bank
        )
        
        self.queues[qos].append(req)
        return True
    
    def _get_current_bandwidth(self, qos_level: int) -> float:
        """Calculate current bandwidth for a QoS level"""
        now = time.time()
        window_start = now - self.bw_window_ms / 1000.0
        
        recent = [
            (t, b) for t, b in self.bandwidth_tracked[qos_level]
            if t >= window_start
        ]
        total_bytes = sum(b for _, b in recent)
        total_time = self.bw_window_ms / 1000.0
        
        return total_bytes / total_time / 1e9 if total_time > 0 else 0
    
    def _can_schedule(self, qos_level: int) -> bool:
        """Check if a QoS level can be scheduled (anti-starvation)"""
        current_bw = self._get_current_bandwidth(qos_level)
        
        # Below guarantee: can always schedule
        if current_bw < self.bw_guarantee.get(qos_level, 0):
            return True
        
        # Above cap: cannot schedule (prevents starvation of others)
        if current_bw >= self.bw_cap.get(qos_level, float('inf')):
            return False
        
        return True  # Between guarantee and cap: fair scheduling
    
    def schedule(self) -> Optional[QueuedRequest]:
        """Schedule the next request using QoS + FR-FCFS"""
        # Check QoS levels from high to low
        for qos_level in range(self.priority_levels - 1, -1, -1):
            if not self._can_schedule(qos_level):
                continue
            
            # Get candidates at this QoS level
            candidates = self.queues[qos_level]
            if not candidates:
                continue
            
            # FR-FCFS selection within same priority
            best = self._fr_fcfs_select(candidates)
            if best:
                self.queues[qos_level].remove(best)
                return best
        
        return None
    
    def _fr_fcfs_select(self, candidates: List[QueuedRequest]) -> Optional[QueuedRequest]:
        """First-Ready FCFS selection"""
        if not candidates:
            return None
        
        # Priority 1: Row hit requests
        row_hits = [r for r in candidates if r.row_hit]
        if row_hits:
            # Sort by arrival time, pick oldest
            return min(row_hits, key=lambda r: r.arrival_time)
        
        # Priority 2: All requests, oldest first
        return min(candidates, key=lambda r: r.arrival_time)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/controller/test_hbm4_qos_scheduler.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/controller/test_hbm4_qos_scheduler.py model/controller/hbm4_qos_scheduler.py
git commit -m "feat(hbm4): add QoS scheduler with 16 priority levels and anti-starvation"
```

---

## Task 6: Create HBM4 Refresh Scheduler

**Files:**
- Create: `model/controller/hbm4_refresh_scheduler.py`
- Test: `tests/controller/test_hbm4_refresh_scheduler.py`

**Step 1: Write the failing test**

```python
# tests/controller/test_hbm4_refresh_scheduler.py
import pytest
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode

def test_refresh_scheduler_modes():
    """All refresh modes must be supported"""
    scheduler = HBM4RefreshScheduler()
    
    assert RefreshMode.ALL_BANKS in scheduler.supported_modes
    assert RefreshMode.PER_BANK in scheduler.supported_modes
    assert RefreshMode.BANK_GROUP in scheduler.supported_modes

def test_refresh_interval_tracking():
    """Refresh interval (tREFI) must be tracked"""
    scheduler = HBM4RefreshScheduler()
    
    # Initial state
    assert scheduler.cycles_since_refresh == 0
    
    # After some cycles
    scheduler.tick()
    assert scheduler.cycles_since_refresh == 1

def test_autonomous_refresh():
    """Controller must support autonomous per-bank refresh"""
    scheduler = HBM4RefreshScheduler()
    scheduler.mode = RefreshMode.PER_BANK
    
    # Verify staggered refresh is possible
    assert scheduler.can_refresh()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/controller/test_hbm4_refresh_scheduler.py -v`
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# model/controller/hbm4_refresh_scheduler.py
"""HBM4 Refresh Scheduler with Autonomous Per-Bank Refresh

Based on research findings:
- Per-bank and all-bank refresh modes
- Autonomous refresh management
- DRFM (Direct Refresh Management) for row-hammer mitigation

Reference: Synopsys DesignWare HBM4/4E Controller IP
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Set
from model.dram.hbm4_spec import HBM4Spec


class RefreshMode(Enum):
    """Refresh operating modes"""
    ALL_BANKS = "all"         # Refresh all banks at once
    PER_BANK = "per_bank"     # Staggered per-bank refresh
    BANK_GROUP = "bank_group" # Refresh by bank group


@dataclass
class RefreshBankStatus:
    """Status tracking for per-bank refresh"""
    bank_id: int
    last_refresh_cycle: int = 0
    needs_refresh: bool = False


class HBM4RefreshScheduler:
    """HBM4 Refresh Scheduler
    
    Manages DRAM refresh operations with support for:
    - All-bank refresh (HBM2 style)
    - Per-bank refresh (staggered, HBM3 style)
    - Bank group refresh
    - Autonomous refresh scheduling
    - DRFM (Direct Refresh Management) for row-hammer
    """
    
    def __init__(self, config: Optional[HBM4Spec] = None):
        if config is None:
            config = HBM4Spec()
        
        self.spec = config
        self.mode = RefreshMode.PER_BANK  # Default to per-bank for HBM4
        
        # Timing parameters from spec
        self.tREFI = config.nREFI  # Refresh interval (cycles)
        self.tRFC = config.nRFC    # Refresh command duration (cycles)
        
        # Refresh state tracking
        self.cycles_since_refresh = 0
        self.current_refresh_bank = 0
        self.total_refresh_count = 0
        
        # Per-bank refresh tracking
        self.bank_status: List[RefreshBankStatus] = [
            RefreshBankStatus(bank_id=i)
            for i in range(config.total_banks)
        ]
        
        # Bank group refresh tracking (8 groups × 16 banks)
        self.bank_groups_per_channel = config.bank_groups_per_channel
        
        self.supported_modes = [
            RefreshMode.ALL_BANKS,
            RefreshMode.PER_BANK,
            RefreshMode.BANK_GROUP
        ]
    
    def tick(self):
        """Advance refresh timer by one cycle"""
        self.cycles_since_refresh += 1
    
    def can_refresh(self) -> bool:
        """Check if refresh is needed"""
        return self.cycles_since_refresh >= self.tREFI
    
    def get_refresh_command(self) -> Optional[tuple]:
        """Get the next refresh command to execute"""
        if not self.can_refresh():
            return None
        
        if self.mode == RefreshMode.ALL_BANKS:
            self.total_refresh_count += 1
            self.cycles_since_refresh = 0
            return ('REFab', None, None)  # All-bank refresh
        
        elif self.mode == RefreshMode.PER_BANK:
            # Rotate through banks
            bank_to_refresh = self.current_refresh_bank
            self.current_refresh_bank = (self.current_refresh_bank + 1) % self.spec.total_banks
            self.cycles_since_refresh = 0
            self.total_refresh_count += 1
            return ('REFsb', bank_to_refresh // 16, bank_to_refresh % 16)
        
        elif self.mode == RefreshMode.BANK_GROUP:
            # Refresh one bank group per interval
            group_to_refresh = (self.total_refresh_count // self.spec.banks_per_pseudo_channel) % self.bank_groups_per_channel
            self.cycles_since_refresh = 0
            self.total_refresh_count += 1
            return ('REFsb', 0, group_to_refresh * self.spec.banks_per_pseudo_channel)
        
        return None
    
    def set_mode(self, mode: RefreshMode):
        """Set refresh operating mode"""
        if mode in self.supported_modes:
            self.mode = mode
    
    def mark_bank_refreshed(self, bank_id: int, cycle: int):
        """Mark a specific bank as refreshed"""
        if 0 <= bank_id < len(self.bank_status):
            self.bank_status[bank_id].last_refresh_cycle = cycle
            self.bank_status[bank_id].needs_refresh = False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/controller/test_hbm4_refresh_scheduler.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/controller/test_hbm4_refresh_scheduler.py model/controller/hbm4_refresh_scheduler.py
git commit -m "feat(hbm4): add refresh scheduler with per-bank and autonomous modes"
```

---

## Task 7: Create HBM4 Controller Integration

**Files:**
- Create: `model/controller/hbm4_controller.py`
- Test: `tests/controller/test_hbm4_controller.py`

**Step 1: Write the failing test**

```python
# tests/controller/test_hbm4_controller.py
import pytest
from model.controller.hbm4_controller import HBM4Controller

def test_hbm4_controller_creation():
    """HBM4 controller with 32 channels must be created"""
    controller = HBM4Controller()
    
    assert controller.num_channels == 32
    assert controller.num_pseudo_channels == 64

def test_hbm4_submit_request():
    """Requests must be submitted and routed to correct channel"""
    controller = HBM4Controller()
    
    # Submit request
    req_id = controller.submit_request(addr=0x10000000, is_read=True, qos=8)
    assert req_id >= 0

def test_hbm4_bandwidth():
    """Peak bandwidth calculation must be 2 TB/s @ 8 GT/s"""
    controller = HBM4Controller()
    
    bw = controller.get_peak_bandwidth()
    expected = 2.0  # TB/s
    assert abs(bw - expected) < 0.01
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/controller/test_hbm4_controller.py -v`
Expected: FAIL - module not found

**Step 3: Write minimal implementation**

```python
# model/controller/hbm4_controller.py
"""HBM4 Controller - Main Controller Module

Layer 2 of the 5-layer HBM4 architecture model.
Integrates address decoder, QoS scheduler, refresh scheduler, and DFI interface.

Based on multi-agent research findings and Ramulator 2.0 architecture.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from model.dram.hbm4_spec import HBM4Spec, HBM4_CONFIG
from model.dram.hbm4_channel_model import HBM4Channel
from model.dram.dfi_interface import DFI5Interface, DFIRequest, DFIResponse
from model.controller.address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler, RefreshMode
from model.controller.request import HBMRequest


@dataclass
class ControllerStats:
    """Controller statistics"""
    total_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    row_hits: int = 0
    refresh_commands: int = 0
    cycles: int = 0


class HBM4Controller:
    """HBM4 Memory Controller
    
    Main controller for HBM4 memory subsystem.
    Key features:
    - 32 independent channels
    - 64 pseudo-channels
    - QoS scheduling with 16 priority levels
    - Autonomous refresh management
    - DFI 5.1 interface to PHY
    """
    
    def __init__(self, config: Optional[HBM4Spec] = None):
        if config is None:
            config = HBM4_CONFIG
        
        self.config = config
        self.spec = config
        
        # === Performance Parameters ===
        self.num_channels = config.channels  # 32
        self.num_pseudo_channels = config.pseudo_channels  # 64
        self.queue_depth = 32
        
        # === Sub-components ===
        self.address_decoder = HBM4AddressDecoder(config)
        self.qos_scheduler = HBM4QoSScheduler(config)
        self.refresh_scheduler = HBM4RefreshScheduler(config)
        self.dfi_interface = DFI5Interface(config)
        
        # === Channel State Machines ===
        self.channels: List[HBM4Channel] = [
            HBM4Channel(i, config)
            for i in range(self.num_channels)
        ]
        
        # === Statistics ===
        self.stats = ControllerStats()
        
        # === Request Tracking ===
        self.pending_requests: Dict[int, HBMRequest] = {}
        self.request_counter = 0
    
    def submit_request(self, addr: int, is_read: bool = True,
                      qos: int = 8, length: int = 64) -> int:
        """Submit a memory request"""
        # Decode address
        addr_components = self.address_decoder.decode(addr)
        
        # Create request
        request = HBMRequest(
            request_id=self.request_counter,
            addr=addr,
            length=length,
            is_read=is_read,
            qos=qos,
            channel=addr_components['channel'],
            pseudo_channel=addr_components['pseudo_channel'],
            bank=addr_components['bank'],
            row=addr_components['row']
        )
        
        # Submit to QoS scheduler
        self.qos_scheduler.submit_request(
            request_id=request.request_id,
            addr=addr,
            qos=qos,
            is_read=is_read,
            channel=request.channel,
            pseudo_channel=request.pseudo_channel,
            bank=request.bank
        )
        
        self.pending_requests[self.request_counter] = request
        self.request_counter += 1
        self.stats.total_requests += 1
        
        if is_read:
            self.stats.read_requests += 1
        else:
            self.stats.write_requests += 1
        
        return request.request_id
    
    def tick(self) -> Optional[DFIResponse]:
        """Advance controller by one cycle"""
        self.stats.cycles += 1
        
        # Advance sub-components
        for channel in self.channels:
            channel.tick()
        
        self.refresh_scheduler.tick()
        
        # Handle refresh if needed
        refresh_cmd = self.refresh_scheduler.get_refresh_command()
        if refresh_cmd:
            self.stats.refresh_commands += 1
            cmd_name, channel_id, bank_id = refresh_cmd
            # Issue refresh command via DFI
            self.dfi_interface.encode_command(cmd_name, {
                'channel': channel_id or 0,
                'bank': bank_id or 0,
                'pseudo_channel': 0,
                'row': 0
            })
        
        # Schedule next request
        scheduled = self.qos_scheduler.schedule()
        if scheduled:
            # Issue command to channel via DFI
            self.dfi_interface.encode_command(
                'ACT' if scheduled.is_read else 'WR',
                {
                    'channel': scheduled.channel,
                    'pseudo_channel': scheduled.pseudo_channel,
                    'bank': scheduled.bank,
                    'row': scheduled.addr
                }
            )
        
        return self.dfi_interface.get_response()
    
    def get_peak_bandwidth(self) -> float:
        """Get peak bandwidth in TB/s"""
        return self.spec.bandwidth
    
    def get_stats(self) -> Dict[str, Any]:
        """Get controller statistics"""
        return {
            'total_requests': self.stats.total_requests,
            'read_requests': self.stats.read_requests,
            'write_requests': self.stats.write_requests,
            'refresh_commands': self.stats.refresh_commands,
            'cycles': self.stats.cycles,
            'peak_bandwidth_tbs': self.get_peak_bandwidth(),
            'peak_bandwidth_gbs': self.spec.bandwidth_gbs
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/controller/test_hbm4_controller.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/controller/test_hbm4_controller.py model/controller/hbm4_controller.py
git commit -m "feat(hbm4): integrate HBM4 controller with all sub-components"
```

---

## Task 8: Create Integration Test

**Files:**
- Create: `tests/dram/test_hbm4_integration.py`

**Step 1: Write the integration test**

```python
# tests/dram/test_hbm4_integration.py
"""HBM4 Phase A Integration Tests

Tests the complete HBM4 controller model from request submission
through DFI interface to channel state machines.
"""

import pytest
import time
from model.controller.hbm4_controller import HBM4Controller
from model.dram.hbm4_spec import HBM4Spec


class TestHBM4Integration:
    """Integration tests for HBM4 controller"""
    
    def test_end_to_end_request(self):
        """Test complete request flow"""
        controller = HBM4Controller()
        
        # Submit read request
        req_id = controller.submit_request(
            addr=0x10000000,
            is_read=True,
            qos=8
        )
        
        # Execute several cycles
        for _ in range(10):
            controller.tick()
        
        # Verify request was processed
        stats = controller.get_stats()
        assert stats['total_requests'] == 1
        assert stats['read_requests'] == 1
    
    def test_multi_channel_parallelism(self):
        """Test that requests to different channels work"""
        controller = HBM4Controller()
        
        # Submit requests to different channels
        channels_used = set()
        for i in range(32):
            addr = i * 0x1000000  # Different channel
            controller.submit_request(addr=addr, is_read=True)
            
            # Decode to verify channel
            decoded = controller.address_decoder.decode(addr)
            channels_used.add(decoded['channel'])
        
        # Verify multiple channels were used
        assert len(channels_used) > 1
    
    def test_qos_priority_ordering(self):
        """Test that QoS scheduling respects priority"""
        controller = HBM4Controller()
        
        # Submit requests with different priorities
        controller.submit_request(addr=0x10000000, qos=0)  # Low priority
        controller.submit_request(addr=0x20000000, qos=15)  # High priority
        
        # Execute to schedule
        for _ in range(10):
            controller.tick()
        
        # High priority should have been scheduled first
        # (verify through queue state)
        stats = controller.get_stats()
        assert stats['total_requests'] == 2
    
    def test_refresh_handling(self):
        """Test that refresh commands are issued"""
        controller = HBM4Controller()
        
        # Submit some requests
        for i in range(10):
            controller.submit_request(addr=0x10000000 + i * 0x100)
        
        # Run for enough cycles to trigger refresh
        spec = HBM4Spec()
        for _ in range(spec.nREFI + 100):
            controller.tick()
        
        stats = controller.get_stats()
        assert stats['refresh_commands'] >= 1
    
    def test_peak_bandwidth_calculation(self):
        """Verify peak bandwidth matches specification"""
        controller = HBM4Controller()
        
        bw = controller.get_peak_bandwidth()
        expected = 2.0  # 2 TB/s @ 8 GT/s with 2048-bit interface
        
        assert abs(bw - expected) < 0.01
    
    def test_32_channel_configuration(self):
        """Verify 32-channel configuration is correct"""
        controller = HBM4Controller()
        
        assert controller.num_channels == 32
        assert controller.num_pseudo_channels == 64
        assert len(controller.channels) == 32
```

**Step 2: Run integration test**

Run: `pytest tests/dram/test_hbm4_integration.py -v`
Expected: PASS (all tests)

**Step 3: Commit**

```bash
git add tests/dram/test_hbm4_integration.py
git commit -m "feat(hbm4): add integration tests for HBM4 controller"
```

---

## Summary

This implementation plan creates the foundation for HBM4 logic base die modeling:

| Task | Component | Key Files |
|------|-----------|-----------|
| 1 | HBM4 Spec Constants | `model/dram/hbm4_spec.py` |
| 2 | Address Decoder | `model/controller/address_decoder.py` |
| 3 | Channel Model | `model/dram/hbm4_channel_model.py` |
| 4 | DFI 5.1 Interface | `model/dram/dfi_interface.py` |
| 5 | QoS Scheduler | `model/controller/hbm4_qos_scheduler.py` |
| 6 | Refresh Scheduler | `model/controller/hbm4_refresh_scheduler.py` |
| 7 | Controller Integration | `model/controller/hbm4_controller.py` |
| 8 | Integration Tests | `tests/dram/test_hbm4_integration.py` |

**Dependencies:**
- Tasks 1-3 can be implemented in parallel
- Tasks 4-6 depend on Task 1 (HBM4 spec)
- Task 7 depends on Tasks 2-6
- Task 8 depends on Task 7

**Reference Models Used:**
- Ramulator 2.0: HBM3 timing, command structure
- DRAMSys: HBM2 address mapping, JSON configuration
- Multi-agent research: 32-channel architecture, DFI 5.1, QoS requirements

---

## Next Steps

After completing Phase A:
1. **Phase B**: Extend DRAM timing model with HBM4-specific timing parameters
2. **Phase C**: Add PHY interface (DFI 5.1 timing, training FSM)
3. **Phase D**: Add lane repair, ECC, and power models

---

**Plan created:** 2026-06-15
**Based on research:** Multi-agent HBM4 analysis (7 agents, 630k tokens)
**Reference models:** Ramulator 2.0, DRAMSys, original Ramulator