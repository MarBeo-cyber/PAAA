# Non-Functional Requirements

These are targets for a deployed PAAA. The "In this repository" column says whether the target is met by the code here.

| ID | Requirement | Target | In this repository |
|---|---|---|---|
| NFR-01 | Local-first processing | mandatory | met by default: no network calls, no third-party dependencies, nothing written to disk |
| NFR-02 | Baseline setup duration | 5-10 minutes MVP | not measured; no acquisition exists to time |
| NFR-03 | Monitoring loop latency | < 500 ms for feedback | not measured, though scoring one sample is pure arithmetic over seven scalars |
| NFR-04 | Stimulation disabled by default | mandatory | met (`StimulationPolicy.enabled = False`), tested |
| NFR-05 | Non-diagnostic language | mandatory | met by the output filter on every plan message, tested |
| NFR-06 | Review recommendation audit | mandatory | partial: `FeedbackPlan.escalation` records the counts, window and thresholds behind each escalation. Retained in memory only |
| NFR-07 | User consent for any sensitive signal | mandatory | met for stimulation. No acquisition consent flow exists because no acquisition exists |
| NFR-08 | Data at rest protection | mandatory before any deployment that stores data | **not met and not applicable**: this package stores nothing |
