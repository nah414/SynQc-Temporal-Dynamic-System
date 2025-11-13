
# Changelog

## 0.2.0 — Fixed
- Deterministic scheduler with preallocated timeline (no shape mismatches).
- Latency applied after full timeline build; length-preserving shift.
- Demod low-pass window now capped.
- Added unit tests and CI workflow.
- Layman's README and packaging via `pyproject.toml`.
- Removed the NumPy dependency by providing pure-Python numeric kernels and RNG helpers.
- Real-time observable capture now supports configurable stride, sample indices, and optional profiling telemetry.
- Real-time profiling now powers an auto-switching bulk expectation kernel for multi-axis timelines.
