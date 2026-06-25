"""Browser exploration utilities for PhoenixArchitect.

``BrowserExplorer`` navigates to a URL, scrolls to load lazy content, and
follows pagination links to collect a sequence of page snapshots. It is the
"feet and eyes" of the autonomous adapter-generation loop.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from phoenix.stealth.humanizer import Humanizer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from phoenix.collectors.browser_pool import BrowserPool
    from phoenix.options import CollectionOptions

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_SCROLL_ATTEMPTS = 3
DEFAULT_PAGE_LOAD_WAIT = 2.0

# CSS selectors used to locate pagination controls. Ordered by specificity:
# numbered pages first, then explicit next-page semantics, then common text.
_PAGINATION_SELECTORS: Sequence[str] = (
    'a[rel="next"]',
    'a[aria-label="Next page"]',
    'a[aria-label="Next"]',
    'button[aria-label="Next page"]',
    'button[aria-label="Next"]',
    'a:has-text("Next")',
    'a:has-text(">")',
    'a:has-text("→")',
    'button:has-text("Next")',
    'button:has-text("Load more")',
    'a:has-text("Load more")',
)


@dataclass(frozen=True)
class PageSnapshot:
    """A captured state of a browsed page."""

    url: str
    html: str
    page_number: int
    title: str = ""


class BrowserExplorer:
    """Explore a website with scrolling and pagination.

    Example:
        pool = BrowserPool(max_contexts=1, stealth_enabled=True)
        explorer = BrowserExplorer(pool)
        snapshots = await explorer.explore(
            "https://example.com/listings", max_pages=3
        )
        for snap in snapshots:
            print(snap.url, len(snap.html))
        await pool.close_all()
    """

    def __init__(
        self,
        browser_pool: BrowserPool,
        *,
        humanizer: Humanizer | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        scroll_attempts: int = DEFAULT_SCROLL_ATTEMPTS,
        page_load_wait: float = DEFAULT_PAGE_LOAD_WAIT,
    ) -> None:
        """Initialize the explorer.

        Args:
            browser_pool: Pool used to acquire and release browser contexts.
            humanizer: Optional human-like delays. A default ``Humanizer`` is
                created if none is supplied.
            timeout_seconds: Maximum seconds to wait for page navigation.
            scroll_attempts: How many times to scroll the page looking for
                lazy-loaded content.
            page_load_wait: Seconds to wait after navigation / scroll for
                dynamic content to settle.
        """
        self._pool = browser_pool
        self._humanizer = humanizer or Humanizer()
        self._timeout_ms = timeout_seconds * 1000
        self._scroll_attempts = scroll_attempts
        self._page_load_wait = page_load_wait

    async def explore(
        self,
        url: str,
        *,
        max_pages: int = 3,
        scroll: bool = True,
        options: CollectionOptions | None = None,
    ) -> list[PageSnapshot]:
        """Collect snapshots from ``url`` across multiple pages.

        The explorer follows numbered pagination or "Next" links up to
        ``max_pages``. It also scrolls each page to trigger lazy loading
        before capturing HTML.

        Args:
            url: Starting URL.
            max_pages: Maximum number of pagination pages to collect.
            scroll: Whether to scroll the page to load lazy content.
            options: Optional collection options for the browser pool.

        Returns:
            List of ``PageSnapshot`` objects, one per collected page.
        """
        if max_pages < 1:
            raise ValueError("max_pages must be >= 1")

        context = await self._pool.acquire(options)
        page = await context.new_page()
        snapshots: list[PageSnapshot] = []
        current_url = url

        try:
            for page_number in range(1, max_pages + 1):
                logger.info("Exploring page %d: %s", page_number, current_url)
                await page.goto(
                    current_url,
                    wait_until="domcontentloaded",
                    timeout=self._timeout_ms,
                )
                with contextlib.suppress(PlaywrightTimeoutError):
                    await page.wait_for_load_state("networkidle", timeout=5000)
                await asyncio.sleep(self._page_load_wait)
                await self._humanizer.after_load(page)

                if scroll:
                    await self._scroll_page(page)

                html = await page.content()
                title = await page.title()
                snapshots.append(
                    PageSnapshot(
                        url=page.url,
                        html=html,
                        page_number=page_number,
                        title=title,
                    ),
                )

                if page_number >= max_pages:
                    break

                next_selector = await self._find_next_pagination(page, page_number)
                if next_selector is None:
                    logger.info("No further pagination found after page %d", page_number)
                    break

                await self._click_pagination(page, next_selector)
                current_url = page.url
        finally:
            await page.close()
            await self._pool.release(context)

        return snapshots

    async def _scroll_page(self, page: Page) -> None:
        """Scroll to the bottom of ``page`` until no new content loads."""
        previous_height = 0
        for attempt in range(self._scroll_attempts):
            current_height = await page.evaluate(
                "document.body ? document.body.scrollHeight : 0",
            )
            if current_height == previous_height:
                logger.debug("Scroll height stable at attempt %d", attempt)
                break
            previous_height = current_height
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(self._humanizer.delay_seconds())
            await asyncio.sleep(self._page_load_wait)

    async def _find_next_pagination(
        self,
        page: Page,
        current_page: int,
    ) -> str | None:
        """Return a CSS selector for the next pagination control, if any."""
        # Prefer explicit numbered pagination: look for a link whose text is
        # exactly the next page number.
        numbered = await page.query_selector(f'a:has-text("{current_page + 1}")')
        if numbered is not None:
            visible = await numbered.is_visible()
            if visible:
                logger.debug("Found numbered pagination for page %d", current_page + 1)
                return f'a:has-text("{current_page + 1}")'

        # Fall back to semantic "next" controls.
        for selector in _PAGINATION_SELECTORS:
            element = await page.query_selector(selector)
            if element is not None and await element.is_visible():
                logger.debug("Found pagination selector: %s", selector)
                return selector

        return None

    async def _click_pagination(self, page: Page, selector: str) -> None:
        """Click the pagination control and wait for the next page."""
        await self._humanizer.before_navigation()
        try:
            await page.click(selector)
        except PlaywrightTimeoutError:
            # Some pagination controls need a gentler click via JS.
            await page.evaluate(
                """
                (selector) => {
                    const el = document.querySelector(selector);
                    if (el) el.click();
                }
                """,
                selector,
            )
        await asyncio.sleep(self._page_load_wait)
        with contextlib.suppress(PlaywrightTimeoutError):
            await page.wait_for_load_state("networkidle", timeout=5000)
