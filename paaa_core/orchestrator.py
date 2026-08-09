from __future__ import annotations

from datetime import datetime
from typing import Optional

from .config import PAAAConfig
from .models import PhysiologicalSample, BaselineProfile, FeedbackPlan
from .baseline import BaselineBuilder
from .deviation import DeviationDetector
from .feedback import BiofeedbackPlanner
from .longitudinal import SessionHistory, SessionObservation
from .safety import SafetyGovernor, StimulationPolicy
from .memory import FunctionalMemory


class PAAAOrchestrator:
    """Integrated PAAA loop.

    Baseline -> sample -> deviation -> session history -> safety -> biofeedback
    -> memory.

    Session history is in-memory for the lifetime of this object. Nothing is
    written to disk.
    """

    def __init__(self, config: PAAAConfig | None = None) -> None:
        self.config = config or PAAAConfig()
        self.safety = SafetyGovernor()
        self.baseline_builder = BaselineBuilder(self.config)
        self.detector = DeviationDetector(self.config)
        self.feedback = BiofeedbackPlanner(self.safety)
        self.history = SessionHistory(self.config)
        self.memory = FunctionalMemory()

    def build_baseline(self, user_alias: str, samples: list[PhysiologicalSample]) -> BaselineProfile:
        return self.baseline_builder.build(user_alias, samples)

    def process(
        self,
        baseline: BaselineProfile,
        sample: PhysiologicalSample,
        policy: StimulationPolicy | None = None,
        timestamp: Optional[datetime] = None,
    ) -> FeedbackPlan:
        state = self.detector.score(baseline, sample)

        observation = SessionObservation(
            z_scores=state.z_scores,
            deviation_score=state.deviation_score,
            risk=state.risk.value,
        )
        if timestamp is not None:
            observation.timestamp = timestamp
        self.history.record(observation)
        escalation = self.history.assess(now=observation.timestamp)

        plan = self.feedback.plan(state, policy=policy, escalation=escalation)
        self.memory.add({
            "risk": state.risk.value,
            "deviation_score": state.deviation_score,
            "stability_score": state.stability_score,
            "drivers": state.drivers,
            "feature_scores": state.feature_scores,
            "confidence": state.confidence,
            "action": plan.action,
            "requires_review": plan.requires_review,
            "message": plan.message,
            "escalation": plan.escalation,
        })
        return plan
