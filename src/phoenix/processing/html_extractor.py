"""HTML extractor for Phoenix Engine.

Extracts structured data from raw HTML using BeautifulSoup. Full selector
engine integration will be added in later phases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from phoenix.models.document import RawResponse


class HTMLExtractor:
    """Extracts structured data from parsed HTML."""

    def __init__(self) -> None:
        """Initialize the extractor."""
        return

    async def extract(self, raw_response: RawResponse, platform: str) -> dict[str, Any]:
        """Extract structured data from ``raw_response``.

        Args:
            raw_response: Raw HTML response from a collector.
            platform: Platform identifier for the URL.

        Returns:
            Dictionary of extracted fields with per-field confidence scores.
        """
        soup = BeautifulSoup(raw_response.html, "html.parser")
        title_tag = soup.find("title")
        body = soup.find("body")

        title = title_tag.get_text(strip=True) if title_tag else None
        text = ""
        if body:
            text = body.get_text(separator=" ", strip=True)

        # Simple Open Graph fallback for image
        og_image = soup.find("meta", property="og:image")
        media_urls: list[str] = []
        if og_image and og_image.get("content"):
            media_urls.append(str(og_image["content"]))

        selectors_used: list[str] = ["title", "body", "meta[property='og:image']"]

        return {
            "platform": platform,
            "url": raw_response.final_url or raw_response.url,
            "title": title,
            "title_confidence": _presence_confidence(title),
            "text": text,
            "text_confidence": _presence_confidence(text),
            "author": None,
            "author_confidence": 0.0,
            "media_urls": media_urls,
            "media_urls_confidence": _presence_confidence(media_urls),
            "selectors_used": selectors_used,
        }


def _presence_confidence(value: object) -> float:
    """Return a naive confidence based on whether ``value`` is present and non-empty."""
    if value is None:
        return 0.0
    if isinstance(value, str) and value.strip() == "":
        return 0.0
    if isinstance(value, list) and not value:
        return 0.0
    if isinstance(value, dict) and not value:
        return 0.0
    return 1.0


__all__ = ["HTMLExtractor"]
