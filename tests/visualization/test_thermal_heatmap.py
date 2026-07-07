"""Tests for thermal_heatmap module"""

import pytest
from sim.visualization.thermal_heatmap import ThermalHeatmap


class TestThermalHeatmap:
    def test_heatmap_creation(self):
        hm = ThermalHeatmap(rows=8, cols=16)
        assert hm.rows == 8
        assert hm.cols == 16

    def test_set_cell(self):
        hm = ThermalHeatmap(rows=4, cols=4)
        hm.set_cell(0, 0, 75.0)
        assert hm.cells[0][0] == 75.0

    def test_set_from_dict(self):
        hm = ThermalHeatmap(rows=4, cols=4)
        hm.set_from_dict({(0, 0): 70.0, (1, 1): 80.0})
        assert hm.cells[0][0] == 70.0
        assert hm.cells[1][1] == 80.0

    def test_get_heat_level(self):
        hm = ThermalHeatmap()
        hm.min_temp = 25.0
        hm.max_temp = 85.0

        assert hm.get_heat_level(25.0) == 0.0
        assert hm.get_heat_level(85.0) == 1.0
        assert abs(hm.get_heat_level(55.0) - 0.5) < 0.01

    def test_temp_to_char(self):
        hm = ThermalHeatmap()
        cold_char = hm._temp_to_char(25.0)
        hot_char = hm._temp_to_char(85.0)
        assert cold_char != hot_char

    def test_generate(self):
        hm = ThermalHeatmap(rows=4, cols=4)
        hm.set_cell(0, 0, 50.0)
        hm.set_cell(3, 3, 80.0)

        output = hm.generate(show_values=True)
        assert "THERMAL" in output
        assert "ROW" in output

    def test_generate_bank_heatmap(self):
        hm = ThermalHeatmap()
        output = hm.generate_bank_heatmap(num_banks=128)
        assert "THERMAL" in output

    def test_generate_channel_heatmap(self):
        hm = ThermalHeatmap()
        output = hm.generate_channel_heatmap(num_channels=16)
        assert "CHANNEL" in output

    def test_get_hotspots(self):
        hm = ThermalHeatmap(rows=4, cols=4)
        hm.set_cell(0, 0, 80.0)  # Hot
        hm.set_cell(1, 1, 40.0)  # Not hot

        hotspots = hm.get_hotspots(threshold=0.7)
        assert len(hotspots) == 1
        assert hotspots[0][:2] == (0, 0)

    def test_get_summary_stats(self):
        hm = ThermalHeatmap(rows=2, cols=2)
        hm.set_cell(0, 0, 30.0)
        hm.set_cell(0, 1, 80.0)
        hm.set_cell(1, 0, 50.0)
        hm.set_cell(1, 1, 60.0)

        stats = hm.get_summary_stats()
        assert stats["min"] == 30.0
        assert stats["max"] == 80.0
        assert stats["avg"] == 55.0
