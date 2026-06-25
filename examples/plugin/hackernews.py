"""Example third-party adapter for Phoenix Engine.

This adapter demonstrates the minimal surface area required to add support
for a new platform. It handles public Hacker News item pages and produces
standardized output.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from phoenix.adapters.base import BaseAdapter
from phoenix.models.output import UnifiedOutput
from phoenix.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from re import Pattern

    from phoenix.collectors.base import Collector
    from phoenix.models.document import RawResponse
    from phoenix.options import ScrapingOptions


class HackerNewsAdapter(BaseAdapter):
    """Example adapter for public Hacker News item pages."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the Hacker News adapter manifest."""
        return PluginManifest(
            name="hackernews",
            version="0.1.0",
            description="Example adapter for Hacker News item pages.",
            author="Phoenix Engine Community",
            platforms=["hackernews"],
            url_patterns=[
                r"https?://news\.ycombinator\.com/item\?id=\d+",
            ],
            strategies=["http"],
            requires_auth=False,
            supports_ai_fallback=False,
        )

    def supported_patterns(self) -> list[Pattern[str]]:
        """Return compiled Hacker News URL patterns."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in self.manifest.url_patterns]

    def preferred_strategies(self) -> list[str]:
        """Hacker News is static HTML; HTTP is sufficient."""
        return ["http"]

    async def collect(
        self,
        url: str,
        _strategy: str,
        collector: Collector,
        options: ScrapingOptions,
    ) -> RawResponse:
        """Collect raw HTML for ``url`` using the supplied ``collector``."""
        return await collector.collect(url, options)

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract Hacker News item fields from ``raw_response``."""
        soup = BeautifulSoup(raw_response.html, "html.parser")
        url = raw_response.final_url or raw_response.url

        selector_sets = {
            "title": [
                ".titleline > a",
                ".athing .titleline a",
            ],
            "author_username": [
                ".hnuser",
                "a.hnuser",
            ],
            "text": [
                ".comment .commtext",
                ".toptext",
            ],
            "score": [
                ".score",
            ],
            "timestamp": [
                ".age",
                ".age a",
            ],
        }

        results = self._extract_with_selectors(soup, selector_sets)
        title = self._first_text(results, "title")
        text = self._first_text(results, "text")

        return {
            "content_type": "post",
            "title": title,
            "text": text or title,
            "author_username": self._first_text(results, "author_username"),
            "score": self._parse_number(self._first_text(results, "score")),
            "timestamp": self._parse_age(self._first_text(results, "timestamp")),
            "url": url,
            "selectors_used": [
                results[field]["selector_used"]
                for field in selector_sets
                if results.get(field, {}).get("selector_used")
            ],
        }

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Convert extracted Hacker News fields into ``UnifiedOutput``."""
        return UnifiedOutput(
            url=url,
            platform="hackernews",
            content_type=extracted.get("content_type", "post"),
            title=extracted.get("title"),
            text=extracted.get("text"),
            author=extracted.get("author_username"),
            timestamp=extracted.get("timestamp"),
            likes=extracted.get("score"),
            scraping_strategy=strategy,
            selectors_used=extracted.get("selectors_used", []),
        )

    def _first_text(self, results: dict[str, Any], field: str) -> str | None:
        """Return the extracted text for ``field`` or ``None``."""
        value = results.get(field, {}).get("value")
        return value.strip() if value else None

    def _parse_number(self, text: str | None) -> int | None:
        """Parse a numeric score string into an integer."""
        if text is None:
            return None
        cleaned = re.sub(r"\b(points?|score)\b", "", text, flags=re.IGNORECASE)
        return self._parse_engagement(cleaned.strip())

    def _parse_age(self, text: str | None) -> datetime | None:
        """Parse a relative age string into a UTC datetime approximation."""
        if not text:
            return None
        # Return current UTC time as a coarse approximation for the example.
        return datetime.now(UTC)


__all__ = ["HackerNewsAdapter"]
