"""Safety Governor tests.

There is one SafetyGovernor (paaa_core.safety) and it is on the live path.
Tests marked REGRESSION pin a bug found in the audit.
"""

import pytest

from paaa_core import safety as safety_module
from paaa_core.deviation import DeviationDetector
from paaa_core.feedback import BiofeedbackPlanner
from paaa_core.models import (
    FeedbackChannel,
    FunctionalRisk,
    FunctionalState,
    PhysiologicalSample,
)
from paaa_core.orchestrator import PAAAOrchestrator
from paaa_core.safety import (
    FORBIDDEN_TERMS,
    PERMITTED_FRAMINGS,
    REPLACEMENTS,
    SafetyGovernor,
    StimulationPolicy,
)


# ── Message filter ────────────────────────────────────────────────────

class TestSafetyGovernor:

    def setup_method(self):
        self.gov = SafetyGovernor(strict_mode=True)

    def test_safe_message_passes(self):
        msg = "A persistent deviation from your personal baseline has been observed."
        assert self.gov.validate_message(msg) == msg

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
        assert self.gov.validate_report(report)["summary"] == report["summary"]

    def test_check_returns_violations(self):
        result = self.gov.check("Parkinson diagnosis confirmed")
        assert not result.passed
        assert len(result.violations) > 0
        assert result.sanitised_message is not None

    def test_non_strict_mode_sanitises(self):
        gov = SafetyGovernor(strict_mode=False)
        assert "observation" in gov.validate_message("A diagnosis was made")

    def test_permitted_framings_pass_the_filter(self):
        # The whitelist and the blacklist must not contradict each other.
        for framing in PERMITTED_FRAMINGS:
            assert self.gov.check(framing).passed, framing


class TestWordBoundaryMatching:
    """REGRESSION: matching used `term in lower`, so any word *containing* a
    forbidden term was blocked. `physiotherapy` tripped `therapy` and
    `treatment plant` tripped `treatment`."""

    def setup_method(self):
        self.gov = SafetyGovernor(strict_mode=True)

    @pytest.mark.parametrize("message", [
        "Bring this to your physiotherapy session",
        "Portalo alla seduta di fisioterapia",
        "Hydrotherapy and aromatherapy are unrelated to this reading",
    ])
    def test_word_containing_forbidden_term_is_not_blocked(self, message):
        assert self.gov.validate_message(message) == message

    @pytest.mark.parametrize("message", [
        "Water treatment plant reading",
        "Impianto di trattamento delle acque",
    ])
    def test_exempt_phrase_is_not_blocked(self, message):
        assert self.gov.validate_message(message) == message

    def test_standalone_term_still_blocked(self):
        # The exemption must not punch a hole in the actual policy.
        with pytest.raises(ValueError):
            self.gov.validate_message("Treatment recommended immediately")
        with pytest.raises(ValueError):
            self.gov.validate_message("Start therapy now")


class TestNonStrictFailsClosed:
    """REGRESSION: non-strict mode returned unsafe text unchanged, because
    `_sanitise` had replacements for only 6 of the 18 forbidden terms.
    `SafetyGovernor(strict_mode=False).validate_message("Parkinson detected")`
    returned "Parkinson detected"."""

    def test_unreplaceable_term_is_never_returned_verbatim(self):
        gov = SafetyGovernor(strict_mode=False)
        out = gov.validate_message("Parkinson detected")
        assert "parkinson" not in out.lower()
        assert gov.check(out).passed

    @pytest.mark.parametrize("term", FORBIDDEN_TERMS)
    def test_every_forbidden_term_is_sanitised_or_refused(self, term):
        gov = SafetyGovernor(strict_mode=False)
        message = f"Report: {term} observed today."
        out = gov.validate_message(message)
        assert gov.check(out).passed
        assert term.lower() not in out.lower()

    def test_replacement_map_covers_every_forbidden_term(self):
        assert set(REPLACEMENTS) == set(FORBIDDEN_TERMS)

    def test_no_replacement_reintroduces_a_forbidden_term(self):
        gov = SafetyGovernor(strict_mode=True)
        for replacement in REPLACEMENTS.values():
            assert gov.check(replacement).passed, replacement

    def test_fails_closed_when_sanitisation_cannot_clean(self, monkeypatch):
        # If the replacement map is ever incomplete again, the governor must
        # raise rather than hand back unsafe text.
        monkeypatch.delitem(safety_module.REPLACEMENTS, "parkinson")
        gov = SafetyGovernor(strict_mode=False)
        with pytest.raises(ValueError, match="could not be sanitised"):
            gov.validate_message("Parkinson detected")


class TestItalianTerms:
    """The shipped runtime messages are Italian; the filter must speak it."""

    def setup_method(self):
        self.gov = SafetyGovernor(strict_mode=True)

    @pytest.mark.parametrize("message", [
        "Diagnosi di malattia neurologica",
        "Iniziare la terapia il prima possibile",
        "Referto clinico allegato",
        "Quadro compatibile con patologia degenerativa",
        "Prescrizione di trattamento farmacologico",
    ])
    def test_italian_medical_claims_blocked(self, message):
        with pytest.raises(ValueError):
            self.gov.validate_message(message)

    @pytest.mark.parametrize("message", [
        "Deviazione persistente. Valuta consulto medico.",
        "Stabilità ridotta. Pausa e biofeedback guidato.",
        "Micro-deviazione rilevata. Respira e stabilizza.",
        "Stato stabile. Monitoraggio passivo.",
    ])
    def test_shipped_runtime_messages_pass(self, message):
        assert self.gov.validate_message(message) == message


# ── The filter is wired into the pipeline ─────────────────────────────

class TestFilterIsOnTheLivePath:
    """REGRESSION: the documented Safety Governor was in an unreachable
    package. Runtime messages were hardcoded strings that never touched a
    filter."""

    def _baseline(self, paaa):
        samples = [
            PhysiologicalSample(
                tremor_amplitude=0.10 + i * 0.004,
                tremor_frequency_hz=4.1 + i * 0.05,
                motor_smoothness=0.90 - i * 0.005,
                reaction_latency_ms=250 + i * 4,
                grip_stability=0.92 - i * 0.004,
                voice_stability=0.91 - i * 0.004,
                stress_proxy=0.15 + i * 0.005,
            )
            for i in range(8)
        ]
        return paaa.build_baseline("test_user", samples)

    def test_planner_filters_every_message_it_builds(self):
        planner = BiofeedbackPlanner()
        with pytest.raises(ValueError, match="Unsafe output"):
            planner._plan(
                risk=FunctionalRisk.LOW,
                message="Diagnosis: Parkinson detected",
                channels=[FeedbackChannel.VISUAL],
                action="passive_monitoring",
            )

    def test_orchestrator_message_passed_through_validate_message(self, monkeypatch):
        paaa = PAAAOrchestrator()
        baseline = self._baseline(paaa)
        seen = []
        original = SafetyGovernor.validate_message

        def spy(self, message):
            seen.append(message)
            return original(self, message)

        monkeypatch.setattr(SafetyGovernor, "validate_message", spy)
        plan = paaa.process(baseline, PhysiologicalSample(
            tremor_amplitude=0.42, tremor_frequency_hz=5.1, motor_smoothness=0.66,
            reaction_latency_ms=420, grip_stability=0.68, voice_stability=0.78,
            stress_proxy=0.36,
        ))
        assert plan.message in seen

    def test_orchestrator_and_planner_share_one_governor(self):
        paaa = PAAAOrchestrator()
        assert paaa.feedback.safety is paaa.safety


# ── Stimulation gating ────────────────────────────────────────────────

def _state(risk=FunctionalRisk.MEDIUM):
    """A real FunctionalState, so a signature change breaks the test."""
    return FunctionalState(
        stability_score=0.7,
        deviation_score=0.3,
        risk=risk,
        drivers=[],
        confidence=0.8,
    )


class TestStimulationGating:

    def test_requires_explicit_consent(self):
        gov = SafetyGovernor()
        state = _state()
        assert gov.stimulation_allowed(state, StimulationPolicy(enabled=True, explicit_consent=False)) is False
        assert gov.stimulation_allowed(
            state, StimulationPolicy(enabled=True, explicit_consent=True, max_intensity_pct=10)
        ) is True

    def test_disabled_policy_blocks(self):
        assert SafetyGovernor().stimulation_allowed(
            _state(), StimulationPolicy(enabled=False, explicit_consent=True)
        ) is False

    def test_high_risk_requires_clinical_mode(self):
        gov = SafetyGovernor()
        policy = StimulationPolicy(enabled=True, explicit_consent=True, max_intensity_pct=10)
        assert gov.stimulation_allowed(_state(FunctionalRisk.HIGH), policy) is False
        assert gov.stimulation_allowed(_state(FunctionalRisk.REVIEW), policy) is False

    def test_intensity_ceiling_enforced(self):
        gov = SafetyGovernor()
        policy = StimulationPolicy(enabled=True, explicit_consent=True, max_intensity_pct=15.1)
        assert gov.stimulation_allowed(_state(), policy) is False

    def test_review_required_reflects_risk(self):
        gov = SafetyGovernor()
        assert gov.review_required(_state(FunctionalRisk.REVIEW)) is True
        assert gov.review_required(_state(FunctionalRisk.LOW)) is False


def test_detector_exists_for_import_sanity():
    assert DeviationDetector() is not None
