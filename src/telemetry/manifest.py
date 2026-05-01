"""Pydantic schemas for dataset provenance manifests.

A manifest is written once after a successful fetch+extract and answers the
question: where did the data on disk come from? Consumed by downstream
indexers when populating Postgres metadata tables.
"""

from pydantic import BaseModel


class ExtractedFile(BaseModel):
    name: str
    size_bytes: int


class Manifest(BaseModel):
    dataset: str
    zenodo_doi: str
    zenodo_record_id: str
    zenodo_archive: str
    zenodo_archive_md5: str
    fetched_at: str
    extracted_files: list[ExtractedFile]
