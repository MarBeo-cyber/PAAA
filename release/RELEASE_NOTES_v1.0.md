# PAAA v1.0 Release Notes

## Scope

Initial GitHub-ready release for the Physiological Autopoietic Adaptive Agent.

## Included

- BaselineBuilder
- MotorFeatureExtractor (derived scores over precomputed inputs; not signal processing)
- DeviationDetector
- SessionHistory (cross-session escalation)
- SafetyGovernor (output language filter + stimulation gating)
- BiofeedbackPlanner
- FunctionalMemory
- PAAAOrchestrator
- CLI demo
- Pre-scripted HTML storyboard (not the engine)
- Tests

## Post-audit corrections

- Merged the duplicate `paaa/` package into `paaa_core/`. There is now one `SafetyGovernor` class, and its message filter runs on every `FeedbackPlan.message`.
- Filter fixed: word-boundary matching, complete replacement map, English + Italian terms, and non-strict mode now fails closed instead of returning unsanitised text.
- Replaced the 1e-6 standard-deviation floor with per-feature resolution floors, so a constant baseline feature no longer saturates the score.
- Every feature in FR-03 now carries a non-zero scoring weight; a feature reported as a driver can move the score.
- `confidence` is derived from signal quality, baseline size and baseline variance instead of being a constant.
- Escalation implemented as documented: N-of-M within a time window, counting all sessions in the window.
- Added `pyproject.toml` and `.gitignore`; `python examples/run_demo.py` and a bare `pytest` both work from a clean clone.
- `config/default.yaml` (never read) replaced by `config/default.json`, which is loaded.
- Documentation corrected: removed the AES-256-at-rest and "GDPR Article 17 implemented" claims (nothing is written to disk), the "voice feature extraction module" claim, and the "HTML/SVG" description of the web demo.

## Validation

130 automated tests pass (`python -m pytest -q`).

No clinical validation has been performed. Thresholds, weights and resolution floors are reasoned defaults.
