"""HBM3 Compatibility Checker"""

from dataclasses import dataclass
from typing import List, Dict
from model.compliance.jedec_validator import ComplianceLevel


@dataclass
class CompatibilityResult:
    """Result of compatibility check"""
    feature: str
    compatible: bool
    notes: str


class HBM3CompatibilityChecker:
    """Checks HBM4 implementation for HBM3 backward compatibility"""

    def __init__(self):
        self.results: List[CompatibilityResult] = []

    def check_mode_support(self, hbm4_mode: str) -> CompatibilityResult:
        """Check if HBM4 mode supports HBM3 operation"""
        hbm3_modes = ["HBM3_LEGACY", "HBM3_COMPAT"]
        return CompatibilityResult(
            feature="HBM3 Mode",
            compatible=hbm4_mode in hbm3_modes,
            notes=f"Mode '{hbm4_mode}' is {'compatible' if hbm4_mode in hbm3_modes else 'not compatible'}"
        )

    def check_timing_compatibility(
        self,
        hbm4_tRCD: float,
        hbm3_tRCD: float = 10.0
    ) -> CompatibilityResult:
        """Check if timing parameters are HBM3 compatible"""
        compatible = abs(hbm4_tRCD - hbm3_tRCD) <= 2.0
        return CompatibilityResult(
            feature="Timing Parameters",
            compatible=compatible,
            notes=f"tRCD difference: {abs(hbm4_tRCD - hbm3_tRCD):.1f}ns"
        )

    def check_all(self, config: Dict) -> List[CompatibilityResult]:
        """Run all compatibility checks"""
        results = []

        results.append(self.check_mode_support(config.get("mode", "HBM4")))
        results.append(self.check_timing_compatibility(
            hbm4_tRCD=config.get("tRCD_ns", 10.0)
        ))

        return results
