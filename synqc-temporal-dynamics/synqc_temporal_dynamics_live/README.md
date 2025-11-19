# SynQc Temporal Dynamic System – Live Core

This folder provides a **live Python implementation** of the core
SynQc Temporal Dynamics pipeline described in the design documents. It
is packaged as `synqc_live` to avoid colliding with the legacy
`synqc` module shipped alongside the historical simulation code:

- `synqc_live/` – core package
  - `config.py` – `SynQcConfig`, `PulseConfig`, YAML loader
  - `timeline.py` – `Pulse`, `ProbeWindow`, `Schedule`
  - `engine.py` – `SynQcEngine` façade
  - `scheduler/` – `Scheduler` for building schedules
  - `probes/` – probe strategy definitions
  - `demod/` – IQ demodulation helpers
  - `adapt/` – adaptive calibration loop
  - `hardware/` – `SimulatedBackend` for I/Q generation
  - `utils/` – timebase helpers

- `tests/` – smoke test to verify the pipeline executes

The implementation uses **pandas >= 3.0** and **numpy** for time-series
manipulation and synthetic signal generation.

If you are preparing a fresh environment, install the core dependencies via:

```bash
pip install -r requirements.txt
```

When working offline, cache wheels for `pandas` (3.x series), `numpy`, and `pyyaml` so that the live
helpers and tests can import their dependencies without network access. You can direct the
bootstrap helper to that directory to avoid proxy failures:

```bash
python utils/install_deps.py --wheel-dir /path/to/wheels
```

## Quick-start example

```python
from synqc_live.config import SynQcConfig, PulseConfig
from synqc_live.engine import SynQcEngine

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

# Run a single iteration
df_iteration = engine.run_iteration()

# Run an adaptive loop
df_adapt = engine.run_adaptive(num_iterations=5)
print(df_adapt)
```

## Helper script

To exercise the live pipeline without installing the package, run the
example script:

```bash
python examples/run_live_pipeline.py
```

It ensures the local sources are on `PYTHONPATH`, executes a short
pipeline iteration plus an adaptive loop (default: two iterations), and
optionally recreates a `synqc_temporal_dynamics_live.zip` archive of the
directory for convenient transfer.

Command-line options:

- `-n/--iterations` — number of adaptive loop iterations
- `--skip-zip` — skip rebuilding the archive
- `--zip-path PATH` — override the archive location

## Runtime helper API

The `synqc_live.runtime` module offers a thin, environment-agnostic wrapper around the engine so you can
configure and run the pipeline from notebooks, CLIs, or batch jobs:

```python
from synqc_live import build_quickstart_config, run_pipeline, run_pipeline_from_yaml

# Start from the baked-in demo configuration
config = build_quickstart_config()
result = run_pipeline(config, num_iterations=3)
iteration_df = result.iteration
adaptive_df = result.require_adaptive()

# Or load a YAML config file directly
result = run_pipeline_from_yaml("config.yaml", num_iterations=2)
```

The `PipelineResult` wrapper exposes `require_adaptive()` to guard against missing adaptive metrics when the
loop is disabled.

## Notebook helpers

For quick experiments in Jupyter, call the notebook-friendly helpers that layer on top of the runtime API:

```python
from synqc_live.notebook_helpers import quickstart_demo

iter_df, adapt_df = quickstart_demo(num_iterations=5, plot=True)
```

If you prefer to construct your own configuration inline, you can still build and execute the engine directly:

```python
from synqc_live.config import SynQcConfig, PulseConfig
from synqc_live.engine import SynQcEngine

cfg = SynQcConfig(
    sample_rate_hz=1e9,
    lo_frequency_hz=50e6,
    cycle_duration_ns=1000.0,
    num_cycles=8,
    target_amplitude=1.0,
    pulses=[PulseConfig(
        label="drive",
        amplitude=1.0,
        phase_deg=0.0,
        frequency_hz=50e6,
        duration_ns=400.0,
    )],
    probe_every_n_cycles=2,
)

engine = SynQcEngine.build_default(cfg)
df_iter = engine.run_iteration()
df_loop = engine.run_adaptive(num_iterations=5)
```

## Command-line interface

Install the package and invoke the lightweight CLI to run the same helpers from a shell:

```bash
synqc-live --iterations 3 --config config.yaml
```

If you omit `--config`, the CLI falls back to the baked-in quickstart configuration. Pass
`--dump-iteration-csv` or `--dump-adaptive-csv` to persist the resulting DataFrames.

## Run inline after installing dependencies

If you prefer to install dependencies and run the snippet directly,
install the requirements and execute the following example:

```bash
pip install -r requirements.txt

python - <<'PY'
from synqc_live.config import SynQcConfig, PulseConfig
from synqc_live.engine import SynQcEngine

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
df_iter = engine.run_iteration()
df_loop = engine.run_adaptive(num_iterations=5)
print(df_loop)
PY
```
