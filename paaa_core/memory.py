from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FunctionalMemory:
    """Small event memory with WAAA-style pruning."""

    max_events: int = 120
    events: list[dict] = field(default_factory=list)

    def add(self, event: dict) -> None:
        e = dict(event)
        e.setdefault("timestamp", now())
        self.events.append(e)
        if len(self.events) > self.max_events:
            self.prune()

    def prune(self) -> None:
        high_value = [e for e in self.events if e.get("risk") in {"HIGH", "REVIEW"} or e.get("requires_review")]
        recent = self.events[-self.max_events // 2 :]
        merged = []
        seen = set()
        for e in high_value + recent:
            key = (e.get("timestamp"), e.get("risk"), e.get("action"))
            if key not in seen:
                merged.append(e)
                seen.add(key)
        self.events = merged[-self.max_events :]
