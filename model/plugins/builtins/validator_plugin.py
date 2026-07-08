"""Validator Plugin

Input validation plugin for HBM4 simulation.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from model.plugins.base import PluginInterface, PluginMetadata


@dataclass
class ValidationRule:
    """A validation rule"""
    field: str
    rule_type: str  # type, range, enum, custom
    constraint: Any
    message: str


@dataclass
class ValidationResult:
    """Result of validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]


class ValidatorPlugin(PluginInterface):
    """Input validation plugin"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="validator",
            version="1.0.0",
            description="Input validation for HBM4 simulation",
            author="HBM4 Team",
        )

    def _do_initialize(self, config: Dict[str, Any]) -> None:
        """Initialize validator"""
        self._rules: Dict[str, List[ValidationRule]] = {}
        self._validation_count = 0
        self._error_count = 0

        # Load default rules
        self._load_default_rules()

    def _do_start(self) -> None:
        """Start validator"""
        logging.info("ValidatorPlugin started")

    def _do_stop(self) -> None:
        """Stop validator"""
        logging.info(f"ValidatorPlugin stopped - validated {self._validation_count} items, "
                    f"{self._error_count} errors")

    def _load_default_rules(self) -> None:
        """Load default validation rules"""
        # HBM4 configuration rules
        self.add_rule(ValidationRule(
            field="hbm4.channels",
            rule_type="range",
            constraint=(1, 64),
            message="Channels must be between 1 and 64"
        ))

        self.add_rule(ValidationRule(
            field="hbm4.data_rate_gbps",
            rule_type="enum",
            constraint=[8, 12, 16],
            message="Data rate must be 8, 12, or 16 Gbps"
        ))

        self.add_rule(ValidationRule(
            field="simulation.duration_us",
            rule_type="range",
            constraint=(0, float('inf')),
            message="Duration must be positive"
        ))

        self.add_rule(ValidationRule(
            field="simulation.request_rate",
            rule_type="range",
            constraint=(0, 1),
            message="Request rate must be between 0 and 1"
        ))

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule

        Args:
            rule: Validation rule to add
        """
        if rule.field not in self._rules:
            self._rules[rule.field] = []
        self._rules[rule.field].append(rule)

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data against rules

        Args:
            data: Data to validate

        Returns:
            Validation result
        """
        self._validation_count += 1
        errors = []
        warnings = []

        for field_path, rules in self._rules.items():
            value = self._get_nested(data, field_path)

            for rule in rules:
                result = self._apply_rule(value, rule)
                if not result["valid"]:
                    errors.append(f"{field_path}: {result['message']}")

        if errors:
            self._error_count += 1

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _apply_rule(self, value: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Apply a single validation rule

        Args:
            value: Value to validate
            rule: Validation rule

        Returns:
            Result dict with 'valid' and 'message' keys
        """
        if rule.rule_type == "type":
            if not isinstance(value, rule.constraint):
                return {"valid": False, "message": rule.message}
            return {"valid": True, "message": ""}

        elif rule.rule_type == "range":
            min_val, max_val = rule.constraint
            if value is None:
                return {"valid": True, "message": ""}
            if not (min_val <= value <= max_val):
                return {"valid": False, "message": rule.message}
            return {"valid": True, "message": ""}

        elif rule.rule_type == "enum":
            if value is None:
                return {"valid": True, "message": ""}
            if value not in rule.constraint:
                return {"valid": False, "message": rule.message}
            return {"valid": True, "message": ""}

        return {"valid": True, "message": ""}

    @staticmethod
    def _get_nested(data: Dict, path: str) -> Any:
        """Get nested dictionary value"""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            **super().get_stats(),
            "validation_count": self._validation_count,
            "error_count": self._error_count,
            "rule_count": sum(len(rules) for rules in self._rules.values()),
        }


# Import logging at module level
import logging
