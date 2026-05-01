"""Loader for the Pandiyan LPBF acoustic emissions dataset.

See `docs/scout/pandiyan.md` for the empirical scout against the on-disk data,
and ADR-005 for the interpretation decisions encoded here. All paper section
references are to:

    Pandiyan et al., "Monitoring of Laser Powder Bed Fusion process by bridging
    dissimilar process maps using deep learning-based domain adaptation on
    acoustic emissions," Additive Manufacturing 80 (2024) 103974.
"""

from collections.abc import Iterable, Iterator
from enum import IntEnum
from pathlib import Path

import numpy as np

# Acquisition constants. Paper-verified, not configurable.
# §2.1: Advantech 1840 DAQ sampling the Avisoft CM16/CMPA AE sensor at 400 kHz.
SAMPLE_RATE_HZ: int = 400_000
# §2.4: each window covers 12.5 ms of laser irradiation = 5,000 samples at 400 kHz.
WINDOW_SAMPLES: int = 5_000
# §2.1 / §2.4: AE sensor's flat band ends at 150 kHz; offline Butterworth lowpass
# at 150 kHz applied before storage.
HARDWARE_LOWPASS_HZ: int = 150_000

# Derived constants — defined in terms of the primaries to avoid magic numbers.
WINDOW_DURATION_S: float = WINDOW_SAMPLES / SAMPLE_RATE_HZ
NYQUIST_HZ: int = SAMPLE_RATE_HZ // 2


class Label(IntEnum):
    """Process regime labels per AddMfg 2024 Table 4 (cross-validated in scout memo)."""

    LOF = 0
    CONDUCTION = 1
    KEYHOLE = 2


class PandiyanRun:
    """Memory-mapped view of one regime's (rawspace, classspace) pair.

    Rows are returned as `float32` cast lazily at access time. The underlying
    rawspace stays as a `float64` mmap on disk; we never materialize the full
    array in RAM (per ADR-005).
    """

    def __init__(self, rawspace_path: Path, classspace_path: Path) -> None:
        rawspace = np.load(rawspace_path, mmap_mode="r")
        if rawspace.ndim != 2 or rawspace.shape[1] != WINDOW_SAMPLES:
            raise ValueError(
                f"rawspace shape {rawspace.shape} does not match expected "
                f"(N, {WINDOW_SAMPLES}); see ADR-005."
            )
        classspace = np.load(classspace_path)
        if classspace.shape != (rawspace.shape[0],):
            raise ValueError(
                f"classspace shape {classspace.shape} does not match "
                f"rawspace row count {rawspace.shape[0]}."
            )
        self._rawspace = rawspace
        self._labels = classspace.astype(np.int64, copy=False)
        self.rawspace_path = rawspace_path
        self.classspace_path = classspace_path

    @classmethod
    def from_data_root(cls, root: Path, regime: str) -> "PandiyanRun":
        """Open a regime by name (e.g. 'D1', 'D2') from `<root>/raw/pandiyan/`."""
        dataset_dir = root / "raw" / "pandiyan"
        return cls(
            rawspace_path=dataset_dir / f"{regime}_rawspace_5000.npy",
            classspace_path=dataset_dir / f"{regime}_classspace_5000.npy",
        )

    def __len__(self) -> int:
        return int(self._rawspace.shape[0])

    def __getitem__(self, i: int) -> tuple[np.ndarray, Label]:
        row = np.asarray(self._rawspace[i], dtype=np.float32)
        return row, Label(int(self._labels[i]))

    def iter_windows(
        self, indices: Iterable[int] | None = None
    ) -> Iterator[tuple[np.ndarray, Label]]:
        if indices is None:
            indices = range(len(self))
        for i in indices:
            yield self[i]

    def sample(
        self, label: Label, n: int, rng: np.random.Generator
    ) -> np.ndarray:
        """Return `n` random windows of the given label as `(n, WINDOW_SAMPLES)` float32."""
        candidates = np.flatnonzero(self._labels == int(label))
        if len(candidates) < n:
            raise ValueError(
                f"requested {n} windows of label {label.name} "
                f"but only {len(candidates)} available"
            )
        chosen = rng.choice(candidates, size=n, replace=False)
        return np.asarray(self._rawspace[chosen], dtype=np.float32)
