import unittest

from synqc.hardware import HardwareSignature
from synqc.probes import drive, probe, seed_default_rng, set_default_rng
from synqc.rng import default_rng, RNG


class TestProbes(unittest.TestCase):
    def test_probe_rng_override(self):
        state = (0.1, -0.2, 0.5)
        gen = default_rng(123)
        val1 = probe(state, shots=100, meas_noise=0.05, rng=gen)
        gen = default_rng(123)
        val2 = probe(state, shots=100, meas_noise=0.05, rng=gen)
        self.assertAlmostEqual(val1, val2)

    def test_probe_ideal_shortcut(self):
        state = (0.0, 0.0, 0.0)
        gen = default_rng(42)
        val = probe(state, shots=100, meas_noise=0.0, rng=gen, ideal=0.75)
        self.assertAlmostEqual(val, 0.75)

    def test_seed_default_rng(self):
        state = (0.0, 0.0, 1.0)
        seed_default_rng(999)
        val1 = probe(state)
        seed_default_rng(999)
        val2 = probe(state)
        self.assertAlmostEqual(val1, val2)

    def test_drive_substeps_matches_manual(self):
        hw = HardwareSignature.superconducting()
        state = (0.0, 0.0, 1.0)
        duration = 4e-7
        detuning = 250e3
        omega = 2.5e6
        coarse = drive(state, detuning, omega, duration, hw, substeps=4)
        manual = state
        for _ in range(4):
            manual = drive(manual, detuning, omega, duration / 4.0, hw, substeps=1)
        for a, b in zip(coarse, manual):
            self.assertAlmostEqual(a, b, places=12)

    def test_set_default_rng_validation(self):
        with self.assertRaises(TypeError):
            set_default_rng("not-a-generator")
        valid = default_rng(1)
        self.assertIs(set_default_rng(valid), valid)
        self.assertIsInstance(valid, RNG)


if __name__ == "__main__":
    unittest.main()
