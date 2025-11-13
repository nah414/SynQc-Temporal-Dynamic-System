from __future__ import annotations

import math
import statistics
from time import perf_counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .probes import drive, probe, add_readout_latency
from .demod import lockin_demod
from .rng import RNG
from .mathkern import measurement_signal, measurement_signals


@dataclass(frozen=True)
class DPDResult:
    t: Sequence[float]
    signal: Sequence[float]
    i_lp: Sequence[float]
    q_lp: Sequence[float]
    phase: float
    amp: float
    states: List[Tuple[float, float, float]]
    probe_mask: Sequence[bool]
    realtime: Optional["RealTimeObservations"] = None


@dataclass(frozen=True)
class RealTimeProfile:
    """Profiling metadata and optimization trace for real-time capture."""

    total_samples: int
    expectation_time_s: float
    noisy_time_s: float
    kernel: str = "scalar"
    avg_expectation_per_sample_s: float = 0.0
    avg_noisy_per_sample_s: float = 0.0
    optimizations: Tuple[str, ...] = ()


@dataclass(frozen=True)
class RealTimeObservations:
    """Container for per-sample qubit observables captured during a DPD run."""

    indices: Tuple[int, ...]
    expectation: Dict[str, Tuple[float, ...]]
    noisy: Optional[Dict[str, Tuple[float, ...]]] = None
    profile: Optional[RealTimeProfile] = None


def _mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def run_dpd_sequence(
    hw,
    detuning_hz,
    omega_hz,
    d1_s,
    probe_s,
    d2_s,
    *,
    readout_axis: str = "z",
    dt_s: float = 1e-7,
    ref_freq_hz: Optional[float] = None,
    shots: int = 200,
    meas_noise: float = 0.02,
    rng: Optional[RNG] = None,
    demod_window: Optional[int] = None,
    demod_window_s: Optional[float] = 0.01,
    drive_substeps: int = 1,
    real_time_axes: Sequence[str] = (),
    real_time_shots: Optional[int] = None,
    real_time_meas_noise: Optional[float] = None,
    real_time_rng: Optional[RNG] = None,
    real_time_stride: int = 1,
    real_time_profile: bool = False,
    real_time_optimize: bool = True,
    real_time_optimize_threshold: float = 5e-06,
    real_time_optimize_warmup: int = 4,
):
    """Simulate a fixed-length drive–probe–drive (DPD) experiment timeline."""

    n1 = max(0, math.ceil(d1_s / dt_s))
    nP = max(0, math.ceil(probe_s / dt_s))
    n2 = max(0, math.ceil(d2_s / dt_s))
    nT = max(1, n1 + nP + n2)

    # Timebase
    t = [dt_s * (i + 1) for i in range(nT)]
    meas = [math.nan] * nT
    states: List[Tuple[float, float, float]] = []

    axes = tuple(dict.fromkeys(real_time_axes))
    realtime_expectation: Dict[str, List[float]] = {axis: [] for axis in axes}
    realtime_noisy: Optional[Dict[str, List[float]]] = None
    rt_stride = max(1, int(real_time_stride))
    if axes:
        rt_shots = shots if real_time_shots is None else real_time_shots
        rt_noise = meas_noise if real_time_meas_noise is None else real_time_meas_noise
        if rt_shots > 0:
            realtime_noisy = {axis: [] for axis in axes}
        realtime_rng = real_time_rng if real_time_rng is not None else rng
        realtime_indices: List[int] = []
        profile_expectation_time = 0.0
        profile_noisy_time = 0.0
        profile_samples = 0
        sample_index = 0
        kernel_mode = "scalar"
        optimizations: List[str] = []
        warmup_target = max(1, int(real_time_optimize_warmup))

        def record_state(current_state: Tuple[float, float, float]):
            nonlocal profile_expectation_time, profile_noisy_time, profile_samples, sample_index, kernel_mode
            states.append(current_state)
            if sample_index % rt_stride == 0:
                profile_samples += 1
                realtime_indices.append(sample_index)
                expectation_cache: Dict[str, float]
                expectation_start = perf_counter() if real_time_profile else None
                if kernel_mode == "bulk":
                    values = measurement_signals(current_state, axes)
                    expectation_cache = dict(zip(axes, values))
                    for axis, val in zip(axes, values):
                        realtime_expectation[axis].append(val)
                else:
                    expectation_cache = {}
                    for axis in axes:
                        val = measurement_signal(current_state, axis=axis)
                        expectation_cache[axis] = val
                        realtime_expectation[axis].append(val)
                if expectation_start is not None:
                    profile_expectation_time += perf_counter() - expectation_start
                    if (
                        real_time_optimize
                        and kernel_mode == "scalar"
                        and len(axes) > 1
                        and profile_samples >= warmup_target
                    ):
                        per_axis_time = profile_expectation_time / (profile_samples * len(axes))
                        if per_axis_time >= real_time_optimize_threshold:
                            kernel_mode = "bulk"
                            optimizations.append("bulk-axis")
                if realtime_noisy is not None:
                    noisy_start = perf_counter() if real_time_profile else None
                    for axis, ideal in expectation_cache.items():
                        realtime_noisy[axis].append(
                            probe(
                                current_state,
                                axis=axis,
                                shots=rt_shots,
                                meas_noise=rt_noise,
                                rng=realtime_rng,
                                ideal=ideal,
                            )
                        )
                    if noisy_start is not None:
                        profile_noisy_time += perf_counter() - noisy_start
            sample_index += 1

    else:

        sample_index = 0

        def record_state(current_state: Tuple[float, float, float]):
            nonlocal sample_index
            states.append(current_state)
            sample_index += 1

    # Reference for demod
    if ref_freq_hz is None:
        ref_freq_hz = detuning_hz if abs(detuning_hz) > 1.0 else 1.0e5

    # Evolve state
    state = (0.0, 0.0, 1.0)

    # Drive 1
    for _ in range(n1):
        state = drive(state, detuning_hz, omega_hz, dt_s, hw, substeps=drive_substeps)
        record_state(state)

    # Probe
    startP = n1
    endP = min(n1 + nP, nT)
    for k in range(startP, endP):
        meas[k] = probe(state, axis=readout_axis, shots=shots, meas_noise=meas_noise, rng=rng)
        record_state(state)

    # Drive 2
    for _ in range(endP, nT):
        state = drive(state, detuning_hz, omega_hz, dt_s, hw, substeps=drive_substeps)
        record_state(state)

    # Build signal and apply latency preserving length
    signal = list(meas)
    signal = add_readout_latency(signal, hw.probe_latency, dt_s)

    # Demodulation over the full vector with zeros outside probe
    probe_mask = [not math.isnan(x) for x in meas]
    demod_input = [signal[i] if probe_mask[i] and not math.isnan(signal[i]) else 0.0 for i in range(nT)]
    i_lp, q_lp = lockin_demod(
        demod_input,
        ref_freq_hz,
        dt_s,
        window=demod_window,
        window_s=demod_window_s,
    )

    if any(probe_mask):
        masked_i = [i_lp[i] for i in range(nT) if probe_mask[i]]
        masked_q = [q_lp[i] for i in range(nT) if probe_mask[i]]
        i_mean = float(_mean(masked_i))
        q_mean = float(_mean(masked_q))
        phase = float(math.atan2(q_mean, i_mean))
        amp = float(math.hypot(i_mean, q_mean))
    else:
        phase = 0.0
        amp = 0.0

    realtime_result = None
    if axes:
        expectation = {axis: tuple(values) for axis, values in realtime_expectation.items()}
        noisy = (
            {axis: tuple(values) for axis, values in realtime_noisy.items()}
            if realtime_noisy is not None
            else None
        )
        profile_data = None
        if real_time_profile:
            avg_expect = (
                profile_expectation_time / profile_samples if profile_samples else 0.0
            )
            avg_noisy = profile_noisy_time / profile_samples if profile_samples else 0.0
            profile_data = RealTimeProfile(
                total_samples=profile_samples,
                expectation_time_s=profile_expectation_time,
                noisy_time_s=profile_noisy_time,
                kernel=kernel_mode,
                avg_expectation_per_sample_s=avg_expect,
                avg_noisy_per_sample_s=avg_noisy,
                optimizations=tuple(optimizations),
            )
        realtime_result = RealTimeObservations(
            indices=tuple(realtime_indices),
            expectation=expectation,
            noisy=noisy,
            profile=profile_data,
        )

    return DPDResult(t, signal, i_lp, q_lp, phase, amp, states, probe_mask, realtime_result)
