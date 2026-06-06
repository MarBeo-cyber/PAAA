from __future__ import annotations

from .models import PhysiologicalSample


class MotorFeatureExtractor:
    """Feature extraction placeholder.

    Production implementation can ingest IMU, EMG, accelerometer, microphone
    and optional wearable sensors. The prototype accepts precomputed features.
    """

    def extract(self, sample: PhysiologicalSample) -> dict:
        sample = sample.clamp()
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
            "stress_proxy": sample.stress_proxy,
        }
