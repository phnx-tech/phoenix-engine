"""Researcher role for PhoenixArchitect.

Discovers candidate URLs from a natural-language query using search engines.
The default backend is DuckDuckGo via the ``duckduckgo-search`` package, with
an optional SerpAPI fallback when ``SERPAPI_KEY`` is configured.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, ClassVar
from urllib.parse import urlparse

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover
    DDGS = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single URL discovered by the Researcher."""

    url: str
    title: str
    snippet: str
    rank: int
    engine: str


class Researcher:
    """Search-driven URL discovery for PhoenixArchitect."""

    # Domains that are rarely useful as scraping targets.
    _BLOCKED_DOMAINS: ClassVar[set[str]] = {
        "youtube.com",
        "youtu.be",
        "facebook.com",
        "instagram.com",
        "tiktok.com",
        "twitter.com",
        "x.com",
        "linkedin.com",
    }

    def __init__(self, max_results: int = 10) -> None:
        """Initialize the researcher.

        Args:
            max_results: Maximum number of results to return per search.
        """
        self._max_results = max_results

    async def discover(
        self,
        query: str,
        *,
        engine: str = "duckduckgo",
        max_results: int | None = None,
    ) -> list[SearchResult]:
        """Return candidate URLs for ``query``.

        Args:
            query: Search query (keyword, dork, or natural-language goal).
            engine: Search engine to use. Supports ``duckduckgo`` and ``serpapi``.
            max_results: Override the default result limit.

        Returns:
            Ordered list of unique candidate URLs.
        """
        limit = max_results if max_results is not None else self._max_results
        if engine == "serpapi":
            return await self._search_serpapi(query, limit)
        if engine == "duckduckgo":
            return await self._search_duckduckgo(query, limit)
        raise ValueError(f"Unsupported search engine: {engine!r}")

    async def _search_duckduckgo(self, query: str, max_results: int) -> list[SearchResult]:
        """Search DuckDuckGo and return parsed results."""
        if DDGS is None:
            logger.warning("duckduckgo-search is not installed")
            return []

        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(self._ddgs_text, query, max_results),
                timeout=30.0,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("DuckDuckGo search failed: %s", exc)
            return []

        return self._normalize_results(results, engine="duckduckgo", max_results=max_results)

    def _ddgs_text(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Synchronous wrapper around ``DDGS().text``."""
        with DDGS() as ddgs:
            return ddgs.text(query, max_results=max_results) or []

    async def _search_serpapi(self, query: str, max_results: int) -> list[SearchResult]:
        """Search via SerpAPI when ``SERPAPI_KEY`` is present."""
        api_key = os.environ.get("SERPAPI_KEY")
        if not api_key:
            logger.warning("SERPAPI_KEY is not set; skipping SerpAPI search")
            return []

        try:
            import httpx  # noqa: PLC0415
        except ImportError:  # pragma: no cover
            return []

        params: dict[str, Any] = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": max_results,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get("https://serpapi.com/search", params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("SerpAPI search failed: %s", exc)
            return []

        organic = data.get("organic_results", []) if isinstance(data, dict) else []
        results = [
            {
                "href": item.get("link", ""),
                "title": item.get("title", ""),
                "body": item.get("snippet", ""),
            }
            for item in organic
            if isinstance(item, dict)
        ]
        return self._normalize_results(results, engine="serpapi", max_results=max_results)

    def _normalize_results(
        self,
        raw_results: list[dict[str, Any]],
        *,
        engine: str,
        max_results: int,
    ) -> list[SearchResult]:
        """Filter, dedupe, and rank raw search results."""
        seen: set[str] = set()
        normalized: list[SearchResult] = []
        rank = 0
        for item in raw_results:
            url = str(item.get("href", "")).strip()
            if not self._is_usable_url(url):
                continue
            if url in seen:
                continue
            seen.add(url)
            normalized.append(
                SearchResult(
                    url=url,
                    title=str(item.get("title", "")),
                    snippet=str(item.get("body", "")),
                    rank=rank,
                    engine=engine,
                ),
            )
            rank += 1
            if len(normalized) >= max_results:
                break
        return normalized

    def _is_usable_url(self, url: str) -> bool:
        """Return ``True`` when ``url`` looks like a public HTTP(S) target."""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = parsed.netloc.split(":", 1)[0].lower().removeprefix("www.")
        if not host:
            return False
        return host not in self._BLOCKED_DOMAINS


__all__ = ["Researcher", "SearchResult"]
