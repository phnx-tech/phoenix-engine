"""Strategy selection data model."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ScrapingStrategy(StrEnum):
    """Supported scraping strategies."""

    HTTP = "http"
    BROWSER = "browser"


class StrategySelection(BaseModel):
    """Selected scraping strategy with fallback chain."""

    primary: str = Field(..., description="Primary strategy ('http' or 'browser').")
    fallbacks: list[str] = Field(
        default_factory=list,
        description="Ordered list of fallback strategies.",
    )
    reason: str = Field(default="", description="Human-readable selection rationale.")


__all__ = ["ScrapingStrategy", "StrategySelection"]
