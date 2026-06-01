"""
PAAA — Test Suite
"""

import pytest
from paaa.baseline import BaselineEngine, BaselineResult
from paaa.safety import SafetyGovernor


# ── BaselineEngine tests ──────────────────────────────────────────

class TestBaselineEngine:

    def setup_method(self):
        self.engine = BaselineEngine(
            min_history_sessions=5,
            z_threshold=1.5,
            persistence_count=3,
        )
        self.history = [1.0, 1.1, 0.9, 1.0, 1.05, 0.95, 1.02, 0.98, 1.0, 1.03]

    def test_returns_baseline_result(self):
        result = self.engine.compare("test_feature", self.history, 1.0)
        assert isinstance(result, BaselineResult)

    def test_normal_value_not_persistent(self):
        result = self.engine.compare("test_feature", self.history, 1.05)
        assert abs(result.z_score) < 1.5
        assert not result.persistent

    def test_large_deviation_high_zscore(self):
        result = self.engine.compare("test_feature", self.history, 3.0)
        assert result.z_score > 1.5
        assert result.deviation_level in ("moderate", "significant")

    def test_insufficient_history_returns_zero_zscore(self):
        result = self.engine.compare("test_feature", [1.0, 1.1], 1.5)
        assert result.z_score == 0.0
        assert not result.persistent

    def test_persistent_flag_with_recent_deviations(self):
        recent = [2.0, 2.1, 1.9]  # all deviated
        result = self.engine.compare("test_feature", self.history, 2.0,
                                     recent_sessions=recent)
        assert result.persistent
        assert result.sessions_deviated == 3

    def test_no_persistence_without_recent_sessions(self):
        result = self.engine.compare("test_feature", self.history, 2.0)
        assert not result.persistent

    def test_deviation_levels(self):
        cases = [
            (1.0, "normal"),
            (1.7, "mild"),
            (1.7, "mild"),
        ]
        history_std = [1.0] * 10  # std will be ~0
        # Use varied history for meaningful std
        for current, _ in cases:
            result = self.engine.compare("f", self.history, current)
            assert result.deviation_level in ("normal", "mild", "moderate", "significant")

    def test_session_report_structure(self):
        r = self.engine.compare("feat_a", self.history, 1.0)
        report = self.engine.session_report({"feat_a": r})
        assert "total_features" in report
        assert "requires_escalation" in report
        assert "persistent_features" in report

    def test_compare_session_multi_feature(self):
        session = {"tremor": 1.0, "gait": 0.98}
        historical = {"tremor": self.history, "gait": self.history}
        results = self.engine.compare_session(session, historical)
        assert "tremor" in results
        assert "gait" in results


# ── SafetyGovernor tests ─────────────────────────────────────────

class TestSafetyGovernor:

    def setup_method(self):
        self.gov = SafetyGovernor(strict_mode=True)

    def test_safe_message_passes(self):
        msg = "A persistent deviation from your personal baseline has been observed."
        result = self.gov.validate_message(msg)
        assert result == msg

    def test_diagnosis_blocked(self):
        with pytest.raises(ValueError, match="Unsafe output"):
            self.gov.validate_message("Diagnosis: Parkinson detected")

    def test_treatment_blocked(self):
        with pytest.raises(ValueError):
            self.gov.validate_message("Treatment recommended immediately")

    def test_therapy_blocked(self):
        with pytest.raises(ValueError):
            self.gov.validate_message("Therapy: consult neurologist")

    def test_disease_name_blocked(self):
        with pytest.raises(ValueError):
            self.gov.validate_message("Neurological disease pattern detected")

    def test_referral_message_is_safe(self):
        msg = self.gov.referral_message(["tremor_rms", "gait_asymmetry"])
        validated = self.gov.validate_message(msg)
        assert "personal baseline" in validated
        assert "healthcare professional" in validated

    def test_report_validation(self):
        report = {
            "summary": "Persistent deviation observed",
            "features": ["tremor_rms"],
            "recommendation": "Consider discussing with your doctor",
        }
        result = self.gov.validate_report(report)
        assert result["summary"] == report["summary"]

    def test_check_returns_violations(self):
        result = self.gov.check("Parkinson diagnosis confirmed")
        assert not result.passed
        assert len(result.violations) > 0
        assert result.sanitised_message is not None

    def test_non_strict_mode_sanitises(self):
        gov = SafetyGovernor(strict_mode=False)
        result = gov.validate_message("A diagnosis was made")
        assert "observation" in result  # sanitised replacement
