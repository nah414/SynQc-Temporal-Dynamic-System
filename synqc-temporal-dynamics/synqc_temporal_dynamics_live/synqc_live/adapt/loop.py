"""
Adaptive calibration loop for SynQc Temporal Dynamics.

This loop runs schedule → hardware → demodulation repeatedly and nudges
the drive amplitudes toward a target probe amplitude.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pandas as pd

from ..config import SynQcConfig, PulseConfig
from ..scheduler import Scheduler
from ..hardware import SimulatedBackend
from ..demod import demodulate_probes


@dataclass
class AdaptiveLoop:
    """
    Simple scalar-gain adaptive loop for SynQc.

    The loop adjusts a global gain applied to all pulses such that the
    average probe amplitude approaches a configured target.
    """

    config: SynQcConfig
    scheduler: Scheduler
    backend: SimulatedBackend
    gain: float = 1.0
    learning_rate: float = 0.3
    _base_pulses: List[PulseConfig] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Snapshot baseline pulses so that gain is always applied relative
        # to the original configuration rather than compounding.
        self._base_pulses = [
            PulseConfig(
                label=p.label,
                amplitude=p.amplitude,
                phase_deg=p.phase_deg,
                frequency_hz=p.frequency_hz,
                duration_ns=p.duration_ns,
            )
            for p in self.config.pulses
        ]

    def _apply_gain(self) -> None:
        """
        Apply the current gain to the configuration's pulses.
        """
        scaled: List[PulseConfig] = []
        for p in self._base_pulses:
            scaled.append(
                PulseConfig(
                    label=p.label,
                    amplitude=p.amplitude * self.gain,
                    phase_deg=p.phase_deg,
                    frequency_hz=p.frequency_hz,
                    duration_ns=p.duration_ns,
                )
            )
        self.config.pulses = scaled

    def run(self, num_iterations: int = 5) -> pd.DataFrame:
        """
        Run the adaptive loop for the requested number of iterations.

        Returns a DataFrame of per-iteration metrics, including the
        observed average probe amplitude and the updated gain.
        """
        records: List[dict] = []

        for iteration in range(num_iterations):
            self._apply_gain()
            schedule = self.scheduler.build_schedule()
            raw = self.backend.run_schedule(schedule)
            demod = demodulate_probes(
                raw,
                lo_frequency_hz=self.config.lo_frequency_hz,
                sample_rate_hz=self.config.sample_rate_hz,
            )

            if "amplitude" not in demod.columns:
                raise RuntimeError("Demodulated DataFrame missing 'amplitude' column")

            # Focus on probe regions if available
            if "is_probe" in demod.columns and demod["is_probe"].any():
                region = demod[demod["is_probe"]]
            else:
                region = demod

            avg_amp = float(region["amplitude"].mean())
            error = float(self.config.target_amplitude - avg_amp)

            # Update gain in the direction of the error
            self.gain += self.learning_rate * error

            records.append(
                {
                    "iteration": iteration,
                    "avg_probe_amplitude": avg_amp,
                    "error": error,
                    "gain": self.gain,
                }
            )

        return pd.DataFrame.from_records(records)
