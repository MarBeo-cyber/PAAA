from paaa_core.models import PhysiologicalSample
from paaa_core.orchestrator import PAAAOrchestrator
from paaa_core.safety import StimulationPolicy

paaa = PAAAOrchestrator()

baseline_samples = [
    PhysiologicalSample(
        tremor_amplitude=0.10 + i * 0.002,
        tremor_frequency_hz=4.2,
        motor_smoothness=0.88,
        reaction_latency_ms=260 + i,
        grip_stability=0.91,
        voice_stability=0.90,
        stress_proxy=0.18,
    )
    for i in range(10)
]

baseline = paaa.build_baseline("demo_user", baseline_samples)

current = PhysiologicalSample(
    tremor_amplitude=0.42,
    tremor_frequency_hz=5.1,
    motor_smoothness=0.66,
    reaction_latency_ms=420,
    grip_stability=0.68,
    voice_stability=0.78,
    stress_proxy=0.36,
)

policy = StimulationPolicy(enabled=False, explicit_consent=False)
plan = paaa.process(baseline, current, policy=policy)

print("PAAA functional continuity plan")
print("--------------------------------")
print("risk:", plan.risk.value)
print("message:", plan.message)
print("channels:", [c.value for c in plan.channels])
print("action:", plan.action)
print("requires_review:", plan.requires_review)
print("stimulation_allowed:", plan.stimulation_allowed)
print("memory_events:", len(paaa.memory.events))
