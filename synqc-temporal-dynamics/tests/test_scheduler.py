import math
import statistics
import unittest

from synqc.hardware import HardwareSignature
from synqc.scheduler import (
    DPDResult,
    RealTimeObservations,
    RealTimeProfile,
    run_dpd_sequence,
)
from synqc.rng import RNG, default_rng


def _std(values):
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _mean(values):
    return statistics.fmean(values) if values else 0.0


class TestScheduler(unittest.TestCase):
    def test_lengths_and_mask(self):
        hw = HardwareSignature.superconducting()
        rng = default_rng(42)
        res = run_dpd_sequence(
            hw,
            detuning_hz=250e3,
            omega_hz=2.5e6,
            d1_s=2e-6,
            probe_s=20e-6,
            d2_s=2e-6,
            dt_s=2e-7,
            rng=rng,
            demod_window=8,
        )
        self.assertIsInstance(res, DPDResult)
        n = len(res.t)
        self.assertEqual(n, len(res.signal))
        self.assertEqual(n, len(res.i_lp))
        self.assertEqual(n, len(res.q_lp))
        self.assertEqual(n, len(res.probe_mask))
        mask = res.probe_mask
        self.assertGreater(sum(1 for flag in mask if flag), 0)
        self.assertTrue(any(mask))
        self.assertTrue(all(not math.isnan(res.signal[i]) for i, flag in enumerate(mask) if flag))

    def test_latency_guard(self):
        hw = HardwareSignature.superconducting()
        hw.probe_latency = 1.0  # way larger than experiment time
        res = run_dpd_sequence(
            hw,
            detuning_hz=100e3,
            omega_hz=1e6,
            d1_s=1e-6,
            probe_s=2e-6,
            d2_s=1e-6,
            dt_s=1e-7,
            drive_substeps=2,
        )
        self.assertEqual(len(res.t), len(res.signal))

    def test_demod_window_effect(self):
        hw = HardwareSignature.superconducting()
        base = run_dpd_sequence(hw, detuning_hz=200e3, omega_hz=2e6,
                                d1_s=1.2e-6, probe_s=8e-6, d2_s=1.2e-6, dt_s=2e-7,
                                demod_window=1)
        smooth = run_dpd_sequence(hw, detuning_hz=200e3, omega_hz=2e6,
                                  d1_s=1.2e-6, probe_s=8e-6, d2_s=1.2e-6, dt_s=2e-7,
                                  demod_window=25)
        self.assertEqual(len(base.i_lp), len(smooth.i_lp))
        base_centered = [x - _mean(base.i_lp) for x in base.i_lp]
        smooth_centered = [x - _mean(smooth.i_lp) for x in smooth.i_lp]
        self.assertLess(_std(smooth_centered), _std(base_centered))

    def test_realtime_observations_alignment(self):
        hw = HardwareSignature.superconducting()
        rng = default_rng(7)
        realtime_rng = RNG(99)
        res = run_dpd_sequence(
            hw,
            detuning_hz=150e3,
            omega_hz=1.5e6,
            d1_s=1.0e-6,
            probe_s=6.0e-6,
            d2_s=1.0e-6,
            dt_s=2.0e-7,
            rng=rng,
            real_time_axes=("x", "z"),
            real_time_shots=400,
            real_time_meas_noise=0.0,
            real_time_rng=realtime_rng,
        )

        self.assertIsInstance(res.realtime, RealTimeObservations)
        realtime = res.realtime
        self.assertSetEqual(set(realtime.expectation), {"x", "z"})
        self.assertEqual(len(res.t), len(res.states))
        for axis in ("x", "z"):
            self.assertEqual(len(realtime.expectation[axis]), len(res.t))
        self.assertIsNotNone(realtime.noisy)
        for axis in ("x", "z"):
            self.assertEqual(len(realtime.noisy[axis]), len(res.t))
        self.assertEqual(tuple(range(len(res.t))), realtime.indices)

        for idx, state in enumerate(res.states):
            self.assertAlmostEqual(realtime.expectation["x"][idx], state[0], places=7)
            self.assertAlmostEqual(realtime.expectation["z"][idx], state[2], places=7)
            # zero measurement noise => noisy readouts match expectation deterministically
            self.assertAlmostEqual(
                realtime.noisy["z"][idx], realtime.expectation["z"][idx], places=7
            )

        # When axes are supplied we should still preserve probe mask semantics.
        probe_samples = sum(1 for flag in res.probe_mask if flag)
        self.assertGreater(probe_samples, 0)

    def test_realtime_stride_and_profile(self):
        hw = HardwareSignature.superconducting()
        res = run_dpd_sequence(
            hw,
            detuning_hz=175e3,
            omega_hz=1.75e6,
            d1_s=1.5e-6,
            probe_s=9.0e-6,
            d2_s=1.5e-6,
            dt_s=2.5e-7,
            real_time_axes=("x",),
            real_time_shots=0,
            real_time_stride=3,
            real_time_profile=True,
        )

        self.assertIsNotNone(res.realtime)
        realtime = res.realtime
        self.assertIsNone(realtime.noisy)
        samples_expected = math.ceil(len(res.t) / 3)
        self.assertEqual(len(realtime.expectation["x"]), samples_expected)
        self.assertEqual(len(realtime.indices), samples_expected)
        self.assertEqual(realtime.indices[0], 0)
        self.assertTrue(all(realtime.indices[i] < realtime.indices[i + 1] for i in range(len(realtime.indices) - 1)))
        profile = realtime.profile
        self.assertIsInstance(profile, RealTimeProfile)
        self.assertEqual(profile.total_samples, samples_expected)
        self.assertGreaterEqual(profile.expectation_time_s, 0.0)
        self.assertEqual(profile.noisy_time_s, 0.0)
        self.assertEqual(profile.kernel, "scalar")
        self.assertEqual(profile.optimizations, ())

    def test_realtime_stride_coerces_minimum(self):
        hw = HardwareSignature.superconducting()
        res = run_dpd_sequence(
            hw,
            detuning_hz=125e3,
            omega_hz=1.25e6,
            d1_s=1.0e-6,
            probe_s=4.0e-6,
            d2_s=1.0e-6,
            dt_s=2.0e-7,
            real_time_axes=("z",),
            real_time_shots=0,
            real_time_stride=0,
        )

        self.assertEqual(len(res.realtime.expectation["z"]), len(res.t))
        self.assertEqual(tuple(range(len(res.t))), res.realtime.indices)

    def test_realtime_optimizer_switches_kernel(self):
        hw = HardwareSignature.superconducting()
        res = run_dpd_sequence(
            hw,
            detuning_hz=200e3,
            omega_hz=2.2e6,
            d1_s=1.2e-6,
            probe_s=8.0e-6,
            d2_s=1.2e-6,
            dt_s=2.0e-7,
            real_time_axes=("x", "y", "z"),
            real_time_shots=0,
            real_time_stride=1,
            real_time_profile=True,
            real_time_optimize=True,
            real_time_optimize_threshold=0.0,
            real_time_optimize_warmup=1,
        )

        realtime = res.realtime
        self.assertIsNotNone(realtime)
        profile = realtime.profile
        self.assertIsNotNone(profile)
        self.assertEqual(profile.kernel, "bulk")
        self.assertIn("bulk-axis", profile.optimizations)
        self.assertGreaterEqual(profile.avg_expectation_per_sample_s, 0.0)
        self.assertGreaterEqual(profile.avg_noisy_per_sample_s, 0.0)


if __name__ == "__main__":
    unittest.main()
