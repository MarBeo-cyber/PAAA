from __future__ import annotations

from statistics import mean, pstdev
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


class BaselineBuilder:
    """Builds a personal baseline.

    PAAA is baseline-first: it does not compare the user to a generic
    population unless explicit clinical validation exists.
    """

    def build(self, user_alias: str, samples: list[PhysiologicalSample], mode: DomainMode = DomainMode.MONITORING) -> BaselineProfile:
        if len(samples) < 5:
            raise ValueError("At least 5 samples are required for a minimal baseline.")

        rows = [s.clamp() for s in samples if s.signal_quality.value == "good"]
        if len(rows) < 5:
            raise ValueError("Insufficient good-quality samples for baseline.")

        means = {}
        stds = {}
        for f in FEATURES:
            vals = [float(getattr(s, f)) for s in rows]
            means[f] = round(mean(vals), 6)
            stds[f] = round(max(pstdev(vals), 1e-6), 6)

        return BaselineProfile(
            user_alias=user_alias,
            sample_count=len(rows),
            means=means,
            stds=stds,
            domain_mode=mode,
        )
