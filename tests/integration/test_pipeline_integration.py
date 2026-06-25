"""Integration tests for the Phoenix Engine collection pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

from phoenix import PhoenixEngine
from phoenix.collectors.base import StubCollector
from phoenix.models.output import UnifiedOutput

pytestmark = pytest.mark.integration


_PLATFORM_FIXTURE_URLS = [
    ("instagram", "https://www.instagram.com/p/C0aBcDeFgHi/"),
    ("x", "https://x.com/TechObserver/status/1234567890"),
    ("tiktok", "https://www.tiktok.com/@chefmaria/video/1234567890123456789"),
    ("linkedin", "https://www.linkedin.com/posts/alexchen_activity-123"),
    ("facebook", "https://www.facebook.com/GreenCityGardens/posts/112233"),
    ("youtube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("generic", "https://example.com/article/123"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(("platform", "url"), _PLATFORM_FIXTURE_URLS)
async def test_pipeline_with_mocked_http_collector(
    fixture_html: Callable[[str], str],
    platform: str,
    url: str,
) -> None:
    """Pipeline returns a valid UnifiedOutput for each fixture via HTTP override."""
    html = fixture_html(platform)
    collector = StubCollector(strategy="http", html=html)
    engine = PhoenixEngine(collectors={"http": collector})

    result = await engine.scrape(url, strategy="http", archive=False)

    assert result.success is True
    assert result.output is not None
    assert isinstance(result.output, UnifiedOutput)
    assert result.output.platform == platform
    assert result.output.url == url
    assert result.output.scraping_strategy == "http"
    assert result.output.text is not None
    assert result.selectors_used


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("platform", "url"),
    [
        ("instagram", "https://www.instagram.com/p/C0aBcDeFgHi/"),
        ("tiktok", "https://www.tiktok.com/@chefmaria/video/1234567890123456789"),
        ("linkedin", "https://www.linkedin.com/posts/alexchen_activity-123"),
        ("facebook", "https://www.facebook.com/GreenCityGardens/posts/112233"),
    ],
)
async def test_pipeline_uses_browser_primary_strategy(
    fixture_html: Callable[[str], str],
    platform: str,
    url: str,
) -> None:
    """Browser-primary platforms succeed when a browser collector is available."""
    html = fixture_html(platform)
    engine = PhoenixEngine(
        collectors={
            "http": StubCollector(strategy="http", html=html),
            "browser": StubCollector(strategy="browser", html=html),
        },
    )

    result = await engine.scrape(url, archive=False)

    assert result.success is True
    assert result.output is not None
    assert result.output.platform == platform
    assert result.output.scraping_strategy == "browser"


@pytest.mark.asyncio
async def test_pipeline_returns_error_when_no_collector_available() -> None:
    """Pipeline surfaces an error when no collector can execute the strategy."""
    engine = PhoenixEngine(collectors={})

    result = await engine.scrape("https://example.com/article/123", archive=False)

    assert result.success is False
    assert result.error is not None
