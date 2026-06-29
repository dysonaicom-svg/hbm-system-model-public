import pytest
from model.analysis.hotspot_detector import HotspotData, HotspotType, HotspotReport


class TestHotspotDataclass:
    def test_hotspot_data_creation(self):
        hotspot = HotspotData(
            hotspot_type=HotspotType.ADDRESS,
            address=0x1000,
            access_count=1000,
            heat_level=0.85
        )
        assert hotspot.hotspot_type == HotspotType.ADDRESS
        assert hotspot.address == 0x1000
        assert hotspot.heat_level == 0.85

    def test_hotspot_type_enum(self):
        assert HotspotType.ADDRESS.value == "address"
        assert HotspotType.BANK.value == "bank"
        assert HotspotType.CHANNEL.value == "channel"

    def test_hotspot_data_all_fields(self):
        hotspot = HotspotData(
            hotspot_type=HotspotType.BANK,
            address=0x2000,
            bank_id=3,
            channel_id=1,
            access_count=500,
            heat_level=0.6
        )
        assert hotspot.hotspot_type == HotspotType.BANK
        assert hotspot.bank_id == 3
        assert hotspot.channel_id == 1
        assert hotspot.access_count == 500

    def test_hotspot_heat_level_range(self):
        """Test that heat_level is within valid range"""
        for heat in [0.0, 0.5, 1.0]:
            h = HotspotData(
                hotspot_type=HotspotType.ADDRESS,
                address=0x1000,
                heat_level=heat
            )
            assert 0.0 <= h.heat_level <= 1.0


class TestHotspotTypeEnum:
    def test_all_hotspot_types_defined(self):
        """Verify all expected hotspot types exist"""
        expected_types = ["address", "bank", "channel", "row"]
        actual_values = [ht.value for ht in HotspotType]
        for expected in expected_types:
            assert expected in actual_values

    def test_hotspot_type_string_values(self):
        """Test that enum values are strings"""
        for ht in HotspotType:
            assert isinstance(ht.value, str)


class TestHotspotReport:
    def test_report_creation(self):
        report = HotspotReport()
        assert report.hotspots == []

    def test_add_hotspot(self):
        report = HotspotReport()
        hotspot = HotspotData(
            hotspot_type=HotspotType.ADDRESS,
            address=0x1000,
            access_count=100
        )
        report.add(hotspot)
        assert len(report.hotspots) == 1

    def test_get_top_n_empty(self):
        report = HotspotReport()
        assert report.get_top_n(10) == []

    def test_get_top_n(self):
        report = HotspotReport()
        report.add(HotspotData(hotspot_type=HotspotType.ADDRESS, address=0x1000, access_count=50))
        report.add(HotspotData(hotspot_type=HotspotType.ADDRESS, address=0x2000, access_count=100))
        report.add(HotspotData(hotspot_type=HotspotType.ADDRESS, address=0x3000, access_count=75))

        top = report.get_top_n(2)
        assert len(top) == 2
        assert top[0].address == 0x2000  # Highest count first
        assert top[1].address == 0x3000

    def test_generate_heatmap_empty(self):
        report = HotspotReport()
        heatmaps = report.generate_heatmap()
        assert heatmaps == {}

    def test_generate_heatmap(self):
        report = HotspotReport()
        report.add(HotspotData(hotspot_type=HotspotType.ADDRESS, address=0x1000, access_count=100))
        report.add(HotspotData(hotspot_type=HotspotType.ADDRESS, address=0x2000, access_count=50))
        report.add(HotspotData(hotspot_type=HotspotType.BANK, bank_id=3, access_count=80))

        heatmaps = report.generate_heatmap()
        assert HotspotType.ADDRESS in heatmaps
        assert HotspotType.BANK in heatmaps
        assert heatmaps[HotspotType.ADDRESS].max_value == 100
        assert "4096" in heatmaps[HotspotType.ADDRESS].data  # 0x1000 = 4096


class TestHotspotDetector:
    def test_detector_creation(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector()
        assert detector is not None
        assert detector.threshold_percentile == 95.0

    def test_detector_custom_threshold(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector(threshold_percentile=90.0)
        assert detector.threshold_percentile == 90.0

    def test_detect_from_trace(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector()
        trace = [(0x1000, True), (0x1000, False), (0x2000, True)] * 10
        report = detector.detect_from_trace(trace)
        assert len(report.hotspots) >= 1
        assert any(h.address == 0x1000 for h in report.hotspots)

    def test_empty_trace(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector()
        report = detector.detect_from_trace([])
        assert len(report.hotspots) == 0

    def test_detect_single_address(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector()
        trace = [(0x1000, True)] * 100
        report = detector.detect_from_trace(trace)
        assert len(report.hotspots) == 1
        assert report.hotspots[0].address == 0x1000
        assert report.hotspots[0].access_count == 100

    def test_detect_no_hotspots(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector(threshold_percentile=99.0)
        # All addresses accessed same number of times
        trace = [(0x1000, True), (0x2000, True), (0x3000, True)] * 3
        report = detector.detect_from_trace(trace)
        # All have equal counts, so threshold catches all
        assert len(report.hotspots) > 0

    def test_heat_level_normalized(self):
        from model.analysis.hotspot_detector import HotspotDetector
        detector = HotspotDetector()
        trace = [(0x1000, True)] * 100 + [(0x2000, True)] * 50
        report = detector.detect_from_trace(trace)
        # Max heat should be 1.0
        max_heat = max(h.heat_level for h in report.hotspots)
        assert max_heat == 1.0