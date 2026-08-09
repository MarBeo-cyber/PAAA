# Functional Requirements

Status reflects what is in this repository, not what is intended.

| ID | Requirement | Status |
|---|---|---|
| FR-01 | Build a personal baseline from controlled setup samples | implemented (`baseline.BaselineBuilder`) |
| FR-02 | Ingest physiological/motor samples from wearable sensors or simulated inputs | partial: simulated / caller-supplied inputs only. No sensor acquisition |
| FR-03 | Score tremor, smoothness, grip, voice, latency and stress proxy features against the personal baseline | implemented (`deviation.FEATURE_WEIGHTS` — every listed feature carries a non-zero weight) |
| FR-04 | Detect deviation from personal baseline | implemented (`deviation.DeviationDetector`) |
| FR-05 | Distinguish monitoring, biofeedback and review recommendation | implemented (`feedback.BiofeedbackPlanner`) |
| FR-06 | Prevent diagnostic claims in output | implemented (`safety.SafetyGovernor.validate_message`, called on every plan message) |
| FR-07 | Gate any stimulation plan behind explicit consent and safety policy | implemented (`safety.SafetyGovernor.stimulation_allowed`) |
| FR-08 | Preserve high-value deviation events using WAAA-style pruning | implemented (`memory.FunctionalMemory`) |
| FR-09 | Escalate persistent deviation across sessions (N-of-M within a time window) | implemented (`longitudinal.SessionHistory`), in-memory only |
| FR-10 | Provide a sensory, intuitive feedback interface | not implemented. `web/` holds a pre-scripted storyboard that does not call the engine |

FR-03 previously read "Extract ... features". PAAA does not extract features from signals; it scores precomputed ones.
