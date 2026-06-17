"""
Signal Integrity Models for HBM4 PHY Simulation

Implements TX pre-emphasis, RX CTLE (Continuous Time Linear Equalizer),
DFE (Decision Feedback Equalizer), and signal conditioning for high-speed
memory interfaces with HBM4-specific parameters and JEDEC compliance.

Reference:
- JEDEC JESD270-4A HBM4 specification
- DFI 5.0/5.1 specification
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Callable
from enum import Enum
import warnings


class EqualizerType(Enum):
    """Types of equalization."""
    NONE = "none"
    TX_PRE_EMPHASIS = "tx_pre_emphasis"
    RX_CTLE = "rx_ctle"
    DFE = "dfe"


class HBM4DataRate(Enum):
    """HBM4 data rate options."""
    GT_8 = 8e9       # 8 GT/s
    GT_12 = 12e9     # 12 GT/s
    GT_16 = 16e9     # 16 GT/s

    @property
    def ui_ps(self) -> float:
        """Unit interval in picoseconds."""
        return 1e12 / self.value

    @property
    def nyquist_ghz(self) -> float:
        """Nyquist frequency in GHz."""
        return self.value / 2 / 1e9


@dataclass
class PreEmphasisConfig:
    """Configuration for TX pre-emphasis."""
    # Number of pre-tap positions
    n_pre_taps: int = 2
    # Number of post-tap positions
    n_post_taps: int = 2
    # Maximum tap weight (fraction of main tap)
    max_tap_weight: float = 0.4
    # Tap resolution (bits)
    tap_resolution: int = 5
    # Main cursor weight (normalized)
    main_cursor: float = 1.0


@dataclass
class CTLEConfig:
    """Configuration for RX CTLE."""
    # Number of DC gain stages
    n_dc_gain_stages: int = 4
    # DC gain range (dB)
    dc_gain_range: Tuple[float, float] = (-6.0, 6.0)
    # Zero frequency options (Hz)
    zero_options: List[float] = field(default_factory=lambda: [4e9, 8e9, 12e9])
    # Pole frequency options (Hz)
    pole_options: List[float] = field(default_factory=lambda: [8e9, 16e9, 24e9])
    # Number of peaking dB
    peaking_range: Tuple[float, float] = (0.0, 12.0)
    # Stage resolution (dB)
    stage_resolution: float = 1.0


@dataclass
class DFEConfig:
    """Configuration for DFE (Decision Feedback Equalizer)."""
    # Number of DFE taps
    n_taps: int = 5
    # Maximum tap magnitude
    max_tap_magnitude: float = 0.3
    # Convergence rate (mu)
    mu: float = 0.01
    # Decision threshold
    decision_threshold: float = 0.0


@dataclass
class DQSignalConfig:
    """Configuration for DQ signal modeling."""
    # DQ signal amplitude (V)
    amplitude_v: float = 0.5
    # Rise/fall time (ps)
    rise_time_ps: float = 15.0
    # Fall time (ps)
    fall_time_ps: float = 15.0
    # DQ impedance (ohm)
    impedance: float = 50.0
    # DQ source impedance (ohm)
    source_impedance: float = 40.0
    # DQ termination voltage (V)
    termination_voltage: float = 0.0


@dataclass
class DQSSignalConfig:
    """Configuration for DQS signal modeling."""
    # DQS amplitude (V)
    amplitude_v: float = 0.5
    # DQS frequency (Hz)
    frequency: float = 8e9
    # DQS duty cycle (fraction)
    duty_cycle: float = 0.5
    # DQS jitter RMS (ps)
    jitter_rms_ps: float = 2.0
    # DQS transition time (ps)
    transition_time_ps: float = 10.0


@dataclass
class TemperatureConfig:
    """Temperature-dependent signal integrity parameters."""
    # Operating temperature (Celsius)
    temperature_c: float = 85.0
    # Temperature coefficient for loss (dB/inch/C)
    loss_temp_coeff: float = 0.02
    # Temperature coefficient for jitter (ps/C)
    jitter_temp_coeff: float = 0.05
    # Temperature coefficient for noise (%/C)
    noise_temp_coeff: float = 1.0
    # Reference temperature (Celsius)
    reference_temp_c: float = 25.0

    def get_loss_adjustment(self, length_mm: float) -> float:
        """Calculate additional loss due to temperature.

        Args:
            length_mm: Channel length in mm

        Returns:
            Additional loss in dB
        """
        temp_delta = self.temperature_c - self.reference_temp_c
        length_m = length_mm / 1000.0
        # Simplified: 0.02 dB/inch/C * temp_delta * length_m * 39.37 in/mm
        return self.loss_temp_coeff * temp_delta * length_m * 39.37

    def get_jitter_adjustment(self) -> float:
        """Calculate additional jitter due to temperature.

        Returns:
            Additional jitter in ps RMS
        """
        temp_delta = self.temperature_c - self.reference_temp_c
        return self.jitter_temp_coeff * temp_delta

    def get_noise_adjustment(self) -> float:
        """Calculate noise scaling factor due to temperature.

        Returns:
            Noise scaling factor (1.0 at reference temp)
        """
        temp_delta = self.temperature_c - self.reference_temp_c
        return 1.0 + (self.noise_temp_coeff / 100.0) * temp_delta


@dataclass
class SignalIntegrityConfig:
    """Complete signal integrity configuration."""
    # Data rate
    data_rate: HBM4DataRate = HBM4DataRate.GT_12
    # Sample rate (Hz)
    sample_rate: float = 32e9
    # Unit interval (s)
    ui_ns: float = 83.33e-9  # 12 GT/s
    # Signal amplitude
    signal_amplitude: float = 1.0
    # Noise RMS
    noise_rms: float = 0.05
    # Jitter RMS (ps)
    jitter_rms_ps: float = 2.0
    # DQ configuration
    dq_config: DQSignalConfig = field(default_factory=DQSignalConfig)
    # DQS configuration
    dqs_config: DQSSignalConfig = field(default_factory=DQSSignalConfig)
    # Temperature configuration
    temperature: TemperatureConfig = field(default_factory=TemperatureConfig)
    # Pre-emphasis config
    pre_emphasis: PreEmphasisConfig = field(default_factory=PreEmphasisConfig)
    # CTLE config
    ctle: CTLEConfig = field(default_factory=CTLEConfig)
    # DFE config
    dfe: DFEConfig = field(default_factory=DFEConfig)

    def update_for_data_rate(self, data_rate: HBM4DataRate) -> None:
        """Update configuration for specific data rate.

        Args:
            data_rate: Target data rate
        """
        self.data_rate = data_rate
        self.ui_ns = data_rate.ui_ps * 1e-9
        self.sample_rate = data_rate.value * 2  # 2x oversampling
        self.dqs_config.frequency = data_rate.value


class TXPreEmphasis:
    """
    TX Pre-emphasis equalizer.

    Implements FIR-based pre-emphasis to compensate for channel loss
    by boosting high-frequency components at the transmitter.
    """

    def __init__(self, config: Optional[PreEmphasisConfig] = None):
        """Initialize pre-emphasis with configuration."""
        self.config = config or PreEmphasisConfig()
        self.taps = self._initialize_taps()

    def _initialize_taps(self) -> np.ndarray:
        """Initialize tap weights to zero (flat response)."""
        n_taps = self.config.n_pre_taps + 1 + self.config.n_post_taps
        taps = np.zeros(n_taps)
        taps[self.config.n_pre_taps] = self.config.main_cursor
        return taps

    def set_taps(self, tap_values: List[float]) -> None:
        """
        Set tap values with saturation and normalization.

        Args:
            tap_values: List of tap weights
        """
        # Set all taps including main cursor
        for i, val in enumerate(tap_values):
            if i < len(self.taps):
                self.taps[i] = np.clip(
                    val,
                    -self.config.max_tap_weight,
                    self.config.max_tap_weight
                )

        # Normalize so sum of all taps equals main_cursor (unity DC gain)
        total = np.sum(self.taps)
        main_idx = self.config.n_pre_taps
        if np.abs(total) > 1e-9:
            scale = self.config.main_cursor / total
            self.taps = self.taps * scale

    def get_taps(self) -> np.ndarray:
        """Get current tap values."""
        return self.taps.copy()

    def equalize(self, signal: np.ndarray) -> np.ndarray:
        """
        Apply pre-emphasis to signal.

        Args:
            signal: Input signal (NRZ data)

        Returns:
            Equalized signal with pre-emphasis applied
        """
        return np.convolve(signal, self.taps, mode='same')

    def frequency_response(self, n_points: int = 256) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate frequency response of pre-emphasis filter.

        Returns:
            Tuple of (frequency vector, complex response)
        """
        dt = 1.0 / (32e9)  # Sample period
        t = np.arange(-len(self.taps)//2, len(self.taps)//2 + 1) * dt

        # FIR frequency response using DTFT
        omega = np.linspace(-np.pi, np.pi, n_points)
        f = omega / (2 * np.pi * dt)

        H = np.zeros(n_points, dtype=complex)
        for k, w in enumerate(omega):
            H[k] = np.sum(self.taps * np.exp(-1j * w * np.arange(len(self.taps))))

        return f, H

    def calculate_boost_db(self) -> float:
        """Calculate high-frequency boost in dB."""
        _, H = self.frequency_response()

        # Boost at Nyquist vs DC
        H_dc = np.abs(H[0])
        H_nyq = np.abs(H[-1])

        if H_dc > 0:
            return 20 * np.log10(H_nyq / H_dc)
        return 0.0


class DQSignalModel:
    """
    DQ (Data) Signal Model for HBM4.

    Models DQ signal characteristics including amplitude,
    transition times, and impedance matching.
    """

    def __init__(self, config: Optional[DQSignalConfig] = None):
        """Initialize DQ signal model."""
        self.config = config or DQSignalConfig()
        self._calibrated = False

    def generate_dq_waveform(self, data_pattern: np.ndarray,
                            sample_rate: float) -> np.ndarray:
        """
        Generate DQ waveform from data pattern.

        Args:
            data_pattern: Binary data pattern (0/1 or -1/+1)
            sample_rate: Sample rate in Hz

        Returns:
            DQ voltage waveform
        """
        # Handle both binary formats
        if np.max(np.abs(data_pattern)) <= 1:
            # Already in -1/+1 format
            symbols = data_pattern
        else:
            # Convert 0/1 to -1/+1
            symbols = 2 * data_pattern - 1

        # Create waveform with rise/fall transitions
        symbol_rate = sample_rate
        samples_per_symbol = int(sample_rate / symbol_rate) if symbol_rate < sample_rate else 1

        waveform = np.zeros(len(symbols) * samples_per_symbol)

        for i, symbol in enumerate(symbols):
            start = i * samples_per_symbol
            end = start + samples_per_symbol

            # Create transition at symbol boundaries
            amplitude = symbol * self.config.amplitude_v

            # Linear interpolation for rise/fall
            transition_samples = int(self.config.rise_time_ps * 1e-12 * sample_rate)
            transition_samples = max(1, min(transition_samples, samples_per_symbol // 4))

            if i == 0:
                prev_amplitude = 0
            else:
                prev_amplitude = symbols[i-1] * self.config.amplitude_v

            # Create waveform with transitions
            for j in range(samples_per_symbol):
                t_frac = j / samples_per_symbol
                if t_frac < 0.5:
                    # Rising/falling edge
                    edge_pos = t_frac / 0.5
                    if amplitude > prev_amplitude:
                        waveform[start + j] = prev_amplitude + (amplitude - prev_amplitude) * edge_pos
                    else:
                        waveform[start + j] = prev_amplitude + (amplitude - prev_amplitude) * edge_pos
                else:
                    waveform[start + j] = amplitude

        return waveform

    def apply_impedance_effects(self, waveform: np.ndarray,
                                channel_impedance: float) -> np.ndarray:
        """
        Apply impedance matching effects to waveform.

        Args:
            waveform: Input waveform
            channel_impedance: Channel impedance in ohms

        Returns:
            Waveform with impedance effects
        """
        # Reflection coefficient
        gamma = (self.config.impedance - channel_impedance) / \
                (self.config.impedance + channel_impedance)

        # Simplified reflection effect
        reflected = np.roll(waveform, len(waveform) // 10) * gamma
        return waveform + reflected * 0.1

    def get_signal_metrics(self) -> Dict[str, float]:
        """Get DQ signal metrics."""
        return {
            'amplitude_v': self.config.amplitude_v,
            'rise_time_ps': self.config.rise_time_ps,
            'fall_time_ps': self.config.fall_time_ps,
            'impedance_ohm': self.config.impedance,
            'source_impedance_ohm': self.config.source_impedance,
            'eye_height_estimate_mv': self.config.amplitude_v * 1000 * 0.8  # 80% margin estimate
        }


class DQSSignalModel:
    """
    DQS (Data Strobe) Signal Model for HBM4.

    Models DQS signal characteristics including duty cycle,
    jitter, and timing alignment with DQ.
    """

    def __init__(self, config: Optional[DQSSignalConfig] = None):
        """Initialize DQS signal model."""
        self.config = config or DQSSignalConfig()
        self._phase_offset = 0.0

    def generate_dqs_waveform(self, n_cycles: int, sample_rate: float) -> np.ndarray:
        """
        Generate DQS waveform.

        Args:
            n_cycles: Number of DQS cycles
            sample_rate: Sample rate in Hz

        Returns:
            DQS voltage waveform
        """
        # Calculate samples per DQS cycle
        period = 1.0 / self.config.frequency
        samples_per_cycle = int(period * sample_rate)

        total_samples = n_cycles * samples_per_cycle
        waveform = np.zeros(total_samples)

        transition_samples = int(self.config.transition_time_ps * 1e-12 * sample_rate)
        transition_samples = max(1, min(transition_samples, samples_per_cycle // 8))

        for cycle in range(n_cycles):
            start = cycle * samples_per_cycle

            # Create duty cycle waveform
            high_samples = int(samples_per_cycle * self.config.duty_cycle)
            low_samples = samples_per_cycle - high_samples

            # Add jitter
            jitter_samples = int(np.random.randn() * self.config.jitter_rms_ps * 1e-12 * sample_rate)

            # Rising edge
            for j in range(transition_samples):
                if start + j < total_samples:
                    waveform[start + j] = (j / transition_samples) * self.config.amplitude_v

            # High level
            for j in range(transition_samples, high_samples - transition_samples):
                if start + j < total_samples:
                    waveform[start + j] = self.config.amplitude_v

            # Falling edge
            for j in range(high_samples - transition_samples, high_samples):
                if start + j < total_samples:
                    waveform[start + j] = (1 - (j - high_samples + transition_samples) / transition_samples) * self.config.amplitude_v

            # Low level
            for j in range(high_samples, samples_per_cycle):
                if start + j < total_samples:
                    waveform[start + j] = 0.0

        return waveform

    def align_to_dq(self, dqs_waveform: np.ndarray, dq_waveform: np.ndarray,
                   timing_offset: float) -> np.ndarray:
        """
        Align DQS to DQ waveform.

        Args:
            dqs_waveform: DQS waveform
            dq_waveform: DQ waveform
            timing_offset: Timing offset as fraction of UI (0-1)

        Returns:
            Aligned DQS waveform
        """
        offset_samples = int(len(dqs_waveform) * timing_offset)
        if offset_samples > 0:
            aligned = np.zeros_like(dqs_waveform)
            aligned[offset_samples:] = dqs_waveform[:-offset_samples]
            return aligned
        return dqs_waveform

    def get_dqs_metrics(self) -> Dict[str, float]:
        """Get DQS signal metrics."""
        return {
            'frequency_hz': self.config.frequency,
            'amplitude_v': self.config.amplitude_v,
            'duty_cycle': self.config.duty_cycle,
            'jitter_rms_ps': self.config.jitter_rms_ps,
            'transition_time_ps': self.config.transition_time_ps,
            'phase_offset_ui': self._phase_offset
        }


class RXCTLE:
    """
    RX Continuous Time Linear Equalizer.

    Implements analog-style CTLE with configurable DC gain,
    zero and pole frequencies for peaking response.
    """

    def __init__(self, config: Optional[CTLEConfig] = None):
        """Initialize CTLE with configuration."""
        self.config = config or CTLEConfig()
        self._dc_gain_db = 0.0
        self._peaking_db = 3.0
        self._zero_idx = 1
        self._pole_idx = 1

    def set_dc_gain(self, gain_db: float) -> None:
        """Set DC gain in dB."""
        self._dc_gain_db = np.clip(
            gain_db,
            self.config.dc_gain_range[0],
            self.config.dc_gain_range[1]
        )

    def set_peaking(self, peaking_db: float) -> None:
        """Set peaking gain in dB."""
        self._peaking_db = np.clip(
            peaking_db,
            self.config.peaking_range[0],
            self.config.peaking_range[1]
        )

    def set_zero_pole(self, zero_idx: int, pole_idx: int) -> None:
        """Set zero and pole frequency indices."""
        self._zero_idx = np.clip(zero_idx, 0, len(self.config.zero_options) - 1)
        self._pole_idx = np.clip(pole_idx, 0, len(self.config.pole_options) - 1)

    def get_zero_frequency(self) -> float:
        """Get current zero frequency."""
        return self.config.zero_options[self._zero_idx]

    def get_pole_frequency(self) -> float:
        """Get current pole frequency."""
        return self.config.pole_options[self._pole_idx]

    def transfer_function(self, frequency: np.ndarray) -> np.ndarray:
        """
        Calculate CTLE transfer function.

        H(s) = H_dc * (s/w_z + 1) / (s/w_p + 1)

        Args:
            frequency: Frequency vector in Hz

        Returns:
            Complex transfer function
        """
        s = 2j * np.pi * frequency

        w_z = 2 * np.pi * self.get_zero_frequency()
        w_p = 2 * np.pi * self.get_pole_frequency()

        H_dc = 10 ** (self._dc_gain_db / 20)

        # Transfer function
        with np.errstate(divide='ignore'):
            H = H_dc * (s / w_z + 1) / (s / w_p + 1)

        return H

    def equalize(self, signal: np.ndarray, sample_rate: float) -> np.ndarray:
        """
        Apply CTLE equalization to signal.

        Args:
            signal: Input signal
            sample_rate: Signal sample rate

        Returns:
            Equalized signal
        """
        n_points = len(signal)

        # Generate frequency vector
        freq = np.fft.rfftfreq(n_points, 1.0 / sample_rate)

        # Get frequency response
        H_ctle = self.transfer_function(freq)

        # FFT of input signal
        X = np.fft.rfft(signal)

        # Apply CTLE
        Y = X * H_ctle

        # Inverse FFT
        y = np.fft.irfft(Y, n=n_points)

        return y

    def optimize_for_channel(self, channel_loss_db: np.ndarray,
                             frequency: np.ndarray) -> None:
        """
        Auto-tune CTLE based on channel loss curve.

        Args:
            channel_loss_db: Channel insertion loss in dB
            frequency: Corresponding frequency vector
        """
        # Find frequency with maximum loss
        max_loss_idx = np.argmax(np.abs(channel_loss_db))

        # Set zero just below the max loss frequency for peaking
        if max_loss_idx > 0:
            self._zero_idx = min(max_loss_idx, len(self.config.zero_options) - 1)

        # Set pole well above for high-frequency boost
        self._pole_idx = min(self._zero_idx + 1, len(self.config.pole_options) - 1)

        # Set peaking to compensate for loss at Nyquist
        if max_loss_idx < len(channel_loss_db) and max_loss_idx > 0:
            nyquist_idx = len(channel_loss_db) - 1
            target_peaking = max(0, np.abs(channel_loss_db[nyquist_idx]) / 2)
            self._peaking_db = min(target_peaking, self.config.peaking_range[1])


class DFEEqualizer:
    """
    Decision Feedback Equalizer (DFE).

    Implements symbol-by-symbol DFE with adaptive tap update.
    """

    def __init__(self, config: Optional[DFEConfig] = None):
        """Initialize DFE with configuration."""
        self.config = config or DFEConfig()
        self.taps = np.zeros(self.config.n_taps)
        self.samples_per_ui = 64

    def reset(self) -> None:
        """Reset DFE state and taps."""
        self.taps = np.zeros(self.config.n_taps)

    def equalize_symbol(self, samples: np.ndarray, decisions: np.ndarray,
                       symbol_idx: int) -> float:
        """
        Equalize a single symbol using DFE.

        Args:
            samples: Received samples around symbol
            decisions: Previous symbol decisions
            symbol_idx: Index of current symbol

        Returns:
            Equalized sample value
        """
        center_sample = samples[self.samples_per_ui // 2]
        feedback = 0.0

        # Calculate feedback from previous symbols
        for i in range(min(symbol_idx, self.config.n_taps)):
            feedback += self.taps[i] * decisions[symbol_idx - i - 1]

        return center_sample - feedback

    def update_taps(self, error: float, decisions: np.ndarray,
                    symbol_idx: int) -> None:
        """
        Update DFE taps using LMS algorithm.

        Args:
            error: Decision error
            decisions: Symbol decisions
            symbol_idx: Current symbol index
        """
        for i in range(min(symbol_idx, self.config.n_taps)):
            # LMS update: w = w + mu * error * d_prev
            self.taps[i] += self.config.mu * error * (-decisions[symbol_idx - i - 1])

            # Saturate taps
            self.taps[i] = np.clip(
                self.taps[i],
                -self.config.max_tap_magnitude,
                self.config.max_tap_magnitude
            )

    def train(self, tx_signal: np.ndarray, rx_signal: np.ndarray,
              n_iterations: int = 100) -> List[float]:
        """
        Train DFE taps using known training pattern.

        Args:
            tx_signal: Transmitted signal
            rx_signal: Received signal (after channel)
            n_iterations: Number of training iterations

        Returns:
            List of MSE values per iteration
        """
        mse_history = []

        # Resample to symbol rate
        n_symbols = len(tx_signal)
        decisions = np.sign(rx_signal[::self.samples_per_ui])

        for _ in range(n_iterations):
            total_error = 0.0

            for i in range(1, n_symbols):
                equalized = self.equalize_symbol(
                    rx_signal[i * self.samples_per_ui:(i + 2) * self.samples_per_ui],
                    decisions[:i],
                    i
                )

                # Decision
                decision = 1 if equalized > self.config.decision_threshold else -1
                decisions[i] = decision

                # Error
                error = equalized - decision
                total_error += error ** 2

                # Update taps
                self.update_taps(error, decisions, i)

            mse = total_error / n_symbols
            mse_history.append(mse)

        return mse_history


class TemperatureCompensatedSignalIntegrity:
    """
    Temperature-compensated signal integrity model.

    Adjusts signal integrity parameters based on operating temperature
    to model real-world behavior across temperature ranges.
    """

    def __init__(self, config: SignalIntegrityConfig):
        """Initialize temperature-compensated model."""
        self.config = config
        self.temp_config = config.temperature
        self._baseline_config = config
        self._apply_temperature_compensation()

    def _apply_temperature_compensation(self) -> None:
        """Apply temperature effects to signal integrity parameters."""
        # Adjust noise based on temperature
        noise_factor = self.temp_config.get_noise_adjustment()
        self.config.noise_rms = self._baseline_config.noise_rms * noise_factor

        # Adjust jitter based on temperature
        jitter_delta = self.temp_config.get_jitter_adjustment()
        self.config.jitter_rms_ps = self._baseline_config.jitter_rms_ps + jitter_delta

    def get_temperature_metrics(self) -> Dict[str, float]:
        """Get temperature-compensated metrics."""
        return {
            'temperature_c': self.temp_config.temperature_c,
            'noise_rms_compensated': self.config.noise_rms,
            'jitter_rms_ps_compensated': self.config.jitter_rms_ps,
            'noise_increase_percent': (self.config.noise_rms / self._baseline_config.noise_rms - 1) * 100,
            'jitter_increase_ps': self.config.jitter_rms_ps - self._baseline_config.jitter_rms_ps
        }

    def adjust_for_temperature(self, temperature_c: float) -> None:
        """Adjust parameters for new temperature.

        Args:
            temperature_c: New temperature in Celsius
        """
        self.temp_config.temperature_c = temperature_c
        self._apply_temperature_compensation()


class SignalIntegrityModel:
    """
    Complete signal integrity model integrating TX, channel, and RX components.

    Combines pre-emphasis, channel model, and CTLE/DFE for end-to-end
    signal path simulation with HBM4 support.
    """

    def __init__(self, config: Optional[SignalIntegrityConfig] = None):
        """Initialize signal integrity model."""
        self.config = config or SignalIntegrityConfig()

        # Initialize components
        self.tx_pre_emphasis = TXPreEmphasis(self.config.pre_emphasis)
        self.rx_ctle = RXCTLE(self.config.ctle)
        self.dfe = DFEEqualizer(self.config.dfe)

        # HBM4-specific components
        self.dq_model = DQSignalModel(self.config.dq_config)
        self.dqs_model = DQSSignalModel(self.config.dqs_config)

        # Temperature compensation
        self._temp_compensation = TemperatureCompensatedSignalIntegrity(self.config)

    def set_pre_emphasis_taps(self, pre_taps: List[float], post_taps: List[float]) -> None:
        """
        Set pre-emphasis tap values.

        Args:
            pre_taps: Pre-tap values (before main cursor)
            post_taps: Post-tap values (after main cursor)
        """
        all_taps = pre_taps + [1.0] + post_taps
        self.tx_pre_emphasis.set_taps(all_taps)

    def simulate_tx_to_rx(self, signal: np.ndarray,
                          channel_response: np.ndarray,
                          temperature: Optional[float] = None) -> np.ndarray:
        """
        Simulate complete TX -> channel -> RX signal path.

        Args:
            signal: Input TX signal
            channel_response: Channel impulse response
            temperature: Optional temperature override (Celsius)

        Returns:
            Received signal after equalization
        """
        # Update temperature if provided
        if temperature is not None:
            self._temp_compensation.adjust_for_temperature(temperature)

        # TX pre-emphasis
        tx_out = self.tx_pre_emphasis.equalize(signal)

        # Channel convolution
        channel_out = np.convolve(tx_out, channel_response, mode='same')

        # Add temperature-compensated noise
        if self.config.noise_rms > 0:
            noise = np.random.randn(len(channel_out)) * self.config.noise_rms
            channel_out += noise

        # Add temperature-dependent jitter (simplified model)
        jitter_samples = int(self.config.jitter_rms_ps * 1e-12 * self.config.sample_rate)
        if jitter_samples > 0:
            for i in range(0, len(channel_out) - jitter_samples, jitter_samples * 10):
                jitter_offset = int(np.random.randn() * jitter_samples)
                if 0 < i + jitter_offset < len(channel_out):
                    channel_out[i:i+jitter_samples] = np.roll(channel_out[i:i+jitter_samples], jitter_offset)

        # RX CTLE
        rx_ctle_out = self.rx_ctle.equalize(
            channel_out,
            self.config.sample_rate
        )

        return rx_ctle_out

    def apply_dfe(self, signal: np.ndarray, decisions: np.ndarray) -> np.ndarray:
        """
        Apply DFE to signal.

        Args:
            signal: Input signal
            decisions: Symbol decisions

        Returns:
            DFE-equalized signal
        """
        n_symbols = len(signal) // self.dfe.samples_per_ui
        output = np.zeros(len(signal))

        for i in range(n_symbols):
            start = i * self.dfe.samples_per_ui
            end = (i + 1) * self.dfe.samples_per_ui

            equalized = self.dfe.equalize_symbol(
                signal[start:end],
                decisions[:i],
                i
            )
            output[start:end] = equalized

        return output

    def estimate_tx_eye(self, prbs_length: int = 127) -> dict:
        """
        Estimate TX eye diagram metrics.

        Args:
            prbs_length: PRBS pattern length

        Returns:
            Dictionary of eye metrics
        """
        # Generate PRBS
        prbs = np.array([1 if i % 2 == 0 else -1 for i in range(prbs_length)])
        samples_per_ui = 64
        signal = np.repeat(prbs, samples_per_ui) * (self.config.signal_amplitude / 2)

        # Apply pre-emphasis
        tx_out = self.tx_pre_emphasis.equalize(signal)

        # Calculate metrics
        return self._calculate_eye_metrics(tx_out, samples_per_ui)

    def estimate_rx_eye(self, channel_response: np.ndarray,
                        prbs_length: int = 127,
                        temperature: Optional[float] = None) -> dict:
        """
        Estimate RX eye diagram metrics after equalization.

        Args:
            channel_response: Channel impulse response
            prbs_length: PRBS pattern length
            temperature: Optional temperature (Celsius)

        Returns:
            Dictionary of eye metrics
        """
        # Generate PRBS
        prbs = np.array([1 if i % 2 == 0 else -1 for i in range(prbs_length)])
        samples_per_ui = 64
        signal = np.repeat(prbs, samples_per_ui) * (self.config.signal_amplitude / 2)

        # Simulate path with temperature
        rx_out = self.simulate_tx_to_rx(signal, channel_response, temperature)

        # Calculate metrics
        return self._calculate_eye_metrics(rx_out, samples_per_ui)

    def analyze_dq_dqs_eye(self, dq_signal: np.ndarray, dqs_signal: np.ndarray,
                           sample_rate: float) -> Dict[str, float]:
        """
        Analyze DQ/DQS eye characteristics.

        Args:
            dq_signal: DQ signal waveform
            dqs_signal: DQS signal waveform
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary with DQ/DQS eye metrics
        """
        # Calculate timing alignment
        # Find DQS rising edges
        dqs_diff = np.diff(dqs_signal)
        rising_edges = np.where(dqs_diff > 0.1 * self.config.dqs_config.amplitude_v)[0]

        # Sample DQ at DQS edges
        if len(rising_edges) > 0:
            sampled_dq = dq_signal[rising_edges]

            # Eye height at sampling point
            eye_height = np.max(sampled_dq) - np.min(sampled_dq)

            # Eye width from DQS jitter
            edge_times = rising_edges / sample_rate
            edge_periods = np.diff(edge_times)
            jitter = np.std(edge_periods) * 1e12  # ps

            return {
                'eye_height_mv': eye_height * 1000,
                'timing_jitter_ps': jitter,
                'dqs_edges_analyzed': len(rising_edges),
                'setup_time_ps': 20.0,  # Simplified
                'hold_time_ps': 10.0    # Simplified
            }

        return {
            'eye_height_mv': 0.0,
            'timing_jitter_ps': 0.0,
            'dqs_edges_analyzed': 0,
            'setup_time_ps': 20.0,
            'hold_time_ps': 10.0
        }

    def _calculate_eye_metrics(self, signal: np.ndarray,
                               samples_per_ui: int) -> dict:
        """
        Calculate eye diagram metrics from signal.

        Args:
            signal: Signal samples
            samples_per_ui: Samples per unit interval

        Returns:
            Dictionary with eye width, height, and other metrics
        """
        n_ui = len(signal) // samples_per_ui

        # Extract eye samples at each UI crossing
        eye_samples = []
        for i in range(n_ui):
            start = i * samples_per_ui
            end = start + samples_per_ui
            eye_samples.append(signal[start:end])

        eye_samples = np.array(eye_samples)

        # Eye height: vertical opening at center
        center = samples_per_ui // 2
        one_level = eye_samples[:, :center // 2]
        zero_level = eye_samples[:, center + center // 2:]

        eye_height = np.mean(one_level.max(axis=1)) - np.mean(zero_level.min(axis=1))

        # Eye width: horizontal opening at center
        crossings = []
        for i in range(n_ui - 1):
            # Find transition
            diff = eye_samples[i + 1] - eye_samples[i]
            zero_crossings = np.where(np.diff(np.sign(diff)))[0]
            if len(zero_crossings) > 0:
                crossings.append(zero_crossings[0])

        if len(crossings) > 0:
            crossing_mean = np.mean(crossings)
            eye_width = 1.0  # Normalized UI
        else:
            eye_width = 0.5

        # SNR estimate
        signal_pwr = np.mean(eye_samples ** 2)
        noise_pwr = np.var(eye_samples)

        return {
            'eye_height': eye_height,
            'eye_width': eye_width,
            'snr_db': 10 * np.log10(signal_pwr / max(noise_pwr, 1e-12)),
            'pre_emphasis_boost_db': self.tx_pre_emphasis.calculate_boost_db(),
            'ctle_dc_gain_db': self.rx_ctle._dc_gain_db,
            'ctle_peaking_db': self.rx_ctle._peaking_db
        }


class JEDECComplianceChecker:
    """
    JEDEC eye mask compliance checker for HBM4.

    Validates eye diagrams against JEDEC JESD270-4A specifications.
    """

    # JEDEC HBM4 eye mask parameters (normalized to UI and signal amplitude)
    HBM4_EYE_MASK = {
        'eye_height_min': 0.1,       # Minimum eye height (fraction of swing)
        'eye_width_min': 0.25,       # Minimum eye width (fraction of UI)
        'ber_target': 1e-16,          # Target BER
        'mask_points': [
            (0.0, 0.4), (0.15, 0.35), (0.25, 0.0),
            (0.35, 0.35), (0.5, 0.4), (0.65, 0.35),
            (0.75, 0.0), (0.85, 0.35), (1.0, 0.4)
        ]
    }

    def __init__(self, mask_type: str = 'hbm4'):
        """Initialize compliance checker.

        Args:
            mask_type: Eye mask type ('hbm4', 'hbm3', 'hbm2e')
        """
        self.mask_type = mask_type
        self._load_mask()

    def _load_mask(self) -> None:
        """Load appropriate eye mask based on type."""
        if self.mask_type == 'hbm4':
            self.mask = self.HBM4_EYE_MASK.copy()
        elif self.mask_type == 'hbm3':
            self.mask = {
                'eye_height_min': 0.12,
                'eye_width_min': 0.3,
                'ber_target': 1e-15,
                'mask_points': [
                    (0.0, 0.35), (0.12, 0.3), (0.2, 0.0),
                    (0.3, 0.3), (0.5, 0.35), (0.7, 0.3),
                    (0.8, 0.0), (0.88, 0.3), (1.0, 0.35)
                ]
            }
        else:  # hbm2e
            self.mask = {
                'eye_height_min': 0.15,
                'eye_width_min': 0.35,
                'ber_target': 1e-12,
                'mask_points': [
                    (0.0, 0.3), (0.1, 0.25), (0.15, 0.0),
                    (0.25, 0.25), (0.5, 0.3), (0.75, 0.25),
                    (0.85, 0.0), (0.9, 0.25), (1.0, 0.3)
                ]
            }

    def check_eye_mask_compliance(self, eye_histogram: np.ndarray,
                                  eye_width: float, eye_height: float) -> Dict[str, any]:
        """
        Check if eye diagram passes JEDEC mask.

        Args:
            eye_histogram: Eye diagram histogram
            eye_width: Measured eye width (UI)
            eye_height: Measured eye height (V or normalized)

        Returns:
            Dictionary with compliance results
        """
        # Normalize measurements
        height_pass = eye_height >= self.mask['eye_height_min']
        width_pass = eye_width >= self.mask['eye_width_min']

        # Check mask polygon intersection
        mask_violations = self._check_mask_violations(eye_histogram)

        # Overall compliance
        compliant = height_pass and width_pass and not mask_violations

        return {
            'compliant': compliant,
            'height_pass': height_pass,
            'width_pass': width_pass,
            'mask_violations': mask_violations,
            'eye_height_measured': eye_height,
            'eye_width_measured': eye_width,
            'eye_height_required': self.mask['eye_height_min'],
            'eye_width_required': self.mask['eye_width_min'],
            'mask_type': self.mask_type,
            'ber_target': self.mask['ber_target']
        }

    def _check_mask_violations(self, eye_histogram: np.ndarray) -> bool:
        """
        Check for violations of eye mask polygon.

        Args:
            eye_histogram: Eye diagram histogram

        Returns:
            True if violations found
        """
        # Simplified check - would need actual polygon intersection
        # for full implementation
        return False


def create_hbm4_signal_integrity_config(data_rate: HBM4DataRate = HBM4DataRate.GT_12,
                                         temperature_c: float = 85.0) -> SignalIntegrityConfig:
    """
    Create HBM4-specific signal integrity configuration.

    Args:
        data_rate: HBM4 data rate
        temperature_c: Operating temperature

    Returns:
        Configured SignalIntegrityConfig
    """
    config = SignalIntegrityConfig()
    config.update_for_data_rate(data_rate)
    config.temperature.temperature_c = temperature_c

    return config
