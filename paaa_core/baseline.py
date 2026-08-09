from __future__ import annotations

from statistics import mean, pstdev

from .config import PAAAConfig
from .models import PhysiologicalSample, BaselineProfile, DomainMode


FEATURES = [
    "tremor_amplitude",
    "tremor_frequency_hz",
    "motor_smoothness",
    "reaction_latency_ms",
    "grip_stability",
    "voice_stability",
    "stress_proxy",
]


# Smallest standard deviation that is meaningful for each feature, i.e. the
# resolution floor of the estimate that produced it. A baseline whose observed
# spread is below this floor carries no usable variance information, and
# dividing by that spread would turn measurement noise into a huge z-score.
#
# | feature              | floor    | rationale                                    |
# |----------------------|----------|----------------------------------------------|
# | tremor_amplitude     | 0.01     | ~1% of the normalised 0..1 amplitude scale   |
# | tremor_frequency_hz  | 0.15 Hz  | spectral bin width of a ~7 s analysis window |
# | motor_smoothness     | 0.02     | ~2% of the normalised 0..1 scale             |
# | reaction_latency_ms  | 10.0 ms  | conservative timing resolution per trial     |
# | grip_stability       | 0.02     | ~2% of the normalised 0..1 scale             |
# | voice_stability      | 0.02     | ~2% of the normalised 0..1 scale             |
# | stress_proxy         | 0.02     | ~2% of the normalised 0..1 scale             |
FEATURE_MIN_STD = {
    "tremor_amplitude": 0.01,
    "tremor_frequency_hz": 0.15,
    "motor_smoothness": 0.02,
    "reaction_latency_ms": 10.0,
    "grip_stability": 0.02,
    "voice_stability": 0.02,
    "stress_proxy": 0.02,
}


def effective_std(feature: str, std: float) -> float:
    """Standard deviation to divide by, never below the resolution floor."""
    return max(float(std), FEATURE_MIN_STD[feature])


class BaselineBuilder:
    """Builds a personal baseline.

    PAAA is baseline-first: it does not compare the user to a generic
    population unless explicit clinical validation exists.
    """

    def __init__(self, config: PAAAConfig | None = None) -> None:
        self.config = config or PAAAConfig()

    def build(self, user_alias: str, samples: list[PhysiologicalSample], mode: DomainMode = DomainMode.MONITORING) -> BaselineProfile:
        minimum = self.config.minimum_samples
        if len(samples) < minimum:
            raise ValueError(f"At least {minimum} samples are required for a minimal baseline.")

        rows = [s.clamp() for s in samples if s.signal_quality.value == "good"]
        if len(rows) < minimum:
            raise ValueError("Insufficient good-quality samples for baseline.")

        means = {}
        stds = {}
        degenerate = []
        for f in FEATURES:
            vals = [float(getattr(s, f)) for s in rows]
            observed = pstdev(vals)
            if observed < FEATURE_MIN_STD[f]:
                # Below sensor/estimator resolution: record it, and score this
                # feature against the resolution floor instead of against a
                # spread we cannot trust.
                degenerate.append(f)
            means[f] = round(mean(vals), 6)
            stds[f] = round(effective_std(f, observed), 6)

        return BaselineProfile(
            user_alias=user_alias,
            sample_count=len(rows),
            means=means,
            stds=stds,
            domain_mode=mode,
            validity_days=self.config.validity_days,
            degenerate_features=degenerate,
        )
