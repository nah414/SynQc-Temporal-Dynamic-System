"""Lightweight random number helpers avoiding external dependencies."""

from __future__ import annotations

import random
from typing import Optional


class RNG:
    """Wrapper around :class:`random.Random` providing a NumPy-like API subset."""

    __slots__ = ("_rng",)

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random()
        if seed is not None:
            self._rng.seed(seed)
        else:
            self._rng.seed()

    def normal(self, mean: float = 0.0, stddev: float = 1.0) -> float:
        """Return a normally distributed sample with the given mean and stddev."""

        return self._rng.gauss(mean, stddev)

    def uniform(self, a: float = 0.0, b: float = 1.0) -> float:
        """Return a uniformly distributed sample in ``[a, b)``."""

        return self._rng.uniform(a, b)

    def seed(self, value: Optional[int]) -> None:
        """Seed the underlying PRNG."""

        self._rng.seed(value)


def default_rng(seed: Optional[int] = None) -> RNG:
    """Create a new :class:`RNG` seeded with ``seed``."""

    return RNG(seed)
