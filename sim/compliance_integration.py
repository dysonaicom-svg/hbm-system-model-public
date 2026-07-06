"""Compliance Integration Module for HBM4 Validation"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from model.compliance.jedec_validator import (
    JEDECValidator,
    ComplianceCheck,
    ComplianceLevel,
)
from model.compliance.hbm3_compatibility import (
    HBM3CompatibilityChecker,
    CompatibilityResult,
)


@dataclass
class ComplianceReport:
    """Complete compliance report"""
    jedec_checks: List[ComplianceCheck]
    compatibility_results: List[CompatibilityResult]
    is_compliant: bool
    warnings: int
    failures: int

    def to_dict(self) -> Dict:
        return {
            "is_compliant": self.is_compliant,
            "warnings": self.warnings,
            "failures": self.failures,
            "jedec_checks": [
                {
                    "check_name": c.check_name,
                    "level": c.level.value,
                    "message": c.message,
                }
                for c in self.jedec_checks
            ],
            "compatibility": [
                {
                    "feature": r.feature,
                    "compatible": r.compatible,
                    "notes": r.notes,
                }
                for r in self.compatibility_results
            ],
        }


class ComplianceValidator:
    """Validates HBM4 implementation against standards"""

    def __init__(self):
        self.jedec_validator = JEDECValidator()
        self.hbm3_checker = HBM3CompatibilityChecker()

    def validate(
        self,
        timing_params: Dict,
        power_params: Dict,
        config: Dict,
    ) -> ComplianceReport:
        """Run full compliance validation"""
        jedec_checks = self.jedec_validator.run_all_checks({
            **timing_params,
            **power_params,
        })

        compatibility_results = self.hbm3_checker.check_all(config)

        warnings = sum(1 for c in jedec_checks if c.level == ComplianceLevel.WARNING)
        failures = sum(1 for c in jedec_checks if c.level == ComplianceLevel.FAIL)
        incompatible = sum(1 for r in compatibility_results if not r.compatible)

        return ComplianceReport(
            jedec_checks=jedec_checks,
            compatibility_results=compatibility_results,
            is_compliant=(failures == 0 and incompatible == 0),
            warnings=warnings,
            failures=failures,
        )

    def validate_from_simulator(self, simulator) -> ComplianceReport:
        """Validate from simulator state"""
        timing_params = {
            "tRCD_ns": getattr(simulator, 'tRCD', 10.0),
            "tRP_ns": getattr(simulator, 'tRP', 10.0),
            "tRAS_ns": getattr(simulator, 'tRAS', 25.0),
            "tRC_ns": getattr(simulator, 'tRC', 35.0),
        }

        power_params = {
            "active_power_w": getattr(simulator, 'active_power_w', 10.0),
            "idle_power_w": getattr(simulator, 'idle_power_w', 2.0),
        }

        config = {
            "mode": getattr(simulator, 'mode', 'HBM4'),
            "tRCD_ns": timing_params["tRCD_ns"],
        }

        return self.validate(timing_params, power_params, config)


def run_compliance_check(config_path: Optional[str] = None) -> ComplianceReport:
    """Run compliance check from config or defaults"""
    validator = ComplianceValidator()

    default_config = {
        "tRCD_ns": 10.0,
        "tRP_ns": 10.0,
        "tRAS_ns": 25.0,
        "tRC_ns": 35.0,
        "active_power_w": 10.0,
        "idle_power_w": 2.0,
        "mode": "HBM4",
    }

    return validator.validate(
        timing_params=default_config,
        power_params=default_config,
        config=default_config,
    )
