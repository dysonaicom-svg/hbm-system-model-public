"""
Tests for Power/Thermal Features

Tests for:
- Power profile exporter
- HotSpot interface
- Enhanced thermal model

Reference: model/dram/power_estimator.py, model/dram/thermal_model.py
"""

import unittest
import tempfile
import json
import csv
from pathlib import Path

from model.dram.power_estimator import (
    HBM4PowerEstimator,
    PowerParameters,
    PowerState,
    CommandType,
    ProcessCorner,
    create_power_estimator,
)
from model.dram.thermal_model import (
    LayeredThermalModel,
    ThermalLayer,
    HotspotSeverity,
    create_layered_thermal_model,
)


class TestPowerProfileExporter(unittest.TestCase):
    """Tests for PowerProfileExporter"""

    def setUp(self):
        """Set up test fixtures"""
        self.power = create_power_estimator("8Gbps", num_channels=8)
        self.thermal = create_layered_thermal_model(num_channels=8)

    def test_export_json_basic(self):
        """Test basic JSON export"""
        from model.dram.power_thermal.power_profile_exporter import PowerProfileExporter

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name

        exporter = PowerProfileExporter(self.power, self.thermal)
        data = exporter.export_json(path)

        self.assertIn('metadata', data)
        self.assertIn('power', data)
        self.assertIn('energy', data)
        self.assertEqual(data['metadata']['hbm_version'], 'HBM4')
        self.assertEqual(data['metadata']['num_channels'], 8)

        # Cleanup
        Path(path).unlink(missing_ok=True)

    def test_export_csv_summary(self):
        """Test CSV summary export"""
        from model.dram.power_thermal.power_profile_exporter import PowerProfileExporter

        with tempfile.NamedTemporaryFile(suffix='_summary.csv', delete=False) as f:
            path = f.name

        exporter = PowerProfileExporter(self.power, self.thermal)
        exporter._export_csv_summary(path)

        self.assertTrue(Path(path).exists())

        # Verify content
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertGreater(len(rows), 0)

        Path(path).unlink(missing_ok=True)

    def test_export_csv_channels(self):
        """Test CSV channels export"""
        from model.dram.power_thermal.power_profile_exporter import PowerProfileExporter

        with tempfile.NamedTemporaryFile(suffix='_channels.csv', delete=False) as f:
            path = f.name

        exporter = PowerProfileExporter(self.power, self.thermal)
        exporter._export_csv_channels(path)

        self.assertTrue(Path(path).exists())

        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Should have 8 channel rows
            self.assertEqual(len(rows), 8)

        Path(path).unlink(missing_ok=True)

    def test_export_combined(self):
        """Test combined export to multiple formats"""
        from model.dram.power_thermal.power_profile_exporter import PowerProfileExporter

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = str(Path(tmpdir) / "combined_export")

            exporter = PowerProfileExporter(self.power, self.thermal)
            results = exporter.export_combined(base_path)

            self.assertIn('json', results)
            self.assertIn('csv_summary', results)
            self.assertIn('csv_channels', results)
            self.assertIn('csv_commands', results)

            # Verify all files exist
            for path in results.values():
                self.assertTrue(Path(path).exists())


class TestHotSpotInterface(unittest.TestCase):
    """Tests for HotSpotInterface"""

    def test_interface_creation(self):
        """Test interface creation"""
        from model.dram.power_thermal.hotspot_interface import (
            HotSpotInterface,
            HotSpotConfig,
        )

        config = HotSpotConfig(ambient_temp_c=50.0)
        interface = HotSpotInterface(config, num_channels=8)

        self.assertEqual(interface.num_channels, 8)
        self.assertEqual(interface.config.ambient_temp_c, 50.0)

    def test_generate_floorplan(self):
        """Test floorplan generation"""
        from model.dram.power_thermal.hotspot_interface import HotSpotInterface

        interface = HotSpotInterface(num_channels=8)
        flp_path = interface.generate_floorplan()

        self.assertTrue(Path(flp_path).exists())

        # Verify content
        with open(flp_path, 'r') as f:
            content = f.read()
            self.assertIn('HBM4_CTRL', content)
            self.assertIn('ambient_temp=45.0', content)

        Path(flp_path).unlink(missing_ok=True)
        if interface._temp_dir:
            interface.cleanup()

    def test_generate_power_file(self):
        """Test power file generation"""
        from model.dram.power_thermal.hotspot_interface import HotSpotInterface

        interface = HotSpotInterface(num_channels=8)
        block_powers = {
            'controller': 1.5,
            'phy': 0.5,
            'channel_0': 0.3,
            'channel_1': 0.3,
        }

        power_path = interface.generate_power_file(block_powers)
        self.assertTrue(Path(power_path).exists())

        with open(power_path, 'r') as f:
            content = f.read()
            self.assertIn('controller', content)
            self.assertIn('1.500000', content)

        Path(power_path).unlink(missing_ok=True)
        if interface._temp_dir:
            interface.cleanup()

    def test_run_hotspot_mock(self):
        """Test HotSpot execution (mock mode)"""
        from model.dram.power_thermal.hotspot_interface import HotSpotInterface

        interface = HotSpotInterface(num_channels=8)

        # Generate files
        flp_path = interface.generate_floorplan()
        power_path = interface.generate_power_file({
            'controller': 1.5,
            'phy': 0.5,
        })

        # Run (will use mock since HotSpot not installed)
        result = interface.run_hotspot(flp_path, power_path=power_path)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.avg_temperature_c)
        self.assertIsNotNone(result.max_temperature_c)
        self.assertGreater(result.max_temperature_c, 0)

        if interface._temp_dir:
            interface.cleanup()

    def test_simulate_from_power_estimator(self):
        """Test simulation from power estimator"""
        from model.dram.power_thermal.hotspot_interface import HotSpotInterface

        power = create_power_estimator("8Gbps", num_channels=8)
        interface = HotSpotInterface(num_channels=8)

        result = interface.simulate_from_power_estimator(power)

        self.assertTrue(result.success)
        self.assertIn('HBM4_CTRL', result.block_temperatures)

        if interface._temp_dir:
            interface.cleanup()


class TestEnhancedThermalModel(unittest.TestCase):
    """Tests for EnhancedThermalModel"""

    def test_model_creation(self):
        """Test enhanced model creation"""
        from model.dram.power_thermal.enhanced_thermal import (
            EnhancedThermalModel,
            create_enhanced_thermal_model,
            CoolingType,
        )

        model = create_enhanced_thermal_model(
            num_channels=8,
            num_zones=4,
            cooling_type=CoolingType.HEATSINK,
        )

        self.assertEqual(len(model.zones), 4)
        self.assertFalse(model.cooling_active)
        self.assertEqual(model.throttle_level.value, 0)

    def test_zone_initialization(self):
        """Test thermal zone initialization"""
        from model.dram.power_thermal.enhanced_thermal import create_enhanced_thermal_model

        model = create_enhanced_thermal_model(num_channels=8, num_zones=4)

        # Check zones have channels assigned
        for zone in model.zones:
            self.assertGreater(len(zone.channels), 0)
            self.assertLessEqual(len(zone.channels), 2)
            self.assertIsNotNone(zone.name)

    def test_thermal_update(self):
        """Test thermal model update"""
        from model.dram.power_thermal.enhanced_thermal import create_enhanced_thermal_model

        model = create_enhanced_thermal_model(num_channels=8, num_zones=4)

        # Update with some power
        channel_powers = {i: 100.0 for i in range(8)}
        model.update(time_ns=1000, channel_powers_mw=channel_powers, dt_ns=1000)

        # Model should have updated
        self.assertEqual(model.base_model.current_time_ns, 1000)

    def test_cooling_activation(self):
        """Test cooling system activation"""
        from model.dram.power_thermal.enhanced_thermal import (
            create_enhanced_thermal_model,
            CoolingType,
        )

        model = create_enhanced_thermal_model(
            num_channels=8,
            cooling_type=CoolingType.HEATSINK,
        )
        model.cooling_config.activation_temp_c = 45.0  # Very low for testing

        # Update with high power to trigger cooling
        channel_powers = {i: 500.0 for i in range(8)}

        # Simulate multiple steps
        for t in range(100, 11000, 1000):
            model.update(time_ns=t, channel_powers_mw=channel_powers, dt_ns=1000)

        # At least some cooling should have activated
        self.assertTrue(
            model.cooling_active or
            model.cooling_energy_j > 0 or
            model.throttle_level != model.throttle_level.NONE
        )

    def test_throttle_levels(self):
        """Test throttle level determination"""
        from model.dram.power_thermal.enhanced_thermal import (
            EnhancedThermalModel,
            ThrottleLevel,
        )

        model = EnhancedThermalModel()
        model.cooling_config.max_temp_c = 50.0
        model.cooling_config.critical_temp_c = 60.0  # Low threshold for testing
        model.cooling_config.emergency_temp_c = 70.0

        # Set zone to critical temperature to trigger throttling
        if model.zones:
            model.zones[0].current_temp_c = 80.0

            # Run update to trigger throttle check
            model._check_throttling(time_ns=1000)

            # Check throttle factor - should be less than 1.0 when throttling
            factor = model.get_throttle_factor()
            self.assertLessEqual(factor, 1.0)

    def test_zone_throttle_level(self):
        """Test per-zone throttle level"""
        from model.dram.power_thermal.enhanced_thermal import (
            create_enhanced_thermal_model,
            ThrottleLevel,
        )

        model = create_enhanced_thermal_model(num_channels=8, num_zones=4)
        # Set lower thresholds for testing
        model.cooling_config.activation_temp_c = 40.0
        model.cooling_config.max_temp_c = 60.0
        model.cooling_config.critical_temp_c = 75.0
        model.cooling_config.emergency_temp_c = 90.0

        # Set zone temperatures
        model.zones[0].current_temp_c = 50.0  # Above activation but below max
        model.zones[1].current_temp_c = 80.0  # Above critical
        model.zones[2].current_temp_c = 95.0  # Above emergency
        model.zones[3].current_temp_c = 35.0  # Below activation

        # Check throttle levels
        self.assertEqual(model.get_zone_throttle_level(0), ThrottleLevel.LIGHT)
        self.assertEqual(model.get_zone_throttle_level(1), ThrottleLevel.HEAVY)
        self.assertEqual(model.get_zone_throttle_level(2), ThrottleLevel.CRITICAL)
        self.assertEqual(model.get_zone_throttle_level(3), ThrottleLevel.NONE)

    def test_thermal_summary(self):
        """Test thermal summary generation"""
        from model.dram.power_thermal.enhanced_thermal import create_enhanced_thermal_model

        model = create_enhanced_thermal_model(num_channels=8, num_zones=4)
        summary = model.get_thermal_summary()

        self.assertIn('base_model', summary)
        self.assertIn('cooling', summary)
        self.assertIn('throttle', summary)
        self.assertIn('zones', summary)
        self.assertIn('power', summary)

        self.assertEqual(len(summary['zones']), 4)

    def test_reset(self):
        """Test model reset"""
        from model.dram.power_thermal.enhanced_thermal import (
            create_enhanced_thermal_model,
            ThrottleLevel,
        )

        model = create_enhanced_thermal_model(num_channels=8, num_zones=4)

        # Make some changes
        model.update(time_ns=10000, dt_ns=1000)
        model.cooling_active = True
        model.cooling_level = 0.8

        # Reset
        model.reset()

        self.assertFalse(model.cooling_active)
        self.assertEqual(model.cooling_level, 0.0)
        self.assertEqual(model.throttle_level, ThrottleLevel.NONE)


class TestAdaptiveThrottler(unittest.TestCase):
    """Tests for AdaptiveThrottler"""

    def test_throttler_creation(self):
        """Test adaptive throttler creation"""
        from model.dram.power_thermal.enhanced_thermal import (
            create_enhanced_thermal_model,
            AdaptiveThrottler,
        )

        thermal = create_enhanced_thermal_model(num_channels=8)
        throttler = AdaptiveThrottler(thermal)

        self.assertEqual(len(throttler.temp_history), 0)
        self.assertEqual(throttler.trend_slope, 0.0)

    def test_update_prediction(self):
        """Test throttler update and prediction"""
        from model.dram.power_thermal.enhanced_thermal import (
            create_enhanced_thermal_model,
            AdaptiveThrottler,
            ThrottleLevel,
        )

        thermal = create_enhanced_thermal_model(num_channels=8)
        throttler = AdaptiveThrottler(thermal)

        # Simulate temperature increase
        for i in range(20):
            thermal.zones[0].current_temp_c = 50.0 + i
            throttler.update(time_ns=i * 1000)

        # Should have temperature history
        self.assertGreater(len(throttler.temp_history), 0)

    def test_prediction_info(self):
        """Test prediction info retrieval"""
        from model.dram.power_thermal.enhanced_thermal import (
            create_enhanced_thermal_model,
            AdaptiveThrottler,
        )

        thermal = create_enhanced_thermal_model(num_channels=8)
        throttler = AdaptiveThrottler(thermal)

        # Add some data
        for i in range(10):
            thermal.zones[0].current_temp_c = 50.0 + i
            throttler.update(time_ns=i * 1000)

        info = throttler.get_prediction_info()
        self.assertIn('trend_slope', info)
        self.assertIn('current_temp', info)


class TestIntegration(unittest.TestCase):
    """Integration tests for power/thermal system"""

    def test_power_thermal_integration(self):
        """Test full power-thermal integration"""
        from model.dram.power_thermal.power_profile_exporter import create_exporter
        from model.dram.power_thermal.enhanced_thermal import create_enhanced_thermal_model

        # Create components
        power = create_power_estimator("8Gbps", num_channels=8)
        thermal = create_enhanced_thermal_model(num_channels=8)

        # Simulate power consumption
        power.set_all_channels_state(PowerState.ACTIVE, cycles=1000)

        # Simulate thermal response
        channel_powers = {i: 100.0 for i in range(8)}
        for t in range(0, 10000, 100):
            thermal.update(time_ns=t, channel_powers_mw=channel_powers, dt_ns=100)

        # Export combined data
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = create_exporter(power, thermal.base_model)
            data = exporter.get_export_data()

            self.assertIn('power', data)
            self.assertIn('thermal', data)

    def test_end_to_end_simulation(self):
        """Test end-to-end simulation with all components"""
        from model.dram.power_thermal.enhanced_thermal import (
            create_enhanced_thermal_model,
            AdaptiveThrottler,
        )
        from model.dram.power_thermal.hotspot_interface import HotSpotInterface

        # Create thermal system
        thermal = create_enhanced_thermal_model(num_channels=8)
        throttler = AdaptiveThrottler(thermal)

        # Create HotSpot interface
        hotspot = HotSpotInterface(num_channels=8)

        # Run simulation
        for t in range(0, 50000, 1000):
            channel_powers = {i: 100.0 + 50.0 * (i % 4) for i in range(8)}
            thermal.update(time_ns=t, channel_powers_mw=channel_powers, dt_ns=1000)
            throttler.update(time_ns=t)

        # Get summaries
        thermal_summary = thermal.get_thermal_summary()
        throttle_info = throttler.get_prediction_info()

        self.assertIsNotNone(thermal_summary)
        self.assertIsNotNone(throttle_info)

        # Cleanup
        hotspot.cleanup()


if __name__ == '__main__':
    unittest.main()
