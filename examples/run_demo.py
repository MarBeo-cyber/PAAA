"""PAAA CLI demo.

Runs the real pipeline: baseline -> deviation -> session history -> safety ->
biofeedback. Every number printed here comes from paaa_core; nothing is
scripted.
"""

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make `python examples/run_demo.py` work from a clean clone, uninstalled.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paaa_core.config import load_config
from paaa_core.models import PhysiologicalSample
from paaa_core.orchestrator import PAAAOrchestrator
from paaa_core.safety import StimulationPolicy

random.seed(7)
config = load_config()
paaa = PAAAOrchestrator(config)

# A real baseline has session-to-session jitter on every feature. A baseline of
# repeated constants has no variance to compare against and must not be treated
# as if it had.
baseline_samples = [
    PhysiologicalSample(
        tremor_amplitude=round(random.gauss(0.10, 0.018), 4),
        tremor_frequency_hz=round(random.gauss(4.2, 0.35), 3),
        motor_smoothness=round(random.gauss(0.88, 0.035), 4),
        reaction_latency_ms=round(random.gauss(262, 18), 1),
        grip_stability=round(random.gauss(0.91, 0.030), 4),
        voice_stability=round(random.gauss(0.90, 0.032), 4),
        stress_proxy=round(random.gauss(0.18, 0.050), 4),
    )
    for _ in range(12)
]

baseline = paaa.build_baseline("demo_user", baseline_samples)

print("PAAA functional continuity demo")
print("=" * 62)
print("baseline sessions:", baseline.sample_count)
print("baseline std per feature:")
for feature, std in baseline.stds.items():
    print(f"  {feature:22s} mean={baseline.means[feature]:9.4f}  std={std:8.4f}")
print("features without usable variance:", baseline.degenerate_features or "none")

# ── One elevated session ──────────────────────────────────────────────
day_one = datetime.now(timezone.utc) - timedelta(days=6)
current = PhysiologicalSample(
    tremor_amplitude=0.145,
    tremor_frequency_hz=4.70,
    motor_smoothness=0.835,
    reaction_latency_ms=305,
    grip_stability=0.865,
    voice_stability=0.870,
    stress_proxy=0.270,
)

policy = StimulationPolicy(
    enabled=config.stimulation_enabled_default,
    explicit_consent=False,
)
state = paaa.detector.score(baseline, current)
plan = paaa.process(baseline, current, policy=policy, timestamp=day_one)

print()
print("Single session")
print("-" * 62)
print("deviation_score:", state.deviation_score)
print("stability_score:", state.stability_score)
print("risk:", plan.risk.value)
print("drivers:", state.drivers or "none")
print("z-scores:", {k: v for k, v in state.z_scores.items() if abs(v) >= 1.0})
print("feature_scores:", state.feature_scores)
print("confidence (in the comparison, not in any clinical inference):", state.confidence)
print("message:", plan.message)
print("channels:", [c.value for c in plan.channels])
print("action:", plan.action)
print("requires_review:", plan.requires_review)
print("stimulation_allowed:", plan.stimulation_allowed)

# ── The same deviation, repeated over days ────────────────────────────
# One session says nothing. Escalation needs the documented
# N-of-M-within-window rule to be satisfied.
print()
print("Escalation across sessions "
      f"(>= {config.escalation_min_sessions} sessions with |z| > "
      f"{config.escalation_z_threshold} in {config.escalation_window_days} days)")
print("-" * 62)
for day in range(1, 6):
    repeat = PhysiologicalSample(
        tremor_amplitude=round(0.145 + random.gauss(0, 0.004), 4),
        tremor_frequency_hz=round(4.70 + random.gauss(0, 0.05), 3),
        motor_smoothness=0.835,
        reaction_latency_ms=305,
        grip_stability=0.865,
        voice_stability=0.870,
        stress_proxy=0.270,
    )
    plan = paaa.process(baseline, repeat, policy=policy, timestamp=day_one + timedelta(days=day))
    escalation = plan.escalation
    flag = "ESCALATED" if escalation and escalation["escalate"] else "-"
    counts = paaa.history.assess(now=day_one + timedelta(days=day)).sessions_deviated
    print(f"day {day + 1}: risk={plan.risk.value:6s} {flag:10s} "
          f"tremor_amplitude deviating in {counts.get('tremor_amplitude', 0)} session(s)")

print()
print("escalation:", plan.escalation)
print("message:", plan.message)
print("memory_events:", len(paaa.memory.events))

# ── The safety boundary is in the execution path ──────────────────────
print()
print("Safety Governor on the live path")
print("-" * 62)
try:
    paaa.safety.validate_message("Diagnosis: Parkinson detected")
    print("NOT BLOCKED - the safety boundary is not working")
except ValueError as exc:
    print("blocked:", exc)
print("allowed:", paaa.safety.validate_message("Bring this to your physiotherapy session"))
