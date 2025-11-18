"""
Timeline and schedule structures for SynQc Temporal Dynamics.

This module defines the canonical timeline representation (pulses, probes,
and the resulting sampled schedule).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd


@dataclass
class Pulse:
    start_ns: float
    duration_ns: float
    amplitude: float
    phase_deg: float
    frequency_hz: float
    label: str = ""


@dataclass
class ProbeWindow:
    start_ns: float
    duration_ns: float
    label: str = "probe"


@dataclass
class Schedule:
    """
    A complete schedule consisting of drive pulses and probe windows.

    The schedule can be rendered into a regularly sampled pandas DataFrame
    compatible with pandas >= 3.0.
    """

    pulses: List[Pulse] = field(default_factory=list)
    probes: List[ProbeWindow] = field(default_factory=list)
    total_duration_ns: float = 0.0

    def to_dataframe(self, sample_rate_hz: float) -> pd.DataFrame:
        """
        Render the schedule into a dense time-series DataFrame with columns:

        - t_s: time in seconds
        - t_ns: time in nanoseconds
        - drive_amplitude: scalar drive envelope
        - drive_phase_deg: drive phase
        - is_probe: boolean mask for probe windows
        """
        if self.total_duration_ns <= 0:
            raise ValueError("total_duration_ns must be positive")

        total_duration_s = self.total_duration_ns * 1e-9
        dt = 1.0 / float(sample_rate_hz)
        num_samples = int(total_duration_s / dt)
        if num_samples <= 0:
            raise ValueError("sample_rate_hz is too low for the requested duration")

        t_s = np.arange(num_samples, dtype=float) * dt
        t_ns = t_s * 1e9

        df = pd.DataFrame({"t_s": t_s, "t_ns": t_ns})
        df["drive_amplitude"] = 0.0
        df["drive_phase_deg"] = 0.0
        df["is_probe"] = False

        # Paint pulses onto the drive amplitude and phase
        for pulse in self.pulses:
            mask = (df["t_ns"] >= pulse.start_ns) & (
                df["t_ns"] < pulse.start_ns + pulse.duration_ns
            )
            if not mask.any():
                continue
            df.loc[mask, "drive_amplitude"] += pulse.amplitude
            df.loc[mask, "drive_phase_deg"] = pulse.phase_deg

        # Mark probe windows
        for probe in self.probes:
            mask = (df["t_ns"] >= probe.start_ns) & (
                df["t_ns"] < probe.start_ns + probe.duration_ns
            )
            if not mask.any():
                continue
            df.loc[mask, "is_probe"] = True

        return df
