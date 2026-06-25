"""Human-like interaction delays and gestures for browser collection."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page, ViewportSize


@dataclass
class Humanizer:
    """Introduces randomized delays and lightweight cursor/scroll gestures.

    These actions raise the cost of trivial bot detection at the cost of
    increased latency. They are skipped when ``delay_min_ms`` and
    ``delay_max_ms`` are both zero.
    """

    delay_min_ms: float = 0.0
    delay_max_ms: float = 0.0
    scroll_pages: int = 0

    def __post_init__(self) -> None:
        """Validate delay bounds."""
        if self.delay_min_ms < 0 or self.delay_max_ms < 0:
            msg = "Humanizer delays must be non-negative"
            raise ValueError(msg)
        if self.delay_min_ms > self.delay_max_ms:
            msg = "delay_min_ms must not exceed delay_max_ms"
            raise ValueError(msg)

    @property
    def enabled(self) -> bool:
        """Return ``True`` when at least one delay or scroll is configured."""
        return (self.delay_max_ms > 0 and self.delay_min_ms >= 0) or self.scroll_pages > 0

    def delay_seconds(self) -> float:
        """Return a random delay between min and max in seconds."""
        if self.delay_max_ms <= 0:
            return 0.0
        return random.uniform(self.delay_min_ms, self.delay_max_ms) / 1000.0  # noqa: S311

    def _delay_seconds(self) -> float:
        """Deprecated alias for :meth:`delay_seconds`."""
        return self.delay_seconds()

    async def before_navigation(self) -> None:
        """Pause briefly before navigating to the target URL."""
        delay = self._delay_seconds()
        if delay > 0:
            await asyncio.sleep(delay)

    async def after_load(self, page: Page | None) -> None:
        """Perform lightweight human-like actions after the page loads."""
        if page is None:
            return
        await self._scroll_page(page)
        await self._small_mouse_move(page)

    async def _scroll_page(self, page: Page) -> None:
        """Scroll down and up a few times to mimic reading behavior."""
        if self.scroll_pages <= 0:
            return
        viewport = self._viewport(page)
        viewport_height = viewport["height"]
        for _ in range(self.scroll_pages):
            step = random.randint(  # noqa: S311
                int(viewport_height * 0.4),
                int(viewport_height * 0.8),
            )
            await page.mouse.wheel(0, step)
            await asyncio.sleep(random.uniform(0.2, 0.5))  # noqa: S311
        # Scroll back toward the top slightly.
        await page.mouse.wheel(0, -random.randint(step // 4, step // 2))  # noqa: S311
        await asyncio.sleep(random.uniform(0.1, 0.3))  # noqa: S311

    @staticmethod
    def _viewport(page: Page) -> ViewportSize:
        """Return a valid viewport dict, falling back to defaults."""
        viewport = page.viewport_size
        if (
            isinstance(viewport, dict)
            and isinstance(viewport.get("width"), int)
            and isinstance(viewport.get("height"), int)
        ):
            return viewport
        return {"width": 1920, "height": 1080}

    async def _small_mouse_move(self, page: Page) -> None:
        """Move the cursor a small amount to appear human."""
        viewport = self._viewport(page)
        x = random.randint(50, max(60, viewport["width"] // 4))  # noqa: S311
        y = random.randint(50, max(60, viewport["height"] // 4))  # noqa: S311
        await page.mouse.move(x, y)


__all__ = ["Humanizer"]
