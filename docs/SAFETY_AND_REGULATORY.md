# Safety and Regulatory Notes — PAAA

## What PAAA Is

PAAA is a **research prototype** for longitudinal personal neurofunctional monitoring.

It is a **personal wellness and self-observation tool**. It supports awareness of longitudinal changes in individual neurofunctional patterns and facilitates consultation with healthcare professionals.

---

## What PAAA Is Not

PAAA **must not** be positioned or marketed as:

- a diagnostic device
- a Parkinson's detection tool
- a neurological disease screening system
- a treatment or therapy system
- a substitute for medical evaluation
- a clinical screening instrument

---

## Permitted Positioning

PAAA may be described as:

- longitudinal personal observation platform
- individual neurofunctional baseline tracker
- biofeedback and self-regulation tool
- data collection support for professional human review
- awareness support for persistent personal changes

---

## Safety Governor — Hard Limits

`paaa_core/safety.py` defines one `SafetyGovernor`. The orchestrator constructs it and shares the instance with the biofeedback planner, whose single plan constructor calls `validate_message` on every message. There is no path out of the planner that skips the filter.

| Limit | Implementation | Where |
|---|---|---|
| No diagnostic claims | Forbidden-terms filter, word-boundary matching, English + Italian | `SafetyGovernor.check` |
| No disease names in output | Same filter; disease names are in the forbidden list | `FORBIDDEN_TERMS` |
| Sanitisation never leaks unsafe text | Sanitised output is re-checked; if it is still unsafe the governor raises instead of returning it | `SafetyGovernor.validate_message` |
| No stimulation without consent | Explicit-consent + intensity-ceiling + clinical-mode gate | `SafetyGovernor.stimulation_allowed` |
| Escalation threshold | Fixed in configuration, applied by the session-history engine | `longitudinal.SessionHistory.assess` |
| Required professional referral | Emitted when the persistence rule is satisfied | `feedback.BiofeedbackPlanner.plan` |

**Forbidden terms (partial list):**
`diagnosis`, `parkinson`, `alzheimer`, `neurological disease`, `neurological disorder`, `treatment`, `therapy`, `prescription`, `clinical finding`, `pathology`, `symptom of`, `indicative of`, `consistent with`, `suggestive of`, `diagnosi`, `malattia`, `malattia neurologica`, `disturbo neurologico`, `patologia`, `terapia`, `trattamento`, `prescrizione`, `referto clinico`, `sintomo di`, `compatibile con`.

The complete list is `paaa_core.safety.FORBIDDEN_TERMS`. Italian terms are included because the shipped runtime messages are Italian.

**What the filter does not do.** It is a term filter, not natural-language understanding. It matches on word boundaries, so `physiotherapy` and `fisioterapia` are not blocked by `therapy` / `terapia`, and a short list of benign phrases (`EXEMPT_PHRASES`, e.g. "water treatment plant") is exempted. It cannot detect a diagnostic claim that avoids every listed term. It is a backstop against unsafe phrasing reaching the user, not a guarantee of safe phrasing.

---

## Escalation Protocol

A single session means nothing. Escalation requires persistence.

**Implemented rule** (`longitudinal.SessionHistory.assess`): a feature escalates when it deviates by **|z| > 1.5 in at least 5 sessions within a 7-day window**. All sessions inside the window are counted, and the count reported on the plan is the count the decision used. The parameters are `escalation_z_threshold`, `escalation_min_sessions` and `escalation_window_days` in `config/default.json`.

When the rule is satisfied:

1. User receives an awareness notification (non-alarmist language, passed through the output filter)
2. The plan is raised to `REVIEW` regardless of the single-session risk band
3. `FeedbackPlan.escalation` carries the per-feature session counts, the window and the thresholds, so the decision is auditable and can be handed to a professional
4. System recommends consultation with a healthcare professional
5. System does **not** name any suspected condition

Steps 2 and 3 of the previous version of this document ("proposes additional targeted data collection", "generates a structured report") are **not implemented**. The escalation payload is the raw material for such a report, not the report.

Session history is held in memory for the lifetime of the `PAAAOrchestrator` object.

---

## Regulatory Pathway

PAAA is currently a research prototype. A future clinical validation pathway would require:

- EU MDR Article 2(1) classification assessment
- Clinical investigation under ISO 14155
- Software as Medical Device (SaMD) assessment per IMDRF framework
- CE marking for any diagnostic claim (currently not applicable)

None of these has been started. The thresholds, weights and resolution floors in this repository are reasoned defaults, not clinically validated parameters.

---

## Data Governance

**Implemented today:** nothing is persisted. The package holds samples, baselines and session history in memory only, writes no files, opens no network connections, and has no third-party dependencies. Deleting the process deletes the data.

Because nothing is stored, there is no encryption at rest, no key management, no export path and no erasure implementation in this repository.

**Requirements for any deployment that does store data** — none of these are satisfied by this code, and all of them must be built before PAAA touches real personal data:

- on-device processing, with no raw biometric data transmitted off the device
- encryption at rest for any stored physiological trace
- user data ownership, export and deletion
- GDPR Article 17 (right to erasure) implementation, and a lawful basis for processing health-adjacent data
