"""X/Twitter platform adapter for Phoenix Engine.

Extracts public X/Twitter tweets, profiles, and threads from raw HTML using
CSS selector fallback chains. Never uses the X API.
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


class XTwitterAdapter(BaseAdapter):
    """Adapter for public X/Twitter tweets and profiles."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the X/Twitter adapter manifest."""
        return PluginManifest(
            name="x_twitter",
            version="0.1.0",
            description="Pure HTML scraper for public X/Twitter tweets and profiles.",
            author="Phoenix Engine Team",
            platforms=["x", "x_twitter"],
            url_patterns=[
                r"https?://(www\.)?(twitter|x)\.com/[^/]+/status/\d+",
                r"https?://(www\.)?(twitter|x)\.com/i/web/status/\d+",
                r"https?://(www\.)?(twitter|x)\.com/[^/]+/?",
            ],
            strategies=["http", "browser"],
            requires_auth=False,
            supports_ai_fallback=True,
        )

    def supported_patterns(self) -> list[Pattern[str]]:
        """Return compiled X/Twitter URL patterns."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in self.manifest.url_patterns]

    def preferred_strategies(self) -> list[str]:
        """X/Twitter static HTML is often sufficient; try HTTP first."""
        return ["http", "browser"]

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
                "message": "X/Twitter content appears private or requires authentication.",
            }
        return raw_response

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract structured X/Twitter data from ``raw_response``."""
        soup = BeautifulSoup(raw_response.html, "html.parser")
        url = raw_response.final_url or raw_response.url

        if re.search(r"/(status|statuses|i/web/status)/[^/?#]+", url):
            return self._extract_tweet(soup, url)
        return self._extract_profile(soup, url)

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Convert extracted X/Twitter fields into ``UnifiedOutput``."""
        output_data: dict[str, Any] = {
            "url": url,
            "platform": "x",
            "content_type": extracted.get("content_type", "post"),
            "title": extracted.get("title"),
            "text": extracted.get("text"),
            "author": extracted.get("author_username") or extracted.get("author"),
            "author_url": (
                f"https://x.com/{extracted.get('author_username', '').lstrip('@')}/"
                if extracted.get("author_username")
                else None
            ),
            "timestamp": self._parse_timestamp(extracted.get("timestamp")),
            "likes": self._parse_number(extracted.get("like_count")),
            "shares": self._parse_number(extracted.get("retweet_count")),
            "comments": self._parse_number(extracted.get("reply_count")),
            "views": self._parse_number(extracted.get("view_count")),
            "media_urls": extracted.get("media_urls", []),
            "thumbnail_url": extracted.get("thumbnail_url"),
            "tags": extracted.get("tags", []),
            "scraping_strategy": strategy,
            "selectors_used": extracted.get("selectors_used", []),
            "tweet_id": extracted.get("tweet_id"),
            "recent_tweets": extracted.get("recent_tweets", []),
        }

        for key in (
            "display_name",
            "location",
            "website",
            "join_date",
            "bio",
            "follower_count",
            "following_count",
            "tweet_count",
        ):
            if key in extracted:
                if key in ("follower_count", "following_count", "tweet_count"):
                    output_data.setdefault("metadata", {})[key] = self._parse_number(
                        extracted[key],
                    )
                else:
                    output_data.setdefault("metadata", {})[key] = extracted[key]

        # Map common profile fields to unified top-level fields.
        if "follower_count" in extracted:
            output_data["follower_count"] = self._parse_number(extracted["follower_count"])
        if "following_count" in extracted:
            output_data["following_count"] = self._parse_number(extracted["following_count"])
        if "tweet_count" in extracted:
            output_data["tweet_count"] = self._parse_number(extracted["tweet_count"])
        if "website" in extracted:
            output_data["website"] = extracted["website"]
        if "location" in extracted:
            output_data["location"] = extracted["location"]
        if "join_date" in extracted:
            output_data["join_date"] = extracted["join_date"]

        return UnifiedOutput(**output_data)

    def _extract_tweet(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
        """Extract fields from an X/Twitter tweet page."""
        selector_sets = {
            "text": [
                ".tweet-text",
                "div[lang='en']",
                "meta[property='og:description']",
            ],
            "author_username": [
                ".tweet-author",
                ".tweet-author-link .tweet-author",
                "a[href^='/'] .tweet-author",
                "meta[property='og:title']",
            ],
            "timestamp": [
                "time[datetime]",
                ".timestamp",
            ],
            "like_count": [
                ".like-count",
                "button[aria-label*='like']",
            ],
            "retweet_count": [
                ".share-count",
                "button[aria-label*='retweet']",
            ],
            "reply_count": [
                ".comment-count",
                "button[aria-label*='reply']",
            ],
        }

        results = self._extract_with_selectors(soup, selector_sets)
        text = self._first_text(results, "text")
        if not text:
            text = self._meta_content(soup, "og:description")

        author = self._first_text(results, "author_username")
        if author:
            author = author.lstrip("@").split()[0]

        tweet_id = self._extract_tweet_id(url)
        media_urls = self._extract_media_urls(soup)
        tags = self._extract_hashtags(text or "")
        mentions = self._extract_mentions(text or "")

        return {
            "content_type": "post",
            "tweet_id": tweet_id,
            "text": text,
            "author_username": author,
            "author": author,
            "timestamp": self._first_time_attr(results, soup),
            "like_count": self._first_text(results, "like_count"),
            "retweet_count": self._first_text(results, "retweet_count"),
            "reply_count": self._first_text(results, "reply_count"),
            "view_count": None,
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

    def _extract_profile(self, soup: BeautifulSoup, url: str) -> dict[str, Any]:
        """Extract fields from an X/Twitter profile page."""
        selector_sets = {
            "display_name": [
                ".profile-display-name",
                "h1",
                "meta[property='og:title']",
            ],
            "username": [
                ".profile-username",
                "h2",
                "meta[property='og:title']",
            ],
            "bio": [
                ".profile-bio",
                "meta[property='og:description']",
            ],
            "location": [
                ".profile-location",
            ],
            "website": [
                ".profile-website",
                "a[href^='http']",
            ],
            "join_date": [
                ".profile-join-date",
            ],
            "follower_count": [
                ".follower-count",
            ],
            "following_count": [
                ".following-count",
            ],
            "tweet_count": [
                ".tweet-count",
            ],
        }

        results = self._extract_with_selectors(soup, selector_sets)
        username = self._first_text(results, "username")
        if not username:
            username = f"@{self._extract_username_from_url(url)}"

        bio = self._first_text(results, "bio")
        if not bio:
            bio = self._meta_content(soup, "og:description")

        recent_tweets = self._extract_recent_tweets(soup)

        return {
            "content_type": "profile",
            "title": self._first_text(results, "display_name"),
            "text": bio,
            "author_username": username.lstrip("@"),
            "author": username.lstrip("@"),
            "username": username,
            "display_name": self._first_text(results, "display_name"),
            "bio": bio,
            "location": self._first_text(results, "location"),
            "website": self._extract_href(soup, results.get("website", {}).get("selector_used")),
            "join_date": self._first_text(results, "join_date"),
            "follower_count": self._first_text(results, "follower_count"),
            "following_count": self._first_text(results, "following_count"),
            "tweet_count": self._first_text(results, "tweet_count"),
            "recent_tweets": recent_tweets,
            "media_urls": [],
            "selectors_used": [
                results[field]["selector_used"]
                for field in selector_sets
                if results.get(field, {}).get("selector_used")
            ],
        }

    def _extract_recent_tweets(self, soup: BeautifulSoup) -> list[str]:
        """Return text of recent tweets found on a profile page."""
        tweets: list[str] = []
        for tweet in soup.select(".recent-tweets .tweet-text"):
            text = tweet.get_text(strip=True)
            if text:
                tweets.append(text)
        return tweets

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

    def _extract_href(self, soup: BeautifulSoup, selector: str | None) -> str | None:
        """Return the href of the first anchor matched by ``selector``."""
        if not selector:
            return None
        elements = soup.select(selector)
        if not elements:
            return None
        href = elements[0].get("href")
        return str(href).strip() if href else None

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

    def _extract_hashtags(self, text: str) -> list[str]:
        """Return hashtags found in ``text``."""
        return re.findall(r"#\w+", text)

    def _extract_mentions(self, text: str) -> list[str]:
        """Return @mentions found in ``text``."""
        return re.findall(r"@\w+", text)

    def _parse_number(self, text: str | None) -> int | None:
        """Parse a numeric count, stripping platform-specific words."""
        if text is None:
            return None
        cleaned = re.sub(
            r"\b(likes?|reposts?|retweets?|replies?|views?|followers?|following|posts?)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        return self._parse_engagement(cleaned.strip())

    def _extract_tweet_id(self, url: str) -> str | None:
        """Extract tweet ID from a tweet URL."""
        match = re.search(r"/(?:status|statuses|i/web/status)/(\d+)", url)
        return match.group(1) if match else None

    def _extract_username_from_url(self, url: str) -> str | None:
        """Extract X/Twitter username from a profile URL."""
        match = re.search(r"(?:twitter|x)\.com/([^/?#]+)/?", url)
        if match and match.group(1) not in (
            "home",
            "explore",
            "notifications",
            "messages",
            "i",
            "search",
        ):
            return match.group(1)
        return None


__all__ = ["XTwitterAdapter"]
