"""Integration tests for collectors and rate limiting.

These tests exercise the same code paths as the unit tests but are marked as
integration tests so that marker-filtered runs still measure coverage on the
infrastructure modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

if TYPE_CHECKING:
    from pathlib import Path
import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from phoenix.collectors.browser import BrowserCollector
from phoenix.collectors.browser_pool import BrowserPool
from phoenix.collectors.direct import DirectCollector
from phoenix.exceptions import BrowserError, HTTPError, ScrapingError
from phoenix.infrastructure.rate_limiter import RateLimiter
from phoenix.models.config import Config
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.integration

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
def fast_rate_limiter() -> RateLimiter:
    """Return a rate limiter with a very high per-domain rate."""
    return RateLimiter(Config(rate_limits={"example.com": 1000.0}))


@pytest.mark.asyncio
async def test_direct_collector_integration_success(
    fast_rate_limiter: RateLimiter,
) -> None:
    """DirectCollector returns a RawResponse on HTTP 200."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=_build_response(URL, 200, HTML))

    collector = DirectCollector(Config(), fast_rate_limiter, http_client=client)
    result = await collector.collect(URL, ScrapingOptions(timeout=10.0, max_retries=0))

    assert result.url == URL
    assert result.status_code == 200
    assert result.html == HTML
    assert result.strategy == "http"
    client.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_direct_collector_integration_404(
    fast_rate_limiter: RateLimiter,
) -> None:
    """DirectCollector raises HTTPError on 4xx responses."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=_build_response(URL, 404, "not found"))

    collector = DirectCollector(Config(), fast_rate_limiter, http_client=client)

    with pytest.raises(HTTPError, match="404"):
        await collector.collect(URL, ScrapingOptions(timeout=5.0, max_retries=0))


@pytest.mark.asyncio
async def test_rate_limiter_integration_paces_requests() -> None:
    """Back-to-back requests to the same domain trigger a sleep."""
    limiter = RateLimiter(Config(rate_limits={"example.com": 1.0}))

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await limiter.wait_if_needed("example.com")
        await limiter.wait_if_needed("example.com")

    mock_sleep.assert_awaited_once()
    call_args = mock_sleep.await_args.args[0]
    assert 0.9 <= call_args <= 1.1


@pytest.mark.asyncio
async def test_rate_limiter_integration_platform_default() -> None:
    """Platform-specific defaults apply when no override is configured."""
    limiter = RateLimiter(Config())

    assert limiter._rate_for("instagram.com") == 0.5
    assert limiter._rate_for("x.com") == 0.5
    assert limiter._rate_for("other.test") == 1.0 / 3.0


def _make_browser_pool(
    tmp_path: Path,
    max_contexts: int = 2,
) -> tuple[BrowserPool, MagicMock, MagicMock, MagicMock]:
    """Return a pool and its mocked Playwright/browser/context objects."""
    page = MagicMock()
    response = MagicMock()
    response.status = 200
    response.headers = {"content-type": "text/html"}

    page.goto = AsyncMock(return_value=response)
    page.content = AsyncMock(return_value=HTML)
    page.wait_for_load_state = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.screenshot = AsyncMock()
    page.url = URL
    page.viewport_size = {"width": 1920, "height": 1080}
    page.close = AsyncMock()
    page.mouse = MagicMock()
    page.mouse.wheel = AsyncMock()
    page.mouse.move = AsyncMock()

    contexts: list[MagicMock] = []

    def _make_context() -> MagicMock:
        context = MagicMock()
        context.new_page = AsyncMock(return_value=page)
        context.close = AsyncMock()
        contexts.append(context)
        return context

    first_context = _make_context()

    def _context_generator() -> MagicMock:
        yield first_context
        while True:
            yield _make_context()

    browser = MagicMock()
    browser.new_context = AsyncMock(side_effect=_context_generator())
    browser.close = AsyncMock()

    playwright = MagicMock()
    playwright.chromium.launch = AsyncMock(return_value=browser)
    playwright.stop = AsyncMock()

    pool = BrowserPool(max_contexts=max_contexts, playwright=playwright)
    return pool, playwright, browser, first_context


@pytest.mark.asyncio
async def test_browser_collector_integration_success(tmp_path: Path) -> None:
    """BrowserCollector returns rendered HTML via a mocked browser pool."""
    pool, _playwright, _browser, context = _make_browser_pool(tmp_path)
    collector = BrowserCollector(pool, RateLimiter(Config()), screenshot_dir=tmp_path / "shots")
    options = ScrapingOptions(timeout=10.0, archive=True)

    result = await collector.collect(URL, options)

    assert result.url == URL
    assert result.status_code == 200
    assert result.html == HTML
    assert result.strategy == "browser"
    context.new_page.assert_awaited_once()


@pytest.mark.asyncio
async def test_browser_collector_integration_timeout(tmp_path: Path) -> None:
    """BrowserCollector raises BrowserError on navigation timeout."""
    pool, _playwright, _browser, context = _make_browser_pool(tmp_path)
    page = context.new_page.return_value
    page.goto = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

    collector = BrowserCollector(pool, RateLimiter(Config()), screenshot_dir=tmp_path / "shots")
    options = ScrapingOptions(timeout=5.0, archive=False)

    with pytest.raises(BrowserError, match="timed out"):
        await collector.collect(URL, options)


@pytest.mark.asyncio
async def test_browser_pool_integration_acquire_and_release(tmp_path: Path) -> None:
    """Acquired contexts are reused after release."""
    pool, _playwright, browser, _context = _make_browser_pool(tmp_path)

    first = await pool.acquire()
    assert browser.new_context.await_count == 1

    await pool.release(first)
    second = await pool.acquire()
    assert second is first
    assert browser.new_context.await_count == 1


@pytest.mark.asyncio
async def test_browser_pool_integration_waits_when_exhausted(tmp_path: Path) -> None:
    """Pool waits for a release when all contexts are in use."""
    pool, _playwright, browser, _contexts = _make_browser_pool(tmp_path, max_contexts=1)

    context = await pool.acquire()
    assert browser.new_context.await_count == 1

    release_called = False

    async def _release_later() -> None:
        nonlocal release_called
        await pool.release(context)
        release_called = True

    import asyncio

    _task = asyncio.create_task(_release_later())
    acquired = await pool.acquire()
    _task.done()
    assert acquired is context
    assert release_called


@pytest.mark.asyncio
async def test_browser_pool_integration_close_all(tmp_path: Path) -> None:
    """close_all closes contexts, browser, and does not stop injected Playwright."""
    pool, playwright, browser, _context = _make_browser_pool(tmp_path)

    await pool.acquire()
    await pool.acquire()
    captured_contexts = list(pool._contexts)
    await pool.close_all()

    assert len(captured_contexts) == 2
    for context in captured_contexts:
        context.close.assert_awaited_once()
    browser.close.assert_awaited_once()
    assert playwright.stop.await_count == 0


@pytest.mark.asyncio
async def test_direct_collector_integration_retries_request_error(
    fast_rate_limiter: RateLimiter,
) -> None:
    """DirectCollector retries request errors up to max_retries."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(side_effect=httpx.ConnectError("connection failed"))

    collector = DirectCollector(Config(), fast_rate_limiter, http_client=client)

    with pytest.raises(ScrapingError, match="connection failed"):
        await collector.collect(URL, ScrapingOptions(timeout=5.0, max_retries=1))

    assert client.get.await_count == 2


@pytest.mark.asyncio
async def test_rate_limiter_integration_config_override_by_platform_key() -> None:
    """Config.rate_limits can use the platform key to override defaults."""
    limiter = RateLimiter(Config(rate_limits={"instagram": 0.1}))

    assert limiter._rate_for("instagram.com") == 0.1
