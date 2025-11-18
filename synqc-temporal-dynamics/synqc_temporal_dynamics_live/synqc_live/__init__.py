"""
SynQc Temporal Dynamics – core package.

Live execution engine for the SynQc Temporal Dynamic System, including
scheduler, probes, demodulation, adaptive loops, and hardware backends.
"""

from .config import SynQcConfig
from .engine import SynQcEngine

__all__ = ["SynQcConfig", "SynQcEngine"]
__version__ = "0.2.0"
