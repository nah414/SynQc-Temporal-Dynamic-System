
# SynQc: Temporal Dynamics Series (v0.2)

**One sentence:** This project simulates a common control pattern for qubits called **Drive–Probe–Drive (DPD)** and shows how a simple tracker can learn and correct frequency errors over time.

## What this is (plain English)
- We "drive" a tiny quantum system, "probe" it to see how it responds, then "drive" again.
- From the probe data we demodulate a **phase** signal (think: a timing offset).
- A lightweight **Kalman tracker** uses that phase as a clue to estimate how far off our frequency is.
- The code is modular and hardware‑agnostic: superconducting, ion traps, neutral atoms, photonics.

## Why it matters
Real quantum hardware drifts. If you can measure that drift quickly and cheaply, you can correct your drive settings and keep the system on target. This repo shows the moving parts clearly: evolution → probe → demod → estimate.

## What's inside
- `synqc/` — the library
  - `mathkern.py` — Bloch‑sphere math and simple T1/T2 relaxation.
  - `hardware.py` — quick profiles for different hardware families.
  - `probes.py` — drive steps, noisy probe readout, and latency handling with configurable RNGs.
  - `demod.py` — I/Q demodulation with a configurable low‑pass filter window.
  - `adapt.py` — scalar Kalman tracker (single‑parameter).
  - `scheduler.py` — builds the full DPD timeline, exposes real-time observables, and returns dataclass results.
- `examples/simulate_dpd.py` — run this to see plots.
- `tests/` — unit tests to keep the basics safe.
- `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `LICENSE` — project hygiene.

## Quick start (Windows, macOS, Linux)
```bash
# From the repo root
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt  # install wheels from a local mirror if offline
pip install -e .
python examples/simulate_dpd.py
```

### Offline or air-gapped environments

If you run in a restricted network, pre-download a `matplotlib` wheel and place it in a local directory. Then

```bash
pip install --no-index --find-links /path/to/wheels -r requirements.txt
pip install --no-index --find-links /path/to/wheels -e .
```

The project now ships a `requirements.txt` to make caching easier.

You’ll see four plots:
1. **Adaptive detuning estimate** — how the tracker changes its guess each iteration.
2. **Demodulated phase** — the phase we extract from the probe data.
3. **Raw probe window** — the measured section of the timeline (NaNs elsewhere).
4. **Real-time Bloch expectations** — optional multi-axis observables captured throughout the drive/probe schedule.

## How it works (two-minute tour)
1. **Evolve** a Bloch vector under a drive with a possible detuning (frequency error).
2. **Probe** the system and read out an axis (we use `z`). Some noise is added.
3. **Demodulate**: multiply by sine/cosine at a reference frequency and low‑pass to get I/Q → phase.
4. **Track**: a small Kalman filter turns phase into an updated detuning estimate.
5. **Repeat**: use that estimate to cancel future errors.

## Configuration you can tweak
- **Durations**: `d1_s`, `probe_s`, `d2_s` and **time step** `dt_s`.
- **Drive**: `detuning_hz`, `omega_hz` (Rabi rate), and optional `drive_substeps` to sub-divide integration.
- **Noise**: measurement noise, number of shots, and which RNG instance you pass to `run_dpd_sequence`/`probe`.
- **Real-time observables**: request `real_time_axes` (with optional shot/noise settings) to record Bloch expectations alongside the probe window, optionally thinning captures via `real_time_stride`, collecting profiling metadata with `real_time_profile`, letting `real_time_optimize` auto-switch to a bulk expectation kernel when profiles show multi-axis pressure, and using `RealTimeObservations.indices` to align the down-sampled points with the global timeline.
- **Tracker**: Kalman `q` (process noise), `r` (measurement noise), and the scale from phase→Hz (demo uses `1e5`).
- **Demodulation**: set `demod_window`/`demod_window_s` to control the boxcar window length.

## Tests & CI
- Run tests locally: `python -m unittest discover -s tests -v`.
- GitHub Actions workflow included (`.github/workflows/ci.yml`) testing Python 3.10–3.12.

## Known limits / next steps
- The phase→Hz mapping is a simple demo scale. For accurate calibration, build a small curve of phase vs detuning around the operating point and feed that to the tracker.
- An **EKF/UKF** can estimate multiple parameters at once (detuning, Rabi rate, T2).
- The demod filter is a basic boxcar. A short causal IIR or a Hann‑windowed FIR will reduce edge effects.

## License
MIT (see `LICENSE`). Use freely in your lab or product. Contributions welcome.
