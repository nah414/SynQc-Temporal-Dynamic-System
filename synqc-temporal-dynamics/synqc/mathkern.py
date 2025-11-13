"""Minimal numerical kernels without NumPy dependency."""

from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple


def rabi_phase(detuning: float, omega: float, duration: float) -> float:
    """Return Ω_eff * t where Ω_eff = sqrt(Ω^2 + Δ^2)."""

    omega_eff = math.hypot(omega, detuning)
    return omega_eff * duration


def bloch_update(state: Tuple[float, float, float], detuning: float, omega: float, duration: float) -> Tuple[float, float, float]:
    """Bloch vector rotation under H ∝ Ω σ_x + Δ σ_z (units: rad/s, s)."""

    x, y, z = state
    omega_eff = math.hypot(omega, detuning)
    if omega_eff == 0.0 or duration == 0.0:
        return x, y, z

    nx, ny, nz = omega / omega_eff, 0.0, detuning / omega_eff
    theta = omega_eff * duration

    r = (x, y, z)
    n = (nx, ny, nz)
    r_par = _scale_vec(n, _dot(r, n))
    r_perp = _sub_vec(r, r_par)
    r_rot = _add_vec(r_par, _add_vec(_scale_vec(r_perp, math.cos(theta)), _scale_vec(_cross(n, r), math.sin(theta))))
    return tuple(r_rot)


def t1_t2_relax(state: Tuple[float, float, float], tstep: float, t1: float, t2: float) -> Tuple[float, float, float]:
    """Apply T1/T2 damping toward |0> (z=+1)."""

    x, y, z = state
    if t2 > 0:
        decay = math.exp(-tstep / t2)
        x *= decay
        y *= decay
    if t1 > 0:
        z = 1.0 - (1.0 - z) * math.exp(-tstep / t1)
    return x, y, z


def measurement_signal(state: Tuple[float, float, float], axis: str = "z") -> float:
    """Ideal expectation along axis."""

    x, y, z = state
    if axis == "x":
        return x
    if axis == "y":
        return y
    return z


def measurement_signals(state: Tuple[float, float, float], axes: Sequence[str]) -> Tuple[float, ...]:
    """Return ideal expectations for multiple axes in one pass.

    This helper avoids repeated branch checks in tight loops where the
    caller needs many projections of the same state, allowing schedulers to
    switch to a marginally faster bulk path when real-time capture profiles
    indicate the scalar helper is a bottleneck.
    """

    x, y, z = state
    results = []
    for axis in axes:
        if axis == "x":
            results.append(x)
        elif axis == "y":
            results.append(y)
        else:
            results.append(z)
    return tuple(results)


def _dot(a: Iterable[float], b: Iterable[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _scale_vec(vec: Iterable[float], scale: float):
    return tuple(scale * x for x in vec)


def _sub_vec(a: Iterable[float], b: Iterable[float]):
    return tuple(x - y for x, y in zip(a, b))


def _add_vec(a: Iterable[float], b: Iterable[float]):
    return tuple(x + y for x, y in zip(a, b))


def _cross(a: Iterable[float], b: Iterable[float]):
    ax, ay, az = a
    bx, by, bz = b
    return (
        ay * bz - az * by,
        az * bx - ax * bz,
        ax * by - ay * bx,
    )
