# PAAA — Technical Architecture Reference

## Five-Layer Architecture

### L1 — Passive Sensing

Continuous, non-intrusive acquisition from personal devices:

- Smartphone inertial sensors (accelerometer, gyroscope, magnetometer)
- Microphone for voice biomarker extraction
- Front camera for micro-expression analysis (optional)
- Touchscreen for guided motor tasks
- Wearable: HRV, SpO2, skin temperature, sleep (optional — Apple Watch, Oura, Garmin)
- Consumer EEG (research phase only — Emotiv, Muse)

Acquisition modes:

| Mode | Frequency | Data |
|---|---|---|
| Passive continuous | All day | IMU, steps, app interactions |
| Guided tasks | 2–3×/week | Tremor spiral, tap tests, standardised reading |
| Voice session | Daily (opt.) | 60s standardised reading passage |
| Nocturnal | Every night | Sleep, HRV, movement, temperature |

---

### L2 — Neurofunctional Feature Extraction

Signal → meaningful feature transformation per domain:

| Domain | Features | Tools |
|---|---|---|
| Tremor | FFT, spectral power 4–12 Hz, RMS | SciPy, NumPy |
| Gait | Step detection, asymmetry index, cadence variability | CoreMotion (iOS) / SensorManager (Android) |
| Fine motor | Inter-key interval, tap accuracy, spiral geometry | Custom + touchscreen API |
| Voice | Jitter, shimmer, HNR, pause duration, F0 variability | openSMILE, DisVoice, Praat |
| HRV | RMSSD, SDNN, LF/HF ratio | HeartPy, neurokit2 |
| GSR | Skin conductance level, event-related peaks | neurokit2 |

---

### L3 — Personal Baseline Engine

**Core principle: individual z-score, not population norm.**

```python
z = (current_value - personal_mean) / personal_std
# flagged only if |z| > 1.5 across ≥5 consecutive sessions in 7 days
```

Three phases:

1. **Calibration (4–8 weeks)** — acquisition without alerts; builds historical distribution
2. **Adaptive monitoring** — per-feature individual z-score with seasonal/circadian correction
3. **Escalation** — persistent deviation triggers awareness increase, report generation, clinical referral recommendation

Contextual factors tracked:
- Time of day (circadian correction)
- Day of week / seasonal patterns
- User-declared context (stress, illness, medication change)

---

### L4 — Awareness & Biofeedback

Output calibrated to increase awareness without alarmism:

- Longitudinal personal dashboard (trends, not thresholds)
- Non-intrusive notifications (contextually timed, not reactive)
- Real-time biofeedback: breathing guidance, relaxation protocols
- Exportable PDF report for healthcare professional (generated on-device via local LLM)
- Clinical referral recommendation when persistent thresholds exceeded (type of specialist indicated by deviation profile)

---

### L5 — Autopoietic Continuity

PAAA monitors its own operational quality with the same logic it applies to the user:

- Sensor quality monitoring (motion artefacts, saturation)
- Acquisition gap detection and logging
- Threshold adaptation when data quality degrades
- Watchdog process with automatic module restart
- Immutable audit log of all elaborations and outputs

---

## Memory Architecture

| Level | Type | Content | Retention |
|---|---|---|---|
| M1 Working | Current session | Raw + processed features | Session only |
| M2 Episodic | Discrete tasks/sessions | Aggregated features per session | 2 years |
| M3 Semantic | Longitudinal patterns | Trends, seasonality, evolving baseline | Unlimited |
| M4 Biographical | Clinically relevant history | Deviations, reports, consultations | Unlimited + export |

**Implementation:**
- SQLCipher for structured data (AES-256 at rest)
- LanceDB or Chroma embedded for semantic embeddings
- Optional encrypted backup to user's personal cloud (zero-knowledge)

---

## Processing Pipeline

```
Sensor acquisition (passive / task-guided)
        ↓
Feature extraction (per domain, per session)
        ↓
Personal baseline comparison (z-score + persistency filter)
        ↓
Context correction (circadian, seasonal, declared)
        ↓
Deviation assessment (persistent? threshold exceeded?)
        ↓ NO → log, continue monitoring
        ↓ YES
Awareness increase + report generation
        ↓
Clinical referral recommendation (if threshold hardcoded)
```

---

## Technology Stack

**Signal Processing:** NumPy, SciPy, librosa, openSMILE, DisVoice  
**Gait / Motor:** CoreMotion (iOS), SensorManager (Android), custom algorithms  
**HRV / Physio:** HeartPy, neurokit2  
**ML / Baseline:** scikit-learn, tsfresh, River (online learning)  
**LLM (report):** LLaMA 3.2 3B quantised (local) or API opt-in  
**Storage:** SQLCipher, LanceDB/Chroma embedded  
**UI:** Flutter (mobile), React Native  
**Privacy:** AES-256 at rest, TLS 1.3 in transit, biometric auth

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Task feedback latency | <2 seconds |
| Background battery | <5%/day |
| Local storage (2 years) | <2 GB |
| Availability | 99% (offline-first) |
| Privacy | GDPR + HIPAA-ready |
