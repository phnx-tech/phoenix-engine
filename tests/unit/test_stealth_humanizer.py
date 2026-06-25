"""Unit tests for the humanizer component."""

from __future__ import annotations

import pytest

from phoenix.stealth.humanizer import Humanizer

pytestmark = pytest.mark.unit


def test_humanizer_disabled_when_delays_zero() -> None:
    """A humanizer with no delays or scrolling is not enabled."""
    humanizer = Humanizer(delay_min_ms=0, delay_max_ms=0, scroll_pages=0)
    assert humanizer.enabled is False


def test_humanizer_enabled_with_delays() -> None:
    """A humanizer with positive max delay is enabled."""
    humanizer = Humanizer(delay_min_ms=100, delay_max_ms=500)
    assert humanizer.enabled is True


def test_humanizer_validates_delay_bounds() -> None:
    """Negative delays or min > max raise ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        Humanizer(delay_min_ms=-1, delay_max_ms=100)
    with pytest.raises(ValueError, match="delay_min_ms"):
        Humanizer(delay_min_ms=500, delay_max_ms=100)


@pytest.mark.asyncio
async def test_humanizer_before_navigation_non_blocking_when_disabled() -> None:
    """before_navigation returns immediately when disabled."""
    humanizer = Humanizer()
    await humanizer.before_navigation()


@pytest.mark.asyncio
async def test_humanizer_after_load_with_zero_scroll_pages() -> None:
    """after_load is safe when no scrolling is configured."""
    humanizer = Humanizer(scroll_pages=0)
    await humanizer.after_load(None)  # type: ignore[arg-type]
