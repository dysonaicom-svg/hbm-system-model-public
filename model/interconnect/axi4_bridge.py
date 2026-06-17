"""
AXI4 Bridge - Enhanced AXI4 Protocol Bridge for HBM Systems

This module provides a comprehensive AXI4 interface bridge with:
- Full AXI4 protocol support (AXI4, AXI4-Lite)
- Out-of-order transaction handling
- Outstanding transaction support
- Burst support (INCR, FIXED, WRAP)
- Transaction ID tracking and ordering
- QoS-based prioritization
- AXI4-Lite compatibility mode

Based on:
- ARM AMBA AXI4 Protocol Specification
- JEDEC JESD270-4A HBM4 specification

Usage:
    >>> from model.interconnect.axi4_bridge import AXI4Bridge, AXI4BridgeConfig
    >>> config = AXI4BridgeConfig(max_pending=16, enable_out_of_order=True)
    >>> bridge = AXI4Bridge(config)
    >>> # Submit AXI4 read transaction
    >>> txn_id = bridge.submit_read(addr=0x1000, length=7, qos=8)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import IntEnum, auto
from collections import deque
import logging
import uuid

logger = logging.getLogger('hbm4.axi4_bridge')
logger.setLevel(logging.WARNING)


# ============================================================================
# AXI4 Protocol Constants
# ============================================================================

class AXI4BurstType(IntEnum):
    """AXI4 Burst Types"""
    FIXED = 0b00
    INCR = 0b01
    WRAP = 0b10
    RESERVED = 0b11


class AXI4Response(IntEnum):
    """AXI4 Response Types"""
    OKAY = 0b00
    EXOKAY = 0b01
    SLVERR = 0b10
    DECERR = 0b11


class AXI4Size(IntEnum):
    """AXI4 Transfer Sizes"""
    SIZE_1 = 0b000   # 1 byte
    SIZE_2 = 0b001   # 2 bytes
    SIZE_4 = 0b010   # 4 bytes
    SIZE_8 = 0b011   # 8 bytes
    SIZE_16 = 0b100  # 16 bytes
    SIZE_32 = 0b101  # 32 bytes
    SIZE_64 = 0b110  # 64 bytes
    SIZE_128 = 0b111 # 128 bytes


class AXI4Lock(IntEnum):
    """AXI4 Lock Types"""
    NORMAL = 0b0
    EXCLUSIVE = 0b1


class AXI4Cache(IntEnum):
    """AXI4 Cache Attributes"""
    NON_BUFFERABLE = 0b0000
    BUFFERABLE = 0b0001
    WRITE_THROUGH_NO_ALLOC = 0b0010
    WRITE_THROUGH_READ_ALLOC = 0b0011
    WRITE_THROUGH_WRITE_ALLOC = 0b0100
    WRITE_THROUGH_READ_WRITE_ALLOC = 0b0101
    WRITE_BACK_NO_ALLOC = 0b0110
    WRITE_BACK_READ_ALLOC = 0b0111
    WRITE_BACK_WRITE_ALLOC = 0b1000
    WRITE_BACK_READ_WRITE_ALLOC = 0b1001


class AXI4Prot(IntEnum):
    """AXI4 Protection Attributes"""
    UNPRIVILEGED = 0b000
    PRIVILEGED = 0b001
    SECURE = 0b000
    NON_SECURE = 0b010
    DATA_ACCESS = 0b000
    INSTRUCTION_ACCESS = 0b100


class AXI4InterfaceType(IntEnum):
    """AXI4 Interface Type"""
    AXI4_FULL = 0     # Full AXI4 with all features
    AXI4_LITE = 1     # AXI4-Lite (simplified, 32-bit only)
    AXI4_STREAMING = 2  # AXI4-Stream (no address)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class AXI4BridgeConfig:
    """Configuration for AXI4 Bridge"""
    # Interface parameters
    interface_type: AXI4InterfaceType = AXI4InterfaceType.AXI4_FULL
    addr_width: int = 64
    data_width: int = 512
    
    # Transaction depth
    max_pending_reads: int = 16
    max_pending_writes: int = 16
    max_outstanding_ar: int = 16
    max_outstanding_aw: int = 16
    
    # Protocol features
    enable_out_of_order: bool = True
    enable_outstanding: bool = True
    enable_qos: bool = True
    enable_region: bool = True
    enable_user: bool = True
    enable_cache: bool = True
    enable_lock: bool = True
    
    # ID width (AXI4 supports up to 16-bit IDs)
    id_width: int = 8
    
    # Timing
    read_latency: int = 4
    write_latency: int = 4
    
    # Validation
    strict_protocol: bool = True
    max_burst_length: int = 256  # AXI4 allows up to 256 beats
    
    def __post_init__(self):
        """Validate configuration"""
        # Validate data width (must be power of 2, >= 8)
        if self.data_width < 8 or (self.data_width & (self.data_width - 1)) != 0:
            raise ValueError(f"data_width must be power of 2 >= 8, got {self.data_width}")
        
        # Validate address width
        if self.addr_width < 32:
            raise ValueError(f"addr_width must be >= 32, got {self.addr_width}")
        
        # Validate ID width
        if self.id_width < 1 or self.id_width > 16:
            raise ValueError(f"id_width must be 1-16, got {self.id_width}")
        
        # AXI4-Lite restrictions
        if self.interface_type == AXI4InterfaceType.AXI4_LITE:
            if self.data_width != 32 and self.data_width != 64:
                raise ValueError("AXI4-Lite requires 32 or 64 bit data width")
            if self.max_pending_reads > 1 or self.max_pending_writes > 1:
                logger.warning("AXI4-Lite does not support outstanding transactions")


@dataclass
class AXI4Signals:
    """AXI4 Signal State Container"""
    # AR channel
    arid: int = 0
    araddr: int = 0
    arlen: int = 0
    arsize: int = 0
    arburst: int = 0
    arlock: int = 0
    arcache: int = 0
    arprot: int = 0
    arqos: int = 0
    arregion: int = 0
    aruser: int = 0
    arvalid: bool = False
    arready: bool = False
    
    # AW channel
    awid: int = 0
    awaddr: int = 0
    awlen: int = 0
    awsize: int = 0
    awburst: int = 0
    awlock: int = 0
    awcache: int = 0
    awprot: int = 0
    awqos: int = 0
    awregion: int = 0
    awuser: int = 0
    awvalid: bool = False
    awready: bool = False
    
    # W channel
    wid: int = 0
    wdata: int = 0
    wstrb: int = 0
    wlast: bool = False
    wuser: int = 0
    wvalid: bool = False
    wready: bool = False
    
    # B channel
    bid: int = 0
    bresp: int = 0
    buser: int = 0
    bvalid: bool = False
    bready: bool = False
    
    # R channel
    rid: int = 0
    rdata: int = 0
    rresp: int = 0
    rlast: bool = False
    ruser: int = 0
    rvalid: bool = False
    rready: bool = False


# ============================================================================
# Transaction Classes
# ============================================================================

@dataclass
class AXI4ReadTransaction:
    """AXI4 Read Transaction (AR channel)"""
    addr: int
    size: int = 6          # bytes per beat
    length: int = 0        # beats - 1
    burst: AXI4BurstType = AXI4BurstType.INCR
    id: int = 0
    qos: int = 0
    cache: int = 0
    prot: int = 0
    lock: int = 0
    region: int = 0
    user: int = 0
    source: int = 0        # Source master ID
    
    # Transaction tracking
    transaction_id: int = field(default_factory=lambda: uuid.uuid4().int)
    submission_cycle: int = 0
    ar_issued_cycle: Optional[int] = None
    first_data_cycle: Optional[int] = None
    completion_cycle: Optional[int] = None
    
    # Computed properties
    @property
    def num_beats(self) -> int:
        """Number of data beats"""
        return self.length + 1
    
    @property
    def total_bytes(self) -> int:
        """Total bytes to transfer"""
        return self.num_beats * (1 << self.size)
    
    @property
    def is_completed(self) -> bool:
        """Check if transaction is completed"""
        return self.completion_cycle is not None
    
    @property
    def latency(self) -> int:
        """Transaction latency in cycles"""
        if self.completion_cycle is not None:
            return self.completion_cycle - self.submission_cycle
        return 0
    
    @property
    def address_phase_latency(self) -> int:
        """Latency from submission to AR issued"""
        if self.ar_issued_cycle is not None:
            return self.ar_issued_cycle - self.submission_cycle
        return 0
    
    @property
    def data_phase_latency(self) -> int:
        """Latency from AR to first data"""
        if self.first_data_cycle is not None and self.ar_issued_cycle is not None:
            return self.first_data_cycle - self.ar_issued_cycle
        return 0
    
    def get_beat_addresses(self) -> List[int]:
        """Calculate addresses for each beat in the burst"""
        addresses = []
        addr = self.addr
        num_beats = self.num_beats
        
        if self.burst == AXI4BurstType.FIXED:
            # Fixed: same address for all beats
            addresses = [addr] * num_beats
        elif self.burst == AXI4BurstType.INCR:
            # Increment: address increases by size
            for i in range(num_beats):
                addresses.append(addr + (i << self.size))
        elif self.burst == AXI4BurstType.WRAP:
            # Wrap: address wraps within cache line
            wrap_boundary = addr & ~((num_beats << self.size) - 1)
            for i in range(num_beats):
                addresses.append(wrap_boundary + ((addr + (i << self.size) - wrap_boundary) % (num_beats << self.size)))
        
        return addresses
    
    def __repr__(self) -> str:
        return (f"AXI4ReadTxn(id={self.id}, addr=0x{self.addr:x}, "
                f"len={self.length}+1, size=2^{self.size}, "
                f"burst={self.burst.name}, qos={self.qos})")


@dataclass
class AXI4WriteTransaction:
    """AXI4 Write Transaction (AW + W channels)"""
    addr: int
    size: int = 6          # bytes per beat
    length: int = 0        # beats - 1
    burst: AXI4BurstType = AXI4BurstType.INCR
    data: List[int] = field(default_factory=list)
    strb: List[int] = field(default_factory=list)
    id: int = 0
    qos: int = 0
    cache: int = 0
    prot: int = 0
    lock: int = 0
    region: int = 0
    user: int = 0
    source: int = 0
    
    # Transaction tracking
    transaction_id: int = field(default_factory=lambda: uuid.uuid4().int)
    submission_cycle: int = 0
    aw_issued_cycle: Optional[int] = None
    w_issued_cycles: List[int] = field(default_factory=list)
    b_issued_cycle: Optional[int] = None
    
    @property
    def num_beats(self) -> int:
        return self.length + 1
    
    @property
    def total_bytes(self) -> int:
        return self.num_beats * (1 << self.size)
    
    @property
    def is_completed(self) -> bool:
        return self.b_issued_cycle is not None
    
    @property
    def latency(self) -> int:
        if self.b_issued_cycle is not None:
            return self.b_issued_cycle - self.submission_cycle
        return 0
    
    def get_beat_addresses(self) -> List[int]:
        """Calculate addresses for each beat"""
        addresses = []
        addr = self.addr
        num_beats = self.num_beats
        
        if self.burst == AXI4BurstType.FIXED:
            addresses = [addr] * num_beats
        elif self.burst == AXI4BurstType.INCR:
            for i in range(num_beats):
                addresses.append(addr + (i << self.size))
        elif self.burst == AXI4BurstType.WRAP:
            wrap_boundary = addr & ~((num_beats << self.size) - 1)
            for i in range(num_beats):
                addresses.append(wrap_boundary + ((addr + (i << self.size) - wrap_boundary) % (num_beats << self.size)))
        
        return addresses
    
    def __repr__(self) -> str:
        return (f"AXI4WriteTxn(id={self.id}, addr=0x{self.addr:x}, "
                f"len={self.length}+1, size=2^{self.size}, "
                f"burst={self.burst.name}, qos={self.qos})")


@dataclass
class AXI4TransactionResponse:
    """AXI4 Transaction Response"""
    id: int
    is_write: bool        # True for write response, False for read
    resp: AXI4Response   # Response status enum
    data: Optional[int] = None  # For reads
    user: int = 0
    
    # Timing
    completion_cycle: int = 0
    
    @property
    def is_okay(self) -> bool:
        return self.resp == AXI4Response.OKAY
    
    @property
    def is_exokay(self) -> bool:
        return self.resp == AXI4Response.EXOKAY
    
    @property
    def is_slverr(self) -> bool:
        return self.resp == AXI4Response.SLVERR
    
    @property
    def is_decerr(self) -> bool:
        return self.resp == AXI4Response.DECERR
    
    @property
    def is_error(self) -> bool:
        return self.resp in (AXI4Response.SLVERR, AXI4Response.DECERR)


# ============================================================================
# Out-of-Order Queue
# ============================================================================

class AXI4OutOfOrderQueue:
    """Queue that supports out-of-order completion"""
    
    def __init__(self, max_size: int = 16):
        self.max_size = max_size
        self._pending: Dict[int, AXI4ReadTransaction] = {}
        self._completed_order: List[int] = []  # IDs in completion order
        self._next_completion_idx: int = 0
    
    def add(self, txn: AXI4ReadTransaction) -> bool:
        """Add transaction to queue"""
        if len(self._pending) >= self.max_size:
            return False
        if txn.id in self._pending:
            logger.warning(f"Duplicate transaction ID: {txn.id}")
            return False
        self._pending[txn.id] = txn
        return True
    
    def mark_completed(self, txn_id: int, cycle: int) -> None:
        """Mark transaction as completed"""
        if txn_id in self._pending:
            txn = self._pending[txn_id]
            txn.completion_cycle = cycle
            self._completed_order.append(txn_id)
            del self._pending[txn_id]
    
    def get_next_completable(self) -> Optional[AXI4ReadTransaction]:
        """Get next transaction that can be returned (in order)"""
        while self._next_completion_idx < len(self._completed_order):
            txn_id = self._completed_order[self._next_completion_idx]
            self._next_completion_idx += 1
            if txn_id in self._pending:
                # Check if completed
                continue
            # This should not happen - already deleted from pending
        return None
    
    def peek_completed(self) -> List[AXI4ReadTransaction]:
        """Peek at completed transactions"""
        completed = []
        for txn_id in self._completed_order[self._next_completion_idx:]:
            if txn_id in self._pending:
                txn = self._pending[txn_id]
                if txn.is_completed:
                    completed.append(txn)
        return completed
    
    def remove(self, txn_id: int) -> Optional[AXI4ReadTransaction]:
        """Remove transaction from queue"""
        if txn_id in self._pending:
            txn = self._pending[txn_id]
            del self._pending[txn_id]
            return txn
        return None
    
    def __len__(self) -> int:
        return len(self._pending)
    
    def __contains__(self, txn_id: int) -> bool:
        return txn_id in self._pending


# ============================================================================
# Main Bridge Class
# ============================================================================

class AXI4Bridge:
    """
    AXI4 Bridge for HBM Memory Systems
    
    Features:
    - Full AXI4 protocol support
    - AXI4-Lite compatibility
    - Out-of-order transaction support
    - Outstanding transaction handling
    - Burst support (INCR, FIXED, WRAP)
    - QoS-based prioritization
    - Transaction ID tracking
    
    Usage:
        >>> config = AXI4BridgeConfig(
        ...     max_pending_reads=16,
        ...     enable_out_of_order=True,
        ...     enable_outstanding=True
        ... )
        >>> bridge = AXI4Bridge(config)
        >>> 
        >>> # Submit transactions
        >>> read_id = bridge.submit_read(addr=0x1000, length=7, qos=8)
        >>> write_id = bridge.submit_write(addr=0x2000, data=[...], length=3)
        >>> 
        >>> # Clock the bridge
        >>> responses = bridge.tick()
    """
    
    def __init__(self, config: Optional[AXI4BridgeConfig] = None):
        """Initialize AXI4 Bridge
        
        Args:
            config: Bridge configuration (uses default if None)
        """
        self.config = config or AXI4BridgeConfig()
        self._cycle: int = 0
        
        # Transaction tracking
        self._pending_reads: Dict[int, AXI4ReadTransaction] = {}
        self._pending_writes: Dict[int, AXI4WriteTransaction] = {}
        
        # Out-of-order queues (one per ID)
        self._read_completion_queue: AXI4OutOfOrderQueue = AXI4OutOfOrderQueue(
            self.config.max_outstanding_ar
        )
        
        # Outstanding transaction tracking
        self._outstanding_ar: int = 0
        self._outstanding_aw: int = 0
        self._outstanding_r_beats: int = 0
        self._outstanding_w_beats: int = 0
        
        # Signal state
        self.signals = AXI4Signals()
        
        # Transaction counters
        self._read_txn_counter: int = 0
        self._write_txn_counter: int = 0
        
        # Statistics
        self.stats = {
            'read_submitted': 0,
            'write_submitted': 0,
            'read_completed': 0,
            'write_completed': 0,
            'ar_issued': 0,
            'aw_issued': 0,
            'w_issued': 0,
            'r_beats': 0,
            'b_responses': 0,
            'total_read_latency': 0,
            'total_write_latency': 0,
            'out_of_order_completions': 0,
            'protocol_violations': 0,
        }
        
        # Response callbacks
        self._read_response_callbacks: List = []
        self._write_response_callbacks: List = []
        
        logger.info(f"AXI4Bridge initialized: {self.config}")
    
    # ========================================================================
    # Transaction Submission
    # ========================================================================
    
    def submit_read(
        self,
        addr: int,
        size: int = 6,
        length: int = 0,
        burst: AXI4BurstType = AXI4BurstType.INCR,
        id: int = 0,
        qos: int = 0,
        cache: int = 0,
        prot: int = 0,
        lock: int = 0,
        source: int = 0,
    ) -> int:
        """
        Submit a read transaction
        
        Args:
            addr: Starting address
            size: Bytes per beat (0=1, 1=2, 2=4, ... 6=64, 7=128)
            length: Number of beats - 1 (0-255 for AXI4)
            burst: Burst type (FIXED, INCR, WRAP)
            id: Transaction ID
            qos: QoS priority (0-15, higher = higher priority)
            cache: Cache attributes
            prot: Protection attributes
            lock: Lock type
            source: Source master ID
            
        Returns:
            Transaction ID
        """
        # Validate burst length
        if length > self.config.max_burst_length - 1:
            raise ValueError(f"Burst length {length+1} exceeds maximum {self.config.max_burst_length}")
        
        # Check pending limit
        if len(self._pending_reads) >= self.config.max_pending_reads:
            logger.warning("Read queue full, rejecting transaction")
            return -1
        
        # Create transaction
        txn = AXI4ReadTransaction(
            addr=addr,
            size=size,
            length=length,
            burst=burst,
            id=id if id != 0 else self._read_txn_counter,
            qos=qos,
            cache=cache,
            prot=prot,
            lock=lock,
            source=source,
        )
        txn.submission_cycle = self._cycle
        
        # Add to pending
        self._pending_reads[txn.id] = txn
        self._read_completion_queue.add(txn)
        self._read_txn_counter += 1
        
        self.stats['read_submitted'] += 1
        
        logger.debug(f"Read txn submitted: id={txn.id}, addr=0x{addr:x}, len={length+1}")
        
        return txn.id
    
    def submit_write(
        self,
        addr: int,
        data: List[int],
        size: int = 6,
        length: int = 0,
        burst: AXI4BurstType = AXI4BurstType.INCR,
        strb: Optional[List[int]] = None,
        id: int = 0,
        qos: int = 0,
        cache: int = 0,
        prot: int = 0,
        lock: int = 0,
        source: int = 0,
    ) -> int:
        """
        Submit a write transaction
        
        Args:
            addr: Starting address
            data: Write data (list of integers)
            size: Bytes per beat
            length: Number of beats - 1
            burst: Burst type
            strb: Byte strobes (None = all bytes valid)
            id: Transaction ID
            qos: QoS priority
            cache: Cache attributes
            prot: Protection attributes
            lock: Lock type
            source: Source master ID
            
        Returns:
            Transaction ID
        """
        # Validate
        if length > self.config.max_burst_length - 1:
            raise ValueError(f"Burst length {length+1} exceeds maximum")
        
        if len(self._pending_writes) >= self.config.max_pending_writes:
            logger.warning("Write queue full, rejecting transaction")
            return -1
        
        # Generate default strb if not provided
        if strb is None:
            strb = [0xFF] * len(data)
        
        # Create transaction
        txn = AXI4WriteTransaction(
            addr=addr,
            size=size,
            length=length,
            burst=burst,
            data=data,
            strb=strb,
            id=id if id != 0 else self._write_txn_counter,
            qos=qos,
            cache=cache,
            prot=prot,
            lock=lock,
            source=source,
        )
        txn.submission_cycle = self._cycle
        
        # Add to pending
        self._pending_writes[txn.id] = txn
        self._write_txn_counter += 1
        
        self.stats['write_submitted'] += 1
        
        logger.debug(f"Write txn submitted: id={txn.id}, addr=0x{addr:x}, len={length+1}")
        
        return txn.id
    
    # ========================================================================
    # Clock/Tick Methods
    # ========================================================================
    
    def tick(self) -> List[AXI4Response]:
        """
        Advance simulation by one clock cycle
        
        Returns:
            List of completed responses this cycle
        """
        self._cycle += 1
        responses = []
        
        # Process read channel
        responses.extend(self._process_read_channel())
        
        # Process write channels
        responses.extend(self._process_write_channels())
        
        return responses
    
    def _process_read_channel(self) -> List[AXI4Response]:
        """Process AR/R channels"""
        responses = []
        
        # Issue AR if available
        if not self.signals.arvalid or self.signals.arready:
            txn = self._select_read_transaction()
            if txn is not None:
                self._issue_ar(txn)
        
        # Process R channel response
        if self.signals.rvalid and self.signals.rready:
            txn_id = self.signals.rid
            resp = self.signals.rresp
            data = self.signals.rdata
            is_last = self.signals.rlast
            
            self.stats['r_beats'] += 1
            
            # Mark transaction progress
            if txn_id in self._pending_reads:
                txn = self._pending_reads[txn_id]
                if txn.first_data_cycle is None:
                    txn.first_data_cycle = self._cycle
                
                if is_last:
                    # Transaction complete
                    txn.completion_cycle = self._cycle
                    self._read_completion_queue.mark_completed(txn_id, self._cycle)
                    self.stats['read_completed'] += 1
                    self.stats['total_read_latency'] += txn.latency
                    self._outstanding_ar -= 1
                    
                    responses.append(AXI4TransactionResponse(
                        id=txn_id,
                        is_write=False,
                        resp=AXI4Response(resp),
                        data=data,
                        completion_cycle=self._cycle,
                    ))
                    
                    # Call callbacks
                    for cb in self._read_response_callbacks:
                        cb(txn)
                    
                    logger.debug(f"Read txn completed: id={txn_id}, latency={txn.latency}")
        
        return responses
    
    def _process_write_channels(self) -> List[AXI4TransactionResponse]:
        """Process AW/W/B channels"""
        responses = []
        
        # Issue AW if available
        if not self.signals.awvalid or self.signals.awready:
            txn = self._select_write_transaction()
            if txn is not None:
                self._issue_aw(txn)
        
        # Issue W if available
        if not self.signals.wvalid or self.signals.wready:
            txn = self._get_write_with_pending_data()
            if txn is not None:
                self._issue_w(txn)
        
        # Process B channel response
        if self.signals.bvalid and self.signals.bready:
            txn_id = self.signals.bid
            resp = self.signals.bresp
            
            self.stats['b_responses'] += 1
            
            if txn_id in self._pending_writes:
                txn = self._pending_writes[txn_id]
                txn.b_issued_cycle = self._cycle
                self.stats['write_completed'] += 1
                self.stats['total_write_latency'] += txn.latency
                self._outstanding_aw -= 1
                
                responses.append(AXI4TransactionResponse(
                    id=txn_id,
                    is_write=True,
                    resp=AXI4Response(resp),
                    completion_cycle=self._cycle,
                ))
                
                # Call callbacks
                for cb in self._write_response_callbacks:
                    cb(txn)
                
                logger.debug(f"Write txn completed: id={txn_id}, latency={txn.latency}")
                
                # Remove from pending
                del self._pending_writes[txn_id]
        
        return responses
    
    def _select_read_transaction(self) -> Optional[AXI4ReadTransaction]:
        """Select next read transaction based on QoS"""
        if not self._pending_reads:
            return None
        
        if self._outstanding_ar >= self.config.max_outstanding_ar:
            return None
        
        # Sort by QoS (higher priority first)
        candidates = sorted(
            self._pending_reads.values(),
            key=lambda t: (-t.qos, t.submission_cycle)
        )
        
        for txn in candidates:
            if txn.ar_issued_cycle is None:
                return txn
        
        return None
    
    def _select_write_transaction(self) -> Optional[AXI4WriteTransaction]:
        """Select next write transaction based on QoS"""
        if not self._pending_writes:
            return None
        
        if self._outstanding_aw >= self.config.max_outstanding_aw:
            return None
        
        candidates = sorted(
            self._pending_writes.values(),
            key=lambda t: (-t.qos, t.submission_cycle)
        )
        
        for txn in candidates:
            if txn.aw_issued_cycle is None:
                return txn
        
        return None
    
    def _issue_ar(self, txn: AXI4ReadTransaction) -> None:
        """Issue AR transaction"""
        self.signals.arvalid = True
        self.signals.araddr = txn.addr
        self.signals.arsize = txn.size
        self.signals.arlen = txn.length
        self.signals.arburst = int(txn.burst)
        self.signals.arid = txn.id
        self.signals.arqos = txn.qos
        self.signals.arcache = txn.cache
        self.signals.arprot = txn.prot
        self.signals.arlock = txn.lock
        self.signals.arregion = txn.region
        self.signals.aruser = txn.user
        
        txn.ar_issued_cycle = self._cycle
        self._outstanding_ar += 1
        self.stats['ar_issued'] += 1
        
        logger.debug(f"AR issued: id={txn.id}, addr=0x{txn.addr:x}")
    
    def _issue_aw(self, txn: AXI4WriteTransaction) -> None:
        """Issue AW transaction"""
        self.signals.awvalid = True
        self.signals.awaddr = txn.addr
        self.signals.awsize = txn.size
        self.signals.awlen = txn.length
        self.signals.awburst = int(txn.burst)
        self.signals.awid = txn.id
        self.signals.awqos = txn.qos
        self.signals.awcache = txn.cache
        self.signals.awprot = txn.prot
        self.signals.awlock = txn.lock
        self.signals.awregion = txn.region
        self.signals.awuser = txn.user
        
        txn.aw_issued_cycle = self._cycle
        self._outstanding_aw += 1
        self.stats['aw_issued'] += 1
        
        logger.debug(f"AW issued: id={txn.id}, addr=0x{txn.addr:x}")
    
    def _get_write_with_pending_data(self) -> Optional[AXI4WriteTransaction]:
        """Get transaction that has pending W data"""
        for txn in self._pending_writes.values():
            if txn.aw_issued_cycle is not None:
                # Check if has pending beats
                issued = len(txn.w_issued_cycles)
                total = txn.num_beats
                if issued < total:
                    return txn
        return None
    
    def _issue_w(self, txn: AXI4WriteTransaction) -> None:
        """Issue W beat"""
        beat_idx = len(txn.w_issued_cycles)
        
        self.signals.wvalid = True
        self.signals.wid = txn.id
        self.signals.wdata = txn.data[beat_idx] if beat_idx < len(txn.data) else 0
        self.signals.wstrb = txn.strb[beat_idx] if beat_idx < len(txn.strb) else 0xFF
        self.signals.wlast = (beat_idx == txn.length)
        self.signals.wuser = txn.user
        
        txn.w_issued_cycles.append(self._cycle)
        self._outstanding_w_beats += 1
        self.stats['w_issued'] += 1
        
        logger.debug(f"W beat issued: id={txn.id}, beat={beat_idx+1}/{txn.num_beats}")
    
    # ========================================================================
    # Signal Interface
    # ========================================================================
    
    def set_ar_ready(self, ready: bool) -> None:
        """Set ARREADY signal"""
        self.signals.arready = ready
    
    def set_aw_ready(self, ready: bool) -> None:
        """Set AWREADY signal"""
        self.signals.awready = ready
    
    def set_w_ready(self, ready: bool) -> None:
        """Set WREADY signal"""
        self.signals.wready = ready
    
    def set_r_valid(self, valid: bool) -> None:
        """Set RVALID signal (slave drives)"""
        self.signals.rvalid = valid
    
    def set_b_valid(self, valid: bool) -> None:
        """Set BVALID signal (slave drives)"""
        self.signals.bvalid = valid
    
    def drive_r_channel(self, rid: int, rdata: int, rresp: int, rlast: bool) -> None:
        """Drive R channel (for slave interface)"""
        self.signals.rid = rid
        self.signals.rdata = rdata
        self.signals.rresp = rresp
        self.signals.rlast = rlast
        self.signals.rvalid = True
    
    def drive_b_channel(self, bid: int, bresp: int) -> None:
        """Drive B channel (for slave interface)"""
        self.signals.bid = bid
        self.signals.bresp = bresp
        self.signals.bvalid = True
    
    # ========================================================================
    # Status and Statistics
    # ========================================================================
    
    def get_pending_count(self, is_read: bool) -> int:
        """Get number of pending transactions"""
        if is_read:
            return len(self._pending_reads)
        return len(self._pending_writes)
    
    def get_outstanding_count(self, is_read: bool) -> int:
        """Get number of outstanding transactions"""
        if is_read:
            return self._outstanding_ar
        return self._outstanding_aw
    
    def get_average_latency(self, is_read: bool) -> float:
        """Get average transaction latency"""
        if is_read:
            if self.stats['read_completed'] == 0:
                return 0.0
            return self.stats['total_read_latency'] / self.stats['read_completed']
        else:
            if self.stats['write_completed'] == 0:
                return 0.0
            return self.stats['total_write_latency'] / self.stats['write_completed']
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics"""
        return {
            'cycle': self._cycle,
            'pending_reads': len(self._pending_reads),
            'pending_writes': len(self._pending_writes),
            'outstanding_ar': self._outstanding_ar,
            'outstanding_aw': self._outstanding_aw,
            'transactions': self.stats.copy(),
            'avg_read_latency': self.get_average_latency(True),
            'avg_write_latency': self.get_average_latency(False),
            'throughput_r_beats': self.stats['r_beats'] / max(1, self._cycle),
            'throughput_w_beats': self.stats['w_issued'] / max(1, self._cycle),
        }
    
    def reset(self) -> None:
        """Reset bridge state"""
        self._cycle = 0
        self._pending_reads.clear()
        self._pending_writes.clear()
        self._read_completion_queue = AXI4OutOfOrderQueue(self.config.max_outstanding_ar)
        self._outstanding_ar = 0
        self._outstanding_aw = 0
        self._outstanding_r_beats = 0
        self._outstanding_w_beats = 0
        
        # Reset signals
        self.signals = AXI4Signals()
        
        # Reset stats
        for key in self.stats:
            self.stats[key] = 0
        
        logger.info("AXI4Bridge reset")
    
    # ========================================================================
    # Callbacks
    # ========================================================================
    
    def on_read_complete(self, callback) -> None:
        """Register read completion callback"""
        self._read_response_callbacks.append(callback)
    
    def on_write_complete(self, callback) -> None:
        """Register write completion callback"""
        self._write_response_callbacks.append(callback)


# ============================================================================
# Factory Functions
# ============================================================================

def create_axi4_bridge(
    max_pending: int = 16,
    enable_out_of_order: bool = True,
    enable_outstanding: bool = True,
    enable_qos: bool = True,
    data_width: int = 512,
) -> AXI4Bridge:
    """Create AXI4 bridge with common configuration"""
    config = AXI4BridgeConfig(
        max_pending_reads=max_pending,
        max_pending_writes=max_pending,
        enable_out_of_order=enable_out_of_order,
        enable_outstanding=enable_outstanding,
        enable_qos=enable_qos,
        data_width=data_width,
    )
    return AXI4Bridge(config)


def create_axi4lite_bridge() -> AXI4Bridge:
    """Create AXI4-Lite bridge (simplified protocol)"""
    config = AXI4BridgeConfig(
        interface_type=AXI4InterfaceType.AXI4_LITE,
        max_pending_reads=1,
        max_pending_writes=1,
        data_width=64,
        enable_out_of_order=False,
        enable_outstanding=False,
    )
    return AXI4Bridge(config)


if __name__ == "__main__":
    # Simple test
    print("Testing AXI4 Bridge...")

    bridge = create_axi4_bridge(max_pending=16)

    # Submit some transactions
    read_id = bridge.submit_read(addr=0x1000, length=7, qos=8)
    write_id = bridge.submit_write(addr=0x2000, data=[0xDEADBEEF] * 8, length=7, qos=4)

    print(f"Submitted read: {read_id}, write: {write_id}")

    # Clock a few cycles
    for i in range(20):
        responses = bridge.tick()
        if responses:
            print(f"Cycle {i}: {len(responses)} responses")

    print(f"\nStats: {bridge.get_stats()}")


# ============================================================================
# Enhanced AXI4 Bridge Features
# ============================================================================

class AXI4TransactionIDTracker:
    """
    Tracks AXI4 transaction IDs for out-of-order completion.

    Supports:
    - Transaction ID validation
    - ID aliasing detection
    - Read/write ID space separation
    - Transaction ordering tracking
    """

    def __init__(self, id_width: int = 8):
        self.id_width = id_width
        self.max_id = (1 << id_width) - 1

        # Track active transaction IDs
        self._active_read_ids: Set[int] = set()
        self._active_write_ids: Set[int] = set()

        # Ordering state per ID
        self._read_order: Dict[int, int] = {}  # id -> sequence number
        self._write_order: Dict[int, int] = {}

        # Statistics
        self.stats = {
            'read_ids_used': 0,
            'write_ids_used': 0,
            'id_collisions': 0,
            'max_concurrent_reads': 0,
            'max_concurrent_writes': 0,
        }

        self._sequence = 0

    def allocate_read_id(self, requested_id: Optional[int] = None) -> int:
        """Allocate a read transaction ID"""
        if requested_id is not None and 0 <= requested_id <= self.max_id:
            txn_id = requested_id
        else:
            # Find next available ID
            for i in range(self.max_id + 1):
                if i not in self._active_read_ids:
                    txn_id = i
                    break
            else:
                txn_id = self._sequence & self.max_id
                self.stats['id_collisions'] += 1

        self._active_read_ids.add(txn_id)
        self._read_order[txn_id] = self._sequence
        self._sequence += 1
        self.stats['read_ids_used'] += 1
        self.stats['max_concurrent_reads'] = max(
            self.stats['max_concurrent_reads'],
            len(self._active_read_ids)
        )

        return txn_id

    def allocate_write_id(self, requested_id: Optional[int] = None) -> int:
        """Allocate a write transaction ID"""
        if requested_id is not None and 0 <= requested_id <= self.max_id:
            txn_id = requested_id
        else:
            for i in range(self.max_id + 1):
                if i not in self._active_write_ids:
                    txn_id = i
                    break
            else:
                txn_id = self._sequence & self.max_id
                self.stats['id_collisions'] += 1

        self._active_write_ids.add(txn_id)
        self._write_order[txn_id] = self._sequence
        self._sequence += 1
        self.stats['write_ids_used'] += 1
        self.stats['max_concurrent_writes'] = max(
            self.stats['max_concurrent_writes'],
            len(self._active_write_ids)
        )

        return txn_id

    def release_read_id(self, txn_id: int) -> None:
        """Release a read transaction ID"""
        self._active_read_ids.discard(txn_id)
        self._read_order.pop(txn_id, None)

    def release_write_id(self, txn_id: int) -> None:
        """Release a write transaction ID"""
        self._active_write_ids.discard(txn_id)
        self._write_order.pop(txn_id, None)

    def get_read_order(self, txn_id: int) -> Optional[int]:
        """Get ordering sequence number for read transaction"""
        return self._read_order.get(txn_id)

    def get_write_order(self, txn_id: int) -> Optional[int]:
        """Get ordering sequence number for write transaction"""
        return self._write_order.get(txn_id)

    def is_read_active(self, txn_id: int) -> bool:
        """Check if read transaction is active"""
        return txn_id in self._active_read_ids

    def is_write_active(self, txn_id: int) -> bool:
        """Check if write transaction is active"""
        return txn_id in self._active_write_ids

    def active_read_count(self) -> int:
        """Get number of active read transactions"""
        return len(self._active_read_ids)

    def active_write_count(self) -> int:
        """Get number of active write transactions"""
        return len(self._active_write_ids)

    def reset(self) -> None:
        """Reset all tracking state"""
        self._active_read_ids.clear()
        self._active_write_ids.clear()
        self._read_order.clear()
        self._write_order.clear()
        self._sequence = 0
        for key in self.stats:
            self.stats[key] = 0


class AXI4ReorderingBuffer:
    """
    Buffer for out-of-order read responses that returns them in order.

    Features:
    - Out-of-order acceptance
    - In-order delivery
    - Speculative completion tracking
    - Gap detection for deadlocks
    """

    def __init__(self, max_entries: int = 32):
        self.max_entries = max_entries
        self._buffer: Dict[int, AXI4TransactionResponse] = {}
        self._expected_order: int = 0
        self._completion_order: List[int] = []

        # Statistics
        self.stats = {
            'entries_received': 0,
            'entries_delivered': 0,
            'out_of_order_receptions': 0,
            'in_order_receptions': 0,
            'buffer_overflows': 0,
        }

    def push(self, response: AXI4TransactionResponse, order: int) -> List[AXI4TransactionResponse]:
        """
        Push a response into the buffer.

        Returns list of responses that can now be delivered in order.
        """
        self._buffer[order] = response
        self.stats['entries_received'] += 1

        # Check if this was out of order
        if order != self._expected_order:
            self.stats['out_of_order_receptions'] += 1
        else:
            self.stats['in_order_receptions'] += 1

        # Collect all contiguous responses starting from expected
        ready = []
        while self._expected_order in self._buffer:
            ready.append(self._buffer.pop(self._expected_order))
            self._expected_order += 1

        if ready:
            self.stats['entries_delivered'] += len(ready)

        return ready

    def can_accept(self) -> bool:
        """Check if buffer can accept more entries"""
        return len(self._buffer) < self.max_entries

    def pending_count(self) -> int:
        """Number of entries waiting to be delivered"""
        return len(self._buffer)

    def expected_order(self) -> int:
        """Next expected order number"""
        return self._expected_order

    def reset(self) -> None:
        """Reset buffer state"""
        self._buffer.clear()
        self._expected_order = 0
        self._completion_order.clear()
        for key in self.stats:
            self.stats[key] = 0


class AXI4BurstGenerator:
    """
    Generates beat addresses for AXI4 bursts.

    Supports all burst types:
    - FIXED: Same address for all beats
    - INCR: Address increments by size
    - WRAP: Address wraps within boundary
    """

    @staticmethod
    def generate_addresses(
        start_addr: int,
        size: int,
        length: int,
        burst_type: AXI4BurstType,
        beat_size_bytes: int = 1,
    ) -> List[int]:
        """
        Generate list of beat addresses for a burst.

        Args:
            start_addr: Starting address
            size: Size encoding (0=1B, 1=2B, 2=4B, etc.)
            length: Burst length (beats - 1)
            burst_type: Type of burst
            beat_size_bytes: Size of each beat in bytes

        Returns:
            List of beat addresses
        """
        num_beats = length + 1
        size_bytes = beat_size_bytes << size  # 2^size * beat_size
        addresses = []

        if burst_type == AXI4BurstType.FIXED:
            addresses = [start_addr] * num_beats

        elif burst_type == AXI4BurstType.INCR:
            for i in range(num_beats):
                addresses.append(start_addr + i * size_bytes)

        elif burst_type == AXI4BurstType.WRAP:
            # Wrap boundary is determined by total burst size
            total_size = num_beats * size_bytes
            wrap_boundary = start_addr & ~(total_size - 1)

            for i in range(num_beats):
                offset = i * size_bytes
                wrapped_addr = wrap_boundary + ((start_addr + offset - wrap_boundary) % total_size)
                addresses.append(wrapped_addr)
        else:
            # RESERVED - treat as INCR
            for i in range(num_beats):
                addresses.append(start_addr + i * size_bytes)

        return addresses

    @staticmethod
    def validate_burst(
        addr: int,
        size: int,
        length: int,
        burst_type: AXI4BurstType,
        max_length: int = 256,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a burst transaction.

        Returns:
            (is_valid, error_message)
        """
        # Check length
        if length >= max_length:
            return False, f"Burst length {length + 1} exceeds maximum {max_length}"

        # Check alignment
        size_bytes = 1 << size
        if addr & (size_bytes - 1):
            return False, f"Address 0x{addr:x} not aligned to size {size_bytes}"

        # Check WRAP boundary
        if burst_type == AXI4BurstType.WRAP:
            total_size = (length + 1) * size_bytes
            if addr & (total_size - 1):
                return False, f"WRAP burst address 0x{addr:x} not aligned to boundary 0x{total_size:x}"

        # Check for reserved burst type
        if burst_type == AXI4BurstType.RESERVED:
            return False, "RESERVED burst type not allowed"

        return True, None


class AXI4MasterInterface:
    """
    High-level AXI4 master interface for submitting transactions.

    Provides a simplified interface compared to raw bridge:
    - Automatic burst handling
    - QoS scheduling hints
    - Transaction tracking
    - Response aggregation
    """

    def __init__(
        self,
        bridge: AXI4Bridge,
        master_id: int = 0,
        default_qos: int = 8,
    ):
        self.bridge = bridge
        self.master_id = master_id
        self.default_qos = default_qos

        # Transaction tracking
        self._pending_transactions: Dict[int, AXI4TransactionResponse] = {}
        self._burst_generator = AXI4BurstGenerator()

        # Statistics
        self.stats = {
            'reads_submitted': 0,
            'writes_submitted': 0,
            'reads_completed': 0,
            'writes_completed': 0,
            'total_bytes_read': 0,
            'total_bytes_written': 0,
        }

    def read(
        self,
        addr: int,
        size: int = 6,  # 64 bytes
        length: int = 0,
        qos: Optional[int] = None,
        id: Optional[int] = None,
    ) -> int:
        """
        Submit a read transaction.

        Args:
            addr: Starting address
            size: Size encoding (2^size bytes per beat)
            length: Burst length (beats - 1)
            qos: QoS priority (None = use default)
            id: Transaction ID (None = auto-assign)

        Returns:
            Transaction ID
        """
        txn_id = self.bridge.submit_read(
            addr=addr,
            size=size,
            length=length,
            burst=AXI4BurstType.INCR,
            qos=qos if qos is not None else self.default_qos,
            id=id if id is not None else 0,
            source=self.master_id,
        )

        if txn_id >= 0:
            self.stats['reads_submitted'] += 1

        return txn_id

    def write(
        self,
        addr: int,
        data: List[int],
        size: int = 6,
        qos: Optional[int] = None,
        id: Optional[int] = None,
    ) -> int:
        """
        Submit a write transaction.

        Args:
            addr: Starting address
            data: Write data
            size: Size encoding
            qos: QoS priority
            id: Transaction ID

        Returns:
            Transaction ID
        """
        length = len(data) - 1
        txn_id = self.bridge.submit_write(
            addr=addr,
            data=data,
            size=size,
            length=length,
            burst=AXI4BurstType.INCR,
            qos=qos if qos is not None else self.default_qos,
            id=id if id is not None else 0,
            source=self.master_id,
        )

        if txn_id >= 0:
            self.stats['writes_submitted'] += 1

        return txn_id

    def read_blocking(
        self,
        addr: int,
        size: int = 6,
        length: int = 0,
        timeout_cycles: int = 10000,
    ) -> Optional[List[int]]:
        """
        Submit read and wait for completion.

        Returns:
            Read data as list of integers
        """
        txn_id = self.read(addr=addr, size=size, length=length)
        if txn_id < 0:
            return None

        start_cycle = self.bridge._cycle
        while (self.bridge._cycle - start_cycle) < timeout_cycles:
            self.bridge.tick()
            if txn_id not in self.bridge._pending_reads:
                # Transaction completed
                return None  # Would need to track actual data
        return None

    def write_blocking(
        self,
        addr: int,
        data: List[int],
        size: int = 6,
        timeout_cycles: int = 10000,
    ) -> bool:
        """
        Submit write and wait for completion.

        Returns:
            True if write completed successfully
        """
        txn_id = self.write(addr=addr, data=data, size=size)
        if txn_id < 0:
            return False

        start_cycle = self.bridge._cycle
        while (self.bridge._cycle - start_cycle) < timeout_cycles:
            self.bridge.tick()
            if txn_id not in self.bridge._pending_writes:
                return True
        return False

    def get_pending_count(self) -> int:
        """Get total pending transactions"""
        return self.bridge.get_pending_count(True) + self.bridge.get_pending_count(False)

    def reset_stats(self) -> None:
        """Reset statistics"""
        for key in self.stats:
            self.stats[key] = 0