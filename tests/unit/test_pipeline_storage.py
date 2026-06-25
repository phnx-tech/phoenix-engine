"""Unit tests for pipeline integration with storage and archiving."""

from __future__ import annotations

import pytest

from phoenix.collectors.base import StubCollector
from phoenix.engine import PhoenixEngine
from phoenix.infrastructure.storage import SQLiteStorageBackend
from phoenix.processing.archiver import SourceArchiver


@pytest.mark.asyncio
async def test_pipeline_persists_result_and_archive() -> None:
    """Successful scrapes are persisted to storage and archived."""
    storage = SQLiteStorageBackend(path=":memory:")
    try:
        engine = PhoenixEngine(
            storage=storage,
            archiver=SourceArchiver(storage=storage),
            collectors={
                "http": StubCollector(
                    strategy="http",
                    html="<html><body><h1>Title</h1><p>Text</p></body></html>",
                ),
                "browser": StubCollector(strategy="browser", html=""),
            },
        )

        result = await engine.scrape("https://example.com/article/1")

        assert result.success is True
        assert result.output.archive_id is not None
        archived = storage.get_archive(result.output.archive_id)
        assert archived is not None
        assert "<html>" in archived["raw_html"]

        results = storage.list_scrape_results(platform="generic")
        assert len(results) == 1
        assert "Title" in str(results[0].output.text)
    finally:
        storage.close()
