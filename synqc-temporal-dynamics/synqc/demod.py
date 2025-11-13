from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple


def _resolve_window(n: int, dt_s: float, window: int | None, window_s: float | None) -> int:
    if window is not None and window <= 0:
        raise ValueError("window must be positive when provided")
    if window is not None:
        return int(window)
    if window_s is not None:
        if window_s <= 0:
            raise ValueError("window_s must be positive when provided")
        if dt_s <= 0:
            return n
        return max(1, int(round(window_s / dt_s)))
    if dt_s <= 0:
        return n
    ideal = int(round(0.01 / dt_s)) if dt_s > 0 else n
    return max(1, min(ideal, max(1, n // 4)))


def _convolve_same(signal: Sequence[float], kernel: Sequence[float]) -> List[float]:
    n = len(signal)
    m = len(kernel)
    half = m // 2
    output: List[float] = []
    for i in range(n):
        acc = 0.0
        for k in range(m):
            idx = i + k - half
            if 0 <= idx < n:
                acc += signal[idx] * kernel[k]
        output.append(acc)
    return output


def _elementwise_mul(a: Sequence[float], b: Sequence[float]) -> List[float]:
    return [x * y for x, y in zip(a, b)]


def _demod_refs(n: int, ref_freq_hz: float, dt_s: float) -> Tuple[List[float], List[float]]:
    t = [i * dt_s for i in range(n)]
    refc = [math.cos(2.0 * math.pi * ref_freq_hz * ti) for ti in t]
    refs = [math.sin(2.0 * math.pi * ref_freq_hz * ti) for ti in t]
    return refc, refs


def lockin_demod(signal: Iterable[float], ref_freq_hz, dt_s, *, window: int | None = None, window_s: float | None = 0.01):
    """Boxcar low-pass of I/Q demod with a configurable averaging window."""

    data = list(signal)
    n = len(data)
    refc, refs = _demod_refs(n, ref_freq_hz, dt_s)
    i_raw = _elementwise_mul(data, refc)
    q_raw = _elementwise_mul(data, refs)
    win = _resolve_window(n, dt_s, window, window_s)
    kernel = [1.0 / win] * win
    i_lp = _convolve_same(i_raw, kernel)
    q_lp = _convolve_same(q_raw, kernel)
    return i_lp, q_lp
