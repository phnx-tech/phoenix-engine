"""Headless browser collector using Playwright."""

from __future__ import annotations

import contextlib
import pathlib
import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from playwright.async_api import BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from phoenix.collectors.base import Collector
from phoenix.exceptions import AntiBotDetectedError, BrowserError
from phoenix.models.document import RawResponse
from phoenix.stealth.captcha import CaptchaAction, CaptchaDetector
from phoenix.stealth.humanizer import Humanizer

if TYPE_CHECKING:
    from phoenix.collectors.browser_pool import BrowserPool
    from phoenix.infrastructure.rate_limiter import RateLimiter
    from phoenix.infrastructure.session_manager import SessionManager
    from phoenix.options import CollectionOptions
    from phoenix.stealth.warming import SessionWarming


class BrowserCollector(Collector):
    """Collector that fetches pages via headless browser automation."""

    def __init__(  # noqa: PLR0913
        self,
        browser_pool: BrowserPool,
        rate_limiter: RateLimiter,
        screenshot_dir: str | pathlib.Path = "screenshots",
        *,
        session_manager: SessionManager | None = None,
        humanizer: Humanizer | None = None,
        captcha_detector: CaptchaDetector | None = None,
        session_warming: SessionWarming | None = None,
    ) -> None:
        """Initialize the browser collector.

        Args:
            browser_pool: Pool used to acquire and release browser contexts.
            rate_limiter: Rate limiter used to pace requests per domain.
            screenshot_dir: Directory where screenshots are saved when
                archiving is enabled.
            session_manager: Optional session manager for cookie injection.
            humanizer: Optional human-like delay/gesture behavior.
            captcha_detector: Optional CAPTCHA / challenge detector.
            session_warming: Optional session warming before target navigation.
        """
        self._pool = browser_pool
        self._rate_limiter = rate_limiter
        self._screenshot_dir = pathlib.Path(screenshot_dir)
        self._session_manager = session_manager
        self._humanizer = humanizer or Humanizer()
        self._captcha_detector = captcha_detector
        self._session_warming = session_warming

    @property
    def strategy(self) -> str:
        """Return the strategy identifier."""
        return "browser"

    @staticmethod
    def _domain(url: str) -> str:
        """Extract the network location from ``url``."""
        parsed = urlparse(url)
        return parsed.netloc or url

    async def _take_screenshot(self, page: Page, url: str) -> str | None:
        """Save a screenshot of ``page`` and return its path."""
        try:
            self._screenshot_dir.mkdir(parents=True, exist_ok=True)
            safe_name = urlparse(url).netloc.replace(":", "_") + "_" + f"{hash(url) & 0xFFFFFFFF:x}"
            path = self._screenshot_dir / f"{safe_name}.png"
            await page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception:  # noqa: BLE001
            # Screenshots are best-effort; do not fail collection for them.
            return None

    async def _inject_cookies(self, context: BrowserContext, url: str) -> None:
        """Inject persisted session cookies for the URL's platform."""
        if self._session_manager is None:
            return
        # Best-effort platform extraction from URL domain.
        domain = self._domain(url)
        # The session manager keys by platform name; we map common domains
        # heuristically. A real adapter will pass its platform explicitly.
        platform = domain.replace("www.", "").split(".")[0]
        cookies = self._session_manager.get_cookies(platform)
        if cookies:
            await context.add_cookies(cookies)  # type: ignore[arg-type]

    async def collect(self, url: str, options: CollectionOptions) -> RawResponse:
        """Fetch ``url`` via browser automation and return a raw response.

        Args:
            url: Target URL.
            options: Per-request collection options.

        Returns:
            RawResponse with rendered HTML, status, headers, and metadata.

        Raises:
            BrowserError: On navigation timeout or browser crash.
        """
        await self._rate_limiter.wait_if_needed(self._domain(url))
        await self._humanizer.before_navigation()

        context: BrowserContext | None = None
        page: Page | None = None
        try:
            context = await self._pool.acquire(options)
            await self._inject_cookies(context, url)

            if self._should_warm(options):
                assert self._session_warming is not None  # noqa: S101
                await self._session_warming.warm(context)

            page = await context.new_page()
            start = time.perf_counter()
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=options.timeout * 1000,
            )

            # Wait for network idle briefly if the page is still loading.
            with contextlib.suppress(PlaywrightTimeoutError):
                await page.wait_for_load_state("networkidle", timeout=5000)

            await self._humanizer.after_load(page)

            html = await page.content()
            latency_ms = (time.perf_counter() - start) * 1000
            status_code = response.status if response is not None else 200
            headers = dict(response.headers) if response is not None else {}
            final_url = page.url

            screenshot_path: str | None = None
            if options.archive:
                screenshot_path = await self._take_screenshot(page, url)

            raw_response = RawResponse(
                url=url,
                final_url=final_url,
                status_code=status_code,
                headers=headers,
                html=html,
                strategy=self.strategy,
                screenshot_path=screenshot_path,
            )
            raw_response.metadata["response_time_ms"] = latency_ms

            return self._apply_captcha_detection(raw_response, options)
        except PlaywrightTimeoutError as exc:
            raise BrowserError(f"Browser navigation timed out for {url}") from exc
        except Exception as exc:
            # Re-raise known scraping exceptions unchanged.
            if isinstance(exc, (BrowserError, AntiBotDetectedError)):
                raise
            raise BrowserError(f"Browser collection failed for {url}: {exc}") from exc
        finally:
            if page is not None:
                await page.close()
            if context is not None:
                await self._pool.release(context)

    def _should_warm(self, options: CollectionOptions) -> bool:
        """Return True when session warming should run before navigation."""
        if self._session_warming is None:
            return False
        if options.warm_session is not None:
            return options.warm_session
        return False

    def _apply_captcha_detection(
        self,
        raw_response: RawResponse,
        options: CollectionOptions,
    ) -> RawResponse:
        """Run CAPTCHA detection and update the response metadata."""
        if self._captcha_detector is None:
            return raw_response
        action = options.captcha_action or self._captcha_detector.action
        if action == CaptchaAction.SKIP:
            return raw_response

        result = self._captcha_detector.detect(
            html=raw_response.html,
            url=raw_response.url,
            final_url=raw_response.final_url,
            status_code=raw_response.status_code,
        )
        if result.detected:
            raw_response.metadata["captcha_detected"] = True
            raw_response.metadata["captcha_reason"] = result.reason
            if action == CaptchaAction.RAISE:
                raise AntiBotDetectedError(
                    f"CAPTCHA/anti-bot challenge detected: {result.reason}",
                )
        return raw_response


__all__ = ["BrowserCollector"]
