[![AURA Framework](https://img.shields.io/badge/AURA-Level%203%20%7C%20PAAA-1F3864)](https://github.com/MarBeo-cyber/AURA)

# PAAA — Personal Autopoietic Adaptive Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Research Prototype](https://img.shields.io/badge/status-research%20prototype-orange.svg)]()

> *PAAA does not search for disease. It searches for persistent deviations from individual neurofunctional continuity.*

PAAA is a longitudinal personal neurofunctional monitoring platform. It compares the user with their own historical baseline — not with population norms — to detect persistent deviations that may merit clinical attention.

**PAAA is not a diagnostic device. It does not identify pathologies. It supports awareness and professional consultation.**

---

## Conceptual Genealogy

| Project | Core Function | Temporal Domain |
|---|---|---|
| WAAA | Weak autopoietic perception | Seconds (cognitive cycle) |
| MAAA | Metacognitive embodied cognition in emergency | Real-time (<200ms) |
| **PAAA** | **Personal neurofunctional continuity** | **Weeks / months / years** |
| SAAA | Sapient learning consolidation | Sessions / learning cycles |

*The WAAA → MAAA → PAAA → SAAA progression constitutes an artificial ontogenesis: development by stages analogous to biological cognitive maturation.*

---

## Five-Layer Architecture

```
L1  Passive Sensing          ← smartphone, wearable, task-based acquisition
L2  Feature Extraction       ← tremor, gait, voice biomarkers, HRV, GSR
L3  Personal Baseline Engine ← individual z-score, persistency filter, seasonality
L4  Awareness & Biofeedback  ← dashboard, notifications, report export
L5  Autopoietic Continuity   ← self-monitoring of sensor quality and data validity
```

No layer compares the user to population norms. All comparison is individual-longitudinal.

---

## What PAAA Monitors

- **Tremor** — frequency and power spectrum analysis (4–12 Hz band)
- **Gait** — step detection, asymmetry, cadence variability
- **Fine motor** — keystroke dynamics, guided touch tasks
- **Voice** — jitter, shimmer, HNR, pause duration, prosody
- **HRV** — heart rate variability (autonomic indicator)
- **Sleep / recovery** — via optional wearable (Oura, Apple Watch)
- **Posture** — optional IMU analysis

---

## Personal Baseline Algorithm

```
Phase 1 — Calibration (4–8 weeks): no alerts; builds historical distribution
Phase 2 — Adaptive monitoring: individual z-score per feature
Phase 3 — Escalation: persistent deviation → awareness increase → report → clinical referral
```

Deviation is flagged only when present across ≥5 sessions in 7 days (default). Single-event anomalies are not reported.

---

## Quick Start

```bash
git clone https://github.com/MarBeo-cyber/PAAA.git
cd PAAA
pip install -r requirements.txt
pip install -e .
python examples/run_demo.py
```

---

## Safety Boundaries

PAAA enforces hard limits through its Safety Governor:

| Limit | Reason |
|---|---|
| No diagnostic output | Not a medical device |
| No disease name in output | Avoids cognitive bias in user |
| No prescription | Does not replace physician |
| Mandatory escalation threshold | Hardcoded; not user-configurable |

---

## Integration with MAAA

When MAAA is active in an emergency scenario, it can access (with prior user consent) the PAAA neurofunctional baseline to calibrate real-time cognitive state monitoring. The shared longitudinal profile enables the MAAA to distinguish genuine cognitive degradation from stress-induced performance variation.

---

## Project Structure

```
PAAA/
├── paaa/
│   ├── baseline.py         Personal Baseline Engine
│   ├── safety.py           Safety Governor
│   └── __init__.py
├── docs/
│   ├── ARCHITECTURE.md     Five-layer technical architecture
│   ├── SAFETY_AND_REGULATORY.md
│   └── references.md       Scientific foundations
├── examples/
│   └── run_demo.py
└── tests/
```

---

## Citation

```bibtex
@software{paaa2025,
  title  = {PAAA: Personal Autopoietic Adaptive Agent},
  author = {Beozzi, Marco Giuseppe},
  year   = {2025},
  url    = {https://github.com/MarBeo-cyber/PAAA},
  note   = {Part of the WAAA → MAAA → PAAA → SAAA artificial ontogenesis}
}
```
