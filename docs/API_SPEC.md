# API Spec

All examples below are real output from `paaa_core`, not illustrative shapes.

## PhysiologicalSample (input)

```json
{
  "tremor_amplitude": 0.42,
  "tremor_frequency_hz": 5.1,
  "motor_smoothness": 0.66,
  "reaction_latency_ms": 420,
  "grip_stability": 0.68,
  "voice_stability": 0.78,
  "stress_proxy": 0.36,
  "signal_quality": "good"
}
```

`signal_quality` is one of `good`, `degraded`, `unusable`.

## FunctionalState (`DeviationDetector.score`)

```json
{
  "stability_score": 0.0496,
  "deviation_score": 0.9504,
  "risk": "REVIEW",
  "drivers": ["tremor_amplitude", "tremor_frequency_hz", "motor_smoothness",
              "reaction_latency_ms", "grip_stability", "voice_stability", "stress_proxy"],
  "confidence": 0.85,
  "non_diagnostic": true,
  "z_scores": {
    "tremor_amplitude": 26.9082,
    "tremor_frequency_hz": 1.9379,
    "motor_smoothness": 11.0229,
    "reaction_latency_ms": 6.8313,
    "grip_stability": 10.2858,
    "voice_stability": 4.899,
    "stress_proxy": 4.9194
  },
  "feature_scores": {
    "tremor_band_score": 0.42,
    "stability_loss": 0.303,
    "latency_penalty": 0.2267,
    "stress_proxy": 0.36
  }
}
```

- `z_scores` are raw, direction-adjusted (positive means "worse") and unclipped. The escalation rule uses these.
- `deviation_score` uses the same z-scores clipped to `[0, 3]` and normalised, weighted by `deviation.FEATURE_WEIGHTS`.
- `confidence` is confidence in the *comparison* — derived from signal quality, baseline size and how many baseline features have usable variance. It is not confidence in any clinical inference.
- `feature_scores` are descriptive derived scores; they do not feed `deviation_score`.

## FeedbackPlan (`PAAAOrchestrator.process`)

```json
{
  "risk": "REVIEW",
  "message": "Deviazione persistente. Valuta consulto medico.",
  "channels": ["visual", "report"],
  "action": "professional_review_recommended",
  "requires_review": true,
  "stimulation_allowed": false,
  "reason": "review_threshold_exceeded",
  "escalation": {
    "escalate": false,
    "window_sessions": 1,
    "window_days": 7,
    "z_threshold": 1.5,
    "min_sessions": 5,
    "sessions_deviated": {"tremor_amplitude": 1, "tremor_frequency_hz": 1},
    "persistent_features": []
  }
}
```

`message` has always passed `SafetyGovernor.validate_message`. `escalation` is attached to every plan, escalating or not, so a caller can always see what the persistence rule concluded.
