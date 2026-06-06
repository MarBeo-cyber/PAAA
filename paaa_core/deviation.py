from __future__ import annotations

from .models import BaselineProfile, PhysiologicalSample, FunctionalState, FunctionalRisk
from .baseline import FEATURES
from .features import MotorFeatureExtractor


class DeviationDetector:
    """Detects deviation from personal baseline.

    It is not diagnostic. It only flags functional deviation that may deserve
    rest, recalibration, or professional review if persistent.
    """

    def __init__(self, review_threshold: float = 0.72, high_threshold: float = 0.55, medium_threshold: float = 0.35) -> None:
        self.review_threshold = review_threshold
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.extractor = MotorFeatureExtractor()

    def score(self, baseline: BaselineProfile, sample: PhysiologicalSample) -> FunctionalState:
        sample = sample.clamp()
        z_scores = {}
        drivers = []

        # Direction-aware features: increased tremor/latency/stress are bad;
        # decreased smoothness/stability is bad.
        for f in FEATURES:
            value = float(getattr(sample, f))
            mu = baseline.means[f]
            sd = max(baseline.stds[f], 1e-6)
            raw_z = (value - mu) / sd
            if f in {"motor_smoothness", "grip_stability", "voice_stability"}:
                raw_z = -raw_z
            z = max(0.0, min(3.0, raw_z)) / 3.0
            z_scores[f] = z
            if z >= 0.45:
                drivers.append(f)

        feature_scores = self.extractor.extract(sample)

        deviation = (
            0.42 * z_scores.get("tremor_amplitude", 0.0)
            + 0.18 * z_scores.get("tremor_frequency_hz", 0.0)
            + 0.14 * z_scores.get("motor_smoothness", 0.0)
            + 0.10 * z_scores.get("grip_stability", 0.0)
            + 0.08 * z_scores.get("reaction_latency_ms", 0.0)
            + 0.08 * feature_scores["stability_loss"]
        )
        deviation = max(0.0, min(1.0, deviation))
        stability = max(0.0, min(1.0, 1.0 - deviation))

        if deviation >= self.review_threshold:
            risk = FunctionalRisk.REVIEW
        elif deviation >= self.high_threshold:
            risk = FunctionalRisk.HIGH
        elif deviation >= self.medium_threshold:
            risk = FunctionalRisk.MEDIUM
        else:
            risk = FunctionalRisk.LOW

        confidence = 0.92 if sample.signal_quality.value == "good" else 0.55

        return FunctionalState(
            stability_score=round(stability, 4),
            deviation_score=round(deviation, 4),
            risk=risk,
            drivers=drivers,
            confidence=confidence,
            non_diagnostic=True,
        )
