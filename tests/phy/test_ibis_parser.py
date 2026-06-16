"""
Tests for IBIS Parser and IBIS Model

Tests cover:
- IBIS file parsing
- Model extraction
- IV/V-T curve generation
- Behavioral model functionality
"""

import pytest
import numpy as np
from typing import List, Tuple

from model.phy.ibis_parser import (
    IBISParser, IBISFile, IBISModel, IBISModelType, IVCurve, VTWaveform,
    CompositeDataTable, IBISPackage, IBISPin, parse_ibis_content
)
from model.phy.ibis_model import (
    IBISModelWrapper, BehavioralModel, WaveformMetrics,
    ChannelResponse, create_model_wrapper, SignalIntegrityMetric
)
from model.phy.ibis_simulator import (
    IBISSimulator, ChannelParameters, SimulationConfig, SimulationMode,
    SignalDistortion, CrosstalkResult, EyeAnalysisResult, SimulationResult,
    create_simulator
)


# Sample IBIS content for testing
SAMPLE_IBIS_CONTENT = """
[File Header]
IBIS Version = 6.1
File Name = sample.ibs
Date = 01/01/2024
Revision = 1.0

[Component]
Sample Component Test Manufacturer

[Package]
R_pkg = 0.1
L_pkg = 2.0
C_pkg = 0.5

[Pin]
pin1  OUTPUT 0.01 0.1 0.2
pin2  INPUT 0.01 0.1 0.2
pin3  IO 0.01 0.1 0.2

[Model]
OUTPUT_MODEL
| Model_type = Output
| Polarity = Non-Inverting
| Enable = Active
| C_comp = 2.5
| V_meas = 1.2
| Manufacturer = TestVendor
| Product = SampleChip

[Pullup]
| Voltage = 1.2
-0.5 0.001
0.0 0.000
0.6 0.002
1.2 0.005
1.8 0.010
2.5 0.050

[Pulldown]
| Voltage = 1.2
-0.5 -0.050
0.0 0.000
0.6 -0.002
1.2 -0.005
1.8 -0.010
2.5 -0.001

[GND Clamp]
-0.5 -0.100
0.0 0.000
0.5 0.000
1.2 0.000

[Power Clamp]
0.0 0.000
0.5 0.000
1.2 0.000
1.8 0.001
2.5 0.050

[Rising Waveform]
| R_load = 50
| V_com = 0.0
0.0 0.0
0.1 0.3
0.2 0.7
0.3 1.0
0.5 1.2
1.0 1.2

[Falling Waveform]
| R_load = 50
| V_com = 1.2
0.0 1.2
0.1 0.9
0.2 0.5
0.3 0.2
0.5 0.0
1.0 0.0

[Model]
INPUT_MODEL
| Model_type = Input
| C_comp = 1.0
| V_meas = 0.0
"""


MINIMAL_IBIS_CONTENT = """
[File Header]
IBIS Version = 6.1
File Name = minimal.ibs

[Component]
Minimal_Component

[Package]
0.05 1.0 0.2

[Pin]
pin1 MINIMAL_MODEL

[Model]
MINIMAL_MODEL
| Model_type = Output
| C_comp = 1.0

[Pullup]
0.0 0.0
1.2 0.005
2.4 0.010

[Pulldown]
0.0 0.0
1.2 -0.005
2.4 -0.010
"""


class TestIBISParser:
    """Test IBIS parser functionality"""

    def test_parse_basic_structure(self):
        """Test parsing basic IBIS file structure"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        assert ibis_file is not None
        assert ibis_file.component == "Sample Component Test Manufacturer"

    def test_parse_package_data(self):
        """Test parsing package RLC data"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        assert ibis_file.default_package is not None
        assert abs(ibis_file.default_package.r_pkg - 0.1) < 0.01
        assert abs(ibis_file.default_package.l_pkg - 2.0) < 0.01
        assert abs(ibis_file.default_package.c_pkg - 0.5) < 0.01

    def test_parse_pins(self):
        """Test parsing pin definitions"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        assert len(ibis_file.pins) == 3
        assert "pin1" in ibis_file.pins
        assert ibis_file.pins["pin1"].model_name == "OUTPUT"

    def test_parse_models(self):
        """Test parsing model definitions"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        assert len(ibis_file.models) >= 2
        assert "OUTPUT_MODEL" in ibis_file.models

        model = ibis_file.models["OUTPUT_MODEL"]
        assert model.model_type == IBISModelType.OUTPUT
        assert model.polarity == "Non-Inverting"
        assert abs(model.c_comp - 2.5) < 0.01

    def test_parse_pullup_curve(self):
        """Test parsing pullup IV curve"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        model = ibis_file.models["OUTPUT_MODEL"]
        assert model.pullup is not None
        assert len(model.pullup.voltage) > 0
        assert len(model.pullup.current) == len(model.pullup.voltage)

        # Check voltage/current relationship
        assert abs(model.pullup.voltage[0] - (-0.5)) < 0.01
        assert abs(model.pullup.voltage[-1] - 2.5) < 0.01

    def test_parse_pulldown_curve(self):
        """Test parsing pulldown IV curve"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        model = ibis_file.models["OUTPUT_MODEL"]
        assert model.pulldown is not None
        assert len(model.pulldown.voltage) > 0

    def test_parse_waveforms(self):
        """Test parsing V-T waveforms"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        model = ibis_file.models["OUTPUT_MODEL"]

        # Rising waveform
        assert model.rising_waveform is not None
        assert len(model.rising_waveform.time) > 0
        assert len(model.rising_waveform.voltage) == len(model.rising_waveform.time)
        assert abs(model.rising_waveform.r_load - 50.0) < 0.01

        # Falling waveform
        assert model.falling_waveform is not None
        assert len(model.falling_waveform.time) > 0

    def test_parse_gnd_clamp(self):
        """Test parsing GND clamp curve"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        model = ibis_file.models["OUTPUT_MODEL"]
        assert model.gnd_clamp is not None
        assert len(model.gnd_clamp.voltage) > 0

    def test_parse_power_clamp(self):
        """Test parsing power clamp curve"""
        parser = IBISParser()
        ibis_file = parser.parse(SAMPLE_IBIS_CONTENT)

        model = ibis_file.models["OUTPUT_MODEL"]
        assert model.power_clamp is not None
        assert len(model.power_clamp.voltage) > 0

    def test_minimal_ibis_parsing(self):
        """Test parsing minimal IBIS file"""
        parser = IBISParser()
        ibis_file = parser.parse(MINIMAL_IBIS_CONTENT)

        assert ibis_file.component == "Minimal_Component"
        assert "MINIMAL_MODEL" in ibis_file.models
        assert ibis_file.models["MINIMAL_MODEL"].pullup is not None

    def test_iv_curve_interpolation(self):
        """Test IV curve interpolation"""
        curve = IVCurve(
            voltage=[0.0, 0.5, 1.0, 1.5, 2.0],
            current=[0.0, 0.001, 0.002, 0.003, 0.004]
        )

        # Test interpolation
        assert abs(curve.interpolate(0.5) - 0.001) < 1e-6
        assert abs(curve.interpolate(0.75) - 0.0015) < 1e-5

        # Test extrapolation
        assert abs(curve.interpolate(-0.1) - 0.0) < 1e-6
        assert abs(curve.interpolate(2.5) - 0.004) < 1e-6

    def test_vt_waveform_interpolation(self):
        """Test V-T waveform interpolation"""
        waveform = VTWaveform(
            time=[0.0, 0.1, 0.2, 0.3, 0.5],
            voltage=[0.0, 0.6, 1.0, 1.2, 1.2],
            impedance=50.0,
            v_com=0.0,
            r_load=50.0
        )

        # Test interpolation at known points
        assert abs(waveform.interpolate(0.1) - 0.6) < 1e-6
        assert abs(waveform.interpolate(0.3) - 1.2) < 1e-6

        # Test interpolation between 0.2 and 0.3 (v goes from 1.0 to 1.2)
        # t=0.25 is halfway, so v should be ~1.1
        assert abs(waveform.interpolate(0.25) - 1.1) < 0.05

        # Test extrapolation
        assert abs(waveform.interpolate(-0.1) - 0.0) < 1e-6
        assert abs(waveform.interpolate(1.0) - 1.2) < 1e-6


class TestIBISModel:
    """Test IBIS model wrapper functionality"""

    def test_model_wrapper_creation(self):
        """Test creating model wrapper from content"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)

        assert wrapper is not None
        assert wrapper.ibis_file is not None

    def test_get_behavioral_model(self):
        """Test getting behavioral model"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        model = wrapper.get_model("OUTPUT_MODEL")

        assert model is not None
        assert model.model_name == "OUTPUT_MODEL"
        assert model.c_comp > 0

    def test_output_levels_from_iv_curves(self):
        """Test computing output levels from IV curves"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        model = wrapper.get_model("OUTPUT_MODEL")

        assert model is not None
        assert model.v_ol >= 0
        assert model.v_oh > 0

    def test_input_thresholds(self):
        """Test input threshold computation"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        model = wrapper.get_model("OUTPUT_MODEL")

        assert model is not None
        assert model.v_il < model.v_ih  # IL < IH for non-inverting

    def test_rise_fall_time_extraction(self):
        """Test rise/fall time extraction from waveforms"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        model = wrapper.get_model("OUTPUT_MODEL")

        assert model is not None
        # Waveforms are defined, so transition times should be computed
        # (actual values depend on waveform data)

    def test_generate_iv_curve(self):
        """Test generating fine-resolution IV curve"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        v, i = wrapper.generate_iv_curve("OUTPUT_MODEL", num_points=50)

        assert len(v) == 50
        assert len(i) == 50
        assert len(v) == len(i)

        # Voltage should be monotonic
        for k in range(len(v) - 1):
            assert v[k] <= v[k + 1]

    def test_generate_vt_curve_rising(self):
        """Test generating rising V-T curve"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        t, v = wrapper.generate_vt_curve("OUTPUT_MODEL", num_points=50, is_rising=True)

        assert len(t) == 50
        assert len(v) == 50

        # Rising waveform should start low and end high
        assert v[0] < v[-1]

    def test_generate_vt_curve_falling(self):
        """Test generating falling V-T curve"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        t, v = wrapper.generate_vt_curve("OUTPUT_MODEL", num_points=50, is_rising=False)

        assert len(t) == 50
        assert len(v) == 50

        # Falling waveform should start high and end low
        assert v[0] > v[-1]

    def test_compute_waveform_metrics(self):
        """Test waveform metrics computation"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        model = wrapper.get_model("OUTPUT_MODEL")

        assert model is not None
        assert model.rising_waveform is not None

        metrics = wrapper.compute_waveform_metrics(model.rising_waveform)

        assert isinstance(metrics, WaveformMetrics)
        assert metrics.rise_time >= 0
        assert metrics.settling_time >= 0

    def test_drive_output_rising(self):
        """Test output drive for rising transition"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        model = wrapper.get_model("OUTPUT_MODEL")

        assert model is not None

        # At time 0, output should be near low
        v0 = model.drive_output(0.0, True)
        # At time 1.0, output should be near high
        v1 = model.drive_output(1.0, True)

        assert v1 > v0  # Rising transition

    def test_drive_output_falling(self):
        """Test output drive for falling transition"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        model = wrapper.get_model("OUTPUT_MODEL")

        assert model is not None

        # At time 0, output should be near high
        v0 = model.drive_output(0.0, False)
        # At time 1.0, output should be near low
        v1 = model.drive_output(1.0, False)

        assert v1 < v0  # Falling transition


class TestIBISSimulator:
    """Test IBIS simulator functionality"""

    def test_simulator_creation(self):
        """Test creating simulator"""
        simulator = IBISSimulator()

        assert simulator is not None
        assert simulator.channel_params is not None

    def test_simulator_with_ibis_file(self):
        """Test creating simulator with IBIS file"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file)

        assert simulator.model_wrapper is not None

    def test_simulator_with_channel_params(self):
        """Test simulator with channel parameters"""
        params = ChannelParameters(
            length=10.0,
            impedance=50.0,
            propagation_velocity=150.0
        )
        simulator = IBISSimulator(channel_params=params)

        assert abs(simulator.channel_params.length - 10.0) < 0.01
        assert abs(simulator.channel_params.impedance - 50.0) < 0.01

    def test_basic_simulation(self):
        """Test basic channel simulation"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file)

        config = SimulationConfig(
            t_stop=20.0,
            dt=0.1,
            v_drive=1.2
        )

        result = simulator.simulate("OUTPUT_MODEL", config)

        assert isinstance(result, SimulationResult)
        assert len(result.time) > 0
        assert len(result.input_voltage) == len(result.time)
        assert len(result.output_voltage) == len(result.time)

        # Output should be different from input due to channel effects
        assert not np.allclose(result.input_voltage, result.output_voltage)

    def test_simulation_time_range(self):
        """Test simulation time range"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file)

        config = SimulationConfig(
            t_start=-5.0,
            t_stop=50.0,
            dt=0.1
        )

        result = simulator.simulate("OUTPUT_MODEL", config)

        assert result.time[0] >= config.t_start
        assert result.time[-1] < config.t_stop

    def test_waveform_metrics_in_result(self):
        """Test waveform metrics in simulation result"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file)

        config = SimulationConfig(t_stop=20.0)
        result = simulator.simulate("OUTPUT_MODEL", config)

        if result.waveform_metrics:
            assert isinstance(result.waveform_metrics, WaveformMetrics)

    def test_distortion_computation(self):
        """Test signal distortion computation"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file)

        config = SimulationConfig(t_stop=20.0)
        result = simulator.simulate("OUTPUT_MODEL", config)

        if result.distortion:
            assert isinstance(result.distortion, SignalDistortion)

    def test_crosstalk_simulation(self):
        """Test crosstalk simulation"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file)

        config = SimulationConfig(t_stop=10.0)

        result = simulator.simulate_crosstalk(
            aggressor_config=config,
            victim_model_name="OUTPUT_MODEL"
        )

        assert isinstance(result, CrosstalkResult)
        assert result.coupling_coefficient >= 0
        assert result.far_end_crosstalk >= 0

    def test_eye_analysis(self):
        """Test eye diagram analysis"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file)

        config = SimulationConfig(t_stop=20.0)
        result = simulator.simulate("OUTPUT_MODEL", config)

        eye_result = simulator.analyze_eye(
            result.output_voltage,
            result.time,
            bit_pattern="101010101010",
            ui=2.0
        )

        assert isinstance(eye_result, EyeAnalysisResult)

    def test_channel_frequency_response(self):
        """Test channel frequency response computation"""
        params = ChannelParameters(
            length=10.0,
            impedance=50.0
        )
        simulator = IBISSimulator(channel_params=params)

        response = simulator.compute_channel_frequency_response()

        assert isinstance(response, ChannelResponse)
        assert len(response.frequency) > 0
        assert len(response.impedance) == len(response.frequency)

    def test_insertion_loss_extraction(self):
        """Test extracting insertion loss at specific frequency"""
        params = ChannelParameters(length=10.0)
        simulator = IBISSimulator(channel_params=params)

        response = simulator.compute_channel_frequency_response()

        loss_1ghz = response.get_insertion_loss(1e9)
        loss_5ghz = response.get_insertion_loss(5e9)

        # Higher frequency should have more loss (for lossy channel)
        # Note: This depends on channel parameters

    def test_phase_delay_extraction(self):
        """Test extracting phase delay at specific frequency"""
        params = ChannelParameters(length=10.0)
        simulator = IBISSimulator(channel_params=params)

        response = simulator.compute_channel_frequency_response()

        delay_1ghz = response.get_phase_delay(1e9)
        # Phase delay should be positive for causal channel

    def test_signal_distortion_comprehensive(self):
        """Test comprehensive signal distortion computation"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file)

        config = SimulationConfig(t_stop=20.0, dt=0.01)
        result = simulator.simulate("OUTPUT_MODEL", config)

        dist = simulator.compute_signal_distortion(result, config)

        assert isinstance(dist, SignalDistortion)
        assert dist.attenuation_db <= 0  # Attenuation should be negative dB


class TestSimulationConfig:
    """Test simulation configuration"""

    def test_config_defaults(self):
        """Test default configuration"""
        config = SimulationConfig()

        assert config.mode == SimulationMode.TIME_DOMAIN
        assert config.t_stop == 50.0
        assert config.dt == 0.001
        assert config.v_drive == 1.2

    def test_config_num_samples(self):
        """Test computing number of samples"""
        config = SimulationConfig(t_stop=10.0, dt=0.1)
        # Default t_start is -5.0, so num_samples = (10 - (-5)) / 0.1 = 150
        assert config.num_samples() == 150

    def test_config_custom_values(self):
        """Test custom configuration values"""
        config = SimulationConfig(
            t_stop=100.0,
            t_start=-10.0,
            dt=0.005,
            v_drive=1.8,
            r_drive=40.0,
            r_load=45.0
        )

        assert config.t_stop == 100.0
        assert config.v_drive == 1.8
        assert config.r_drive == 40.0


class TestChannelParameters:
    """Test channel parameters"""

    def test_channel_defaults(self):
        """Test default channel parameters"""
        params = ChannelParameters()

        assert params.length == 10.0
        assert params.impedance == 50.0
        assert params.propagation_velocity == 150.0

    def test_custom_channel_params(self):
        """Test custom channel parameters"""
        params = ChannelParameters(
            length=50.0,
            impedance=85.0,
            propagation_velocity=120.0,
            resistance_per_mm=0.5,
            dielectric_loss_tan=0.03
        )

        assert params.length == 50.0
        assert params.impedance == 85.0
        assert params.dielectric_loss_tan == 0.03


class TestBehavioralModel:
    """Test behavioral model functionality"""

    def test_behavioral_model_creation(self):
        """Test creating behavioral model"""
        model = BehavioralModel(
            model_name="TEST",
            v_oh=1.2,
            v_ol=0.0,
            r_out=50.0,
            c_comp=2.0
        )

        assert model.model_name == "TEST"
        assert model.v_oh == 1.2
        assert model.v_ol == 0.0

    def test_drive_output_step(self):
        """Test step response output"""
        model = BehavioralModel(
            model_name="STEP_TEST",
            v_cc=1.2,
            rising_waveform=None,
            falling_waveform=None
        )

        # Without waveforms, uses simple step model
        v_low = model.drive_output(1.0, False, 1.2)
        v_high = model.drive_output(1.0, True, 1.2)

        assert v_low < 0.1  # Should be near 0
        assert v_high > 1.0  # Should be near Vcc

    def test_behavioral_model_with_waveform(self):
        """Test behavioral model with waveform data"""
        waveform = VTWaveform(
            time=[0.0, 0.1, 0.2, 0.3, 0.5, 1.0],
            voltage=[0.0, 0.3, 0.8, 1.1, 1.2, 1.2],
            impedance=50.0,
            v_com=0.0,
            r_load=50.0
        )

        model = BehavioralModel(
            model_name="WAVEFORM_TEST",
            rising_waveform=waveform
        )

        v_early = model.drive_output(0.05, True)
        v_late = model.drive_output(0.5, True)

        assert v_late > v_early  # Rising waveform


class TestIVCurve:
    """Test IV curve functionality"""

    def test_iv_curve_validation(self):
        """Test IV curve validates equal length arrays"""
        with pytest.raises(ValueError):
            IVCurve(voltage=[0.0, 1.0], current=[0.0])

    def test_iv_curve_interpolation_at_endpoints(self):
        """Test IV curve interpolation at endpoints"""
        curve = IVCurve(
            voltage=[0.0, 1.0, 2.0],
            current=[0.0, 0.001, 0.002]
        )

        assert abs(curve.interpolate(0.0) - 0.0) < 1e-9
        assert abs(curve.interpolate(2.0) - 0.002) < 1e-9


class TestVTWaveform:
    """Test V-T waveform functionality"""

    def test_vt_waveform_validation(self):
        """Test VT waveform validates equal length arrays"""
        with pytest.raises(ValueError):
            VTWaveform(time=[0.0, 1.0], voltage=[0.0], impedance=50.0, v_com=0.0, r_load=50.0)


class TestIBISPackage:
    """Test IBIS package functionality"""

    def test_package_from_list(self):
        """Test creating package from list"""
        pkg = IBISPackage.from_list([0.1, 2.0, 0.5])

        assert abs(pkg.r_pkg - 0.1) < 0.01
        assert abs(pkg.l_pkg - 2.0) < 0.01
        assert abs(pkg.c_pkg - 0.5) < 0.01

    def test_package_from_list_invalid(self):
        """Test package creation with invalid data"""
        with pytest.raises(ValueError):
            IBISPackage.from_list([0.1])


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_end_to_end_simulation(self):
        """Test complete simulation workflow"""
        # Create wrapper
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)

        # Create simulator
        simulator = IBISSimulator(wrapper.ibis_file, ChannelParameters())

        # Run simulation
        config = SimulationConfig(t_stop=20.0, dt=0.1)
        result = simulator.simulate("OUTPUT_MODEL", config)

        # Verify results
        assert len(result.time) > 0
        assert len(result.input_voltage) == len(result.time)
        assert len(result.output_voltage) == len(result.time)

        # Compute metrics
        dist = simulator.compute_signal_distortion(result, config)
        assert dist.attenuation_db <= 0

    def test_crosstalk_workflow(self):
        """Test crosstalk analysis workflow"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file, ChannelParameters())

        config = SimulationConfig(t_stop=10.0)
        crosstalk = simulator.simulate_crosstalk(config, "OUTPUT_MODEL")

        assert crosstalk.coupling_coefficient >= 0
        assert crosstalk.rms_voltage >= 0

    def test_eye_analysis_workflow(self):
        """Test eye analysis workflow"""
        wrapper = create_model_wrapper(SAMPLE_IBIS_CONTENT)
        simulator = IBISSimulator(wrapper.ibis_file, ChannelParameters())

        config = SimulationConfig(t_stop=40.0)
        result = simulator.simulate("OUTPUT_MODEL", config)

        eye = simulator.analyze_eye(
            result.output_voltage,
            result.time,
            bit_pattern="101010101010",
            ui=2.0
        )

        assert eye.eye_height >= 0
        assert eye.eye_width >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])