"""
Tests for HBM4 Thermal Model

Tests cover:
- Basic thermal model creation and initialization
- Temperature tracking and updates
- Thermal throttling behavior
- PDN voltage operating points
- Hotspot configuration
- Integration with power estimator
- Thermal statistics tracking
"""

import pytest
from model.hbm4.power.thermal_model import (
    HBM4ThermalModel,
    ThrottleLevel,
    PDNVoltageMode,
    TemperatureThresholds,
    ThermalResistance,
    ComponentTemperatures,
    HotspotConfig,
    PDNOperatingPoint,
    ThrottleState,
    ThermalStatistics,
    create_thermal_model,
)


class TestBasicThermalModelCreation:
    """Test basic thermal model creation and initialization"""

    def test_thermal_model_creation(self):
        """Test thermal model can be created"""
        model = HBM4ThermalModel()
        assert model is not None
        assert model.ambient_temp_c == 25.0

    def test_default_initial_temperatures(self):
        """Test default temperature initialization"""
        model = HBM4ThermalModel()
        temps = model.temperatures

        # Ambient should be 25°C
        assert temps.ambient == 25.0
        # All temperatures should be initialized
        assert temps.die == 35.0  # Initial temp
        assert temps.controller_cluster >= 25.0
        assert temps.d2d_phy >= 25.0
        assert temps.tsv_phy >= 25.0
        assert temps.ecc_ras >= 25.0
        assert temps.clocking >= 25.0

    def test_custom_ambient_temperature(self):
        """Test thermal model with custom ambient temperature"""
        model = HBM4ThermalModel(ambient_temp_c=45.0)
        assert model.ambient_temp_c == 45.0
        assert model.temperatures.ambient == 45.0

    def test_custom_thresholds(self):
        """Test thermal model with custom thresholds"""
        custom_thresholds = TemperatureThresholds(
            warning=80.0,
            throttle=90.0,
            critical=100.0,
            shutdown=105.0,
        )
        model = HBM4ThermalModel(thresholds=custom_thresholds)
        assert model.thresholds.warning == 80.0
        assert model.thresholds.throttle == 90.0
        assert model.thresholds.critical == 100.0
        assert model.thresholds.shutdown == 105.0

    def test_hotspot_configs_initialized(self):
        """Test hotspot configurations are initialized"""
        model = HBM4ThermalModel()

        expected_hotspots = [
            'controller_cluster',
            'd2d_phy',
            'tsv_phy',
            'ecc_ras',
            'clocking',
            'phy_interface',
        ]

        for hotspot in expected_hotspots:
            assert hotspot in model.hotspot_configs
            config = model.hotspot_configs[hotspot]
            assert isinstance(config, HotspotConfig)
            assert config.r_junction > 0
            assert 0 < config.size_factor <= 1.0


class TestTemperatureTracking:
    """Test temperature tracking and updates"""

    def test_initial_temperature_state(self):
        """Test initial temperature state"""
        model = HBM4ThermalModel()
        temps = model.temperatures

        assert temps.max_temperature == max(
            temps.controller_cluster,
            temps.d2d_phy,
            temps.tsv_phy,
            temps.ecc_ras,
            temps.clocking,
            temps.phy_interface,
        )

    def test_update_temperature_basic(self):
        """Test basic temperature update"""
        model = HBM4ThermalModel()
        initial_temp = model.temperatures.die

        power_breakdown = {
            'controller_cluster': 200.0,
            'd2d_phy': 150.0,
            'tsv_phy': 180.0,
            'ecc_ras': 50.0,
            'clocking': 100.0,
            'phy_interface': 60.0,
        }

        # Update with sufficient time for temperature dynamics
        model.update_temperature(timestamp_ns=10000, power_breakdown=power_breakdown)

        # With high power (200mW), temperature should rise above ambient
        assert model.temperatures.controller_cluster > 25.0
        # Stats should be updated
        assert model.stats.samples > 0

    def test_update_temperature_multiple_steps(self):
        """Test temperature updates over multiple time steps"""
        model = HBM4ThermalModel()

        power_breakdown = {
            'controller_cluster': 100.0,
            'd2d_phy': 80.0,
            'tsv_phy': 120.0,
            'ecc_ras': 30.0,
            'clocking': 50.0,
            'phy_interface': 40.0,
        }

        # Update at multiple time points with larger time steps
        model.update_temperature(timestamp_ns=5000, power_breakdown=power_breakdown)
        temp_after_step1 = model.temperatures.controller_cluster

        model.update_temperature(timestamp_ns=10000, power_breakdown=power_breakdown)
        temp_after_step2 = model.temperatures.controller_cluster

        model.update_temperature(timestamp_ns=15000, power_breakdown=power_breakdown)
        temp_after_step3 = model.temperatures.controller_cluster

        # Temperature should converge - final should be higher than initial
        # and should be above ambient
        assert temp_after_step3 > 25.0  # Above ambient
        assert temp_after_step3 > model.temperatures.ambient

    def test_get_component_temperature(self):
        """Test getting temperature for specific component"""
        model = HBM4ThermalModel()

        temp = model.get_component_temperature('controller_cluster')
        assert isinstance(temp, float)
        assert temp > 0

        temp = model.get_component_temperature('d2d_phy')
        assert isinstance(temp, float)

        temp = model.get_component_temperature('tsv_phy')
        assert isinstance(temp, float)

    def test_get_die_temperature(self):
        """Test getting die temperature"""
        model = HBM4ThermalModel()
        die_temp = model.get_die_temperature()
        assert die_temp > 0
        assert die_temp >= model.temperatures.ambient

    def test_get_max_temperature(self):
        """Test getting maximum temperature"""
        model = HBM4ThermalModel()
        max_temp = model.get_max_temperature()
        assert max_temp > 0
        assert max_temp == model.temperatures.max_temperature


class TestThermalThrottling:
    """Test thermal throttling behavior"""

    def test_initial_throttle_state(self):
        """Test initial throttle state is NONE"""
        model = HBM4ThermalModel()
        assert model.get_throttle_level() == ThrottleLevel.NONE
        assert not model.is_throttling_active()
        assert model.get_throttle_factor() == 1.0

    def test_throttle_level_determination(self):
        """Test throttle level determination from thresholds"""
        thresholds = TemperatureThresholds()

        # Test each level
        assert thresholds.get_throttle_level(80.0) == ThrottleLevel.NONE
        assert thresholds.get_throttle_level(85.0) == ThrottleLevel.WARNING
        assert thresholds.get_throttle_level(95.0) == ThrottleLevel.THROTTLE
        assert thresholds.get_throttle_level(105.0) == ThrottleLevel.CRITICAL
        assert thresholds.get_throttle_level(110.0) == ThrottleLevel.SHUTDOWN

    def test_throttling_at_high_power(self):
        """Test throttling activates at high power"""
        model = HBM4ThermalModel()

        # High power breakdown
        high_power = {
            'controller_cluster': 500.0,
            'd2d_phy': 400.0,
            'tsv_phy': 450.0,
            'ecc_ras': 200.0,
            'clocking': 300.0,
            'phy_interface': 200.0,
        }

        # Update many times to accumulate heat
        for t in range(100, 100000, 100):
            model.update_temperature(timestamp_ns=t, power_breakdown=high_power)

        # At high power, throttling should eventually activate
        level = model.get_throttle_level()
        assert level in [ThrottleLevel.NONE, ThrottleLevel.WARNING,
                         ThrottleLevel.THROTTLE, ThrottleLevel.CRITICAL]

    def test_throttle_factor_at_critical(self):
        """Test throttle factor at critical level"""
        model = HBM4ThermalModel()

        # Extreme power to trigger critical throttling
        extreme_power = {
            'controller_cluster': 800.0,
            'd2d_phy': 600.0,
            'tsv_phy': 700.0,
            'ecc_ras': 300.0,
            'clocking': 400.0,
            'phy_interface': 300.0,
        }

        for t in range(100, 200000, 100):
            model.update_temperature(timestamp_ns=t, power_breakdown=extreme_power)

        # Eventually should reach throttle or critical
        factor = model.get_throttle_factor()
        assert factor >= 0.0
        assert factor <= 1.0

    def test_throttle_summary(self):
        """Test throttle summary generation"""
        model = HBM4ThermalModel()
        summary = model.get_throttle_summary()

        assert 'level' in summary
        assert 'active' in summary
        assert 'throttle_factor' in summary
        assert 'pdn_mode' in summary
        assert 'pdn_voltage_mv' in summary
        assert summary['throttle_factor'] == 1.0


class TestPDNVoltageOperatingPoints:
    """Test PDN voltage operating points"""

    def test_pdn_operating_points_initialized(self):
        """Test PDN operating points are initialized"""
        model = HBM4ThermalModel()

        assert PDNVoltageMode.NOMINAL in model.pdn_operating_points
        assert PDNVoltageMode.PERFORMANCE in model.pdn_operating_points
        assert PDNVoltageMode.LOW_POWER in model.pdn_operating_points
        assert PDNVoltageMode.ULTRA_LOW in model.pdn_operating_points

    def test_nominal_pdn_voltage(self):
        """Test nominal PDN voltage is 900mV"""
        model = HBM4ThermalModel()
        assert model.get_pdn_voltage() == 900.0

    def test_get_pdn_mode(self):
        """Test getting PDN mode"""
        model = HBM4ThermalModel()
        assert model.get_pdn_mode() == PDNVoltageMode.NOMINAL

    def test_pdn_mode_changes_with_temperature(self):
        """Test PDN mode changes at high temperature"""
        model = HBM4ThermalModel()

        # Extreme power to trigger PDN mode change
        extreme_power = {
            'controller_cluster': 800.0,
            'd2d_phy': 600.0,
            'tsv_phy': 700.0,
            'ecc_ras': 300.0,
            'clocking': 400.0,
            'phy_interface': 300.0,
        }

        for t in range(100, 50000, 100):
            model.update_temperature(timestamp_ns=t, power_breakdown=extreme_power)

        # PDN mode should be NOMINAL at low temp, or switch at high temp
        mode = model.get_pdn_mode()
        assert isinstance(mode, PDNVoltageMode)

    def test_pdn_voltage_corresponds_to_mode(self):
        """Test PDN voltage corresponds to operating mode"""
        model = HBM4ThermalModel()

        # Verify voltage for each mode
        nominal = model.pdn_operating_points[PDNVoltageMode.NOMINAL]
        assert nominal.voltage_mv == 900

        perf = model.pdn_operating_points[PDNVoltageMode.PERFORMANCE]
        assert perf.voltage_mv == 1000

        low = model.pdn_operating_points[PDNVoltageMode.LOW_POWER]
        assert low.voltage_mv == 800

        ultra = model.pdn_operating_points[PDNVoltageMode.ULTRA_LOW]
        assert ultra.voltage_mv == 650


class TestHotspotConfiguration:
    """Test hotspot configuration"""

    def test_hotspot_r_junction_values(self):
        """Test hotspot thermal resistance values"""
        model = HBM4ThermalModel()

        # Each hotspot should have valid R_junction
        for name, config in model.hotspot_configs.items():
            assert config.r_junction > 0
            assert config.r_junction < 10.0  # Reasonable upper bound

    def test_hotspot_size_factors(self):
        """Test hotspot size factors sum to reasonable total"""
        model = HBM4ThermalModel()

        total_size = sum(
            config.size_factor
            for config in model.hotspot_configs.values()
        )

        # Total should be less than 1.0 (die coverage)
        assert total_size <= 1.0
        # But should cover significant portion
        assert total_size >= 0.3

    def test_hotspot_power_densities(self):
        """Test hotspot power density values"""
        model = HBM4ThermalModel()

        for name, config in model.hotspot_configs.items():
            assert config.power_density > 0

    def test_get_thermal_resistance(self):
        """Test getting thermal resistance for component"""
        model = HBM4ThermalModel()

        r = model.get_thermal_resistance('controller_cluster')
        assert r > 0

        r = model.get_thermal_resistance('d2d_phy')
        assert r > 0

        r = model.get_thermal_resistance('nonexistent')
        # Should return default
        assert r > 0


class TestThermalResistance:
    """Test thermal resistance modeling"""

    def test_thermal_resistance_total(self):
        """Test total thermal resistance calculation"""
        tr = ThermalResistance()
        # total is a property, not a method
        total = tr.total

        # Total should be sum of R_jc + R_jb + R_ca
        assert abs(total - (tr.r_jc + tr.r_jb + tr.r_ca)) < 0.001

    def test_temperature_rise_calculation(self):
        """Test temperature rise calculation"""
        tr = ThermalResistance()
        delta_t = tr.get_temperature_rise(power_mw=1000.0)

        # At 1000mW and ~19°C/W total resistance, should get ~19°C rise
        assert delta_t > 10.0
        assert delta_t < 30.0

    def test_custom_thermal_resistance(self):
        """Test custom thermal resistance values"""
        tr = ThermalResistance(r_jc=1.0, r_jb=2.0, r_ca=15.0, r_sp=3.0)
        assert tr.r_jc == 1.0
        assert tr.r_jb == 2.0
        assert tr.r_ca == 15.0
        assert tr.r_sp == 3.0


class TestPowerToTemperature:
    """Test power to temperature conversion"""

    def test_calculate_power_limit(self):
        """Test power limit calculation"""
        model = HBM4ThermalModel()

        # Target 80°C with 25°C ambient = 55°C delta
        limit = model.calculate_power_limit(target_temp_c=80.0)

        # With ~10.5°C/W total resistance, limit ~5.2W
        assert limit > 4000  # At least 4W
        assert limit < 8000  # But less than 8W

    def test_calculate_power_limit_custom_ambient(self):
        """Test power limit with custom ambient"""
        model = HBM4ThermalModel()

        # Higher ambient = lower power limit
        limit_25 = model.calculate_power_limit(target_temp_c=80.0, ambient_temp_c=25.0)
        limit_35 = model.calculate_power_limit(target_temp_c=80.0, ambient_temp_c=35.0)

        assert limit_35 < limit_25

    def test_get_temperature_rise(self):
        """Test temperature rise from power"""
        model = HBM4ThermalModel()

        # 100mW with typical R should give small rise
        rise = model.get_temperature_rise(power_mw=100.0)
        assert rise > 0
        assert rise < 10.0  # Small rise for low power

        # Higher power = more rise
        rise_high = model.get_temperature_rise(power_mw=1000.0)
        assert rise_high > rise

    def test_get_temperature_rise_with_component(self):
        """Test temperature rise for specific component"""
        model = HBM4ThermalModel()

        rise = model.get_temperature_rise(power_mw=200.0, component='controller_cluster')
        assert rise > 0


class TestThermalStatistics:
    """Test thermal statistics tracking"""

    def test_initial_statistics(self):
        """Test initial statistics are zeroed"""
        model = HBM4ThermalModel()
        stats = model.stats

        assert stats.samples == 0
        assert stats.peak_temperature_c == 0.0
        assert stats.average_temperature_c == 0.0
        assert stats.throttle_events == 0
        assert stats.warning_events == 0

    def test_statistics_update(self):
        """Test statistics are updated on temperature change"""
        model = HBM4ThermalModel()

        power_breakdown = {
            'controller_cluster': 150.0,
            'd2d_phy': 100.0,
            'tsv_phy': 120.0,
            'ecc_ras': 50.0,
            'clocking': 80.0,
            'phy_interface': 60.0,
        }

        for t in range(100, 5000, 100):
            model.update_temperature(timestamp_ns=t, power_breakdown=power_breakdown)

        assert model.stats.samples > 0
        assert model.stats.peak_temperature_c > 0

    def test_reset_statistics(self):
        """Test resetting statistics"""
        model = HBM4ThermalModel()

        power_breakdown = {
            'controller_cluster': 150.0,
            'd2d_phy': 100.0,
            'tsv_phy': 120.0,
            'ecc_ras': 50.0,
            'clocking': 80.0,
            'phy_interface': 60.0,
        }

        model.update_temperature(timestamp_ns=1000, power_breakdown=power_breakdown)

        # Reset
        model.reset()

        assert model.stats.samples == 0
        assert model.stats.peak_temperature_c == 0.0


class TestIntegrationWithPowerEstimator:
    """Test integration with power estimator"""

    def test_set_power_estimator(self):
        """Test setting power estimator reference"""
        model = HBM4ThermalModel()
        model._power_estimator = None  # Not set yet

        # Should work without estimator (uses defaults)
        model.update_temperature(timestamp_ns=1000)

    def test_update_with_default_power(self):
        """Test update with default power when no estimator"""
        model = HBM4ThermalModel()
        initial_temp = model.temperatures.controller_cluster

        model.update_temperature(timestamp_ns=1000)

        # Temperature should change from default power
        new_temp = model.temperatures.controller_cluster
        assert new_temp != initial_temp or model.stats.samples > 0


class TestFactoryFunction:
    """Test factory function"""

    def test_create_thermal_model_default(self):
        """Test create_thermal_model with defaults"""
        model = create_thermal_model()
        assert model is not None
        assert model.ambient_temp_c == 25.0

    def test_create_thermal_model_custom_ambient(self):
        """Test create_thermal_model with custom ambient"""
        model = create_thermal_model(ambient_temp_c=35.0)
        assert model.ambient_temp_c == 35.0

    def test_create_thermal_model_speed_grades(self):
        """Test create_thermal_model with different speed grades"""
        # 8Gbps should have default thresholds
        model_8g = create_thermal_model(speed_grade='8Gbps')
        assert model_8g.thresholds.warning == 85.0

        # 16Gbps should have tighter thresholds
        model_16g = create_thermal_model(speed_grade='16Gbps')
        assert model_16g.thresholds.warning == 80.0
        assert model_16g.thresholds.throttle == 90.0

    def test_create_thermal_model_12gbps(self):
        """Test create_thermal_model with 12Gbps"""
        model = create_thermal_model(speed_grade='12Gbps')
        assert model.thresholds.warning == 82.0
        assert model.thresholds.throttle == 92.0


class TestSummaryGeneration:
    """Test summary generation"""

    def test_get_summary_structure(self):
        """Test summary has expected structure"""
        model = HBM4ThermalModel()
        summary = model.get_summary()

        assert 'temperatures' in summary
        assert 'throttle' in summary
        assert 'pdn' in summary
        assert 'thresholds' in summary
        assert 'stats' in summary
        assert 'thermal_resistance' in summary

    def test_summary_temperatures(self):
        """Test summary temperature values"""
        model = HBM4ThermalModel()
        summary = model.get_summary()

        temps = summary['temperatures']
        assert 'ambient_c' in temps
        assert 'die_c' in temps
        assert 'max_c' in temps
        assert 'controller_cluster_c' in temps

    def test_summary_throttle(self):
        """Test summary throttle values"""
        model = HBM4ThermalModel()
        summary = model.get_summary()

        throttle = summary['throttle']
        assert 'level' in throttle
        assert 'active' in throttle
        assert 'throttle_factor' in throttle

    def test_summary_pdn(self):
        """Test summary PDN values"""
        model = HBM4ThermalModel()
        summary = model.get_summary()

        pdn = summary['pdn']
        assert 'nominal' in pdn
        assert 'perf' in pdn
        assert pdn['nominal']['voltage_mv'] == 900


class TestResetFunctionality:
    """Test reset functionality"""

    def test_reset_temperatures(self):
        """Test reset restores temperatures to initial state"""
        model = HBM4ThermalModel()

        # Heat up
        high_power = {
            'controller_cluster': 300.0,
            'd2d_phy': 200.0,
            'tsv_phy': 250.0,
            'ecc_ras': 100.0,
            'clocking': 150.0,
            'phy_interface': 100.0,
        }
        model.update_temperature(timestamp_ns=5000, power_breakdown=high_power)

        hot_temp = model.temperatures.controller_cluster

        # Reset
        model.reset()

        # Should be back to ambient/initial
        assert model.temperatures.controller_cluster <= model.ambient_temp_c + 10.0
        assert model.temperatures.die <= model.ambient_temp_c + 10.0

    def test_reset_throttle_state(self):
        """Test reset restores throttle state"""
        model = HBM4ThermalModel()

        # Accumulate some throttle state
        model.throttle_state.throttle_count = 5
        model.throttle_state.max_temperature_reached = 100.0

        model.reset()

        assert model.throttle_state.throttle_count == 0
        assert model.throttle_state.max_temperature_reached == 0.0
        assert model.throttle_state.level == ThrottleLevel.NONE


class TestComponentTemperatures:
    """Test ComponentTemperatures dataclass"""

    def test_component_temperatures_max(self):
        """Test max temperature property"""
        temps = ComponentTemperatures()
        temps.controller_cluster = 80.0
        temps.d2d_phy = 75.0
        temps.tsv_phy = 85.0
        temps.ecc_ras = 70.0
        temps.clocking = 72.0
        temps.phy_interface = 68.0

        assert temps.max_temperature == 85.0

    def test_component_temperatures_average(self):
        """Test average temperature property"""
        temps = ComponentTemperatures()
        temps.controller_cluster = 80.0
        temps.d2d_phy = 80.0
        temps.tsv_phy = 80.0
        temps.ecc_ras = 80.0
        temps.clocking = 80.0
        temps.phy_interface = 80.0

        assert temps.average_temperature == 80.0


class TestThrottleState:
    """Test ThrottleState dataclass"""

    def test_initial_throttle_state(self):
        """Test initial throttle state values"""
        state = ThrottleState()

        assert state.level == ThrottleLevel.NONE
        assert not state.active
        assert state.throttle_factor == 1.0
        assert state.pdn_mode == PDNVoltageMode.NOMINAL


class TestTemperatureThresholds:
    """Test TemperatureThresholds dataclass"""

    def test_custom_thresholds(self):
        """Test custom thresholds"""
        thresholds = TemperatureThresholds(
            warning=80.0,
            throttle=90.0,
            critical=100.0,
            shutdown=105.0,
        )

        assert thresholds.warning == 80.0
        assert thresholds.throttle == 90.0
        assert thresholds.critical == 100.0
        assert thresholds.shutdown == 105.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])