"""PAAA — Personal Autopoietic Adaptive Agent.

A longitudinal personal neurofunctional monitoring platform.
Compares the user with their own historical baseline to detect
persistent deviations that may merit clinical attention.

NOT a diagnostic device. Does not identify pathologies.
Supports awareness and professional consultation only.
"""
__version__ = "0.3.0"
__author__ = "Marco Giuseppe Beozzi"
__license__ = "MIT"

from paaa.baseline import BaselineEngine, BaselineResult
from paaa.safety import SafetyGovernor

__all__ = ["BaselineEngine", "BaselineResult", "SafetyGovernor"]
