# tests/analysis/test_bottleneck_detector.py
import pytest
from model.analysis.bottleneck_detector import Bottleneck, BottleneckType, BottleneckReport


class TestBottleneckDataclass:
    def test_bottleneck_creation(self):
        bottleneck = Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.8,
            location="channel_0.bank_3",
            description="Bank 3 has 85% conflict rate"
        )
        assert bottleneck.bottleneck_type == BottleneckType.BANK_CONFLICT
        assert bottleneck.severity == 0.8
        assert "bank_3" in bottleneck.location

    def test_bottleneck_type_enum(self):
        assert BottleneckType.BANK_CONFLICT.value == "bank_conflict"
        assert BottleneckType.QUEUE_BLOCKING.value == "queue_blocking"
        assert BottleneckType.CHANNEL_UTILIZATION.value == "channel_utilization"

    def test_bottleneck_with_metrics(self):
        bottleneck = Bottleneck(
            bottleneck_type=BottleneckType.QUEUE_OVERFLOW,
            severity=0.95,
            location="channel_0.queue",
            description="Queue overflow detected",
            metrics={"queue_depth": 64, "max_depth": 32}
        )
        assert bottleneck.metrics is not None
        assert bottleneck.metrics["queue_depth"] == 64

    def test_bottleneck_severity_range(self):
        """Test that severity values are within valid range"""
        for severity in [0.0, 0.5, 1.0]:
            b = Bottleneck(
                bottleneck_type=BottleneckType.THERMAL_THROTTLE,
                severity=severity,
                location="channel_0",
                description="Thermal throttle"
            )
            assert 0.0 <= b.severity <= 1.0


class TestBottleneckTypeEnum:
    def test_all_bottleneck_types_defined(self):
        """Verify all expected bottleneck types exist"""
        expected_types = [
            "bank_conflict",
            "queue_blocking",
            "channel_utilization",
            "queue_overflow",
            "refresh_conflict",
            "thermal_throttle",
        ]
        actual_values = [bt.value for bt in BottleneckType]
        for expected in expected_types:
            assert expected in actual_values

    def test_bottleneck_type_string_values(self):
        """Test that enum values are strings"""
        for bt in BottleneckType:
            assert isinstance(bt.value, str)


class TestBottleneckReport:
    def test_report_creation(self):
        report = BottleneckReport()
        assert report.bottlenecks == []
        assert report.get_summary()["total_bottlenecks"] == 0

    def test_add_bottleneck(self):
        report = BottleneckReport()
        bottleneck = Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.8,
            location="channel_0",
            description="Test bottleneck"
        )
        report.add(bottleneck)
        assert len(report.bottlenecks) == 1

    def test_get_summary_empty(self):
        report = BottleneckReport()
        summary = report.get_summary()
        assert summary["total_bottlenecks"] == 0
        assert summary["by_type"] == {}
        assert summary["critical_count"] == 0

    def test_get_summary_with_bottlenecks(self):
        report = BottleneckReport()
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.8,
            location="channel_0",
            description="Conflict"
        ))
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.BANK_CONFLICT,
            severity=0.9,
            location="channel_1",
            description="Conflict"
        ))
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.QUEUE_OVERFLOW,
            severity=0.75,
            location="channel_0",
            description="Overflow"
        ))

        summary = report.get_summary()
        assert summary["total_bottlenecks"] == 3
        assert summary["by_type"]["bank_conflict"] == 2
        assert summary["by_type"]["queue_overflow"] == 1
        # critical_count is severity > 0.7
        assert summary["critical_count"] == 3

    def test_get_summary_critical_threshold(self):
        report = BottleneckReport()
        # Severity 0.7 is NOT critical (threshold is > 0.7)
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.CHANNEL_UTILIZATION,
            severity=0.7,
            location="channel_0",
            description="At threshold"
        ))
        # Severity 0.71 IS critical
        report.add(Bottleneck(
            bottleneck_type=BottleneckType.CHANNEL_UTILIZATION,
            severity=0.71,
            location="channel_1",
            description="Over threshold"
        ))
        summary = report.get_summary()
        assert summary["critical_count"] == 1


class TestBottleneckDetector:
    def test_detector_creation(self):
        from model.analysis.bottleneck_detector import BottleneckDetector
        detector = BottleneckDetector()
        assert detector is not None
        assert detector.conflict_threshold == 0.7
        assert detector.utilization_threshold == 0.9

    def test_detector_custom_thresholds(self):
        from model.analysis.bottleneck_detector import BottleneckDetector
        detector = BottleneckDetector(conflict_threshold=0.8, utilization_threshold=0.95)
        assert detector.conflict_threshold == 0.8
        assert detector.utilization_threshold == 0.95

    def test_detect_bank_conflict(self):
        from model.analysis.bottleneck_detector import BottleneckDetector, BottleneckType
        detector = BottleneckDetector()
        # Mock metrics with high bank conflict
        metrics = {
            "channel_0": {
                "bank_conflict_rate": 0.85,
                "bank_utilization": {"bank_0": 0.9, "bank_1": 0.85}
            }
        }
        report = detector.detect(metrics)
        assert len(report.bottlenecks) > 0
        assert any(b.bottleneck_type == BottleneckType.BANK_CONFLICT for b in report.bottlenecks)

    def test_detect_no_bottleneck(self):
        from model.analysis.bottleneck_detector import BottleneckDetector
        detector = BottleneckDetector()
        # Metrics below threshold
        metrics = {
            "channel_0": {
                "bank_conflict_rate": 0.3,
                "utilization": 0.5
            }
        }
        report = detector.detect(metrics)
        assert len(report.bottlenecks) == 0

    def test_detect_channel_utilization(self):
        from model.analysis.bottleneck_detector import BottleneckDetector, BottleneckType
        detector = BottleneckDetector()
        metrics = {
            "channel_0": {
                "bank_conflict_rate": 0.3,
                "utilization": 0.95
            }
        }
        report = detector.detect(metrics)
        assert len(report.bottlenecks) > 0
        assert any(b.bottleneck_type == BottleneckType.CHANNEL_UTILIZATION for b in report.bottlenecks)

    def test_detect_multiple_channels(self):
        from model.analysis.bottleneck_detector import BottleneckDetector
        detector = BottleneckDetector()
        metrics = {
            "channel_0": {"bank_conflict_rate": 0.85, "utilization": 0.5},
            "channel_1": {"bank_conflict_rate": 0.3, "utilization": 0.95},
            "channel_2": {"bank_conflict_rate": 0.3, "utilization": 0.5},
        }
        report = detector.detect(metrics)
        assert len(report.bottlenecks) == 2  # One from channel_0, one from channel_1

    def test_detect_empty_metrics(self):
        from model.analysis.bottleneck_detector import BottleneckDetector
        detector = BottleneckDetector()
        report = detector.detect({})
        assert len(report.bottlenecks) == 0

    def test_detect_missing_keys(self):
        from model.analysis.bottleneck_detector import BottleneckDetector
        detector = BottleneckDetector()
        # Metrics with missing keys should not cause errors
        metrics = {
            "channel_0": {"some_other_key": 0.9}
        }
        report = detector.detect(metrics)
        assert len(report.bottlenecks) == 0

    def test_bottleneck_severity_matches_metric(self):
        from model.analysis.bottleneck_detector import BottleneckDetector
        detector = BottleneckDetector()
        conflict_rate = 0.87
        metrics = {
            "channel_0": {"bank_conflict_rate": conflict_rate}
        }
        report = detector.detect(metrics)
        assert len(report.bottlenecks) == 1
        assert report.bottlenecks[0].severity == conflict_rate
