import pytest
from model.analysis.latency_analyzer import LatencyStats, LatencyDistribution


class TestLatencyDistribution:
    def test_empty_distribution(self):
        dist = LatencyDistribution()
        stats = dist.analyze()
        assert stats.sample_count == 0

    def test_single_sample(self):
        dist = LatencyDistribution()
        dist.add_sample(100.0)
        stats = dist.analyze()
        assert stats.mean_ns == 100.0
        assert stats.sample_count == 1

    def test_percentiles(self):
        dist = LatencyDistribution()
        for i in range(100):
            dist.add_sample(float(i))
        stats = dist.analyze()
        assert 49 <= stats.p50_ns <= 51
        assert 89 <= stats.p90_ns <= 91

    def test_min_max(self):
        dist = LatencyDistribution()
        dist.add_sample(10.0)
        dist.add_sample(50.0)
        dist.add_sample(100.0)
        stats = dist.analyze()
        assert stats.min_ns == 10.0
        assert stats.max_ns == 100.0

    def test_median(self):
        dist = LatencyDistribution()
        for v in [1, 2, 3, 4, 5]:
            dist.add_sample(float(v))
        stats = dist.analyze()
        assert stats.median_ns == 3.0

    def test_std_dev(self):
        dist = LatencyDistribution()
        for _ in range(10):
            dist.add_sample(100.0)
        stats = dist.analyze()
        assert stats.std_dev_ns == 0.0

    def test_histogram(self):
        dist = LatencyDistribution()
        for i in range(100):
            dist.add_sample(float(i))
        centers, counts = dist.get_histogram(bins=10)
        assert len(centers) == 10
        assert sum(counts) == 100

    def test_histogram_empty(self):
        dist = LatencyDistribution()
        centers, counts = dist.get_histogram(bins=10)
        assert centers == []
        assert counts == []

    def test_histogram_single_value(self):
        dist = LatencyDistribution()
        for _ in range(5):
            dist.add_sample(100.0)
        centers, counts = dist.get_histogram(bins=10)
        assert centers == [100.0]
        assert counts == [5]

    def test_custom_percentiles(self):
        dist = LatencyDistribution()
        for i in range(100):
            dist.add_sample(float(i))
        pcts = dist.get_percentiles([25, 50, 75])
        assert 24 <= pcts[25] <= 26
        assert 49 <= pcts[50] <= 51
        assert 74 <= pcts[75] <= 76

    def test_empty_custom_percentiles(self):
        dist = LatencyDistribution()
        pcts = dist.get_percentiles([50, 90])
        assert pcts[50] == 0.0
        assert pcts[90] == 0.0

    def test_p95_p99(self):
        dist = LatencyDistribution()
        for i in range(1000):
            dist.add_sample(float(i))
        stats = dist.analyze()
        assert 940 <= stats.p95_ns <= 960
        assert 980 <= stats.p99_ns <= 999

    def test_dataclass_fields(self):
        stats = LatencyStats()
        assert stats.min_ns == 0.0
        assert stats.max_ns == 0.0
        assert stats.mean_ns == 0.0
        assert stats.median_ns == 0.0
        assert stats.p50_ns == 0.0
        assert stats.p90_ns == 0.0
        assert stats.p95_ns == 0.0
        assert stats.p99_ns == 0.0
        assert stats.std_dev_ns == 0.0
        assert stats.sample_count == 0
