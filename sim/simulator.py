"""
HBM System Simulation Framework - Optimized Version
End-to-end simulation framework integrating controller, DRAM model, and traffic generator

Optimizations:
- __slots__ for memory reduction
- Batch request processing
- Object pooling to reduce GC pressure
- Cached timing calculations

Pipeline Integration:
- TrafficGenerator: Generates memory requests
- HBMController: Schedules requests using FR-FCFS/QoS
- CommandSequencer: Generates DRAM command sequences
- CommandPipeline: Executes commands on DRAM with timing
- DRAMModel: Full DRAM timing model
- MultiChannelSupport: 8-channel HBM3 proper channel selection and load balancing
"""

import time
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import logging

from model.dram.dram_model import DRAMModel, create_dram_model
from model.dram.timing import HBM3Timing, get_timing_for_hbm_version
from model.controller.controller import HBMController
from model.controller.config import HBMConfig, HBM3_DEFAULT
from model.controller.request import HBMRequest, HBMResponse, RequestBatch, HBMRequestPool
from model.controller.command_sequencer import (
    CommandSequencer,
    CommandSequence,
    BankState as SeqBankState,
    DRAMCommand,
)
from model.controller.command_pipeline import CommandPipeline
from model.dram.bank_state_machine import BankStateEnum
from model.multi_channel import (
    ChannelSelector,
    MultiChannelTrafficGenerator,
    MultiChannelStats,
    ChannelStats,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrafficPattern(Enum):
    """Traffic patterns"""
    RANDOM = "random"
    SEQUENTIAL = "sequential"
    STRIDE = "stride"
    HOT_SPOT = "hot_spot"
    ADDR_SCATTER = "scatter"


@dataclass
class SimulationConfig:
    """Simulation configuration"""
    # Clock configuration
    clock_freq_hz: float = 1.28e9  # 1.28 GHz
    simulation_time_us: float = 100.0  # Simulation time (microseconds)

    # Traffic configuration
    traffic_pattern: TrafficPattern = TrafficPattern.RANDOM
    request_rate: float = 0.5  # Request rate (0-1)
    read_ratio: float = 0.7  # Read request ratio
    burst_size: int = 64  # Burst size

    # Address configuration
    address_range: int = 0x100_0000  # Address range
    stride_value: int = 4096  # Stride pattern step

    # HBM configuration
    hbm_config: HBMConfig = field(default_factory=lambda: HBM3_DEFAULT)

    # Simulation options
    enable_logging: bool = False
    enable_stats: bool = True
    seed: Optional[int] = None  # Random seed


@dataclass
class SimulationStats:
    """Simulation statistics"""
    total_cycles: int = 0
    total_requests: int = 0
    completed_requests: int = 0
    read_requests: int = 0
    write_requests: int = 0
    row_hits: int = 0
    row_misses: int = 0
    row_conflicts: int = 0
    total_latency_cycles: int = 0
    refresh_count: int = 0

    # Extended statistics for cycle-accurate analysis
    max_latency_cycles: int = 0
    min_latency_cycles: int = 0
    total_dram_activations: int = 0
    total_dram_reads: int = 0
    total_dram_writes: int = 0
    total_refresh_cycles: int = 0
    idle_cycles: int = 0
    busy_cycles: int = 0

    # Multi-channel statistics
    per_channel_stats: Dict[int, ChannelStats] = field(default_factory=dict)

    # Peak bandwidth for efficiency calculation (GB/s)
    _peak_bandwidth: float = field(default=0.0, repr=False)

    @property
    def avg_latency(self) -> float:
        if self.completed_requests == 0:
            return 0.0
        return self.total_latency_cycles / self.completed_requests

    @property
    def row_hit_rate(self) -> float:
        total = self.row_hits + self.row_misses + self.row_conflicts
        if total == 0:
            return 0.0
        return self.row_hits / total

    @property
    def throughput_gbps(self) -> float:
        if self.total_cycles == 0:
            return 0.0
        # HBM3 burst length 32 bytes, each request 4 bursts = 128 bytes per request
        bytes_transferred = self.completed_requests * 128
        # tCK = 781.25 ps = 0.78125 ns per cycle
        tCK_ns = 0.78125
        total_ns = self.total_cycles * tCK_ns
        # Bandwidth = bytes / seconds = bytes / (ns * 1e-9) / 1e9 = GB/s
        return bytes_transferred / total_ns

    @property
    def efficiency(self) -> float:
        """Calculate system efficiency (busy cycles / total cycles)"""
        if self.total_cycles == 0:
            return 0.0
        return self.busy_cycles / self.total_cycles

    @property
    def bandwidth_efficiency(self) -> float:
        """Calculate bandwidth efficiency (actual bandwidth / theoretical peak)"""
        peak_bandwidth = self._peak_bandwidth if self._peak_bandwidth > 0 else 1638.4
        actual = self.throughput_gbps
        return actual / peak_bandwidth if peak_bandwidth > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary"""
        return {
            'total_cycles': self.total_cycles,
            'total_requests': self.total_requests,
            'completed_requests': self.completed_requests,
            'read_requests': self.read_requests,
            'write_requests': self.write_requests,
            'row_hits': self.row_hits,
            'row_misses': self.row_misses,
            'row_conflicts': self.row_conflicts,
            'row_hit_rate': self.row_hit_rate,
            'avg_latency': self.avg_latency,
            'max_latency': self.max_latency_cycles,
            'min_latency': self.min_latency_cycles,
            'throughput_gbps': self.throughput_gbps,
            'efficiency': self.efficiency,
            'bandwidth_efficiency': self.bandwidth_efficiency,
            'refresh_count': self.refresh_count,
            'total_dram_activations': self.total_dram_activations,
            'per_channel_stats': {
                ch: {
                    'requests': s.total_requests,
                    'hit_rate': s.hit_rate,
                    'avg_latency': s.avg_latency,
                }
                for ch, s in self.per_channel_stats.items()
            }
        }


class TrafficGenerator:
    """Traffic Generator - Optimized"""

    __slots__ = ('config', 'current_addr', 'hot_bank', '_random')

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.current_addr = 0
        self.hot_bank = 0
        self._random = random.Random(config.seed)

    def generate(self) -> List[HBMRequest]:
        """Generate request batch"""
        requests = []

        # Determine if request should be generated based on request rate
        if self._random.random() > self.config.request_rate:
            return requests

        # Generate address based on pattern
        if self.config.traffic_pattern == TrafficPattern.RANDOM:
            addr = self._random.randint(0, self.config.address_range - 1)
        elif self.config.traffic_pattern == TrafficPattern.SEQUENTIAL:
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.burst_size) % self.config.address_range
        elif self.config.traffic_pattern == TrafficPattern.STRIDE:
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.stride_value) % self.config.address_range
        elif self.config.traffic_pattern == TrafficPattern.HOT_SPOT:
            if self._random.random() < 0.8:  # 80% access hot spot
                addr = self._random.randint(0, self.config.address_range // 10)
            else:
                addr = self._random.randint(0, self.config.address_range - 1)
        else:  # ADDR_SCATTER
            addr = self._random.randint(0, self.config.address_range - 1)

        # Align address
        addr = addr & ~0x3F  # 64-byte alignment

        # Generate read or write request
        is_read = self._random.random() < self.config.read_ratio
        req = HBMRequest(addr=addr, length=self.config.burst_size, is_read=is_read)
        requests.append(req)

        return requests

    def generate_batch(self, batch_size: int) -> List[HBMRequest]:
        """Generate batch of requests efficiently

        Args:
            batch_size: Number of requests to generate

        Returns:
            List of generated requests
        """
        return [self._generate_single() for _ in range(batch_size)]

    def _generate_single(self) -> HBMRequest:
        """Generate single request"""
        if self.config.traffic_pattern == TrafficPattern.RANDOM:
            addr = self._random.randint(0, self.config.address_range - 1)
        elif self.config.traffic_pattern == TrafficPattern.SEQUENTIAL:
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.burst_size) % self.config.address_range
        elif self.config.traffic_pattern == TrafficPattern.STRIDE:
            addr = self.current_addr
            self.current_addr = (self.current_addr + self.config.stride_value) % self.config.address_range
        elif self.config.traffic_pattern == TrafficPattern.HOT_SPOT:
            if self._random.random() < 0.8:
                addr = self._random.randint(0, self.config.address_range // 10)
            else:
                addr = self._random.randint(0, self.config.address_range - 1)
        else:
            addr = self._random.randint(0, self.config.address_range - 1)

        addr = addr & ~0x3F
        is_read = self._random.random() < self.config.read_ratio
        return HBMRequest(addr=addr, length=self.config.burst_size, is_read=is_read)


class HBMSimulator:
    """HBM Simulator - Optimized Version

    Integrated pipeline:
    1. TrafficGenerator -> generates requests
    2. HBMController -> schedules requests (FR-FCFS/QoS)
    3. CommandSequencer -> generates DRAM command sequences
    4. CommandPipeline -> executes commands with timing
    5. DRAMModel -> full DRAM timing model

    Multi-channel support (8-channel HBM3):
    - ChannelSelector: proper channel selection strategies
    - MultiChannelStats: per-channel statistics tracking
    - Address-based channel selection per JEDEC HBM3 spec

    Cycle-accurate simulation:
    - Each step() advances exactly one cycle
    - All timing parameters in cycles (based on HBM3 tCK = 781.25ps)
    - Command pipeline modeled with proper DRAM timing constraints

    Optimizations:
    - __slots__ for memory reduction
    - Request object pooling
    - Batch processing
    - Pre-computed timing values
    """

    __slots__ = (
        'config', 'tCK_ps', 'tCK_ns', 'dram', 'controller', 'sequencer',
        'pipeline', 'channel_selector', 'traffic_gen', 'multi_channel_stats',
        'stats', 'current_cycle', 'max_cycles', '_bank_states',
        '_active_sequences', '_last_completion_cycle', '_completion_gaps',
        'timing', '_last_cmd_type', '_request_pool', '_batch_size',
        '_pending_batch'
    )

    def __init__(self, sim_config: SimulationConfig):
        self.config = sim_config

        # Clock period (cycles to ns conversion)
        self.tCK_ps = 781.25  # HBM3 tCK
        self.tCK_ns = self.tCK_ps / 1000.0

        # Get number of channels from config
        num_channels = sim_config.hbm_config.channels_per_stack
        total_channels = sim_config.hbm_config.stack_count * num_channels

        # Create DRAM model
        self.dram = DRAMModel(
            hbm_version="hbm3",
            stack_count=sim_config.hbm_config.stack_count,
            banks_per_channel=sim_config.hbm_config.banks_per_pseudo_channel
        )

        # Create controller
        self.controller = HBMController(sim_config.hbm_config)

        # Create command sequence generator
        self.sequencer = CommandSequencer()

        # Create command pipeline
        self.pipeline = CommandPipeline()

        # Create multi-channel support components
        self.channel_selector = ChannelSelector(
            num_channels=num_channels,
            strategy=ChannelSelector.ADDR_BASED
        )

        # Create multi-channel traffic generator
        self.traffic_gen = MultiChannelTrafficGenerator(
            config=sim_config,
            num_channels=num_channels,
            channel_selector=self.channel_selector
        )

        # Create multi-channel statistics
        self.multi_channel_stats = MultiChannelStats(num_channels=total_channels)

        # Statistics
        self.stats = SimulationStats()
        self.stats.per_channel_stats = {
            i: ChannelStats(channel_id=i) for i in range(total_channels)
        }
        # Set peak bandwidth for efficiency calculation
        self.stats._peak_bandwidth = sim_config.hbm_config.calc_bandwidth_total()

        # Simulation state
        self.current_cycle = 0
        self.max_cycles = int(sim_config.simulation_time_us * 1e-6 * sim_config.clock_freq_hz)

        # Bank state mapping (simplified, for sequence generation)
        self._bank_states: Dict[Tuple[int, int, int], SeqBankState] = {}

        # Active command sequences
        self._active_sequences: Dict[int, CommandSequence] = {}

        # Cycle-accurate tracking
        self._last_completion_cycle = 0
        self._completion_gaps: List[int] = []  # Gap between completions

        # Timing parameters
        self.timing = get_timing_for_hbm_version("hbm3")

        # Enable DRAM memory model so read/write data is stored
        self.dram.enable_memory_model()

        # Track last command type for turnaround calculation
        self._last_cmd_type: str = "READ"

        # Request object pool for reduced allocation overhead
        self._request_pool = HBMRequestPool(max_size=1024)

        # Batch processing configuration
        self._batch_size = 32  # Process up to 32 requests per cycle
        self._pending_batch: Optional[RequestBatch] = None

        logger.info(f"Simulator initialized: {sim_config.simulation_time_us}us = {self.max_cycles} cycles")
        logger.info(f"  Controller: {type(self.controller).__name__}")
        logger.info(f"  Sequencer: {type(self.sequencer).__name__}")
        logger.info(f"  Pipeline: {type(self.pipeline).__name__}")
        logger.info(f"  DRAM: {type(self.dram).__name__}")
        logger.info(f"  Channels: {total_channels} total ({num_channels} per stack)")
        logger.info(f"  ChannelSelector: {self.channel_selector.strategy}")

    def _get_bank_state(self, request: HBMRequest) -> SeqBankState:
        """Get bank state for request

        Args:
            request: HBM request

        Returns:
            BankState for the request's bank
        """
        bank_key = (request.channel_id, request.pseudo_channel_id, request.bank_id)

        if bank_key not in self._bank_states:
            self._bank_states[bank_key] = SeqBankState(
                bank_id=request.bank_id,
                state=BankStateEnum.IDLE,
                open_row=-1
            )

        return self._bank_states[bank_key]

    def _update_bank_state(self, request: HBMRequest, is_row_hit: bool):
        """Update bank state

        Args:
            request: Completed request
            is_row_hit: Whether it was a row hit
        """
        bank_key = (request.channel_id, request.pseudo_channel_id, request.bank_id)

        if bank_key not in self._bank_states:
            self._bank_states[bank_key] = SeqBankState(
                bank_id=request.bank_id,
                state=BankStateEnum.ACTIVE,
                open_row=request.row_id
            )
        else:
            state = self._bank_states[bank_key]
            if is_row_hit:
                # Row hit: keep row open
                state.state = BankStateEnum.ACTIVE
                state.open_row = request.row_id
            else:
                # Row miss: row now open
                state.state = BankStateEnum.ACTIVE
                state.open_row = request.row_id

    def _generate_command_sequence(self, request: HBMRequest) -> CommandSequence:
        """Generate DRAM command sequence for a request

        Args:
            request: HBM request to generate commands for

        Returns:
            CommandSequence with all commands and timing
        """
        bank_state = self._get_bank_state(request)
        return self.sequencer.generate_command_sequence(
            request, bank_state, self.current_cycle
        )

    def _execute_command_sequence(self, sequence: CommandSequence) -> float:
        """Execute a command sequence on the DRAM model

        Args:
            sequence: Command sequence to execute

        Returns:
            Actual latency in cycles
        """
        start_cycle = self.current_cycle

        for cmd in sequence.commands:
            if cmd.command == DRAMCommand.ACT:
                # Execute activate on DRAM
                resp = self.dram.execute_activate(
                    stack_id=sequence.request.stack_id,
                    channel_id=sequence.request.channel_id,
                    bank_id=sequence.request.bank_id,
                    row_id=cmd.row_id,
                    current_time=int(cmd.cycle)
                )
                if resp.success:
                    self.stats.total_dram_activations += 1
            elif cmd.command == DRAMCommand.RD:
                # Execute read on DRAM
                resp = self.dram.execute_read(
                    stack_id=sequence.request.stack_id,
                    channel_id=sequence.request.channel_id,
                    bank_id=sequence.request.bank_id,
                    col_id=cmd.col_id,
                    current_time=int(cmd.cycle),
                    length=sequence.request.length
                )
                if resp.success:
                    self.stats.total_dram_reads += 1
            elif cmd.command == DRAMCommand.WR:
                # Execute write on DRAM
                write_data = sequence.request.get_write_data()
                if write_data is None:
                    write_data = bytes(sequence.request.length)
                resp = self.dram.execute_write(
                    stack_id=sequence.request.stack_id,
                    channel_id=sequence.request.channel_id,
                    bank_id=sequence.request.bank_id,
                    col_id=cmd.col_id,
                    data=write_data,
                    current_time=int(cmd.cycle)
                )
                if resp.success:
                    self.stats.total_dram_writes += 1
            elif cmd.command == DRAMCommand.PRE:
                # Execute precharge on DRAM
                resp = self.dram.execute_precharge(
                    stack_id=sequence.request.stack_id,
                    channel_id=sequence.request.channel_id,
                    bank_id=sequence.request.bank_id,
                    current_time=int(cmd.cycle)
                )

        # Calculate actual latency
        end_cycle = sequence.end_cycle
        return end_cycle - start_cycle

    def _process_pending_sequences(self) -> List[HBMResponse]:
        """Process completed command sequences

        Returns:
            List of HBMResponse for completed requests
        """
        responses = []
        completed_ids = []

        for req_id, sequence in self._active_sequences.items():
            if self.current_cycle >= sequence.end_cycle:
                # Sequence completed
                completed_ids.append(req_id)

                # Calculate latency
                latency_cycles = sequence.total_cycles
                latency_ns = latency_cycles * self.tCK_ns

                # Read data from DRAM if this was a read request
                read_data = None
                if sequence.request.is_read:
                    read_data = self.dram.read(
                        stack_id=sequence.request.stack_id,
                        channel_id=sequence.request.channel_id,
                        bank_id=sequence.request.bank_id,
                        row_id=sequence.request.row_id,
                        col_id=sequence.request.col_id,
                        length=sequence.request.length,
                    )

                # Create response
                response = HBMResponse(
                    request_id=req_id,
                    status="OK",
                    latency=latency_ns,
                    channel_id=sequence.request.channel_id,
                    bank_id=sequence.request.bank_id,
                    data=read_data,
                )
                responses.append(response)

                # Update bank state
                self._update_bank_state(sequence.request, sequence.is_row_hit)

                # Update stats
                self.stats.completed_requests += 1
                self.stats.total_latency_cycles += latency_cycles

                # Track max/min latency
                if latency_cycles > self.stats.max_latency_cycles:
                    self.stats.max_latency_cycles = latency_cycles
                if self.stats.min_latency_cycles == 0 or latency_cycles < self.stats.min_latency_cycles:
                    self.stats.min_latency_cycles = latency_cycles

                # Update per-channel stats
                ch_id = sequence.request.channel_id
                if ch_id in self.stats.per_channel_stats:
                    ch_stats = self.stats.per_channel_stats[ch_id]
                    ch_stats.total_requests += 1
                    ch_stats.total_latency_cycles += latency_cycles
                    if sequence.is_row_hit:
                        ch_stats.row_hits += 1
                    else:
                        ch_stats.row_misses += 1

                # Release channel (for load balancing)
                self.channel_selector.release_channel(ch_id)

        # Remove completed sequences
        for req_id in completed_ids:
            del self._active_sequences[req_id]

        return responses

    def step(self) -> Optional[HBMResponse]:
        """Execute one cycle

        Pipeline flow:
        1. Generate new requests from traffic generator (with multi-channel support)
        2. Submit requests to controller
        3. Controller schedules one request per cycle
        4. CommandSequencer generates DRAM command sequence
        5. CommandPipeline tracks pending commands
        6. Process completed sequences
        7. Return response with actual latency

        Returns:
            HBMResponse if a request completed this cycle
        """
        self.current_cycle += 1

        # Update pipeline cycle
        self.pipeline.set_cycle(self.current_cycle)

        # 1. Generate new requests from traffic generator (multi-channel aware)
        new_requests = self.traffic_gen.generate()
        for req in new_requests:
            self.controller.submit_request(req)
            self.stats.total_requests += 1
            if req.is_read:
                self.stats.read_requests += 1
            else:
                self.stats.write_requests += 1

            # Update per-channel stats
            ch_id = req.channel_id
            if ch_id in self.stats.per_channel_stats:
                self.stats.per_channel_stats[ch_id].total_requests += 1

        # 2. Controller tick - schedules ONE request per cycle
        scheduled_request, response = self.controller.tick()

        if scheduled_request:
            # Update last command type for turnaround tracking
            self._last_cmd_type = "READ" if scheduled_request.is_read else "WRITE"

            # 3. Generate command sequence using CommandSequencer
            sequence = self._generate_command_sequence(scheduled_request)

            # 4. Execute on DRAM with proper timing
            actual_latency = self._execute_command_sequence(sequence)

            # 5. Track active sequence for completion
            self._active_sequences[scheduled_request.request_id] = sequence

            # Mark cycle as busy
            self.stats.busy_cycles += 1

        # 6. Process completed sequences
        responses = self._process_pending_sequences()

        # 7. Track completion gap for jitter analysis
        if responses:
            if self._last_completion_cycle > 0:
                gap = self.current_cycle - self._last_completion_cycle
                self._completion_gaps.append(gap)
            self._last_completion_cycle = self.current_cycle

        # Return first response if any completed this cycle
        if responses:
            return responses[0]

        # Check if there are pending requests (not idle if pending)
        if self.stats.total_requests > self.stats.completed_requests + len(self._active_sequences):
            # Pending requests exist, this is a stall cycle
            pass
        else:
            self.stats.idle_cycles += 1

        # 8. Update DRAM stats
        dram_stats = self.dram.stats
        self.stats.row_hits = dram_stats.row_hits
        self.stats.row_misses = dram_stats.row_misses
        self.stats.row_conflicts = dram_stats.row_conflicts
        self.stats.refresh_count = dram_stats.total_refreshes

        return None

    def get_completion_jitter(self) -> Dict[str, float]:
        """Get completion jitter statistics

        Returns:
            Dict with jitter metrics (std, mean, max)
        """
        if len(self._completion_gaps) < 2:
            return {'mean': 0.0, 'std': 0.0, 'max': 0}

        import statistics
        return {
            'mean': statistics.mean(self._completion_gaps),
            'std': statistics.stdev(self._completion_gaps) if len(self._completion_gaps) > 1 else 0.0,
            'max': max(self._completion_gaps),
            'count': len(self._completion_gaps),
        }

    def get_channel_stats(self) -> Dict[int, ChannelStats]:
        """Get per-channel statistics

        Returns:
            Dict mapping channel_id to ChannelStats
        """
        return self.stats.per_channel_stats

    def get_load_balance_score(self) -> float:
        """Calculate load balance score (0-1, 1=perfect balance)

        Returns:
            Load balance score
        """
        requests = [s.total_requests for s in self.stats.per_channel_stats.values()]
        if sum(requests) == 0:
            return 1.0

        avg = sum(requests) / len(requests)
        if avg == 0:
            return 1.0

        # Calculate coefficient of variation
        variance = sum((x - avg) ** 2 for x in requests) / len(requests)
        cv = (variance ** 0.5) / avg

        # Convert to 0-1 score (lower CV = better balance)
        return max(0.0, 1.0 - min(1.0, cv))

    def run(self) -> SimulationStats:
        """Run simulation"""
        logger.info(f"Starting simulation: {self.max_cycles} cycles")
        start_time = time.time()

        completed_prev = 0

        while self.current_cycle < self.max_cycles:
            response = self.step()

            # Periodically print progress
            if self.current_cycle % (self.max_cycles // 10) == 0:
                elapsed = time.time() - start_time
                rate = (self.stats.completed_requests - completed_prev) / max(elapsed, 0.001)
                logger.info(f"  Cycle {self.current_cycle}/{self.max_cycles}: "
                           f"{self.stats.completed_requests} completed, {rate:.0f} req/s")
                completed_prev = self.stats.completed_requests

        self.stats.total_cycles = self.current_cycle

        elapsed = time.time() - start_time
        logger.info(f"Simulation completed in {elapsed:.2f}s")
        logger.info(f"  Efficiency: {self.stats.efficiency:.2%}, "
                   f"Bandwidth eff: {self.stats.bandwidth_efficiency:.2%}")

        return self.stats

    def run_verbose(self) -> SimulationStats:
        """Run simulation with detailed statistics output"""
        stats = self.run()

        print(f"\n{'='*60}")
        print(f"Cycle-Accurate Simulation Results")
        print(f"{'='*60}")
        print(f"  Total cycles: {stats.total_cycles}")
        print(f"  Total requests: {stats.total_requests}")
        print(f"  Completed: {stats.completed_requests}")
        print(f"  Read/Write: {stats.read_requests}/{stats.write_requests}")
        print(f"  Row hit rate: {stats.row_hit_rate:.2%}")
        print(f"  Latency (avg/max/min): {stats.avg_latency:.1f}/{stats.max_latency_cycles}/{stats.min_latency_cycles} cycles")
        print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")
        print(f"  Efficiency: {stats.efficiency:.2%}")
        print(f"  Bandwidth efficiency: {stats.bandwidth_efficiency:.2%}")
        print(f"  DRAM activations: {stats.total_dram_activations}")
        print(f"  Refresh count: {stats.refresh_count}")
        print(f"  Idle cycles: {stats.idle_cycles}")

        # Jitter analysis
        jitter = self.get_completion_jitter()
        if jitter['count'] > 0:
            print(f"  Completion jitter: mean={jitter['mean']:.2f}, std={jitter['std']:.2f}, max={jitter['max']}")

        print(f"{'='*60}")

        return stats

    def get_stats(self) -> SimulationStats:
        """Get statistics"""
        self.stats.total_cycles = self.current_cycle
        self.stats.row_hits = self.dram.stats.row_hits
        self.stats.row_misses = self.dram.stats.row_misses
        self.stats.row_conflicts = self.dram.stats.row_conflicts
        return self.stats

    def get_pool_stats(self) -> Dict[str, int]:
        """Get request pool statistics"""
        return {
            'pool_size': self._request_pool.pool_size,
            'total_allocated': self._request_pool.total_allocated,
        }


def run_simulation(config: SimulationConfig = None) -> SimulationStats:
    """Run simulation shortcut function"""
    if config is None:
        config = SimulationConfig()

    sim = HBMSimulator(config)
    return sim.run()


if __name__ == "__main__":
    print("=" * 60)
    print("HBM System Simulation - Optimized")
    print("=" * 60)

    # Basic simulation
    print("\n--- Basic Simulation (100us Random Traffic) ---")
    config = SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.RANDOM,
        request_rate=0.3,
        read_ratio=0.7,
    )
    stats = run_simulation(config)

    print(f"\nResults:")
    print(f"  Total cycles: {stats.total_cycles}")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Completed: {stats.completed_requests}")
    print(f"  Read/Write: {stats.read_requests}/{stats.write_requests}")
    print(f"  Row hit rate: {stats.row_hit_rate:.2%}")
    print(f"  Avg latency: {stats.avg_latency:.1f} cycles")
    print(f"  Throughput: {stats.throughput_gbps:.2f} GB/s")

    # Sequential traffic test
    print("\n--- Sequential Traffic ---")
    config_seq = SimulationConfig(
        simulation_time_us=100.0,
        traffic_pattern=TrafficPattern.SEQUENTIAL,
        request_rate=0.5,
        read_ratio=1.0,
    )
    stats_seq = run_simulation(config_seq)
    print(f"  Row hit rate: {stats_seq.row_hit_rate:.2%}")
    print(f"  Throughput: {stats_seq.throughput_gbps:.2f} GB/s")

    print("\n" + "=" * 60)
    print("Simulation complete!")