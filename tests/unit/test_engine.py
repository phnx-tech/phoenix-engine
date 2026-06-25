"""Unit tests for the Phoenix Engine public API."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from phoenix import PhoenixEngine
from phoenix.collectors.base import StubCollector
from phoenix.exceptions import LicenseMissingError
from phoenix.models import Config
from phoenix.models.output import CollectionResult, ScrapingResult, UnifiedOutput
from phoenix.processing.ai_assistant import AIAssistant

pytestmark = pytest.mark.unit

URL = "https://example.com/post/123"


@pytest.mark.asyncio
async def test_engine_scrape_returns_unified_output() -> None:
    """Scrape returns a successful ScrapingResult with UnifiedOutput."""
    engine = PhoenixEngine(collectors={"http": StubCollector(strategy="http")})
    result = await engine.scrape(URL)

    assert isinstance(result, ScrapingResult)
    assert result.success is True
    assert result.url == URL
    assert result.output is not None
    assert isinstance(result.output, UnifiedOutput)
    assert result.output.platform == "generic"


@pytest.mark.asyncio
async def test_engine_collect_alias_matches_scrape() -> None:
    """``collect`` is an alias for ``scrape``."""
    engine = PhoenixEngine(collectors={"http": StubCollector(strategy="http")})
    result = await engine.collect(URL)

    assert result.success is True
    assert result.output is not None


@pytest.mark.asyncio
async def test_engine_scrape_batch() -> None:
    """Batch scraping returns one result per URL in order."""
    urls = ["https://a.example.com/1", "https://b.example.com/2"]
    engine = PhoenixEngine(collectors={"http": StubCollector(strategy="http")})
    results = await engine.scrape_batch(urls)

    assert len(results) == 2
    for url, result in zip(urls, results, strict=True):
        assert result.success is True
        assert result.url == url


@pytest.mark.asyncio
async def test_engine_collect_batch_alias_matches_scrape_batch() -> None:
    """``collect_batch`` is an alias for ``scrape_batch``."""
    urls = ["https://a.example.com/1", "https://b.example.com/2"]
    engine = PhoenixEngine(collectors={"http": StubCollector(strategy="http")})
    results = await engine.collect_batch(urls)

    assert len(results) == 2
    assert all(result.success for result in results)


@pytest.mark.asyncio
async def test_engine_scrape_batch_empty_urls_raises() -> None:
    """``scrape_batch`` rejects an empty URL list."""
    engine = PhoenixEngine()
    with pytest.raises(ValueError, match="urls must not be empty"):
        await engine.scrape_batch([])


@pytest.mark.asyncio
async def test_engine_async_context_manager() -> None:
    """The engine supports async context manager usage."""
    async with PhoenixEngine() as engine:
        assert engine.version == "0.1.0"


def test_engine_builds_ai_assistant_when_enabled() -> None:
    """Engine wires an AIAssistant when ai_enabled is True."""
    config = Config(ai_enabled=True)
    engine = PhoenixEngine(config=config, collectors={"http": StubCollector(strategy="http")})

    assert engine.ai_assistant is not None
    assert isinstance(engine.ai_assistant, AIAssistant)


def test_engine_no_ai_assistant_when_disabled() -> None:
    """Engine does not create an AIAssistant when ai_enabled is False."""
    engine = PhoenixEngine(collectors={"http": StubCollector(strategy="http")})

    assert engine.ai_assistant is None


def test_collection_result_alias() -> None:
    """CollectionResult remains a backward-compatible alias."""
    assert CollectionResult is ScrapingResult


def test_engine_enforces_license_when_enabled(tmp_path: Path) -> None:
    """Engine creation fails when license enforcement is enabled but no key is set."""
    config = Config(
        data_dir=str(tmp_path),
        license_enforcement_enabled=True,
        license_secret="secret",  # noqa: S106
    )
    with pytest.raises(LicenseMissingError):
        PhoenixEngine(config=config)


def test_engine_accepts_valid_license(tmp_path: Path) -> None:
    """Engine creation succeeds with a valid license key."""
    from phoenix.infrastructure.license_manager import LicenseManager

    secret = "test-secret"  # noqa: S105
    manager = LicenseManager(
        secret=secret,
        license_key=None,
        state_path=tmp_path / "license_state.json",
    )
    key = manager.generate_key(max_uses=10)

    config = Config(
        data_dir=str(tmp_path),
        license_key=key,
        license_secret=secret,
        license_enforcement_enabled=True,
    )
    engine = PhoenixEngine(config=config)
    assert engine._license_manager is not None
