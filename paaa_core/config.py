"""PAAA configuration.

Thresholds used to live as literals in three places (``deviation.py``,
``baseline.py`` and an unread YAML file). They live here now, and
``config/default.json`` is an optional override that is actually loaded.

JSON rather than YAML so that loading needs no third-party dependency.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.json"


@dataclass(frozen=True)
class PAAAConfig:
    # Baseline
    minimum_samples: int = 5
    validity_days: int = 30
    # Deviation thresholds (on the 0..1 deviation score)
    medium_threshold: float = 0.35
    high_threshold: float = 0.55
    review_threshold: float = 0.72
    # A feature is reported as a driver above this normalised deviation
    driver_threshold: float = 0.45
    # Safety
    stimulation_enabled_default: bool = False
    max_stimulation_intensity_pct: float = 15.0
    explicit_consent_required: bool = True
    # Escalation (see docs/SAFETY_AND_REGULATORY.md)
    escalation_z_threshold: float = 1.5
    escalation_min_sessions: int = 5
    escalation_window_days: int = 7


def load_config(path: Optional[Path | str] = None) -> PAAAConfig:
    """Load configuration, falling back to built-in defaults.

    Unknown keys in the file are ignored; missing keys keep their default.
    A missing file is not an error — the defaults above are the contract.
    """
    path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        return PAAAConfig()

    raw = json.loads(path.read_text(encoding="utf-8"))
    known = {f.name for f in fields(PAAAConfig)}
    overrides = {k: v for k, v in raw.items() if k in known}
    return PAAAConfig(**overrides)
