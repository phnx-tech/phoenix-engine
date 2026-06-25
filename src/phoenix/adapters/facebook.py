"""Facebook platform adapter for Phoenix Engine.

Extracts structured data from public Facebook pages and posts using CSS
selector fallback chains. No official Facebook API is used.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from phoenix.adapters.base import BaseAdapter
from phoenix.models.output import UnifiedOutput
from phoenix.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from phoenix.collectors.base import Collector
    from phoenix.models.document import RawResponse
    from phoenix.options import CollectionOptions


class FacebookAdapter(BaseAdapter):
    """Adapter for scraping public Facebook pages and posts."""

    _URL_PATTERNS: ClassVar[list[str]] = [
        r"https?://(?:www\.)?facebook\.com/[^/]+/posts/[^/]+",
        r"https?://(?:www\.)?facebook\.com/[^/]+/photos/[^/]+",
        r"https?://(?:www\.)?facebook\.com/[^/]+/videos/[^/]+",
        r"https?://(?:www\.)?facebook\.com/[^/]+/reel/[^/]+",
        r"https?://(?:www\.)?facebook\.com/pages/[^/]+",
        r"https?://(?:www\.)?facebook\.com/[^/]+",
    ]

    _PAGE_SELECTOR_SETS: ClassVar[dict[str, list[str]]] = {
        "name": [
            "h1.fb-page-name",
            ".fb-page-name",
            "[data-page-id] h1",
        ],
        "category": [
            ".fb-page-category",
            "[data-page-category]",
        ],
        "followers_count": [
            ".fb-followers-count",
            '.fb-page-counts [data-field="followers"]',
        ],
        "likes_count": [
            ".fb-likes-count",
            '.fb-page-counts [data-field="likes"]',
        ],
        "description": [
            ".fb-page-description",
            ".fb-page-about p",
        ],
        "website": [
            ".fb-page-website",
            ".fb-page-about a[href]",
        ],
    }

    _POST_SELECTOR_SETS: ClassVar[dict[str, list[str]]] = {
        "author": [
            ".fb-author.author-name",
            ".fb-author",
            "[data-author-name]",
        ],
        "text": [
            ".fb-user-content.post-caption p",
            ".fb-user-content",
            ".post-caption",
        ],
        "reaction_count": [
            ".fb-reaction-count.like-count",
            ".fb-reaction-count",
            ".like-count",
        ],
        "comment_count": [
            ".fb-comment-count.comment-count",
            ".fb-comment-count",
            ".comment-count",
        ],
        "share_count": [
            ".fb-share-count.share-count",
            ".fb-share-count",
            ".share-count",
        ],
    }

    _PRIVATE_INDICATORS: ClassVar[list[str]] = [
        "log in to",
        "login to",
        "sign in to",
        "signin to",
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
        "friends only",
        "only friends",
        "only available to friends",
        "this content isn't available right now",
    ]

    @property
    def manifest(self) -> PluginManifest:
        """Return the Facebook adapter manifest."""
        return PluginManifest(
            name="facebook",
            version="0.1.0",
            description="Scraper for public Facebook pages and posts.",
            author="Phoenix Engine Team",
            platforms=["facebook"],
            url_patterns=list(self._URL_PATTERNS),
            strategies=["browser", "http"],
            requires_auth=True,
            supports_ai_fallback=True,
        )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        """Return compiled URL patterns handled by this adapter."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in self._URL_PATTERNS]

    def preferred_strategies(self) -> list[str]:
        """Facebook is heavily JavaScript-rendered; prefer browser."""
        return ["browser", "http"]

    async def collect(
        self,
        url: str,
        _strategy: str,
        collector: Collector,
        options: CollectionOptions,
    ) -> RawResponse:
        """Collect raw HTML for ``url`` and flag non-public content."""
        raw_response = await collector.collect(url, options)
        if not self._is_public_content(raw_response.html):
            raw_response.error = {
                "code": "SCR_061",
                "message": "Authentication required -- this content is not publicly accessible.",
            }
        return raw_response

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract structured Facebook fields from ``raw_response``."""
        soup = BeautifulSoup(raw_response.html, "html.parser")
        url = raw_response.final_url or raw_response.url
        content_type = self._classify_url(url)

        if content_type in {"post", "video", "reel"}:
            return self._extract_post(soup, url, content_type)
        return self._extract_page(soup, url)

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Convert extracted Facebook fields into ``UnifiedOutput``."""
        content_type = extracted.get("content_type", "post")
        selectors_used = list(extracted.get("selectors_used", []))

        base_output: dict[str, Any] = {
            "url": url,
            "platform": self.manifest.platforms[0],
            "content_type": content_type,
            "scraping_strategy": strategy,
            "selectors_used": selectors_used,
        }

        if content_type == "profile":
            base_output.update(self._normalize_page(extracted, url))
        else:
            base_output.update(self._normalize_post(extracted, url))

        return UnifiedOutput(**base_output)

    def health_check(self) -> dict[str, Any]:
        """Return Facebook adapter health metadata."""
        base = super().health_check()
        base["requires_auth"] = self.manifest.requires_auth
        return base

    # ------------------------------------------------------------------
    # URL classification
    # ------------------------------------------------------------------

    def _classify_url(self, url: str) -> str:
        """Classify a Facebook URL into a content type."""
        path = urlparse(url).path.lower()
        if "/posts/" in path or "/photos/" in path:
            return "post"
        if "/videos/" in path:
            return "video"
        if "/reel/" in path:
            return "reel"
        return "profile"

    # ------------------------------------------------------------------
    # Page extraction
    # ------------------------------------------------------------------

    def _extract_page(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
        """Extract public Facebook page fields."""
        text_results = self._extract_with_selectors(soup, self._PAGE_SELECTOR_SETS)
        selectors_used = self._collect_selectors(text_results)

        website = self._extract_attribute(
            soup,
            self._PAGE_SELECTOR_SETS["website"],
            "href",
        )
        if website["selector_used"]:
            selectors_used.append(website["selector_used"])

        recent_posts = self._extract_recent_posts(soup)

        return {
            "content_type": "profile",
            "platform": "facebook",
            "url": url,
            "name": text_results["name"]["value"],
            "category": text_results["category"]["value"],
            "followers_count": self._parse_engagement(
                self._clean_count_text(text_results["followers_count"]["value"]),
            ),
            "likes_count": self._parse_engagement(
                self._clean_count_text(text_results["likes_count"]["value"]),
            ),
            "description": text_results["description"]["value"],
            "website": self._resolve_url(
                website["value"],
                url,
            ),
            "recent_posts": recent_posts,
            "selectors_used": selectors_used,
            "is_public": self._is_public_content(str(soup)),
        }

    def _extract_recent_posts(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract recent post previews from a page feed."""
        posts: list[dict[str, Any]] = []
        for post in soup.select(".fb-recent-posts .fb-post-preview"):
            post_id = post.get("data-post-id")
            text_el = post.select_one(".fb-post-preview-text")
            text = text_el.get_text(strip=True) if text_el else None
            posts.append(
                {
                    "post_id": str(post_id) if post_id else None,
                    "text": text,
                },
            )
        return posts

    # ------------------------------------------------------------------
    # Post extraction
    # ------------------------------------------------------------------

    def _extract_post(
        self,
        soup: BeautifulSoup,
        url: str,
        content_type: str = "post",
    ) -> dict[str, Any]:
        """Extract public Facebook post fields."""
        text_results = self._extract_with_selectors(soup, self._POST_SELECTOR_SETS)
        selectors_used = self._collect_selectors(text_results)

        post_id = self._extract_attribute(
            soup,
            ["article.fb-story[data-story-id]", ".fb-story[data-story-id]", "[data-story-id]"],
            "data-story-id",
        )
        if post_id["selector_used"]:
            selectors_used.append(post_id["selector_used"])

        timestamp = self._extract_attribute(
            soup,
            ["time.timestamp", "time", ".timestamp"],
            "datetime",
        )
        if timestamp["selector_used"]:
            selectors_used.append(timestamp["selector_used"])

        author_url = self._extract_author_url(soup, url)
        reactions_breakdown = self._extract_reactions_breakdown(soup)
        media_urls = self._extract_media_urls(soup, url)

        return {
            "content_type": content_type,
            "platform": "facebook",
            "url": url,
            "id": post_id["value"] or self._parse_post_id_from_url(url),
            "author": text_results["author"]["value"],
            "author_url": author_url,
            "text": text_results["text"]["value"],
            "timestamp": self._parse_iso_timestamp(timestamp["value"]),
            "reaction_count": self._parse_engagement(
                self._clean_count_text(text_results["reaction_count"]["value"]),
            ),
            "comment_count": self._parse_engagement(
                self._clean_count_text(text_results["comment_count"]["value"]),
            ),
            "share_count": self._parse_engagement(
                self._clean_count_text(text_results["share_count"]["value"]),
            ),
            "reactions_breakdown": reactions_breakdown,
            "media_urls": media_urls,
            "selectors_used": selectors_used,
            "is_public": self._is_public_content(str(soup)),
        }

    def _parse_post_id_from_url(self, url: str) -> str | None:
        """Parse the post ID from the URL path when not found in HTML."""
        parts = [p for p in urlparse(url).path.split("/") if p]
        if parts and parts[-1] not in {"posts", "photos", "videos", "reel"}:
            return parts[-1]
        return None

    def _extract_author_url(self, soup: BeautifulSoup, url: str) -> str | None:
        """Extract the author profile URL from the post."""
        link = soup.select_one(".fb-author-link[href]")
        if link and link.has_attr("href"):
            return self._resolve_url(str(link["href"]), url)
        return None

    def _extract_reactions_breakdown(
        self,
        soup: BeautifulSoup,
    ) -> dict[str, int | None]:
        """Extract individual reaction counts when visible."""
        reactions: dict[str, int | None] = {}
        for reaction_type in ("like", "love", "wow", "haha", "sad", "angry"):
            result = self._extract_with_selectors(
                soup,
                {
                    reaction_type: [f".fb-reaction-{reaction_type}"],
                },
            )
            reactions[reaction_type] = self._parse_engagement(
                result[reaction_type]["value"],
            )
        return reactions

    def _extract_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """Extract image/video URLs attached to the post."""
        urls: list[str] = []
        for img in soup.select(".fb-media img[src], .fb-media video[src]"):
            src = img.get("src")
            if src:
                resolved = self._resolve_url(str(src), url)
                if resolved:
                    urls.append(resolved)
        return urls

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    def _normalize_page(
        self,
        extracted: dict[str, Any],
        url: str,
    ) -> dict[str, Any]:
        """Map page fields to UnifiedOutput fields."""
        return {
            "title": extracted.get("name"),
            "text": extracted.get("description"),
            "author": extracted.get("name"),
            "author_url": url,
            "likes": extracted.get("likes_count"),
            "views": None,
            "comments": None,
            "shares": None,
            "media_urls": [],
            "thumbnail_url": None,
            "tags": [],
        }

    def _normalize_post(
        self,
        extracted: dict[str, Any],
        _url: str,
    ) -> dict[str, Any]:
        """Map post fields to UnifiedOutput fields."""
        text = extracted.get("text")
        title = text.split("\n")[0] if isinstance(text, str) and text else None
        media_urls = list(extracted.get("media_urls", []))
        return {
            "title": title,
            "text": text,
            "author": extracted.get("author"),
            "author_url": extracted.get("author_url"),
            "timestamp": extracted.get("timestamp"),
            "likes": extracted.get("reaction_count"),
            "shares": extracted.get("share_count"),
            "comments": extracted.get("comment_count"),
            "views": None,
            "media_urls": media_urls,
            "thumbnail_url": media_urls[0] if media_urls else None,
            "tags": [],
        }

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _extract_attribute(
        self,
        soup: BeautifulSoup,
        selectors: list[str],
        attribute: str,
    ) -> dict[str, Any]:
        """Extract an HTML attribute using selector fallback chains."""
        for selector in selectors:
            elements = soup.select(selector)
            if elements and elements[0].has_attr(attribute):
                return {
                    "value": str(elements[0][attribute]),
                    "selector_used": selector,
                    "matched": True,
                }
        return {"value": None, "selector_used": None, "matched": False}

    def _collect_selectors(
        self,
        results: dict[str, dict[str, Any]],
    ) -> list[str]:
        """Collect selectors that successfully matched."""
        selectors: list[str] = []
        for result in results.values():
            selector_used = result.get("selector_used")
            if selector_used:
                selectors.append(selector_used)
        return selectors

    def _resolve_url(self, value: str | None, base_url: str) -> str | None:
        """Resolve a possibly relative URL against ``base_url``."""
        if not value:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        return urljoin(base_url, stripped)

    def _parse_iso_timestamp(self, value: str | None) -> datetime | None:
        """Parse an ISO 8601 timestamp string into a UTC datetime."""
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.strip())
            return parsed.astimezone(UTC)
        except ValueError:
            return None

    def _is_public_content(self, html: str) -> bool:
        """Return ``True`` when ``html`` appears to be publicly accessible."""
        text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
        text_lower = text.lower()
        return not any(indicator in text_lower for indicator in self._PRIVATE_INDICATORS)

    def _clean_count_text(self, text: str | None) -> str | None:
        """Extract a leading numeric count such as ``1.2K`` from noisy text."""
        if not text:
            return None
        match = re.search(r"[\d\.,]+\s*[KMBkmb]?", text)
        if match:
            return match.group(0).strip()
        return None
