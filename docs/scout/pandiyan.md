# Pandiyan LPBF Acoustic Dataset — Scout Memo

| | |
|---|---|
| Date | 2026-05-01 |
| Source | Zenodo `10.5281/zenodo.10473583` (`Domain adaptation.zip`, 2.3 GB) |
| On disk | `$TELEMETRY_DATA_ROOT/raw/pandiyan/` |
| Source paper | Pandiyan et al., *Additive Manufacturing* **80** (2024) 103974 — [DOI 10.1016/j.addma.2024.103974](https://doi.org/10.1016/j.addma.2024.103974) |
| Background paper | Pandiyan et al., *Procedia CIRP* **94** (2020) 392–397 — DOI 10.1016/j.procir.2020.09.152 |

## Purpose

Captures the actual shape, dtype, and label distribution of the dataset as
extracted on 2026-05-01, cross-checked against the source paper. Schema,
loader, and test work in subsequent commits calibrates against the values
reported here. Per ADR-004 this file is hand-written documentation, not
generated artifact — re-running the inspection is *not* part of the build.

## File inventory (observed on disk)

| File | Shape | dtype | Bytes |
| :--- | :--- | :--- | ---: |
| `D1_rawspace_5000.npy` | `(31095, 5000)` | `float64` | 1,243,800,128 |
| `D1_classspace_5000.npy` | `(31095,)` | `float64` | 248,888 |
| `D2_rawspace_5000.npy` | `(29192, 5000)` | `float64` | 1,167,680,128 |
| `D2_classspace_5000.npy` | `(29192,)` | `float64` | 233,664 |

Both `rawspace` arrays are C-contiguous → mmap reads are sequential and cache-friendly.

## Hardware and acquisition (from paper §2.1)

* LPBF machine: **SISMA MySint 100**, 1070 nm fiber laser, 200 W max, Gaussian spot 1/e² = 55 µm.
* AE sensor: **Avisoft Bioacoustics CM16/CMPA** — flat frequency response **0–150 kHz**, fixed at 45° facing the build plate.
* DAQ: **Advantech 1840** PCIe card, ±5 V dynamic range, **400 kHz sampling rate** (Nyquist = 200 kHz, comfortably above the sensor's 150 kHz upper bound).
* Trigger: photodiode at >0.5 V (laser irradiating powder); window starts when photodiode saturates at 5 V.
* Recording per scan track: optical signal sits at 5 V saturation for **12.5 ms** → exactly **5,000 samples** at 400 kHz per window.
* Offline preprocessing: low-pass **Butterworth filter at 150 kHz** applied per window before storage.

The 12.5 ms × 400 kHz → 5,000 samples derivation in the original handoff is
**confirmed**. (My earlier flag suggesting the sampling rate might be 1 MHz
based on the 2020 paper was wrong — that paper used different hardware on
a different study.)

## Verified label encoding (from paper Table 4)

Cross-reference of paper Table 4 ("Total number of AE windows ...") against
our scout class counts gives an unambiguous integer-to-regime mapping. Three
counts match exactly across non-corresponding cells; the encoding is pinned
with effectively zero residual ambiguity.

| Class | Encoding | Paper D1 count | Scout label `0`/`1`/`2` D1 | Paper D2 count | Scout label `0`/`1`/`2` D2 |
| :--- | :---: | ---: | ---: | ---: | ---: |
| Lack of Fusion (LoF) | **0** | 10,450 | 10,719 (label 0) | **9,875** | **9,875 (label 0) ✓** |
| Conduction mode | **1** | 9,576 | 10,294 (label 1) | **8,977** | **8,977 (label 1) ✓** |
| Keyhole pores | **2** | **10,082** | **10,082 (label 2) ✓** | 11,750 | 10,340 (label 2) |

The slight non-matching counts (D1 LoF/Conduction higher in the dataset
than the paper, D2 Keyhole lower) most likely reflect a re-cleaning or
train/test split between paper submission and Zenodo upload. The integer
encoding is invariant — `Label.LOF = 0`, `Label.CONDUCTION = 1`, `Label.KEYHOLE = 2`.

## Class distribution observed on disk

| Regime | label 0 (LoF) | label 1 (Conduction) | label 2 (Keyhole) | total |
| :--- | ---: | ---: | ---: | ---: |
| D1 | 10,719 (34.47 %) | 10,294 (33.11 %) | 10,082 (32.42 %) | 31,095 |
| D2 |  9,875 (33.83 %) |  8,977 (30.75 %) | 10,340 (35.42 %) | 29,192 |

D1 is well balanced. D2 modestly underrepresents Conduction.

## Normalization: empirical findings

The paper's §2.4 (Dataset preparation) describes only the offline 150 kHz
Butterworth filter and is silent on amplitude normalization. Our scout
data shows mean ≈ 0 across the dataset, so something happened — but
per-window statistics rule out per-window z-scoring.

Per-window stats from a sample of D1 rows:

| Row | mean | std | min | max |
| ---: | ---: | ---: | ---: | ---: |
| 0 | −0.0018 | 1.077 | −2.48 | +2.43 |
| 1 | −0.0078 | 1.085 | −2.53 | +2.66 |
| 2 | −0.0037 | 1.006 | −2.77 | +2.46 |
| 100 | −0.0065 | 0.973 | −2.49 | +2.45 |
| 15000 | −0.0071 | 1.190 | −2.60 | +2.49 |
| **30000** | **−0.0040** | **0.459** | **−2.13** | **+2.21** |

Per-window stds vary from ≈ 0.46 to ≈ 1.19 — **a per-window z-score would
force every std to exactly 1.0**. So the normalization is not per-window.
The most plausible interpretation: the data is mean-centered (perhaps
globally or per-regime) and stored in dimensionless engineering units
after the 150 kHz Butterworth. Per-window std variation is **real signal
energy** (e.g., row 30000's std 0.46 is a genuinely quieter window) and
must not be flattened by the loader.

## Surprises that change the design

### Dtype is `float64`, not `float32`

The handoff notes assumed `float32`. Reality: all four files are `float64`.

* Combined raw footprint is ~2.3 GB on disk and in RAM. Fits the t3.xlarge
  per ADR-001, but is double what the handoff budgeted.
* The agent loop should cast to `float32` at the loader boundary —
  halves FFT memory and compute. Casting later defeats mmap's zero-copy
  benefit; casting globally up-front defeats the point of mmap entirely.
* The "all telemetry arrays are `np.float32`" rule is a *loader-output*
  invariant, not an on-disk truth.

### Labels are stored as `float64`, not `int`

Class file dtype is `float64`; values are exactly {0.0, 1.0, 2.0}. The
loader will cast to a `Label` IntEnum at the boundary; the DB column will
be text per the agreed encoding decision (text in DB, IntEnum in Python).

## Sanity checks (passed)

* `rawspace.shape[1] == 5000` for both regimes (12.5 ms × 400 kHz).
* `rawspace.shape[0] == classspace.shape[0]` for both regimes (one label per window).
* No NaN or Inf in the first 1,000 sampled rows of either regime.
* Both `rawspace` arrays are C-contiguous.
* Class encoding inferred from data matches paper Table 4 (3 exact integer matches).

## Implications for the next commit (loader + tests)

1. `PandiyanRun.rawspace` is `np.load(path, mmap_mode='r')`. The loader
   yields rows cast to `float32` at row-fetch time — never globally.
2. `PandiyanRun.classspace` is loaded fully (≤ 250 KB) and cast to a
   `Label` IntEnum: `LOF = 0`, `CONDUCTION = 1`, `KEYHOLE = 2`.
3. `PandiyanRun` exposes named constants: `SAMPLE_RATE_HZ = 400_000`,
   `WINDOW_SAMPLES = 5_000`, `WINDOW_DURATION_S = 0.0125`,
   `HARDWARE_LOWPASS_HZ = 150_000`, `NYQUIST_HZ = 200_000`. One-line
   docstring per constant citing the AddMfg 2024 paper §2.1.
4. The loader does **not** renormalize. The data already lives in the
   amplitude regime the source paper used; per-window std variation is
   signal, not noise.
5. The loader does **not** recompute per-window stats at load time —
   the agent loop computes its own envelope/kurtosis on demand.
