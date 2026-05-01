---
id: "005"
title: Pandiyan Dataset Interpretation and Loader Design
status: Accepted
tags: [telemetry, pandiyan, signal-processing, storage]
last_updated: 2026-05-01
---

# ADR-005: Pandiyan Dataset Interpretation and Loader Design

## Context

The scout pass for the Pandiyan LPBF acoustic emissions dataset (`docs/scout/pandiyan.md`) produced empirical findings — actual shapes, dtypes, label distribution, normalization characteristics — and cross-validated them against the source paper (Pandiyan et al., *Additive Manufacturing* 80 (2024) 103974, [DOI 10.1016/j.addma.2024.103974](https://doi.org/10.1016/j.addma.2024.103974), open access).

Several interpretations need to be locked before the loader (`src/telemetry/pandiyan.py`) lands, because each one becomes a hardcoded constant or invariant. Without this ADR, future code reviews would have no traceable reason to accept `SAMPLE_RATE_HZ = 400_000` or `Label.LOF = 0` as correct.

## Decisions

### 1. Acquisition constants — hardcoded and paper-cited

| Constant | Value | Paper section |
| :--- | :--- | :--- |
| `SAMPLE_RATE_HZ` | 400_000 | §2.1 |
| `WINDOW_SAMPLES` | 5_000 | §2.4 |
| `WINDOW_DURATION_S` | 0.0125 | derived (`WINDOW_SAMPLES / SAMPLE_RATE_HZ`) |
| `HARDWARE_LOWPASS_HZ` | 150_000 | §2.1, §2.4 |
| `NYQUIST_HZ` | 200_000 | derived (`SAMPLE_RATE_HZ / 2`) |

These are not configurable — the data was captured at exactly these settings. Making them parameters would invite a downstream caller to mismatch reality and silently produce wrong filters.

### 2. Label encoding — IntEnum mirroring paper Table 4

```python
class Label(IntEnum):
    LOF = 0           # Lack of Fusion (too cold, unmelted-powder porosity)
    CONDUCTION = 1    # Optimal melt-pool dynamics
    KEYHOLE = 2       # Vapor-cavity collapse porosity (too hot)
```

The mapping is verified by cross-referencing paper Table 4 against the on-disk class counts: three integer counts (D2 LoF = 9 875, D2 Conduction = 8 977, D1 Keyhole = 10 082) match exactly. The probability of two random class-count distributions matching exactly in three cells across two regimes is effectively zero. See scout memo for the cross-table.

The DB column for `label` stores text (`'LOF'`, `'CONDUCTION'`, `'KEYHOLE'`) per the existing encoding decision (text in DB, IntEnum in Python — chosen for query ergonomics + fast in-loop comparisons).

### 3. Storage — mmap'd `.npy` + metadata in Postgres

Telemetry waveform bytes stay on disk in their original `.npy` form. The OS page cache + numpy's mmap give zero-copy, sequential reads on the C-contiguous arrays. Postgres stores only metadata: dataset, run, per-window label, and pointers back to the file. The same pattern applies to any future high-frequency-waveform dataset.

### 4. Dtype boundary — `float64` on disk, `float32` at row fetch

The published `.npy` files are `float64`. The loader exposes rows as `float32`:

```python
def __getitem__(self, i: int) -> tuple[np.ndarray, Label]:
    row = np.asarray(self._mmap[i], dtype=np.float32)  # 20 KB allocation
    return row, Label(int(self._labels[i]))
```

Critically: `np.asarray(self._mmap[i], dtype=np.float32)` allocates a **single 20 KB row**. Calling `self._mmap.astype(np.float32)` would materialize all 1.16 GB at float32 in memory and defeat mmap entirely. The cast happens per accessed row, never globally.

### 5. Loader does not renormalize

The paper's §2.4 documents only an offline 150 kHz Butterworth filter applied before storage. Empirically the data is mean-centered (≈ 0) but per-window standard deviations vary from 0.46 to 1.19 in our sample, ruling out per-window z-scoring. The variation is real signal energy — louder regimes (e.g., keyhole) have larger amplitudes than quieter ones, and downstream RMS/kurtosis features depend on it.

The loader passes the bytes through unchanged. The agent loop computes its own bandpass/envelope/kurtosis on demand. Both kurtosis and normalized PSD are scale-invariant, so the unknown amplitude unit does not affect correctness.

### 6. Window-count discrepancy — accept on-disk counts as ground truth

Paper Table 4 and Zenodo `.npy` files disagree on three of six cells (D1 LoF, D1 Conduction, D2 Keyhole). The most likely cause is a re-cleaning or train/eval split between paper submission and Zenodo upload. The encoding (decision 2) is invariant — it depends only on which windows are present, not on their counts. We treat the on-disk counts as authoritative since the on-disk data is what we will be operating on.

## Where we deviate from the paper

The paper feeds 12.5 ms windows into a CNN with internal `BatchNorm` and trains a classifier. We do **not** implement that pipeline. Instead, the agent loop applies deterministic bandpass + envelope + kurtogram analysis to find fault-frequency signatures.

This is a different downstream path on the same dataset — *not* a deviation in dataset interpretation. The acquisition constants, label encoding, and storage of the data itself remain identical to the paper's. No claim made by our agent loop conflicts with the paper's results.

## Options Considered

### Storage
- **mmap'd `.npy` + metadata in Postgres [ACCEPTED]:** zero-copy sequential reads, OS page cache wins on repeated access, no format conversion.
- **Parquet [REJECTED]:** list-of-float columns are awkward for fixed-width waveforms; AE noise compresses poorly so the file-size argument is weak; loses the numpy native fast path.
- **HDF5 [REJECTED]:** good format generally but no win over mmap'd `.npy` here, and adds a runtime dependency.
- **BYTEA in Postgres [REJECTED]:** every read pays driver round-trip overhead; throws away the binary format; would dominate the agent loop's per-iteration cost.

### Dtype boundary
- **Cast to `float32` at row fetch [ACCEPTED]:** halves working memory and FFT cost. AE has analog noise + ADC quantization that effectively limits precision well below float32's mantissa (24 bits), so no information is lost.
- **Keep `float64` throughout [REJECTED]:** doubles memory and FFT cost for no precision gain on this signal class.
- **Pre-cast to a parallel `float32` `.npy` on disk [REJECTED]:** doubles disk usage; the mmap'd-with-row-cast pattern gets the same runtime benefit without the duplicate file.

### Label encoding
- **`IntEnum` mirroring paper Table 4 [ACCEPTED]:** fast comparisons in the agent loop's hot path; readable at the boundary; type-checked.
- **Plain string labels in Python [REJECTED]:** slower equality checks; harder to use in numpy boolean masks.
- **Keep raw `float64` values from disk [REJECTED]:** loses semantic meaning; invites accidental float-equality bugs.

## Consequences

- The loader can hardcode `fs=400_000` and pass it directly to `scipy.signal.butter(..., fs=...)` without configuration. Downstream code never has to ask the dataset "what's your sample rate?" — the answer is fixed and ADR-traceable.
- The pattern set here (paper-cited constants, IntEnum labels, no boundary normalization, mmap'd `.npy` storage, `float32` row cast) becomes the template for any future high-frequency-waveform dataset we ingest. If a second dataset arrives, this ADR will likely be split into a dataset-agnostic storage-strategy ADR + a per-dataset interpretation ADR; until then it carries both.
- The paper's CNN-based classifier accuracies are **not** a baseline our agent must match. Comparing apples-to-apples would require running their `BatchNorm`-front-ended classifier, which is out of scope. Our deterministic-search agent solves a different problem (finding the optimal kurtogram band) on the same dataset.
- The window-count discrepancy is a known footgun for anyone trying to compare the dataset against paper figures one-to-one. The scout memo records the exact mismatch; this ADR pins the policy (trust on-disk counts).

## AI Coding Directives

- **DIRECTIVE:** Pandiyan acquisition constants are paper-verified and not configurable. The loader MUST expose them as named module-level constants citing AddMfg 2024 §2.1 / §2.4 in docstrings: `SAMPLE_RATE_HZ = 400_000`, `WINDOW_SAMPLES = 5_000`, `HARDWARE_LOWPASS_HZ = 150_000`. Derived constants (`WINDOW_DURATION_S`, `NYQUIST_HZ`) MUST be defined in terms of the primaries, not as separate magic numbers.
- **DIRECTIVE:** Pandiyan label values `0`/`1`/`2` map to `Label.LOF` / `Label.CONDUCTION` / `Label.KEYHOLE` per paper Table 4. Code MUST NOT introduce alternative mappings without a superseding ADR. The DB column for `label` stores the text name, not the integer.
- **DIRECTIVE:** Telemetry loaders MUST NOT renormalize stored waveforms. Per-window std variation carries real signal-energy information that downstream RMS / kurtosis / envelope features depend on.
- **DIRECTIVE:** Telemetry rawspace files MUST be opened with `np.load(path, mmap_mode='r')`. Casting to `np.float32` happens per accessed row via `np.asarray(arr[i], dtype=np.float32)`, never globally via `arr.astype(...)`.
- **DIRECTIVE:** Telemetry waveform bytes never enter Postgres. Postgres holds metadata + per-window labels (text) + file pointers only.
