"""
Configuration structures for SynQc Temporal Dynamics.

This module defines simple dataclasses for the runtime configuration and

a YAML loader for file-based configs. PyYAML is treated as an optional

dependency; importing this module does not require it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class PulseConfig:
    """
    Definition of a single drive pulse in the SynQc schedule.
    """

    label: str
    amplitude: float
    phase_deg: float
    frequency_hz: float
    duration_ns: float


@dataclass
class SynQcConfig:
    """
    High-level configuration for a SynQc temporal calibration run.
    """

    sample_rate_hz: float
    lo_frequency_hz: float
    cycle_duration_ns: float
    num_cycles: int
    target_amplitude: float = 1.0
    pulses: List[PulseConfig] = field(default_factory=list)
    probe_every_n_cycles: int = 4

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SynQcConfig":
        pulses = [PulseConfig(**p) for p in data.get("pulses", [])]
        return cls(
            sample_rate_hz=float(data["sample_rate_hz"]),
            lo_frequency_hz=float(data["lo_frequency_hz"]),
            cycle_duration_ns=float(data["cycle_duration_ns"]),
            num_cycles=int(data["num_cycles"]),
            target_amplitude=float(data.get("target_amplitude", 1.0)),
            pulses=pulses,
            probe_every_n_cycles=int(data.get("probe_every_n_cycles", 4)),
        )


def load_config(path: str | Path) -> SynQcConfig:
    """
    Load a SynQcConfig from a YAML file.

    PyYAML is imported lazily so that simply importing this module does
    not require the dependency.
    """
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(
            "PyYAML is required to load config files. Install 'pyyaml'."
        ) from exc

    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top of YAML file, got {type(data)}")
    return SynQcConfig.from_dict(data)
