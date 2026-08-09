from __future__ import annotations

from .models import FunctionalState, FunctionalRisk, FeedbackPlan, FeedbackChannel
from .longitudinal import EscalationAssessment
from .safety import SafetyGovernor, StimulationPolicy


class BiofeedbackPlanner:
    """Plans non-diagnostic feedback.

    Every message this class emits passes through
    :meth:`SafetyGovernor.validate_message` before the plan is returned. There
    is no path out of the planner that skips the filter.
    """

    def __init__(self, safety: SafetyGovernor | None = None) -> None:
        self.safety = safety or SafetyGovernor()

    def plan(
        self,
        state: FunctionalState,
        policy: StimulationPolicy | None = None,
        escalation: EscalationAssessment | None = None,
    ) -> FeedbackPlan:
        policy = policy or StimulationPolicy()
        stim_ok = self.safety.stimulation_allowed(state, policy)
        # The assessment travels with every plan, escalating or not, so a
        # caller can always see what the persistence rule concluded.
        assessment = escalation.to_dict() if escalation is not None else None

        # Persistent deviation across sessions overrides the single-session
        # risk band: continuity is the point, one sample is not.
        if escalation is not None and escalation.escalate:
            features = ", ".join(escalation.persistent_features)
            return self._plan(
                risk=FunctionalRisk.REVIEW,
                message=(
                    f"Deviazione persistente dalla tua baseline personale in: {features}. "
                    f"Osservata in almeno {escalation.min_sessions} sessioni negli ultimi "
                    f"{escalation.window_days} giorni. Valuta di parlarne con un "
                    f"professionista sanitario."
                ),
                channels=[FeedbackChannel.VISUAL, FeedbackChannel.REPORT],
                action="professional_review_recommended",
                requires_review=True,
                stimulation_allowed=False,
                reason="persistent_deviation_across_sessions",
                escalation=assessment,
            )

        if state.risk == FunctionalRisk.REVIEW:
            return self._plan(
                risk=state.risk,
                message="Deviazione persistente. Valuta consulto medico.",
                channels=[FeedbackChannel.VISUAL, FeedbackChannel.REPORT],
                action="professional_review_recommended",
                requires_review=self.safety.review_required(state),
                stimulation_allowed=False,
                reason="review_threshold_exceeded",
                escalation=assessment,
            )

        if state.risk == FunctionalRisk.HIGH:
            return self._plan(
                risk=state.risk,
                message="Stabilità ridotta. Pausa e biofeedback guidato.",
                channels=[FeedbackChannel.VISUAL, FeedbackChannel.AUDIO, FeedbackChannel.HAPTIC],
                action="guided_pause_and_recalibration",
                requires_review=self.safety.review_required(state),
                stimulation_allowed=stim_ok,
                reason="high_functional_deviation",
                escalation=assessment,
            )

        if state.risk == FunctionalRisk.MEDIUM:
            return self._plan(
                risk=state.risk,
                message="Micro-deviazione rilevata. Respira e stabilizza.",
                channels=[FeedbackChannel.VISUAL, FeedbackChannel.BONE_CONDUCTION],
                action="light_biofeedback",
                requires_review=self.safety.review_required(state),
                stimulation_allowed=stim_ok,
                reason="medium_functional_deviation",
                escalation=assessment,
            )

        return self._plan(
            risk=state.risk,
            message="Stato stabile. Monitoraggio passivo.",
            channels=[FeedbackChannel.VISUAL],
            action="passive_monitoring",
            requires_review=self.safety.review_required(state),
            stimulation_allowed=False,
            reason="within_baseline",
            escalation=assessment,
        )

    def _plan(self, message: str, **kwargs) -> FeedbackPlan:
        """Build a plan with the message filtered. The only constructor used."""
        return FeedbackPlan(message=self.safety.validate_message(message), **kwargs)
