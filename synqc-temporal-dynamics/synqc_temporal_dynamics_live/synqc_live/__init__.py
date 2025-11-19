"""
SynQc Temporal Dynamics – core package.

Live execution engine for the SynQc Temporal Dynamic System, including
scheduler, probes, demodulation, adaptive loops, and hardware backends.
"""

from .adapt import AdaptiveLoop
from .config import SynQcConfig
from .engine import SynQcEngine
from .notebook_helpers import quickstart_demo
from .runtime import (
    PipelineResult,
    build_quickstart_config,
    make_engine,
    run_pipeline,
    run_pipeline_from_yaml,
)

__all__ = [
    "AdaptiveLoop",
    "PipelineResult",
    "SynQcConfig",
    "SynQcEngine",
    "build_quickstart_config",
    "make_engine",
    "quickstart_demo",
    "run_pipeline",
    "run_pipeline_from_yaml",
]
__version__ = "0.2.0"
