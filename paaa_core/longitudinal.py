"""Longitudinal session history and the escalation protocol.

A single session says nothing. PAAA's premise is continuity: a deviation only
matters if it *persists*. This module is the one place where that rule lives.

The rule implemented here is the rule in ``docs/SAFETY_AND_REGULATORY.md``:
a feature escalates when it deviates by |z| > 1.5 in at least 5 sessions
within a 7-day window. Sessions are timestamped, all sessions inside the
window are counted (not just the most recent N), and the reported count is the
count that was actually used for the decision.

The store is in-memory. It does not survive process restart and nothing is
written to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .config import PAAAConfig


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def deviation_level(z: float) -> str:
    """Qualitative band for a z-score. Descriptive, never diagnostic."""
    az = abs(z)
    if az < 1.5:
        return "normal"
    if az < 2.5:
        return "mild"
    if az < 3.5:
        return "moderate"
    return "significant"


@dataclass
class SessionObservation:
    """One scored session, kept so that persistence can be evaluated."""

    z_scores: Dict[str, float]
    deviation_score: float = 0.0
    risk: str = "LOW"
    timestamp: datetime = field(default_factory=_utc_now)


@dataclass
class EscalationAssessment:
    escalate: bool
    window_sessions: int
    sessions_deviated: Dict[str, int]
    persistent_features: List[str]
    z_threshold: float
    min_sessions: int
    window_days: int

    def to_dict(self) -> dict:
        return {
            "escalate": self.escalate,
            "window_sessions": self.window_sessions,
            "window_days": self.window_days,
            "z_threshold": self.z_threshold,
            "min_sessions": self.min_sessions,
            "sessions_deviated": dict(self.sessions_deviated),
            "persistent_features": list(self.persistent_features),
        }


class SessionHistory:
    """Timestamped session store with N-of-M-within-window persistence.

    The previous implementation looked only at the last N entries and required
    *all* of them to deviate, so nine deviating sessions out of ten escalated
    nothing. Here every session inside the window is counted.
    """

    def __init__(self, config: PAAAConfig | None = None, max_sessions: int = 500) -> None:
        self.config = config or PAAAConfig()
        self.max_sessions = max_sessions
        self.sessions: List[SessionObservation] = []

    def record(self, observation: SessionObservation) -> None:
        self.sessions.append(observation)
        if len(self.sessions) > self.max_sessions:
            self.sessions = self.sessions[-self.max_sessions:]

    def sessions_in_window(self, now: Optional[datetime] = None) -> List[SessionObservation]:
        now = now or _utc_now()
        cutoff = now - timedelta(days=self.config.escalation_window_days)
        return [s for s in self.sessions if s.timestamp >= cutoff]

    def assess(self, now: Optional[datetime] = None) -> EscalationAssessment:
        """Evaluate the documented escalation rule over the current window."""
        window = self.sessions_in_window(now)
        threshold = self.config.escalation_z_threshold
        minimum = self.config.escalation_min_sessions

        counts: Dict[str, int] = {}
        for session in window:
            for feature, z in session.z_scores.items():
                if abs(z) > threshold:
                    counts[feature] = counts.get(feature, 0) + 1

        persistent = sorted(f for f, c in counts.items() if c >= minimum)
        return EscalationAssessment(
            escalate=bool(persistent),
            window_sessions=len(window),
            sessions_deviated=counts,
            persistent_features=persistent,
            z_threshold=threshold,
            min_sessions=minimum,
            window_days=self.config.escalation_window_days,
        )
