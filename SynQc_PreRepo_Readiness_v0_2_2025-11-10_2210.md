# SynQc: Temporal Dynamics Series — Pre‑Repo Readiness Spec (v0.2)
**Date:** November 10, 2025 ()  
**Location:** America/Chicago  
**Author:** Nova (with Adam)

## 1) Purpose
Establish a concrete, testable definition of “works” **before** opening a public repository. This spec defines scope, interfaces, KPIs (key performance indicators), validation methods, and go/no‑go gates for the initial release (**v0.2 → v0.3**). No code in this packet—only structure, tests, and acceptance criteria.

## 2) Scope (v0.2 → v0.3)
- Cross‑hardware **Drive–Probe–Drive (DPD)** control framework
- Real‑time **sensing & interpretation** layer (hardware‑aware)
- **Demod** and lock‑in signal pipeline (deterministic, testable)
- **Adapt** layer using a Kalman‑type learner for online parameter updates
- **Scheduler** to coordinate timing and feedback cycles
- Cross‑OS baseline (Windows/macOS/Linux) with reproducible results
- Documentation: Quickstart + KPI guardrails

## 3) System sketch (conceptual)
```
┌────────────┐     probes     ┌───────────────┐
│ scheduler  ├───►(measure)──►│  demod/lock‑in│
└─────┬──────┘                └──────┬────────┘
      │ drive/probe                   │ features
      ▼                               ▼
┌────────────┐  params  ┌───────────────┐
│  hardware  ◄──────────┤   adapt (KF) │
│  (abstract)│  (update)└───────────────┘
└────────────┘
```
**Clocking loop:** drive₁ → probe → drive₂ → update(θ̂) → next cycle.

## 4) Formal DPD loop (minimal math)
- Plant (effective Hamiltonian) parameters: **θ = [Δ, g, φ, T₁, T₂, …]**.
- Measurement model: **yₖ = h(θₖ, uₖ) + εₖ**, with probe control **uₖ** and noise **εₖ**.
- Estimator (Kalman‑style): predict **θ̂ₖ|ₖ₋₁**, update with innovation **νₖ = yₖ − h(θ̂ₖ|ₖ₋₁, uₖ)**.
- Adaptation rule: **θ̂ₖ = θ̂ₖ|ₖ₋₁ + Kₖ νₖ**, with bounded gain **Kₖ** and stability guardrails.
- Scheduler enforces bounded latency **L_total ≤ 25 ms** for a full DPD cycle in simulation (baseline PC).

## 5) Module contracts (no code, testable interfaces)
### 5.1 scheduler
- **Inputs:** trial plan, timing budget, hardware profile
- **Outputs:** drive/probe timing events, cycle logs
- **Must:** enforce deterministic ordering; expose per‑cycle latency statistics

### 5.2 probes
- **Inputs:** hardware profile, probe plan
- **Outputs:** measurement records (time‑series yₖ), metadata (freq, phase, power)
- **Must:** support mid‑circuit and continuous‑time modes in simulation

### 5.3 demod
- **Inputs:** raw yₖ, reference tone(s)
- **Outputs:** I/Q features, SNR, phase/frequency estimates
- **Must:** pass SNR ≥ 20 dB on synthetic tones @ −10 dBFS with AWGN (σ chosen in test spec)

### 5.4 adapt
- **Inputs:** features, prior θ̂, covariance P
- **Outputs:** updated θ̂, P, and control suggestions Δu
- **Must:** converge within 200 cycles on the synthetic plant (see §6), RMSE ≤ target

### 5.5 hardware (abstract)
- **Inputs:** drive/probe sequences
- **Outputs:** simulated measurements (with configurable T₁/T₂, detunings, drift, jitter)
- **Must:** support multiple “profiles”: superconducting, trapped‑ion, neutral‑atom, photonic (parameter sets only; no vendor code)

## 6) Synthetic‑plant testbed (reference)
- Base oscillator with detuning **Δ₀ ∈ [−2π·2 MHz, +2π·2 MHz]**
- Coupling **g ∈ [0, 2π·5 MHz]**, decoherence **T₁/T₂ ∈ [1 μs, 100 μs]**
- Additive white Gaussian noise with **SNR sweep: 10 → 40 dB**
- Timing jitter ≤ 200 ns (configurable)
- Drift model: random walk on **Δ** with σ_Δ ≤ 2π·10 kHz per 100 cycles

**Acceptance:** Adaptation recovers **Δ, g** within ±2% (RMSE over last 100 cycles) across SNR ≥ 20 dB and jitter ≤ 200 ns.

## 7) KPIs & thresholds (v0.3 target)
- **Latency:** end‑to‑end DPD cycle ≤ 25 ms (baseline), demod ≤ 3 ms
- **Convergence:** parameters within ±2% in ≤ 200 cycles on reference plant
- **SNR handling:** maintain feature stability (std/mean ≤ 3%) at SNR ≥ 20 dB
- **Determinism:** jitter of scheduler timestamps ≤ 1 ms (software clock)
- **Cross‑OS reproducibility:** identical KPI pass/fail on Windows/macOS/Linux (simulated)

## 8) Tests (no code—definitions only)
1. **Unit: scheduler timing determinism** (1000 cycles; histogram & max jitter)
2. **Unit: demod fidelity** (pure tones + AWGN; recover amp/phase/freq within spec)
3. **Unit: adapt stability** (bounded gains; no divergence under noise & drift)
4. **Integration: closed‑loop DPD** (synthetic plant; KPI thresholds §7)
5. **Cross‑hardware profiles** (run the same suite with SC/Ion/NA/Photonic params)
6. **Cross‑OS parity** (three OS VMs/hosts; identical pass/fail)
7. **Docs check** (Quickstart + KPI guardrails visible, accurate, and consistent)

## 9) Go/No‑Go gates
- **Gate A (Design Freeze):** All module contracts finalized; synthetic‑plant spec locked.
- **Gate B (Sim KPI Pass):** All §7 KPIs pass on synthetic plant across four hardware profiles.
- **Gate C (Cross‑OS):** Same pass/fail across Windows/macOS/Linux.
- **Gate D (Docs):** Quickstart + KPI guardrails complete with screenshots/plots from tests.
**Only after D** do we create the public repository.

## 10) Risks & mitigations
- **Risk:** Demod instability at low SNR. **Mitigation:** reference‑tracking, robust estimators.
- **Risk:** Adapt divergence under drift. **Mitigation:** gain‑clipping, covariance inflation.
- **Risk:** OS‑dependent timers. **Mitigation:** monotonic clocks, explicit timing layer.
- **Risk:** Scope creep before v0.3. **Mitigation:** freeze interfaces, add stretch goals to v0.4.

## 11) Stretch goals (deferred to v0.4+)
- Streaming spectral estimator, multi‑tone probes, non‑Gaussian noise
- Online experiment‑design (active learning for probe selection)
- Hardware latency calibration (separate timing budget per profile)
- Optional DSP accelerations (NumPy/SciPy/CUDA), guarded by feature flags

---
**Decision:** We will not open a public repo until Gates A–D are green. This packet is the single source of truth for pre‑repo readiness.
