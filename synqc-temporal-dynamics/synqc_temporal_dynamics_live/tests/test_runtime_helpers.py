"""Tests for the environment-agnostic runtime helpers."""

from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("numpy")

from synqc_live.runtime import (
    PipelineResult,
    build_quickstart_config,
    run_pipeline,
    run_pipeline_from_yaml,
)


@pytest.fixture()
def quickstart_config():
    return build_quickstart_config()


def test_build_quickstart_config_defaults(quickstart_config):
    assert quickstart_config.num_cycles == 8
    assert quickstart_config.probe_every_n_cycles == 2
    assert len(quickstart_config.pulses) == 1
    drive = quickstart_config.pulses[0]
    assert drive.label == "drive"


def test_run_pipeline_without_adaptive(quickstart_config):
    result = run_pipeline(quickstart_config, run_adaptive=False)
    assert isinstance(result, PipelineResult)
    assert isinstance(result.iteration, pd.DataFrame)
    assert result.adaptive is None
    assert not result.iteration.empty


def test_run_pipeline_with_adaptive(quickstart_config):
    result = run_pipeline(quickstart_config, num_iterations=2, run_adaptive=True)
    assert result.adaptive is not None
    adaptive_df = result.require_adaptive()
    assert {"iteration", "gain"}.issubset(adaptive_df.columns)


@pytest.mark.parametrize("num_iterations", [0, -1])
def test_run_pipeline_validates_iteration_count(quickstart_config, num_iterations):
    with pytest.raises(ValueError):
        run_pipeline(quickstart_config, num_iterations=num_iterations)


def test_run_pipeline_from_yaml(tmp_path, quickstart_config):
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
        sample_rate_hz: 1e9
        lo_frequency_hz: 50e6
        cycle_duration_ns: 1000.0
        num_cycles: 8
        target_amplitude: 1.0
        pulses:
          - label: drive
            amplitude: 1.0
            phase_deg: 0.0
            frequency_hz: 50e6
            duration_ns: 400.0
        probe_every_n_cycles: 2
        """,
        encoding="utf-8",
    )

    result = run_pipeline_from_yaml(yaml_path, run_adaptive=False)
    assert isinstance(result.iteration, pd.DataFrame)
    assert result.adaptive is None

    with pytest.raises(FileNotFoundError):
        run_pipeline_from_yaml(Path("does-not-exist.yaml"))
