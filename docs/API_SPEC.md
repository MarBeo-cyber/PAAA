# API Spec

## PhysiologicalSample

```json
{
  "tremor_amplitude": 0.42,
  "tremor_frequency_hz": 5.1,
  "motor_smoothness": 0.66,
  "reaction_latency_ms": 420,
  "grip_stability": 0.68,
  "voice_stability": 0.78,
  "stress_proxy": 0.36
}
```

## FeedbackPlan

```json
{
  "risk": "HIGH",
  "message": "Stabilità ridotta. Pausa e biofeedback guidato.",
  "channels": ["visual", "audio", "haptic"],
  "action": "guided_pause_and_recalibration",
  "requires_review": false,
  "stimulation_allowed": false
}
```
