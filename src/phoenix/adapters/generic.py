"""Generic web adapter for unknown HTTP(S) URLs.

This adapter acts as the catch-all scraper for any URL that is not handled by
a platform-specific adapter. It extracts basic article/blog metadata using
Open Graph tags, schema.org JSON-LD, and content-density heuristics.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from phoenix.adapters.base import BaseAdapter
from phoenix.plugins.manifest import PluginManifest
from phoenix.processing.html_extractor import HTMLExtractor
from phoenix.processing.normalizer import Normalizer

if TYPE_CHECKING:
    from phoenix.collectors.base import Collector
    from phoenix.models.document import RawResponse
    from phoenix.models.output import UnifiedOutput
    from phoenix.options import CollectionOptions


class GenericWebAdapter(BaseAdapter):
    """Catch-all adapter for any public HTTP(S) webpage."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the generic web adapter manifest."""
        return PluginManifest(
            name="generic_web",
            version="0.1.0",
            description="Catch-all adapter for generic HTTP(S) webpages.",
            author="Phoenix Engine Team",
            platforms=["generic"],
            url_patterns=[r"https?://.+"],
            strategies=["http", "browser"],
            requires_auth=False,
            supports_ai_fallback=True,
        )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        """Return the generic HTTP(S) URL pattern."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in self.manifest.url_patterns]

    def preferred_strategies(self) -> list[str]:
        """Generic pages prefer direct HTTP; browser is a fallback."""
        return ["http", "browser"]

    async def collect(
        self,
        url: str,
        strategy: str,
        collector: Collector,
        options: CollectionOptions,
    ) -> RawResponse:
        """Collect ``url`` using the supplied ``collector``.

        The generic adapter delegates collection to the strategy-specific
        collector and performs a public-content sanity check on the result.
        """
        raw_response = await collector.collect(url, options)
        if not self._is_public_content(raw_response.html):
            raw_response.error = {
                "code": "SCR_020",
                "message": "Content appears to require authentication or is not public.",
            }
        return raw_response

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract generic article metadata from ``raw_response``.

        Uses the shared :class:`HTMLExtractor` for basic fields and augments
        the result with Open Graph / JSON-LD metadata when available.
        """
        extractor = HTMLExtractor()
        base = await extractor.extract(raw_response, self.manifest.platforms[0])

        soup = BeautifulSoup(raw_response.html, "html.parser")
        metadata = self._extract_metadata(soup)

        # Structured metadata (Open Graph / JSON-LD) takes precedence over
        # basic HTML extraction for these fields.
        for key in ("title", "author", "description", "site_name", "published_date"):
            if key in metadata:
                base[key] = metadata[key]

        # Merge media URLs and deduplicate while preserving order.
        base_media = list(base.get("media_urls", []))
        structured_media = list(metadata.get("media_urls", []))
        base["media_urls"] = list(dict.fromkeys(structured_media + base_media))

        # Ensure content text is reasonably clean.
        base["text"] = self._clean_text(soup)

        return base

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Normalize extracted generic-web fields into ``UnifiedOutput``."""
        normalizer = Normalizer()
        return await normalizer.normalize(
            extracted,
            self.manifest.platforms[0],
            url,
            strategy,
        )

    def health_check(self) -> dict[str, Any]:
        """Return generic adapter health metadata."""
        base = super().health_check()
        base["catch_all"] = True
        return base

    # ------------------------------------------------------------------
    # Generic extraction helpers
    # ------------------------------------------------------------------

    def _extract_metadata(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract Open Graph and JSON-LD metadata from ``soup``."""
        metadata: dict[str, Any] = {}

        # Open Graph
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        og_image = soup.find("meta", property="og:image")
        og_site = soup.find("meta", property="og:site_name")

        if og_title and og_title.get("content"):
            metadata["title"] = str(og_title["content"]).strip()
        if og_desc and og_desc.get("content"):
            metadata["description"] = str(og_desc["content"]).strip()
        if og_image and og_image.get("content"):
            metadata.setdefault("media_urls", []).append(str(og_image["content"]))
        if og_site and og_site.get("content"):
            metadata["site_name"] = str(og_site["content"]).strip()

        # Schema.org JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(data, dict):
                self._merge_jsonld(metadata, data)

        return metadata

    def _merge_jsonld(self, metadata: dict[str, Any], data: dict[str, Any]) -> None:
        """Merge JSON-LD structured data into ``metadata``."""
        if "headline" in data and "title" not in metadata:
            metadata["title"] = data["headline"]
        if "author" in data:
            author = data["author"]
            if isinstance(author, dict):
                metadata["author"] = author.get("name")
            elif isinstance(author, list) and author:
                first = author[0]
                if isinstance(first, dict):
                    metadata["author"] = first.get("name")
        if "datePublished" in data:
            metadata["published_date"] = data["datePublished"]
        if "publisher" in data and isinstance(data["publisher"], dict):
            metadata.setdefault("site_name", data["publisher"].get("name"))

    def _clean_text(self, soup: BeautifulSoup) -> str:
        """Return cleaned page text with navigation/footer noise reduced."""
        # Drop script/style/nav/footer/header/aside tags
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main is None:
            return soup.get_text(separator=" ", strip=True)

        text = main.get_text(separator=" ", strip=True)
        # Collapse whitespace
        return re.sub(r"\s+", " ", text).strip()


__all__ = ["GenericWebAdapter"]
