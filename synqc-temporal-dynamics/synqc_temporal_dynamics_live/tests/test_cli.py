import argparse
from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("numpy")

import synqc_live.cli as cli


class FakeResult:
    def __init__(self, iteration=None, adaptive=None):
        self.iteration = iteration
        self.adaptive = adaptive


class DummyCSV:
    def __init__(self):
        self.calls = []

    def to_csv(self, path, index):
        self.calls.append((path, index))


def test_parse_args_defaults():
    args = cli._parse_args([])
    assert args.config is None
    assert args.iterations == 5
    assert args.no_adapt is False
    assert args.dump_iteration_csv is None
    assert args.dump_adaptive_csv is None


def test_main_runs_quickstart(monkeypatch):
    calls = {}

    def fake_build_quickstart():
        return "CFG"

    def fake_run_pipeline(cfg, num_iterations, run_adaptive):
        calls["run_pipeline"] = (cfg, num_iterations, run_adaptive)
        return FakeResult()

    monkeypatch.setattr(cli, "build_quickstart_config", fake_build_quickstart)
    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(cli, "_print_summary", lambda result: None)

    cli.main(["--iterations", "3", "--no-adapt"])

    assert calls["run_pipeline"] == ("CFG", 3, False)


def test_main_runs_from_yaml(monkeypatch, tmp_path):
    calls = {}
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text("dummy: true")

    def fake_run_pipeline_from_yaml(path, num_iterations, run_adaptive):
        calls["run_pipeline_from_yaml"] = (path, num_iterations, run_adaptive)
        return FakeResult()

    monkeypatch.setattr(cli, "run_pipeline_from_yaml", fake_run_pipeline_from_yaml)
    monkeypatch.setattr(cli, "_print_summary", lambda result: None)

    cli.main(["--config", str(yaml_path), "-n", "2"])

    assert calls["run_pipeline_from_yaml"] == (yaml_path, 2, True)


def test_main_writes_csv(monkeypatch, tmp_path):
    iteration_csv = tmp_path / "iter.csv"
    adaptive_csv = tmp_path / "adaptive.csv"
    iteration_df = DummyCSV()
    adaptive_df = DummyCSV()

    def fake_run_pipeline(cfg, num_iterations, run_adaptive):
        return FakeResult(iteration_df, adaptive_df)

    monkeypatch.setattr(cli, "build_quickstart_config", lambda: "CFG")
    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(cli, "_print_summary", lambda result: None)

    cli.main([
        "--iterations",
        "1",
        "--dump-iteration-csv",
        str(iteration_csv),
        "--dump-adaptive-csv",
        str(adaptive_csv),
    ])

    assert iteration_df.calls == [(Path(iteration_csv), False)]
    assert adaptive_df.calls == [(Path(adaptive_csv), False)]
