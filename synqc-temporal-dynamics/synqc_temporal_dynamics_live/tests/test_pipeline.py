"""
Basic smoke test for the SynQc Temporal Dynamics live code.
"""

from pathlib import Path
import sys

import pytest

pytest.importorskip("pandas")
pytest.importorskip("numpy")

# Ensure the local package is importable even alongside the root project package
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from synqc_live.config import SynQcConfig, PulseConfig
from synqc_live.engine import SynQcEngine


def test_pipeline_smoke() -> None:
    config = SynQcConfig(
        sample_rate_hz=1e9,
        lo_frequency_hz=50e6,
        cycle_duration_ns=1000.0,
        num_cycles=8,
        target_amplitude=1.0,
        pulses=[
            PulseConfig(
                label="drive",
                amplitude=1.0,
                phase_deg=0.0,
                frequency_hz=50e6,
                duration_ns=400.0,
            ),
        ],
        probe_every_n_cycles=2,
    )

    engine = SynQcEngine.build_default(config)
    df = engine.run_iteration()
    assert not df.empty
    assert {"I", "Q", "amplitude"}.issubset(df.columns)

    result = engine.run_adaptive(num_iterations=3)
    assert not result.empty
    assert {"iteration", "avg_probe_amplitude", "gain"}.issubset(result.columns)
