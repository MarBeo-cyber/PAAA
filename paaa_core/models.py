from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DomainMode(str, Enum):
    WELLNESS = "wellness"
    MONITORING = "monitoring"
    CLINICAL_REVIEW = "clinical_review"


class SignalQuality(str, Enum):
    GOOD = "good"
    DEGRADED = "degraded"
    UNUSABLE = "unusable"


class FunctionalRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    REVIEW = "REVIEW"


class FeedbackChannel(str, Enum):
    VISUAL = "visual"
    AUDIO = "audio"
    HAPTIC = "haptic"
    BONE_CONDUCTION = "bone_conduction"
    REPORT = "report"


@dataclass
class PhysiologicalSample:
    """One time-window of non-diagnostic physiological/motor observations."""

    sample_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=utc_now)
    tremor_amplitude: float = 0.0
    tremor_frequency_hz: float = 0.0
    motor_smoothness: float = 1.0
    reaction_latency_ms: float = 250.0
    grip_stability: float = 1.0
    voice_stability: float = 1.0
    stress_proxy: float = 0.0
    signal_quality: SignalQuality = SignalQuality.GOOD
    metadata: Dict = field(default_factory=dict)

    def clamp(self) -> "PhysiologicalSample":
        for name in ["tremor_amplitude", "motor_smoothness", "grip_stability", "voice_stability", "stress_proxy"]:
            setattr(self, name, max(0.0, min(1.0, float(getattr(self, name)))))
        self.tremor_frequency_hz = max(0.0, float(self.tremor_frequency_hz))
        self.reaction_latency_ms = max(0.0, float(self.reaction_latency_ms))
        return self


@dataclass
class BaselineProfile:
    """Personal baseline built in controlled setup or low-risk daily calibration.

    `stds` are floored at the per-feature resolution limit (see
    ``baseline.FEATURE_MIN_STD``). `degenerate_features` lists the features
    whose observed spread was below that limit, i.e. features for which the
    baseline carries no usable variance information.
    """

    user_alias: str
    sample_count: int
    means: Dict[str, float]
    stds: Dict[str, float]
    created_at: str = field(default_factory=utc_now)
    validity_days: int = 30
    domain_mode: DomainMode = DomainMode.MONITORING
    degenerate_features: List[str] = field(default_factory=list)


@dataclass
class FunctionalState:
    """Deviation of one sample from the personal baseline.

    `confidence` is confidence in the *comparison* (how much baseline evidence
    backs it), not confidence in any clinical inference. `z_scores` are raw,
    direction-adjusted and unclipped, so downstream escalation can apply the
    documented |z| > 1.5 rule. `feature_scores` are the derived motor scores
    reported alongside the deviation score.
    """

    stability_score: float
    deviation_score: float
    risk: FunctionalRisk
    drivers: List[str]
    confidence: float
    non_diagnostic: bool = True
    z_scores: Dict[str, float] = field(default_factory=dict)
    feature_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class FeedbackPlan:
    risk: FunctionalRisk
    message: str
    channels: List[FeedbackChannel]
    action: str
    requires_review: bool = False
    stimulation_allowed: bool = False
    reason: str = ""
    escalation: Optional[Dict] = None
