import pytest

from paaa_core.models import (
    FeedbackChannel,
    FunctionalRisk,
    FunctionalState,
    PhysiologicalSample,
    SignalQuality,
)
from paaa_core.orchestrator import PAAAOrchestrator
from paaa_core.safety import StimulationPolicy, SafetyGovernor


def make_baseline(paaa):
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
        for i in range(8)
    ]
    return paaa.build_baseline("test_user", samples)


def test_baseline_requires_minimum_samples():
    paaa = PAAAOrchestrator()
    with pytest.raises(ValueError):
        paaa.build_baseline("x", [PhysiologicalSample() for _ in range(3)])


def test_deviation_detects_high_tremor():
    paaa = PAAAOrchestrator()
    baseline = make_baseline(paaa)
    sample = PhysiologicalSample(tremor_amplitude=0.48, tremor_frequency_hz=5.2, motor_smoothness=0.62, reaction_latency_ms=430, grip_stability=0.70, voice_stability=0.80, stress_proxy=0.3)
    plan = paaa.process(baseline, sample)
    assert plan.risk.value in {"HIGH", "REVIEW"}
    assert plan.action in {"guided_pause_and_recalibration", "professional_review_recommended"}


def test_stable_sample_stays_low_risk():
    paaa = PAAAOrchestrator()
    baseline = make_baseline(paaa)
    sample = PhysiologicalSample(tremor_amplitude=0.11, tremor_frequency_hz=4.3, motor_smoothness=0.88, reaction_latency_ms=262, grip_stability=0.91, voice_stability=0.89, stress_proxy=0.18)
    plan = paaa.process(baseline, sample)
    assert plan.risk is FunctionalRisk.LOW
    assert plan.action == "passive_monitoring"
    assert plan.requires_review is False


def test_stimulation_disabled_by_default():
    paaa = PAAAOrchestrator()
    baseline = make_baseline(paaa)
    sample = PhysiologicalSample(tremor_amplitude=0.30, tremor_frequency_hz=5.0, motor_smoothness=0.70, reaction_latency_ms=360, grip_stability=0.74, voice_stability=0.82, stress_proxy=0.3)
    plan = paaa.process(baseline, sample)
    assert plan.stimulation_allowed is False


def test_stimulation_requires_explicit_consent():
    governor = SafetyGovernor()
    # A real FunctionalState, so a signature change is caught here.
    state = FunctionalState(
        stability_score=0.7,
        deviation_score=0.3,
        risk=FunctionalRisk.MEDIUM,
        drivers=[],
        confidence=0.8,
    )
    assert governor.stimulation_allowed(state, StimulationPolicy(enabled=True, explicit_consent=False)) is False
    assert governor.stimulation_allowed(state, StimulationPolicy(enabled=True, explicit_consent=True, max_intensity_pct=10)) is True


def test_memory_pruning_keeps_size():
    paaa = PAAAOrchestrator()
    baseline = make_baseline(paaa)
    for _ in range(140):
        paaa.process(baseline, PhysiologicalSample(tremor_amplitude=0.12, tremor_frequency_hz=4.1, motor_smoothness=0.89, reaction_latency_ms=255, grip_stability=0.91, voice_stability=0.90, stress_proxy=0.16))
    assert len(paaa.memory.events) <= paaa.memory.max_events


def test_plan_shape_is_serialisable():
    paaa = PAAAOrchestrator()
    baseline = make_baseline(paaa)
    plan = paaa.process(baseline, PhysiologicalSample(tremor_amplitude=0.12, tremor_frequency_hz=4.1, motor_smoothness=0.89, reaction_latency_ms=255, grip_stability=0.91, voice_stability=0.90, stress_proxy=0.16))
    assert isinstance(plan.message, str) and plan.message
    assert all(isinstance(c, FeedbackChannel) for c in plan.channels)
    assert isinstance(plan.escalation, dict)


def test_signal_quality_enum_values_are_not_typos():
    # REGRESSION: UNUSABLE was "usable_false", which would leak into any
    # serialized output.
    assert SignalQuality.UNUSABLE.value == "unusable"
    assert SignalQuality.GOOD.value == "good"
    assert SignalQuality.DEGRADED.value == "degraded"
