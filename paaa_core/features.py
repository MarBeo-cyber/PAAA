from __future__ import annotations

from .models import PhysiologicalSample


class MotorFeatureExtractor:
    """Derived motor scores over precomputed features.

    This is a scoring abstraction, not signal processing. It takes the seven
    scalars already present on a :class:`PhysiologicalSample` and derives
    interpretable secondary scores from them. There is no accelerometer, audio,
    FFT or sampling-rate handling in this package; a production implementation
    would sit upstream of this class and produce those seven scalars from IMU,
    EMG, accelerometer or microphone streams.

    All four outputs are reported on ``FunctionalState.feature_scores``. They
    are descriptive: the deviation score itself is computed from per-feature
    z-scores against the personal baseline (see :mod:`paaa_core.deviation`),
    because an absolute level says nothing about *this* user's continuity.
    """

    def extract(self, sample: PhysiologicalSample) -> dict:
        sample = sample.clamp()

        # 3.5-7.0 Hz is the band in which rest tremor is functionally relevant.
        # Amplitude outside that band is reported as zero band energy.
        tremor_band_score = 0.0
        if 3.5 <= sample.tremor_frequency_hz <= 7.0:
            tremor_band_score = sample.tremor_amplitude

        stability_loss = 1.0 - (
            0.40 * sample.motor_smoothness
            + 0.35 * sample.grip_stability
            + 0.25 * sample.voice_stability
        )

        latency_penalty = min(1.0, max(0.0, (sample.reaction_latency_ms - 250.0) / 750.0))

        return {
            "tremor_band_score": round(tremor_band_score, 4),
            "stability_loss": round(max(0.0, stability_loss), 4),
            "latency_penalty": round(latency_penalty, 4),
            "stress_proxy": round(sample.stress_proxy, 4),
        }
