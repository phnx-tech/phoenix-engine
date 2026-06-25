"""PhoenixArchitect Inspector role.

Analyzes collected page snapshots and produces a structured site spec that
tells the Coder what to build.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from phoenix.architect.explorer import PageSnapshot
    from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor


class Inspector:
    """Inspect snapshots and emit a site analysis spec."""

    def __init__(self, extractor: PhoenixAIExtractor) -> None:
        """Initialize the inspector with a Phoenix AI extractor.

        Args:
            extractor: AI extractor used to analyze HTML and produce the spec.
        """
        self._extractor = extractor

    async def inspect(
        self,
        snapshots: list[PageSnapshot],
        url: str,
    ) -> dict[str, Any]:
        """Analyze ``snapshots`` and return a site spec for ``url``.

        Args:
            snapshots: Collected page snapshots from the target site.
            url: Original target URL.

        Returns:
            Site spec with ``platform_name``, ``content_type``,
            ``data_fields``, ``data_location``, ``selectors``,
            ``url_patterns``, and ``notes``.
        """
        if not snapshots:
            return self._empty_spec(url)

        sample = snapshots[0]
        schema = (
            "Return a JSON object with exactly these fields:\n"
            "  platform_name: short unique snake_case identifier for this site\n"
            "  content_type: one of: real_estate, e_commerce, news, jobs, "
            "generic, article, product, profile, post, video\n"
            "  data_fields: list of field names to extract (e.g. title, price, "
            "author, description)\n"
            "  data_location: where the data lives - one of: __NEXT_DATA__, "
            "JSON-LD, meta_tags, css_selectors, mixed\n"
            "  selectors: dict of field name to plain CSS selector compatible "
            "with BeautifulSoup's soup.select() (only when data_location is "
            "css_selectors or mixed). Do NOT use Scrapy pseudo selectors such "
            "as ::text or ::attr(href); select the element and read the "
            "attribute in code instead.\n"
            "  url_patterns: list of regex patterns this adapter should match\n"
            "  notes: brief observations about the page structure"
        )
        result = await self._extractor.extract(
            html=sample.html[:24000],
            url=url,
            platform="unknown",
            content_type="unknown",
            schema_description=schema,
            strict=False,
        )
        if isinstance(result, list) and result:
            result = result[0]
        if not isinstance(result, dict):
            return self._empty_spec(url)

        return self._normalize_spec(result, url)

    @staticmethod
    def _empty_spec(url: str) -> dict[str, Any]:
        """Return a minimal spec when inspection cannot run."""
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").replace(".", "_")
        return {
            "platform_name": domain or "generated_site",
            "content_type": "generic",
            "data_fields": ["title", "text", "author"],
            "data_location": "css_selectors",
            "selectors": {},
            "url_patterns": [rf"https?://(?:www\.)?{parsed.netloc}/.+"],
            "notes": "No snapshots available; fallback spec.",
        }

    @staticmethod
    def _normalize_spec(result: dict[str, Any], url: str) -> dict[str, Any]:
        """Ensure the spec contains all expected keys."""
        parsed = urlparse(url)
        default_patterns = [rf"https?://(?:www\.)?{parsed.netloc}/.+"]
        return {
            "platform_name": str(result.get("platform_name", "generated_site")),
            "content_type": str(result.get("content_type", "generic")),
            "data_fields": list(result.get("data_fields", ["title", "text"])),
            "data_location": str(result.get("data_location", "css_selectors")),
            "selectors": dict(result.get("selectors", {})) if result.get("selectors") else {},
            "url_patterns": list(result.get("url_patterns", default_patterns)),
            "notes": str(result.get("notes", "")),
        }


__all__ = ["Inspector"]
