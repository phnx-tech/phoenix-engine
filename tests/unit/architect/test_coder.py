"""Tests for the PhoenixArchitect Coder."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from phoenix.architect.coder import Coder
from phoenix.architect.explorer import PageSnapshot


@pytest.fixture
def coder() -> Coder:
    extractor = AsyncMock()
    extractor.extract = AsyncMock(
        return_value={
            "code": "class GeneratedAdapter:\n    pass\n",
            "platform_name": "quotes_toscrape",
            "url_patterns": [r"https?://quotes\.toscrape\.com/.+"],
        },
    )
    return Coder(extractor)


@pytest.mark.asyncio
async def test_generate_returns_code(coder: Coder) -> None:
    snapshot = PageSnapshot(
        url="https://quotes.toscrape.com/",
        html="<html></html>",
        page_number=1,
    )
    spec = {"platform_name": "quotes_toscrape", "content_type": "quote"}
    code = await coder.generate(spec, snapshot, snapshot.url)
    assert "class GeneratedAdapter" in code


@pytest.mark.asyncio
async def test_generate_handles_list_response() -> None:
    extractor = AsyncMock()
    extractor.extract = AsyncMock(
        return_value=[{"code": "code", "platform_name": "x", "url_patterns": []}],
    )
    coder = Coder(extractor)
    snapshot = PageSnapshot(url="https://example.com/", html="<html></html>", page_number=1)
    code = await coder.generate({"platform_name": "x"}, snapshot, snapshot.url)
    assert code == "code"


@pytest.mark.asyncio
async def test_generate_returns_empty_on_invalid_result() -> None:
    extractor = AsyncMock()
    extractor.extract = AsyncMock(return_value="not a dict")
    coder = Coder(extractor)
    snapshot = PageSnapshot(url="https://example.com/", html="<html></html>", page_number=1)
    code = await coder.generate({"platform_name": "x"}, snapshot, snapshot.url)
    assert code == ""
