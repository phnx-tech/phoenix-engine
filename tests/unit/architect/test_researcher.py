"""Tests for the PhoenixArchitect Researcher role."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from phoenix.architect.researcher import Researcher


@pytest.mark.asyncio
async def test_researcher_filters_non_http_urls() -> None:
    researcher = Researcher()
    raw = [
        {"href": "https://example.com/page", "title": "Example", "body": "snippet"},
        {"href": "ftp://example.com/file", "title": "FTP", "body": "ignored"},
        {"href": "", "title": "Empty", "body": "ignored"},
    ]

    with patch.object(researcher, "_ddgs_text", return_value=raw):
        results = await researcher.discover("test query", engine="duckduckgo")

    assert len(results) == 1
    assert results[0].url == "https://example.com/page"


@pytest.mark.asyncio
async def test_researcher_dedupes_urls() -> None:
    researcher = Researcher()
    raw = [
        {"href": "https://example.com/page", "title": "A", "body": ""},
        {"href": "https://example.com/page", "title": "B", "body": ""},
    ]

    with patch.object(researcher, "_ddgs_text", return_value=raw):
        results = await researcher.discover("test query", engine="duckduckgo")

    assert len(results) == 1


@pytest.mark.asyncio
async def test_researcher_blocks_social_domains() -> None:
    researcher = Researcher()
    raw = [
        {"href": "https://youtube.com/watch", "title": "Video", "body": ""},
        {"href": "https://example.com/article", "title": "Article", "body": ""},
    ]

    with patch.object(researcher, "_ddgs_text", return_value=raw):
        results = await researcher.discover("test query", engine="duckduckgo")

    assert len(results) == 1
    assert results[0].url == "https://example.com/article"


@pytest.mark.asyncio
async def test_researcher_serpapi_requires_key() -> None:
    researcher = Researcher()
    with patch.dict("os.environ", {}, clear=True):
        results = await researcher.discover("test query", engine="serpapi")
    assert results == []


@pytest.mark.asyncio
async def test_researcher_unsupported_engine_raises() -> None:
    researcher = Researcher()
    with pytest.raises(ValueError, match="Unsupported search engine"):
        await researcher.discover("test query", engine="bing")
