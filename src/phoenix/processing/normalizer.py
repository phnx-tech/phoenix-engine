"""Content normalizer for Phoenix Engine.

Transforms extracted HTML fields into the unified output schema.
"""

from __future__ import annotations

from typing import Any

from phoenix.models.output import UnifiedOutput


class Normalizer:
    """Transforms platform-specific extracted data into the unified output schema."""

    def __init__(self) -> None:
        """Initialize the normalizer."""
        return

    async def normalize(  # noqa: PLR0913
        self,
        extracted: dict[str, Any],
        platform: str,
        url: str,
        strategy: str,
        *,
        fallback_triggered: bool = False,
        ai_assisted: bool = False,
    ) -> UnifiedOutput:
        """Convert extracted fields into a :class:`UnifiedOutput`.

        Args:
            extracted: Dictionary of fields returned by the HTML extractor.
            platform: Platform identifier for the source URL.
            url: Normalized source URL.
            strategy: Collection strategy that produced the raw response.
            fallback_triggered: Whether a fallback strategy was used.
            ai_assisted: Whether AI assisted extraction.

        Returns:
            A validated ``UnifiedOutput`` instance with extraction metadata and
            confidence scores.
        """
        field_confidences = self._build_field_confidences(extracted)
        confidence = self._overall_confidence(
            field_confidences,
            fallback_triggered=fallback_triggered,
            ai_assisted=ai_assisted,
        )

        output_data: dict[str, Any] = {
            **extracted,
            "platform": platform,
            "url": url,
            "scraping_strategy": strategy,
            "field_confidences": field_confidences,
            "confidence": confidence,
        }
        output_data.setdefault("content_type", "post")
        output_data.setdefault("media_urls", [])
        output_data.setdefault("tags", [])
        output_data.setdefault("selectors_used", [])
        return UnifiedOutput(**output_data)

    @staticmethod
    def _build_field_confidences(extracted: dict[str, Any]) -> dict[str, float]:
        """Return confidence scores for each field in ``extracted``.

        Explicit ``{field}_confidence`` keys are used when present. Otherwise a
        simple presence/non-empty heuristic is applied.
        """
        confidences: dict[str, float] = {}
        for key in list(extracted.keys()):
            if key.endswith("_confidence"):
                continue
            explicit = extracted.get(f"{key}_confidence")
            if isinstance(explicit, float):
                confidences[key] = max(0.0, min(1.0, explicit))
            elif isinstance(explicit, list) and explicit:
                # List of per-element confidences; use mean.
                confidences[key] = (
                    sum(max(0.0, min(1.0, v)) for v in explicit if isinstance(v, (int, float)))
                    / len([v for v in explicit if isinstance(v, (int, float))])
                    if [v for v in explicit if isinstance(v, (int, float))]
                    else 0.0
                )
            else:
                confidences[key] = _presence_confidence(extracted[key])
        return confidences

    @staticmethod
    def _overall_confidence(
        field_confidences: dict[str, float],
        *,
        fallback_triggered: bool,
        ai_assisted: bool,
    ) -> float:
        """Compute an overall confidence from per-field scores and pipeline flags."""
        if not field_confidences:
            return 0.0
        score = sum(field_confidences.values()) / len(field_confidences)
        if fallback_triggered or ai_assisted:
            score *= 0.8
        return round(max(0.0, min(1.0, score)), 4)


def _presence_confidence(value: object) -> float:
    """Return a naive confidence based on whether ``value`` is present and non-empty."""
    if value is None:
        return 0.0
    if isinstance(value, str) and value.strip() == "":
        return 0.0
    if isinstance(value, list) and not value:
        return 0.0
    if isinstance(value, dict) and not value:
        return 0.0
    return 1.0


# Public alias used in Architecture v2.0.0.
ContentNormalizer = Normalizer


__all__ = ["ContentNormalizer", "Normalizer"]
