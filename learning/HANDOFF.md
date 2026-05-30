# Handoff — EC2 → Local (Learning Pivot)

**Date:** 2026-05-30
**Reason:** Stepping back from active telemetry-orchestrator build to learn ML/AI/stats
fundamentals through experience. Moving off the remote EC2 to local to cut cost until
GPU/compute power is actually needed.

---

## Decision: dataset for the learning journey

**Verdict — pivot away from LPBF as the *starting* dataset.** Not because it's bad, but
because it's the wrong *altitude* to begin at, and it doesn't naturally feed the
telemetry-orchestrator either.

### Why not LPBF (laser powder-bed fusion) first
- Vision-first (powder-bed images, optical tomography, melt-pool monitoring) → pushes
  CNNs/segmentation before stats & classical-ML foundations are in place.
- Spatial, not temporal → weak time-series curriculum.
- Gated by a hard data-engineering problem (in-situ ↔ ex-situ XCT registration).
- Melt-pool physics is a deep, non-transferable rabbit hole.
- First "stuck" moments are plumbing/CV/physics, not ML fundamentals.

### Chosen learning vehicle: aerospace digital-twin stack + one vibration dataset
- **CMAPSS → N-CMAPSS** (NASA turbofan run-to-failure). Climbs the curriculum in order:
  stats → imputation → linear/tree baselines → window features → sequence models →
  regimes → uncertainty → fault diagnostics.
- **+ one industrial-vibration/acoustic dataset** (Paderborn bearings or Hitachi MIMII)
  as the signal-processing module → FFT/PSD/STFT/wavelets/spectral features. This is the
  exact math the orchestrator is built around (`src/signal_processing/`).
- Bonus: every skill transfers directly into telemetry-orchestrator (aerospace,
  high-frequency telemetry, anomaly detection).

### Where LPBF actually belongs
- A **later standalone capstone** for computer vision + multimodal fusion — once
  fundamentals are real. It is *not* a feed for telemetry-orchestrator (wrong
  modality/domain: 2-D manufacturing imagery vs. 1-D high-frequency telemetry).

### Suggested ladder
1. CMAPSS — fundamentals (EDA, baselines, RUL regression, validation, calibration)
2. + Paderborn bearings / MIMII — signal processing (FFT/PSD/wavelets, anomaly detection)
3. N-CMAPSS — sequence models, regimes, fault classes, uncertainty
4. + FAA SDR / NTSB / weather text — multimodal retrieval + "explain & diagnose"
5. LPBF (capstone) — pure CV + multimodal fusion, its own project

Full reasoning + ranked alternatives: `learning/deep-research-report.md`
Original research brief: `learning/deep-research-prompt.md`

---

## Repo state at handoff
- Branch `setup` is fully pushed to `origin/setup` — all infra work is on GitHub.
- `main` is still at "Initial commit" (behind `setup`).
- Only untracked content of value: this `learning/` folder.
- `.DS_Store` / `src/.DS_Store` = junk (no real source in `src/`); should be gitignored.

## On local, after pulling
1. `git fetch && git checkout setup && git pull` (or pull whatever branch the learning
   files land on).
2. Confirm `learning/` is present with all three files.
3. Pick up at: **week-by-week CMAPSS Module 1 plan** (not yet written).

## EC2 teardown reminder
- Stop (or terminate) the `t3.xlarge` in `us-west-2` to stop incurring cost.
- `stop` preserves the EBS volume (small ongoing storage cost, fast restart).
- `terminate` is cheapest but destroys the instance — everything needed is already in
  git, so terminate is safe if you don't want the bootstrap state. See
  `project_ec2_state` memory for instance details.

## Next action
Write the week-by-week CMAPSS Module 1 plan — each step designed around the specific
fundamental it should make you "get stuck" on.
