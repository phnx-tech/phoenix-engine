"""Phoenix AI content classifier for Phoenix Engine.

Classifies raw HTML or extracted text into content types and platforms
when the standard router/heuristics are uncertain.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor


class HeuristicContentClassifier:
    """Fast rule-based content classification.

    This classifier looks at URL patterns, HTML meta tags, schema.org markup,
    and common DOM cues to classify a page without calling an LLM. It is used
    as the first stage before falling back to AI classification.
    """

    # (substring in URL path or domain, content_type, confidence)
    _URL_RULES: tuple[tuple[str, str, float], ...] = (
        ("/property", "real_estate", 0.8),
        ("/apartment", "real_estate", 0.8),
        ("/real-estate", "real_estate", 0.9),
        ("/listing", "real_estate", 0.7),
        ("/product", "product", 0.8),
        ("/item", "product", 0.7),
        ("/job", "job", 0.8),
        ("/jobs", "job", 0.8),
        ("/career", "job", 0.7),
        ("/article", "article", 0.7),
        ("/news", "article", 0.7),
        ("/blog", "article", 0.7),
        ("/post", "post", 0.6),
        ("/video", "video", 0.7),
        ("/watch", "video", 0.7),
        ("/profile", "profile", 0.7),
        ("/user", "profile", 0.6),
        ("/quote", "quote", 0.8),
    )

    _PLATFORM_RULES: tuple[tuple[str, str, float], ...] = (
        ("instagram.com", "instagram", 0.95),
        ("twitter.com", "x", 0.95),
        ("x.com", "x", 0.95),
        ("tiktok.com", "tiktok", 0.95),
        ("linkedin.com", "linkedin", 0.95),
        ("facebook.com", "facebook", 0.95),
        ("youtube.com", "youtube", 0.95),
        ("youtu.be", "youtube", 0.95),
        ("olx", "olx", 0.9),
        ("bayut", "bayut", 0.9),
        ("hatla2ee", "hatla2ee", 0.9),
        ("contactcars", "contactcars", 0.9),
    )

    def classify(self, html: str, url: str) -> dict[str, Any]:
        """Classify ``html`` using fast heuristics.

        Args:
            html: Raw HTML content.
            url: Source URL.

        Returns:
            Dictionary with ``platform``, ``content_type``, and ``confidence``.
        """
        url_lower = url.lower()
        html_lower = html[:5000].lower()

        platform = "generic"
        platform_confidence = 0.0
        for substring, detected_platform, confidence in self._PLATFORM_RULES:
            if substring in url_lower:
                platform = detected_platform
                platform_confidence = confidence
                break

        content_type = "article"
        content_confidence = 0.0
        for substring, detected_type, confidence in self._URL_RULES:
            if substring in url_lower:
                content_type = detected_type
                content_confidence = confidence
                break

        # Schema.org hints boost confidence.
        if '"@type":' in html or "schema.org" in html_lower:
            content_confidence = max(content_confidence, 0.6)
            if "product" in html_lower:
                content_type = "product"
                content_confidence = max(content_confidence, 0.8)
            elif "jobposting" in html_lower:
                content_type = "job"
                content_confidence = max(content_confidence, 0.8)
            elif "apartment" in html_lower or "residence" in html_lower:
                content_type = "real_estate"
                content_confidence = max(content_confidence, 0.8)

        # Page title / meta cues.
        if re.search(r"<title>[^<]*(?:apartment|villa|property|listing)", html_lower):
            content_type = "real_estate"
            content_confidence = max(content_confidence, 0.7)
        elif re.search(r"<title>[^<]*(?:quote)", html_lower):
            content_type = "quote"
            content_confidence = max(content_confidence, 0.7)

        overall_confidence = max(platform_confidence, content_confidence)
        if platform_confidence > 0 and content_confidence > 0:
            overall_confidence = min(0.95, (platform_confidence + content_confidence) / 2 + 0.1)

        return {
            "platform": platform,
            "content_type": content_type,
            "confidence": round(overall_confidence, 2),
            "reasoning": "heuristic URL/schema/meta classification",
        }


class ContentClassifier:
    """Classifies HTML content using Phoenix AI."""

    def __init__(self, extractor: PhoenixAIExtractor) -> None:
        """Initialize the classifier with a Phoenix AI extractor instance."""
        self.extractor = extractor

    async def classify(
        self,
        html: str,
        url: str,
    ) -> dict[str, Any]:
        """Classify ``html`` into content type and platform.

        Args:
            html: Raw HTML content.
            url: Source URL.

        Returns:
            Dictionary with ``platform``, ``content_type``, and ``confidence``.
        """
        schema = (
            "Return a JSON object with exactly these fields:\n"
            "  platform: string - one of: instagram, x_twitter, tiktok, linkedin, "
            "facebook, youtube, olx, generic\n"
            "  content_type: string - one of: post, profile, video, article, "
            "real_estate, product, job, quote, page\n"
            "  confidence: number between 0.0 and 1.0\n"
            "  reasoning: string - brief explanation"
        )
        result = await self.extractor.extract(
            html=html[:24000],
            url=url,
            platform="unknown",
            content_type="unknown",
            schema_description=schema,
            strict=False,
        )
        # Some local models wrap the object in a one-item list.
        if isinstance(result, list) and result:
            result = result[0]
        if not isinstance(result, dict):
            return {
                "platform": "generic",
                "content_type": "article",
                "confidence": 0.0,
                "reasoning": "",
            }
        return {
            "platform": result.get("platform", "generic"),
            "content_type": result.get("content_type", "article"),
            "confidence": float(result.get("confidence", 0.0)),
            "reasoning": result.get("reasoning", ""),
        }


__all__ = ["ContentClassifier", "HeuristicContentClassifier"]
