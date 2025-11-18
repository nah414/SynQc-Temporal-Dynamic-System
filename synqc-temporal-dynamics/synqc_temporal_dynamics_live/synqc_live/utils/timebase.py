"""
Timebase conversion utilities for SynQc.
"""


def ns_to_s(ns: float) -> float:
    """
    Convert nanoseconds to seconds.
    """
    return ns * 1e-9


def s_to_ns(seconds: float) -> float:
    """
    Convert seconds to nanoseconds.
    """
    return seconds * 1e9
