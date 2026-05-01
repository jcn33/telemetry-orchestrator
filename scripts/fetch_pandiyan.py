"""Fetch the Pandiyan LPBF acoustic emissions dataset from Zenodo.

Downloads `Domain adaptation.zip` (~2.3 GB) from record 10473583, MD5-verifies
it against Zenodo's reported checksum, and extracts the four .npy files
(D1/D2 rawspace + classspace) into $TELEMETRY_DATA_ROOT/raw/pandiyan/.

Run on the EC2 host: python scripts/fetch_pandiyan.py
"""

import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from telemetry.manifest import ExtractedFile, Manifest

ZENODO_DOI = "10.5281/zenodo.10473583"
ZENODO_RECORD_ID = "10473583"
ZENODO_ARCHIVE_NAME = "Domain adaptation.zip"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"
ZENODO_ARCHIVE_URL = (
    f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files/"
    f"{urllib.parse.quote(ZENODO_ARCHIVE_NAME)}/content"
)

DATASET_NAME = "pandiyan"
HASH_CHUNK_BYTES = 1 << 20
SOCKET_TIMEOUT_S = 300


def get_data_root() -> Path:
    root = os.environ.get("TELEMETRY_DATA_ROOT")
    if not root:
        sys.exit(
            "TELEMETRY_DATA_ROOT is not set.\n"
            "  export TELEMETRY_DATA_ROOT=/home/ubuntu/telemetry-data\n"
            "  or: set -a; source .env; set +a"
        )
    return Path(root)


def fetch_archive_md5(api_url: str) -> str:
    with urllib.request.urlopen(api_url, timeout=SOCKET_TIMEOUT_S) as resp:
        record = json.load(resp)
    for f in record["files"]:
        if f["key"] == ZENODO_ARCHIVE_NAME:
            algo, _, hex_value = f["checksum"].partition(":")
            if algo != "md5":
                sys.exit(f"Unexpected checksum algorithm from Zenodo: {algo}")
            return hex_value
    sys.exit(f"'{ZENODO_ARCHIVE_NAME}' not found in record {ZENODO_RECORD_ID}.")


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while chunk := f.read(HASH_CHUNK_BYTES):
            h.update(chunk)
    return h.hexdigest()


def download_with_progress(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=SOCKET_TIMEOUT_S) as resp:
        total = int(resp.headers.get("Content-Length", "0"))
        downloaded = 0
        with dest.open("wb") as out:
            while chunk := resp.read(HASH_CHUNK_BYTES):
                out.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 / total
                    print(
                        f"\r  {downloaded / 1024 / 1024:>7.1f} / "
                        f"{total / 1024 / 1024:>7.1f} MB ({pct:5.1f}%)",
                        end="",
                        flush=True,
                    )
    print()


def extract_npy_files(zip_path: Path, dest_dir: Path) -> list[ExtractedFile]:
    extracted: list[ExtractedFile] = []
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".npy"):
                continue
            flat_name = Path(member).name
            target = dest_dir / flat_name
            if target.exists():
                print(f"  {flat_name}: already extracted, skipping")
            else:
                print(f"  {flat_name}: extracting...")
                with zf.open(member) as src, target.open("wb") as dst:
                    while chunk := src.read(HASH_CHUNK_BYTES):
                        dst.write(chunk)
            extracted.append(ExtractedFile(name=flat_name, size_bytes=target.stat().st_size))
    return extracted


def main() -> None:
    data_root = get_data_root()
    dataset_dir = data_root / "raw" / DATASET_NAME
    dataset_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dataset_dir / ZENODO_ARCHIVE_NAME

    print(f"Fetching Zenodo metadata for {ZENODO_DOI}...")
    expected_md5 = fetch_archive_md5(ZENODO_API_URL)
    print(f"  expected MD5: {expected_md5}")

    if zip_path.exists() and md5_file(zip_path) == expected_md5:
        print(f"Zip already verified at {zip_path}, skipping download")
    else:
        print(f"Downloading {ZENODO_ARCHIVE_NAME}...")
        download_with_progress(ZENODO_ARCHIVE_URL, zip_path)
        print("Verifying MD5...")
        actual_md5 = md5_file(zip_path)
        if actual_md5 != expected_md5:
            zip_path.unlink()
            sys.exit(f"MD5 mismatch: got {actual_md5}, expected {expected_md5}. Re-run.")
        print("  MD5 OK")

    print(f"Extracting .npy files to {dataset_dir}...")
    extracted = extract_npy_files(zip_path, dataset_dir)
    if not extracted:
        sys.exit("No .npy files found in the archive.")

    manifest = Manifest(
        dataset=DATASET_NAME,
        zenodo_doi=ZENODO_DOI,
        zenodo_record_id=ZENODO_RECORD_ID,
        zenodo_archive=ZENODO_ARCHIVE_NAME,
        zenodo_archive_md5=expected_md5,
        fetched_at=datetime.now(UTC).isoformat(),
        extracted_files=sorted(extracted, key=lambda f: f.name),
    )
    manifest_path = dataset_dir / "MANIFEST.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2) + "\n")
    print(f"\nWrote {manifest_path}")
    for f in manifest.extracted_files:
        print(f"  - {f.name}  ({f.size_bytes / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
