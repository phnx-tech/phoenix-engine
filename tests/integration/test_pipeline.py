"""Integration tests for the Phoenix Engine pipeline."""

from __future__ import annotations

import pytest

from phoenix import PhoenixEngine
from phoenix.models.output import UnifiedOutput

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_pipeline_default_collector_returns_unified_output() -> None:
    """Full pipeline returns a successful CollectionResult with UnifiedOutput."""
    async with PhoenixEngine() as engine:
        result = await engine.scrape("https://example.com/article/123")

    assert result.url == "https://example.com/article/123"
    assert result.success is True
    assert result.output is not None
    assert isinstance(result.output, UnifiedOutput)
    assert result.output.platform == "generic"


@pytest.mark.asyncio
async def test_pipeline_strategy_override() -> None:
    """Pipeline respects a user-supplied strategy override."""
    async with PhoenixEngine() as engine:
        result = await engine.scrape(
            "https://instagram.com/p/ABC123",
            strategy="http",
            archive=False,
        )

    assert result.success is True
    assert result.output is not None
    assert result.output.scraping_strategy == "http"
