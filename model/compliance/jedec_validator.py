"""JEDEC Standard Compliance Validator"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class ComplianceLevel(Enum):
    """Compliance check levels"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class ComplianceCheck:
    """Result of a single compliance check"""
    check_name: str
    level: ComplianceLevel
    message: str
    details: Optional[Dict] = None


class JEDECValidator:
    """Validates HBM4 implementation against JEDEC JESD270-4A"""

    def __init__(self):
        self.checks: List[ComplianceCheck] = []

    def validate_timing(
        self,
        tRCD_ns: float,
        tRP_ns: float,
        tRAS_ns: float,
        tRC_ns: float
    ) -> List[ComplianceCheck]:
        """Validate DRAM timing parameters"""
        checks = []

        # JEDEC HBM4 timing constraints (simplified)
        if tRCD_ns < 8.0 or tRCD_ns > 20.0:
            checks.append(ComplianceCheck(
                check_name="tRCD_timing",
                level=ComplianceLevel.WARNING,
                message=f"tRCD={tRCD_ns}ns outside typical range (8-20ns)"
            ))

        if tRP_ns < 8.0 or tRP_ns > 20.0:
            checks.append(ComplianceCheck(
                check_name="tRP_timing",
                level=ComplianceLevel.WARNING,
                message=f"tRP={tRP_ns}ns outside typical range (8-20ns)"
            ))

        # tRC should be >= tRAS + tRP
        if tRC_ns < tRAS_ns + tRP_ns:
            checks.append(ComplianceCheck(
                check_name="tRC_consistency",
                level=ComplianceLevel.FAIL,
                message=f"tRC({tRC_ns}ns) must be >= tRAS({tRAS_ns}) + tRP({tRP_ns})"
            ))

        return checks

    def validate_power(
        self,
        active_power_w: float,
        idle_power_w: float,
        max_power_w: float = 50.0
    ) -> List[ComplianceCheck]:
        """Validate power consumption"""
        checks = []

        if active_power_w > max_power_w:
            checks.append(ComplianceCheck(
                check_name="active_power",
                level=ComplianceLevel.FAIL,
                message=f"Active power ({active_power_w}W) exceeds max ({max_power_w}W)"
            ))

        if idle_power_w > active_power_w * 0.2:
            checks.append(ComplianceCheck(
                check_name="idle_power",
                level=ComplianceLevel.WARNING,
                message="Idle power seems high relative to active power"
            ))

        return checks

    def run_all_checks(self, config: Dict) -> List[ComplianceCheck]:
        """Run all compliance checks"""
        all_checks = []

        # Timing checks
        all_checks.extend(self.validate_timing(
            tRCD_ns=config.get("tRCD_ns", 10.0),
            tRP_ns=config.get("tRP_ns", 10.0),
            tRAS_ns=config.get("tRAS_ns", 25.0),
            tRC_ns=config.get("tRC_ns", 35.0)
        ))

        # Power checks
        all_checks.extend(self.validate_power(
            active_power_w=config.get("active_power_w", 10.0),
            idle_power_w=config.get("idle_power_w", 2.0)
        ))

        return all_checks
