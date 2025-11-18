"""
Definitions of probe strategies for SynQc.

A probe strategy determines on which cycles probe windows should be placed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProbeStrategy:
    """
    Simple "every N cycles" probe strategy.
    """

    every_n_cycles: int = 4

    def is_probe_cycle(self, cycle_index: int) -> bool:
        if self.every_n_cycles <= 0:
            return False
        return (cycle_index % self.every_n_cycles) == 0
