# tests/analysis/test_optimizer.py
"""Tests for Optimizer Module"""

import pytest
from model.analysis.optimizer import Optimizer, OptimizationSuggestion
from model.analysis.bottleneck_detector import BottleneckReport, Bottleneck, BottleneckType
from model.analysis.dvfs_analyzer import DVFSResult, DVFSSpeedGrade


class TestOptimizationSuggestion:
    """Test the OptimizationSuggestion dataclass"""

    def test_creation_basic(self):
        suggestion = OptimizationSuggestion(
            category="frequency",
            priority=1,
            description="Test suggestion",
            expected_improvement="10% improvement"
        )
        assert suggestion.category == "frequency"
        assert suggestion.priority == 1
        assert suggestion.config_change is None

    def test_creation_with_config(self):
        suggestion = OptimizationSuggestion(
            category="scheduling",
            priority=2,
            description="Test with config",
            expected_improvement="15% improvement",
            config_change={"queue_depth": 128}
        )
        assert suggestion.config_change is not None
        assert suggestion.config_change["queue_depth"] == 128


class TestOptimizer:
    """Test the Optimizer class"""

    def test_optimizer_creation(self):
        optimizer = Optimizer()
        assert optimizer.suggestions == []

    def test_empty_reports(self):
        """Test with no bottlenecks and no DVFS results"""
        optimizer = Optimizer()
        suggestions = optimizer.generate_suggestions(BottleneckReport(), [])
        assert suggestions == []

    def test_bank_conflict_detection(self):
        """Test detection of high-severity bank conflicts"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.85,
            location="channel_0.bank_3",
            description="High bank conflict"
        ))
        suggestions = optimizer.generate_suggestions(report, [])

        assert len(suggestions) >= 1
        scheduling = [s for s in suggestions if s.category == "scheduling"]
        assert any("bank conflict" in s.description.lower() for s in scheduling)
        # Priority 1 for bank conflicts
        bank_conflict_suggestion = next(
            (s for s in suggestions if "bank conflict" in s.description.lower()),
            None
        )
        assert bank_conflict_suggestion is not None
        assert bank_conflict_suggestion.priority == 1

    def test_queue_blocking_detection(self):
        """Test detection of queue blocking issues"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.QUEUE_BLOCKING,
            severity=0.75,
            location="channel_0.queue",
            description="Queue blocking detected"
        ))
        suggestions = optimizer.generate_suggestions(report, [])

        assert len(suggestions) >= 1
        assert any("queue" in s.description.lower() for s in suggestions)

    def test_channel_utilization_detection(self):
        """Test detection of high channel utilization"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.CHANNEL_UTILIZATION,
            severity=0.95,
            location="channel_0",
            description="High channel utilization"
        ))
        suggestions = optimizer.generate_suggestions(report, [])

        addressing = [s for s in suggestions if s.category == "addressing"]
        assert len(addressing) >= 1
        assert any("channel" in s.description.lower() or "load" in s.description.lower()
                   for s in addressing)

    def test_queue_overflow_detection(self):
        """Test detection of queue overflow"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.QUEUE_OVERFLOW,
            severity=0.8,
            location="channel_0",
            description="Queue overflow"
        ))
        suggestions = optimizer.generate_suggestions(report, [])

        assert len(suggestions) >= 1
        assert any("overflow" in s.description.lower() or "buffer" in s.description.lower()
                   for s in suggestions)

    def test_refresh_conflict_detection(self):
        """Test detection of refresh conflicts"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.REFRESH_CONFLICT,
            severity=0.6,
            location="channel_0",
            description="Refresh conflict"
        ))
        suggestions = optimizer.generate_suggestions(report, [])

        assert len(suggestions) >= 1
        assert any("refresh" in s.description.lower() for s in suggestions)

    def test_thermal_throttle_detection(self):
        """Test detection of thermal throttling"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.THERMAL_THROTTLE,
            severity=0.7,
            location="channel_0",
            description="Thermal throttle"
        ))
        suggestions = optimizer.generate_suggestions(report, [])

        assert len(suggestions) >= 1
        assert any("thermal" in s.description.lower() or "frequency" in s.description.lower()
                   for s in suggestions)

    def test_dvfs_best_efficiency(self):
        """Test DVFS suggestion for best efficiency"""
        optimizer = Optimizer()
        dvfs_results = [
            DVFSResult.from_speed_grade(DVFSSpeedGrade.S8),
            DVFSResult.from_speed_grade(DVFSSpeedGrade.S12),
            DVFSResult.from_speed_grade(DVFSSpeedGrade.S16),
        ]
        suggestions = optimizer.generate_suggestions(BottleneckReport(), dvfs_results)

        frequency_suggestions = [s for s in suggestions if s.category == "frequency"]
        assert len(frequency_suggestions) >= 1
        # At least one suggestion should have config_change with frequency
        eff_suggestions = [s for s in frequency_suggestions if s.config_change]
        assert len(eff_suggestions) >= 1

    def test_dvfs_all_configurations(self):
        """Test that all DVFS configurations are suggested"""
        optimizer = Optimizer()
        dvfs_results = [
            DVFSResult(frequency_gtps=8.0, voltage_v=0.8, power_w=5.0,
                      bandwidth_gbps=32.0, latency_ns=200.0, efficiency=6.4),
            DVFSResult(frequency_gtps=12.0, voltage_v=0.92, power_w=8.3,
                      bandwidth_gbps=48.0, latency_ns=133.0, efficiency=5.8),
            DVFSResult(frequency_gtps=16.0, voltage_v=1.04, power_w=13.3,
                      bandwidth_gbps=64.0, latency_ns=100.0, efficiency=4.8),
        ]
        suggestions = optimizer.generate_suggestions(BottleneckReport(), dvfs_results)

        # Should have at least 3 frequency suggestions (efficiency, performance, power)
        frequency_suggestions = [s for s in suggestions if s.category == "frequency"]
        assert len(frequency_suggestions) >= 3

        # Check that different frequencies are suggested
        frequencies = [s.config_change["frequency"] for s in frequency_suggestions
                      if s.config_change]
        assert 8.0 in frequencies
        assert 16.0 in frequencies

    def test_priority_ordering(self):
        """Test that suggestions are sorted by priority"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.CHANNEL_UTILIZATION,
            severity=0.95,
            location="channel_0",
            description="High utilization"
        ))
        dvfs_results = [DVFSResult.from_speed_grade(DVFSSpeedGrade.S12)]
        suggestions = optimizer.generate_suggestions(report, dvfs_results)

        # Verify sorted by priority
        priorities = [s.priority for s in suggestions]
        assert priorities == sorted(priorities)
        # First suggestion should have priority 1 or 2 (highest priority)
        assert suggestions[0].priority <= 2

    def test_multiple_bottleneck_types(self):
        """Test handling of multiple bottleneck types"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.8,
            location="channel_0",
            description="Bank conflict"
        ))
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.QUEUE_OVERFLOW,
            severity=0.75,
            location="channel_0",
            description="Queue overflow"
        ))
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.CHANNEL_UTILIZATION,
            severity=0.95,
            location="channel_1",
            description="Channel utilization"
        ))
        suggestions = optimizer.generate_suggestions(report, [])

        categories = set(s.category for s in suggestions)
        assert len(categories) >= 2  # At least scheduling and addressing

    def test_get_top_suggestions(self):
        """Test getting top N suggestions"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.85,
            location="channel_0",
            description="Bank conflict"
        ))
        dvfs_results = [DVFSResult.from_speed_grade(DVFSSpeedGrade.S12)]
        optimizer.generate_suggestions(report, dvfs_results)

        top3 = optimizer.get_top_suggestions(3)
        assert len(top3) <= 3
        # Top suggestions should be the highest priority ones
        if len(optimizer.suggestions) >= 3:
            assert top3[0].priority <= top3[-1].priority

    def test_get_by_category(self):
        """Test filtering suggestions by category"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.85,
            location="channel_0",
            description="Bank conflict"
        ))
        dvfs_results = [DVFSResult.from_speed_grade(DVFSSpeedGrade.S12)]
        optimizer.generate_suggestions(report, dvfs_results)

        scheduling = optimizer.get_by_category("scheduling")
        frequency = optimizer.get_by_category("frequency")
        addressing = optimizer.get_by_category("addressing")

        assert all(s.category == "scheduling" for s in scheduling)
        assert all(s.category == "frequency" for s in frequency)
        assert all(s.category == "addressing" for s in addressing)

    def test_low_severity_bottlenecks(self):
        """Test that low-severity bottlenecks don't generate suggestions"""
        optimizer = Optimizer()
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.5,  # Below 0.7 threshold
            location="channel_0",
            description="Low conflict rate"
        ))
        suggestions = optimizer.generate_suggestions(report, [])

        # Should not have scheduling suggestion for low-severity bank conflict
        bank_conflict_suggestions = [
            s for s in suggestions
            if "bank conflict" in s.description.lower()
        ]
        assert len(bank_conflict_suggestions) == 0

    def test_combined_analysis(self):
        """Test combined bottleneck and DVFS analysis"""
        optimizer = Optimizer()

        # Create bottlenecks
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.9,
            location="channel_0",
            description="Critical bank conflict"
        ))
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.QUEUE_BLOCKING,
            severity=0.8,
            location="channel_1",
            description="Queue blocking"
        ))

        # Create DVFS results
        dvfs_results = [
            DVFSResult(frequency_gtps=8.0, voltage_v=0.8, power_w=5.0,
                      bandwidth_gbps=32.0, latency_ns=200.0, efficiency=6.4),
            DVFSResult(frequency_gtps=16.0, voltage_v=1.04, power_w=13.3,
                      bandwidth_gbps=64.0, latency_ns=100.0, efficiency=4.8),
        ]

        suggestions = optimizer.generate_suggestions(report, dvfs_results)

        # Should have suggestions from both sources
        assert len(suggestions) >= 3  # At least bank conflict, queue, and DVFS

        # Check categories are represented
        categories = set(s.category for s in suggestions)
        assert "scheduling" in categories
        assert "frequency" in categories

    def test_expected_improvement_format(self):
        """Test that expected_improvement is properly formatted"""
        optimizer = Optimizer()
        dvfs_results = [DVFSResult.from_speed_grade(DVFSSpeedGrade.S12)]
        suggestions = optimizer.generate_suggestions(BottleneckReport(), dvfs_results)

        for suggestion in suggestions:
            assert suggestion.expected_improvement is not None
            assert len(suggestion.expected_improvement) > 0
            # Should contain some metric info
            assert any(char.isdigit() for char in suggestion.expected_improvement)