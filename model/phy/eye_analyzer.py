"""
Eye Diagram Analyzer for HBM4 Signal Integrity

Provides comprehensive eye diagram generation, metrics calculation, BER estimation,
margin analysis, DQ/DQS eye analysis, and JEDEC compliance checking for HBM4
high-speed memory interfaces.

Reference:
- JEDEC JESD270-4A HBM4 specification
- IEEE 802.3 for eye measurement methodologies
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Callable
from enum import Enum
import warnings
from scipy import stats, special


class EyeMeasurementType(Enum):
    """Types of eye measurements."""
    TIME_DOMAIN = "time_domain"
    VOLTAGE_DOMAIN = "voltage_domain"
    COMBINED = "combined"


class DQSignalType(Enum):
    """DQ signal types."""
    DQ = "dq"
    DQS = "dqs"
    WCK = "wck"  # Write clock for HBM4


@dataclass
class EyeMeasurementConfig:
    """Configuration for eye measurements."""
    # Samples per UI
    samples_per_ui: int = 64
    # Number of UI to capture
    n_ui: int = 1000
    # Voltage resolution for histogram
    v_resolution: float = 0.001
    # Time resolution for histogram (fraction of UI)
    t_resolution: float = 0.01
    # Decision threshold (normalized)
    decision_threshold: float = 0.0
    # BER target
    target_ber: float = 1e-16
    # Confidence level for BER estimation
    confidence_level: float = 0.95


@dataclass
class EyeMaskConfig:
    """JEDEC eye mask configuration."""
    # Mask type
    mask_type: str = "hbm4"
    # Eye height target (fraction of signal swing)
    eye_height_target: float = 0.1
    # Eye width target (fraction of UI)
    eye_width_target: float = 0.25
    # BER target
    ber_target: float = 1e-16
    # Mask polygon points (time, voltage) normalized
    mask_points: List[Tuple[float, float]] = field(default_factory=lambda: [
        (0.0, 0.4), (0.15, 0.35), (0.25, 0.0),
        (0.35, 0.35), (0.5, 0.4), (0.65, 0.35),
        (0.75, 0.0), (0.85, 0.35), (1.0, 0.4)
    ])
    # Voltage margin requirement (fraction)
    voltage_margin_min: float = 0.05
    # Timing margin requirement (fraction of UI)
    timing_margin_min: float = 0.1


@dataclass
class DQDEyeConfig:
    """Configuration for DQ/DQS eye analysis."""
    # DQS to DQ timing offset (fraction of UI)
    dqs_to_dq_offset: float = 0.0
    # DQS duty cycle
    dqs_duty_cycle: float = 0.5
    # Read preamble/postamble length (UI)
    read_preamble_ui: float = 2.0
    read_postamble_ui: float = 1.0
    # Write preamble/postamble length (UI)
    write_preamble_ui: float = 1.5
    write_postamble_ui: float = 0.5


@dataclass
class EyeMetrics:
    """Results of eye diagram analysis."""
    # Eye width (UI)
    eye_width: float
    # Eye height (V or normalized)
    eye_height: float
    # Eye area (normalized)
    eye_area: float
    # Vertical closure at center (%)
    vertical_closure: float
    # Horizontal closure at center (%)
    horizontal_closure: float
    # BER estimate
    ber_estimate: float
    # SNR at center (dB)
    snr_db: float
    # Jitter (RMS, UI)
    jitter_rms: float
    # Noise (RMS, V)
    noise_rms: float
    # One level mean
    one_level_mean: float
    # Zero level mean
    zero_level_mean: float
    # One level sigma
    one_level_sigma: float
    # Zero level sigma
    zero_level_sigma: float
    # DCD jitter (UI)
    jitter_dcd: float = 0.0
    # Random jitter (UI)
    jitter_random: float = 0.0
    # Deterministic jitter (UI)
    jitter_deterministic: float = 0.0
    # Voltage margin (V)
    voltage_margin: float = 0.0
    # Timing margin (UI)
    timing_margin: float = 0.0
    # Eye height in mV
    eye_height_mv: float = 0.0
    # Eye width in ps
    eye_width_ps: float = 0.0


@dataclass
class DQDEyeMetrics:
    """DQ/DQS specific eye metrics."""
    # Eye height at DQ capture point (mV)
    eye_height_mv: float = 0.0
    # Eye width at DQ capture point (UI)
    eye_width_ui: float = 0.0
    # Setup time margin (ps)
    setup_margin_ps: float = 0.0
    # Hold time margin (ps)
    hold_margin_ps: float = 0.0
    # DQS duty cycle error (ps)
    dqs_duty_error_ps: float = 0.0
    # DQ-DQS skew (ps)
    dq_dqs_skew_ps: float = 0.0
    # BER estimate
    ber_estimate: float = 1.0
    # Compliant flag
    compliant: bool = False


class EyeDiagramAnalyzer:
    """
    Eye diagram analyzer for high-speed signals.

    Provides comprehensive eye diagram analysis including:
    - Eye width/height calculation
    - BER estimation via bathtub curve
    - Margin analysis with statistical bounds
    - JEDEC compliance checking
    - DQ/DQS specific analysis
    """

    def __init__(self, config: Optional[EyeMeasurementConfig] = None,
                 mask_config: Optional[EyeMaskConfig] = None,
                 dqd_config: Optional[DQDEyeConfig] = None):
        """Initialize eye analyzer."""
        self.config = config or EyeMeasurementConfig()
        self.mask_config = mask_config or EyeMaskConfig()
        self.dqd_config = dqd_config or DQDEyeConfig()
        self._histogram: Optional[np.ndarray] = None
        self._time_bins: Optional[np.ndarray] = None
        self._voltage_bins: Optional[np.ndarray] = None
        self._eye_samples: Optional[np.ndarray] = None
        self._bathtub_data: Optional[Tuple[np.ndarray, np.ndarray]] = None

    def generate_eye_diagram(self, signal: np.ndarray,
                             samples_per_ui: Optional[int] = None,
                             n_ui: Optional[int] = None) -> np.ndarray:
        """
        Generate eye diagram data from signal.

        Args:
            signal: Input signal (oversampled NRZ)
            samples_per_ui: Samples per unit interval
            n_ui: Number of UI to capture

        Returns:
            2D histogram matrix (time x voltage)
        """
        spui = samples_per_ui or self.config.samples_per_ui
        n = n_ui or self.config.n_ui

        # Limit samples if signal is shorter
        max_ui = min(n, len(signal) // spui)
        signal = signal[:max_ui * spui]

        # Calculate histogram dimensions
        t_bins = int(1.0 / self.config.t_resolution)
        v_bins = int(2.0 / self.config.v_resolution)  # Assume +/-1V range

        # Initialize histogram
        histogram = np.zeros((t_bins, v_bins))

        # Voltage bins - extend range to cover all signal values
        v_min, v_max = -1.0, 1.0
        epsilon = 0.01
        v_edges = np.linspace(v_min - epsilon, v_max + epsilon, v_bins + 1)

        # Time bins
        t_edges = np.linspace(0, 1.0, t_bins + 1)

        # Build histogram
        for i in range(max_ui):
            start = i * spui
            end = start + spui
            ui_samples = signal[start:end]

            # Time bin for each sample
            t_indices = np.clip(
                ((np.arange(spui) / spui) * t_bins).astype(int),
                0, t_bins - 1
            )

            # Voltage bin for each sample
            v_raw = np.digitize(ui_samples, v_edges)
            v_indices = np.clip(v_raw - 1, 0, v_bins - 1)

            # Increment histogram
            for j in range(spui):
                histogram[t_indices[j], v_indices[j]] += 1

        self._histogram = histogram
        self._time_bins = t_edges[:-1]
        self._voltage_bins = v_edges[:-1]
        self._eye_samples = signal

        return histogram

    def calculate_eye_width(self, percentile: float = 0.5) -> float:
        """
        Calculate eye width at specified percentile.

        Args:
            percentile: Fraction of vertical opening (0.5 = center)

        Returns:
            Eye width in UI
        """
        if self._histogram is None:
            return 0.0

        t_bins, v_bins = self._histogram.shape
        eye_widths = []

        for t in range(t_bins):
            col = self._histogram[t, :]
            total = np.sum(col)

            if total > 0:
                cumsum = np.cumsum(col) / total
                low_idx = np.searchsorted(cumsum, (1 - percentile) / 2)
                high_idx = np.searchsorted(cumsum, 1 - (1 - percentile) / 2)

                eye_widths.append(1.0 / t_bins)

        return sum(eye_widths) if eye_widths else 0.0

    def calculate_eye_height(self, percentile: float = 0.5) -> float:
        """
        Calculate eye height at specified percentile.

        Args:
            percentile: Fraction of horizontal opening (0.5 = center)

        Returns:
            Eye height in voltage units
        """
        if self._histogram is None:
            return 0.0

        t_bins, v_bins = self._histogram.shape

        center_t_bin = t_bins // 2
        col = self._histogram[center_t_bin, :]

        total = np.sum(col)
        if total == 0:
            return 0.0

        cumsum = np.cumsum(col) / total
        low_thresh = (1 - percentile) / 2
        high_thresh = 1 - low_thresh

        low_idx = np.searchsorted(cumsum, low_thresh)
        high_idx = np.searchsorted(cumsum, high_thresh)

        if low_idx < v_bins and high_idx < v_bins:
            low_v = self._voltage_bins[low_idx]
            high_v = self._voltage_bins[high_idx]
            return max(high_v - low_v, 0.0)

        return 0.0

    def calculate_full_metrics(self, ui_ps: float = 83.33) -> EyeMetrics:
        """
        Calculate comprehensive eye metrics.

        Args:
            ui_ps: Unit interval in picoseconds (default 83.33ps for 12GT/s)

        Returns:
            EyeMetrics object with all measurements
        """
        if self._histogram is None or self._eye_samples is None:
            return EyeMetrics(
                eye_width=0.0, eye_height=0.0, eye_area=0.0,
                vertical_closure=100.0, horizontal_closure=100.0,
                ber_estimate=1.0, snr_db=0.0, jitter_rms=0.0,
                noise_rms=0.0, one_level_mean=0.0, zero_level_mean=0.0,
                one_level_sigma=0.0, zero_level_sigma=0.0
            )

        # Calculate basic metrics
        eye_width = self.calculate_eye_width(0.5)
        eye_height = self.calculate_eye_height(0.5)

        # Calculate eye area
        eye_area = eye_width * eye_height

        # Calculate closures
        vertical_closure = (1.0 - eye_height / 2.0) * 100
        horizontal_closure = (1.0 - eye_width) * 100

        # BER estimation
        ber_estimate = self.estimate_ber()

        # SNR calculation
        snr_db = self.calculate_snr()

        # Jitter estimation with decomposition
        jitter_total, jitter_dcd, jitter_rj, jitter_dj = self.estimate_jitter_decomposed()

        # Noise estimation
        noise_rms = self.estimate_noise()

        # Level statistics
        spui = self.config.samples_per_ui
        n_ui = len(self._eye_samples) // spui

        one_samples = []
        zero_samples = []

        for i in range(n_ui):
            start = i * spui
            one_samples.extend(self._eye_samples[start:start + spui // 4])
            zero_samples.extend(self._eye_samples[start + 3 * spui // 4:start + spui])

        one_samples = np.array(one_samples)
        zero_samples = np.array(zero_samples)

        one_level_mean = np.mean(one_samples)
        zero_level_mean = np.mean(zero_samples)
        one_level_sigma = np.std(one_samples)
        zero_level_sigma = np.std(zero_samples)

        # Calculate margins
        voltage_margin = eye_height / 2 - 3 * noise_rms
        timing_margin = eye_width - 6 * jitter_total

        return EyeMetrics(
            eye_width=eye_width,
            eye_height=eye_height,
            eye_area=eye_area,
            vertical_closure=vertical_closure,
            horizontal_closure=horizontal_closure,
            ber_estimate=ber_estimate,
            snr_db=snr_db,
            jitter_rms=jitter_total,
            jitter_dcd=jitter_dcd,
            jitter_random=jitter_rj,
            jitter_deterministic=jitter_dj,
            noise_rms=noise_rms,
            one_level_mean=one_level_mean,
            zero_level_mean=zero_level_mean,
            one_level_sigma=one_level_sigma,
            zero_level_sigma=zero_level_sigma,
            voltage_margin=voltage_margin,
            timing_margin=timing_margin,
            eye_height_mv=eye_height * 1000,
            eye_width_ps=eye_width * ui_ps
        )

    def estimate_ber(self, method: str = "bathtub") -> float:
        """
        Estimate BER from eye diagram.

        Args:
            method: Estimation method ("bathtub", "gaussian", or "histogram")

        Returns:
            Estimated BER
        """
        if self._histogram is None:
            return 1.0

        snr_db = self.calculate_snr()

        if snr_db < 1.0:
            return 0.5

        noise_rms = self.estimate_noise()
        eye_height = self.calculate_eye_height(0.5)

        if method == "bathtub":
            # Simplified bathtub model
            Q = snr_db / (20 * np.log10(np.e))
            ber = 0.5 * (1 - special.erf(Q / np.sqrt(2)))
            return max(min(ber, 1.0), 1e-20)

        elif method == "gaussian":
            V_margin = eye_height / 2
            sigma = max(noise_rms, 1e-6)
            Q = V_margin / sigma
            ber = 0.5 * np.exp(-Q**2 / 2)
            return min(ber, 1.0)

        else:  # histogram
            t_bins, v_bins = self._histogram.shape

            t_low = t_bins // 4
            t_high = 3 * t_bins // 4

            v_center = v_bins // 2
            v_bin_width = (self._voltage_bins[1] - self._voltage_bins[0]) if len(self._voltage_bins) > 1 else 0.01
            v_margin = max(1, int(eye_height / (2 * v_bin_width)))
            v_margin = min(v_margin, v_center - 1)

            outside_eye = np.sum(
                self._histogram[t_low:t_high, :max(0, v_center - v_margin)]
            ) + np.sum(
                self._histogram[t_low:t_high, min(v_bins, v_center + v_margin):]
            )

            total = np.sum(self._histogram)
            return outside_eye / total if total > 0 else 1.0

    def calculate_snr(self) -> float:
        """
        Calculate SNR at eye center.

        Returns:
            SNR in dB
        """
        if self._eye_samples is None:
            return 0.0

        spui = self.config.samples_per_ui
        n_ui = len(self._eye_samples) // spui

        center_samples = []
        for i in range(n_ui):
            idx = i * spui + spui // 2
            if idx < len(self._eye_samples):
                center_samples.append(self._eye_samples[idx])

        center_samples = np.array(center_samples)

        signal_mean = np.abs(np.mean(center_samples))
        noise_sigma = np.std(center_samples)

        if noise_sigma < 1e-9:
            return 40.0

        snr_linear = (signal_mean / noise_sigma) ** 2
        return 10 * np.log10(max(snr_linear, 1e-12))

    def estimate_jitter(self) -> float:
        """
        Estimate RMS jitter from eye crossings.

        Returns:
            RMS jitter in UI
        """
        if self._eye_samples is None:
            return 0.0

        spui = self.config.samples_per_ui
        n_ui = len(self._eye_samples) // spui

        crossings = []

        for i in range(n_ui - 1):
            start = i * spui
            ui_data = self._eye_samples[start:start + spui]
            next_ui = self._eye_samples[start + spui:start + 2 * spui]

            combined = np.concatenate([ui_data, next_ui])
            signs = np.sign(combined)
            sign_changes = np.where(np.diff(signs) != 0)[0]

            for idx in sign_changes:
                if idx < spui:
                    t_crossing = (idx + 1) / spui - 0.5
                    crossings.append(t_crossing)

        if len(crossings) < 2:
            return 0.1

        crossings = np.array(crossings)
        return np.std(crossings)

    def estimate_jitter_decomposed(self) -> Tuple[float, float, float, float]:
        """
        Decompose jitter into components.

        Returns:
            Tuple of (total_rms, DCD, RJ, DJ) in UI
        """
        if self._eye_samples is None:
            return 0.0, 0.0, 0.0, 0.0

        spui = self.config.samples_per_ui
        n_ui = len(self._eye_samples) // spui

        crossings = []

        for i in range(n_ui - 1):
            start = i * spui
            ui_data = self._eye_samples[start:start + spui]
            next_ui = self._eye_samples[start + spui:start + 2 * spui]

            combined = np.concatenate([ui_data, next_ui])
            signs = np.sign(combined)
            sign_changes = np.where(np.diff(signs) != 0)[0]

            for idx in sign_changes:
                if idx < spui:
                    t_crossing = (idx + 1) / spui - 0.5
                    crossings.append(t_crossing)

        if len(crossings) < 2:
            return 0.1, 0.0, 0.1, 0.0

        crossings = np.array(crossings)

        # Total jitter RMS
        total_jitter = np.std(crossings)

        # DCD: difference between mean of rising and falling crossings
        rising_crossings = crossings[crossings >= 0]
        falling_crossings = crossings[crossings < 0]

        dcd = 0.0
        if len(rising_crossings) > 0 and len(falling_crossings) > 0:
            rising_mean = np.mean(rising_crossings)
            falling_mean = np.abs(np.mean(falling_crossings))
            dcd = abs(rising_mean - falling_mean)

        # Simplified RJ and DJ estimation
        # In practice, would use dual-dirac model or CDF fitting
        jitter_without_dcd = np.abs(crossings) - dcd / 2
        jitter_without_dcd = jitter_without_dcd[jitter_without_dcd > 0]

        if len(jitter_without_dcd) > 0:
            # DJ = deterministic jitter (bounded)
            dj = np.ptp(jitter_without_dcd) / 2
            # RJ = random jitter (sigma of unbounded portion)
            rj = max(np.std(jitter_without_dcd) - dj / 6, 0.01)
        else:
            dj = 0.0
            rj = total_jitter

        return total_jitter, dcd, rj, dj

    def estimate_noise(self) -> float:
        """
        Estimate RMS noise from eye diagram.

        Returns:
            RMS noise in voltage units
        """
        if self._eye_samples is None:
            return 0.0

        spui = self.config.samples_per_ui
        n_ui = len(self._eye_samples) // spui

        one_samples = []
        zero_samples = []

        for i in range(n_ui):
            start = i * spui
            ui_data = self._eye_samples[start:start + spui]

            one_samples.extend(ui_data[:spui // 4])
            zero_samples.extend(ui_data[3 * spui // 4:spui])

        one_samples = np.array(one_samples)
        zero_samples = np.array(zero_samples)

        noise_one = np.std(one_samples)
        noise_zero = np.std(zero_samples)

        return (noise_one + noise_zero) / 2

    def bathtub_curve(self, n_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate bathtub curve (BER vs time offset).

        Args:
            n_points: Number of points to sample

        Returns:
            Tuple of (time offsets in UI, BER values)
        """
        if self._histogram is None:
            return np.array([]), np.array([])

        t_bins, v_bins = self._histogram.shape

        t_offsets = np.linspace(0, 1.0, n_points)
        ber_values = []

        threshold = self.config.decision_threshold

        for t in t_offsets:
            t_idx = int(t * t_bins)
            if t_idx >= t_bins:
                t_idx = t_bins - 1

            col = self._histogram[t_idx, :]
            total = np.sum(col)

            if total > 0:
                v_center = v_bins // 2
                above = np.sum(col[v_center:])
                below = np.sum(col[:v_center])

                ber_t = (above + below) / total
                ber_values.append(ber_t)
            else:
                ber_values.append(1.0)

        self._bathtub_data = (t_offsets, np.array(ber_values))
        return t_offsets, np.array(ber_values)

    def margin_analysis(self, target_ber: float = 1e-16) -> Dict[str, float]:
        """
        Analyze margin to target BER.

        Args:
            target_ber: Target BER specification

        Returns:
            Dictionary with margin metrics
        """
        metrics = self.calculate_full_metrics()

        # Calculate margins
        margin_voltage = metrics.eye_height / 2 - 3 * metrics.noise_rms
        margin_time = metrics.eye_width - 6 * metrics.jitter_rms

        # Voltage margin in dB
        signal_swing = metrics.one_level_mean - metrics.zero_level_mean
        margin_voltage_db = 20 * np.log10(
            max(margin_voltage / signal_swing, 1e-6)
        ) if signal_swing > 0 else -100

        margin_time_ui = max(margin_time, 0)
        margin_combined = margin_voltage * margin_time_ui
        ber_margin = -np.log10(metrics.ber_estimate / target_ber) if metrics.ber_estimate > 0 else 0

        return {
            'voltage_margin': margin_voltage,
            'voltage_margin_db': margin_voltage_db,
            'time_margin_ui': margin_time_ui,
            'combined_margin': margin_combined,
            'ber_margin_orders': ber_margin,
            'meets_target_ber': metrics.ber_estimate <= target_ber
        }

    def check_jedec_compliance(self, ui_ps: float = 83.33) -> Dict[str, any]:
        """
        Check JEDEC compliance for HBM4 eye.

        Args:
            ui_ps: Unit interval in picoseconds

        Returns:
            Dictionary with compliance results
        """
        metrics = self.calculate_full_metrics(ui_ps=ui_ps)

        # HBM4 specifications from JESD270-4A
        hbm4_requirements = {
            'eye_height_min_mv': 50.0,      # > 50 mV UI
            'eye_width_min_ui': 0.25,        # > 0.25 UI
            'ber_max': 1e-16,
            'snr_min_db': 12.0,
            'jitter_max_ui': 0.15
        }

        height_pass = metrics.eye_height_mv >= hbm4_requirements['eye_height_min_mv']
        width_pass = metrics.eye_width >= hbm4_requirements['eye_width_min_ui']
        ber_pass = metrics.ber_estimate <= hbm4_requirements['ber_max']
        snr_pass = metrics.snr_db >= hbm4_requirements['snr_min_db']
        jitter_pass = metrics.jitter_rms <= hbm4_requirements['jitter_max_ui']

        compliant = height_pass and width_pass and ber_pass and snr_pass and jitter_pass

        return {
            'compliant': compliant,
            'height_pass': height_pass,
            'width_pass': width_pass,
            'ber_pass': ber_pass,
            'snr_pass': snr_pass,
            'jitter_pass': jitter_pass,
            'metrics': {
                'eye_height_mv': metrics.eye_height_mv,
                'eye_width_ui': metrics.eye_width,
                'eye_width_ps': metrics.eye_width_ps,
                'ber_estimate': metrics.ber_estimate,
                'snr_db': metrics.snr_db,
                'jitter_rms_ui': metrics.jitter_rms,
                'voltage_margin_mv': metrics.voltage_margin * 1000,
                'timing_margin_ps': metrics.timing_margin * ui_ps
            },
            'requirements': hbm4_requirements,
            'ui_ps': ui_ps
        }


class DQDEyeAnalyzer:
    """
    DQ/DQS-specific eye analyzer for HBM4.

    Analyzes the relationship between DQ data and DQS strobe signals.
    """

    def __init__(self, config: Optional[DQDEyeConfig] = None):
        """Initialize DQ/DQS eye analyzer."""
        self.config = config or DQDEyeConfig()
        self._dqs_edges: Optional[np.ndarray] = None
        self._dq_samples: Optional[np.ndarray] = None

    def analyze_dq_dqs_eye(self, dq_signal: np.ndarray, dqs_signal: np.ndarray,
                          sample_rate: float) -> DQDEyeMetrics:
        """
        Analyze DQ/DQS eye characteristics.

        Args:
            dq_signal: DQ signal waveform
            dqs_signal: DQS signal waveform
            sample_rate: Sample rate in Hz

        Returns:
            DQDEyeMetrics with analysis results
        """
        # Find DQS edges
        self._dqs_edges = self._find_dqs_edges(dqs_signal, sample_rate)
        self._dq_samples = dq_signal

        if len(self._dqs_edges) == 0:
            return DQDEyeMetrics()

        # Sample DQ at DQS edges
        sampled_dq = self._sample_at_edges(dq_signal, self._dqs_edges)

        # Calculate metrics
        eye_height = np.max(sampled_dq) - np.min(sampled_dq)

        # Timing analysis
        edge_periods = np.diff(self._dqs_edges / sample_rate)
        period_mean = np.mean(edge_periods)
        period_std = np.std(edge_periods)
        jitter_ps = period_std * 1e12

        # DQS duty cycle
        duty_error = self._calculate_duty_error(dqs_signal, sample_rate)

        # DQ-DQS skew
        skew = self._estimate_skew(dq_signal, dqs_signal, sample_rate)

        # Setup/hold margins
        setup_ps, hold_ps = self._calculate_setup_hold_margins(
            dq_signal, dqs_signal, sample_rate
        )

        # BER estimation
        ber = self._estimate_ber_from_dq_dqs(eye_height, jitter_ps / 1000)

        # Compliance check
        compliant = (eye_height * 1000 >= 50 and
                    setup_ps >= 10 and
                    hold_ps >= 10 and
                    ber <= 1e-16)

        return DQDEyeMetrics(
            eye_height_mv=eye_height * 1000,
            eye_width_ui=1.0 - 2 * (jitter_ps / 1000 / (1 / sample_rate)),
            setup_margin_ps=setup_ps,
            hold_margin_ps=hold_ps,
            dqs_duty_error_ps=duty_error,
            dq_dqs_skew_ps=skew,
            ber_estimate=ber,
            compliant=compliant
        )

    def _find_dqs_edges(self, dqs_signal: np.ndarray, sample_rate: float) -> np.ndarray:
        """Find DQS rising/falling edges."""
        threshold = np.mean(dqs_signal)
        edges = []

        # Find rising edges
        for i in range(1, len(dqs_signal)):
            if dqs_signal[i-1] < threshold and dqs_signal[i] >= threshold:
                edges.append(i)

        return np.array(edges)

    def _sample_at_edges(self, signal: np.ndarray, edges: np.ndarray) -> np.ndarray:
        """Sample signal at specified edges."""
        samples = []
        for edge in edges:
            if 0 < edge < len(signal) - 1:
                samples.append(signal[edge])
        return np.array(samples)

    def _calculate_duty_error(self, dqs_signal: np.ndarray, sample_rate: float) -> float:
        """Calculate DQS duty cycle error in ps."""
        threshold = np.mean(dqs_signal)

        high_samples = np.sum(dqs_signal >= threshold)
        total_samples = len(dqs_signal)
        duty_cycle = high_samples / total_samples

        period_ps = (1.0 / sample_rate) * 1e12
        ideal_high = self.config.dqs_duty_cycle * period_ps
        actual_high = duty_cycle * period_ps

        return abs(actual_high - ideal_high)

    def _estimate_skew(self, dq_signal: np.ndarray, dqs_signal: np.ndarray,
                      sample_rate: float) -> float:
        """Estimate DQ-DQS skew in ps."""
        # Find DQ transition points
        dq_diff = np.abs(np.diff(dq_signal))
        dq_transitions = np.where(dq_diff > 0.1 * np.max(dq_diff))[0]

        # Find DQS transition points
        dqs_diff = np.abs(np.diff(dqs_signal))
        dqs_transitions = np.where(dqs_diff > 0.1 * np.max(dqs_diff))[0]

        if len(dq_transitions) == 0 or len(dqs_transitions) == 0:
            return 0.0

        # Calculate average skew
        skew_samples = []
        for dq_t in dq_transitions[:10]:  # Sample first 10 transitions
            closest_dqs = min(dqs_transitions, key=lambda x: abs(x - dq_t))
            skew_samples.append(dq_t - closest_dqs)

        skew_ps = np.mean(skew_samples) / sample_rate * 1e12
        return abs(skew_ps)

    def _calculate_setup_hold_margins(self, dq_signal: np.ndarray,
                                     dqs_signal: np.ndarray,
                                     sample_rate: float) -> Tuple[float, float]:
        """Calculate setup and hold margins in ps."""
        period_ps = (1.0 / sample_rate) * 1e12

        # Find valid sampling windows
        edges = self._find_dqs_edges(dqs_signal, sample_rate)

        if len(edges) < 2:
            return 20.0, 20.0

        # Estimate margins based on DQ transitions relative to DQS edges
        setup_samples = []
        hold_samples = []

        for edge in edges[1:-1]:
            # Look for DQ transitions before this edge (setup)
            search_range = min(20, edge)
            if search_range > 0:
                window = dq_signal[edge - search_range:edge]
                if len(window) > 1:
                    trans = np.where(np.abs(np.diff(window)) > 0.01)[0]
                    if len(trans) > 0:
                        setup_samples.append(edge - trans[-1] - 1)

            # Look for DQ transitions after this edge (hold)
            search_range = min(20, len(dq_signal) - edge)
            if search_range > 0:
                window = dq_signal[edge:edge + search_range]
                if len(window) > 1:
                    trans = np.where(np.abs(np.diff(window)) > 0.01)[0]
                    if len(trans) > 0:
                        hold_samples.append(trans[0])

        if len(setup_samples) > 0:
            setup_ps = np.min(setup_samples) / sample_rate * 1e12
        else:
            setup_ps = period_ps * 0.25  # Default 25% of period

        if len(hold_samples) > 0:
            hold_ps = np.min(hold_samples) / sample_rate * 1e12
        else:
            hold_ps = period_ps * 0.25  # Default 25% of period

        return abs(setup_ps), abs(hold_ps)

    def _estimate_ber_from_dq_dqs(self, eye_height: float, jitter_ui: float) -> float:
        """Estimate BER from DQ/DQS metrics."""
        # Simplified BER estimation
        V_margin = eye_height / 2
        noise_rms = 0.02  # Assumed noise

        if V_margin <= 0:
            return 1.0

        Q = V_margin / noise_rms
        ber_voltage = 0.5 * np.exp(-Q**2 / 2)

        # Jitter component
        ber_jitter = jitter_ui / 2 if jitter_ui < 1 else 0.5

        # Combined BER
        return min(ber_voltage + ber_jitter, 1.0)


class BathtubCurveGenerator:
    """
    Bathtub curve generator for BER analysis.

    Produces bathtub curves showing BER variation across
    the unit interval.
    """

    def __init__(self, n_samples_per_ui: int = 64):
        """Initialize bathtub generator."""
        self.n_samples = n_samples_per_ui

    def generate_bathtub(self, signal: np.ndarray,
                        threshold: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate bathtub curve from signal.

        Args:
            signal: Input signal
            threshold: Decision threshold

        Returns:
            Tuple of (time offsets, BER values)
        """
        n_ui = len(signal) // self.n_samples
        t_offsets = np.linspace(0, 1.0, self.n_samples)
        ber_curve = np.zeros(self.n_samples)

        for t in range(self.n_samples):
            n_errors = 0
            n_samples_total = 0

            for ui in range(n_ui - 1):
                idx = ui * self.n_samples + t
                if idx < len(signal) - 1:
                    sample = signal[idx]
                    next_sample = signal[idx + 1]

                    if sample > threshold:
                        expected = 1
                    else:
                        expected = -1

                    if expected == 1 and sample < threshold:
                        n_errors += 1
                    elif expected == -1 and sample > threshold:
                        n_errors += 1

                    n_samples_total += 1

            if n_samples_total > 0:
                ber_curve[t] = n_errors / n_samples_total

        return t_offsets, ber_curve

    def fit_bathtub_model(self, t: np.ndarray, ber: np.ndarray) -> Dict[str, float]:
        """
        Fit bathtub model to data.

        Model: BER ~ exp(-((t - t_center) / sigma_t)^2 / 2) + BER_floor

        Returns:
            Dictionary with fitted parameters
        """
        center_idx = np.argmin(ber)
        t_center = t[center_idx]

        min_ber = ber[center_idx]
        threshold_ber = min_ber * 10

        left_idx = np.where(ber[:center_idx] > threshold_ber)[0]
        right_idx = np.where(ber[center_idx:] > threshold_ber)[0]

        left_width = 0.0
        right_width = 0.0

        if len(left_idx) > 0:
            left_width = t_center - t[left_idx[-1]]
        if len(right_idx) > 0:
            right_width = t[right_idx[0] + center_idx] - t_center

        sigma_t = (left_width + right_width) / 2

        return {
            'center_ui': t_center,
            'sigma_ui': sigma_t,
            'ber_floor': min_ber
        }

    def estimate_ber_from_bathtub(self, bathtub_curve: Tuple[np.ndarray, np.ndarray],
                                 time_margin: float) -> float:
        """
        Estimate BER at specified time margin.

        Args:
            bathtub_curve: Tuple of (time_offsets, ber_values)
            time_margin: Time margin in UI from center

        Returns:
            Estimated BER at specified margin
        """
        t_offsets, ber_values = bathtub_curve

        # Find center
        center_idx = len(t_offsets) // 2

        # Find point at specified margin from center
        target_idx = center_idx + int(time_margin * len(t_offsets) / 2)
        target_idx = max(0, min(target_idx, len(ber_values) - 1))

        return ber_values[target_idx]


class EyeVisualizationHelper:
    """
    Helper class for eye diagram visualization.

    Provides utilities for creating visualization data.
    """

    @staticmethod
    def create_eye_plot_data(histogram: np.ndarray,
                           time_bins: np.ndarray,
                           voltage_bins: np.ndarray) -> Dict[str, any]:
        """
        Create data structure for eye diagram plotting.

        Returns:
            Dictionary with plot-ready data
        """
        return {
            'histogram': histogram,
            'time_bins': time_bins,
            'voltage_bins': voltage_bins,
            'time_range': (time_bins[0], time_bins[-1]) if len(time_bins) > 0 else (0, 1),
            'voltage_range': (voltage_bins[0], voltage_bins[-1]) if len(voltage_bins) > 0 else (-1, 1)
        }

    @staticmethod
    def create_mask_polygon(mask_config: EyeMaskConfig,
                           signal_swing: float = 1.0) -> List[Tuple[float, float]]:
        """
        Create mask polygon for plotting.

        Args:
            mask_config: Eye mask configuration
            signal_swing: Signal swing (V)

        Returns:
            List of (time, voltage) polygon points
        """
        polygon = []
        for t, v in mask_config.mask_points:
            polygon.append((t, v * signal_swing))
        polygon.append(polygon[0])  # Close polygon
        return polygon

    @staticmethod
    def annotate_eye_metrics(metrics: EyeMetrics,
                           ui_ps: float = 83.33) -> Dict[str, str]:
        """
        Create annotation text for eye metrics.

        Returns:
            Dictionary of label-text pairs
        """
        return {
            'eye_height': f"Eye Height: {metrics.eye_height_mv:.1f} mV",
            'eye_width': f"Eye Width: {metrics.eye_width_ps:.1f} ps ({metrics.eye_width:.2f} UI)",
            'ber': f"BER: {metrics.ber_estimate:.2e}",
            'snr': f"SNR: {metrics.snr_db:.1f} dB",
            'jitter': f"Jitter (RMS): {metrics.jitter_rms * ui_ps:.1f} ps",
            'voltage_margin': f"V Margin: {metrics.voltage_margin * 1000:.1f} mV",
            'timing_margin': f"T Margin: {metrics.timing_margin * ui_ps:.1f} ps"
        }


def create_hbm4_eye_analyzer(data_rate_gt: float = 12.0,
                             target_ber: float = 1e-16) -> EyeDiagramAnalyzer:
    """
    Create HBM4-specific eye analyzer.

    Args:
        data_rate_gt: Data rate in GT/s
        target_ber: Target BER

    Returns:
        Configured EyeDiagramAnalyzer
    """
    ui_ps = 1000.0 / data_rate_gt

    config = EyeMeasurementConfig(
        samples_per_ui=int(ui_ps / 0.5),  # ~0.5 ps per sample
        n_ui=2000,
        target_ber=target_ber
    )

    mask_config = EyeMaskConfig(
        mask_type='hbm4',
        eye_height_target=0.1,
        eye_width_target=0.25,
        ber_target=target_ber
    )

    return EyeDiagramAnalyzer(config=config, mask_config=mask_config)


def estimate_channel_budget(eye_metrics: EyeMetrics,
                           ui_ps: float = 83.33) -> Dict[str, float]:
    """
    Estimate total channel budget from eye metrics.

    Args:
        eye_metrics: Eye metrics
        ui_ps: Unit interval in picoseconds

    Returns:
        Channel budget breakdown
    """
    total_ui = 1.0
    total_mv = eye_metrics.eye_height_mv

    return {
        'total_time_ui': total_ui,
        'total_voltage_mv': total_mv,
        'allocated_to_jitter_ui': eye_metrics.jitter_rms * 6,
        'allocated_to_noise_mv': eye_metrics.noise_rms * 6 * 1000,
        'remaining_timing_margin_ui': max(0, total_ui - eye_metrics.jitter_rms * 6),
        'remaining_voltage_margin_mv': max(0, total_mv - eye_metrics.noise_rms * 6 * 1000),
        'eye_openness_percent': (eye_metrics.eye_width * eye_metrics.eye_height / (total_ui * total_mv)) * 1000
    }
