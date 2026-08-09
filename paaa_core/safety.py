"""PAAA — Safety Governor.

Single safety boundary for PAAA. It has two jobs and both are enforced on the
live pipeline:

1. **Stimulation gating** — no stimulation plan is ever emitted unless explicit
   policy conditions are met. This code only models a plan; it does not actuate
   hardware.
2. **Output language gating** — no PAAA output may make a diagnostic claim,
   name a disease, or prescribe a treatment. Every ``FeedbackPlan.message``
   passes through :meth:`SafetyGovernor.validate_message` before it is returned
   by the orchestrator.

These limits are not user-configurable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .models import FunctionalState, FunctionalRisk


# ── Output language policy ────────────────────────────────────────────
#
# Terms are matched on word boundaries, so "physiotherapy" does not trip
# "therapy" and "fisioterapia" does not trip "terapia". Italian terms are
# included because the shipped runtime messages are Italian.

FORBIDDEN_TERMS = [
    # English
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
    # Italian
    "diagnosi",
    "malattia neurologica",
    "malattia",
    "disturbo neurologico",
    "patologia",
    "terapia",
    "trattamento",
    "prescrizione",
    "referto clinico",
    "sintomo di",
    "compatibile con",
    "indicativo di",
    "suggestivo di",
]

# Every forbidden term must have a replacement, otherwise sanitisation cannot
# clean a message and the governor has to fail closed. `test_safety.py`
# asserts this map covers FORBIDDEN_TERMS exactly.
REPLACEMENTS = {
    # English
    "diagnosis": "observation",
    "parkinson": "[condition name removed]",
    "parkinson's": "[condition name removed]",
    "alzheimer": "[condition name removed]",
    "alzheimer's": "[condition name removed]",
    "neurological disease": "personal-baseline deviation",
    "neurological disorder": "personal-baseline deviation",
    "disorder detected": "deviation observed",
    "disease detected": "deviation observed",
    "treatment": "self-care approach",
    "therapy": "supportive practice",
    "prescription": "suggestion",
    "clinical finding": "observation",
    "pathology": "observed pattern",
    "symptom of": "signal associated with",
    "indicative of": "observed alongside",
    "consistent with": "observed alongside",
    "suggestive of": "observed alongside",
    # Italian
    "diagnosi": "osservazione",
    "malattia neurologica": "deviazione dalla baseline personale",
    "malattia": "quadro osservato",
    "disturbo neurologico": "deviazione dalla baseline personale",
    "patologia": "quadro osservato",
    "terapia": "pratica di supporto",
    "trattamento": "approccio di autocura",
    "prescrizione": "suggerimento",
    "referto clinico": "osservazione",
    "sintomo di": "segnale associato a",
    "compatibile con": "osservato insieme a",
    "indicativo di": "osservato insieme a",
    "suggestivo di": "osservato insieme a",
}

# Benign phrases in which a forbidden term is not a medical claim. A term
# occurrence that falls inside one of these phrases is not a violation.
EXEMPT_PHRASES = [
    "treatment plant",
    "treatment plants",
    "water treatment",
    "sewage treatment",
    "waste treatment",
    "heat treatment",
    "surface treatment",
    "trattamento delle acque",
    "trattamento acque",
    "impianto di trattamento",
]

PERMITTED_FRAMINGS = [
    "persistent deviation from your personal baseline",
    "change worth discussing with a healthcare professional",
    "pattern that has been consistent over recent sessions",
    "observation that may merit professional review",
    "longitudinal change in your neurofunctional profile",
]


def _word_pattern(term: str) -> re.Pattern:
    """Compile a case-insensitive, word-boundary pattern for `term`."""
    return re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)


_FORBIDDEN_PATTERNS = {t: _word_pattern(t) for t in FORBIDDEN_TERMS}
_EXEMPT_PATTERNS = [_word_pattern(p) for p in EXEMPT_PHRASES]


@dataclass
class StimulationPolicy:
    enabled: bool = False
    max_intensity_pct: float = 15.0
    clinical_mode: bool = False
    explicit_consent: bool = False


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
    """Safety boundary for PAAA.

    Enforces hard limits on every output so that PAAA never:

    - makes diagnostic claims
    - names diseases or neurological conditions
    - prescribes treatments
    - replaces professional medical evaluation

    and never emits a stimulation plan without explicit consent.

    These limits are NOT configurable by the user.
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    # ── Stimulation gating ────────────────────────────────────────────

    def stimulation_allowed(self, state: FunctionalState, policy: StimulationPolicy) -> bool:
        if not policy.enabled:
            return False
        if not policy.explicit_consent:
            return False
        if state.risk in {FunctionalRisk.REVIEW, FunctionalRisk.HIGH} and not policy.clinical_mode:
            return False
        return 0 < policy.max_intensity_pct <= 15.0

    def review_required(self, state: FunctionalState) -> bool:
        return state.risk == FunctionalRisk.REVIEW

    # ── Output language gating ────────────────────────────────────────

    def validate_message(self, message: str) -> str:
        """Validate an outgoing message.

        Strict mode (the default, and what the pipeline uses): any forbidden
        term raises ``ValueError``.

        Non-strict mode: sanitisation is attempted first. The sanitised text is
        re-checked and only returned if it is clean. If sanitisation cannot
        produce clean text the governor **fails closed** and raises rather than
        returning unsafe text.
        """
        result = self.check(message)
        if result.passed:
            return message

        if self.strict_mode:
            raise ValueError(
                f"Unsafe output detected. Violations: {result.violations}. "
                f"PAAA cannot produce diagnostic or medicalized claims."
            )

        sanitised = result.sanitised_message or ""
        recheck = self.check(sanitised)
        if not recheck.passed:
            # Fail closed: never hand back text we could not clean.
            raise ValueError(
                f"Unsafe output could not be sanitised. Residual violations: "
                f"{recheck.violations}. PAAA fails closed rather than emitting "
                f"diagnostic or medicalized claims."
            )
        return sanitised

    def check(self, message: str) -> SafetyCheckResult:
        """Check a message for policy violations."""
        exempt_spans = self._exempt_spans(message)
        violations = []
        for term, pattern in _FORBIDDEN_PATTERNS.items():
            if any(
                not self._within(match.span(), exempt_spans)
                for match in pattern.finditer(message)
            ):
                violations.append(term)

        if not violations:
            return SafetyCheckResult(passed=True, original_message=message)

        return SafetyCheckResult(
            passed=False,
            original_message=message,
            sanitised_message=self._sanitise(message, violations),
            violations=violations,
        )

    @staticmethod
    def _exempt_spans(message: str) -> list[tuple[int, int]]:
        spans = []
        for pattern in _EXEMPT_PATTERNS:
            spans.extend(m.span() for m in pattern.finditer(message))
        return spans

    @staticmethod
    def _within(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
        return any(start <= span[0] and span[1] <= end for start, end in spans)

    def _sanitise(self, message: str, violations: list[str]) -> str:
        """Replace forbidden terms with safe alternatives.

        Longest terms first, so "neurological disease" is rewritten as a phrase
        before "malattia" or any shorter overlapping term is considered.
        Occurrences inside an exempt phrase are left untouched.
        """
        safe = message
        for term in sorted(violations, key=len, reverse=True):
            replacement = REPLACEMENTS.get(term)
            if replacement is None:
                continue
            exempt_spans = self._exempt_spans(safe)
            pattern = _FORBIDDEN_PATTERNS[term]
            out, cursor = [], 0
            for match in pattern.finditer(safe):
                if self._within(match.span(), exempt_spans):
                    continue
                out.append(safe[cursor:match.start()])
                out.append(replacement)
                cursor = match.end()
            out.append(safe[cursor:])
            safe = "".join(out)
        return safe

    def validate_report(self, report: dict) -> dict:
        """Validate a full report dictionary.

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
        """Generate a safe referral recommendation message.

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
