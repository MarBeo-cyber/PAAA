# PAAA Architecture

## Core function

PAAA preserves **functional continuity** by comparing current physiological/motor state against a personal baseline.

## Layers

| Layer | Name | Role |
|---|---|---|
| L1 | Physiological Sensing | IMU, accelerometer, microphone, optional EMG/EEG/wearables |
| L2 | Feature Extraction | Tremor amplitude/frequency, smoothness, latency, voice/grip stability |
| L3 | Baseline & Deviation | Personal baseline, z-score deviation, persistence |
| L4 | Biofeedback Regulation | Visual/audio/haptic/bone conduction feedback |
| L5 | Safety & Continuity | consent, non-diagnostic boundary, review gates, memory pruning |

## Runtime

```text
Sample -> FeatureExtractor -> BaselineComparison -> DeviationDetector
       -> SafetyGovernor -> BiofeedbackPlanner -> FunctionalMemory
```
