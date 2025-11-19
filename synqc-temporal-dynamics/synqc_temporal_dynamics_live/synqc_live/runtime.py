"""
Environment-agnostic runtime helpers for SynQc Temporal Dynamics.

This module provides a small, stable API that can be used from:
- Jupyter notebooks
- Command-line interfaces
- Long-running services or batch jobs

It wraps SynQcConfig + SynQcEngine into a simple "run the pipeline" call.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import SynQcConfig, PulseConfig, load_config
from .engine import SynQcEngine


@dataclass
class PipelineResult:
    """
    Result of running the live SynQc pipeline.

    Attributes
    ----------
    config:
        The configuration used to build the engine.
    iteration:
        DataFrame from a single schedule → backend → demodulation pass.
    adaptive:
        DataFrame of per-iteration metrics from the adaptive loop,
        or None if the adaptive loop was skipped.
    """

    config: SynQcConfig
    iteration: pd.DataFrame
    adaptive: Optional[pd.DataFrame] = None

    def require_adaptive(self) -> pd.DataFrame:
        """
        Return the adaptive DataFrame or raise if it was not produced.

        This guards downstream consumers from silently operating on
        ``None`` when the adaptive loop has been disabled.
        """

        if self.adaptive is None:
            raise ValueError(
                "Adaptive loop results are unavailable; set run_adaptive=True."
            )
        return self.adaptive


def build_quickstart_config(
    *,
    sample_rate_hz: float = 1e9,
    lo_frequency_hz: float = 50e6,
    cycle_duration_ns: float = 1000.0,
    num_cycles: int = 8,
    target_amplitude: float = 1.0,
    drive_amplitude: float = 1.0,
    drive_phase_deg: float = 0.0,
    drive_frequency_hz: float = 50e6,
    drive_duration_ns: float = 400.0,
    probe_every_n_cycles: int = 2,
) -> SynQcConfig:
    """
    Build a simple, default SynQcConfig for quick experiments.

    This mirrors the example configuration used in the live-core README.
    """

    pulse = PulseConfig(
        label="drive",
        amplitude=drive_amplitude,
        phase_deg=drive_phase_deg,
        frequency_hz=drive_frequency_hz,
        duration_ns=drive_duration_ns,
    )

    return SynQcConfig(
        sample_rate_hz=sample_rate_hz,
        lo_frequency_hz=lo_frequency_hz,
        cycle_duration_ns=cycle_duration_ns,
        num_cycles=num_cycles,
        target_amplitude=target_amplitude,
        pulses=[pulse],
        probe_every_n_cycles=probe_every_n_cycles,
    )


def make_engine(config: SynQcConfig) -> SynQcEngine:
    """
    Construct a SynQcEngine from a configuration.

    This is a thin wrapper over SynQcEngine.build_default, provided so
    that callers don't depend directly on the engine wiring details.
    """
    return SynQcEngine.build_default(config)


def run_pipeline(
    config: SynQcConfig,
    *,
    num_iterations: int = 5,
    run_adaptive: bool = True,
) -> PipelineResult:
    """
    Run the live SynQc pipeline for the given configuration.

    Parameters
    ----------
    config:
        High-level configuration for the SynQc run.
    num_iterations:
        Number of adaptive iterations to execute if run_adaptive is True.
    run_adaptive:
        If False, only a single iteration is executed and the adaptive
        loop is skipped.

    Returns
    -------
    PipelineResult
        Contains the per-sample DataFrame from a single iteration and,
        optionally, the adaptive loop summary.
    """
    if num_iterations < 1:
        raise ValueError("num_iterations must be at least 1 when running adaptively")

    engine = make_engine(config)
    df_iter = engine.run_iteration()

    if run_adaptive:
        df_loop = engine.run_adaptive(num_iterations=num_iterations)
    else:
        df_loop = None

    return PipelineResult(config=config, iteration=df_iter, adaptive=df_loop)


def run_pipeline_from_yaml(
    path: str | Path,
    *,
    num_iterations: int = 5,
    run_adaptive: bool = True,
) -> PipelineResult:
    """
    Load a SynQc configuration from a YAML file and run the pipeline.

    Parameters
    ----------
    path:
        Path to a YAML file consumable by synqc_live.config.load_config.
    num_iterations:
        Number of adaptive iterations to execute if run_adaptive is True.
    run_adaptive:
        If False, only a single iteration is executed and the adaptive
        loop is skipped.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Config file not found: {path_obj}")

    config = load_config(path_obj)
    return run_pipeline(config, num_iterations=num_iterations, run_adaptive=run_adaptive)
