"""LinkedIn platform adapter for Phoenix Engine.

Extracts publicly visible LinkedIn posts, profiles, and company pages from
HTML using selector fallback chains. No official LinkedIn API is used.
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


class LinkedInAdapter(BaseAdapter):
    """Adapter for public LinkedIn posts, profiles, and company pages."""

    _URL_PATTERNS: ClassVar[list[str]] = [
        r"https?://(www\.)?linkedin\.com/posts/.+",
        r"https?://(www\.)?linkedin\.com/pulse/.+",
        r"https?://(www\.)?linkedin\.com/activity/.+",
        r"https?://(www\.)?linkedin\.com/in/[^/]+/?",
        r"https?://(www\.)?linkedin\.com/company/[^/]+/?",
    ]

    @property
    def manifest(self) -> PluginManifest:
        """Return the LinkedIn adapter manifest."""
        return PluginManifest(
            name="linkedin",
            version="0.1.0",
            description="Pure-scraping adapter for public LinkedIn posts, profiles, and companies.",
            author="Phoenix Engine Team",
            platforms=["linkedin"],
            url_patterns=self._URL_PATTERNS,
            strategies=["browser", "http"],
            requires_auth=True,
            supports_ai_fallback=True,
        )

    def supported_patterns(self) -> list[Pattern[str]]:
        """Return compiled URL regex patterns handled by this adapter."""
        return [re.compile(pattern, re.IGNORECASE) for pattern in self._URL_PATTERNS]

    def preferred_strategies(self) -> list[str]:
        """LinkedIn content is often behind auth walls; prefer browser."""
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
                "code": "SCR_021",
                "message": "Authentication required — this content is not publicly accessible.",
            }
        return raw_response

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract structured LinkedIn fields from ``raw_response``.

        Uses selector fallback chains for resilience against LinkedIn layout
        changes. Returns post, profile, or company data depending on the URL.
        """
        soup = BeautifulSoup(raw_response.html, "html.parser")
        content_type = self._detect_content_type(raw_response.url)

        if content_type == "profile":
            data = self._extract_profile(soup)
        elif content_type == "company":
            data = self._extract_company(soup)
        else:
            data = self._extract_post(soup)

        data["content_type"] = content_type
        data["url"] = raw_response.url
        data["_platform"] = "linkedin"
        data["_strategy"] = raw_response.strategy
        return data

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Convert extracted LinkedIn fields into ``UnifiedOutput``."""
        content_type = extracted.get("content_type", "post")
        selectors_used: list[str] = []
        for result in extracted.get("_selector_results", {}).values():
            selector_used = result.get("selector_used")
            if selector_used and selector_used not in selectors_used:
                selectors_used.append(selector_used)

        base: dict[str, Any] = {
            "url": url,
            "platform": "linkedin",
            "content_type": content_type,
            "scraping_strategy": strategy,
            "selectors_used": selectors_used,
            "ai_assisted": False,
        }

        if content_type == "post":
            base.update(self._normalize_post(extracted))
        elif content_type == "profile":
            base.update(self._normalize_profile(extracted))
        elif content_type == "company":
            base.update(self._normalize_company(extracted))

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

    def _detect_content_type(self, url: str) -> str:
        """Detect whether the URL represents a post, profile, or company page."""
        lowered = url.lower()
        if "/in/" in lowered:
            return "profile"
        if "/company/" in lowered:
            return "company"
        return "post"

    # ------------------------------------------------------------------
    # Profile extraction
    # ------------------------------------------------------------------

    def _extract_profile(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract public LinkedIn profile metadata."""
        text_selectors: dict[str, list[str]] = {
            "name": [
                "h1.top-card-layout__title",
                ".profile-name",
                "h1.profile-topcard__name",
                "h1",
            ],
            "headline": [
                ".top-card-layout__headline",
                ".profile-headline",
                ".profile-topcard__summary",
            ],
            "location": [
                ".top-card-layout__first-subline",
                ".profile-location",
                ".profile-topcard__location",
            ],
            "industry": [
                ".top-card-layout__second-subline",
                ".profile-industry",
            ],
            "current_position": [
                ".experience-item__title",
                ".profile-current-position",
                ".experience-section li",
            ],
            "education": [
                ".education-item__school-name",
                ".profile-education",
                ".education-section li",
            ],
            "connections_count": [
                ".top-card-layout__connections",
                ".profile-connections",
                ".connections-count",
            ],
        }

        values, selector_results, warnings, partial_reasons = self._run_selector_chains(
            soup,
            text_selectors,
        )

        values["connections_count"] = self._clean_count(values.get("connections_count"))
        values["_selector_results"] = selector_results
        values["_warnings"] = warnings
        values["_partial_reasons"] = partial_reasons
        return values

    # ------------------------------------------------------------------
    # Company extraction
    # ------------------------------------------------------------------

    def _extract_company(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract public LinkedIn company page metadata."""
        text_selectors: dict[str, list[str]] = {
            "name": [
                "h1.top-card-layout__title",
                ".company-name",
                "h1.org-top-card-summary__title",
                "h1",
            ],
            "industry": [
                ".top-card-layout__first-subline",
                ".company-industry",
                ".org-about-company-module__industry",
            ],
            "company_size": [
                ".top-card-layout__second-subline",
                ".company-size",
                ".org-about-company-module__company-size",
            ],
            "headquarters": [
                ".company-headquarters",
                ".org-about-company-module__headquarters",
                ".top-card-layout__subline",
            ],
            "description": [
                ".company-description",
                ".org-about-us-organization-description__text",
                ".description",
                "meta[property='og:description']",
            ],
            "follower_count": [
                ".company-follower-count",
                ".org-top-card-summary__follower-count",
                ".follower-count",
            ],
            "website": [
                ".company-website a",
                ".org-about-us-company-module__website",
                "a[href^='http']",
            ],
        }

        values, selector_results, warnings, partial_reasons = self._run_selector_chains(
            soup,
            text_selectors,
        )

        specialties = self._extract_list(
            soup,
            ".company-specialties li, .org-about-company-module__specialties li",
        )
        values["specialties"] = specialties
        selector_results["specialties"] = {
            "value": ", ".join(specialties),
            "selector_used": ".company-specialties li",
            "matched": bool(specialties),
        }
        if not specialties:
            partial_reasons.append("specialties: no matching selectors found")

        values["follower_count"] = self._clean_count(values.get("follower_count"))

        website_url = self._extract_first_attribute(
            soup,
            [
                (".company-website a", "href"),
                (".org-about-us-company-module__website", "href"),
                ("a[href^='http']", "href"),
            ],
        )
        if website_url:
            values["website"] = website_url
            selector_results["website"]["value"] = website_url

        values["_selector_results"] = selector_results
        values["_warnings"] = warnings
        values["_partial_reasons"] = partial_reasons
        return values

    # ------------------------------------------------------------------
    # Post extraction
    # ------------------------------------------------------------------

    def _extract_post(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract public LinkedIn post metadata."""
        text_selectors: dict[str, list[str]] = {
            "author": [
                ".feed-shared-actor__name",
                ".li-name",
                ".author-name",
                ".profile-name",
            ],
            "author_headline": [
                ".feed-shared-actor__description",
                ".li-headline",
                ".author-headline",
            ],
            "text": [
                ".feed-shared-update-v2__description",
                ".li-content p",
                ".post-caption p",
                "meta[property='og:description']",
            ],
            "timestamp": [
                "time[datetime]",
                ".li-timestamp",
                ".feed-shared-actor__sub-description",
            ],
            "reaction_count": [
                ".social-details-social-counts__reactions-count",
                ".li-reactions",
                ".reaction-count",
            ],
            "comment_count": [
                ".social-details-social-counts__comments",
                ".li-comments",
                ".comment-count",
            ],
            "repost_count": [
                ".social-details-social-counts__shares",
                ".li-shares",
                ".share-count",
            ],
        }

        values, selector_results, warnings, partial_reasons = self._run_selector_chains(
            soup,
            text_selectors,
        )

        post_id = self._extract_first_attribute(
            soup,
            [
                ("article[data-urn]", "data-urn"),
                ("[data-activity-urn]", "data-activity-urn"),
                (".li-post[data-id]", "data-id"),
            ],
        )
        if post_id is None:
            partial_reasons.append("id: no matching selectors found")
        else:
            values["id"] = post_id
            selector_results["id"] = {
                "value": post_id,
                "selector_used": "article[data-urn]",
                "matched": True,
            }

        values["reaction_count"] = self._clean_count(values.get("reaction_count"))
        values["comment_count"] = self._clean_count(values.get("comment_count"))
        values["repost_count"] = self._clean_count(values.get("repost_count"))
        timestamp_attr = self._extract_first_attribute(
            soup,
            [("time[datetime]", "datetime"), (".li-timestamp", "datetime")],
        )
        values["timestamp"] = self._parse_timestamp(
            timestamp_attr or values.get("timestamp"),
        )

        author_url = values.get("author_url")
        if author_url is None and values.get("author"):
            slug = re.sub(r"\s+", "-", values["author"]).lower()
            author_url = f"https://www.linkedin.com/in/{slug}/"
            values["author_url"] = author_url

        values["_selector_results"] = selector_results
        values["_warnings"] = warnings
        values["_partial_reasons"] = partial_reasons
        return values

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    def _normalize_post(self, extracted: dict[str, Any]) -> dict[str, Any]:
        """Map extracted post fields to UnifiedOutput fields."""
        return {
            "title": extracted.get("text"),
            "text": extracted.get("text"),
            "author": extracted.get("author"),
            "author_url": extracted.get("author_url"),
            "timestamp": extracted.get("timestamp"),
            "likes": extracted.get("reaction_count"),
            "shares": extracted.get("repost_count"),
            "comments": extracted.get("comment_count"),
            "media_urls": [],
            "tags": [],
        }

    def _normalize_profile(self, extracted: dict[str, Any]) -> dict[str, Any]:
        """Map extracted profile fields to UnifiedOutput fields."""
        return {
            "title": extracted.get("name"),
            "text": extracted.get("headline"),
            "author": extracted.get("name"),
            "author_url": extracted.get("url"),
            "media_urls": [],
            "tags": [],
        }

    def _normalize_company(self, extracted: dict[str, Any]) -> dict[str, Any]:
        """Map extracted company fields to UnifiedOutput fields."""
        return {
            "title": extracted.get("name"),
            "text": extracted.get("description"),
            "author": extracted.get("name"),
            "author_url": extracted.get("url"),
            "likes": extracted.get("follower_count"),
            "media_urls": [],
            "tags": extracted.get("specialties", []),
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

    def _extract_list(self, soup: BeautifulSoup, selector: str) -> list[str]:
        """Extract a list of text values from matching elements."""
        items: list[str] = []
        for element in soup.select(selector):
            if isinstance(element, Tag):
                text = element.get_text(strip=True)
                if text:
                    items.append(text)
        return items

    def _clean_count(self, text: str | None) -> int | None:
        """Clean a count string before parsing it as an integer."""
        if text is None:
            return None
        cleaned = re.sub(
            r"(?i)\s*(likes?|comments?|reposts?|reactions?|followers?|connections?)\s*",
            "",
            text,
        )
        cleaned = cleaned.strip(" +")
        return self._parse_engagement(cleaned)

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        """Parse a timestamp string into a UTC datetime."""
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            if cleaned.endswith("Z"):
                cleaned = cleaned[:-1] + "+00:00"
            return datetime.fromisoformat(cleaned).astimezone(UTC)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(cleaned, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
        return None

    def health_check(self) -> dict[str, Any]:
        """Return LinkedIn adapter health metadata."""
        base = super().health_check()
        base["platform"] = "linkedin"
        return base
