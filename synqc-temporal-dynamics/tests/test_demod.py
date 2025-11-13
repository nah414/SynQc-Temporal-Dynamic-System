import unittest

from synqc.demod import lockin_demod


def _max_abs(values):
    return max(abs(v) for v in values) if values else 0.0


class TestDemod(unittest.TestCase):
    def test_explicit_window_samples(self):
        signal = [1.0] * 100
        i_lp, q_lp = lockin_demod(signal, ref_freq_hz=1e6, dt_s=1e-6, window=5)
        self.assertEqual(len(signal), len(i_lp))
        self.assertLessEqual(_max_abs(q_lp), 1e-6)

    def test_window_seconds(self):
        signal = [1.0] * 50
        i_lp, _ = lockin_demod(signal, ref_freq_hz=1e3, dt_s=1e-3, window=None, window_s=0.005)
        # 5 ms window -> ~5 samples for dt=1 ms
        self.assertEqual(len(signal), len(i_lp))

    def test_invalid_window(self):
        signal = [1.0] * 10
        with self.assertRaises(ValueError):
            lockin_demod(signal, ref_freq_hz=1e3, dt_s=1e-3, window=0)
        with self.assertRaises(ValueError):
            lockin_demod(signal, ref_freq_hz=1e3, dt_s=1e-3, window=None, window_s=0.0)


if __name__ == "__main__":
    unittest.main()
