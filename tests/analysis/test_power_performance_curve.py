import pytest
from model.analysis.power_performance_curve import PowerPerformanceCurve, CurvePoint
from model.analysis.dvfs_analyzer import DVFSAnalyzer


class TestCurvePoint:
    def test_curve_point_creation(self):
        point = CurvePoint(x=10.0, y=64.0, label="8 GT/s")
        assert point.x == 10.0
        assert point.y == 64.0
        assert point.label == "8 GT/s"

    def test_curve_point_defaults(self):
        point = CurvePoint(x=10.0, y=64.0)
        assert point.label == ""

    def test_curve_point_floating_point(self):
        point = CurvePoint(x=12.5, y=96.7)
        assert abs(point.x - 12.5) < 0.001
        assert abs(point.y - 96.7) < 0.001


class TestPowerPerformanceCurve:
    def test_initialization(self):
        curve = PowerPerformanceCurve()
        assert curve.points == []
        assert curve.pareto_points == []

    def test_generate_from_dvfs_empty(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        points = curve.generate_from_dvfs(analyzer)
        assert points == []

    def test_generate_from_dvfs_with_results(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))

        points = curve.generate_from_dvfs(analyzer)

        assert len(points) == 3
        assert all(isinstance(p, CurvePoint) for p in points)
        assert all(p.x > 0 for p in points)  # Power should be positive
        assert all(p.y > 0 for p in points)  # Bandwidth should be positive

    def test_generate_from_dvfs_labels(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))

        points = curve.generate_from_dvfs(analyzer)

        expected_labels = ["8.0 GT/s", "12.0 GT/s", "16.0 GT/s"]
        actual_labels = [p.label for p in points]
        assert actual_labels == expected_labels

    def test_generate_from_dvfs_populates_pareto_points(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))

        curve.generate_from_dvfs(analyzer)

        assert len(curve.pareto_points) == 3

    def test_generate_from_dvfs_updates_existing_points(self):
        curve = PowerPerformanceCurve()
        analyzer1 = DVFSAnalyzer()
        analyzer1.analyze_frequency_sweep((8.0, 12.0, 4.0))
        curve.generate_from_dvfs(analyzer1)
        assert len(curve.points) == 2

        analyzer2 = DVFSAnalyzer()
        analyzer2.analyze_frequency_sweep((8.0, 16.0, 8.0))
        curve.generate_from_dvfs(analyzer2)
        assert len(curve.points) == 2  # Now 8 and 16 GT/s

    def test_find_operating_point_empty(self):
        curve = PowerPerformanceCurve()
        result = curve.find_operating_point(target_performance=50.0)
        assert result is None

    def test_find_operating_point_exact_match(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 8.0))  # Only 8 and 16 GT/s
        curve.generate_from_dvfs(analyzer)

        # Find point closest to 32 GB/s (halfway between 8GT/s and 16GT/s bandwidth)
        target = analyzer.results[1].bandwidth_gbps  # 16 GT/s result
        result = curve.find_operating_point(target_performance=target)

        assert result is not None
        assert result.y == target

    def test_find_operating_point_within_tolerance(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 8.0))
        curve.generate_from_dvfs(analyzer)

        # Get exact bandwidth
        target = analyzer.results[1].bandwidth_gbps
        # Try with 5% tolerance
        result = curve.find_operating_point(target_performance=target * 0.96, tolerance=0.05)

        assert result is not None

    def test_find_operating_point_outside_tolerance(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))  # Points at 32, 48, 64 GB/s
        curve.generate_from_dvfs(analyzer)

        # Target 40 GB/s is between 32 and 48, so closest is 48 (diff=16.7%)
        result = curve.find_operating_point(target_performance=40.0, tolerance=0.01)

        assert result is None

    def test_find_operating_point_returns_best_match(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))  # Points at 32, 48, 64 GB/s
        curve.generate_from_dvfs(analyzer)

        # Target 46 GB/s is closer to 48 than 32
        # diff to 48 = 4.17%, diff to 32 = 30.4%
        result = curve.find_operating_point(target_performance=46.0)

        assert result is not None
        assert result.y == 48.0  # Should return 48 GB/s point

    def test_points_x_is_power(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 8.0))
        curve.generate_from_dvfs(analyzer)

        # Verify x values match power from DVFS results
        for i, point in enumerate(curve.points):
            assert abs(point.x - analyzer.results[i].power_w) < 0.001

    def test_points_y_is_bandwidth(self):
        curve = PowerPerformanceCurve()
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 8.0))
        curve.generate_from_dvfs(analyzer)

        # Verify y values match bandwidth from DVFS results
        for i, point in enumerate(curve.points):
            assert abs(point.y - analyzer.results[i].bandwidth_gbps) < 0.001


class TestPowerPerformanceCurveIntegration:
    def test_full_workflow(self):
        """Test complete workflow: analyze -> generate curve -> find operating point"""
        # Step 1: Analyze DVFS
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))  # Points at 32, 48, 64 GB/s

        # Step 2: Generate power-performance curve
        curve = PowerPerformanceCurve()
        curve.generate_from_dvfs(analyzer)

        # Step 3: Find operating point for target performance
        # Target 58 GB/s is closer to 64 than 48
        # diff to 64 = 10.3%, diff to 48 = 17.2%, closest is 64
        operating_point = curve.find_operating_point(target_performance=58.0, tolerance=0.11)

        assert operating_point is not None
        assert operating_point.y == 64.0  # Best match

    def test_pareto_points_linked_to_dvfs_results(self):
        """Verify Pareto points correspond to DVFS results"""
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))

        curve = PowerPerformanceCurve()
        curve.generate_from_dvfs(analyzer)

        # All Pareto points should reference valid DVFS results
        for pp in curve.pareto_points:
            assert pp.dvfs_result in analyzer.results

    def test_power_performance_tradeoff(self):
        """Verify higher power correlates with higher performance"""
        analyzer = DVFSAnalyzer()
        analyzer.analyze_frequency_sweep((8.0, 16.0, 4.0))

        curve = PowerPerformanceCurve()
        curve.generate_from_dvfs(analyzer)

        # Sort by power
        sorted_by_power = sorted(curve.points, key=lambda p: p.x)

        # Higher power should mean higher bandwidth
        for i in range(len(sorted_by_power) - 1):
            assert sorted_by_power[i + 1].y >= sorted_by_power[i].y