# PAAA v1.0 - Physiological Autopoietic Adaptive Agent

The **PAAA** is the functional-continuity module of the autopoietic ontology.

> Not a simulation of life, but a simulation of the functions that make life capable of persisting, learning and cooperating.

After the **WAAA**, which consolidates continuous monitoring and informational persistence, and the **MAAA**, which stabilises situated action under emergency, the **PAAA** introduces a function neither of the adjacent levels covers: preserving the physiological and neuro-functional continuity of the subject who acts and learns. A system that stabilises action in an emergency while knowing nothing about the physiological condition of the person acting operates blind.

PAAA focuses on that continuity through baseline monitoring, non-diagnostic deviation detection, biofeedback and safety-gated optional stimulation planning.

## Status

This is a **research prototype**, not a product and not a device. What that means concretely:

| Area | State |
|---|---|
| Personal baseline (per-feature mean / population std, per-feature resolution floor) | implemented, tested |
| Deviation detection (per-feature z-scores, direction-aware, weighted) | implemented, tested |
| Cross-session escalation (>= 5 sessions with \|z\| > 1.5 in 7 days) | implemented, tested, in-memory only |
| Safety Governor: output language filter on every message | implemented, tested, on the live path |
| Safety Governor: stimulation consent gating | implemented, tested |
| Functional memory with WAAA-style pruning | implemented, tested |
| Sensor acquisition (IMU, accelerometer, microphone, EMG/EEG) | **not implemented.** The package accepts seven precomputed scalars |
| Signal processing (FFT, sampling rates, dysphonia measures) | **not implemented** |
| Persistence / storage / encryption / erasure | **not implemented.** Nothing is written to disk |
| Clinical validation | **none** |

The thresholds and weights are reasoned defaults, not clinically validated parameters. No part of this repository has been evaluated against clinical data.

## Included

- Personal baseline builder
- Feature-scoring abstraction over precomputed inputs (derived motor scores; **not** signal acquisition or signal processing)
- Deviation detector
- Cross-session escalation engine
- Safety Governor (output language filter + stimulation gating)
- Biofeedback Planner
- WAAA-inspired functional memory pruning
- CLI demo
- Pre-scripted HTML storyboard of the sensory interface (see below)
- Tests

## Quickstart

Works from a clean clone, with no install:

```bash
python examples/run_demo.py
python -m pytest -q
```

Or install it:

```bash
pip install -e ".[dev]"
pytest -q
```

Requires Python 3.10+. The package itself has no third-party dependencies.

## Demos

- `examples/run_demo.py` runs the real pipeline. Every number it prints comes from `paaa_core`.
- `web/PAAA_Functional_Continuity_Demo.html` is a **pre-scripted storyboard** of the intended sensory interface. Its four buttons set fixed scores; it does not call the engine and shares no code with it. It is HTML/CSS with animated `div` elements — there is no SVG and no chart.
- `web/PAAA.mp4` is a screen recording of that storyboard.

## Safety boundary

PAAA is not a diagnostic or therapeutic medical device. It can support monitoring and suggest professional review when persistent deviations are detected, but it does not diagnose Parkinson's disease or any neurological disorder.

The boundary is enforced in code, not only in prose: every `FeedbackPlan.message` produced by the pipeline passes through `SafetyGovernor.validate_message`, which blocks diagnostic and disease-naming language in English and Italian. See `docs/SAFETY_AND_REGULATORY.md`.
