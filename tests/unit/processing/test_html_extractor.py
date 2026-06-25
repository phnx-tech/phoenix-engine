"""Tests for the HTML extractor."""

from __future__ import annotations

import pytest

from phoenix.models.document import RawResponse
from phoenix.processing.html_extractor import HTMLExtractor


@pytest.mark.asyncio
async def test_html_extractor_returns_confidence_scores() -> None:
    html = """
    <html>
      <head><title>Page Title</title><meta property="og:image" content="https://img.png"/></head>
      <body><p>Hello world</p></body>
    </html>
    """
    raw_response = RawResponse(
        url="https://example.com",
        status_code=200,
        html=html,
        strategy="http",
    )
    extractor = HTMLExtractor()
    result = await extractor.extract(raw_response, "generic")

    assert result["title_confidence"] == 1.0
    assert result["text_confidence"] == 1.0
    assert result["author_confidence"] == 0.0
    assert result["media_urls_confidence"] == 1.0


@pytest.mark.asyncio
async def test_html_extractor_missing_fields_have_zero_confidence() -> None:
    html = "<html><head></head><body></body></html>"
    raw_response = RawResponse(
        url="https://example.com",
        status_code=200,
        html=html,
        strategy="http",
    )
    extractor = HTMLExtractor()
    result = await extractor.extract(raw_response, "generic")

    assert result["title_confidence"] == 0.0
    assert result["text_confidence"] == 0.0
    assert result["media_urls_confidence"] == 0.0
