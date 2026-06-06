from __future__ import annotations

from .models import FunctionalState, FunctionalRisk, FeedbackPlan, FeedbackChannel
from .safety import SafetyGovernor, StimulationPolicy


class BiofeedbackPlanner:
    """Plans non-diagnostic feedback."""

    def __init__(self, safety: SafetyGovernor | None = None) -> None:
        self.safety = safety or SafetyGovernor()

    def plan(self, state: FunctionalState, policy: StimulationPolicy | None = None) -> FeedbackPlan:
        policy = policy or StimulationPolicy()
        stim_ok = self.safety.stimulation_allowed(state, policy)

        if state.risk == FunctionalRisk.REVIEW:
            return FeedbackPlan(
                risk=state.risk,
                message="Deviazione persistente. Valuta consulto medico.",
                channels=[FeedbackChannel.VISUAL, FeedbackChannel.REPORT],
                action="professional_review_recommended",
                requires_review=True,
                stimulation_allowed=False,
                reason="review_threshold_exceeded",
            )

        if state.risk == FunctionalRisk.HIGH:
            return FeedbackPlan(
                risk=state.risk,
                message="Stabilità ridotta. Pausa e biofeedback guidato.",
                channels=[FeedbackChannel.VISUAL, FeedbackChannel.AUDIO, FeedbackChannel.HAPTIC],
                action="guided_pause_and_recalibration",
                requires_review=False,
                stimulation_allowed=stim_ok,
                reason="high_functional_deviation",
            )

        if state.risk == FunctionalRisk.MEDIUM:
            return FeedbackPlan(
                risk=state.risk,
                message="Micro-deviazione rilevata. Respira e stabilizza.",
                channels=[FeedbackChannel.VISUAL, FeedbackChannel.BONE_CONDUCTION],
                action="light_biofeedback",
                requires_review=False,
                stimulation_allowed=stim_ok,
                reason="medium_functional_deviation",
            )

        return FeedbackPlan(
            risk=state.risk,
            message="Stato stabile. Monitoraggio passivo.",
            channels=[FeedbackChannel.VISUAL],
            action="passive_monitoring",
            requires_review=False,
            stimulation_allowed=False,
            reason="within_baseline",
        )
