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

The Safety Governor module enforces these limits on every output:

| Limit | Implementation |
|---|---|
| No diagnostic claims | NLP filter; forbidden terms list (see below) |
| No disease names in output | Whitelist of permitted terms |
| No prescriptions | Output always framed as "observation to investigate" |
| Mandatory escalation threshold | Hardcoded; not user-configurable |
| Required professional referral | Triggered when persistent threshold exceeded |

**Forbidden terms (partial list):**
`diagnosis`, `Parkinson detected`, `neurological disease`, `treatment`, `therapy`, `disorder detected`, `clinical finding`, `pathology identified`

---

## Escalation Protocol

When a persistent deviation is detected (≥5 sessions / 7 days, |z| > 1.5):

1. User receives an awareness notification (non-alarmist language)
2. System proposes additional targeted data collection
3. System generates a structured report for healthcare professional
4. System recommends consultation with appropriate specialist type
5. System does **not** name the suspected condition

---

## Regulatory Pathway

PAAA is currently a research prototype. A future clinical validation pathway would require:

- EU MDR Article 2(1) classification assessment
- Clinical investigation under ISO 14155
- Software as Medical Device (SaMD) assessment per IMDRF framework
- CE marking for any diagnostic claim (currently not applicable)

---

## Data Governance

- All biometric data processed on-device
- No raw biometric data transmitted to cloud
- AES-256 encryption at rest
- User retains full data ownership and deletion rights
- GDPR Article 17 (right to erasure) implemented
