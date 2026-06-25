"""Selector engine stub wrapping the HTML extractor.

This module exposes the documentation-facing ``SelectorEngine`` name. In the
current phase it delegates to :class:`~phoenix.processing.html_extractor.HTMLExtractor`;
full CSS/XPath selector set management will be added in later phases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from phoenix.processing.html_extractor import HTMLExtractor

if TYPE_CHECKING:
    from phoenix.models.document import RawResponse


class SelectorEngine:
    """Facade over HTML extraction for the public selector engine API."""

    def __init__(self) -> None:
        """Initialize the selector engine."""
        self._extractor = HTMLExtractor()

    async def extract(self, raw_response: RawResponse, platform: str) -> dict[str, Any]:
        """Extract structured data from ``raw_response`` for ``platform``.

        Args:
            raw_response: Raw HTML response from a scraper.
            platform: Platform identifier for the URL.

        Returns:
            Dictionary of extracted fields.
        """
        return await self._extractor.extract(raw_response, platform)


__all__ = ["SelectorEngine"]
