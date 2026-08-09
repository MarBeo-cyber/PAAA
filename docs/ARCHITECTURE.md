# PAAA Architecture

## Core function

PAAA preserves **functional continuity** by comparing current physiological/motor state against a personal baseline.

## Layers

| Layer | Name | Role | In this repository |
|---|---|---|---|
| L1 | Physiological Sensing | IMU, accelerometer, microphone, optional EMG/EEG/wearables | **Not implemented.** L1 is the design boundary, not shipped code. The package's input contract begins at L2 |
| L2 | Feature Scoring | Derived scores over precomputed tremor amplitude/frequency, smoothness, latency, voice/grip stability, stress proxy | `features.py` — arithmetic over seven scalars. No FFT, no sampling rate, no audio |
| L3 | Baseline & Deviation | Personal baseline, per-feature z-score deviation | `baseline.py`, `deviation.py` |
| L4 | Longitudinal Continuity | Timestamped session history, N-of-M-within-window escalation | `longitudinal.py` |
| L5 | Biofeedback Regulation | Visual/audio/haptic/bone conduction feedback planning | `feedback.py` |
| L6 | Safety & Continuity | Consent gating, non-diagnostic output filter, review gates, memory pruning | `safety.py`, `memory.py` |

L1 is described because the architecture is only meaningful with it: the seven scalars have to come from somewhere. Nothing in this repository produces them. A caller supplies them, and the honest reading of `PhysiologicalSample` is "the output of an L1 that does not exist yet".

## Input contract

`PhysiologicalSample` carries seven scalars plus a signal-quality flag:

| Field | Range | Meaning |
|---|---|---|
| `tremor_amplitude` | 0..1 | normalised tremor amplitude |
| `tremor_frequency_hz` | >= 0 | dominant tremor frequency |
| `motor_smoothness` | 0..1 | higher is better |
| `reaction_latency_ms` | >= 0 | lower is better |
| `grip_stability` | 0..1 | higher is better |
| `voice_stability` | 0..1 | higher is better |
| `stress_proxy` | 0..1 | higher is worse |

## Runtime

```text
Sample -> DeviationDetector (per-feature z vs BaselineProfile)
       -> SessionHistory     (timestamped store, persistence rule)
       -> SafetyGovernor     (stimulation gating + output language filter)
       -> BiofeedbackPlanner -> FunctionalMemory
```

`MotorFeatureExtractor` runs inside `DeviationDetector` and contributes the derived scores reported on `FunctionalState.feature_scores`. The deviation score itself is computed from per-feature z-scores against the personal baseline, because an absolute level says nothing about *this* user's continuity.

Every message leaving `BiofeedbackPlanner` passes through `SafetyGovernor.validate_message`. There is one `SafetyGovernor` class in the package and the orchestrator shares its instance with the planner.

## Scoring

Deviation is a weighted sum of per-feature normalised z-scores. Weights sum to 1.0 and every feature carries a non-zero weight, so any feature reported as a driver is a feature that can move the score:

| Feature | Weight |
|---|---|
| `tremor_amplitude` | 0.34 |
| `tremor_frequency_hz` | 0.14 |
| `motor_smoothness` | 0.14 |
| `grip_stability` | 0.12 |
| `voice_stability` | 0.10 |
| `reaction_latency_ms` | 0.10 |
| `stress_proxy` | 0.06 |

Direction is inverted for `motor_smoothness`, `grip_stability` and `voice_stability`, where lower is worse.

Each feature has a minimum standard deviation (`baseline.FEATURE_MIN_STD`) representing the resolution of the estimate that produced it. A baseline whose observed spread falls below that floor is scored against the floor and recorded in `BaselineProfile.degenerate_features`; without this, a constant baseline feature turns measurement noise into a maximal z-score.

## Persistence

There is none. `SessionHistory` is in-memory and lives as long as the `PAAAOrchestrator` object. Nothing is written to disk.
