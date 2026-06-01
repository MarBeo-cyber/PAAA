"""
PAAA — Personal Baseline Engine

Compares each neurofunctional feature against the user's own historical baseline.
No population norm is used. All comparison is individual-longitudinal.
"""

from dataclasses import dataclass, field
from statistics import mean, stdev
from datetime import datetime
from typing import Optional
import json


@dataclass
class BaselineResult:
    """Result of a single feature comparison against personal baseline."""
    feature: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    persistent: bool
    sessions_deviated: int
    context: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def deviation_level(self) -> str:
        az = abs(self.z_score)
        if az < 1.5:
            return "normal"
        if az < 2.5:
            return "mild"
        if az < 3.5:
            return "moderate"
        return "significant"

    def to_dict(self) -> dict:
        return {
            "feature": self.feature,
            "value": self.value,
            "z_score": round(self.z_score, 3),
            "deviation_level": self.deviation_level,
            "persistent": self.persistent,
            "sessions_deviated": self.sessions_deviated,
            "timestamp": self.timestamp.isoformat(),
        }


class BaselineEngine:
    """
    Personal baseline comparison engine.
    
    Compares current measurements against the user's individual historical
    distribution. Flags deviations only when persistent across multiple sessions.
    """

    def __init__(
        self,
        min_history_sessions: int = 10,
        z_threshold: float = 1.5,
        persistence_count: int = 5,
        persistence_window_days: int = 7,
    ):
        self.min_history = min_history_sessions
        self.z_threshold = z_threshold
        self.persistence_count = persistence_count
        self.persistence_window_days = persistence_window_days

    def compare(
        self,
        feature: str,
        history: list[float],
        current: float,
        recent_sessions: Optional[list[float]] = None,
        context: Optional[dict] = None,
    ) -> BaselineResult:
        """
        Compare current value against personal baseline.

        Args:
            feature: Name of the neurofunctional feature.
            history: Historical values for this feature (personal baseline).
            current: Current measured value.
            recent_sessions: Last N session values for persistence check.
            context: Contextual factors (time_of_day, stress_declared, etc.)

        Returns:
            BaselineResult with z-score and persistence flag.
        """
        if len(history) < self.min_history:
            return BaselineResult(
                feature=feature,
                value=current,
                baseline_mean=current,
                baseline_std=0.0,
                z_score=0.0,
                persistent=False,
                sessions_deviated=0,
                context=context or {},
            )

        mu = mean(history)
        sigma = stdev(history) or 1e-6
        z = (current - mu) / sigma

        # Persistence check: deviation must appear in N of last M sessions
        sessions_deviated = 0
        persistent = False
        if recent_sessions is not None and len(recent_sessions) >= self.persistence_count:
            deviated = [abs((v - mu) / sigma) > self.z_threshold for v in recent_sessions[-self.persistence_count:]]
            sessions_deviated = sum(deviated)
            persistent = sessions_deviated >= self.persistence_count

        return BaselineResult(
            feature=feature,
            value=current,
            baseline_mean=mu,
            baseline_std=sigma,
            z_score=z,
            persistent=persistent,
            sessions_deviated=sessions_deviated,
            context=context or {},
        )

    def compare_session(
        self,
        session_features: dict[str, float],
        historical_features: dict[str, list[float]],
        recent_features: Optional[dict[str, list[float]]] = None,
        context: Optional[dict] = None,
    ) -> dict[str, BaselineResult]:
        """Compare all features of a session against personal baseline."""
        results = {}
        for feature, current_value in session_features.items():
            history = historical_features.get(feature, [])
            recent = (recent_features or {}).get(feature)
            results[feature] = self.compare(
                feature=feature,
                history=history,
                current=current_value,
                recent_sessions=recent,
                context=context,
            )
        return results

    def persistent_deviations(
        self, results: dict[str, BaselineResult]
    ) -> list[BaselineResult]:
        """Return only features with persistent deviation."""
        return [r for r in results.values() if r.persistent]

    def session_report(self, results: dict[str, BaselineResult]) -> dict:
        """Generate a structured session summary."""
        persistent = self.persistent_deviations(results)
        return {
            "total_features": len(results),
            "features_deviated": sum(1 for r in results.values() if abs(r.z_score) > self.z_threshold),
            "features_persistent": len(persistent),
            "max_z_score": max((abs(r.z_score) for r in results.values()), default=0.0),
            "persistent_features": [r.to_dict() for r in persistent],
            "requires_escalation": len(persistent) > 0,
        }
