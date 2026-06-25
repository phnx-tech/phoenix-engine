"""Phoenix AI CSS selector repair for Phoenix Engine adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor


class SelectorRepair:
    """Repairs broken CSS selectors after site layout changes using Phoenix AI."""

    def __init__(self, extractor: PhoenixAIExtractor) -> None:
        """Initialize with a Phoenix AI extractor instance."""
        self.extractor = extractor

    async def repair(
        self,
        html_sample: str,
        old_selectors: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Suggest replacement selectors for ``old_selectors``.

        Args:
            html_sample: Representative HTML from the new layout.
            old_selectors: Field-to-selector mapping that previously worked.

        Returns:
            List of suggestions with ``field``, ``old``, ``new``, ``confidence``.
        """
        return await self.extractor.suggest_selectors(html_sample, old_selectors)


__all__ = ["SelectorRepair"]
