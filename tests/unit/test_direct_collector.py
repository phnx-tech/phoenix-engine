"""Unit tests for the direct HTTP collector."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from phoenix.collectors.direct import DirectCollector
from phoenix.exceptions import HTTPError, ScrapingError
from phoenix.infrastructure.rate_limiter import RateLimiter
from phoenix.models.config import Config
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit

URL = "https://example.com/page"
HTML = "<html><body>hello</body></html>"


def _build_response(url: str, status_code: int, text: str) -> httpx.Response:
    """Return a real httpx.Response for use with a mocked client."""
    request = httpx.Request("GET", url)
    return httpx.Response(
        status_code,
        text=text,
        request=request,
        headers={"content-type": "text/html"},
    )


@pytest.fixture
def mock_rate_limiter() -> RateLimiter:
    """Return a rate limiter with no delays for unit tests."""
    return RateLimiter(Config(rate_limits={"example.com": 1000.0}))


@pytest.mark.asyncio
async def test_direct_collector_success(mock_rate_limiter: RateLimiter) -> None:
    """DirectCollector returns a RawResponse on HTTP 200."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=_build_response(URL, 200, HTML))

    collector = DirectCollector(Config(), mock_rate_limiter, http_client=client)
    options = ScrapingOptions(timeout=10.0, max_retries=0)
    result = await collector.collect(URL, options)

    assert result.url == URL
    assert result.final_url == URL
    assert result.status_code == 200
    assert result.html == HTML
    assert result.strategy == "http"
    assert result.headers.get("content-type") == "text/html"
    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_direct_collector_timeout(mock_rate_limiter: RateLimiter) -> None:
    """DirectCollector raises ScrapingError on httpx timeout."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    collector = DirectCollector(Config(), mock_rate_limiter, http_client=client)
    options = ScrapingOptions(timeout=5.0, max_retries=0)

    with pytest.raises(ScrapingError, match="timed out"):
        await collector.collect(URL, options)


@pytest.mark.asyncio
async def test_direct_collector_404(mock_rate_limiter: RateLimiter) -> None:
    """DirectCollector raises HTTPError on 4xx/5xx responses."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=_build_response(URL, 404, "not found"))

    collector = DirectCollector(Config(), mock_rate_limiter, http_client=client)
    options = ScrapingOptions(timeout=5.0, max_retries=0)

    with pytest.raises(HTTPError, match="404"):
        await collector.collect(URL, options)


@pytest.mark.asyncio
async def test_direct_collector_redirect(mock_rate_limiter: RateLimiter) -> None:
    """DirectCollector records the final URL after redirects."""
    final_url = "https://example.com/page-final"
    response = _build_response(final_url, 200, HTML)
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=response)

    collector = DirectCollector(Config(), mock_rate_limiter, http_client=client)
    options = ScrapingOptions(timeout=5.0, max_retries=0)
    result = await collector.collect(URL, options)

    assert result.url == URL
    assert result.final_url == final_url
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_direct_collector_rate_limiter_called() -> None:
    """DirectCollector awaits the rate limiter before requesting."""
    rate_limiter = MagicMock(spec=RateLimiter)
    rate_limiter.wait_if_needed = AsyncMock()
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=_build_response(URL, 200, HTML))

    collector = DirectCollector(Config(), rate_limiter, http_client=client)
    options = ScrapingOptions(timeout=5.0, max_retries=0)
    await collector.collect(URL, options)

    rate_limiter.wait_if_needed.assert_awaited_once_with("example.com")
