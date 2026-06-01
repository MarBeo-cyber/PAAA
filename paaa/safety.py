"""
PAAA — Safety Governor

Enforces hard limits on all PAAA outputs.
No diagnostic claims. No disease identification. No prescriptions.
"""

from dataclasses import dataclass
from typing import Optional
import re


FORBIDDEN_TERMS = [
    "diagnosis",
    "parkinson",
    "parkinson's",
    "alzheimer",
    "alzheimer's",
    "neurological disease",
    "neurological disorder",
    "disorder detected",
    "disease detected",
    "treatment",
    "therapy",
    "prescription",
    "clinical finding",
    "pathology",
    "symptom of",
    "indicative of",
    "consistent with",
    "suggestive of",
]

PERMITTED_FRAMINGS = [
    "persistent deviation from your personal baseline",
    "change worth discussing with a healthcare professional",
    "pattern that has been consistent over recent sessions",
    "observation that may merit professional review",
    "longitudinal change in your neurofunctional profile",
]


@dataclass
class SafetyCheckResult:
    passed: bool
    original_message: str
    sanitised_message: Optional[str] = None
    violations: list[str] = None

    def __post_init__(self):
        if self.violations is None:
            self.violations = []


class SafetyGovernor:
    """
    Safety Governor for PAAA.

    Enforces hard limits on every output to ensure PAAA never:
    - Makes diagnostic claims
    - Names diseases or neurological conditions
    - Prescribes treatments
    - Replaces professional medical evaluation

    These limits are NOT configurable by the user.
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._forbidden = [t.lower() for t in FORBIDDEN_TERMS]

    def validate_message(self, message: str) -> str:
        """
        Validate output message. Raises ValueError if unsafe content detected.

        In strict mode (default): raises on any forbidden term.
        In non-strict mode: attempts sanitisation.
        """
        result = self.check(message)
        if not result.passed:
            if self.strict_mode:
                raise ValueError(
                    f"Unsafe output detected. Violations: {result.violations}. "
                    f"PAAA cannot produce diagnostic or medicalized claims."
                )
            return result.sanitised_message or message
        return message

    def check(self, message: str) -> SafetyCheckResult:
        """Check message for policy violations."""
        lower = message.lower()
        violations = [term for term in self._forbidden if term in lower]

        if not violations:
            return SafetyCheckResult(passed=True, original_message=message)

        sanitised = self._sanitise(message, violations)
        return SafetyCheckResult(
            passed=False,
            original_message=message,
            sanitised_message=sanitised,
            violations=violations,
        )

    def _sanitise(self, message: str, violations: list[str]) -> str:
        """Attempt to replace forbidden terms with safe alternatives."""
        safe = message
        replacements = {
            "diagnosis": "observation",
            "treatment": "self-care approach",
            "therapy": "supportive practice",
            "symptom": "signal",
            "disease": "condition",
            "disorder": "pattern",
        }
        for term, replacement in replacements.items():
            safe = re.sub(term, replacement, safe, flags=re.IGNORECASE)
        return safe

    def validate_report(self, report: dict) -> dict:
        """
        Validate a full report dictionary.
        Checks all string values for policy violations.
        """
        def check_value(v):
            if isinstance(v, str):
                return self.validate_message(v)
            if isinstance(v, dict):
                return {k: check_value(val) for k, val in v.items()}
            if isinstance(v, list):
                return [check_value(item) for item in v]
            return v

        return {k: check_value(v) for k, v in report.items()}

    def referral_message(self, features: list[str]) -> str:
        """
        Generate a safe referral recommendation message.
        Never names conditions. Always frames as personal observation.
        """
        feature_list = ", ".join(features) if features else "several tracked parameters"
        return (
            f"PAAA has observed a persistent deviation from your personal baseline "
            f"in the following areas: {feature_list}. "
            f"This pattern has been consistent over recent sessions. "
            f"You may wish to discuss these observations with a healthcare professional. "
            f"A structured report is available to share with your doctor."
        )
