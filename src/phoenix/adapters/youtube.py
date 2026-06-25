"""YouTube platform adapter for Phoenix Engine.

Extracts structured data from public YouTube videos and channels using CSS
selector fallback chains. No official YouTube API is used.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from phoenix.adapters.base import BaseAdapter
from phoenix.models.output import UnifiedOutput
from phoenix.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from phoenix.collectors.base import Collector
    from phoenix.models.document import RawResponse
    from phoenix.options import CollectionOptions


class YouTubeAdapter(BaseAdapter):
    """Adapter for scraping public YouTube videos and channels."""

    _URL_PATTERNS: ClassVar[list[str]] = [
        r"https?://(?:www\.)?youtube\.com/watch\?.*v=[^&]+",
        r"https?://(?:www\.)?youtube\.com/shorts/[^/]+",
        r"https?://(?:www\.)?youtube\.com/embed/[^/]+",
        r"https?://(?:www\.)?youtube\.com/@(?:[^/]+)",
        r"https?://(?:www\.)?youtube\.com/c/[^/]+",
        r"https?://(?:www\.)?youtube\.com/channel/[^/]+",
        r"https?://(?:www\.)?youtu\.be/[^/]+",
    ]

    _VIDEO_SELECTOR_SETS: ClassVar[dict[str, list[str]]] = {
        "title": [
            "h1.yt-video-title",
            ".yt-video-title",
            'meta[property="og:title"]',
        ],
        "description": [
            ".yt-video-description p",
            ".yt-video-description",
            'meta[name="description"]',
        ],
        "channel": [
            ".yt-channel-name",
            ".yt-channel-link",
            "[data-channel-name]",
        ],
        "view_count": [
            ".yt-view-count",
            "[data-view-count]",
        ],
        "like_count": [
            ".yt-like-count",
            "[data-like-count]",
        ],
        "comment_count": [
            ".yt-comment-count",
            "[data-comment-count]",
        ],
        "category": [
            ".yt-category",
            "[data-category]",
        ],
        "duration": [
            ".yt-duration",
            "[data-duration]",
        ],
    }

    _CHANNEL_SELECTOR_SETS: ClassVar[dict[str, list[str]]] = {
        "name": [
            "h1.yt-channel-name",
            ".yt-channel-name",
            'meta[property="og:title"]',
        ],
        "description": [
            ".yt-channel-description",
            'meta[name="description"]',
        ],
        "subscriber_count": [
            ".yt-subscriber-count",
            "[data-subscriber-count]",
        ],
        "video_count": [
            ".yt-video-count",
            "[data-video-count]",
        ],
        "view_count": [
            ".yt-channel-view-count",
            "[data-channel-view-count]",
        ],
        "joined_date": [
            ".yt-joined-date",
            "[data-joined-date]",
        ],
    }

    @property
    def manifest(self) -> PluginManifest:
        """Return the YouTube adapter manifest."""
        return PluginManifest(
            name="youtube",
            version="0.1.0",
            description="Scraper for public YouTube videos and channels.",
            author="Phoenix Engine Team",
            platforms=["youtube"],
            url_patterns=list(self._URL_PATTERNS),
            strategies=["http", "browser"],
            requires_auth=False,
            supports_ai_fallback=True,
        )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        """Return compiled URL patterns handled by this adapter."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in self._URL_PATTERNS]

    def preferred_strategies(self) -> list[str]:
        """YouTube serves useful metadata server-side; prefer HTTP."""
        return ["http", "browser"]

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
        """Extract structured YouTube fields from ``raw_response``."""
        soup = BeautifulSoup(raw_response.html, "html.parser")
        url = raw_response.final_url or raw_response.url
        content_type = self._classify_url(url)

        if content_type in {"video", "short"}:
            return self._extract_video(soup, url, content_type)
        return self._extract_channel(soup, url)

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Convert extracted YouTube fields into ``UnifiedOutput``."""
        content_type = extracted.get("content_type", "video")
        selectors_used = list(extracted.get("selectors_used", []))

        base_output: dict[str, Any] = {
            "url": url,
            "platform": self.manifest.platforms[0],
            "content_type": content_type,
            "scraping_strategy": strategy,
            "selectors_used": selectors_used,
        }

        if content_type == "profile":
            base_output.update(self._normalize_channel(extracted, url))
        else:
            base_output.update(self._normalize_video(extracted, url))

        return UnifiedOutput(**base_output)

    # ------------------------------------------------------------------
    # URL classification
    # ------------------------------------------------------------------

    def _classify_url(self, url: str) -> str:
        """Classify a YouTube URL into a content type."""
        path = urlparse(url).path.lower()
        if "/shorts/" in path:
            return "short"
        if "/watch" in path or "/embed/" in path or "/youtu.be/" in path:
            return "video"
        return "profile"

    # ------------------------------------------------------------------
    # Video extraction
    # ------------------------------------------------------------------

    def _extract_video(
        self,
        soup: BeautifulSoup,
        url: str,
        content_type: str = "video",
    ) -> dict[str, Any]:
        """Extract public YouTube video fields."""
        text_results = self._extract_with_selectors(soup, self._VIDEO_SELECTOR_SETS)
        selectors_used = self._collect_selectors(text_results)

        video_id = self._extract_video_id(soup, url)

        timestamp = self._extract_attribute(
            soup,
            ["time.timestamp", "time", ".timestamp"],
            "datetime",
        )
        if timestamp["selector_used"]:
            selectors_used.append(timestamp["selector_used"])

        channel_url = self._extract_channel_url(soup, url)
        tags = self._extract_tags(soup)
        transcript_segments = self._extract_transcript_segments(soup)
        thumbnail_url = self._extract_thumbnail_url(soup, url)
        media_urls = self._extract_media_urls(soup, url)
        comments_disabled = self._comments_disabled(soup)
        comment_count = self._parse_comment_count(
            self._clean_count_text(text_results["comment_count"]["value"]),
            comments_disabled=comments_disabled,
        )

        return {
            "content_type": content_type,
            "platform": "youtube",
            "url": url,
            "id": video_id,
            "title": text_results["title"]["value"],
            "description": text_results["description"]["value"],
            "channel": text_results["channel"]["value"],
            "channel_url": channel_url,
            "timestamp": self._parse_iso_timestamp(timestamp["value"]),
            "duration": text_results["duration"]["value"],
            "view_count": self._parse_engagement(
                self._clean_count_text(text_results["view_count"]["value"]),
            ),
            "like_count": self._parse_engagement(
                self._clean_count_text(text_results["like_count"]["value"]),
            ),
            "comment_count": comment_count,
            "comments_disabled": comments_disabled,
            "tags": tags,
            "category": text_results["category"]["value"],
            "transcript_segments": transcript_segments,
            "media_urls": media_urls,
            "thumbnail_url": thumbnail_url,
            "selectors_used": selectors_used,
            "is_public": self._is_public_content(str(soup)),
        }

    def _extract_video_id(self, soup: BeautifulSoup, url: str) -> str | None:
        """Extract the YouTube video ID from HTML or URL."""
        article = soup.select_one("article.yt-video[data-video-id]")
        if article and article.has_attr("data-video-id"):
            return str(article["data-video-id"])

        parsed = urlparse(url)
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[-1]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[-1]
        if parsed.netloc in {"youtu.be", "www.youtu.be"}:
            return parsed.path.strip("/")
        query_params = self._parse_query_params(url)
        return query_params.get("v")

    def _extract_channel_url(self, soup: BeautifulSoup, url: str) -> str | None:
        """Extract the channel URL from the video page."""
        link = soup.select_one(".yt-channel-link[href]")
        if link and link.has_attr("href"):
            return self._resolve_url(str(link["href"]), url)
        return None

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        """Extract hashtag tags from the video page."""
        tags: list[str] = []
        for tag in soup.select(".yt-tags .tag, .yt-tag"):
            text = tag.get_text(strip=True)
            if text:
                tags.append(text)
        return tags

    def _extract_transcript_segments(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract transcript segments if present in the HTML."""
        segments: list[dict[str, Any]] = []
        for segment in soup.select(".yt-transcript .yt-transcript-segment"):
            text = segment.get_text(strip=True)
            if not text:
                continue
            start = segment.get("data-start")
            segments.append(
                {
                    "start": start,
                    "text": text,
                },
            )
        return segments

    def _extract_thumbnail_url(self, soup: BeautifulSoup, url: str) -> str | None:
        """Extract the video thumbnail URL."""
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.has_attr("content"):
            return self._resolve_url(str(og_image["content"]), url)

        video = soup.select_one("video[poster]")
        if video and video.has_attr("poster"):
            return self._resolve_url(str(video["poster"]), url)
        return None

    def _extract_media_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """Extract video source URLs from the page."""
        urls: list[str] = []
        for video in soup.select("video[src]"):
            src = video.get("src")
            if src:
                resolved = self._resolve_url(str(src), url)
                if resolved:
                    urls.append(resolved)
        return urls

    def _comments_disabled(self, soup: BeautifulSoup) -> bool:
        """Return ``True`` when the video has comments disabled."""
        indicator = soup.select_one(".yt-comments-disabled")
        if indicator is not None and not self._is_hidden(indicator):
            indicator_text = indicator.get_text(separator=" ", strip=True).lower()
            if "turned off" in indicator_text or "disabled" in indicator_text:
                return True
        text = soup.get_text(separator=" ", strip=True).lower()
        return "comments are turned off" in text or "comments disabled" in text

    def _is_hidden(self, element: Tag) -> bool:
        """Return ``True`` when ``element`` appears hidden via inline style."""
        style = str(element.get("style", "")).lower().replace(" ", "")
        return "display:none" in style

    def _parse_comment_count(
        self,
        raw_value: str | None,
        *,
        comments_disabled: bool,
    ) -> int | None:
        """Parse comment count, returning ``None`` when comments are disabled."""
        if comments_disabled:
            return None
        return self._parse_engagement(raw_value)

    # ------------------------------------------------------------------
    # Channel extraction
    # ------------------------------------------------------------------

    def _extract_channel(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
        """Extract public YouTube channel fields."""
        text_results = self._extract_with_selectors(soup, self._CHANNEL_SELECTOR_SETS)
        selectors_used = self._collect_selectors(text_results)

        name = text_results["name"]["value"]
        if not name:
            og_title = self._extract_attribute(
                soup,
                ['meta[property="og:title"]'],
                "content",
            )
            if og_title["value"]:
                name = og_title["value"]
                selectors_used.append(og_title["selector_used"])

        description = text_results["description"]["value"]
        if not description:
            meta_desc = self._extract_attribute(
                soup,
                ['meta[name="description"]'],
                "content",
            )
            if meta_desc["value"]:
                description = meta_desc["value"]
                selectors_used.append(meta_desc["selector_used"])

        channel_id_el = soup.select_one(".yt-channel-id[data-channel-id]")
        channel_id = (
            str(channel_id_el["data-channel-id"])
            if (channel_id_el and channel_id_el.has_attr("data-channel-id"))
            else None
        )

        recent_videos = self._extract_recent_videos(soup)

        return {
            "content_type": "profile",
            "platform": "youtube",
            "url": url,
            "channel_id": channel_id,
            "name": name,
            "description": description,
            "subscriber_count": self._parse_engagement(
                self._clean_count_text(text_results["subscriber_count"]["value"]),
            ),
            "video_count": self._parse_engagement(
                self._clean_count_text(text_results["video_count"]["value"]),
            ),
            "view_count": self._parse_engagement(
                self._clean_count_text(text_results["view_count"]["value"]),
            ),
            "joined_date": text_results["joined_date"]["value"],
            "recent_videos": recent_videos,
            "selectors_used": selectors_used,
            "is_public": self._is_public_content(str(soup)),
        }

    def _extract_recent_videos(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract recent video previews from a channel page."""
        videos: list[dict[str, Any]] = []
        for item in soup.select(".yt-recent-videos .yt-video-item"):
            video_id = item.get("data-video-id")
            title_el = item.select_one(".yt-video-item-title")
            views_el = item.select_one(".yt-video-item-views")
            videos.append(
                {
                    "video_id": str(video_id) if video_id else None,
                    "title": title_el.get_text(strip=True) if title_el else None,
                    "view_count": self._parse_engagement(
                        self._clean_count_text(
                            views_el.get_text(strip=True) if views_el else None,
                        ),
                    ),
                },
            )
        return videos

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    def _normalize_video(
        self,
        extracted: dict[str, Any],
        _url: str,
    ) -> dict[str, Any]:
        """Map video fields to UnifiedOutput fields."""
        media_urls = list(extracted.get("media_urls", []))
        return {
            "title": extracted.get("title"),
            "text": extracted.get("description"),
            "author": extracted.get("channel"),
            "author_url": extracted.get("channel_url"),
            "timestamp": extracted.get("timestamp"),
            "views": extracted.get("view_count"),
            "likes": extracted.get("like_count"),
            "comments": extracted.get("comment_count"),
            "shares": None,
            "media_urls": media_urls,
            "thumbnail_url": extracted.get("thumbnail_url"),
            "tags": list(extracted.get("tags", [])),
        }

    def _normalize_channel(
        self,
        extracted: dict[str, Any],
        url: str,
    ) -> dict[str, Any]:
        """Map channel fields to UnifiedOutput fields."""
        return {
            "title": extracted.get("name"),
            "text": extracted.get("description"),
            "author": extracted.get("name"),
            "author_url": url,
            "timestamp": None,
            "views": extracted.get("view_count"),
            "likes": None,
            "comments": None,
            "shares": None,
            "media_urls": [],
            "thumbnail_url": None,
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

    def _parse_query_params(self, url: str) -> dict[str, str]:
        """Parse query string parameters from ``url``."""
        params = parse_qs(urlparse(url).query)
        return {k: v[0] for k, v in params.items() if v}

    def _clean_count_text(self, text: str | None) -> str | None:
        """Extract a leading numeric count such as ``1.2K`` from noisy text."""
        if not text:
            return None
        match = re.search(r"[\d\.,]+\s*[KMBkmb]?", text)
        if match:
            return match.group(0).strip()
        return None
