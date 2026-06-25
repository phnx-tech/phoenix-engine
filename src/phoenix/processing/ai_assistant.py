"""AI assistant wrapper around PhoenixAIExtractor.

Provides AI-powered selector generation and extraction fallback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, cast

from phoenix.models.output import UnifiedOutput
from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor

if TYPE_CHECKING:
    from phoenix.models.document import RawResponse


class AIAssistant:
    """Wraps :class:`PhoenixAIExtractor` for Phoenix Engine AI-assisted extraction."""

    _UNIFIED_FIELDS: ClassVar[list[tuple[str, str, str]]] = [
        ("title", "string or null", "Content title or headline."),
        ("text", "string or null", "Main text content."),
        ("author", "string or null", "Content author or username."),
        ("author_url", "string or null", "Author profile URL."),
        ("timestamp", "ISO 8601 datetime string or null", "Publication timestamp."),
        ("likes", "integer or null", "Like/reaction count."),
        ("shares", "integer or null", "Share/repost count."),
        ("comments", "integer or null", "Comment count."),
        ("views", "integer or null", "View count."),
        ("media_urls", "list of strings", "URLs of images/videos."),
        ("thumbnail_url", "string or null", "Thumbnail/preview image URL."),
        ("tags", "list of strings", "Hashtags, mentions, or topics."),
        (
            "content_type",
            "string",
            f"Type of content (e.g. {UnifiedOutput.model_fields['content_type'].default}).",
        ),
    ]

    def __init__(self, extractor: PhoenixAIExtractor | None = None) -> None:
        """Initialize the AI assistant.

        Args:
            extractor: Optional :class:`PhoenixAIExtractor` instance.
        """
        self.extractor = extractor or PhoenixAIExtractor()

    @classmethod
    def _build_schema_description(cls) -> str:
        """Build a schema description from :class:`UnifiedOutput` fields."""
        lines = ["Return a JSON object with the following fields:"]
        for name, json_type, description in cls._UNIFIED_FIELDS:
            lines.append(f"  {name}: {json_type} - {description}")
        lines.append("Fields that are not present in the HTML should be set to null.")
        return "\n".join(lines)

    async def extract(
        self,
        raw_response: RawResponse,
        platform: str,
        content_type: str,
    ) -> dict[str, Any]:
        """Extract structured data from ``raw_response`` using Phoenix AI.

        Args:
            raw_response: Raw response from a collector.
            platform: Platform identifier.
            content_type: Type of content.

        Returns:
            Parsed JSON dict with extracted fields.
        """
        schema_description = self._build_schema_description()
        url = raw_response.final_url or raw_response.url
        result = await self.extractor.extract(
            html=raw_response.html,
            url=url,
            platform=platform,
            content_type=content_type,
            schema_description=schema_description,
        )
        return cast("dict[str, Any]", result)

    async def suggest_selectors(
        self,
        html_sample: str,
        old_selectors: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Request updated CSS selectors from Phoenix AI.

        Args:
            html_sample: Representative HTML from the new layout.
            old_selectors: Field-to-selector mapping that previously worked.

        Returns:
            List of selector suggestions.
        """
        return await self.extractor.suggest_selectors(html_sample, old_selectors)


__all__ = ["AIAssistant"]
