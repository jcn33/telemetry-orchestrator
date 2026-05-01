import pytest
from pydantic import ValidationError

from telemetry.manifest import ExtractedFile, Manifest


def test_manifest_round_trip():
    m = Manifest(
        dataset="pandiyan",
        zenodo_doi="10.5281/zenodo.10473583",
        zenodo_record_id="10473583",
        zenodo_archive="Domain adaptation.zip",
        zenodo_archive_md5="661cbc5637dc29346e3254e1b2f2311f",
        fetched_at="2026-05-01T00:00:00+00:00",
        extracted_files=[
            ExtractedFile(name="D1_rawspace_5000.npy", size_bytes=1_234_567_890),
            ExtractedFile(name="D1_classspace_5000.npy", size_bytes=254_873),
        ],
    )
    restored = Manifest.model_validate_json(m.model_dump_json())
    assert restored == m
    assert restored.extracted_files[0].name == "D1_rawspace_5000.npy"


def test_manifest_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        Manifest(dataset="pandiyan")  # type: ignore[call-arg]
