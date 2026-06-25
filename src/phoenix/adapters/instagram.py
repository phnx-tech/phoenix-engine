"""Instagram platform adapter for Phoenix Engine.

Extracts public Instagram posts, Reels, and profiles from raw HTML using
CSS selector fallback chains. Never uses the Instagram API.
"""

from __future__ import annotations

import re
from datetime import datetime
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


class InstagramAdapter(BaseAdapter):
    """Adapter for public Instagram posts, Reels, and profiles."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the Instagram adapter manifest."""
        return PluginManifest(
            name="instagram",
            version="0.1.0",
            description="Pure HTML scraper for public Instagram posts, Reels, and profiles.",
            author="Phoenix Engine Team",
            platforms=["instagram"],
            url_patterns=[
                r"https?://(www\.)?instagram\.com/p/[^/]+/?",
                r"https?://(www\.)?instagram\.com/reel/[^/]+/?",
                r"https?://(www\.)?instagram\.com/[^/]+/?",
            ],
            strategies=["browser", "http"],
            requires_auth=False,
            supports_ai_fallback=True,
        )

    def supported_patterns(self) -> list[Pattern[str]]:
        """Return compiled Instagram URL patterns."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in self.manifest.url_patterns]

    def preferred_strategies(self) -> list[str]:
        """Instagram is JavaScript-heavy; prefer browser rendering."""
        return ["browser", "http"]

    async def collect(
        self,
        url: str,
        _strategy: str,
        collector: Collector,
        options: ScrapingOptions,
    ) -> RawResponse:
        """Collect raw HTML for ``url`` using the supplied ``collector``."""
        raw_response = await collector.collect(url, options)
        if not self._is_public_content(raw_response.html):
            raw_response.error = {
                "code": "SCR_020",
                "message": "Instagram content appears private or requires authentication.",
            }
        return raw_response

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract structured Instagram data from ``raw_response``."""
        soup = BeautifulSoup(raw_response.html, "html.parser")
        url = raw_response.final_url or raw_response.url

        if "/p/" in url:
            return self._extract_post(soup, url)
        if "/reel/" in url:
            return self._extract_reel(soup, url)
        return self._extract_profile(soup, url)

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Convert extracted Instagram fields into ``UnifiedOutput``."""
        output_data: dict[str, Any] = {
            "url": url,
            "platform": "instagram",
            "content_type": extracted.get("content_type", "post"),
            "title": extracted.get("title"),
            "text": extracted.get("caption") or extracted.get("text"),
            "author": extracted.get("author_username") or extracted.get("author"),
            "author_url": extracted.get("author_url"),
            "timestamp": extracted.get("timestamp"),
            "likes": extracted.get("likes_count") or extracted.get("likes"),
            "comments": extracted.get("comments_count") or extracted.get("comments"),
            "shares": extracted.get("shares_count"),
            "views": extracted.get("views_count") or extracted.get("view_count"),
            "media_urls": extracted.get("media_urls", []),
            "thumbnail_url": extracted.get("thumbnail_url"),
            "tags": extracted.get("tags", []),
            "scraping_strategy": strategy,
            "selectors_used": extracted.get("selectors_used", []),
        }

        # Preserve platform-specific extras.
        for key in ("post_type", "location", "mentions", "audio_attribution"):
            if key in extracted:
                output_data.setdefault("metadata", {})[key] = extracted[key]

        # Map profile-level counts to unified top-level fields.
        for key in ("follower_count", "following_count", "posts_count"):
            if key in extracted:
                output_data[key] = extracted[key]
                output_data.setdefault("metadata", {})[key] = extracted[key]

        return UnifiedOutput(**output_data)

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_post(self, soup: BeautifulSoup, _url: str) -> dict[str, Any]:
        """Extract fields from an Instagram post page."""
        selector_sets = {
            "caption": [
                "article._aatb div._a9zs h1",
                "article div[class*='_a9zs'] span",
                "meta[property='og:title']",
            ],
            "author_username": [
                "article._aatb header a",
                "article header a[href^='/']",
                "meta[property='og:title']",
            ],
            "timestamp": [
                "article._aatb time",
                "article time[datetime]",
            ],
            "likes_count": [
                "article._aatb section span",
                "article section span[class*='_aacl']",
            ],
            "comments_count": [
                "article._aatb a[href*='comments'] span",
                "article a[href*='comments']",
            ],
        }

        results = self._extract_with_selectors(soup, selector_sets)
        caption = self._first_text(results, "caption")
        # Use og:title as caption fallback if it exists.
        if not caption:
            caption = self._meta_content(soup, "og:title")

        author = self._first_text(results, "author_username")
        if author:
            author = author.lstrip("@").split()[0]

        likes = self._parse_number(self._first_text(results, "likes_count"))
        comments = self._parse_number(self._first_text(results, "comments_count"))

        timestamp = self._parse_timestamp(self._first_time_attr(results, soup))

        media_urls = self._extract_media_urls(soup)
        tags = self._extract_hashtags(caption or "")
        mentions = self._extract_mentions(caption or "")

        return {
            "content_type": "post",
            "caption": caption,
            "text": caption,
            "author_username": author,
            "author": author,
            "author_url": f"https://instagram.com/{author}" if author else None,
            "timestamp": timestamp,
            "likes_count": likes,
            "comments_count": comments,
            "media_urls": media_urls,
            "thumbnail_url": media_urls[0] if media_urls else None,
            "tags": tags,
            "mentions": mentions,
            "selectors_used": [
                results[field]["selector_used"]
                for field in selector_sets
                if results.get(field, {}).get("selector_used")
            ],
        }

    def _extract_reel(self, soup: BeautifulSoup, _url: str) -> dict[str, Any]:
        """Extract fields from an Instagram Reel page."""
        selector_sets = {
            "caption": [
                "div._a9zs span",
                "meta[property='og:title']",
            ],
            "author_username": [
                "header a[href^='/']",
                "meta[property='og:title']",
            ],
            "views_count": [
                "span._aacl",
            ],
            "likes_count": [
                "section span._aacl",
                "span[class*='_aacl']",
            ],
            "timestamp": [
                "time[datetime]",
            ],
        }

        results = self._extract_with_selectors(soup, selector_sets)
        caption = self._first_text(results, "caption")
        if not caption:
            caption = self._meta_content(soup, "og:title")

        author = self._first_text(results, "author_username")
        if author:
            author = author.lstrip("@").split()[0]

        views = self._parse_number(self._first_text(results, "views_count"))
        likes = self._parse_number(self._first_text(results, "likes_count"))
        timestamp = self._parse_timestamp(self._first_time_attr(results, soup))

        media_urls = self._extract_media_urls(soup)
        tags = self._extract_hashtags(caption or "")

        return {
            "content_type": "reel",
            "caption": caption,
            "text": caption,
            "author_username": author,
            "author": author,
            "author_url": f"https://instagram.com/{author}" if author else None,
            "timestamp": timestamp,
            "views_count": views,
            "likes_count": likes,
            "media_urls": media_urls,
            "thumbnail_url": media_urls[0] if media_urls else None,
            "tags": tags,
            "audio_attribution": self._meta_content(soup, "og:title"),
            "selectors_used": [
                results[field]["selector_used"]
                for field in selector_sets
                if results.get(field, {}).get("selector_used")
            ],
        }

    def _extract_profile(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
        """Extract fields from an Instagram profile page."""
        selector_sets = {
            "display_name": [
                "header h2",
                "header h1",
                "meta[property='og:title']",
            ],
            "bio": [
                "header div._aa_c",
                "header span[class*='_aa_c']",
                "meta[property='og:description']",
            ],
            "follower_count": [
                "header ul li span",
            ],
            "following_count": [
                "header ul li span",
            ],
            "post_count": [
                "header ul li span",
            ],
        }

        results = self._extract_with_selectors(soup, selector_sets)
        username = self._extract_username_from_url(url)
        display_name = self._first_text(results, "display_name") or username
        bio = self._first_text(results, "bio")
        if not bio:
            bio = self._meta_content(soup, "og:description")

        followers, following, posts = self._parse_profile_stats(soup)

        thumbnails = self._extract_thumbnail_grid(soup)

        return {
            "content_type": "profile",
            "title": display_name,
            "text": bio,
            "author_username": username,
            "author": username,
            "author_url": url,
            "follower_count": followers,
            "following_count": following,
            "posts_count": posts,
            "recent_post_thumbnails": thumbnails,
            "media_urls": thumbnails[:12],
            "selectors_used": [
                results[field]["selector_used"]
                for field in selector_sets
                if results.get(field, {}).get("selector_used")
            ],
        }

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _first_text(self, results: dict[str, Any], field: str) -> str | None:
        """Return the extracted text for ``field`` or ``None``."""
        value = results.get(field, {}).get("value")
        return value.strip() if value else None

    def _first_time_attr(
        self,
        results: dict[str, Any],
        soup: BeautifulSoup,
    ) -> str | None:
        """Return the datetime attribute of the first matched ``time`` tag."""
        selector_used = results.get("timestamp", {}).get("selector_used")
        if not selector_used:
            return None
        elements = soup.select(selector_used)
        if not elements:
            return None
        time_tag = elements[0]
        if time_tag.name == "time":
            return str(time_tag.get("datetime", "")).strip() or None
        return time_tag.get_text(strip=True) or None

    def _meta_content(self, soup: BeautifulSoup, property_name: str) -> str | None:
        """Return the content of a meta tag with ``property`` attribute."""
        tag = soup.find("meta", property=property_name)
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
        return None

    def _parse_timestamp(self, text: str | None) -> datetime | None:
        """Parse an ISO timestamp string into a datetime."""
        if not text:
            return None
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    def _extract_media_urls(self, soup: BeautifulSoup) -> list[str]:
        """Extract image URLs from meta tags and img elements."""
        urls: list[str] = []
        og_image = self._meta_content(soup, "og:image")
        if og_image:
            urls.append(og_image)

        for img in soup.find_all("img"):
            src = img.get("src")
            if src and isinstance(src, str) and src.startswith("http"):
                urls.append(src)

        return list(dict.fromkeys(urls))

    def _extract_thumbnail_grid(self, soup: BeautifulSoup) -> list[str]:
        """Extract recent post thumbnail URLs from a profile grid."""
        urls: list[str] = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and isinstance(src, str) and src.startswith("http"):
                urls.append(src)
        return list(dict.fromkeys(urls))[:12]

    def _extract_hashtags(self, text: str) -> list[str]:
        """Return hashtags found in ``text``."""
        return re.findall(r"#\w+", text)

    def _extract_mentions(self, text: str) -> list[str]:
        """Return @mentions found in ``text``."""
        return re.findall(r"@\w+", text)

    def _extract_username_from_url(self, url: str) -> str | None:
        """Extract Instagram username from a profile URL."""
        match = re.search(r"instagram\.com/([^/?#]+)/?", url)
        if match and match.group(1) not in ("p", "reel", "tv", "accounts"):
            return match.group(1)
        return None

    def _parse_number(self, text: str | None) -> int | None:
        """Parse a numeric count, stripping platform-specific words."""
        if text is None:
            return None
        # Remove words like "likes", "comments", "views", "followers".
        cleaned = re.sub(
            r"\b(likes?|comments?|views?|followers?|following|posts?)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        return self._parse_engagement(cleaned.strip())

    def _parse_profile_stats(
        self,
        soup: BeautifulSoup,
    ) -> tuple[int | None, int | None, int | None]:
        """Parse follower/following/post counts from a profile header."""
        followers: int | None = None
        following: int | None = None
        posts: int | None = None

        for li in soup.find_all("li"):
            text = li.get_text(separator=" ", strip=True).lower()
            span = li.find("span")
            value = self._parse_number(span.get_text(strip=True)) if span else None

            if "follower" in text:
                followers = value
            elif "following" in text:
                following = value
            elif "post" in text:
                posts = value

        return followers, following, posts


__all__ = ["InstagramAdapter"]
