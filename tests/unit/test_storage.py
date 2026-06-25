"""Unit tests for storage backends."""

from __future__ import annotations

import pytest

from phoenix.infrastructure.storage import SQLiteStorageBackend, StorageBackend
from phoenix.models.output import ScrapingResult, UnifiedOutput
from phoenix.models.session import Session


@pytest.fixture
def storage() -> SQLiteStorageBackend:
    """Return an in-memory SQLite storage backend."""
    backend = SQLiteStorageBackend(path=":memory:")
    try:
        yield backend
    finally:
        backend.close()


def test_storage_backend_is_abstract() -> None:
    """``StorageBackend`` cannot be instantiated directly."""
    with pytest.raises(TypeError):
        StorageBackend()  # type: ignore[abstract]


def test_save_and_get_scrape_result(storage: SQLiteStorageBackend) -> None:
    """A saved scraping result can be retrieved by id."""
    output = UnifiedOutput(
        url="https://example.com/post/1",
        platform="generic",
        content_type="article",
        title="Hello",
        text="World",
    )
    result = ScrapingResult(success=True, url=output.url, output=output)

    result_id = storage.save_scrape_result(result)
    loaded = storage.get_scrape_result(result_id)

    assert loaded is not None
    assert loaded.success is True
    assert loaded.output is not None
    assert loaded.output.title == "Hello"


def test_list_scrape_results_by_platform(storage: SQLiteStorageBackend) -> None:
    """Results can be filtered by platform."""
    for platform, title in [("x_twitter", "Tweet"), ("generic", "Page")]:
        output = UnifiedOutput(
            url=f"https://example.com/{platform}",
            platform=platform,
            title=title,
        )
        storage.save_scrape_result(ScrapingResult(success=True, output=output))

    x_results = storage.list_scrape_results(platform="x_twitter")

    assert len(x_results) == 1
    assert x_results[0].output.platform == "x_twitter"


def test_save_and_get_archive(storage: SQLiteStorageBackend) -> None:
    """A saved archive can be retrieved by archive id."""
    archive_id = storage.save_archive(
        archive_id="abc123",
        url="https://example.com",
        raw_html="<html></html>",
        metadata={"status": 200},
    )

    loaded = storage.get_archive("abc123")

    assert loaded is not None
    assert loaded["archive_id"] == "abc123"
    assert loaded["raw_html"] == "<html></html>"
    assert loaded["metadata"]["status"] == 200
    assert archive_id is not None


def test_save_and_get_session(storage: SQLiteStorageBackend) -> None:
    """A saved session can be retrieved by platform."""
    session = Session(
        platform="x_twitter",
        cookies=[{"name": "auth", "value": "secret"}],
        is_valid=True,
    )

    storage.save_session(session)
    loaded = storage.get_session("x_twitter")

    assert loaded is not None
    assert loaded.platform == "x_twitter"
    assert loaded.cookies[0]["name"] == "auth"
    assert loaded.is_valid is True


def test_update_existing_session(storage: SQLiteStorageBackend) -> None:
    """Saving a session for an existing platform updates it."""
    storage.save_session(
        Session(platform="x_twitter", cookies=[{"name": "a", "value": "1"}]),
    )
    storage.save_session(
        Session(platform="x_twitter", cookies=[{"name": "b", "value": "2"}]),
    )

    sessions = storage.list_sessions()

    assert len(sessions) == 1
    assert sessions[0].cookies[0]["name"] == "b"


def test_save_and_get_domain_memory(storage: SQLiteStorageBackend) -> None:
    """Domain memory is persisted and retrieved by domain."""
    memory = {
        "strategy_memory": {"http": {"success": True}},
        "selector_memory": {"title": {"selectors": {"h1": {"match_rate": 1.0}}}},
        "aggregates": {"attempts": 5, "successes": 4},
    }

    storage.save_domain_memory("example.com", memory)
    loaded = storage.get_domain_memory("example.com")

    assert loaded is not None
    assert loaded["strategy_memory"]["http"]["success"] is True
    assert loaded["selector_memory"]["title"]["selectors"]["h1"]["match_rate"] == 1.0
    assert loaded["aggregates"]["successes"] == 4


def test_save_domain_memory_updates_existing(storage: SQLiteStorageBackend) -> None:
    """Saving domain memory for an existing domain updates it in place."""
    storage.save_domain_memory("example.com", {"aggregates": {"attempts": 1}})
    storage.save_domain_memory("example.com", {"aggregates": {"attempts": 2}})

    loaded = storage.get_domain_memory("example.com")

    assert loaded is not None
    assert loaded["aggregates"]["attempts"] == 2


def test_get_missing_domain_memory_returns_none(storage: SQLiteStorageBackend) -> None:
    """Fetching memory for an unknown domain returns None."""
    assert storage.get_domain_memory("unknown.test") is None


def test_save_and_get_baseline(storage: SQLiteStorageBackend) -> None:
    """A structural baseline is persisted and retrieved by URL."""
    baseline_id = storage.save_baseline(
        url="https://example.com/post/1",
        platform="generic",
        content_type="article",
        structural_fingerprint="abc123",
        selectors_snapshot={"title": {"selector": "h1", "matched": True}},
        critical_fields_hash="hash1",
        html_size_bytes=1234,
        archive_id="arch1",
    )

    loaded = storage.get_latest_baseline("https://example.com/post/1")

    assert loaded is not None
    assert loaded["id"] == baseline_id
    assert loaded["structural_fingerprint"] == "abc123"
    assert loaded["selectors_snapshot"]["title"]["matched"] is True
    assert loaded["html_size_bytes"] == 1234


def test_save_baseline_updates_existing(storage: SQLiteStorageBackend) -> None:
    """Saving a baseline for the same URL updates the existing row."""
    url = "https://example.com/post/1"
    storage.save_baseline(
        url=url,
        platform="generic",
        structural_fingerprint="old",
        selectors_snapshot={},
    )
    storage.save_baseline(
        url=url,
        platform="generic",
        structural_fingerprint="new",
        selectors_snapshot={},
    )

    loaded = storage.get_latest_baseline(url)

    assert loaded is not None
    assert loaded["structural_fingerprint"] == "new"


def test_save_alert(storage: SQLiteStorageBackend) -> None:
    """A change alert is persisted and retrievable fields are correct."""
    alert = {
        "url": "https://example.com/post/1",
        "platform": "generic",
        "content_type": "article",
        "alert_type": "structural_change",
        "severity": "warning",
        "details": {"old_fingerprint": "a", "new_fingerprint": "b"},
        "baseline_id": "baseline-1",
    }

    alert_id = storage.save_alert(alert)

    assert alert_id is not None
    assert isinstance(alert_id, str)
