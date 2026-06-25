"""Scraping options passed to scrapers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ScrapingOptions(BaseModel):
    """Options controlling a single scraping operation."""

    model_config = ConfigDict(populate_by_name=True)

    timeout: float = Field(default=30.0, description="Request timeout in seconds.")
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for transient failures.",
    )
    archive: bool = Field(default=True, description="Whether to archive raw source data.")
    strategy: str | None = Field(
        default=None,
        alias="strategy_override",
        description="Force a specific scraping strategy.",
    )
    include_comments: bool = Field(
        default=False,
        description="Whether to include comments when available.",
    )
    scroll_pages: int = Field(
        default=0,
        description="Number of pages to scroll for infinite-scroll content.",
    )
    stealth_enabled: bool | None = Field(
        default=None,
        description="Override config stealth enable flag.",
    )
    stealth_profile: str | None = Field(
        default=None,
        description="Override the stealth profile preset to use.",
    )
    proxy: str | None = Field(
        default=None,
        description="Override proxy URL for this request.",
    )
    humanize: bool | None = Field(
        default=None,
        description="Override human-like delays and gestures.",
    )
    warm_session: bool | None = Field(
        default=None,
        description="Override session warming behavior.",
    )
    captcha_action: str | None = Field(
        default=None,
        description="Override CAPTCHA detection action: 'flag', 'raise', or 'skip'.",
    )

    @property
    def strategy_override(self) -> str | None:
        """Backward-compatible alias for :attr:`strategy`."""
        return self.strategy


# Backward-compatible alias retained for existing consumers.
CollectionOptions = ScrapingOptions


__all__ = ["CollectionOptions", "ScrapingOptions"]
