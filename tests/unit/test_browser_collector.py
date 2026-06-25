"""Unit tests for the browser collector."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from phoenix.collectors.browser import BrowserCollector
from phoenix.collectors.browser_pool import BrowserPool
from phoenix.exceptions import AntiBotDetectedError, BrowserError
from phoenix.infrastructure.rate_limiter import RateLimiter
from phoenix.infrastructure.session_manager import SessionManager
from phoenix.models.config import Config
from phoenix.options import ScrapingOptions
from phoenix.stealth.captcha import CaptchaAction, CaptchaDetector
from phoenix.stealth.warming import SessionWarming

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit

URL = "https://example.com/page"
HTML = "<html><body>rendered</body></html>"


def _make_pool(tmp_path: Path) -> tuple[BrowserPool, MagicMock, MagicMock, MagicMock]:
    """Return a pool and its mocked Playwright pieces."""
    context = MagicMock()
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
    context.new_page = AsyncMock(return_value=page)
    context.close = AsyncMock()
    context.add_cookies = AsyncMock()

    browser = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    browser.close = AsyncMock()

    playwright = MagicMock()
    playwright.chromium.launch = AsyncMock(return_value=browser)
    playwright.stop = AsyncMock()

    pool = BrowserPool(max_contexts=2, playwright=playwright)
    return pool, playwright, browser, context


@pytest.fixture
def mock_rate_limiter() -> RateLimiter:
    """Return a rate limiter with no delays for unit tests."""
    return RateLimiter(Config(rate_limits={"example.com": 1000.0}))


@pytest.mark.asyncio
async def test_browser_collector_success(tmp_path: Path, mock_rate_limiter: RateLimiter) -> None:
    """BrowserCollector returns rendered HTML as a RawResponse."""
    pool, _playwright, _browser, context = _make_pool(tmp_path)
    collector = BrowserCollector(pool, mock_rate_limiter, screenshot_dir=tmp_path / "shots")
    options = ScrapingOptions(timeout=10.0, archive=True)

    result = await collector.collect(URL, options)

    assert result.url == URL
    assert result.final_url == URL
    assert result.status_code == 200
    assert result.html == HTML
    assert result.strategy == "browser"
    assert result.headers.get("content-type") == "text/html"
    assert result.screenshot_path is not None
    context.new_page.assert_awaited_once()


@pytest.mark.asyncio
async def test_browser_collector_timeout(tmp_path: Path, mock_rate_limiter: RateLimiter) -> None:
    """BrowserCollector raises BrowserError on navigation timeout."""
    pool, _playwright, _browser, context = _make_pool(tmp_path)
    page = context.new_page.return_value
    page.goto = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

    collector = BrowserCollector(pool, mock_rate_limiter, screenshot_dir=tmp_path / "shots")
    options = ScrapingOptions(timeout=5.0, archive=False)

    with pytest.raises(BrowserError, match="timed out"):
        await collector.collect(URL, options)


@pytest.mark.asyncio
async def test_browser_collector_screenshot_failure_is_non_fatal(
    tmp_path: Path,
    mock_rate_limiter: RateLimiter,
) -> None:
    """A failing screenshot does not fail collection."""
    pool, _playwright, _browser, context = _make_pool(tmp_path)
    page = context.new_page.return_value
    page.screenshot = AsyncMock(side_effect=RuntimeError("disk full"))

    collector = BrowserCollector(pool, mock_rate_limiter, screenshot_dir=tmp_path / "shots")
    options = ScrapingOptions(timeout=5.0, archive=True)

    result = await collector.collect(URL, options)

    assert result.html == HTML
    assert result.screenshot_path is None


@pytest.mark.asyncio
async def test_browser_collector_crashes_raise_browser_error(
    tmp_path: Path,
    mock_rate_limiter: RateLimiter,
) -> None:
    """Unexpected page errors are wrapped as BrowserError."""
    pool, _playwright, _browser, context = _make_pool(tmp_path)
    page = context.new_page.return_value
    page.goto = AsyncMock(side_effect=ValueError("boom"))

    collector = BrowserCollector(pool, mock_rate_limiter, screenshot_dir=tmp_path / "shots")
    options = ScrapingOptions(timeout=5.0, archive=False)

    with pytest.raises(BrowserError, match="boom"):
        await collector.collect(URL, options)


@pytest.mark.asyncio
async def test_browser_collector_flags_captcha(
    tmp_path: Path,
    mock_rate_limiter: RateLimiter,
) -> None:
    """CAPTCHA detection flags the response metadata when action is FLAG."""
    pool, _playwright, _browser, context = _make_pool(tmp_path)
    page = context.new_page.return_value
    page.content = AsyncMock(return_value="<html>cf-challenge</html>")

    detector = CaptchaDetector(action=CaptchaAction.FLAG)
    collector = BrowserCollector(
        pool,
        mock_rate_limiter,
        screenshot_dir=tmp_path / "shots",
        captcha_detector=detector,
    )
    options = ScrapingOptions(timeout=5.0, archive=False, captcha_action="flag")

    result = await collector.collect(URL, options)

    assert result.metadata.get("captcha_detected") is True
    assert "cf-challenge" in result.metadata.get("captcha_reason", "")


@pytest.mark.asyncio
async def test_browser_collector_raises_on_captcha(
    tmp_path: Path,
    mock_rate_limiter: RateLimiter,
) -> None:
    """CAPTCHA detection raises AntiBotDetectedError when action is RAISE."""
    pool, _playwright, _browser, context = _make_pool(tmp_path)
    page = context.new_page.return_value
    page.content = AsyncMock(return_value="<html>g-recaptcha</html>")

    detector = CaptchaDetector(action=CaptchaAction.RAISE)
    collector = BrowserCollector(
        pool,
        mock_rate_limiter,
        screenshot_dir=tmp_path / "shots",
        captcha_detector=detector,
    )
    options = ScrapingOptions(timeout=5.0, archive=False, captcha_action="raise")

    with pytest.raises(AntiBotDetectedError, match="g-recaptcha"):
        await collector.collect(URL, options)


@pytest.mark.asyncio
async def test_browser_collector_injects_session_cookies(
    tmp_path: Path,
    mock_rate_limiter: RateLimiter,
) -> None:
    """BrowserCollector loads persisted cookies through the session manager."""
    pool, _playwright, _browser, context = _make_pool(tmp_path)

    storage = MagicMock()
    cookies = [{"name": "session", "value": "abc", "domain": "example.com"}]
    storage.get_session.return_value.cookies = cookies
    storage.get_session.return_value.is_valid = True
    session_manager = SessionManager(storage)

    collector = BrowserCollector(
        pool,
        mock_rate_limiter,
        screenshot_dir=tmp_path / "shots",
        session_manager=session_manager,
    )
    options = ScrapingOptions(timeout=5.0, archive=False)
    await collector.collect("https://example.com/page", options)

    context.add_cookies.assert_awaited_once()


@pytest.mark.asyncio
async def test_browser_collector_warms_session(
    tmp_path: Path,
    mock_rate_limiter: RateLimiter,
) -> None:
    """BrowserCollector warms the session before navigation when configured."""
    pool, _playwright, _browser, _context = _make_pool(tmp_path)
    warming = SessionWarming(warm_urls=["https://warm.example"], visits=1, wait_seconds=0.1)
    collector = BrowserCollector(
        pool,
        mock_rate_limiter,
        screenshot_dir=tmp_path / "shots",
        session_warming=warming,
    )
    options = ScrapingOptions(timeout=5.0, archive=False, warm_session=True)

    result = await collector.collect(URL, options)

    assert result.html == HTML
