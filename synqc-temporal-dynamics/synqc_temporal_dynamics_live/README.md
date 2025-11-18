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
