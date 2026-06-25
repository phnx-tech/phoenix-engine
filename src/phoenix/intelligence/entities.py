"""Phoenix AI entity extraction and cross-platform resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor


class EntityResolver:
    """Extracts entities and resolves matches across platforms using Phoenix AI."""

    def __init__(self, extractor: PhoenixAIExtractor) -> None:
        """Initialize the resolver with a Phoenix AI extractor instance."""
        self.extractor = extractor

    async def extract_entities(
        self,
        html: str,
        url: str,
        platform: str,
    ) -> list[dict[str, Any]]:
        """Extract named entities from ``html``.

        Args:
            html: Raw HTML content.
            url: Source URL.
            platform: Platform identifier.

        Returns:
            List of entity dicts with ``name``, ``type``, ``handle``, and ``url``.
        """
        schema = (
            "Return a JSON object with an 'entities' array. Each entity has:\n"
            "  name: string\n"
            "  type: string - one of: person, organization, product, location, topic\n"
            "  handle: string or null - social media handle if visible\n"
            "  url: string or null - linked URL if visible\n"
            "  confidence: number between 0.0 and 1.0"
        )
        result = await self.extractor.extract(
            html=html[:24000],
            url=url,
            platform=platform,
            content_type="entity_extraction",
            schema_description=schema,
            strict=False,
        )
        # Local models sometimes wrap or unwrap the entity array.
        if isinstance(result, list):
            if len(result) == 1 and isinstance(result[0], dict) and "entities" in result[0]:
                result = result[0]
            else:
                return result
        entities = result.get("entities", []) if isinstance(result, dict) else []
        if not isinstance(entities, list):
            return []
        return entities

    async def resolve(
        self,
        entity_a: dict[str, Any],
        entity_b: dict[str, Any],
    ) -> dict[str, Any]:
        """Return whether two entity dicts refer to the same real-world entity.

        Args:
            entity_a: First entity dict.
            entity_b: Second entity dict.

        Returns:
            Dict with ``match`` (bool), ``confidence`` (float), and ``reasoning``.
        """
        schema = (
            "Return a JSON object with:\n"
            "  match: boolean - true if the two entities are the same\n"
            "  confidence: number between 0.0 and 1.0\n"
            "  reasoning: string - brief explanation"
        )
        prompt_html = (
            f"Entity A: {entity_a}\n\nEntity B: {entity_b}\n\n"
            "Are these the same real-world entity?"
        )
        result = await self.extractor.extract(
            html=prompt_html,
            url="entity-resolution",
            platform="unknown",
            content_type="entity_resolution",
            schema_description=schema,
            strict=False,
        )
        if isinstance(result, list) and result:
            result = result[0]
        if not isinstance(result, dict):
            return {"match": False, "confidence": 0.0, "reasoning": ""}
        return {
            "match": bool(result.get("match", False)),
            "confidence": float(result.get("confidence", 0.0)),
            "reasoning": result.get("reasoning", ""),
        }


__all__ = ["EntityResolver"]
