from __future__ import annotations

from .config import PAAAConfig
from .models import BaselineProfile, PhysiologicalSample, FunctionalState, FunctionalRisk
from .baseline import FEATURES, effective_std
from .features import MotorFeatureExtractor


# Every feature listed in FR-03 carries a real weight. A feature that can be
# reported as a driver must be able to move the score, otherwise the driver
# list is a lie. Weights sum to 1.0.
FEATURE_WEIGHTS = {
    "tremor_amplitude": 0.34,
    "tremor_frequency_hz": 0.14,
    "motor_smoothness": 0.14,
    "grip_stability": 0.12,
    "voice_stability": 0.10,
    "reaction_latency_ms": 0.10,
    "stress_proxy": 0.06,
}

# Features where a *lower* value is worse.
INVERTED_FEATURES = {"motor_smoothness", "grip_stability", "voice_stability"}

_QUALITY_WEIGHT = {"good": 1.0, "degraded": 0.6, "unusable": 0.2}

# Baseline sessions beyond which extra history no longer raises confidence.
_CONFIDENCE_SATURATION_SAMPLES = 30


class DeviationDetector:
    """Detects deviation from personal baseline.

    It is not diagnostic. It only flags functional deviation that may deserve
    rest, recalibration, or professional review if persistent.
    """

    def __init__(self, config: PAAAConfig | None = None) -> None:
        self.config = config or PAAAConfig()
        self.review_threshold = self.config.review_threshold
        self.high_threshold = self.config.high_threshold
        self.medium_threshold = self.config.medium_threshold
        self.extractor = MotorFeatureExtractor()

    def score(self, baseline: BaselineProfile, sample: PhysiologicalSample) -> FunctionalState:
        sample = sample.clamp()
        raw_z_scores = {}
        normalised = {}
        drivers = []

        # Direction-aware features: increased tremor/latency/stress are bad;
        # decreased smoothness/stability is bad.
        for f in FEATURES:
            value = float(getattr(sample, f))
            mu = baseline.means[f]
            sd = effective_std(f, baseline.stds[f])
            raw_z = (value - mu) / sd
            if f in INVERTED_FEATURES:
                raw_z = -raw_z
            raw_z_scores[f] = round(raw_z, 4)
            z = max(0.0, min(3.0, raw_z)) / 3.0
            normalised[f] = z
            if z >= self.config.driver_threshold:
                drivers.append(f)

        deviation = sum(FEATURE_WEIGHTS[f] * normalised[f] for f in FEATURES)
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

        return FunctionalState(
            stability_score=round(stability, 4),
            deviation_score=round(deviation, 4),
            risk=risk,
            drivers=drivers,
            confidence=self._confidence(baseline, sample),
            non_diagnostic=True,
            z_scores=raw_z_scores,
            feature_scores=self.extractor.extract(sample),
        )

    @staticmethod
    def _confidence(baseline: BaselineProfile, sample: PhysiologicalSample) -> float:
        """How much evidence backs this comparison.

        Derived from three things we actually know:

        - signal quality of the current sample,
        - how many sessions the baseline was built from,
        - what fraction of features have usable baseline variance (features at
          the resolution floor are scored against an assumed noise floor).

        This is confidence in the comparison, not in any clinical inference.
        """
        quality = _QUALITY_WEIGHT.get(sample.signal_quality.value, 0.2)
        history = min(1.0, baseline.sample_count / _CONFIDENCE_SATURATION_SAMPLES)
        measured = 1.0 - (len(baseline.degenerate_features) / len(FEATURES))
        return round(quality * (0.5 + 0.25 * history + 0.25 * measured), 3)
