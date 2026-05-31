from dataclasses import dataclass
from statistics import mean, stdev


@dataclass
class BaselineResult:
    value: float
    baseline_mean: float
    z_score: float
    persistent: bool


class BaselineEngine:
    def compare(self, history: list[float], current: float, persistence_count: int = 3) -> BaselineResult:
        if len(history) < 5:
            return BaselineResult(current, current, 0.0, False)

        mu = mean(history)
        sigma = stdev(history) or 1e-6
        z = (current - mu) / sigma
        recent = history[-persistence_count:] + [current]
        persistent = all(abs((x - mu) / sigma) > 1.5 for x in recent)

        return BaselineResult(current, mu, z, persistent)
