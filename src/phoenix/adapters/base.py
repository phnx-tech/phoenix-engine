"""Abstract base class and plugin interface for Phoenix Engine adapters.

Adapters are self-contained platform scrapers that define how to collect,
extract, and normalize public HTML content for a specific site or family of
sites. The core engine discovers adapters through :class:`PluginLoader` and
routes URLs to them without modifying core code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from re import Pattern

    from phoenix.collectors.base import Collector
    from phoenix.models.document import RawResponse
    from phoenix.models.output import UnifiedOutput
    from phoenix.options import CollectionOptions
    from phoenix.plugins.manifest import PluginManifest


class BaseAdapter(ABC):
    """Abstract contract implemented by every Phoenix Engine adapter."""

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest describing this adapter."""

    @abstractmethod
    def supported_patterns(self) -> list[Pattern[str]]:
        """Return compiled URL regex patterns handled by this adapter."""

    def preferred_strategies(self) -> list[str]:
        """Return the ordered list of preferred collection strategies.

        Defaults to ``["http", "browser"]`` so fast direct HTTP is attempted
        first, with headless browser rendering as a fallback.
        """
        return ["http", "browser"]

    @abstractmethod
    async def collect(
        self,
        url: str,
        strategy: str,
        collector: Collector,
        options: CollectionOptions,
    ) -> RawResponse:
        """Collect raw HTML for ``url`` using the supplied ``collector``.

        Args:
            url: Target URL to collect.
            strategy: Strategy identifier selected for this collection.
            collector: Concrete collector implementing the strategy.
            options: Collection options such as timeout and archive flags.

        Returns:
            A raw response containing HTML, status, headers, and metadata.
        """

    @abstractmethod
    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract structured platform-specific fields from ``raw_response``.

        Args:
            raw_response: Raw HTML response produced by a collector.

        Returns:
            Dictionary of extracted fields. The exact keys are platform-
            specific; the adapter's ``normalize`` method maps them to the
            unified schema.
        """

    @abstractmethod
    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Convert extracted fields into the unified output schema.

        Args:
            extracted: Dictionary returned by :meth:`extract`.
            url: Normalized source URL.
            strategy: Collection strategy that produced the raw response.

        Returns:
            A validated ``UnifiedOutput`` instance.
        """

    def health_check(self) -> dict[str, Any]:
        """Return adapter health and diagnostic metadata.

        Subclasses may override this to include selector health, session
        status, or other platform-specific diagnostics.
        """
        return {
            "adapter": self.manifest.name,
            "version": self.manifest.version,
            "platforms": self.manifest.platforms,
            "url_patterns": len(self.manifest.url_patterns),
            "strategies": self.preferred_strategies(),
            "requires_auth": self.manifest.requires_auth,
            "supports_ai_fallback": self.manifest.supports_ai_fallback,
        }

    # ------------------------------------------------------------------
    # Shared utility methods for adapter authors
    # ------------------------------------------------------------------

    def _is_public_content(self, html: str) -> bool:
        """Return ``True`` when ``html`` appears to be publicly accessible.

        This is a heuristic guard used by adapters to avoid extracting data
        from login walls or private/error pages. It looks for common phrases
        that indicate authentication is required or the content is not public.
        """
        text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
        text_lower = text.lower()

        private_indicators = [
            "log in to",
            "login to",
            "sign in to",
            "signin to",
            "authentication required",
            "this content isn't available",
            "this page isn't available",
            "page not found",
            "sorry, this page isn't available",
            "please log in",
            "please sign in",
            "you must log in",
            "you must sign in",
            "members only",
            "private group",
            "this account is private",
            "this profile is private",
        ]

        return not any(indicator in text_lower for indicator in private_indicators)

    def _extract_with_selectors(
        self,
        soup: BeautifulSoup,
        selector_sets: dict[str, list[str]],
    ) -> dict[str, Any]:
        """Extract fields from ``soup`` using ordered selector fallback chains.

        Args:
            soup: Parsed BeautifulSoup document.
            selector_sets: Mapping of field name to ordered list of CSS
                selectors. Each field is resolved by trying selectors in order
                and returning the first successful match.

        Returns:
            Dictionary with field names as keys. Values are dictionaries
            containing ``value`` (extracted text or ``None``), ``selector_used``,
            and ``matched``.
        """
        results: dict[str, Any] = {}
        for field, selectors in selector_sets.items():
            value: str | None = None
            selector_used: str | None = None
            matched = False
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    first = elements[0]
                    value = first.get_text(strip=True) if first.name else str(first)
                    selector_used = selector
                    matched = True
                    break
            results[field] = {
                "value": value,
                "selector_used": selector_used,
                "matched": matched,
                "confidence": 1.0 if matched else 0.0,
            }
        return results

    def _parse_engagement(self, text: str | None) -> int | None:
        """Parse an engagement count string into an integer.

        Supports counts with suffixes such as ``1.2K``, ``3M``, and comma
        separators. Returns ``None`` for empty or unparseable input.

        Examples:
            ``"1.2K"`` -> ``1200``
            ``"3M"`` -> ``3000000``
            ``"1,234"`` -> ``1234``
        """
        if text is None:
            return None

        cleaned = text.strip().lower().replace(",", "")
        if not cleaned:
            return None

        multiplier = 1
        if cleaned.endswith("k"):
            multiplier = 1_000
            cleaned = cleaned[:-1]
        elif cleaned.endswith("m"):
            multiplier = 1_000_000
            cleaned = cleaned[:-1]
        elif cleaned.endswith("b"):
            multiplier = 1_000_000_000
            cleaned = cleaned[:-1]

        try:
            return int(float(cleaned) * multiplier)
        except ValueError:
            return None


# ``PluginInterface`` is provided as a synonym for authors who prefer that name.
PluginInterface = BaseAdapter

# ``ScraperPlugin`` is the public name used in Architecture v2.0.0 / API Spec v2.0.0.
ScraperPlugin = BaseAdapter


__all__ = ["BaseAdapter", "PluginInterface", "ScraperPlugin"]
