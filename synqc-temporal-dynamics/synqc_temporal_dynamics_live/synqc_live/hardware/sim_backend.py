"""
Simulated hardware backend for SynQc Temporal Dynamics.

This backend consumes a Schedule, renders it to a time series, and then
produces synthetic I/Q data with configurable drift and noise. It is
designed to be lightweight but realistic enough for pipeline testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from ..timeline import Schedule


@dataclass
class SimulatedBackend:
    """
    Simple I/Q-producing backend for SynQc.

    Parameters
    ----------
    lo_frequency_hz : float
        Local oscillator frequency used when synthesizing I/Q.
    sample_rate_hz : float
        Sample rate in Hz.
    base_amplitude : float
        Global scaling factor applied to the drive amplitude.
    drift_rate : float
        Strength of slow sinusoidal drift in the envelope.
    noise_std : float
        Standard deviation of additive Gaussian noise.
    seed : Optional[int]
        Seed for the RNG (for reproducibility).
    """

    lo_frequency_hz: float
    sample_rate_hz: float
    base_amplitude: float = 1.0
    drift_rate: float = 0.01
    noise_std: float = 0.02
    seed: Optional[int] = None

    def run_schedule(self, schedule: Schedule) -> pd.DataFrame:
        """
        Execute a schedule and return a DataFrame with I/Q samples.
        """
        df = schedule.to_dataframe(self.sample_rate_hz)

        rng = np.random.default_rng(self.seed)
        t = df["t_s"].to_numpy(dtype=float)
        drive = df["drive_amplitude"].to_numpy(dtype=float) * self.base_amplitude

        # Slow envelope drift and Gaussian noise
        drift = 1.0 + self.drift_rate * np.sin(2.0 * np.pi * 0.1 * t)
        noise = self.noise_std * rng.standard_normal(len(t))

        envelope = drive * drift + noise

        # Up-convert to I/Q using the LO
        omega = 2.0 * np.pi * self.lo_frequency_hz
        I = envelope * np.cos(omega * t)
        Q = envelope * np.sin(omega * t)

        df["I"] = I
        df["Q"] = Q

        return df
