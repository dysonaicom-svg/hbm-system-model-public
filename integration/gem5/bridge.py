"""
Python-gem5 Bridge Module
Provides bidirectional communication between Python HBM model and gem5 simulator

Features:
- gem5 to Python: Pass memory requests from gem5 to Python HBM model
- Python to gem5: Return responses from Python model to gem5
- Timing synchronization: Align simulation cycles between gem5 and Python
- Statistics exchange: Share performance metrics between simulators

Usage:
    1. Initialize bridge with gem5 system and Python model
    2. Register callbacks for request/response handling
    3. Call sync() periodically to exchange data
"""

import threading
import queue
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Memory request types"""
    READ = 0
    WRITE = 1
    READ_RESPONSE = 2
    WRITE_RESPONSE = 3
    REFRESH = 4


@dataclass
class MemoryRequest:
    """Memory request structure for bridge"""
    request_id: int
    request_type: RequestType
    addr: int
    length: int  # bytes
    data: Optional[bytes] = None
    qos: int = 8  # 0-15 QoS priority
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return (f"MemoryRequest(id={self.request_id}, type={self.request_type.name}, "
                f"addr=0x{self.addr:08x}, len={self.length})")


@dataclass
class MemoryResponse:
    """Memory response structure for bridge"""
    request_id: int
    status: str  # "OK", "ERROR", "TIMEOUT"
    latency: float  # nanoseconds
    data: Optional[bytes] = None
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BridgeConfig:
    """Configuration for Python-gem5 bridge"""
    # Simulation parameters
    sync_interval_cycles: int = 100  # Sync every N cycles
    request_queue_size: int = 1024    # Max pending requests
    response_timeout_ns: float = 1e6  # 1ms timeout

    # Performance parameters
    enable_batching: bool = True
    batch_size: int = 32
    enable_compression: bool = False

    # Debugging
    enable_logging: bool = False
    log_file: Optional[str] = None


class HBMBridge:
    """
    Python-gem5 Bridge for HBM simulation

    This bridge enables co-simulation between gem5 and the Python HBM model:
    - gem5 generates memory requests
    - Python HBM model processes them with accurate timing
    - Results are returned to gem5 for further simulation

    Synchronization:
    - Bridge syncs with gem5 every N cycles
    - Pending requests are batched for efficiency
    - Responses are matched by request_id
    """

    def __init__(self, config: Optional[BridgeConfig] = None):
        """Initialize bridge

        Args:
            config: Bridge configuration
        """
        self.config = config or BridgeConfig()
        self.enabled = False

        # Request/response queues
        self._request_queue: queue.Queue = queue.Queue(maxsize=self.config.request_queue_size)
        self._response_queue: queue.Queue = queue.Queue(maxsize=self.config.request_queue_size)

        # Pending requests tracking
        self._pending_requests: Dict[int, MemoryRequest] = {}
        self._pending_lock = threading.Lock()

        # Statistics
        self._stats = {
            'total_requests': 0,
            'total_responses': 0,
            'total_syncs': 0,
            'request_queue_full': 0,
            'response_timeouts': 0,
        }

        # Callbacks
        self._on_request_callback: Optional[Callable] = None
        self._on_response_callback: Optional[Callable] = None
        self._on_sync_callback: Optional[Callable] = None

        # Synchronization state
        self._current_cycle: int = 0
        self._last_sync_cycle: int = 0
        self._sync_thread: Optional[threading.Thread] = None
        self._running: bool = False

        # External model reference
        self._external_model = None

        logger.info(f"Bridge initialized with config: sync_interval={self.config.sync_interval_cycles}")

    def set_external_model(self, model):
        """Set external Python HBM model for co-simulation

        Args:
            model: Python HBM model instance
        """
        self._external_model = model
        logger.info(f"External model set: {type(model).__name__}")

    def set_request_callback(self, callback: Callable[[MemoryRequest], None]):
        """Set callback for incoming requests

        Args:
            callback: Function to call with MemoryRequest
        """
        self._on_request_callback = callback

    def set_response_callback(self, callback: Callable[[MemoryResponse], None]):
        """Set callback for outgoing responses

        Args:
            callback: Function to call with MemoryResponse
        """
        self._on_response_callback = callback

    def set_sync_callback(self, callback: Callable[[int], None]):
        """Set callback for synchronization events

        Args:
            callback: Function to call with current cycle
        """
        self._on_sync_callback = callback

    def enable(self):
        """Enable bridge"""
        self.enabled = True
        logger.info("Bridge enabled")

    def disable(self):
        """Disable bridge"""
        self.enabled = False
        logger.info("Bridge disabled")

    def submit_request(self, request: MemoryRequest) -> bool:
        """Submit request to bridge

        Args:
            request: Memory request to submit

        Returns:
            True if request was queued successfully
        """
        if not self.enabled:
            return False

        try:
            self._request_queue.put_nowait(request)
            with self._pending_lock:
                self._pending_requests[request.request_id] = request
            self._stats['total_requests'] += 1

            if self.config.enable_logging:
                logger.debug(f"Request submitted: {request}")

            # Call callback if registered
            if self._on_request_callback:
                self._on_request_callback(request)

            return True
        except queue.Full:
            self._stats['request_queue_full'] += 1
            logger.warning(f"Request queue full, dropping request {request.request_id}")
            return False

    def submit_response(self, response: MemoryResponse) -> bool:
        """Submit response from Python model

        Args:
            response: Memory response to submit

        Returns:
            True if response was queued successfully
        """
        try:
            self._response_queue.put_nowait(response)
            self._stats['total_responses'] += 1

            if self.config.enable_logging:
                logger.debug(f"Response submitted: {response}")

            # Call callback if registered
            if self._on_response_callback:
                self._on_response_callback(response)

            return True
        except queue.Full:
            logger.warning(f"Response queue full, dropping response {response.request_id}")
            return False

    def get_pending_requests(self) -> List[MemoryRequest]:
        """Get list of pending requests

        Returns:
            List of pending MemoryRequest objects
        """
        with self._pending_lock:
            return list(self._pending_requests.values())

    def get_request_count(self) -> int:
        """Get number of pending requests"""
        with self._pending_lock:
            return len(self._pending_requests)

    def complete_request(self, request_id: int, response: MemoryResponse):
        """Mark request as completed

        Args:
            request_id: ID of completed request
            response: Response data
        """
        with self._pending_lock:
            if request_id in self._pending_requests:
                del self._pending_requests[request_id]

        self.submit_response(response)

    def sync(self, current_cycle: int) -> Dict[str, Any]:
        """
        Synchronize with gem5 at given cycle

        This should be called periodically from the gem5 simulation loop.
        It exchanges pending requests/responses and returns sync status.

        Args:
            current_cycle: Current simulation cycle in gem5

        Returns:
            Dict with sync status and statistics
        """
        if not self.enabled:
            return {'status': 'disabled', 'current_cycle': current_cycle}

        self._current_cycle = current_cycle

        # Check if sync is needed
        cycles_since_sync = current_cycle - self._last_sync_cycle
        sync_due = cycles_since_sync >= self.config.sync_interval_cycles

        sync_result = {
            'status': 'ok',
            'current_cycle': current_cycle,
            'cycles_since_sync': cycles_since_sync,
            'pending_requests': self.get_request_count(),
            'pending_responses': self._response_queue.qsize(),
        }

        if sync_due:
            self._last_sync_cycle = current_cycle
            self._stats['total_syncs'] += 1

            # Process pending requests through external model
            if self._external_model:
                self._process_pending_requests()

            # Call sync callback if registered
            if self._on_sync_callback:
                self._on_sync_callback(current_cycle)

            sync_result['synced'] = True

        return sync_result

    def _process_pending_requests(self):
        """Process pending requests through external model"""
        if not self._external_model:
            return

        requests_to_process = []

        # Collect requests from queue
        while not self._request_queue.empty():
            try:
                request = self._request_queue.get_nowait()
                requests_to_process.append(request)
            except queue.Empty:
                break

        # Process in batch
        for request in requests_to_process:
            if request.request_type in (RequestType.READ, RequestType.WRITE):
                # Process through external model
                response = self._process_request(request)

                if response:
                    self.complete_request(request.request_id, response)
            else:
                # Refresh or other - handle directly
                pass

    def _process_request(self, request: MemoryRequest) -> Optional[MemoryResponse]:
        """Process single request through external model

        Args:
            request: Request to process

        Returns:
            Response from model, or None if failed
        """
        if not self._external_model:
            return None

        try:
            # Convert to model-specific format
            from model.controller.request import HBMRequest, HBMResponse

            # Create model request
            model_req = HBMRequest(
                addr=request.addr,
                length=request.length,
                is_read=(request.request_type == RequestType.READ),
                qos=request.qos,
            )

            # Submit to model
            success = self._external_model.submit_request(model_req)
            if not success:
                return MemoryResponse(
                    request_id=request.request_id,
                    status="ERROR",
                    latency=0.0,
                    metadata={'error': 'submit_failed'},
                )

            # Process model (one tick)
            scheduled, model_resp = self._external_model.tick()

            if model_resp:
                return MemoryResponse(
                    request_id=request.request_id,
                    status=model_resp.status,
                    latency=model_resp.latency,
                    data=model_resp.data,
                    metadata={},
                )
            else:
                # Request pending
                return None

        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {e}")
            return MemoryResponse(
                request_id=request.request_id,
                status="ERROR",
                latency=0.0,
                metadata={'error': str(e)},
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics

        Returns:
            Dict with statistics
        """
        stats = self._stats.copy()
        stats['pending_requests'] = len(self._pending_requests)
        stats['pending_responses'] = self._response_queue.qsize()
        stats['request_queue_size'] = self._request_queue.qsize()
        return stats

    def reset_stats(self):
        """Reset statistics counters"""
        for key in self._stats:
            self._stats[key] = 0

    def start_background_sync(self, interval_ms: float = 1.0):
        """Start background synchronization thread

        Args:
            interval_ms: Sync interval in milliseconds
        """
        if self._running:
            return

        self._running = True
        self._sync_thread = threading.Thread(
            target=self._background_sync_loop,
            args=(interval_ms,),
            daemon=True
        )
        self._sync_thread.start()
        logger.info(f"Background sync started (interval={interval_ms}ms)")

    def stop_background_sync(self):
        """Stop background synchronization thread"""
        self._running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=1.0)
            self._sync_thread = None
        logger.info("Background sync stopped")

    def _background_sync_loop(self, interval_ms: float):
        """Background sync loop

        Args:
            interval_ms: Sync interval in milliseconds
        """
        interval_s = interval_ms / 1000.0

        while self._running:
            try:
                self.sync(self._current_cycle + 1)
                time.sleep(interval_s)
            except Exception as e:
                logger.error(f"Background sync error: {e}")


class DualSimulatorBridge:
    """
    Bridge for dual simulator mode: gem5 + Python HBM in parallel

    This enables:
    - Simultaneous simulation in both simulators
    - Request forwarding between simulators
    - Result comparison for validation
    """

    def __init__(self, gem5_system=None, python_model=None):
        """Initialize dual bridge

        Args:
            gem5_system: gem5 system object
            python_model: Python HBM model instance
        """
        self.gem5_system = gem5_system
        self.python_model = python_model

        # Create internal bridges
        self.gem5_to_python = HBMBridge()
        self.python_to_gem5 = HBMBridge()

        # Link them
        self.gem5_to_python.set_external_model(python_model)

        # Statistics for comparison
        self._comparison_stats = {
            'gem5_requests': 0,
            'python_requests': 0,
            'mismatches': 0,
            'avg_latency_diff_ns': 0.0,
        }

        logger.info("DualSimulatorBridge initialized")

    def set_gem5_system(self, gem5_system):
        """Set gem5 system reference"""
        self.gem5_system = gem5_system

    def set_python_model(self, python_model):
        """Set Python HBM model reference"""
        self.python_model = python_model
        self.gem5_to_python.set_external_model(python_model)

    def sync_all(self, current_cycle: int) -> Dict[str, Any]:
        """Synchronize both simulators

        Args:
            current_cycle: Current simulation cycle

        Returns:
            Dict with sync status for both bridges
        """
        gem5_status = self.gem5_to_python.sync(current_cycle)
        python_status = self.python_to_gem5.sync(current_cycle)

        return {
            'gem5_to_python': gem5_status,
            'python_to_gem5': python_status,
            'current_cycle': current_cycle,
        }

    def compare_results(self, gem5_result: MemoryResponse,
                       python_result: MemoryResponse) -> Dict[str, Any]:
        """Compare results from both simulators

        Args:
            gem5_result: Result from gem5
            python_result: Result from Python model

        Returns:
            Dict with comparison results
        """
        comparison = {
            'request_id': gem5_result.request_id,
            'latency_match': abs(gem5_result.latency - python_result.latency) < 1.0,  # 1ns tolerance
            'gem5_latency_ns': gem5_result.latency,
            'python_latency_ns': python_result.latency,
            'latency_diff_ns': abs(gem5_result.latency - python_result.latency),
            'status_match': gem5_result.status == python_result.status,
            'data_match': gem5_result.data == python_result.data if gem5_result.data and python_result.data else True,
        }

        # Update stats
        self._comparison_stats['gem5_requests'] += 1
        self._comparison_stats['python_requests'] += 1

        if not comparison['latency_match'] or not comparison['status_match']:
            self._comparison_stats['mismatches'] += 1

        # Update average latency diff
        total = self._comparison_stats['gem5_requests']
        current_avg = self._comparison_stats['avg_latency_diff_ns']
        self._comparison_stats['avg_latency_diff_ns'] = (
            (current_avg * (total - 1) + comparison['latency_diff_ns']) / total
        )

        return comparison

    def get_comparison_stats(self) -> Dict[str, Any]:
        """Get comparison statistics

        Returns:
            Dict with comparison stats
        """
        return self._comparison_stats.copy()


def create_bridge(mode: str = 'single', config: Optional[BridgeConfig] = None) -> HBMBridge:
    """Factory function to create bridge

    Args:
        mode: 'single' or 'dual'
        config: Bridge configuration

    Returns:
        Bridge instance
    """
    if mode == 'single':
        return HBMBridge(config)
    elif mode == 'dual':
        return DualSimulatorBridge()
    else:
        raise ValueError(f"Unknown mode: {mode}")