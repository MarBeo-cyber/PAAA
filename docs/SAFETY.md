# PAAA Safety

## Non-diagnostic boundary

The PAAA does not diagnose neurological disease. It detects deviation from a personal baseline.

This is enforced in code: every message emitted by `BiofeedbackPlanner` passes through `SafetyGovernor.validate_message`, which blocks diagnostic and disease-naming terms in English and Italian. See `SAFETY_AND_REGULATORY.md` for what the filter does and does not cover.

## Stimulation boundary

No real stimulation is actuated by this package. Stimulation is represented only as a planned output and is disabled by default. Any plan additionally requires explicit consent, an intensity ceiling of 15%, and clinical mode for HIGH/REVIEW states.

## Review trigger

Persistent or high deviation generates a recommendation for professional medical review, not a diagnosis. "Persistent" is a rule with numbers behind it: at least 5 sessions with |z| > 1.5 inside a 7-day window, evaluated by `longitudinal.SessionHistory` and reported on `FeedbackPlan.escalation`.

## Data protection

Physiological traces can be sensitive. **This package persists nothing** — no files, no database, no network. Session history lives in memory for the lifetime of the orchestrator object.

Any real deployment must be local-first with encrypted persistence, explicit consent for acquisition, and an erasure path. None of that exists here, and it must be built before PAAA touches real personal data.
