"""Unit tests for the Phoenix Engine strategy selector."""

from __future__ import annotations

import pytest

from phoenix.infrastructure.storage import SQLiteStorageBackend
from phoenix.models import Config
from phoenix.processing.domain_memory import DomainMemory
from phoenix.strategy_selector import StrategySelector

pytestmark = pytest.mark.unit


@pytest.fixture
def selector() -> StrategySelector:
    """Return a StrategySelector with default config."""
    return StrategySelector(Config())


@pytest.mark.parametrize(
    ("platform", "expected_primary", "expected_fallbacks"),
    [
        ("instagram", "browser", ["http"]),
        ("tiktok", "browser", ["http"]),
        ("linkedin", "browser", ["http"]),
        ("facebook", "browser", ["http"]),
        ("x", "http", ["browser"]),
        ("youtube", "http", ["browser"]),
        ("generic", "http", ["browser"]),
    ],
)
async def test_strategy_selector_default_rules(
    selector: StrategySelector,
    platform: str,
    expected_primary: str,
    expected_fallbacks: list[str],
) -> None:
    """Default platform rules select the expected primary and fallbacks."""
    selection = await selector.select("https://example.com/path", platform)

    assert selection.primary == expected_primary
    assert selection.fallbacks == expected_fallbacks


async def test_strategy_selector_user_override_wins(selector: StrategySelector) -> None:
    """User override takes precedence over default rules."""
    selection = await selector.select(
        "https://instagram.com/p/123",
        "instagram",
        user_override="http",
    )

    assert selection.primary == "http"
    assert "browser" in selection.fallbacks


async def test_strategy_selector_invalid_override_raises(selector: StrategySelector) -> None:
    """Invalid strategy overrides raise ValueError."""
    with pytest.raises(ValueError, match="Invalid strategy override"):
        await selector.select("https://example.com", "generic", user_override="api")


async def test_strategy_selector_domain_memory_browser(selector: StrategySelector) -> None:
    """Domain memory can promote browser to primary."""
    selector.record_success("https://example.com/page", "browser")

    selection = await selector.select("https://example.com/other", "generic")

    assert selection.primary == "browser"


async def test_strategy_selector_domain_memory_http(selector: StrategySelector) -> None:
    """Domain memory can promote http to primary."""
    selector.record_success("https://instagram.com/p/123", "http")

    selection = await selector.select("https://instagram.com/p/456", "instagram")

    assert selection.primary == "http"


async def test_strategy_selector_reason_included(selector: StrategySelector) -> None:
    """Selection includes a human-readable reason."""
    selection = await selector.select("https://x.com/user/status/123", "x")

    assert selection.reason


@pytest.mark.asyncio
async def test_strategy_selector_uses_persistent_domain_memory() -> None:
    """Persisted domain memory influences strategy selection."""
    storage = SQLiteStorageBackend(path=":memory:")
    try:
        memory = DomainMemory(storage=storage)
        await memory.record_success(
            "https://example.com/post/1",
            "browser",
            {},
            None,
        )

        selector = StrategySelector(Config(), domain_memory=memory)
        selection = await selector.select("https://example.com/other", "generic")

        assert selection.primary == "browser"
    finally:
        storage.close()
