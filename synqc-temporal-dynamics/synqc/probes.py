from __future__ import annotations

import math
from typing import Optional

from .mathkern import bloch_update, t1_t2_relax, measurement_signal
from .rng import RNG, default_rng

_DEFAULT_RNG: RNG = default_rng()


def seed_default_rng(seed: Optional[int] = None) -> RNG:
    """Seed and return the module-level default RNG used by :func:`probe`."""

    global _DEFAULT_RNG
    _DEFAULT_RNG = default_rng(seed)
    return _DEFAULT_RNG


def set_default_rng(generator: RNG) -> RNG:
    """Override the module-level RNG with a caller-supplied instance."""

    if not isinstance(generator, RNG):
        raise TypeError("generator must be an instance of synqc.rng.RNG")
    global _DEFAULT_RNG
    _DEFAULT_RNG = generator
    return _DEFAULT_RNG


def get_default_rng() -> RNG:
    """Return the RNG used when :func:`probe` is called without an override."""

    return _DEFAULT_RNG


def drive(state, detuning_hz, omega_hz, duration_s, hw, substeps: int = 1):
    """Integrate a constant drive segment, optionally with sub-stepping."""

    if substeps < 1:
        raise ValueError("substeps must be >= 1")

    det = 2.0 * math.pi * detuning_hz
    omg = 2.0 * math.pi * omega_hz
    sub_dt = duration_s / substeps if substeps > 1 else duration_s
    x, y, z = state
    for _ in range(substeps):
        x, y, z = bloch_update((x, y, z), det, omg, sub_dt)
        x, y, z = t1_t2_relax((x, y, z), sub_dt, hw.t1, hw.t2)
    return (x, y, z)


def probe(
    state,
    axis="z",
    shots=200,
    meas_noise=0.02,
    rng: Optional[RNG] = None,
    *,
    ideal: Optional[float] = None,
):
    """Return a noisy readout of the expectation along ``axis``."""

    generator = rng if rng is not None else _DEFAULT_RNG
    if ideal is None:
        ideal = measurement_signal(state, axis=axis)
    noise_sigma = meas_noise / math.sqrt(max(1, shots))
    noise = generator.normal(0.0, noise_sigma)
    return float(ideal + noise)


def add_readout_latency(samples, latency_s, dt_s):
    """Shift samples by integer bins of latency; preserve length."""

    n = len(samples)
    bins = int(round(latency_s / dt_s))
    if bins <= 0 or bins >= n:
        return list(samples)
    out = list(samples)
    for i in range(bins):
        out[i] = 0.0
    for i in range(bins, n):
        out[i] = samples[i - bins]
    return out
