from __future__ import annotations

from .models import PhysiologicalSample, BaselineProfile, FeedbackPlan
from .baseline import BaselineBuilder
from .deviation import DeviationDetector
from .feedback import BiofeedbackPlanner
from .safety import StimulationPolicy
from .memory import FunctionalMemory


class PAAAOrchestrator:
    """Integrated PAAA loop.

    Baseline -> sample -> deviation -> safety -> biofeedback -> memory.
    """

    def __init__(self) -> None:
        self.baseline_builder = BaselineBuilder()
        self.detector = DeviationDetector()
        self.feedback = BiofeedbackPlanner()
        self.memory = FunctionalMemory()

    def build_baseline(self, user_alias: str, samples: list[PhysiologicalSample]) -> BaselineProfile:
        return self.baseline_builder.build(user_alias, samples)

    def process(self, baseline: BaselineProfile, sample: PhysiologicalSample, policy: StimulationPolicy | None = None) -> FeedbackPlan:
        state = self.detector.score(baseline, sample)
        plan = self.feedback.plan(state, policy=policy)
        self.memory.add({
            "risk": state.risk.value,
            "deviation_score": state.deviation_score,
            "stability_score": state.stability_score,
            "drivers": state.drivers,
            "action": plan.action,
            "requires_review": plan.requires_review,
            "message": plan.message,
        })
        return plan
