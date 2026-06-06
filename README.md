# PAAA v1.0 - Physiological Autopoietic Adaptive Agent

The **PAAA** is the functional-continuity module of the autopoietic ontology.

> Not a simulation of life, but a simulation of the functions that make life capable of persisting, learning and cooperating.

PAAA focuses on physiological and neuro-functional continuity through baseline monitoring, non-diagnostic deviation detection, biofeedback and safety-gated optional stimulation planning.

## Included

- Personal baseline builder
- Motor/physiological feature extraction abstraction
- Deviation detector
- Safety Governor
- Biofeedback Planner
- WAAA-inspired functional memory pruning
- CLI demo
- HTML/SVG sensory demo
- Tests

## Quickstart

```bash
python examples/run_demo.py
python -m pytest tests -q
```

## Safety boundary

PAAA is not a diagnostic or therapeutic medical device. It can support monitoring and suggest professional review when persistent deviations are detected, but it does not diagnose Parkinson's disease or any neurological disorder.
