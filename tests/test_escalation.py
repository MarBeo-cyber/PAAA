"""Escalation protocol tests.

The documented rule is: >= 5 sessions with |z| > 1.5 within a 7-day window.
Tests marked REGRESSION pin a bug found in the audit.
"""

from datetime import datetime, timedelta, timezone

import pytest

from paaa_core.config import PAAAConfig
from paaa_core.longitudinal import SessionHistory, SessionObservation
from paaa_core.models import PhysiologicalSample
from paaa_core.orchestrator import PAAAOrchestrator


NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


def history_with(z_values, feature="tremor_amplitude", spacing_days=1, config=None):
    """One session per `spacing_days`, oldest first, ending at NOW."""
    history = SessionHistory(config or PAAAConfig())
    total = len(z_values)
    for index, z in enumerate(z_values):
        history.record(SessionObservation(
            z_scores={feature: z},
            timestamp=NOW - timedelta(days=spacing_days * (total - 1 - index)),
        ))
    return history


class TestPersistenceCounting:
    """REGRESSION: the old check required *all* of the last N sessions to
    deviate and only inspected that slice. `[3.0] * 9 + [1.0]` reported
    persistent=False with sessions_deviated=4 — nine deviating sessions
    escalated nothing and the reported count was wrong."""

    def test_nine_of_ten_deviating_sessions_escalate(self):
        history = history_with([3.0] * 9 + [1.0], spacing_days=0)
        assessment = history.assess(now=NOW)
        assert assessment.escalate is True
        assert assessment.sessions_deviated["tremor_amplitude"] == 9
        assert assessment.persistent_features == ["tremor_amplitude"]

    def test_reported_count_is_the_count_used_for_the_decision(self):
        history = history_with([3.0] * 6 + [0.1] * 4, spacing_days=0)
        assessment = history.assess(now=NOW)
        assert assessment.sessions_deviated["tremor_amplitude"] == 6
        assert assessment.window_sessions == 10
        assert assessment.escalate is True

    def test_four_deviating_sessions_do_not_escalate(self):
        assessment = history_with([3.0] * 4 + [0.1] * 6, spacing_days=0).assess(now=NOW)
        assert assessment.escalate is False
        assert assessment.sessions_deviated["tremor_amplitude"] == 4

    def test_exactly_five_deviating_sessions_escalate(self):
        assessment = history_with([3.0] * 5, spacing_days=0).assess(now=NOW)
        assert assessment.escalate is True

    def test_threshold_is_absolute_z(self):
        assessment = history_with([-3.0] * 5, spacing_days=0).assess(now=NOW)
        assert assessment.escalate is True

    def test_z_exactly_at_threshold_does_not_count(self):
        assessment = history_with([1.5] * 6, spacing_days=0).assess(now=NOW)
        assert assessment.escalate is False
        assert assessment.sessions_deviated == {}


class TestTimeWindow:
    """REGRESSION: persistence_window_days was stored and never used, and
    compare() took bare floats with no timestamps, so the 7-day window was not
    expressible at all."""

    def test_sessions_outside_the_window_do_not_count(self):
        # Six deviating sessions eight days apart: only the last is in window.
        history = history_with([3.0] * 6, spacing_days=8)
        assessment = history.assess(now=NOW)
        assert assessment.window_sessions == 1
        assert assessment.escalate is False

    def test_window_boundary_is_inclusive(self):
        history = history_with([3.0] * 6, spacing_days=7)
        assert history.assess(now=NOW).window_sessions == 2

    def test_five_deviating_sessions_inside_seven_days_escalate(self):
        assessment = history_with([3.0] * 5, spacing_days=1).assess(now=NOW)
        assert assessment.window_sessions == 5
        assert assessment.escalate is True

    def test_deviations_spread_too_thin_do_not_escalate(self):
        # Five deviating sessions spread over 20 days: only 2 land in window.
        assessment = history_with([3.0] * 5, spacing_days=5).assess(now=NOW)
        assert assessment.escalate is False

    def test_window_is_configurable_from_config(self):
        config = PAAAConfig(escalation_window_days=30)
        assessment = history_with([3.0] * 5, spacing_days=5, config=config).assess(now=NOW)
        assert assessment.escalate is True

    def test_per_feature_counting(self):
        history = SessionHistory()
        for day in range(6):
            history.record(SessionObservation(
                z_scores={"tremor_amplitude": 3.0, "voice_stability": 0.2},
                timestamp=NOW - timedelta(days=5 - day),
            ))
        assessment = history.assess(now=NOW)
        assert assessment.persistent_features == ["tremor_amplitude"]
        assert "voice_stability" not in assessment.sessions_deviated


class TestOrchestratorEscalation:
    """REGRESSION: the live orchestrator scored one isolated sample with no
    session history at all, so escalation across sessions did not exist on the
    running path."""

    def _baseline(self, paaa):
        samples = [
            PhysiologicalSample(
                tremor_amplitude=0.10 + (i % 5) * 0.008,
                tremor_frequency_hz=4.0 + (i % 4) * 0.30,
                motor_smoothness=0.86 + (i % 3) * 0.025,
                reaction_latency_ms=250 + (i % 6) * 12,
                grip_stability=0.88 + (i % 4) * 0.020,
                voice_stability=0.87 + (i % 3) * 0.022,
                stress_proxy=0.15 + (i % 4) * 0.030,
            )
            for i in range(12)
        ]
        return paaa.build_baseline("test_user", samples)

    def _elevated(self):
        return PhysiologicalSample(
            tremor_amplitude=0.30, tremor_frequency_hz=4.6, motor_smoothness=0.86,
            reaction_latency_ms=270, grip_stability=0.90, voice_stability=0.89,
            stress_proxy=0.18,
        )

    def test_single_session_does_not_escalate(self):
        paaa = PAAAOrchestrator()
        baseline = self._baseline(paaa)
        plan = paaa.process(baseline, self._elevated(), timestamp=NOW)
        assert plan.escalation["escalate"] is False

    def test_five_sessions_in_window_escalate_to_review(self):
        paaa = PAAAOrchestrator()
        baseline = self._baseline(paaa)
        plan = None
        for day in range(5):
            plan = paaa.process(baseline, self._elevated(), timestamp=NOW + timedelta(days=day))
        assert plan.escalation["escalate"] is True
        assert plan.risk.value == "REVIEW"
        assert plan.requires_review is True
        assert plan.stimulation_allowed is False
        assert plan.action == "professional_review_recommended"
        assert "tremor_amplitude" in plan.escalation["persistent_features"]

    def test_escalation_message_passes_the_safety_filter(self):
        paaa = PAAAOrchestrator()
        baseline = self._baseline(paaa)
        plan = None
        for day in range(5):
            plan = paaa.process(baseline, self._elevated(), timestamp=NOW + timedelta(days=day))
        assert paaa.safety.check(plan.message).passed
        assert "baseline personale" in plan.message

    def test_sessions_spread_beyond_the_window_do_not_escalate(self):
        paaa = PAAAOrchestrator()
        baseline = self._baseline(paaa)
        plan = None
        for day in range(5):
            plan = paaa.process(baseline, self._elevated(), timestamp=NOW + timedelta(days=day * 5))
        assert plan.escalation["escalate"] is False

    def test_history_records_every_processed_session(self):
        paaa = PAAAOrchestrator()
        baseline = self._baseline(paaa)
        for day in range(3):
            paaa.process(baseline, self._elevated(), timestamp=NOW + timedelta(days=day))
        assert len(paaa.history.sessions) == 3
        assert all(s.z_scores for s in paaa.history.sessions)


def test_history_is_capped():
    history = SessionHistory(max_sessions=10)
    for _ in range(50):
        history.record(SessionObservation(z_scores={"tremor_amplitude": 0.1}))
    assert len(history.sessions) == 10
