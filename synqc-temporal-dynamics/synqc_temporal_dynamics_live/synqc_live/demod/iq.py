"""
IQ demodulation for SynQc Temporal Dynamics.

For the initial live implementation, we assume the backend already produces
I/Q samples at baseband. Demodulation therefore reduces to computing
amplitude and phase time series, with probe regions preserved via the
`is_probe` mask.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def demodulate_probes(
    raw_df: pd.DataFrame,
    lo_frequency_hz: float,
    sample_rate_hz: float,
    *,
    copy: bool = True,
) -> pd.DataFrame:
    """
    Compute amplitude and phase from I/Q samples.

    Parameters
    ----------
    raw_df : DataFrame
        Input DataFrame with columns at least ['I', 'Q'] and optionally 'is_probe'.
    lo_frequency_hz : float
        Local oscillator frequency (currently unused, reserved for future refinements).
    sample_rate_hz : float
        Sample rate in Hz (currently unused, reserved for future refinements).
    copy : bool
        Whether to copy the input DataFrame (default True).

    Returns
    -------
    DataFrame
        Same index as the input, with added 'amplitude' and 'phase_rad' columns.
    """
    df = raw_df.copy() if copy else raw_df

    if "I" not in df.columns or "Q" not in df.columns:
        raise ValueError("raw_df must contain 'I' and 'Q' columns")

    I = df["I"].to_numpy(dtype=float)
    Q = df["Q"].to_numpy(dtype=float)

    df["amplitude"] = np.sqrt(I * I + Q * Q)
    df["phase_rad"] = np.arctan2(Q, I)

    return df
