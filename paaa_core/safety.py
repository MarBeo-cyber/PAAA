from __future__ import annotations

from dataclasses import dataclass
from .models import FunctionalState, FunctionalRisk


@dataclass
class StimulationPolicy:
    enabled: bool = False
    max_intensity_pct: float = 15.0
    clinical_mode: bool = False
    explicit_consent: bool = False


class SafetyGovernor:
    """Safety boundary for PAAA.

    The prototype is monitoring and biofeedback-first. Stimulation is disabled
    unless explicit policy conditions are met. Even then, this code only models
    a plan; it does not actuate hardware.
    """

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
