# ML/AI Learning Journey — Plan

> Status: **decided** (2026-05-31). This is the working plan for a hands-on, project-driven
> journey through ML / statistics / signal processing, run *separately* from but feeding back
> into the telemetry-orchestrator.

---

## TL;DR

A **two-phase** journey run through a **shared, domain-general orchestration engine**:

1. **Phase 1 — Fundamentals on finance.** Prediction markets (Polymarket / Kalshi) + crypto/on-chain.
   Chosen for zero-friction free live data, a fast self-serve feedback loop, and because prediction
   markets are the best probability/calibration trainer available.
2. **Phase 2 — Depth on physics.** The additive-manufacturing (LPBF) digital thread / Pandiyan, for
   signal-processing + computer-vision depth and aerospace career capital.

A **hard, skill-based transition trigger** separates them so phase 2 actually happens.
**Finance data is never merged into the orchestrator's schema** — the *engine* generalizes, the
*fuel* (data + signal-processing layer) stays domain-specific.

---

## How we got here (the reasoning that survived)

The learning goal is not to finish a benchmark — it's to grow through the full spectrum (statistics →
time series → signal processing → deep learning → CV → system design) on a dataset that feels like a
*living system*, and ideally to build toward novel, widely-applicable value.

Key conclusions from the deliberation (see `deep-research-prompt.md` / `deep-research-report.md`):

- **Pandiyan LPBF acoustic is a deep but narrow dataset** — single modality, no temporal degradation,
  no images. A great *signal-processing course*, a weak *full-spectrum* learning vehicle. It is best
  **reserved as the telemetry-orchestrator's dataset**, not burned as a tutorial.
- **The moat is the data asset, not the model.** Novel individual value comes from *assembling /
  simulating / linking* data nobody else has — not from a better model on a picked-over dataset.
- **Finance is the best domain for a *self-serve feedback loop*** (deploy solo, get a P&L daily with no
  gatekeeper) and the **worst for *novel/widespread value*** (adversarial, zero-sum, capital-beats-
  ingenuity, edges decay). So it earns its place as a **fundamentals on-ramp**, not the destination.
- **The fundamentals are domain-agnostic**, so starting on low-friction finance data is cheap — *if*
  the destination is a real commitment rather than a someday.

---

## Phase 1 — Fundamentals (finance / prediction markets)

**Why this domain for phase 1**

- Zero setup friction: free, live, abundant data; no 50 GB Zenodo download or EC2 overhead.
- Fast feedback keeps early-stage momentum high.
- **Lean prediction markets + crypto/on-chain — NOT equities/crypto day-trading.** Prediction markets
  are the ideal probability/calibration teacher (Brier score, calibration curves, Bayesian updating,
  Kelly sizing) and are inefficient enough that individual *modeling ingenuity* still has leverage.
  Equities day-trading mostly teaches that models barely beat baseline — a real but demoralizing
  phase-1 lesson.

**What to learn here (domain-agnostic base)**

- Descriptive statistics, probability, distributions, variance/covariance, correlation.
- Linear & logistic regression, regularization, maximum likelihood, cross-entropy.
- Trees, random forests, gradient boosting.
- Cross-validation, the bias-variance tradeoff, calibration, uncertainty.
- Baseline time-series: rolling features, autocorrelation, lagged variables, change-point/anomaly,
  forecasting fundamentals.
- Honest evaluation: backtesting, multiple-testing, non-stationarity, overfitting humility.

**Caution carried forward**

- Finance deploys your *losses* as efficiently as your gains. "Steady profit" is the rare outcome,
  not the expected one. Treat any P&L as tuition, and treat the *learning* as the deliverable.

---

## Transition trigger (do not skip)

The dominant failure mode of "start easy, evolve later" plans is **never evolving** — the on-ramp
becomes the whole journey, or the P&L loop hooks you. Mitigate with a **skill milestone, not a date**:

> **Move to Phase 2 when I can, from scratch:**
> 1. build a properly cross-validated, **calibrated** classifier and explain *why* it works, and
> 2. build a **baseline time-series forecaster** and explain its assumptions and failure modes.

When both are true, the generic base is in place and the physics depth phase begins.

---

## Phase 2 — Depth (physics / additive-manufacturing digital thread)

**Goal**: build the signal-processing + computer-vision depth that finance can't teach, in a defensible
physical-tech domain that compounds into aerospace/manufacturing career capital.

**The asset to assemble** (the moat — link sources nobody has linked publicly):

- Pandiyan **400 kHz acoustic** windows (already loaded; reserved for the orchestrator).
- ORNL **Peregrine** layerwise powder-bed images (computer vision, segmentation).
- NIST **melt-pool monitoring** + process parameters (time series, process-to-defect).
- **Physics-simulated** melt-pool / thermal ground truth (Rosenthal, Eagar–Tsai, FE thermal models) —
  this is how you *generate new signals* and validate your pipeline against known truth.

**What to learn here**

- DSP: FFT/STFT, filtering, wavelets, spectral & cepstral features, envelope analysis.
- Deep learning on signals (1D-CNN on waveforms, spectrogram → 2D-CNN) and on images (CNNs, ViTs,
  segmentation).
- Multimodal fusion (signals + images + process params), representation learning, anomaly detection.
- Uncertainty-aware prediction, surrogate modeling, process optimization.

**Alternative considered**: materials discovery (Materials Project + DFT simulation + OpenAlex/patent
linkage) — the bolder, novelty-maximizing cousin; heavier on compute, lighter on signal-processing.

---

## Engine vs. fuel — how both connect to the telemetry-orchestrator

**Do not merge finance data into the orchestrator's schema.** It would dilute the aerospace portfolio
identity into a generic time-series tool. Instead, separate the engine from the fuel:

| Layer | Domain-general? | Role |
|---|---|---|
| Orchestration machinery — LangGraph agent loop, HITL review UI, anomaly pipeline, Qdrant retrieval, Claude diagnosis | **Yes** | The reusable *engine*. Can be pointed at either domain. |
| Signal-processing + data layer — loaders, schema, physics constants | No | Domain-specific *fuel*. |

So "build both into it ultimately" = **the engine generalizes; the data stays separate.** Skills and
patterns flow back into the orchestrator; rows do not. Pandiyan stays reserved as the physics fuel.

---

## Logistics

- Work **locally** (off the EC2) during the learning journey to avoid its overhead.
- Phase-1 sandbox lives separately from the orchestrator repo (or in a clearly isolated subtree) so the
  aerospace artifact stays clean.

## Open / next

- Draft a concrete **first-90-days plan** for the Phase 1 prediction-markets work (offered, not yet
  produced).
