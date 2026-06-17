"""
Unit Tests for DFI 5.1 Encoder (HBM4 Controller/PHY Interface)

Tests DFI 5.1 compliant encoder for HBM4 including:
- Command encoding (ACT, PRE, RD, WR, REFab, etc.)
- Address encoding for 32-channel HBM4 architecture
- Timing parameter validation
- Frequency change protocol
- Control update handshake
- Low power state management

Reference:
- DFI 5.1 Specification
- JEDEC JESD270-4A HBM4 Specification
"""

import pytest
from model.controller.dfi_encoder import (
    # Core classes
    DFI5Encoder,
    DFI5TimingParams,
    DFI5Command,
    DFIPowerState,
    DFI5PhyState,
    DFI5FreqChangeState,
    DFIEncoderError,
    DFIEncodingError,
    DFITimingError,

    # Signal bundles
    DFI5AddressSignals,
    DFI5ControlSignals,
    DFI5DataSignals,
    DFI5EncodedFrame,

    # Request/Response
    DFI5EncoderRequest,
    DFI5EncoderResponse,

    # Address decoder
    HBM4DFIAddressDecoder,

    # Convenience functions
    create_hbm4_encoder,
    encode_hbm4_request,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def encoder():
    """Create a DFI 5.1 encoder for testing"""
    return DFI5Encoder(tCK_ps=125.0)


@pytest.fixture
def encoder_12gbps():
    """Create a DFI 5.1 encoder at 12 Gbps"""
    return DFI5Encoder(tCK_ps=83.33)


@pytest.fixture
def encoder_16gbps():
    """Create a DFI 5.1 encoder at 16 Gbps"""
    return DFI5Encoder(tCK_ps=62.5)


@pytest.fixture
def timing_params():
    """Create DFI timing parameters for testing"""
    return DFI5TimingParams()


@pytest.fixture
def address_decoder():
    """Create HBM4 address decoder for testing"""
    return HBM4DFIAddressDecoder()


# =============================================================================
# Test DFI 5.1 Command Encoding
# =============================================================================

class TestDFI5CommandEncoding:
    """Test DFI 5.1 command encoding"""

    def test_encode_act_command(self, encoder):
        """Test encoding ACT (Activate) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
        )

        response = encoder.encode(request)

        assert response.success is True
        assert len(response.frames) >= 1
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.ACT.value
        assert frame.addr.dfi_channel == 0
        assert frame.addr.dfi_row == 100
        assert frame.ctrl.dfi_cmd_en is True

    def test_encode_pre_command(self, encoder):
        """Test encoding PRE (Precharge) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.PRE,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=0,
            col=0,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.PRE.value
        assert frame.ctrl.dfi_cmd_en is True

    def test_encode_prea_command(self, encoder):
        """Test encoding PREA (Precharge All) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.PREA,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=0,
            col=0,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.PREA.value

    def test_encode_rd_command(self, encoder):
        """Test encoding RD (Read) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.RD,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=10,
            is_read=True,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.RD.value
        assert frame.addr.dfi_col == 10
        assert frame.data.dfi_rddata_en == 1  # Pseudo-channel 0

    def test_encode_wr_command(self, encoder):
        """Test encoding WR (Write) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.WR,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=10,
            is_read=False,
            data=0xDEADBEEF,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.WR.value
        assert frame.data.dfi_wrdata_en == 1
        assert frame.data.dfi_wrdata == 0xDEADBEEF

    def test_encode_rd_a_command(self, encoder):
        """Test encoding RD_A (Read with Auto-Precharge) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.RD_A,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=10,
            is_read=True,
            is_auto_precharge=True,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.RD_A.value

    def test_encode_wr_a_command(self, encoder):
        """Test encoding WR_A (Write with Auto-Precharge) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.WR_A,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=10,
            is_read=False,
            is_auto_precharge=True,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.WR_A.value

    def test_encode_refab_command(self, encoder):
        """Test encoding REFab (All-Bank Refresh) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.REFab,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=0,
            col=0,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.REFab.value

    def test_encode_refsb_command(self, encoder):
        """Test encoding REFsb (Per-Bank Refresh) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.REFsb,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=0,
            col=0,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.REFsb.value

    def test_encode_nop_command(self, encoder):
        """Test encoding NOP (No Operation) command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.NOP,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=0,
            col=0,
        )

        response = encoder.encode(request)

        assert response.success is True
        frame = response.frames[0]
        assert frame.addr.dfi_cmd == DFI5Command.NOP.value


# =============================================================================
# Test HBM4 Address Decoder
# =============================================================================

class TestHBM4AddressDecoder:
    """Test HBM4 address decoder for DFI interface"""

    def test_decode_address_full(self, address_decoder):
        """Test decoding a complete HBM4 address"""
        # Create a full address with all fields set
        address = address_decoder.encode_address(
            stack=2,
            channel=15,  # Max channel
            pseudo_channel=1,
            bank_group=4,
            bank=8,
            row=256,
            column=32,
            burst=2
        )

        decoded = address_decoder.decode_address(address)

        assert decoded['stack'] == 2
        assert decoded['channel'] == 15
        assert decoded['pseudo_channel'] == 1
        assert decoded['bank_group'] == 4
        assert decoded['bank'] == 8
        assert decoded['row'] == 256
        assert decoded['column'] == 32
        assert decoded['burst'] == 2

    def test_decode_address_max_values(self, address_decoder):
        """Test decoding address with maximum field values"""
        address = address_decoder.encode_address(
            stack=3,  # Max stack (2 bits)
            channel=31,  # Max channel (5 bits, 32 channels)
            pseudo_channel=1,  # Max pseudo-channel
            bank_group=7,  # Max bank group (3 bits, 8 groups)
            bank=15,  # Max bank (4 bits, 16 banks)
            row=524287,  # Max row (19 bits, 512K rows)
            column=63,  # Max column (6 bits, 64 cols)
            burst=3  # Max burst
        )

        decoded = address_decoder.decode_address(address)

        assert decoded['stack'] == 3
        assert decoded['channel'] == 31
        assert decoded['pseudo_channel'] == 1
        assert decoded['bank_group'] == 7
        assert decoded['bank'] == 15
        assert decoded['row'] == 524287
        assert decoded['column'] == 63
        assert decoded['burst'] == 3

    def test_encode_decode_roundtrip(self, address_decoder):
        """Test encode/decode roundtrip"""
        original = {
            'stack': 1,
            'channel': 20,
            'pseudo_channel': 0,
            'bank_group': 3,
            'bank': 5,
            'row': 1000,
            'column': 20,
            'burst': 0
        }

        address = address_decoder.encode_address(**original)
        decoded = address_decoder.decode_address(address)

        assert decoded == original

    def test_validate_address_fields_valid(self, address_decoder):
        """Test validation with valid address fields"""
        valid, msg = address_decoder.validate_address_fields(
            channel=16,
            pseudo_channel=0,
            bank_group=4,
            bank=10,
            row=500,
            column=30
        )

        assert valid is True
        assert msg == ""

    def test_validate_address_fields_invalid_channel(self, address_decoder):
        """Test validation with invalid channel"""
        valid, msg = address_decoder.validate_address_fields(
            channel=32,  # Invalid: max is 31
            pseudo_channel=0,
            bank_group=4,
            bank=10,
            row=500,
            column=30
        )

        assert valid is False
        assert "Channel 32 out of range" in msg

    def test_validate_address_fields_invalid_pseudo_channel(self, address_decoder):
        """Test validation with invalid pseudo-channel"""
        valid, msg = address_decoder.validate_address_fields(
            channel=0,
            pseudo_channel=2,  # Invalid: max is 1
            bank_group=4,
            bank=10,
            row=500,
            column=30
        )

        assert valid is False
        assert "Pseudo-channel 2 out of range" in msg

    def test_validate_address_fields_invalid_bank_group(self, address_decoder):
        """Test validation with invalid bank group"""
        valid, msg = address_decoder.validate_address_fields(
            channel=0,
            pseudo_channel=0,
            bank_group=8,  # Invalid: max is 7
            bank=10,
            row=500,
            column=30
        )

        assert valid is False
        assert "Bank group 8 out of range" in msg

    def test_validate_address_fields_invalid_bank(self, address_decoder):
        """Test validation with invalid bank"""
        valid, msg = address_decoder.validate_address_fields(
            channel=0,
            pseudo_channel=0,
            bank_group=4,
            bank=16,  # Invalid: max is 15
            row=500,
            column=30
        )

        assert valid is False
        assert "Bank 16 out of range" in msg

    def test_validate_address_fields_invalid_row(self, address_decoder):
        """Test validation with invalid row"""
        valid, msg = address_decoder.validate_address_fields(
            channel=0,
            pseudo_channel=0,
            bank_group=4,
            bank=10,
            row=524288,  # Invalid: max is 524287
            column=30
        )

        assert valid is False
        assert "Row 524288 out of range" in msg

    def test_validate_address_fields_invalid_column(self, address_decoder):
        """Test validation with invalid column"""
        valid, msg = address_decoder.validate_address_fields(
            channel=0,
            pseudo_channel=0,
            bank_group=4,
            bank=10,
            row=500,
            column=64  # Invalid: max is 63
        )

        assert valid is False
        assert "Column 64 out of range" in msg

    def test_channel_count(self, address_decoder):
        """Test channel count property"""
        assert address_decoder.channel_count == 32

    def test_pseudo_channel_count(self, address_decoder):
        """Test pseudo-channel count property"""
        assert address_decoder.pseudo_channel_count == 2

    def test_bank_count(self, address_decoder):
        """Test bank count property"""
        assert address_decoder.bank_count == 16

    def test_bank_group_count(self, address_decoder):
        """Test bank group count property"""
        assert address_decoder.bank_group_count == 8


# =============================================================================
# Test DFI 5.1 Timing Parameters
# =============================================================================

class TestDFI5TimingParams:
    """Test DFI 5.1 timing parameters"""

    def test_default_timing_params(self, timing_params):
        """Test default timing parameters"""
        assert timing_params.tPHY_wrlAT == 5
        assert timing_params.tPHY_rdLat == 5
        assert timing_params.tDFI_PHY_UPD == 8
        assert timing_params.tDFI_CTRL_UPD == 8
        assert timing_params.tFC_LATENCY == 8
        assert timing_params.tLP_CTRL_ENTER == 2

    def test_write_latency_property(self, timing_params):
        """Test write latency property"""
        assert timing_params.write_latency_cycles == timing_params.tPHY_wrlAT

    def test_read_latency_property(self, timing_params):
        """Test read latency property"""
        assert timing_params.read_latency_cycles == timing_params.tPHY_rdLat

    def test_get_write_latency_ps(self, timing_params):
        """Test write latency calculation in picoseconds"""
        latency_ps = timing_params.get_write_latency_ps(125.0)
        assert latency_ps == 625.0  # 5 * 125

    def test_get_read_latency_ps(self, timing_params):
        """Test read latency calculation in picoseconds"""
        latency_ps = timing_params.get_read_latency_ps(125.0)
        assert latency_ps == 625.0  # 5 * 125

    def test_custom_timing_params(self):
        """Test custom timing parameters"""
        custom_params = DFI5TimingParams(
            tPHY_wrlAT=10,
            tPHY_rdLat=8,
            tDFI_PHY_UPD=16,
        )

        assert custom_params.tPHY_wrlAT == 10
        assert custom_params.tPHY_rdLat == 8
        assert custom_params.tDFI_PHY_UPD == 16


# =============================================================================
# Test DFI 5.1 Encoder Core
# =============================================================================

class TestDFI5EncoderCore:
    """Test DFI 5.1 encoder core functionality"""

    def test_encoder_initialization(self, encoder):
        """Test encoder initialization"""
        assert encoder.tCK_ps == 125.0
        # Frequency in MHz (8 GT/s DDR = 8000 MT/s = 8 GHz DFI clock)
        assert abs(encoder.frequency_mhz - 8000.0) < 0.01
        assert encoder.channel_count == 32

    def test_encoder_timing_checks_disabled(self):
        """Test encoder with timing checks disabled"""
        encoder = DFI5Encoder(tCK_ps=125.0, enable_timing_checks=False)
        assert encoder.enable_timing_checks is False

    def test_encoder_version(self, encoder):
        """Test encoder version"""
        assert encoder.VERSION == "5.1"

    def test_encoder_tick(self, encoder):
        """Test encoder tick advances cycle counter"""
        initial_cycle = encoder.cycle
        encoder.tick()
        assert encoder.cycle == initial_cycle + 1

    def test_encoder_multiple_ticks(self, encoder):
        """Test encoder multiple ticks"""
        for _ in range(10):
            encoder.tick()
        assert encoder.cycle == 10

    def test_encoder_reset(self, encoder):
        """Test encoder reset"""
        encoder.tick()
        encoder.tick()
        encoder.tick()
        encoder.reset()
        assert encoder.cycle == 0


# =============================================================================
# Test DFI 5.1 Encoder Address Encoding
# =============================================================================

class TestDFI5EncoderAddressEncoding:
    """Test DFI 5.1 encoder address encoding"""

    def test_encode_all_32_channels(self, encoder):
        """Test encoding commands to all 32 channels"""
        for channel in range(32):
            request = DFI5EncoderRequest(
                command=DFI5Command.ACT,
                channel=channel,
                pseudo_channel=0,
                bank=0,
                bank_group=0,
                row=100,
                col=0,
            )
            response = encoder.encode(request)
            assert response.success is True
            assert response.frames[0].addr.dfi_channel == channel

    def test_encode_both_pseudo_channels(self, encoder):
        """Test encoding commands to both pseudo-channels"""
        for pch in range(2):
            request = DFI5EncoderRequest(
                command=DFI5Command.ACT,
                channel=0,
                pseudo_channel=pch,
                bank=0,
                bank_group=0,
                row=100,
                col=0,
            )
            response = encoder.encode(request)
            assert response.success is True
            assert response.frames[0].addr.dfi_pseudo_channel == pch

    def test_encode_all_bank_groups(self, encoder):
        """Test encoding commands to all bank groups"""
        for bg in range(8):
            request = DFI5EncoderRequest(
                command=DFI5Command.ACT,
                channel=0,
                pseudo_channel=0,
                bank=0,
                bank_group=bg,
                row=100,
                col=0,
            )
            response = encoder.encode(request)
            assert response.success is True
            assert response.frames[0].addr.dfi_bank_group == bg

    def test_encode_all_banks(self, encoder):
        """Test encoding commands to all banks"""
        for bank in range(16):
            request = DFI5EncoderRequest(
                command=DFI5Command.ACT,
                channel=0,
                pseudo_channel=0,
                bank=bank,
                bank_group=0,
                row=100,
                col=0,
            )
            response = encoder.encode(request)
            assert response.success is True
            assert response.frames[0].addr.dfi_bank == bank

    def test_encode_invalid_channel(self, encoder):
        """Test encoding with invalid channel fails"""
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=32,  # Invalid: max is 31
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
        )
        response = encoder.encode(request)
        assert response.success is False
        assert "Invalid channel" in response.error_message


# =============================================================================
# Test DFI 5.1 Control Update Handshake
# =============================================================================

class TestDFI5ControlUpdateHandshake:
    """Test DFI 5.1 control update handshake"""

    def test_request_ctrlupd(self, encoder):
        """Test control update request"""
        result = encoder.request_ctrlupd()
        assert result is True

    def test_request_ctrlupd_double_request(self, encoder):
        """Test double control update request fails"""
        encoder.request_ctrlupd()
        result = encoder.request_ctrlupd()
        assert result is False

    def test_acknowledge_ctrlupd(self, encoder):
        """Test control update acknowledgment"""
        encoder.request_ctrlupd()
        result = encoder.acknowledge_ctrlupd()
        assert result is True

    def test_acknowledge_ctrlupd_without_request(self, encoder):
        """Test acknowledgment without request fails"""
        result = encoder.acknowledge_ctrlupd()
        assert result is False

    def test_get_ctrlupd_signals(self, encoder):
        """Test getting control update signals"""
        req, ack = encoder.get_ctrlupd_signals()
        assert req is False
        assert ack is False

        encoder.request_ctrlupd()
        req, ack = encoder.get_ctrlupd_signals()
        assert req is True
        assert ack is False


# =============================================================================
# Test DFI 5.1 PHY Update Handshake
# =============================================================================

class TestDFI5PHYUpdateHandshake:
    """Test DFI 5.1 PHY update handshake"""

    def test_request_phyupd(self, encoder):
        """Test PHY update request"""
        result = encoder.request_phyupd()
        assert result is True

    def test_request_phyupd_with_type(self, encoder):
        """Test PHY update request with type"""
        result = encoder.request_phyupd(update_type=1)
        assert result is True

    def test_request_phyupd_double_request(self, encoder):
        """Test double PHY update request fails"""
        encoder.request_phyupd()
        result = encoder.request_phyupd()
        assert result is False

    def test_acknowledge_phyupd(self, encoder):
        """Test PHY update acknowledgment"""
        encoder.request_phyupd()
        result = encoder.acknowledge_phyupd()
        assert result is True

    def test_acknowledge_phyupd_without_request(self, encoder):
        """Test acknowledgment without request fails"""
        result = encoder.acknowledge_phyupd()
        assert result is False

    def test_get_phyupd_signals(self, encoder):
        """Test getting PHY update signals"""
        req, ack, update_type = encoder.get_phyupd_signals()
        assert req is False
        assert ack is False


# =============================================================================
# Test DFI 5.1 Frequency Change Protocol
# =============================================================================

class TestDFI5FrequencyChangeProtocol:
    """Test DFI 5.1 frequency change protocol"""

    def test_request_freq_change(self, encoder):
        """Test frequency change request"""
        result = encoder.request_freq_change(target_freq_mhz=12000.0)
        assert result is True
        assert encoder.get_freq_change_state() == DFI5FreqChangeState.FC_REQUESTED

    def test_enter_freq_change(self, encoder):
        """Test entering frequency change"""
        encoder.request_freq_change(target_freq_mhz=12000.0)
        result = encoder.enter_freq_change()
        assert result is True
        assert encoder.get_freq_change_state() == DFI5FreqChangeState.FC_ENTERING

    def test_freq_change_full_sequence(self, encoder):
        """Test full frequency change sequence"""
        # Request frequency change to 12 Gbps
        encoder.request_freq_change(target_freq_mhz=12000.0)
        assert encoder.get_freq_change_state() == DFI5FreqChangeState.FC_REQUESTED

        # Enter frequency change
        encoder.enter_freq_change()
        assert encoder.get_freq_change_state() == DFI5FreqChangeState.FC_ENTERING

        # Advance through FC_ENTERING state
        for _ in range(10):
            encoder.tick()
            if encoder.get_freq_change_state() != DFI5FreqChangeState.FC_ENTERING:
                break
        assert encoder.get_freq_change_state() == DFI5FreqChangeState.FC_ACTIVE

        # Exit frequency change
        encoder.exit_freq_change()
        assert encoder.get_freq_change_state() == DFI5FreqChangeState.FC_EXITING

        # Advance through remaining states to IDLE
        for _ in range(30):
            encoder.tick()
            if encoder.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE:
                break

        assert encoder.get_freq_change_state() == DFI5FreqChangeState.FC_IDLE

    def test_exit_freq_change(self, encoder):
        """Test exiting frequency change"""
        encoder.request_freq_change(target_freq_mhz=12000.0)
        encoder.enter_freq_change()

        # Advance to FC_ACTIVE
        for _ in range(10):
            encoder.tick()

        result = encoder.exit_freq_change()
        assert result is True

    def test_get_freq_change_signals(self, encoder):
        """Test getting frequency change signals"""
        en, ack = encoder.get_freq_change_signals()
        assert en is False
        assert ack is False

    def test_get_freq_change_latency_remaining(self, encoder):
        """Test getting remaining latency"""
        latency = encoder.get_freq_change_latency_remaining()
        assert latency == 0

        encoder.request_freq_change(target_freq_mhz=12000.0)
        encoder.enter_freq_change()

        latency = encoder.get_freq_change_latency_remaining()
        assert latency > 0


# =============================================================================
# Test DFI 5.1 Power State Management
# =============================================================================

class TestDFI5PowerStateManagement:
    """Test DFI 5.1 power state management"""

    def test_initial_power_state(self, encoder):
        """Test initial power state is IDLE"""
        assert encoder.get_power_state() == DFIPowerState.PWR_IDLE

    def test_set_power_state_to_power_down(self, encoder):
        """Test setting power state to POWER_DOWN"""
        result = encoder.set_power_state(DFIPowerState.PWR_POWER_DOWN)
        assert result is True
        assert encoder.get_power_state() == DFIPowerState.PWR_POWER_DOWN

    def test_set_power_state_to_self_refresh(self, encoder):
        """Test setting power state to SELF_REFRESH"""
        result = encoder.set_power_state(DFIPowerState.PWR_SELF_REFRESH)
        assert result is True
        assert encoder.get_power_state() == DFIPowerState.PWR_SELF_REFRESH

    def test_set_power_state_transition(self, encoder):
        """Test power state transition from POWER_DOWN to IDLE"""
        encoder.set_power_state(DFIPowerState.PWR_POWER_DOWN)
        result = encoder.set_power_state(DFIPowerState.PWR_IDLE)
        assert result is True
        assert encoder.get_power_state() == DFIPowerState.PWR_IDLE

    def test_get_cke_power_down(self, encoder):
        """Test CKE is low during power down"""
        encoder.set_power_state(DFIPowerState.PWR_POWER_DOWN)
        cke = encoder.get_cke()
        assert cke == 0x00

    def test_get_cke_idle(self, encoder):
        """Test CKE is high during idle"""
        cke = encoder.get_cke()
        assert cke == 0xFF


# =============================================================================
# Test DFI 5.1 Latency Calculations
# =============================================================================

class TestDFI5LatencyCalculations:
    """Test DFI 5.1 latency calculations"""

    def test_read_latency_cycles(self, encoder, timing_params):
        """Test read latency in cycles"""
        request = DFI5EncoderRequest(
            command=DFI5Command.RD,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
            is_read=True,
        )
        response = encoder.encode(request)
        assert response.latency_cycles == timing_params.tPHY_rdLat

    def test_write_latency_cycles(self, encoder, timing_params):
        """Test write latency in cycles"""
        request = DFI5EncoderRequest(
            command=DFI5Command.WR,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
            is_read=False,
        )
        response = encoder.encode(request)
        assert response.latency_cycles == timing_params.tPHY_wrlAT

    def test_get_write_latency_ps(self, encoder):
        """Test getting write latency in picoseconds"""
        latency_ps = encoder.get_write_latency_ps()
        expected = encoder.timing.tPHY_wrlAT * encoder.tCK_ps
        assert latency_ps == expected

    def test_get_read_latency_ps(self, encoder):
        """Test getting read latency in picoseconds"""
        latency_ps = encoder.get_read_latency_ps()
        expected = encoder.timing.tPHY_rdLat * encoder.tCK_ps
        assert latency_ps == expected


# =============================================================================
# Test DFI 5.1 Encoder Statistics
# =============================================================================

class TestDFI5EncoderStatistics:
    """Test DFI 5.1 encoder statistics"""

    def test_initial_statistics(self, encoder):
        """Test initial statistics are zero"""
        stats = encoder.get_statistics()
        assert stats['commands_encoded'] == 0
        assert stats['frames_generated'] == 0
        assert stats['timing_violations'] == 0
        assert stats['errors'] == 0

    def test_statistics_after_encoding(self, encoder):
        """Test statistics after encoding commands"""
        for _ in range(5):
            request = DFI5EncoderRequest(
                command=DFI5Command.ACT,
                channel=0,
                pseudo_channel=0,
                bank=0,
                bank_group=0,
                row=100,
                col=0,
            )
            encoder.encode(request)

        stats = encoder.get_statistics()
        assert stats['commands_encoded'] == 5
        assert stats['frames_generated'] == 5

    def test_reset_statistics(self, encoder):
        """Test resetting statistics"""
        # Encode some commands
        for _ in range(3):
            request = DFI5EncoderRequest(
                command=DFI5Command.ACT,
                channel=0,
                pseudo_channel=0,
                bank=0,
                bank_group=0,
                row=100,
                col=0,
            )
            encoder.encode(request)

        encoder.reset_statistics()
        stats = encoder.get_statistics()
        assert stats['commands_encoded'] == 0
        assert stats['frames_generated'] == 0


# =============================================================================
# Test DFI 5.1 Signal Summary
# =============================================================================

class TestDFI5SignalSummary:
    """Test DFI 5.1 signal summary generation"""

    def test_get_dfi_signals_summary(self, encoder):
        """Test getting DFI signals summary"""
        summary = encoder.get_dfi_signals_summary()

        assert summary['version'] == "5.1"
        assert summary['frequency_mhz'] == 8000.0
        assert summary['tCK_ps'] == 125.0
        assert summary['phy_state'] == "PHY_IDLE"
        assert summary['ctrl_state'] == "PWR_IDLE"
        assert summary['fc_state'] == "FC_IDLE"
        assert 'ctrlupd_req' in summary
        assert 'ctrlupd_ack' in summary
        assert 'freq_change_en' in summary
        assert 'freq_change_ack' in summary
        assert 'cke' in summary


# =============================================================================
# Test DFI 5.1 Speed Grades
# =============================================================================

class TestDFI5SpeedGrades:
    """Test DFI 5.1 encoder at different speed grades"""

    def test_encoder_8gbps(self, encoder):
        """Test encoder at 8 Gbps"""
        assert encoder.tCK_ps == 125.0
        assert encoder.frequency_mhz == 8000.0

    def test_encoder_12gbps(self, encoder_12gbps):
        """Test encoder at 12 Gbps"""
        assert abs(encoder_12gbps.tCK_ps - 83.33) < 0.01
        assert abs(encoder_12gbps.frequency_mhz - 12000.0) < 1.0  # Allow 1 MHz tolerance

    def test_encoder_16gbps(self, encoder_16gbps):
        """Test encoder at 16 Gbps"""
        assert encoder_16gbps.tCK_ps == 62.5
        assert encoder_16gbps.frequency_mhz == 16000.0

    def test_create_hbm4_encoder_8gbps(self):
        """Test create_hbm4_encoder convenience function for 8 Gbps"""
        encoder = create_hbm4_encoder("8Gbps")
        assert encoder.tCK_ps == 125.0

    def test_create_hbm4_encoder_12gbps(self):
        """Test create_hbm4_encoder convenience function for 12 Gbps"""
        encoder = create_hbm4_encoder("12Gbps")
        assert abs(encoder.tCK_ps - 83.33) < 0.01

    def test_create_hbm4_encoder_16gbps(self):
        """Test create_hbm4_encoder convenience function for 16 Gbps"""
        encoder = create_hbm4_encoder("16Gbps")
        assert encoder.tCK_ps == 62.5

    def test_create_hbm4_encoder_invalid_speed_grade(self):
        """Test create_hbm4_encoder with invalid speed grade"""
        with pytest.raises(ValueError):
            create_hbm4_encoder("invalid")


# =============================================================================
# Test DFI 5.1 Convenience Functions
# =============================================================================

class TestDFI5ConvenienceFunctions:
    """Test DFI 5.1 convenience functions"""

    def test_encode_hbm4_request_act(self):
        """Test encode_hbm4_request for ACT command"""
        response = encode_hbm4_request(
            command='ACT',
            channel=0,
            pseudo_channel=0,
            bank_group=0,
            bank=0,
            row=100,
            col=0,
        )

        assert response.success is True
        assert response.frames[0].addr.dfi_cmd == DFI5Command.ACT.value

    def test_encode_hbm4_request_rd(self):
        """Test encode_hbm4_request for RD command"""
        response = encode_hbm4_request(
            command='RD',
            channel=0,
            pseudo_channel=0,
            bank_group=0,
            bank=0,
            row=100,
            col=10,
        )

        assert response.success is True
        assert response.frames[0].addr.dfi_cmd == DFI5Command.RD.value

    def test_encode_hbm4_request_wr(self):
        """Test encode_hbm4_request for WR command"""
        response = encode_hbm4_request(
            command='WR',
            channel=0,
            pseudo_channel=0,
            bank_group=0,
            bank=0,
            row=100,
            col=10,
        )

        assert response.success is True
        assert response.frames[0].addr.dfi_cmd == DFI5Command.WR.value

    def test_encode_hbm4_request_refab(self):
        """Test encode_hbm4_request for REFab command"""
        response = encode_hbm4_request(
            command='REFab',
            channel=0,
            pseudo_channel=0,
            bank_group=0,
            bank=0,
            row=0,
            col=0,
        )

        assert response.success is True
        assert response.frames[0].addr.dfi_cmd == DFI5Command.REFab.value


# =============================================================================
# Test DFI 5.1 Frame Generation
# =============================================================================

class TestDFI5FrameGeneration:
    """Test DFI 5.1 encoded frame generation"""

    def test_frame_has_address_signals(self, encoder):
        """Test generated frame has address signals"""
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=5,
            pseudo_channel=1,
            bank=3,
            bank_group=2,
            row=1000,
            col=0,
        )

        response = encoder.encode(request)
        frame = response.frames[0]

        assert frame.addr is not None
        assert frame.addr.dfi_channel == 5
        assert frame.addr.dfi_pseudo_channel == 1
        assert frame.addr.dfi_bank == 3
        assert frame.addr.dfi_bank_group == 2
        assert frame.addr.dfi_row == 1000

    def test_frame_has_control_signals(self, encoder):
        """Test generated frame has control signals"""
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
        )

        response = encoder.encode(request)
        frame = response.frames[0]

        assert frame.ctrl is not None
        assert frame.ctrl.dfi_cmd_en is True

    def test_frame_has_data_signals(self, encoder):
        """Test generated frame has data signals for RD/WR"""
        request = DFI5EncoderRequest(
            command=DFI5Command.RD,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
            is_read=True,
        )

        response = encoder.encode(request)
        frame = response.frames[0]

        assert frame.data is not None
        assert frame.data.dfi_rddata_en == 1

    def test_frame_metadata(self, encoder):
        """Test frame metadata"""
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
            request_id=42,
        )

        response = encoder.encode(request)
        frame = response.frames[0]

        assert frame.is_valid is True
        assert frame.request_id == 42
        assert frame.cycle == encoder.cycle


# =============================================================================
# Test DFI 5.1 Error Handling
# =============================================================================

class TestDFI5ErrorHandling:
    """Test DFI 5.1 encoder error handling"""

    def test_error_log(self, encoder):
        """Test error log is populated on errors"""
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=32,  # Invalid
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
        )

        encoder.encode(request)
        errors = encoder.get_errors()
        assert len(errors) > 0
        assert errors[0]['type'] == 'channel'


# =============================================================================
# Test DFI 5.1 Command Queue
# =============================================================================

class TestDFI5CommandQueue:
    """Test DFI 5.1 command queue management"""

    def test_queue_command(self, encoder):
        """Test queueing a command"""
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
        )

        result = encoder.queue_command(request)
        assert result is True

    def test_get_pending_commands(self, encoder):
        """Test getting pending command count"""
        request = DFI5EncoderRequest(
            command=DFI5Command.ACT,
            channel=0,
            pseudo_channel=0,
            bank=0,
            bank_group=0,
            row=100,
            col=0,
        )

        encoder.queue_command(request)
        count = encoder.get_pending_commands()
        assert count == 1


# =============================================================================
# Test DFI 5.1 Signal Bundles
# =============================================================================

class TestDFI5SignalBundles:
    """Test DFI 5.1 signal bundle classes"""

    def test_address_signals_create_empty(self):
        """Test creating empty address signals"""
        signals = DFI5AddressSignals.create_empty()
        assert signals.dfi_cmd == 0
        assert signals.dfi_channel == 0

    def test_address_signals_clear(self):
        """Test clearing address signals"""
        signals = DFI5AddressSignals()
        signals.dfi_cmd = 5
        signals.dfi_channel = 10
        signals.clear()
        assert signals.dfi_cmd == 0
        assert signals.dfi_channel == 0

    def test_control_signals_default(self):
        """Test control signals default values"""
        signals = DFI5ControlSignals()
        assert signals.dfi_cmd_en is False
        assert signals.dfi_ctrlupd_req is False
        assert signals.dfi_freq_change_en is False

    def test_data_signals_default(self):
        """Test data signals default values"""
        signals = DFI5DataSignals()
        assert signals.dfi_wrdata_en == 0
        assert signals.dfi_rddata_en == 0
        assert signals.dfi_rddata_valid is False

    def test_encoded_frame_create(self):
        """Test creating an encoded frame"""
        frame = DFI5EncodedFrame()
        assert frame.cycle == 0
        assert frame.is_valid is False
        assert frame.request_id is None


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
