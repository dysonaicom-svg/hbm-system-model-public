"""Signal Mapping between Python Model and RTL

Maps Python model signals to RTL signals for verification alignment.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class SignalMapping:
    """Mapping between Python and RTL signal"""
    python_signal: str
    rtl_signal: str
    tolerance: int = 1  # Cycle tolerance for alignment

    def __repr__(self):
        return f"SignalMapping({self.python_signal} -> {self.rtl_signal}, tol={self.tolerance})"


class SignalMapper:
    """Maps Python model signals to RTL signals"""

    def __init__(self):
        self._mappings: Dict[str, SignalMapping] = {}

    def register_mapping(self, python_name: str, rtl_name: str, tolerance: int = 1) -> None:
        """Register a signal mapping

        Args:
            python_name: Name of signal in Python model
            rtl_name: Name of corresponding RTL signal
            tolerance: Cycle tolerance for alignment comparison
        """
        self._mappings[python_name] = SignalMapping(
            python_signal=python_name,
            rtl_signal=rtl_name,
            tolerance=tolerance
        )

    def get_mapping(self, python_name: str) -> Optional[SignalMapping]:
        """Get mapping for a Python signal"""
        return self._mappings.get(python_name)

    def get_all_mappings(self) -> List[SignalMapping]:
        """Get all registered mappings"""
        return list(self._mappings.values())

    def validate_mappings(self) -> List[str]:
        """Validate all mappings, return list of error messages"""
        errors = []
        for name, mapping in self._mappings.items():
            if not mapping.python_signal:
                errors.append(f"Empty python_signal for {name}")
            if not mapping.rtl_signal:
                errors.append(f"Empty rtl_signal for {name}")
            if mapping.tolerance < 0:
                errors.append(f"Negative tolerance for {name}")
        return errors

    def get_rtl_signal_name(self, python_name: str) -> Optional[str]:
        """Get RTL signal name for Python signal"""
        mapping = self.get_mapping(python_name)
        return mapping.rtl_signal if mapping else None

    def register_default_hbm4_mappings(self) -> None:
        """Register default HBM4 signal mappings"""
        # Request signals
        self.register_mapping("request.valid", "req_valid", tolerance=1)
        self.register_mapping("request.addr", "req_addr", tolerance=0)
        self.register_mapping("request.is_read", "req_rd_wr_n", tolerance=0)

        # Bank signals
        self.register_mapping("bank.state", "bank_st", tolerance=1)
        self.register_mapping("bank.open_row", "open_row", tolerance=0)
        self.register_mapping("bank.active", "bank_act", tolerance=1)

        # Channel signals
        self.register_mapping("channel.data_valid", "rd_data_valid", tolerance=1)
        self.register_mapping("channel.data", "rd_data", tolerance=0)

        # DFI signals
        self.register_mapping("dfi.ctrl.clk", "dfi_clk", tolerance=0)
        self.register_mapping("dfi.ctrl.rst_n", "dfi_reset_n", tolerance=0)
        self.register_mapping("dfi.write.data", "wrdata", tolerance=0)
        self.register_mapping("dfi.read.data", "rddata", tolerance=1)
