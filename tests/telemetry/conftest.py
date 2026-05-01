from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def synthetic_pandiyan(tmp_path: Path) -> Path:
    """Write a tiny synthetic Pandiyan-shaped dataset under tmp_path/raw/pandiyan/.

    Returns the dataset root (the parent of raw/), mirroring the production
    layout that PandiyanRun.from_data_root expects.
    """
    dataset_dir = tmp_path / "raw" / "pandiyan"
    dataset_dir.mkdir(parents=True)

    rng = np.random.default_rng(seed=42)
    rawspace = rng.standard_normal((10, 5000)).astype(np.float64)
    # 4 LoF, 3 Conduction, 3 Keyhole — exercises every label value
    labels = np.array([0, 0, 0, 0, 1, 1, 1, 2, 2, 2], dtype=np.float64)

    np.save(dataset_dir / "D1_rawspace_5000.npy", rawspace)
    np.save(dataset_dir / "D1_classspace_5000.npy", labels)

    return tmp_path
