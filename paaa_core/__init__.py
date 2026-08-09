"""PAAA — Physiological Autopoietic Adaptive Agent.

The functional-continuity module of the autopoietic ontology. After the WAAA,
which consolidates continuous monitoring and informational persistence, and the
MAAA, which stabilises situated action under emergency, the PAAA preserves the
physiological and neurofunctional continuity of the user: personal baseline,
non-diagnostic deviation detection, biofeedback, and safety gating.

It compares the user with their own historical baseline to detect persistent
deviations that may merit clinical attention.

NOT a diagnostic device. Does not identify pathologies.
Supports awareness and professional consultation only.
"""

__version__ = "1.0.0"
__author__ = "Marco Giuseppe Beozzi"
__license__ = "MIT"

from .baseline import BaselineBuilder, FEATURES, FEATURE_MIN_STD
from .config import PAAAConfig, load_config
from .deviation import DeviationDetector, FEATURE_WEIGHTS
from .feedback import BiofeedbackPlanner
from .features import MotorFeatureExtractor
from .longitudinal import (
    EscalationAssessment,
    SessionHistory,
    SessionObservation,
    deviation_level,
)
from .memory import FunctionalMemory
from .models import (
    BaselineProfile,
    FeedbackChannel,
    FeedbackPlan,
    FunctionalRisk,
    FunctionalState,
    PhysiologicalSample,
    SignalQuality,
)
from .orchestrator import PAAAOrchestrator
from .safety import SafetyGovernor, StimulationPolicy

__all__ = [
    "BaselineBuilder",
    "BaselineProfile",
    "BiofeedbackPlanner",
    "DeviationDetector",
    "EscalationAssessment",
    "FEATURES",
    "FEATURE_MIN_STD",
    "FEATURE_WEIGHTS",
    "FeedbackChannel",
    "FeedbackPlan",
    "FunctionalMemory",
    "FunctionalRisk",
    "FunctionalState",
    "MotorFeatureExtractor",
    "PAAAConfig",
    "PAAAOrchestrator",
    "PhysiologicalSample",
    "SafetyGovernor",
    "SessionHistory",
    "SessionObservation",
    "SignalQuality",
    "StimulationPolicy",
    "deviation_level",
    "load_config",
]
