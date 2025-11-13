import statistics

import matplotlib.pyplot as plt

from synqc.adapt import ScalarKalman
from synqc.hardware import HardwareSignature
from synqc.scheduler import run_dpd_sequence

# Config
hw = HardwareSignature.superconducting()
detuning_true_hz = 250e3   # true detuning (Hz)
omega_hz = 2.5e6           # Rabi rate (Hz)

d1_s = 2.0e-6
probe_s = 20.0e-6
d2_s = 2.0e-6
dt_s = 2.0e-7

# Tracker
kf = ScalarKalman(x0=0.0, p0=1e12, q=1e7, r=1e6)

est_hist = []
phase_hist = []
innov_hist = []

for _ in range(25):
    detuning_cmd = -kf.x
    residual = detuning_true_hz + detuning_cmd
    res = run_dpd_sequence(hw, residual, omega_hz, d1_s, probe_s, d2_s, readout_axis="z", dt_s=dt_s)

    # Phase → Hz proxy (demo)
    z_meas = res.phase * 1.0e5
    kf.predict()
    x, p, k, innov = kf.update(z_meas, H=1.0)

    est_hist.append(x)
    phase_hist.append(res.phase)
    innov_hist.append(innov)

print("Final estimate (Hz):", est_hist[-1])
print("Mean |innovation|:", statistics.fmean(abs(v) for v in innov_hist))

# Plots
plt.figure()
plt.title("Adaptive detuning estimate")
plt.plot(est_hist, label="Kalman estimate (Hz)")
plt.axhline(0.0, linestyle="--")
plt.xlabel("Iteration")
plt.ylabel("Detuning estimate (Hz)")
plt.legend()
plt.tight_layout()

plt.figure()
plt.title("Probe demodulated phase (proxy)")
plt.plot(phase_hist, label="Measured phase (rad)")
plt.xlabel("Iteration")
plt.ylabel("Phase (rad)")
plt.legend()
plt.tight_layout()

res0 = run_dpd_sequence(
    hw,
    detuning_true_hz,
    omega_hz,
    d1_s,
    probe_s,
    d2_s,
    dt_s=dt_s,
    real_time_axes=("x", "y", "z"),
    real_time_shots=0,
    real_time_stride=4,
    real_time_profile=True,
)
plt.figure()
plt.title("DPD: raw probe window (with NaNs elsewhere)")
plt.plot(res0.t, res0.signal, label="Measured (probe window)")
plt.xlabel("Time (s)")
plt.ylabel("Signal (arb)")
plt.legend()
plt.tight_layout()

if res0.realtime is not None:
    if res0.realtime.profile:
        profile = res0.realtime.profile
        print(
            "Real-time capture stride=4 →",
            profile.total_samples,
            "samples",
            f"(expectation walltime: {profile.expectation_time_s:.6f}s)",
            f"kernel={profile.kernel}",
            f"optimizations={list(profile.optimizations)}",
        )
    plt.figure()
    plt.title("DPD: real-time Bloch expectations")
    sample_times = [res0.t[i] for i in res0.realtime.indices]
    for axis, values in res0.realtime.expectation.items():
        plt.plot(sample_times, values, label=f"<{axis}>")
    plt.xlabel("Time (s)")
    plt.ylabel("Expectation value")
    plt.legend()
    plt.tight_layout()

plt.show()
