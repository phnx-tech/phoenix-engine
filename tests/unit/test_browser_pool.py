"""Unit tests for the Playwright browser context pool."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from phoenix.collectors.browser_pool import BrowserPool
from phoenix.options import ScrapingOptions
from phoenix.stealth.profile import profile_presets
from phoenix.stealth.rotator import ProxyRotator

pytestmark = pytest.mark.unit


def _make_pool(
    max_contexts: int = 2,
    **kwargs: object,
) -> tuple[BrowserPool, MagicMock, MagicMock, list[MagicMock]]:
    """Return a pool and its mocked Playwright/browser/context objects."""
    contexts: list[MagicMock] = []

    def _new_context(**_kwargs: object) -> MagicMock:
        context = MagicMock()
        context.close = AsyncMock()
        contexts.append(context)
        return context

    browser = MagicMock()
    browser.new_context = AsyncMock(side_effect=_new_context)
    browser.close = AsyncMock()

    playwright = MagicMock()
    playwright.chromium.launch = AsyncMock(return_value=browser)
    playwright.stop = AsyncMock()

    pool = BrowserPool(max_contexts=max_contexts, playwright=playwright, **kwargs)
    return pool, playwright, browser, contexts


@pytest.mark.asyncio
async def test_browser_pool_acquire_release() -> None:
    """Acquired contexts are reused after release."""
    pool, _playwright, browser, _contexts = _make_pool(max_contexts=2)

    first = await pool.acquire()
    assert browser.new_context.await_count == 1

    await pool.release(first)
    second = await pool.acquire()
    assert second is first
    assert browser.new_context.await_count == 1
    await pool.close_all()


@pytest.mark.asyncio
async def test_browser_pool_respects_max_contexts() -> None:
    """Pool waits for a release when max contexts are in use."""
    pool, _playwright, browser, _contexts = _make_pool(max_contexts=1)

    context = await pool.acquire()
    assert browser.new_context.await_count == 1

    release_called = False

    async def _release_later() -> None:
        nonlocal release_called
        await pool.release(context)
        release_called = True

    _task = asyncio.create_task(_release_later())
    acquired = await pool.acquire()
    assert acquired is context
    assert release_called
    await _task


@pytest.mark.asyncio
async def test_browser_pool_close_all() -> None:
    """close_all closes contexts, browser, and does not stop injected Playwright."""
    pool, playwright, browser, contexts = _make_pool(max_contexts=2)

    await pool.acquire()
    await pool.acquire()
    await pool.close_all()

    assert len(contexts) == 2
    for context in contexts:
        context.close.assert_awaited_once()
    browser.close.assert_awaited_once()
    assert playwright.stop.await_count == 0


@pytest.mark.asyncio
async def test_browser_pool_applies_stealth_profile() -> None:
    """Stealth-enabled pool creates contexts with profile settings."""
    profile = profile_presets()["chrome_windows"]
    pool, _playwright, browser, _contexts = _make_pool(
        max_contexts=1,
        stealth_enabled=True,
        stealth_profile=profile,
    )

    await pool.acquire()

    browser.new_context.assert_awaited_once()
    kwargs = browser.new_context.await_args.kwargs
    assert kwargs["user_agent"] == profile.user_agent
    assert kwargs["viewport"] == profile.viewport


@pytest.mark.asyncio
async def test_browser_pool_applies_proxy_rotator() -> None:
    """Pool injects the next proxy URL into new contexts."""
    pool, _playwright, browser, _contexts = _make_pool(
        max_contexts=1,
        proxy_rotator=ProxyRotator(proxies=["http://proxy1:8080"]),
    )

    await pool.acquire()

    kwargs = browser.new_context.await_args.kwargs
    assert kwargs.get("proxy") == {"server": "http://proxy1:8080"}


@pytest.mark.asyncio
async def test_browser_pool_request_specific_profile() -> None:
    """Per-request options can select a specific preset profile."""
    pool, _playwright, browser, _contexts = _make_pool(max_contexts=1)
    options = ScrapingOptions(stealth_enabled=True, stealth_profile="firefox_windows")

    await pool.acquire(options)

    kwargs = browser.new_context.await_args.kwargs
    assert "Firefox" in kwargs["user_agent"]
