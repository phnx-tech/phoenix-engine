"""Unit tests for session warming."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from phoenix.stealth.warming import SessionWarming

pytestmark = pytest.mark.unit


def test_session_warming_requires_warm_urls() -> None:
    """Empty warm URL list raises ValueError."""
    with pytest.raises(ValueError, match="at least one warm URL"):
        SessionWarming(warm_urls=[])


def test_session_warming_validates_visit_count() -> None:
    """Negative visits raise ValueError."""
    with pytest.raises(ValueError, match="visits must be non-negative"):
        SessionWarming(visits=-1)


@pytest.mark.asyncio
async def test_session_warming_visits_benign_pages() -> None:
    """Warming navigates to the configured URLs and closes the page."""
    context = MagicMock()
    page = MagicMock()
    context.new_page = AsyncMock(return_value=page)
    page.goto = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.close = AsyncMock()

    warming = SessionWarming(warm_urls=["https://example.com"], visits=1, wait_seconds=0.1)
    await warming.warm(context)

    context.new_page.assert_awaited_once()
    page.goto.assert_awaited_once_with(
        "https://example.com",
        wait_until="domcontentloaded",
        timeout=15000,
    )
    page.close.assert_awaited_once()
