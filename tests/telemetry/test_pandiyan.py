import numpy as np
import pytest

from telemetry.pandiyan import (
    HARDWARE_LOWPASS_HZ,
    NYQUIST_HZ,
    SAMPLE_RATE_HZ,
    WINDOW_DURATION_S,
    WINDOW_SAMPLES,
    Label,
    PandiyanRun,
)


def test_constants_match_paper():
    assert SAMPLE_RATE_HZ == 400_000
    assert WINDOW_SAMPLES == 5_000
    assert HARDWARE_LOWPASS_HZ == 150_000
    assert WINDOW_DURATION_S == 0.0125
    assert NYQUIST_HZ == 200_000


def test_label_enum_values():
    assert Label.LOF == 0
    assert Label.CONDUCTION == 1
    assert Label.KEYHOLE == 2


def test_load_from_data_root(synthetic_pandiyan):
    run = PandiyanRun.from_data_root(synthetic_pandiyan, "D1")
    assert len(run) == 10


def test_getitem_returns_float32_row(synthetic_pandiyan):
    run = PandiyanRun.from_data_root(synthetic_pandiyan, "D1")
    row, label = run[0]
    assert row.dtype == np.float32
    assert row.shape == (WINDOW_SAMPLES,)
    assert label == Label.LOF


def test_getitem_label_progression(synthetic_pandiyan):
    run = PandiyanRun.from_data_root(synthetic_pandiyan, "D1")
    expected = [Label.LOF] * 4 + [Label.CONDUCTION] * 3 + [Label.KEYHOLE] * 3
    actual = [run[i][1] for i in range(len(run))]
    assert actual == expected


def test_iter_windows_default_full_range(synthetic_pandiyan):
    run = PandiyanRun.from_data_root(synthetic_pandiyan, "D1")
    rows = list(run.iter_windows())
    assert len(rows) == 10
    assert all(r.dtype == np.float32 for r, _ in rows)


def test_iter_windows_with_indices(synthetic_pandiyan):
    run = PandiyanRun.from_data_root(synthetic_pandiyan, "D1")
    selected = list(run.iter_windows(indices=[0, 5, 9]))
    labels = [lbl for _, lbl in selected]
    assert labels == [Label.LOF, Label.CONDUCTION, Label.KEYHOLE]


def test_sample_by_label(synthetic_pandiyan):
    run = PandiyanRun.from_data_root(synthetic_pandiyan, "D1")
    rng = np.random.default_rng(seed=0)
    sampled = run.sample(Label.LOF, n=3, rng=rng)
    assert sampled.shape == (3, WINDOW_SAMPLES)
    assert sampled.dtype == np.float32


def test_sample_raises_when_insufficient(synthetic_pandiyan):
    run = PandiyanRun.from_data_root(synthetic_pandiyan, "D1")
    rng = np.random.default_rng()
    with pytest.raises(ValueError, match="requested 100 windows of label LOF"):
        run.sample(Label.LOF, n=100, rng=rng)


def test_loader_rejects_wrong_window_size(tmp_path):
    dataset_dir = tmp_path / "raw" / "pandiyan"
    dataset_dir.mkdir(parents=True)
    np.save(dataset_dir / "D1_rawspace_5000.npy", np.zeros((5, 1000), dtype=np.float64))
    np.save(dataset_dir / "D1_classspace_5000.npy", np.zeros(5, dtype=np.float64))

    with pytest.raises(ValueError, match="rawspace shape"):
        PandiyanRun.from_data_root(tmp_path, "D1")


def test_loader_rejects_mismatched_row_counts(tmp_path):
    dataset_dir = tmp_path / "raw" / "pandiyan"
    dataset_dir.mkdir(parents=True)
    np.save(dataset_dir / "D1_rawspace_5000.npy", np.zeros((5, 5000), dtype=np.float64))
    np.save(dataset_dir / "D1_classspace_5000.npy", np.zeros(7, dtype=np.float64))

    with pytest.raises(ValueError, match="classspace shape"):
        PandiyanRun.from_data_root(tmp_path, "D1")
