"""
RTL-Python Timing Alignment Tests

Tests to verify timing parameters alignment between:
- RTL: rtl/hbm_types.svh (HBM4_TIMING_DEFAULT)
- Python: model/dram/timing.py (HBM4Timing)

Author: Claude Code (AI-driven verification)
Date: 2026-06-16
"""

import pytest
from typing import Dict, Tuple


# =============================================================================
# RTL Timing Constants (from hbm_types.svh)
# =============================================================================

# HBM4 timing at 8 GT/s DDR (tCK = 125 ps)
# From hbm_types.svh HBM4_TIMING_DEFAULT macro (line 425)
RTL_HBM4_TIMING = {
    "tRCD": 8,
    "tRP": 8,
    "tRAS": 20,
    "tRC": 22,
    "tCCD": 4,
    "tRRD": 4,
    "tFAW": 16,
    "tRFC": 180,
    "tREFI": 3900,
    "tCL": 8,
    "tCWL": 3,
}

# Bank group timing from HBM4 spec
RTL_BANK_GROUP_TIMING = {
    "nRRDS": 3,    # RAS-to-RAS delay (same BG)
    "nRRDL": 4,    # RAS-to-RAS delay (different BG)
    "nCCDS": 2,    # CAS-to-CAS delay (same BG)
    "nCCDL": 3,    # CAS-to-CAS delay (different BG)
    "nWTRS": 4,    # Write-to-read (same BG)
    "nWTRL": 5,    # Write-to-read (different BG)
    "nRTW": 4,     # Read-to-write turnaround
}

# HBM3 timing from hbm_types.svh HBM3_TIMING_DEFAULT (line 432)
RTL_HBM3_TIMING = {
    "tRCD": 17,
    "tRP": 17,
    "tRAS": 42,
    "tRC": 59,
    "tCCD": 5,
    "tRRD": 5,
    "tFAW": 26,
    "tRFC": 295,
    "tREFI": 5000,
}


# =============================================================================
# Import Python Components
# =============================================================================

from model.dram.timing import HBM3Timing, HBM4Timing
from model.dram.hbm4_spec import HBM4Spec


# =============================================================================
# Test Class: HBM4 Timing Values
# =============================================================================

class TestHBM4TimingAlignment:
    """Test HBM4 timing parameter alignment"""

    @pytest.fixture
    def python_timing(self):
        """Get Python HBM4 timing"""
        return HBM4Timing()

    @pytest.fixture
    def python_spec(self):
        """Get Python HBM4 spec"""
        return HBM4Spec()

    def test_tRCD_alignment(self, python_timing):
        """Verify tRCD (RAS to CAS delay) matches"""
        assert python_timing.nRCD == RTL_HBM4_TIMING["tRCD"], \
            f"tRCD mismatch: RTL={RTL_HBM4_TIMING['tRCD']}, Python={python_timing.nRCD}"

    def test_tRP_alignment(self, python_timing):
        """Verify tRP (precharge time) matches"""
        assert python_timing.nRP == RTL_HBM4_TIMING["tRP"], \
            f"tRP mismatch: RTL={RTL_HBM4_TIMING['tRP']}, Python={python_timing.nRP}"

    def test_tRAS_alignment(self, python_timing):
        """Verify tRAS (row active time) matches"""
        assert python_timing.nRAS == RTL_HBM4_TIMING["tRAS"], \
            f"tRAS mismatch: RTL={RTL_HBM4_TIMING['tRAS']}, Python={python_timing.nRAS}"

    def test_tRC_alignment(self, python_timing):
        """Verify tRC (row cycle time) matches"""
        assert python_timing.nRC == RTL_HBM4_TIMING["tRC"], \
            f"tRC mismatch: RTL={RTL_HBM4_TIMING['tRC']}, Python={python_timing.nRC}"

    def test_tCCD_alignment(self, python_timing):
        """Verify tCCD (CAS to CAS delay) matches"""
        assert python_timing.nCCD == RTL_HBM4_TIMING["tCCD"], \
            f"tCCD mismatch: RTL={RTL_HBM4_TIMING['tCCD']}, Python={python_timing.nCCD}"

    def test_tRRD_alignment(self, python_timing):
        """Verify tRRD (row to row delay) matches"""
        assert python_timing.nRRD == RTL_HBM4_TIMING["tRRD"], \
            f"tRRD mismatch: RTL={RTL_HBM4_TIMING['tRRD']}, Python={python_timing.nRRD}"

    def test_tFAW_alignment(self, python_timing):
        """Verify tFAW (four activate window) matches"""
        assert python_timing.nFAW == RTL_HBM4_TIMING["tFAW"], \
            f"tFAW mismatch: RTL={RTL_HBM4_TIMING['tFAW']}, Python={python_timing.nFAW}"

    def test_tRFC_alignment(self, python_timing):
        """Verify tRFC (refresh cycle) matches"""
        assert python_timing.nRFC == RTL_HBM4_TIMING["tRFC"], \
            f"tRFC mismatch: RTL={RTL_HBM4_TIMING['tRFC']}, Python={python_timing.nRFC}"

    def test_tREFI_alignment(self, python_timing):
        """Verify tREFI (refresh interval) matches"""
        assert python_timing.nREFI == RTL_HBM4_TIMING["tREFI"], \
            f"tREFI mismatch: RTL={RTL_HBM4_TIMING['tREFI']}, Python={python_timing.nREFI}"

    def test_tCL_alignment(self, python_timing):
        """Verify tCL (CAS latency) matches"""
        assert python_timing.nCL == RTL_HBM4_TIMING["tCL"], \
            f"tCL mismatch: RTL={RTL_HBM4_TIMING['tCL']}, Python={python_timing.nCL}"

    def test_tCWL_alignment(self, python_timing):
        """Verify tCWL (CAS write latency) matches"""
        assert python_timing.nCWL == RTL_HBM4_TIMING["tCWL"], \
            f"tCWL mismatch: RTL={RTL_HBM4_TIMING['tCWL']}, Python={python_timing.nCWL}"


# =============================================================================
# Test Class: Bank Group Timing
# =============================================================================

class TestBankGroupTimingAlignment:
    """Test bank group timing alignment"""

    @pytest.fixture
    def python_timing(self):
        """Get Python HBM4 timing"""
        return HBM4Timing()

    def test_nRRDS_alignment(self, python_timing):
        """Verify nRRDS (same BG RAS delay) matches"""
        assert python_timing.nRRDS == RTL_BANK_GROUP_TIMING["nRRDS"], \
            f"nRRDS mismatch: RTL={RTL_BANK_GROUP_TIMING['nRRDS']}, Python={python_timing.nRRDS}"

    def test_nRRDL_alignment(self, python_timing):
        """Verify nRRDL (different BG RAS delay) matches"""
        assert python_timing.nRRDL == RTL_BANK_GROUP_TIMING["nRRDL"], \
            f"nRRDL mismatch: RTL={RTL_BANK_GROUP_TIMING['nRRDL']}, Python={python_timing.nRRDL}"

    def test_nCCDS_alignment(self, python_timing):
        """Verify nCCDS (same BG CAS delay) matches"""
        assert python_timing.nCCDS == RTL_BANK_GROUP_TIMING["nCCDS"], \
            f"nCCDS mismatch: RTL={RTL_BANK_GROUP_TIMING['nCCDS']}, Python={python_timing.nCCDS}"

    def test_nCCDL_alignment(self, python_timing):
        """Verify nCCDL (different BG CAS delay) matches"""
        assert python_timing.nCCDL == RTL_BANK_GROUP_TIMING["nCCDL"], \
            f"nCCDL mismatch: RTL={RTL_BANK_GROUP_TIMING['nCCDL']}, Python={python_timing.nCCDL}"

    def test_nWTRS_alignment(self, python_timing):
        """Verify nWTRS (same BG write-to-read) matches"""
        assert python_timing.nWTRS == RTL_BANK_GROUP_TIMING["nWTRS"], \
            f"nWTRS mismatch: RTL={RTL_BANK_GROUP_TIMING['nWTRS']}, Python={python_timing.nWTRS}"

    def test_nWTRL_alignment(self, python_timing):
        """Verify nWTRL (different BG write-to-read) matches"""
        assert python_timing.nWTRL == RTL_BANK_GROUP_TIMING["nWTRL"], \
            f"nWTRL mismatch: RTL={RTL_BANK_GROUP_TIMING['nWTRL']}, Python={python_timing.nWTRL}"

    def test_nRTW_alignment(self, python_timing):
        """Verify nRTW (read-to-write) matches"""
        assert python_timing.nRTW == RTL_BANK_GROUP_TIMING["nRTW"], \
            f"nRTW mismatch: RTL={RTL_BANK_GROUP_TIMING['nRTW']}, Python={python_timing.nRTW}"


# =============================================================================
# Test Class: Timing Relationships
# =============================================================================

class TestTimingRelationships:
    """Test timing parameter relationships (invariants)"""

    @pytest.fixture
    def python_timing(self):
        """Get Python HBM4 timing"""
        return HBM4Timing()

    def test_tRC_greater_equal_tRAS(self, python_timing):
        """Verify tRC >= tRAS"""
        assert python_timing.nRC >= python_timing.nRAS, \
            f"tRC ({python_timing.nRC}) should be >= tRAS ({python_timing.nRAS})"

    def test_tRAS_greater_equal_tRP(self, python_timing):
        """Verify tRAS >= tRP"""
        assert python_timing.nRAS >= python_timing.nRP, \
            f"tRAS ({python_timing.nRAS}) should be >= tRP ({python_timing.nRP})"

    def test_tREFI_greater_tRFC(self, python_timing):
        """Verify tREFI > tRFC"""
        assert python_timing.nREFI > python_timing.nRFC, \
            f"tREFI ({python_timing.nREFI}) should be > tRFC ({python_timing.nRFC})"

    def test_nRRDL_greater_equal_nRRDS(self, python_timing):
        """Verify nRRDL >= nRRDS"""
        assert python_timing.nRRDL >= python_timing.nRRDS, \
            f"nRRDL ({python_timing.nRRDL}) should be >= nRRDS ({python_timing.nRRDS})"

    def test_nCCDL_greater_equal_nCCDS(self, python_timing):
        """Verify nCCDL >= nCCDS"""
        assert python_timing.nCCDL >= python_timing.nCCDS, \
            f"nCCDL ({python_timing.nCCDL}) should be >= nCCDS ({python_timing.nCCDS})"

    def test_nWTRL_greater_equal_nWTRS(self, python_timing):
        """Verify nWTRL >= nWTRS"""
        assert python_timing.nWTRL >= python_timing.nWTRS, \
            f"nWTRL ({python_timing.nWTRL}) should be >= nWTRS ({python_timing.nWTRS})"

    def test_timing_positive_values(self, python_timing):
        """Verify all timing values are positive"""
        assert python_timing.nRCD > 0, "nRCD should be positive"
        assert python_timing.nRP > 0, "nRP should be positive"
        assert python_timing.nRAS > 0, "nRAS should be positive"
        assert python_timing.nRC > 0, "nRC should be positive"
        assert python_timing.nCCD > 0, "nCCD should be positive"
        assert python_timing.nRRD > 0, "nRRD should be positive"
        assert python_timing.nFAW > 0, "nFAW should be positive"
        assert python_timing.nRFC > 0, "nRFC should be positive"
        assert python_timing.nREFI > 0, "nREFI should be positive"


# =============================================================================
# Test Class: Clock Configuration
# =============================================================================

class TestClockConfiguration:
    """Test clock configuration alignment"""

    @pytest.fixture
    def python_timing(self):
        """Get Python HBM4 timing"""
        return HBM4Timing()

    def test_clock_period_ps(self, python_timing):
        """Verify clock period matches (125 ps for 8 GT/s)"""
        assert python_timing.tCK_ps == 125.0, \
            f"Clock period should be 125 ps, got {python_timing.tCK_ps}"

    def test_clock_frequency_mhz(self, python_timing):
        """Verify clock frequency calculation"""
        expected_freq = 1000 / 125.0  # 8.0 GHz
        actual_freq = python_timing.clock_freq / 1e9  # Convert to GHz
        # Use 0.1 GHz tolerance for floating-point comparison
        assert abs(actual_freq - expected_freq) < 0.1, \
            f"Clock frequency should be ~8.0 GHz, got {actual_freq:.3f} GHz"

    def test_clock_period_ns(self, python_timing):
        """Verify clock period in nanoseconds"""
        assert python_timing.clock_period_ns == 0.125, \
            f"Clock period should be 0.125 ns, got {python_timing.clock_period_ns}"


# =============================================================================
# Test Class: HBM3 Timing Reference
# =============================================================================

class TestHBM3TimingAlignment:
    """Test HBM3 timing for reference (legacy alignment)"""

    @pytest.fixture
    def python_timing(self):
        """Get Python HBM3 timing"""
        return HBM3Timing()

    def test_hbm3_tRCD_alignment(self, python_timing):
        """Verify HBM3 tRCD matches RTL"""
        assert python_timing.tRCD == RTL_HBM3_TIMING["tRCD"], \
            f"tRCD mismatch: RTL={RTL_HBM3_TIMING['tRCD']}, Python={python_timing.tRCD}"

    def test_hbm3_tRP_alignment(self, python_timing):
        """Verify HBM3 tRP matches RTL"""
        assert python_timing.tRP == RTL_HBM3_TIMING["tRP"], \
            f"tRP mismatch: RTL={RTL_HBM3_TIMING['tRP']}, Python={python_timing.tRP}"

    def test_hbm3_tRAS_alignment(self, python_timing):
        """Verify HBM3 tRAS matches RTL"""
        assert python_timing.tRAS == RTL_HBM3_TIMING["tRAS"], \
            f"tRAS mismatch: RTL={RTL_HBM3_TIMING['tRAS']}, Python={python_timing.tRAS}"

    def test_hbm3_tRC_alignment(self, python_timing):
        """Verify HBM3 tRC matches RTL"""
        assert python_timing.tRC == RTL_HBM3_TIMING["tRC"], \
            f"tRC mismatch: RTL={RTL_HBM3_TIMING['tRC']}, Python={python_timing.tRC}"

    def test_hbm3_tCCD_alignment(self, python_timing):
        """Verify HBM3 tCCD matches RTL"""
        assert python_timing.tCCD == RTL_HBM3_TIMING["tCCD"], \
            f"tCCD mismatch: RTL={RTL_HBM3_TIMING['tCCD']}, Python={python_timing.tCCD}"

    def test_hbm3_tFAW_alignment(self, python_timing):
        """Verify HBM3 tFAW matches RTL"""
        assert python_timing.tFAW == RTL_HBM3_TIMING["tFAW"], \
            f"tFAW mismatch: RTL={RTL_HBM3_TIMING['tFAW']}, Python={python_timing.tFAW}"

    def test_hbm3_tRFC_alignment(self, python_timing):
        """Verify HBM3 tRFC matches RTL"""
        assert python_timing.tRFC == RTL_HBM3_TIMING["tRFC"], \
            f"tRFC mismatch: RTL={RTL_HBM3_TIMING['tRFC']}, Python={python_timing.tRFC}"

    def test_hbm3_tREFI_alignment(self, python_timing):
        """Verify HBM3 tREFI matches RTL"""
        assert python_timing.tREFI == RTL_HBM3_TIMING["tREFI"], \
            f"tREFI mismatch: RTL={RTL_HBM3_TIMING['tREFI']}, Python={python_timing.tREFI}"

    def test_hbm3_clock_period(self, python_timing):
        """Verify HBM3 clock period (781.25 ps for 1.28 GHz)"""
        assert python_timing.tCK_ps == 781.25, \
            f"HBM3 clock period should be 781.25 ps, got {python_timing.tCK_ps}"


# =============================================================================
# Test Class: Timing Conversion
# =============================================================================

class TestTimingConversion:
    """Test timing conversion functions"""

    @pytest.fixture
    def python_timing(self):
        """Get Python HBM4 timing"""
        return HBM4Timing()

    def test_cycles_to_ns(self, python_timing):
        """Verify cycles to nanoseconds conversion"""
        cycles = 8
        expected_ns = 8 * 0.125  # 8 cycles * 0.125 ns/cycle
        actual_ns = python_timing.cycles_to_ns(cycles)
        assert abs(actual_ns - expected_ns) < 0.001, \
            f"Expected {expected_ns} ns, got {actual_ns} ns"

    def test_cycles_to_seconds(self, python_timing):
        """Verify cycles to seconds conversion"""
        cycles = 1000
        expected_s = 1000 * 0.125e-9  # 1000 cycles * 0.125 ns * 1e-9
        actual_s = python_timing.cycles_to_seconds(cycles)
        assert abs(actual_s - expected_s) < 1e-12, \
            f"Expected {expected_s} s, got {actual_s} s"

    def test_ns_to_cycles(self, python_timing):
        """Verify nanoseconds to cycles conversion"""
        ns = 1.0
        expected_cycles = int(1.0 / 0.125 + 0.5)  # 1 ns / 0.125 ns per cycle
        actual_cycles = python_timing.ns_to_cycles(ns)
        assert actual_cycles == expected_cycles, \
            f"Expected {expected_cycles} cycles, got {actual_cycles}"


# =============================================================================
# Test Class: Spec vs Timing Alignment
# =============================================================================

class TestSpecTimingAlignment:
    """Test HBM4Spec timing values align with HBM4Timing"""

    @pytest.fixture
    def spec(self):
        """Get HBM4 spec"""
        return HBM4Spec()

    @pytest.fixture
    def timing(self):
        """Get HBM4 timing"""
        return HBM4Timing()

    def test_spec_nRCD_matches_timing(self, spec, timing):
        """Verify spec nRCD matches timing nRCD"""
        assert spec.nRCDRD == timing.nRCD, \
            f"Spec nRCDRD ({spec.nRCDRD}) should match timing nRCD ({timing.nRCD})"

    def test_spec_nRP_matches_timing(self, spec, timing):
        """Verify spec nRP matches timing nRP"""
        assert spec.nRP == timing.nRP, \
            f"Spec nRP ({spec.nRP}) should match timing nRP ({timing.nRP})"

    def test_spec_nRAS_matches_timing(self, spec, timing):
        """Verify spec nRAS matches timing nRAS"""
        assert spec.nRAS == timing.nRAS, \
            f"Spec nRAS ({spec.nRAS}) should match timing nRAS ({timing.nRAS})"

    def test_spec_nRC_matches_timing(self, spec, timing):
        """Verify spec nRC matches timing nRC"""
        assert spec.nRC == timing.nRC, \
            f"Spec nRC ({spec.nRC}) should match timing nRC ({timing.nRC})"

    def test_spec_nCL_matches_timing(self, spec, timing):
        """Verify spec nCL matches timing nCL"""
        assert spec.nCL == timing.nCL, \
            f"Spec nCL ({spec.nCL}) should match timing nCL ({timing.nCL})"

    def test_spec_nBL_matches_timing(self, spec, timing):
        """Verify spec nBL matches timing nBL"""
        assert spec.nBL == timing.nBL, \
            f"Spec nBL ({spec.nBL}) should match timing nBL ({timing.nBL})"

    def test_spec_nFAW_matches_timing(self, spec, timing):
        """Verify spec nFAW matches timing nFAW"""
        assert spec.nFAW == timing.nFAW, \
            f"Spec nFAW ({spec.nFAW}) should match timing nFAW ({timing.nFAW})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])