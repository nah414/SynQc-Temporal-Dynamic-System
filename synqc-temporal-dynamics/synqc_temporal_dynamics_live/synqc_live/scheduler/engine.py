"""
Schedule construction logic for SynQc Temporal Dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..config import SynQcConfig, PulseConfig
from ..timeline import Pulse, ProbeWindow, Schedule
from ..probes import ProbeStrategy


@dataclass
class Scheduler:
    """
    Build a time-ordered Schedule from a SynQcConfig.

    This is a deliberately simple implementation that generates a fixed
    pattern of drive pulses per cycle and probe windows at the tail of
    designated cycles.
    """

    config: SynQcConfig
    probe_strategy: ProbeStrategy = field(init=False)

    def __post_init__(self) -> None:
        self.probe_strategy = ProbeStrategy(
            every_n_cycles=self.config.probe_every_n_cycles
        )

    def build_schedule(self) -> Schedule:
        pulses: List[Pulse] = []
        probes: List[ProbeWindow] = []

        cycle_ns = self.config.cycle_duration_ns
        total_duration_ns = cycle_ns * self.config.num_cycles

        for cycle in range(self.config.num_cycles):
            cycle_start = cycle * cycle_ns
            offset = 0.0

            # Emit configured pulses within this cycle
            for pc in self.config.pulses:
                pulses.append(
                    Pulse(
                        start_ns=cycle_start + offset,
                        duration_ns=pc.duration_ns,
                        amplitude=pc.amplitude,
                        phase_deg=pc.phase_deg,
                        frequency_hz=pc.frequency_hz,
                        label=f"{pc.label}_c{cycle}",
                    )
                )
                offset += pc.duration_ns

            # Optionally append a probe window at the tail of the cycle
            if self.probe_strategy.is_probe_cycle(cycle):
                probe_duration_ns = min(0.25 * cycle_ns, cycle_ns)
                probes.append(
                    ProbeWindow(
                        start_ns=cycle_start + cycle_ns - probe_duration_ns,
                        duration_ns=probe_duration_ns,
                        label=f"probe_c{cycle}",
                    )
                )

        return Schedule(
            pulses=pulses,
            probes=probes,
            total_duration_ns=total_duration_ns,
        )
