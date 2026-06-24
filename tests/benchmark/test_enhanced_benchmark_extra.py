"""
Additional Tests for Enhanced Benchmark Module

Covers edge cases and additional functionality.

Run with: pytest tests/benchmark/test_enhanced_benchmark_extra.py -v
"""

import pytest
from model.benchmark.enhanced_benchmark import (
    EnhancedBenchmark,
    EnhancedBenchmarkReport,
    MultiChannelResult,
    MixedTrafficResult,
    BankGroupConflictResult,
    RefreshImpactResult,
    QoSImpactResult,
)


class TestEnhancedBenchmarkReport:
    """Tests for EnhancedBenchmarkReport"""

    def test_default_report(self):
        """Test default report initialization"""
        report = EnhancedBenchmarkReport()
        assert report.multi_channel is None
        assert report.mixed_traffic is None
        assert report.bank_group_conflict is None
        assert report.refresh_impact is None
        assert report.qos_impact is None
        assert report.total_bandwidth_gbs == 0.0
        assert report.average_latency_ns == 0.0
        assert report.peak_efficiency_percent == 0.0

    def test_report_to_dict(self):
        """Test report to_dict conversion"""
        report = EnhancedBenchmarkReport()
        report.timestamp = "2026-01-01T00:00:00"
        report.duration_seconds = 10.5

        d = report.to_dict()
        assert d['timestamp'] == "2026-01-01T00:00:00"
        assert d['duration_seconds'] == 10.5
        assert 'multi_channel' in d
        assert 'mixed_traffic' in d
        assert 'findings' in d
        assert 'warnings' in d


class TestMultiChannelResult:
    """Tests for MultiChannelResult"""

    def test_default_result(self):
        """Test default MultiChannelResult"""
        result = MultiChannelResult()
        assert result.num_channels == 32
        assert result.channels_active == 0
        assert result.peak_bandwidth_gbs == 0.0
        assert result.measured_bandwidth_gbs == 0.0

    def test_to_dict(self):
        """Test to_dict conversion"""
        result = MultiChannelResult()
        result.num_channels = 32
        result.channels_active = 16
        result.peak_bandwidth_gbs = 1024.0
        result.measured_bandwidth_gbs = 800.0
        result.bandwidth_efficiency_percent = 78.1

        d = result.to_dict()
        assert d['num_channels'] == 32
        assert d['channels_active'] == 16
        assert d['bandwidth_efficiency_percent'] == 78.1

    def test_str_representation(self):
        """Test string representation"""
        result = MultiChannelResult()
        result.num_channels = 32
        result.channels_active = 16
        result.peak_bandwidth_gbs = 1024.0
        result.measured_bandwidth_gbs = 800.0
        result.bandwidth_efficiency_percent = 78.1
        result.channel_utilization_percent = 50.0

        s = str(result)
        assert "32" in s
        assert "16" in s
        assert "78.1" in s


class TestMixedTrafficResult:
    """Tests for MixedTrafficResult"""

    def test_default_result(self):
        """Test default MixedTrafficResult"""
        result = MixedTrafficResult()
        assert result.read_ratio == 0.5
        assert result.write_ratio == 0.5
        assert result.read_bandwidth_gbs == 0.0
        assert result.write_bandwidth_gbs == 0.0

    def test_to_dict(self):
        """Test to_dict conversion"""
        result = MixedTrafficResult()
        result.read_ratio = 0.7
        result.write_ratio = 0.3
        result.read_bandwidth_gbs = 500.0
        result.write_bandwidth_gbs = 200.0
        result.total_bandwidth_gbs = 700.0

        d = result.to_dict()
        assert d['read_ratio'] == 0.7
        assert d['write_ratio'] == 0.3
        assert d['total_bandwidth_gbs'] == 700.0

    def test_str_representation(self):
        """Test string representation"""
        result = MixedTrafficResult()
        result.read_ratio = 0.7
        result.write_ratio = 0.3
        result.total_bandwidth_gbs = 700.0

        s = str(result)
        assert "70%" in s or "0.7" in s
        assert "700" in s


class TestBankGroupConflictResult:
    """Tests for BankGroupConflictResult"""

    def test_default_result(self):
        """Test default BankGroupConflictResult"""
        result = BankGroupConflictResult()
        assert result.same_bank_group_requests == 0
        assert result.different_bank_group_requests == 0
        assert result.bank_group_conflicts == 0
        assert result.latency_penalty_ns == 0.0

    def test_to_dict(self):
        """Test to_dict conversion"""
        result = BankGroupConflictResult()
        result.same_bg_latency_avg_ns = 50.0
        result.different_bg_latency_avg_ns = 70.0
        result.latency_penalty_ns = 20.0
        result.conflict_rate_percent = 25.0

        d = result.to_dict()
        assert d['same_bg_latency_avg_ns'] == 50.0
        assert d['latency_penalty_ns'] == 20.0
        assert d['conflict_rate_percent'] == 25.0

    def test_str_representation(self):
        """Test string representation"""
        result = BankGroupConflictResult()
        result.same_bg_latency_avg_ns = 50.0
        result.different_bg_latency_avg_ns = 70.0
        result.latency_penalty_ns = 20.0

        s = str(result)
        assert "50" in s
        assert "70" in s
        assert "20" in s


class TestRefreshImpactResult:
    """Tests for RefreshImpactResult"""

    def test_default_result(self):
        """Test default RefreshImpactResult"""
        result = RefreshImpactResult()
        assert result.refresh_interval_ns > 0
        assert result.refresh_duration_ns > 0
        assert result.refresh_count == 0
        assert result.bandwidth_loss_percent == 0.0

    def test_to_dict(self):
        """Test to_dict conversion"""
        result = RefreshImpactResult()
        result.refresh_count = 100
        result.refresh_total_time_ns = 18000.0
        result.bandwidth_loss_percent = 2.5
        result.effective_bandwidth_gbs = 1800.0

        d = result.to_dict()
        assert d['refresh_count'] == 100
        assert d['bandwidth_loss_percent'] == 2.5
        assert d['effective_bandwidth_gbs'] == 1800.0

    def test_str_representation(self):
        """Test string representation"""
        result = RefreshImpactResult()
        result.refresh_count = 100
        result.bandwidth_loss_percent = 2.5

        s = str(result)
        assert "100" in s
        assert "2.5" in s


class TestQoSImpactResult:
    """Tests for QoSImpactResult"""

    def test_default_result(self):
        """Test default QoSImpactResult"""
        result = QoSImpactResult()
        assert result.num_qos_levels == 16
        assert result.critical_latency_ns == 0.0
        assert result.high_latency_ns == 0.0
        assert result.normal_latency_ns == 0.0
        assert result.low_latency_ns == 0.0
        assert result.starvation_detected is False

    def test_to_dict(self):
        """Test to_dict conversion"""
        result = QoSImpactResult()
        result.num_qos_levels = 16
        result.critical_latency_ns = 30.0
        result.normal_latency_ns = 50.0
        result.low_latency_ns = 80.0
        result.critical_to_normal_ratio = 1.67
        result.qos_effectiveness_percent = 75.0
        result.starvation_detected = False

        d = result.to_dict()
        assert d['num_qos_levels'] == 16
        assert d['critical_latency_ns'] == 30.0
        assert d['critical_to_normal_ratio'] == 1.67
        assert d['qos_effectiveness_percent'] == 75.0

    def test_str_representation(self):
        """Test string representation"""
        result = QoSImpactResult()
        result.critical_latency_ns = 30.0
        result.normal_latency_ns = 50.0
        result.qos_effectiveness_percent = 75.0
        result.starvation_detected = False

        s = str(result)
        assert "30" in s
        assert "50" in s
        assert "75" in s


class TestEnhancedBenchmarkEdgeCases:
    """Tests for edge cases and error handling"""

    def test_multi_channel_with_zero_requests(self):
        """Test multi-channel with minimal requests"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps", random_seed=42)
        result = benchmark.run_multi_channel_test(
            num_requests_per_channel=1,
            pattern=None
        )

        assert result.total_requests >= 1

    def test_mixed_traffic_zero_requests(self):
        """Test mixed traffic with minimal requests"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_mixed_traffic_test(
            read_ratio=0.5,
            num_requests=10
        )

        assert result.total_requests >= 0

    def test_bank_group_conflict_zero_requests(self):
        """Test bank group with minimal requests"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_bank_group_conflict_test(num_requests=5)

        assert result.total_requests >= 0

    def test_refresh_impact_short_duration(self):
        """Test refresh impact with short duration"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_refresh_impact_test(
            test_duration_ns=1_000,
            enable_refresh=True
        )

        assert result.test_duration_ns >= 0

    def test_qos_impact_minimal_requests(self):
        """Test QoS with minimal requests"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark.run_qos_impact_test(
            num_requests=10,
            high_load=True
        )

        assert result.total_requests >= 0

    def test_percentile_with_empty_data(self):
        """Test percentile calculation with empty data"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark._percentile([], 99)

        assert result == 0.0

    def test_percentile_with_single_item(self):
        """Test percentile calculation with single item"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        result = benchmark._percentile([42.0], 99)

        assert result == 42.0


class TestEnhancedBenchmarkFindings:
    """Tests for findings and warnings generation"""

    def test_generate_findings_empty_report(self):
        """Test findings with empty report"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()

        findings = benchmark._generate_findings(report)
        assert isinstance(findings, list)

    def test_generate_findings_multi_channel_high(self):
        """Test findings with high multi-channel efficiency"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.multi_channel = MultiChannelResult()
        report.multi_channel.bandwidth_efficiency_percent = 85.0

        findings = benchmark._generate_findings(report)
        assert any("Excellent" in f or "Good" in f for f in findings)

    def test_generate_findings_multi_channel_low(self):
        """Test findings with low multi-channel efficiency"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.multi_channel = MultiChannelResult()
        report.multi_channel.bandwidth_efficiency_percent = 40.0

        findings = benchmark._generate_findings(report)
        assert any("needs improvement" in f.lower() for f in findings)

    def test_generate_findings_mixed_traffic_balanced(self):
        """Test findings with balanced read/write"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.mixed_traffic = MixedTrafficResult()
        report.mixed_traffic.read_latency_avg_ns = 50.0
        report.mixed_traffic.write_latency_avg_ns = 55.0

        findings = benchmark._generate_findings(report)
        assert isinstance(findings, list)

    def test_generate_findings_bank_group_low_penalty(self):
        """Test findings with low bank group penalty"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.bank_group_conflict = BankGroupConflictResult()
        report.bank_group_conflict.latency_penalty_ns = 5.0

        findings = benchmark._generate_findings(report)
        assert isinstance(findings, list)

    def test_generate_findings_refresh_minimal(self):
        """Test findings with minimal refresh overhead"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.refresh_impact = RefreshImpactResult()
        report.refresh_impact.bandwidth_loss_percent = 1.0

        findings = benchmark._generate_findings(report)
        assert isinstance(findings, list)

    def test_generate_findings_qos_strong(self):
        """Test findings with strong QoS"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.qos_impact = QoSImpactResult()
        report.qos_impact.critical_to_normal_ratio = 2.0

        findings = benchmark._generate_findings(report)
        assert isinstance(findings, list)

    def test_generate_warnings_low_efficiency(self):
        """Test warnings with low efficiency"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.multi_channel = MultiChannelResult()
        report.multi_channel.bandwidth_efficiency_percent = 40.0

        warnings = benchmark._generate_warnings(report)
        assert any("critically low" in w.lower() for w in warnings)

    def test_generate_warnings_high_refresh_loss(self):
        """Test warnings with high refresh loss"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.refresh_impact = RefreshImpactResult()
        report.refresh_impact.bandwidth_loss_percent = 10.0

        warnings = benchmark._generate_warnings(report)
        assert any("5%" in w or "threshold" in w.lower() for w in warnings)

    def test_generate_warnings_starvation(self):
        """Test warnings with starvation"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.qos_impact = QoSImpactResult()
        report.qos_impact.starvation_detected = True

        warnings = benchmark._generate_warnings(report)
        assert any("starvation" in w.lower() for w in warnings)

    def test_generate_warnings_high_conflict(self):
        """Test warnings with high conflict rate"""
        benchmark = EnhancedBenchmark()
        report = EnhancedBenchmarkReport()
        report.bank_group_conflict = BankGroupConflictResult()
        report.bank_group_conflict.conflict_rate_percent = 50.0

        warnings = benchmark._generate_warnings(report)
        assert any("conflict" in w.lower() for w in warnings)


class TestEnhancedBenchmarkSpeedGrades:
    """Tests for different speed grades"""

    def test_8gbps_speed_grade(self):
        """Test 8Gbps speed grade"""
        benchmark = EnhancedBenchmark(speed_grade="8Gbps")
        assert benchmark.spec.data_rate_gtps == 8.0

    def test_12gbps_speed_grade(self):
        """Test 12Gbps speed grade"""
        benchmark = EnhancedBenchmark(speed_grade="12Gbps")
        assert benchmark.spec.data_rate_gtps == 12.0

    def test_16gbps_speed_grade(self):
        """Test 16Gbps speed grade"""
        benchmark = EnhancedBenchmark(speed_grade="16Gbps")
        assert benchmark.spec.data_rate_gtps == 16.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
