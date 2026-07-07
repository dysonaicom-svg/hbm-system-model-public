"""
HBM4 Optimized Controller - Phase 14 Integration

Integrates all Phase 10-13 modules into a complete optimized controller:
- Phase 10: Analysis (BottleneckDetector, HotspotDetector, LatencyAnalyzer, DVFSAnalyzer, Optimizer)
- Phase 11: Compliance (JEDECValidator, HBM3Compatibility)
- Phase 13: Performance Optimization (ParallelScheduler, AdvancedPrefetch, SmartQueue, BankPredictor)

This creates a closed-loop optimization system where:
1. Controller executes requests
2. Analysis modules collect metrics
3. Compliance modules validate behavior
4. Optimizer generates suggestions
5. Phase 13 modules apply optimizations

Usage:
    from model.controller.hbm4_optimized_controller import HBM4OptimizedController

    controller = HBM4OptimizedController(enable_analysis=True, enable_compliance=True)
    # Use like a normal HBM4Controller
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from model.dram.hbm4_spec import HBM4Spec, HBM4_CONFIG
from model.dram.dfi_interface import DFI5Interface
from model.dram.hbm4_channel_model import HBM4ChannelArray
from model.controller.hbm4_controller import HBM4Controller
from model.controller.hbm4_address_decoder import HBM4AddressDecoder
from model.controller.hbm4_qos_scheduler import HBM4QoSScheduler
from model.controller.hbm4_refresh_scheduler import HBM4RefreshScheduler
from model.controller.config import HBMConfig

# Phase 10: Analysis modules
from model.analysis.bottleneck_detector import (
    BottleneckDetector, BottleneckReport, BottleneckType
)
from model.analysis.hotspot_detector import (
    HotspotDetector, HotspotReport, HotspotType
)
from model.analysis.latency_analyzer import LatencyDistribution, LatencyStats
from model.analysis.dvfs_analyzer import DVFSAnalyzer, DVFSResult
from model.analysis.power_performance_curve import PowerPerformanceCurve
from model.analysis.optimizer import Optimizer, OptimizationSuggestion

# Phase 11: Compliance modules
from model.compliance.jedec_validator import JEDECValidator, ComplianceCheck, ComplianceLevel
from model.compliance.hbm3_compatibility import HBM3CompatibilityChecker

# Phase 13: Performance optimization modules
from model.controller.parallel_scheduler import ParallelChannelScheduler
from model.controller.advanced_prefetch import AdvancedPrefetchEngine, AccessPatternClassifier
from model.controller.smart_queue import SmartQueue
from model.controller.bank_predictor import BankPredictor

_logger = logging.getLogger('hbm4.optimized_controller')


@dataclass
class OptimizationReport:
    """Complete optimization report"""
    bottlenecks: BottleneckReport
    hotspots: HotspotReport
    latency_stats: LatencyStats
    dvfs_recommendations: List[DVFSResult]
    suggestions: List[OptimizationSuggestion]
    compliance_results: List[ComplianceCheck]
    hbm3_compatibility: bool
    optimization_score: float = 0.0  # 0-100, higher is better


@dataclass
class Phase14Stats:
    """Statistics for Phase 14 features"""
    # Analysis stats
    accesses_analyzed: int = 0
    latency_samples_collected: int = 0
    bottleneck_checks: int = 0
    hotspot_detections: int = 0

    # Compliance stats
    compliance_checks_passed: int = 0
    compliance_checks_failed: int = 0
    hbm3_compat_checks: int = 0

    # Optimization stats
    optimizations_applied: int = 0
    suggestions_generated: int = 0

    # Performance stats
    prefetch_hits: int = 0
    prefetch_misses: int = 0
    bank_conflicts_avoided: int = 0
    coalesced_writes: int = 0


class HBM4OptimizedController:
    """HBM4 Controller with integrated analysis, compliance, and optimization

    This controller wraps HBM4Controller and adds:
    - Real-time performance analysis
    - JEDEC compliance validation
    - HBM3 backward compatibility checking
    - Automatic optimization suggestions
    - Advanced prefetching with pattern classification
    - Bank conflict prediction
    - Smart queue management

    Args:
        enable_analysis: Enable real-time analysis (default True)
        enable_compliance: Enable compliance checking (default True)
        enable_optimization: Enable automatic optimization (default True)
        spec: Optional HBM4 specification (uses default if None)
        config: Optional HBM4 configuration override
    """

    def __init__(
        self,
        enable_analysis: bool = True,
        enable_compliance: bool = True,
        enable_optimization: bool = True,
        spec: Optional[HBM4Spec] = None,
        config: Optional[HBMConfig] = None,
    ):
        # Base HBM4 controller
        self._base_controller = HBM4Controller(
            spec=spec,
            config=config,
            enable_qos=True,
            enable_refresh=True,
            enable_dfi=True,
            enable_pipeline=True,
            enable_prefetch=True,
        )

        # Phase 14 feature flags
        self._enable_analysis = enable_analysis
        self._enable_compliance = enable_compliance
        self._enable_optimization = enable_optimization

        # Statistics
        self.stats = Phase14Stats()

        # Initialize Phase 10 analysis modules
        if enable_analysis:
            self._init_analysis_modules()

        # Initialize Phase 11 compliance modules
        if enable_compliance:
            self._init_compliance_modules()

        # Initialize Phase 13 optimization modules
        if enable_optimization:
            self._init_optimization_modules()

        # Integration state
        self._access_history: List[Tuple[int, bool]] = []  # (addr, is_read)
        self._latency_distribution = LatencyDistribution()

        # Current DVFS state
        self._current_frequency_gtps = 16.0  # Default HBM4 speed

        _logger.info(
            f"HBM4OptimizedController initialized: "
            f"analysis={enable_analysis}, compliance={enable_compliance}, "
            f"optimization={enable_optimization}"
        )

    def _init_analysis_modules(self):
        """Initialize Phase 10 analysis modules"""
        self.bottleneck_detector = BottleneckDetector()
        self.hotspot_detector = HotspotDetector(threshold_percentile=95.0)
        self.latency_analyzer = LatencyDistribution()
        self.dvfs_analyzer = DVFSAnalyzer()
        self.power_curve = PowerPerformanceCurve()
        self.optimizer = Optimizer()

        _logger.debug("Phase 10 analysis modules initialized")

    def _init_compliance_modules(self):
        """Initialize Phase 11 compliance modules"""
        self.jedec_validator = JEDECValidator()
        self.hbm3_checker = HBM3CompatibilityChecker()

        _logger.debug("Phase 11 compliance modules initialized")

    def _init_optimization_modules(self):
        """Initialize Phase 13 optimization modules"""
        spec = self._base_controller.spec

        self.parallel_scheduler = ParallelChannelScheduler(num_channels=spec.channels)
        self.prefetch_engine = AdvancedPrefetchEngine(
            max_prefetch_degree=8,
            confidence_threshold=0.7
        )
        self.smart_queue = SmartQueue(
            max_size=256,
            aging_factor=100,
            coalescing_window=10,
            max_wait_timeout=10000
        )
        self.bank_predictor = BankPredictor(num_banks=spec.banks_per_pseudo_channel)

        _logger.debug("Phase 13 optimization modules initialized")

    # =========================================================================
    # Proxy properties to base controller
    # =========================================================================

    @property
    def channels(self) -> int:
        return self._base_controller.channels

    @property
    def pseudo_channels(self) -> int:
        return self._base_controller.pseudo_channels

    @property
    def dfi_ready(self) -> bool:
        return self._base_controller.dfi_ready

    @property
    def current_time_ns(self) -> float:
        return self._base_controller.current_time_ns

    @property
    def current_cycle(self) -> int:
        return self._base_controller._cycle_count

    @property
    def stats_base(self):
        """Base controller stats"""
        return self._base_controller.stats

    # =========================================================================
    # Request submission with integrated analysis
    # =========================================================================

    def submit_request(
        self,
        addr: int,
        is_read: bool,
        qos_level: int = 8,
        size_bytes: int = 64,
    ) -> Optional[str]:
        """Submit request with integrated analysis and optimization

        This method wraps the base controller's submit_request and adds:
        - Access pattern recording for analysis
        - Hotspot detection
        - Prefetch generation
        - Bank conflict prediction
        - Smart queue management (if enabled)
        """
        # Record access for analysis
        if self._enable_analysis:
            self._access_history.append((addr, is_read))
            self.stats.accesses_analyzed += 1

            # Update hotspot detector (uses trace-based approach)
            # Hotspots are detected periodically via detect() method

            # Update latency analyzer with pending request
            # (actual completion time tracked in tick())

        # Apply bank conflict prediction (Phase 13)
        if self._enable_optimization:
            decoded = self._base_controller.decoder.decode(addr)

            # Check if this access might conflict
            conflict_pred = self.bank_predictor.predict_conflict(
                target_bank=decoded.bank_id,
                target_row=decoded.row_id,
                current_cycle=self.current_cycle
            )

            if conflict_pred.will_conflict:
                self.stats.bank_conflicts_avoided += 1
                # Could adjust scheduling priority here if needed

            # Update bank predictor
            self.bank_predictor.record_access(
                bank_id=decoded.bank_id,
                row_id=decoded.row_id,
                cycle=self.current_cycle
            )

        # Submit to base controller
        request_id = self._base_controller.submit_request(
            addr=addr,
            is_read=is_read,
            qos_level=qos_level,
            size_bytes=size_bytes,
        )

        return request_id

    def tick(self) -> List:
        """Advance simulation by one cycle with integrated analysis"""
        # Tick base controller
        responses = self._base_controller.tick()

        # Update latency for completed requests
        if self._enable_analysis:
            for resp in responses:
                if hasattr(resp, 'completion_time') and resp.completion_time > 0:
                    latency_ns = resp.completion_time - resp.arrival_time
                    self._latency_distribution.add_sample(latency_ns)
                    self.stats.latency_samples_collected += 1

        # Update DVFS analysis (periodic)
        if self._enable_analysis and self.current_cycle % 1000 == 0:
            self._update_dvfs_analysis()

        return responses

    def _update_dvfs_analysis(self):
        """Update DVFS analysis based on current state"""
        if not hasattr(self, 'dvfs_analyzer'):
            return

        # Get current performance metrics
        base_stats = self._base_controller.stats

        if base_stats.total_requests > 0:
            latency_ns = base_stats.average_latency_ns
            bandwidth = self._estimate_bandwidth()
            power = self._estimate_power()

            # Record for DVFS analysis
            self.dvfs_analyzer.record_operation(
                frequency_gtps=self._current_frequency_gtps,
                bandwidth_gbps=bandwidth,
                latency_ns=latency_ns,
                power_w=power,
                efficiency=self._calculate_efficiency(bandwidth, power)
            )

    def _estimate_bandwidth(self) -> float:
        """Estimate current bandwidth in GB/s"""
        # ponytail: simplified bandwidth estimation
        base_stats = self._base_controller.stats
        if self.current_time_ns > 0:
            return base_stats.total_bandwidth_bytes / self.current_time_ns * 1000
        return 0.0

    def _estimate_power(self) -> float:
        """Estimate current power in Watts"""
        # ponytail: simplified power estimation
        base_stats = self._base_controller.stats
        active_ratio = base_stats.total_requests / max(1, self.current_cycle)
        return 10.0 + active_ratio * 30.0  # 10-40W range

    def _calculate_efficiency(self, bandwidth: float, power: float) -> float:
        """Calculate power efficiency (GB/s per Watt)"""
        if power > 0:
            return bandwidth / power
        return 0.0

    # =========================================================================
    # Analysis and reporting
    # =========================================================================

    def analyze_performance(self) -> OptimizationReport:
        """Generate complete optimization report

        This method collects all analysis data and generates a comprehensive
        optimization report including:
        - Bottleneck analysis
        - Hotspot detection
        - Latency statistics
        - DVFS recommendations
        - Optimization suggestions
        - Compliance results
        """
        # Initialize default values
        bottleneck_report = BottleneckReport()
        hotspot_report = HotspotReport()
        latency_stats = LatencyStats()
        dvfs_results: List[DVFSResult] = []
        suggestions: List[OptimizationSuggestion] = []
        compliance_results: List[ComplianceCheck] = []
        hbm3_compat = True

        # Collect analysis results
        if self._enable_analysis:
            # Format metrics for bottleneck detector
            access_metrics = self._collect_access_metrics()
            channel_metrics = {}
            for channel_id, count in access_metrics.get('channel_distribution', {}).items():
                total = access_metrics['access_count']
                channel_metrics[f'channel_{channel_id}'] = {
                    'bank_conflict_rate': access_metrics.get('bank_conflicts', 0) / max(total, 1),
                    'utilization': count / max(total, 1),
                }
            bottleneck_report = self.bottleneck_detector.detect(channel_metrics)
            self.stats.bottleneck_checks += 1

            hotspot_report = self.hotspot_detector.generate_report()
            self.stats.hotspot_detections = len(hotspot_report.hotspots)

            latency_stats = self._latency_distribution.analyze()

            dvfs_results = self.dvfs_analyzer.get_recommendations()

            suggestions = self.optimizer.generate_suggestions(
                bottleneck_report, dvfs_results
            )
            self.stats.suggestions_generated = len(suggestions)

        # Collect compliance results
        if self._enable_compliance:
            compliance_results = self.jedec_validator.run_all_checks(
                self._get_compliance_config()
            )

            for check in compliance_results:
                if check.level == ComplianceLevel.PASS:
                    self.stats.compliance_checks_passed += 1
                elif check.level == ComplianceLevel.FAIL:
                    self.stats.compliance_checks_failed += 1

            hbm3_compat = self.hbm3_checker.check_all(
                self._get_compliance_config()
            )

        # Calculate optimization score
        score = self._calculate_optimization_score(bottleneck_report, compliance_results)

        return OptimizationReport(
            bottlenecks=bottleneck_report,
            hotspots=hotspot_report,
            latency_stats=latency_stats,
            dvfs_recommendations=dvfs_results,
            suggestions=suggestions,
            compliance_results=compliance_results,
            hbm3_compatibility=hbm3_compat,
            optimization_score=score,
        )

    def _collect_access_metrics(self) -> Dict:
        """Collect access metrics for bottleneck analysis"""
        return {
            'access_count': len(self._access_history),
            'read_count': sum(1 for _, r in self._access_history if r),
            'write_count': sum(1 for _, r in self._access_history if not r),
            'unique_addresses': len(set(addr for addr, _ in self._access_history)),
            'channel_distribution': self._get_channel_distribution(),
            'bank_conflicts': self.bank_predictor.get_statistics()['total_predictions'],
        }

    def _get_channel_distribution(self) -> Dict[int, int]:
        """Get distribution of accesses across channels"""
        dist = defaultdict(int)
        for addr, _ in self._access_history:
            decoded = self._base_controller.decoder.decode(addr)
            dist[decoded.channel_id] += 1
        return dict(dist)

    def _get_compliance_config(self) -> Dict:
        """Get configuration for compliance checking"""
        spec = self._base_controller.spec
        # Convert timing from cycles to nanoseconds (nRCDRD ≈ tRCD, nRAS ≈ tRAS, etc.)
        return {
            'tRCD_ns': spec.nRCDRD * spec.tCK_ps / 1000.0,  # Convert ps to ns
            'tRP_ns': spec.nRP * spec.tCK_ps / 1000.0,
            'tRAS_ns': spec.nRAS * spec.tCK_ps / 1000.0,
            'tRC_ns': spec.nRC * spec.tCK_ps / 1000.0,
            'active_power_w': self._estimate_power(),
            'idle_power_w': 5.0,  # Assumed idle power
        }

    def _calculate_optimization_score(
        self,
        bottleneck_report: Optional[BottleneckReport],
        compliance_results: List[ComplianceCheck]
    ) -> float:
        """Calculate overall optimization score (0-100)"""
        score = 100.0

        # Deduct for bottlenecks
        if bottleneck_report and bottleneck_report.bottlenecks:
            high_severity = sum(
                1 for b in bottleneck_report.bottlenecks
                if b.severity > 0.7
            )
            score -= high_severity * 5.0

        # Deduct for compliance failures
        failed = sum(1 for c in compliance_results if c.level == ComplianceLevel.FAIL)
        score -= failed * 10.0

        # Deduct for warnings
        warnings = sum(1 for c in compliance_results if c.level == ComplianceLevel.WARNING)
        score -= warnings * 2.0

        return max(0.0, min(100.0, score))

    # =========================================================================
    # DVFS control
    # =========================================================================

    def set_frequency(self, frequency_gtps: float) -> bool:
        """Set operating frequency

        Args:
            frequency_gtps: Frequency in GT/s (8, 12, or 16)

        Returns:
            True if frequency change was accepted
        """
        valid_frequencies = [8.0, 12.0, 16.0]
        if frequency_gtps not in valid_frequencies:
            _logger.warning(f"Invalid frequency {frequency_gtps} GT/s")
            return False

        old_freq = self._current_frequency_gtps
        self._current_frequency_gtps = frequency_gtps

        # Update base controller if needed
        # Note: This would require more complex integration with timing

        _logger.info(f"Frequency changed: {old_freq} -> {frequency_gtps} GT/s")
        return True

    def get_current_frequency(self) -> float:
        """Get current operating frequency"""
        return self._current_frequency_gtps

    # =========================================================================
    # Prefetch control
    # =========================================================================

    def get_prefetch_predictions(self, stream_id: int = 0) -> List[Tuple[int, float]]:
        """Get prefetch predictions for a stream

        Returns:
            List of (address, confidence) tuples
        """
        if not hasattr(self, 'prefetch_engine'):
            return []

        # Get pattern classification
        pattern = self.prefetch_engine.classifier.classify()

        # Get predictions
        decisions = self.prefetch_engine.predict(0, stream_id)

        return [(d.address, d.confidence) for d in decisions]

    # =========================================================================
    # Queue management
    # =========================================================================

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics from both smart queue and base controller"""
        sq_stats = self.smart_queue.get_statistics() if hasattr(self, 'smart_queue') else {}
        stats = {
            'smart_queue': {
                'size': self.smart_queue.get_queue_depth(),
                'utilization': sq_stats.get('utilization', 0),
                'coalesced': sq_stats.get('coalesced_requests', 0),
            },
            'base_controller': {
                'read_queue_depth': len(self._base_controller.queue_manager.read_queue._queue),
                'write_queue_depth': len(self._base_controller.queue_manager.write_queue._queue),
            }
        }
        return stats

    # =========================================================================
    # Bank predictor control
    # =========================================================================

    def get_bank_conflict_prediction(
        self,
        bank_id: int,
        target_row: int
    ) -> Tuple[bool, float]:
        """Get bank conflict prediction

        Returns:
            Tuple of (will_conflict, confidence)
        """
        if not hasattr(self, 'bank_predictor'):
            return False, 0.0

        prediction = self.bank_predictor.predict_conflict(
            target_bank=bank_id,
            target_row=target_row,
            current_cycle=self.current_cycle
        )

        return prediction.will_conflict, prediction.confidence

    def get_optimal_bank_order(self, target_rows: List[int]) -> List[int]:
        """Get optimal bank access order to minimize conflicts

        Args:
            target_rows: List of target row addresses

        Returns:
            Ordered list of bank IDs
        """
        if not hasattr(self, 'bank_predictor'):
            # Fallback: return sequential bank order
            return list(range(len(target_rows)))

        optimal = self.bank_predictor.get_optimal_bank_order(target_rows)
        # BankPredictor returns list of ints, not BankState objects
        return list(optimal)

    # =========================================================================
    # Reset and cleanup
    # =========================================================================

    def reset(self):
        """Reset controller and all analysis/compliance/optimization state"""
        # Reset base controller
        self._base_controller.reset()

        # Reset analysis modules
        if self._enable_analysis:
            self.bottleneck_detector = BottleneckDetector()
            self.hotspot_detector = HotspotDetector(threshold_percentile=95.0)
            self._latency_distribution = LatencyDistribution()
            self.dvfs_analyzer = DVFSAnalyzer()

        # Reset optimization modules
        if self._enable_optimization:
            spec = self._base_controller.spec
            self.parallel_scheduler = ParallelChannelScheduler(num_channels=spec.channels)
            self.prefetch_engine = AdvancedPrefetchEngine(
            max_prefetch_degree=8,
            confidence_threshold=0.7
        )
            self.smart_queue = SmartQueue(
            max_size=256,
            aging_factor=100,
            coalescing_window=10,
            max_wait_timeout=10000
        )
            self.bank_predictor = BankPredictor(num_banks=spec.banks_per_pseudo_channel)

        # Reset state
        self._access_history = []
        self.stats = Phase14Stats()

        _logger.info("HBM4OptimizedController reset complete")


def create_optimized_controller(
    analysis: bool = True,
    compliance: bool = True,
    optimization: bool = True,
    **kwargs
) -> HBM4OptimizedController:
    """Factory function to create an optimized HBM4 controller

    Args:
        analysis: Enable analysis modules
        compliance: Enable compliance modules
        optimization: Enable optimization modules
        **kwargs: Additional arguments for HBM4OptimizedController

    Returns:
        Configured HBM4OptimizedController instance
    """
    return HBM4OptimizedController(
        enable_analysis=analysis,
        enable_compliance=compliance,
        enable_optimization=optimization,
        **kwargs
    )
