"""Tests for the PhoenixArchitect Inspector."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from phoenix.architect.explorer import PageSnapshot
from phoenix.architect.inspector import Inspector


@pytest.fixture
def inspector() -> Inspector:
    extractor = AsyncMock()
    extractor.extract = AsyncMock(
        return_value={
            "platform_name": "quotes_toscrape",
            "content_type": "quote",
            "data_fields": ["text", "author"],
            "data_location": "css_selectors",
            "selectors": {"text": "span.text", "author": "small.author"},
            "url_patterns": [r"https?://quotes\.toscrape\.com/.+"],
            "notes": "Simple quote listing page",
        },
    )
    return Inspector(extractor)


@pytest.mark.asyncio
async def test_inspect_returns_spec(inspector: Inspector) -> None:
    snapshot = PageSnapshot(
        url="https://quotes.toscrape.com/",
        html="<html></html>",
        page_number=1,
    )
    spec = await inspector.inspect([snapshot], snapshot.url)
    assert spec["platform_name"] == "quotes_toscrape"
    assert spec["content_type"] == "quote"
    assert "text" in spec["data_fields"]


@pytest.mark.asyncio
async def test_inspect_handles_list_response() -> None:
    extractor = AsyncMock()
    extractor.extract = AsyncMock(return_value=[{"platform_name": "list_spec"}])
    inspector = Inspector(extractor)
    snapshot = PageSnapshot(
        url="https://example.com/",
        html="<html></html>",
        page_number=1,
    )
    spec = await inspector.inspect([snapshot], snapshot.url)
    assert spec["platform_name"] == "list_spec"


@pytest.mark.asyncio
async def test_inspect_returns_fallback_when_no_snapshots() -> None:
    extractor = AsyncMock()
    inspector = Inspector(extractor)
    spec = await inspector.inspect([], "https://example.com/path")
    assert spec["platform_name"] == "example_com"
    assert spec["url_patterns"] == [r"https?://(?:www\.)?example.com/.+"]
