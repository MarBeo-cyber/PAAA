"""
PAAA Demo — Personal Baseline Engine + Safety Governor

Simulates a longitudinal monitoring session with tremor feature,
showing the full pipeline from acquisition to referral recommendation.
"""

from paaa.baseline import BaselineEngine, BaselineResult
from paaa.safety import SafetyGovernor

# ── Simulate 12 weeks of tremor baseline (normal range 0.08–0.13 Hz RMS)
baseline_history = [
    0.10, 0.11, 0.09, 0.10, 0.12, 0.11, 0.10,
    0.09, 0.11, 0.10, 0.12, 0.10, 0.11, 0.09,
    0.10, 0.11, 0.10, 0.09, 0.12, 0.11,
]

# ── Simulate 7 recent sessions showing persistent deviation
recent_sessions = [0.19, 0.20, 0.18, 0.21, 0.19]

engine  = BaselineEngine(min_history_sessions=10, z_threshold=1.5, persistence_count=5)
safety  = SafetyGovernor(strict_mode=True)

print("=" * 60)
print("PAAA — Personal Neurofunctional Monitoring Demo")
print("=" * 60)

# ── Session 1: normal measurement
print("\nSession — normal measurement (value: 0.11)")
r1 = engine.compare("tremor_rms", baseline_history, 0.11, recent_sessions=baseline_history[-5:])
print(f"  Z-score:          {r1.z_score:.3f}")
print(f"  Deviation level:  {r1.deviation_level}")
print(f"  Persistent:       {r1.persistent}")

# ── Session 2: persistent deviation
print("\nSession — persistent deviation (value: 0.20)")
r2 = engine.compare(
    "tremor_rms", baseline_history, 0.20,
    recent_sessions=recent_sessions,
    context={"time_of_day": "morning", "stress_declared": False}
)
print(f"  Z-score:          {r2.z_score:.3f}")
print(f"  Deviation level:  {r2.deviation_level}")
print(f"  Persistent:       {r2.persistent}")
print(f"  Sessions deviated:{r2.sessions_deviated}")

# ── Session report
print("\nSession Report:")
report = engine.session_report({"tremor_rms": r2})
for k, v in report.items():
    if k != "persistent_features":
        print(f"  {k}: {v}")

# ── Safety check on referral message
if report["requires_escalation"]:
    print("\n⚠️  Persistent deviation detected — generating referral message")
    features = [f["feature"] for f in report["persistent_features"]]
    referral = safety.referral_message(features)
    validated = safety.validate_message(referral)
    print(f"\nReferral message (validated):")
    print(f"  {validated}")

# ── Demonstrate safety governor blocking unsafe output
print("\n── Safety Governor Test ──")
unsafe_attempts = [
    "Parkinson detected with 89% confidence",
    "Diagnosis: early-stage neurological disease",
    "Treatment recommended: consult neurologist immediately",
    "Persistent deviation from your personal baseline detected",  # SAFE
]
for msg in unsafe_attempts:
    try:
        result = safety.validate_message(msg)
        print(f"  ✓ SAFE:   {msg[:60]}")
    except ValueError as e:
        print(f"  ✗ BLOCKED: {msg[:60]}")

print("\n" + "=" * 60)
print("Demo complete. PAAA produced zero diagnostic claims.")
print("=" * 60)
