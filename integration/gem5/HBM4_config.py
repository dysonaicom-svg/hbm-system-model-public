"""
gem5 HBM4 Memory System Configuration
Provides HBM4 memory system integration for gem5 simulations

Features:
- HBM4 32-channel support
- Configurable timing parameters
- Python bridge for external HBM model integration

Usage (without gem5):
    from hbm4_config import HBM4Presets, HBM4AddrMap, get_config_by_name

Usage (with gem5):
    from m5.objects import *
    from hbm4_config import create_hbm4_mem_system
"""

# Optional gem5 imports - only needed when running in gem5 environment
try:
    from m5.objects import *
    from m5.util import addToPath
    import m5
    GEM5_AVAILABLE = True
except ImportError:
    GEM5_AVAILABLE = False

# HBM4 Timing Parameters (based on JEDEC HBM4 draft)
class HBM4Timing:
    """HBM4 timing parameters"""
    # Clock: 8.0 GHz (125 ps period)
    tCK = 125  # ps

    # Command timing (cycles)
    tRCD = 16
    tRP = 16
    tRAS = 40
    tRC = 56
    tCCD = 4
    tRRD = 4
    tFAW = 20

    # Refresh timing
    tRFC = 280  # 16Gb HBM4
    tREFI = 3900  # Normal refresh interval

    # Read/Write timing
    tRTP = 6  # Read to precharge
    tWTP = 8  # Write to precharge
    tWR = 18  # Write recovery
    tRTRS = 2  # RTT park cycle

    # Data timing
    tDQSCK = 3  # DQS capture skew
    tQH = 0.4   # Data valid window quarter

    # Burst length (HBM uses 2-blocks per burst = 32 bytes)
    nBL = 2


class HBM4Config:
    """HBM4 configuration for gem5"""

    # HBM4 Stack Configuration
    STACK_COUNT = 1
    CHANNELS_PER_STACK = 32  # HBM4 supports up to 32 channels
    PSEUDO_CHANNELS_PER_CHANNEL = 2
    BANKS_PER_PSEUDO_CHANNEL = 16
    BANK_GROUPS_PER_CHANNEL = 8
    ROWS_PER_BANK = 262144  # 256K rows
    COLS_PER_ROW = 256      # 32-bit * 256 cols = 1KB row
    DEVICE_WIDTH = 64       # x64 DRAM

    # HBM4 Geometry
    BANK_GROUP_SIZE = ROWS_PER_BANK // BANK_GROUPS_PER_CHANNEL

    # Capacity calculation
    @staticmethod
    def calc_capacity():
        """Calculate total capacity in bytes"""
        channels = HBM4Config.STACK_COUNT * HBM4Config.CHANNELS_PER_STACK
        pseudo_channels = HBM4Config.PSEUDO_CHANNELS_PER_CHANNEL
        banks = HBM4Config.BANKS_PER_PSEUDO_CHANNEL
        rows = HBM4Config.ROWS_PER_BANK
        cols = HBM4Config.COLS_PER_ROW
        width = HBM4Config.DEVICE_WIDTH // 8  # bytes

        capacity = channels * pseudo_channels * banks * rows * cols * width
        return capacity

    # Bandwidth calculation
    @staticmethod
    def calc_bandwidth():
        """Calculate peak bandwidth in GB/s"""
        # HBM4: 8.0 Gb/s/pin, 2048-bit interface (512 DQ pins per channel)
        data_rate = 8.0e9  # 8.0 Gb/s/pin
        io_width = 2048    # 2048-bit interface
        channels = HBM4Config.CHANNELS_PER_STACK

        # Single channel bandwidth
        bw_per_channel = data_rate * io_width / 8 / 1e9  # GB/s
        return bw_per_channel * channels


def create_hbm4_mem_system(system, mem_range, options):
    """
    Create HBM4 memory system for gem5 simulation

    Args:
        system: gem5 system object
        mem_range: memory address range
        options: simulation options

    Returns:
        Memory controller and memories
    """
    # Create HBM4 memory controller
    ctrl = HBM4MemoryController()

    # Configure timing
    timing = ctrl.timing
    timing.tCK = HBM4Timing.tCK
    timing.tRCD = HBM4Timing.tRCD
    timing.tRP = HBM4Timing.tRP
    timing.tRAS = HBM4Timing.tRAS
    timing.tRC = HBM4Timing.tRC
    timing.tCCD = HBM4Timing.tCCD
    timing.tRRD = HBM4Timing.tRRD
    timing.tFAW = HBM4Timing.tFAW
    timing.tRFC = HBM4Timing.tRFC
    timing.tREFI = HBM4Timing.tREFI
    timing.tRTP = HBM4Timing.tRTP
    timing.tWTP = HBM4Timing.tWTP
    timing.tWR = HBM4Timing.tWR

    # Configure memory
    ctrl.version = HBM4Config.STACK_COUNT
    ctrl.channels = HBM4Config.CHANNELS_PER_STACK
    ctrl.pseudo_channels = HBM4Config.PSEUDO_CHANNELS_PER_CHANNEL
    ctrl.banks = HBM4Config.BANKS_PER_PSEUDO_CHANNEL
    ctrl.rows = HBM4Config.ROWS_PER_BANK
    ctrl.columns = HBM4Config.COLS_PER_ROW

    # Connect to system
    ctrl.port = system.mem_ctrls.port

    # Create memory
    memory = HBM4()
    memory.range = mem_range

    # Configure memory bandwidth
    memory.data_rate = 8.0  # 8.0 GT/s
    memory.width = HBM4Config.DEVICE_WIDTH

    return ctrl, memory


# Configuration presets
class HBM4Presets:
    """HBM4 configuration presets"""

    @staticmethod
    def hbm4_32ch():
        """HBM4 32-channel configuration (JEDEC standard)"""
        return {
            'stack_count': 1,
            'channels_per_stack': 32,
            'pseudo_channels': 2,
            'banks_per_pseudo_channel': 16,
            'rows_per_bank': 262144,
            'cols_per_row': 256,
            'data_rate': 8.0e9,  # 8.0 Gb/s/pin
            'io_width': 2048,     # 2048-bit
            'peak_bandwidth_gbps': 819.2 * 32 / 8,  # ~3.2 TB/s
        }

    @staticmethod
    def hbm4_16ch():
        """HBM4 16-channel configuration"""
        return {
            'stack_count': 1,
            'channels_per_stack': 16,
            'pseudo_channels': 2,
            'banks_per_pseudo_channel': 16,
            'rows_per_bank': 262144,
            'cols_per_row': 256,
            'data_rate': 8.0e9,
            'io_width': 2048,
            'peak_bandwidth_gbps': 819.2 * 16 / 8,  # ~1.6 TB/s
        }

    @staticmethod
    def hbm4_8ch():
        """HBM4 8-channel configuration (compatible with HBM3)"""
        return {
            'stack_count': 1,
            'channels_per_stack': 8,
            'pseudo_channels': 2,
            'banks_per_pseudo_channel': 16,
            'rows_per_bank': 262144,
            'cols_per_row': 256,
            'data_rate': 6.4e9,  # HBM3 data rate
            'io_width': 1024,
            'peak_bandwidth_gbps': 819.2,  # ~819 GB/s
        }

    @staticmethod
    def hbm3_8ch():
        """HBM3 8-channel configuration (legacy)"""
        return {
            'stack_count': 1,
            'channels_per_stack': 8,
            'pseudo_channels': 2,
            'banks_per_pseudo_channel': 16,
            'rows_per_bank': 131072,
            'cols_per_row': 256,
            'data_rate': 6.4e9,
            'io_width': 1024,
            'peak_bandwidth_gbps': 819.2,
        }


def get_config_by_name(name):
    """Get configuration by preset name"""
    presets = {
        'hbm4_32ch': HBM4Presets.hbm4_32ch,
        'hbm4_16ch': HBM4Presets.hbm4_16ch,
        'hbm4_8ch': HBM4Presets.hbm4_8ch,
        'hbm3_8ch': HBM4Presets.hbm3_8ch,
    }

    if name in presets:
        return presets[name]()
    else:
        raise ValueError(f"Unknown preset: {name}")


# Address mapping for gem5
class HBM4AddrMap:
    """HBM4 address mapping for gem5"""

    # Address bit fields (64-bit address)
    # Stack[1:0] | Channel[4:0] | PseudoCh[5] | BankGroup[8:6] | Bank[11:7] | Row[27:12] | Col[15:3] | Byte[2:0]

    STACK_BITS = 2
    CHANNEL_BITS = 5
    PSEUDO_CHANNEL_BITS = 1
    BANK_GROUP_BITS = 3
    BANK_BITS = 5
    ROW_BITS = 16
    COL_BITS = 13
    BYTE_BITS = 3

    @staticmethod
    def decode(addr, config=None):
        """Decode HBM4 address into components

        Returns:
            dict with stack_id, channel_id, pseudo_channel_id, bank_group_id, bank_id, row_id, col_id
        """
        if config is None:
            config = HBM4Presets.hbm4_32ch()

        stack_id = (addr >> (HBM4AddrMap.CHANNEL_BITS +
                            HBM4AddrMap.PSEUDO_CHANNEL_BITS +
                            HBM4AddrMap.BANK_GROUP_BITS +
                            HBM4AddrMap.BANK_BITS +
                            HBM4AddrMap.ROW_BITS +
                            HBM4AddrMap.COL_BITS)) & ((1 << HBM4AddrMap.STACK_BITS) - 1)

        channel_id = (addr >> (HBM4AddrMap.PSEUDO_CHANNEL_BITS +
                              HBM4AddrMap.BANK_GROUP_BITS +
                              HBM4AddrMap.BANK_BITS +
                              HBM4AddrMap.ROW_BITS +
                              HBM4AddrMap.COL_BITS)) & ((1 << HBM4AddrMap.CHANNEL_BITS) - 1)

        pseudo_channel_id = (addr >> (HBM4AddrMap.BANK_GROUP_BITS +
                                      HBM4AddrMap.BANK_BITS +
                                      HBM4AddrMap.ROW_BITS +
                                      HBM4AddrMap.COL_BITS)) & 1

        bank_group_id = (addr >> (HBM4AddrMap.BANK_BITS +
                                  HBM4AddrMap.ROW_BITS +
                                  HBM4AddrMap.COL_BITS)) & ((1 << HBM4AddrMap.BANK_GROUP_BITS) - 1)

        bank_id = (addr >> (HBM4AddrMap.ROW_BITS +
                           HBM4AddrMap.COL_BITS)) & ((1 << HBM4AddrMap.BANK_BITS) - 1)

        row_id = (addr >> HBM4AddrMap.COL_BITS) & ((1 << HBM4AddrMap.ROW_BITS) - 1)
        col_id = addr & ((1 << HBM4AddrMap.COL_BITS) - 1)

        return {
            'stack_id': stack_id,
            'channel_id': channel_id,
            'pseudo_channel_id': pseudo_channel_id,
            'bank_group_id': bank_group_id,
            'bank_id': bank_id,
            'row_id': row_id,
            'col_id': col_id,
        }