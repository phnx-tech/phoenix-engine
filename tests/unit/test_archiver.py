"""Unit tests for the source archiver."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from phoenix.infrastructure.storage import SQLiteStorageBackend
from phoenix.processing.archiver import SourceArchiver

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def local_dir(tmp_path: Path) -> Path:
    """Return a temporary local archive directory."""
    return tmp_path / "archives"


def test_archive_generates_identifier(local_dir: Path) -> None:
    """Archiving returns a deterministic identifier."""
    archiver = SourceArchiver(local_dir=local_dir)

    archive_id = archiver.archive("https://example.com", "<html></html>")

    assert archive_id
    assert (local_dir / f"{archive_id}.html").exists()
    assert (local_dir / f"{archive_id}.json").exists()


def test_archive_with_storage_backend(local_dir: Path) -> None:
    """Archiving writes to a storage backend when provided."""
    storage = SQLiteStorageBackend(path=":memory:")
    try:
        archiver = SourceArchiver(storage=storage)
        archive_id = archiver.archive("https://example.com", "<html></html>")

        loaded = archiver.retrieve(archive_id)

        assert loaded is not None
        assert loaded["raw_html"] == "<html></html>"
        assert loaded["archive_id"] == archive_id
    finally:
        storage.close()


def test_retrieve_from_local_dir(local_dir: Path) -> None:
    """Archives can be retrieved from the local directory."""
    archiver = SourceArchiver(local_dir=local_dir)
    archive_id = archiver.archive("https://example.com", "<html>hi</html>")

    loaded = archiver.retrieve(archive_id)

    assert loaded is not None
    assert loaded["raw_html"] == "<html>hi</html>"


def test_retrieve_missing_archive_returns_none(local_dir: Path) -> None:
    """Retrieving a missing archive returns ``None``."""
    archiver = SourceArchiver(local_dir=local_dir)

    assert archiver.retrieve("missing") is None
