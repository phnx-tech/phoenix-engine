"""TikTok platform adapter for Phoenix Engine.

Extracts public video and profile metadata from TikTok HTML using selector
fallback chains. No official TikTok API is used.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ClassVar

from bs4 import BeautifulSoup, Tag

from phoenix.adapters.base import BaseAdapter
from phoenix.models.output import UnifiedOutput
from phoenix.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from re import Pattern

    from phoenix.collectors.base import Collector
    from phoenix.models.document import RawResponse
    from phoenix.options import CollectionOptions


class TikTokAdapter(BaseAdapter):
    """Adapter for public TikTok videos and profiles."""

    _URL_PATTERNS: ClassVar[list[str]] = [
        r"https?://(www\.)?tiktok\.com/@[^/]+/video/\d+",
        r"https?://(www\.)?tiktok\.com/video/\d+",
        r"https?://(www\.)?tiktok\.com/@[^/]+/?$",
    ]

    @property
    def manifest(self) -> PluginManifest:
        """Return the TikTok adapter manifest."""
        return PluginManifest(
            name="tiktok",
            version="0.1.0",
            description="Pure-scraping adapter for public TikTok videos and profiles.",
            author="Phoenix Engine Team",
            platforms=["tiktok"],
            url_patterns=self._URL_PATTERNS,
            strategies=["browser", "http"],
            requires_auth=False,
            supports_ai_fallback=True,
        )

    def supported_patterns(self) -> list[Pattern[str]]:
        """Return compiled URL regex patterns handled by this adapter."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in self._URL_PATTERNS]

    def preferred_strategies(self) -> list[str]:
        """TikTok is heavily JavaScript-rendered; prefer browser."""
        return ["browser", "http"]

    async def collect(
        self,
        url: str,
        _strategy: str,
        collector: Collector,
        options: CollectionOptions,
    ) -> RawResponse:
        """Collect ``url`` using the supplied ``collector``.

        Delegates to the strategy-specific collector and flags login walls or
        private content when detected.
        """
        raw_response = await collector.collect(url, options)
        if not self._is_public_content(raw_response.html):
            raw_response.error = {
                "code": "SCR_020",
                "message": "Content appears to require authentication or is not public.",
            }
        return raw_response

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract structured TikTok fields from ``raw_response``.

        Uses selector fallback chains for resilience against TikTok layout
        changes. Returns video or profile data depending on the URL and HTML
        structure.
        """
        soup = BeautifulSoup(raw_response.html, "html.parser")
        content_type = self._detect_content_type(raw_response.url, soup)

        data = self._extract_video(soup) if content_type == "video" else self._extract_profile(soup)

        data["content_type"] = content_type
        data["url"] = raw_response.url
        data["_platform"] = "tiktok"
        data["_strategy"] = raw_response.strategy
        return data

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Convert extracted TikTok fields into ``UnifiedOutput``."""
        content_type = extracted.get("content_type", "post")
        selectors_used: list[str] = []
        for result in extracted.get("_selector_results", {}).values():
            selector_used = result.get("selector_used")
            if selector_used and selector_used not in selectors_used:
                selectors_used.append(selector_used)

        base: dict[str, Any] = {
            "url": url,
            "platform": "tiktok",
            "content_type": content_type,
            "scraping_strategy": strategy,
            "selectors_used": selectors_used,
            "ai_assisted": False,
        }

        if content_type == "video":
            base.update(self._normalize_video(extracted))
        elif content_type == "profile":
            base.update(self._normalize_profile(extracted))

        warnings = extracted.get("_warnings", [])
        partial_reasons = extracted.get("_partial_reasons", [])
        if warnings:
            base["_warnings"] = warnings
        if partial_reasons:
            base["_partial_reasons"] = partial_reasons
            base["data_completeness"] = "partial"

        return UnifiedOutput(**base)

    # ------------------------------------------------------------------
    # Content type detection
    # ------------------------------------------------------------------

    def _detect_content_type(self, url: str, soup: BeautifulSoup) -> str:
        """Detect whether the page represents a video or profile."""
        if "/video/" in url.lower():
            return "video"
        if soup.select_one(".tt-profile-page, [data-e2e='user-page']") is not None:
            return "profile"
        if soup.select_one(".tt-video-page, [data-e2e='video-page']") is not None:
            return "video"
        return "profile" if url.rstrip("/").rsplit("/", 1)[-1].startswith("@") else "video"

    # ------------------------------------------------------------------
    # Video extraction
    # ------------------------------------------------------------------

    def _extract_video(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract TikTok video metadata using selector fallback chains."""
        text_selectors: dict[str, list[str]] = {
            "description": [
                "h1[data-e2e='browse-video-desc']",
                ".tt-caption p",
                ".post-caption p",
                "meta[property='og:description']",
            ],
            "author_username": [
                "a.tt-author-link .tt-username",
                ".tt-author-link .author-name",
                ".author-name",
                "meta[property='og:url']",
            ],
            "play_count": [
                "strong[data-e2e='play-count']",
                ".tt-views",
                ".view-count",
            ],
            "like_count": [
                "strong[data-e2e='like-count']",
                ".tt-likes",
                ".like-count",
            ],
            "comment_count": [
                "strong[data-e2e='comment-count']",
                ".tt-comments",
                ".comment-count",
            ],
            "share_count": [
                "strong[data-e2e='share-count']",
                ".tt-shares",
                ".share-count",
            ],
            "music_title": [
                "h4[data-e2e='music-title']",
                ".tt-sound-title",
                ".music-info .title",
            ],
            "timestamp": [
                "time.timestamp",
                "time[datetime]",
                ".tt-video-date",
            ],
        }

        values, selector_results, warnings, partial_reasons = self._run_selector_chains(
            soup,
            text_selectors,
        )

        video_id = self._extract_first_attribute(
            soup,
            [
                ("article[data-video-id]", "data-video-id"),
                ("[data-video-id]", "data-video-id"),
            ],
        )
        if video_id is None:
            partial_reasons.append("video_id: no matching selectors found")
        else:
            values["video_id"] = video_id
            selector_results["video_id"] = {
                "value": video_id,
                "selector_used": "article[data-video-id]",
                "matched": True,
            }

        video_url = self._extract_attribute_chain(
            soup,
            "video.post-media",
            "src",
            fallbacks=["video", "meta[property='og:video']"],
        )
        thumbnail_url = self._extract_attribute_chain(
            soup,
            "video.post-media",
            "poster",
            fallbacks=["meta[property='og:image']"],
        )
        duration = self._extract_attribute_chain(
            soup,
            "video.post-media",
            "data-duration",
            fallbacks=["video", "meta[property='og:video:duration']"],
        )

        if video_url:
            values["video_url"] = video_url
            selector_results.setdefault(
                "video_url",
                {
                    "value": video_url,
                    "selector_used": "video.post-media",
                    "matched": True,
                },
            )
        if thumbnail_url:
            values["thumbnail_url"] = thumbnail_url
        if duration is not None:
            values["duration"] = self._parse_duration(duration)

        description_text = values.get("description", "") or ""
        values["hashtags"] = self._extract_hashtags(description_text)

        values["music_info"] = {
            "title": values.pop("music_title", None),
        }

        values["play_count"] = self._clean_count(values.get("play_count"))
        values["like_count"] = self._clean_count(values.get("like_count"))
        values["comment_count"] = self._clean_count(values.get("comment_count"))
        values["share_count"] = self._clean_count(values.get("share_count"))
        values["timestamp"] = self._parse_timestamp(values.get("timestamp"))

        author_url = values.get("author_url")
        if author_url is None and values.get("author_username"):
            author_url = f"https://www.tiktok.com/@{values['author_username'].lstrip('@')}"
            values["author_url"] = author_url

        values["_selector_results"] = selector_results
        values["_warnings"] = warnings
        values["_partial_reasons"] = partial_reasons
        return values

    # ------------------------------------------------------------------
    # Profile extraction
    # ------------------------------------------------------------------

    def _extract_profile(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract TikTok profile metadata using selector fallback chains."""
        text_selectors: dict[str, list[str]] = {
            "username": [
                "h1[data-e2e='user-title']",
                ".tt-username",
                ".profile-username",
            ],
            "display_name": [
                "h2[data-e2e='user-subtitle']",
                ".tt-nickname",
                ".profile-display-name",
            ],
            "bio": [
                "p[data-e2e='user-bio']",
                ".tt-bio",
                ".profile-bio",
            ],
            "follower_count": [
                "strong[data-e2e='followers-count']",
                ".tt-followers",
                ".follower-count",
            ],
            "following_count": [
                "strong[data-e2e='following-count']",
                ".tt-following",
                ".following-count",
            ],
            "likes_count": [
                "strong[data-e2e='likes-count']",
                ".tt-likes",
                ".likes-count",
            ],
            "video_count": [
                "strong[data-e2e='video-count']",
                ".tt-videos",
                ".video-count",
            ],
        }

        values, selector_results, warnings, partial_reasons = self._run_selector_chains(
            soup,
            text_selectors,
        )

        recent_videos = self._extract_recent_videos(soup)
        values["recent_videos"] = recent_videos
        selector_results["recent_videos"] = {
            "value": str(len(recent_videos)),
            "selector_used": ".tt-video-item",
            "matched": bool(recent_videos),
        }
        if not recent_videos:
            partial_reasons.append("recent_videos: no matching selectors found")

        values["follower_count"] = self._clean_count(values.get("follower_count"))
        values["following_count"] = self._clean_count(values.get("following_count"))
        values["likes_count"] = self._clean_count(values.get("likes_count"))
        values["video_count"] = self._clean_count(values.get("video_count"))

        username = values.get("username")
        if username:
            values["username"] = username.lstrip("@")
            values.setdefault("author_url", f"https://www.tiktok.com/@{values['username']}")

        values["_selector_results"] = selector_results
        values["_warnings"] = warnings
        values["_partial_reasons"] = partial_reasons
        return values

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    def _normalize_video(self, extracted: dict[str, Any]) -> dict[str, Any]:
        """Map extracted video fields to UnifiedOutput fields."""
        media_urls: list[str] = []
        video_url = extracted.get("video_url")
        if video_url:
            media_urls.append(video_url)

        return {
            "title": extracted.get("description"),
            "text": extracted.get("description"),
            "author": extracted.get("author_username"),
            "author_url": extracted.get("author_url"),
            "timestamp": extracted.get("timestamp"),
            "likes": extracted.get("like_count"),
            "shares": extracted.get("share_count"),
            "comments": extracted.get("comment_count"),
            "views": extracted.get("play_count"),
            "media_urls": media_urls,
            "thumbnail_url": extracted.get("thumbnail_url"),
            "tags": extracted.get("hashtags", []),
        }

    def _normalize_profile(self, extracted: dict[str, Any]) -> dict[str, Any]:
        """Map extracted profile fields to UnifiedOutput fields."""
        return {
            "title": extracted.get("display_name"),
            "text": extracted.get("bio"),
            "author": extracted.get("username"),
            "author_url": extracted.get("author_url"),
            "likes": extracted.get("likes_count"),
            "views": extracted.get("video_count"),
            "media_urls": [],
            "tags": [],
        }

    # ------------------------------------------------------------------
    # Shared extraction helpers
    # ------------------------------------------------------------------

    def _run_selector_chains(
        self,
        soup: BeautifulSoup,
        selector_sets: dict[str, list[str]],
    ) -> tuple[dict[str, Any], dict[str, Any], list[str], list[str]]:
        """Run text selector fallback chains and return values plus metadata."""
        results = self._extract_with_selectors(soup, selector_sets)
        values: dict[str, Any] = {}
        selector_results: dict[str, Any] = {}
        warnings: list[str] = []
        partial_reasons: list[str] = []

        for field, result in results.items():
            value = result.get("value")
            selector_used = result.get("selector_used")
            matched = result.get("matched", False)
            selector_results[field] = {
                "value": value,
                "selector_used": selector_used,
                "matched": matched,
            }

            if matched and value is not None:
                values[field] = value
                primary = selector_sets[field][0]
                if selector_used and selector_used != primary:
                    warnings.append(
                        f"Used fallback selector {selector_used} for {field} "
                        "— primary selector may need updating.",
                    )
            else:
                partial_reasons.append(
                    f"{field}: no matching selectors found — site structure may have changed.",
                )

        return values, selector_results, warnings, partial_reasons

    def _extract_attribute_chain(
        self,
        soup: BeautifulSoup,
        primary_selector: str,
        attribute: str,
        fallbacks: list[str] | None = None,
    ) -> str | None:
        """Extract an HTML attribute using a selector fallback chain."""
        return self._extract_first_attribute(
            soup,
            [(primary_selector, attribute)] + [(fb, attribute) for fb in (fallbacks or [])],
        )

    def _extract_first_attribute(
        self,
        soup: BeautifulSoup,
        selector_attribute_pairs: list[tuple[str, str]],
    ) -> str | None:
        """Return the first attribute value found across selector/attribute pairs."""
        for selector, attribute in selector_attribute_pairs:
            element = soup.select_one(selector)
            if not isinstance(element, Tag):
                continue
            value = element.get(attribute)
            if value:
                return str(value)
        return None

    def _extract_recent_videos(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract the recent video list from a profile page."""
        items = soup.select(".tt-video-item, [data-e2e='user-post-item'], .tt-video-card")
        videos: list[dict[str, Any]] = []
        for item in items:
            video_id = item.get("data-video-id") or item.get("data-id")
            link_tag = item.select_one("a[href*='/video/']")
            link = link_tag.get("href") if isinstance(link_tag, Tag) else None
            thumb_tag = item.select_one("img, video")
            thumbnail = None
            if isinstance(thumb_tag, Tag):
                thumbnail = thumb_tag.get("poster") or thumb_tag.get("src")
            view_tag = item.select_one(".tt-video-views, .view-count")
            views = self._parse_engagement(
                view_tag.get_text(strip=True) if isinstance(view_tag, Tag) else None,
            )
            videos.append(
                {
                    "video_id": str(video_id) if video_id else None,
                    "url": link,
                    "thumbnail_url": str(thumbnail) if thumbnail else None,
                    "views": views,
                },
            )
        return videos

    def _extract_hashtags(self, text: str) -> list[str]:
        """Extract hashtags from text."""
        return re.findall(r"#\w+", text)

    def _clean_count(self, text: str | None) -> int | None:
        """Clean a count string before parsing it as an integer."""
        if text is None:
            return None
        cleaned = re.sub(
            r"(?i)\s*(views?|likes?|comments?|shares?)\s*",
            "",
            text,
        )
        cleaned = cleaned.strip(" +")
        return self._parse_engagement(cleaned)

    _DURATION_PARTS_MINUTE = 2
    _DURATION_PARTS_HOUR = 3
    _SECONDS_PER_MINUTE = 60
    _SECONDS_PER_HOUR = 3600

    def _parse_duration(self, value: str | None) -> int | None:
        """Parse a duration string into seconds."""
        if value is None:
            return None
        cleaned = value.strip()
        if cleaned.isdigit():
            return int(cleaned)
        parts = cleaned.split(":")
        try:
            if len(parts) == self._DURATION_PARTS_MINUTE:
                minutes, seconds = parts
                return int(minutes) * self._SECONDS_PER_MINUTE + int(seconds)
            if len(parts) == self._DURATION_PARTS_HOUR:
                hours, minutes, seconds = parts
                return (
                    int(hours) * self._SECONDS_PER_HOUR
                    + int(minutes) * self._SECONDS_PER_MINUTE
                    + int(seconds)
                )
        except ValueError:
            return None
        return None

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        """Parse a timestamp string into a UTC datetime."""
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            # Replace trailing Z with +00:00 for fromisoformat compatibility.
            if cleaned.endswith("Z"):
                cleaned = cleaned[:-1] + "+00:00"
            return datetime.fromisoformat(cleaned).astimezone(UTC)
        except ValueError:
            pass
        # Fallback: parse common date formats.
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(cleaned, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
        return None

    def health_check(self) -> dict[str, Any]:
        """Return TikTok adapter health metadata."""
        base = super().health_check()
        base["platform"] = "tiktok"
        return base
