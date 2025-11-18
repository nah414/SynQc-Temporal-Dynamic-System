"""
High-level orchestration engine for SynQc Temporal Dynamics.

The SynQcEngine glues together configuration, scheduling, hardware
execution, demodulation, and adaptive control.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import SynQcConfig
from .scheduler import Scheduler
from .hardware import SimulatedBackend
from .demod import demodulate_probes
from .adapt import AdaptiveLoop


@dataclass
class SynQcEngine:
    """
    High-level façade for the SynQc runtime.

    Use `SynQcEngine.build_default(...)` for a quick-start configuration,
    or construct your own engine wiring explicitly.
    """

    config: SynQcConfig
    scheduler: Scheduler
    backend: SimulatedBackend
    adaptive_loop: AdaptiveLoop

    @classmethod
    def build_default(cls, config: SynQcConfig) -> "SynQcEngine":
        scheduler = Scheduler(config=config)
        backend = SimulatedBackend(
            lo_frequency_hz=config.lo_frequency_hz,
            sample_rate_hz=config.sample_rate_hz,
        )
        adaptive_loop = AdaptiveLoop(
            config=config,
            scheduler=scheduler,
            backend=backend,
        )
        return cls(
            config=config,
            scheduler=scheduler,
            backend=backend,
            adaptive_loop=adaptive_loop,
        )

    def run_iteration(self) -> pd.DataFrame:
        """
        Run a single schedule → backend → demodulation pass.
        """
        schedule = self.scheduler.build_schedule()
        raw = self.backend.run_schedule(schedule)
        return demodulate_probes(
            raw,
            lo_frequency_hz=self.config.lo_frequency_hz,
            sample_rate_hz=self.config.sample_rate_hz,
        )

    def run_adaptive(self, num_iterations: int = 5) -> pd.DataFrame:
        """
        Run an adaptive calibration loop.
        """
        return self.adaptive_loop.run(num_iterations=num_iterations)
