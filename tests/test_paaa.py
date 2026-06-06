from paaa_core.models import PhysiologicalSample, FunctionalRisk
from paaa_core.orchestrator import PAAAOrchestrator
from paaa_core.safety import StimulationPolicy, SafetyGovernor
from paaa_core.deviation import DeviationDetector


def make_baseline(paaa):
    samples = [
        PhysiologicalSample(
            tremor_amplitude=0.10 + i * 0.001,
            tremor_frequency_hz=4.1,
            motor_smoothness=0.90,
            reaction_latency_ms=250 + i,
            grip_stability=0.92,
            voice_stability=0.91,
            stress_proxy=0.15,
        )
        for i in range(8)
    ]
    return paaa.build_baseline("test_user", samples)


def test_baseline_requires_minimum_samples():
    paaa = PAAAOrchestrator()
    try:
        paaa.build_baseline("x", [PhysiologicalSample() for _ in range(3)])
        assert False
    except ValueError:
        assert True


def test_deviation_detects_high_tremor():
    paaa = PAAAOrchestrator()
    baseline = make_baseline(paaa)
    sample = PhysiologicalSample(tremor_amplitude=0.48, tremor_frequency_hz=5.2, motor_smoothness=0.62, reaction_latency_ms=430, grip_stability=0.70, voice_stability=0.80, stress_proxy=0.3)
    plan = paaa.process(baseline, sample)
    assert plan.risk.value in {"HIGH", "REVIEW"}
    assert plan.action in {"guided_pause_and_recalibration", "professional_review_recommended"}


def test_stimulation_disabled_by_default():
    paaa = PAAAOrchestrator()
    baseline = make_baseline(paaa)
    sample = PhysiologicalSample(tremor_amplitude=0.30, tremor_frequency_hz=5.0, motor_smoothness=0.70, reaction_latency_ms=360, grip_stability=0.74, voice_stability=0.82, stress_proxy=0.3)
    plan = paaa.process(baseline, sample)
    assert plan.stimulation_allowed is False


def test_stimulation_requires_explicit_consent():
    governor = SafetyGovernor()
    state = type("State", (), {"risk": FunctionalRisk.MEDIUM})()
    assert governor.stimulation_allowed(state, StimulationPolicy(enabled=True, explicit_consent=False)) is False
    assert governor.stimulation_allowed(state, StimulationPolicy(enabled=True, explicit_consent=True, max_intensity_pct=10)) is True


def test_memory_pruning_keeps_size():
    paaa = PAAAOrchestrator()
    baseline = make_baseline(paaa)
    for _ in range(140):
        paaa.process(baseline, PhysiologicalSample(tremor_amplitude=0.12, tremor_frequency_hz=4.1, motor_smoothness=0.89, reaction_latency_ms=255, grip_stability=0.91, voice_stability=0.90, stress_proxy=0.16))
    assert len(paaa.memory.events) <= paaa.memory.max_events
