"""Session warming to age cookies and localStorage before target navigation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page


@dataclass
class SessionWarming:
    """Navigate to benign sites before the real target to warm the session.

    Many anti-bot systems flag cold browsers that immediately visit a target
    site. Visiting a search engine or news site first makes the browser look
    like a normal user.
    """

    warm_urls: list[str] = field(
        default_factory=lambda: ["https://www.google.com", "https://www.bing.com"],
    )
    visits: int = 1
    wait_seconds: float = 2.0

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.warm_urls:
            msg = "SessionWarming requires at least one warm URL"
            raise ValueError(msg)
        if self.visits < 0:
            msg = "visits must be non-negative"
            raise ValueError(msg)
        if self.wait_seconds < 0:
            msg = "wait_seconds must be non-negative"
            raise ValueError(msg)

    async def warm(self, context: BrowserContext) -> None:
        """Open a new page and visit benign URLs before the target."""
        if self.visits <= 0:
            return
        urls = random.sample(self.warm_urls, min(self.visits, len(self.warm_urls)))
        page: Page | None = None
        try:
            page = await context.new_page()
            for url in urls:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(int(self.wait_seconds * 1000))
        finally:
            if page is not None:
                await page.close()


__all__ = ["SessionWarming"]
