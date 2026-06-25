"""Unit tests for the persistent domain memory store."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from phoenix.infrastructure.storage import SQLiteStorageBackend
from phoenix.models.output import UnifiedOutput
from phoenix.processing.domain_memory import DomainMemory, DomainMemoryEntry


@pytest.fixture
def storage() -> SQLiteStorageBackend:
    """Return an in-memory SQLite storage backend."""
    backend = SQLiteStorageBackend(path=":memory:")
    try:
        yield backend
    finally:
        backend.close()


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Return a temporary data directory for JSON fallback tests."""
    return tmp_path / "data"


def test_get_returns_empty_entry_when_missing(storage: SQLiteStorageBackend) -> None:
    """Fetching unknown domain memory returns an empty entry."""
    memory = DomainMemory(storage=storage)

    entry = memory.get("example.com")

    assert isinstance(entry, DomainMemoryEntry)
    assert entry.domain == "example.com"
    assert entry.strategy_memory == {}
    assert entry.selector_memory == {}


@pytest.mark.asyncio
async def test_record_success_persists_strategy_memory(storage: SQLiteStorageBackend) -> None:
    """A successful scrape records strategy success."""
    memory = DomainMemory(storage=storage)

    await memory.record_success(
        "https://example.com/post/1",
        "browser",
        {"selectors_used": ["h1"]},
        UnifiedOutput(url="https://example.com/post/1", platform="generic"),
    )

    entry = memory.get("example.com")
    assert entry.strategy_memory["browser"]["success"] is True
    assert entry.aggregates["successes"] == 1
    assert entry.aggregates["attempts"] == 1


@pytest.mark.asyncio
async def test_record_failure_persists_failure(storage: SQLiteStorageBackend) -> None:
    """A failed scrape records failure counters."""
    memory = DomainMemory(storage=storage)

    await memory.record_failure(
        "https://example.com/post/1",
        "http",
        {"code": "SCR_011"},
    )

    entry = memory.get("example.com")
    assert entry.aggregates["failures"] == 1
    assert entry.aggregates["attempts"] == 1
    assert entry.aggregates["last_error_code"] == "SCR_011"


@pytest.mark.asyncio
async def test_selector_memory_tracks_match_rate(storage: SQLiteStorageBackend) -> None:
    """Selector outcomes are tracked with match rate and best selector."""
    memory = DomainMemory(storage=storage)
    extracted = {
        "title": {
            "value": "Hello",
            "selector_used": "h1",
            "matched": True,
            "confidence": 0.95,
        },
    }

    await memory.record_success(
        "https://example.com/post/1",
        "http",
        extracted,
        UnifiedOutput(url="https://example.com/post/1", platform="generic"),
    )
    await memory.record_success(
        "https://example.com/post/2",
        "http",
        {"title": {"value": None, "selector_used": "h1", "matched": False}},
        UnifiedOutput(url="https://example.com/post/2", platform="generic"),
    )

    entry = memory.get("example.com")
    title_mem = entry.selector_memory["title"]
    assert title_mem["selectors"]["h1"]["attempts"] == 2
    assert title_mem["selectors"]["h1"]["successes"] == 1
    assert title_mem["selectors"]["h1"]["match_rate"] == 0.5
    assert title_mem["best_selector"] == "h1"


@pytest.mark.asyncio
async def test_json_fallback_persists_across_instances(tmp_data_dir: Path) -> None:
    """Without storage, memory is persisted to a JSON file."""
    memory1 = DomainMemory(data_dir=tmp_data_dir)
    await memory1.record_success(
        "https://example.com/post/1",
        "http",
        {"selectors_used": ["h1"]},
        UnifiedOutput(url="https://example.com/post/1", platform="generic"),
    )

    memory2 = DomainMemory(data_dir=tmp_data_dir)
    entry = memory2.get("example.com")

    assert entry.strategy_memory["http"]["success"] is True
    assert entry.aggregates["successes"] == 1


@pytest.mark.asyncio
async def test_json_fallback_isolation(tmp_data_dir: Path) -> None:
    """Different data directories do not share memory."""
    memory = DomainMemory(data_dir=tmp_data_dir)
    await memory.record_success(
        "https://example.com/post/1",
        "http",
        {},
        UnifiedOutput(url="https://example.com/post/1", platform="generic"),
    )

    other = DomainMemory(data_dir=tmp_data_dir / "other")
    assert other.get("example.com").aggregates.get("attempts", 0) == 0


def test_domain_strips_www() -> None:
    """The domain helper normalizes ``www.`` away."""
    memory = DomainMemory()
    assert memory._domain("https://www.example.com/path") == "example.com"
    assert memory._domain("https://example.com/path") == "example.com"
