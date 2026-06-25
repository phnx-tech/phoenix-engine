"""Output data models for Phoenix Engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class UnifiedOutput(BaseModel):
    """Standardized output format for all scraped content."""

    model_config = ConfigDict(extra="allow")

    url: str = Field(..., description="Source URL.")
    platform: str = Field(..., description="Platform identifier.")
    content_type: str = Field(default="post", description="Type of content.")
    title: str | None = Field(default=None, description="Content title or headline.")
    text: str | None = Field(default=None, description="Main text content.")
    author: str | None = Field(default=None, description="Content author.")
    author_url: str | None = Field(default=None, description="Author profile URL.")
    timestamp: datetime | None = Field(default=None, description="Publication timestamp.")
    likes: int | None = Field(default=None, description="Like count.")
    shares: int | None = Field(default=None, description="Share count.")
    comments: int | None = Field(default=None, description="Comment count.")
    views: int | None = Field(default=None, description="View count.")
    media_urls: list[str] = Field(default_factory=list, description="Media URLs.")
    thumbnail_url: str | None = Field(default=None, description="Thumbnail/preview image URL.")
    tags: list[str] = Field(default_factory=list, description="Hashtags and mentions.")
    scraped_at: datetime = Field(default_factory=_utc_now, description="Scrape timestamp.")
    scraping_strategy: str | None = Field(default=None, description="Strategy used.")
    selectors_used: list[str] = Field(default_factory=list, description="Selectors used.")
    ai_assisted: bool = Field(default=False, description="Whether AI assisted extraction.")
    archive_id: str | None = Field(default=None, description="Archive identifier.")
    field_confidences: dict[str, float] = Field(
        default_factory=dict,
        description="Confidence score (0.0-1.0) for each extracted field.",
    )
    confidence: float = Field(
        default=0.0,
        description="Overall extraction confidence (0.0-1.0).",
    )


class ScrapingResult(BaseModel):
    """Result of a scraping operation."""

    success: bool = Field(..., description="Whether the operation succeeded.")
    url: str | None = Field(default=None, description="Source URL.")
    output: UnifiedOutput | None = Field(default=None, description="Extracted data.")
    error: dict[str, Any] | None = Field(default=None, description="Error information.")
    selectors_used: list[str] = Field(default_factory=list, description="Selectors used.")
    fallback_triggered: bool = Field(default=False, description="Whether fallback was used.")
    ai_assisted: bool = Field(default=False, description="Whether AI assisted.")
    timing_ms: dict[str, int] = Field(default_factory=dict, description="Timing breakdown.")
    archived_path: str | None = Field(default=None, description="Path to archived HTML.")
    adapter_confidence: float | None = Field(
        default=None,
        description="Confidence score of the adapter that produced this result.",
    )
    diagnostics: Diagnostics | None = Field(
        default=None,
        description="Diagnostic information for the operation.",
    )


# Backward-compatible alias retained for existing consumers.
CollectionResult = ScrapingResult


class ChangeAlert(BaseModel):
    """Alert emitted when a page's structure or selectors drift."""

    model_config = ConfigDict(frozen=True)

    alert_type: str = Field(..., description="Alert category, e.g. structural_change.")
    severity: str = Field(default="info", description="Alert severity: info, warning, critical.")
    url: str = Field(..., description="URL that triggered the alert.")
    platform: str = Field(..., description="Platform identifier.")
    content_type: str | None = Field(default=None, description="Content type if known.")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Comparison details for the alert.",
    )
    baseline_id: str | None = Field(default=None, description="Identifier of the baseline used.")
    timestamp: datetime = Field(default_factory=_utc_now, description="When the alert was raised.")


class ErrorRecord(BaseModel):
    """Immutable audit/error log record for a failed scrape action."""

    model_config = ConfigDict(frozen=True)

    error_id: str = Field(..., description="Unique error identifier.")
    code: str = Field(..., description="Error code (e.g. SCR_010).")
    message: str = Field(..., description="Human-readable error message.")
    url: str | None = Field(default=None, description="URL that triggered the error.")
    timestamp: datetime = Field(default_factory=_utc_now, description="When the error occurred.")
    platform: str | None = Field(default=None, description="Platform identifier.")
    strategy: str | None = Field(default=None, description="Strategy that failed.")
    http_status: int | None = Field(default=None, description="HTTP status code.")
    selectors_tried: list[str] = Field(
        default_factory=list,
        description="Selectors attempted before failure.",
    )
    html_snippet: str | None = Field(default=None, description="Relevant HTML for debugging.")
    suggested_fix: str | None = Field(default=None, description="Suggested resolution.")


class Diagnostics(BaseModel):
    """Diagnostic information collected during a scraping operation."""

    model_config = ConfigDict(populate_by_name=True)

    url: str = Field(..., description="URL being scraped.")
    platform: str | None = Field(default=None, description="Platform identifier.")
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When diagnostics were captured.",
    )
    primary_strategy: str | None = Field(
        default=None,
        alias="strategy_used",
        description="Primary strategy that was used.",
    )
    strategies_attempted: list[str] = Field(
        default_factory=list,
        description="Strategies attempted in order.",
    )
    selectors_tried: list[str] = Field(
        default_factory=list,
        description="Selectors tried during extraction.",
    )
    selector_health: dict[str, Any] = Field(
        default_factory=dict,
        description="Selector health snapshot.",
    )
    http_status: int | None = Field(default=None, description="HTTP response status.")
    response_headers: dict[str, Any] = Field(
        default_factory=dict,
        description="HTTP response headers.",
    )
    html_size_bytes: int = Field(default=0, description="Size of raw HTML in bytes.")
    timing: dict[str, float] = Field(default_factory=dict, description="Timing breakdown.")
    retries: int = Field(default=0, description="Number of retries performed.")
    ai_assisted: bool = Field(
        default=False,
        description="Whether AI assisted extraction.",
    )
    ai_model: str | None = Field(
        default=None,
        description="AI model used for extraction.",
    )
    ai_tokens_used: int = Field(
        default=0,
        description="Total tokens consumed by AI extraction.",
    )
    change_alert: dict[str, Any] | None = Field(
        default=None,
        description="Change-detection alert, if any.",
    )

    @property
    def strategy_used(self) -> str | None:
        """Backward-compatible alias for :attr:`primary_strategy`."""
        return self.primary_strategy


__all__ = [
    "ChangeAlert",
    "CollectionResult",
    "Diagnostics",
    "ErrorRecord",
    "ScrapingResult",
    "UnifiedOutput",
]
