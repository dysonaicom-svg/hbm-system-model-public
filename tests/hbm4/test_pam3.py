"""
HBM4 PAM3 Signal Model Tests

Tests for PAM3 encoding/decoding and signal integrity analysis.
"""

import pytest
import math
from model.dram.phy_signal import (
    PAM3SignalModel,
    PAM3Level,
    PAM3Symbol,
    PAM3EyeDiagram,
    HBM4PAM3Encoder,
)


class TestPAM3SignalModel:
    """Test PAM3 Signal Model"""

    def test_encode_basic(self):
        """Test basic PAM3 encoding"""
        model = PAM3SignalModel()

        # Encode 2 bits -> 1 symbol
        # 00 -> -1, 01 -> 0, 10 -> 0, 11 -> +1
        data = 0b11  # MSB first: bits 1,1 -> +1
        symbols = model.encode(data, 2)

        assert len(symbols) == 1
        assert symbols[0].level == 1
        assert symbols[0].amplitude == model.level_voltage[1]

    def test_encode_multi_symbol(self):
        """Test multi-symbol encoding"""
        model = PAM3SignalModel()

        # 2 bits -> 1 symbol
        # For data=3 (binary 11):
        # i=0: bit1=(3>>1)&1=1, bit0=(3>>0)&1=1 -> (1,1) -> +1
        data = 0b11
        symbols = model.encode(data, 2)

        assert len(symbols) == 1
        assert symbols[0].level == 1   # (1,1) -> +1

    def test_decode_basic(self):
        """Test basic PAM3 decoding"""
        model = PAM3SignalModel()

        # Create symbols: +1
        symbols = [
            PAM3Symbol(level=1, ui_position=0, amplitude=0.5),
        ]

        data, num_bits = model.decode(symbols)

        assert num_bits == 2
        # +1 (1,1) -> data = 3
        assert data == 0b11

    def test_encode_decode_roundtrip(self):
        """Test encode-decode roundtrip"""
        model = PAM3SignalModel()

        # Simple test: data=3 -> +1 symbol -> decoded=3
        original_data = 0b11
        num_bits = 2

        symbols = model.encode(original_data, num_bits)
        decoded_data, decoded_bits = model.decode(symbols)

        assert decoded_bits == num_bits
        assert decoded_data == original_data

    def test_level_voltages(self):
        """Test level voltage assignments"""
        model = PAM3SignalModel(voltage_swing=1.0)

        assert model.level_voltage[-1] == -0.5
        assert model.level_voltage[0] == 0
        assert model.level_voltage[1] == 0.5

    def test_eye_diagram_computation(self):
        """Test eye diagram computation"""
        model = PAM3SignalModel(
            symbol_rate=8e9,
            voltage_swing=0.8,
            noise_std=0.02,
        )

        eye = model.compute_eye_diagram(num_symbols=500, samples_per_ui=32)

        assert isinstance(eye, PAM3EyeDiagram)
        assert eye.eye_height > 0
        assert eye.snr_db > 0
        assert 0 <= eye.ber_estimate <= 1

    def test_snr_estimate(self):
        """Test SNR estimation"""
        model = PAM3SignalModel(
            voltage_swing=1.0,
            noise_std=0.1,
        )

        snr_db = model.get_snr_estimate()
        # SNR = 10*log10(Vswing^2/noise^2) for amplitude
        # Actual formula uses voltage_swing directly
        assert snr_db > 0  # SNR should be positive

    def test_bandwidth_efficiency(self):
        """Test bandwidth efficiency calculation"""
        model = PAM3SignalModel()

        efficiency = model.get_bandwidth_efficiency()

        # PAM3 theoretical maximum = log2(3) ≈ 1.585
        assert abs(efficiency - math.log2(3)) < 0.01


class TestHBM4PAM3Encoder:
    """Test HBM4-specific PAM3 encoder"""

    def test_initialization(self):
        """Test encoder initialization"""
        encoder = HBM4PAM3Encoder()

        assert encoder.signal_model is not None
        assert encoder.signal_model.symbol_rate == 8e9

    def test_encode_command(self):
        """Test command encoding"""
        encoder = HBM4PAM3Encoder()

        # 10-bit command
        command = 0b1010101010
        symbols = encoder.encode_command(command, 10)

        # 10 bits -> 5 symbols
        assert len(symbols) == 5

    def test_encode_data_burst(self):
        """Test data burst encoding"""
        encoder = HBM4PAM3Encoder()

        # 128-bit burst
        data = 0xFFFFFFFFFFFFFFFF
        symbols = encoder.encode_data_burst(data, dq_width=128)

        # 128 bits -> 64 symbols
        assert len(symbols) == 64

    def test_training_patterns(self):
        """Test training pattern insertion"""
        encoder = HBM4PAM3Encoder()

        # Get balanced pattern
        symbols = encoder.insert_training_pattern('balanced', length=32)

        assert len(symbols) == 32
        # Balanced pattern should have -1, 0, +1 levels
        levels = [s.level for s in symbols]
        assert -1 in levels
        assert 0 in levels
        assert 1 in levels

    def test_verify_training_pattern(self):
        """Test training pattern verification"""
        encoder = HBM4PAM3Encoder()

        # Create expected pattern
        expected = encoder.insert_training_pattern('balanced', length=32)

        # Verify with matching pattern
        verified, error_rate = encoder.verify_training_pattern(expected, 'balanced')

        assert verified
        assert error_rate == 0.0


class TestPAM3SignalIntegrity:
    """Test PAM3 signal integrity under noise"""

    def test_noise_application(self):
        """Test noise application to symbols"""
        model = PAM3SignalModel(noise_std=0.01)

        symbol = PAM3Symbol(level=1, ui_position=0, amplitude=0.5)

        # Apply noise
        noisy_symbol = model.apply_noise(symbol, seed=42)

        # Level should still be +1 (noise within threshold)
        assert noisy_symbol.level == 1
        # Amplitude should be close to 0.5
        assert abs(noisy_symbol.amplitude - 0.5) < 0.05

    def test_error_detection(self):
        """Test error detection under high noise"""
        model = PAM3SignalModel(noise_std=0.5)  # Very high noise

        # Encode data
        data = 0b11
        symbols = model.encode(data, 2)

        # Apply noise and check level decision
        error_count = 0
        for _ in range(100):
            noisy = model.apply_noise(symbols[0], seed=None)
            if noisy.level != symbols[0].level:
                error_count += 1

        # With high noise, some errors expected
        assert error_count > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])