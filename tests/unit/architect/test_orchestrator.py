"""Tests for the PhoenixArchitect orchestrator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from phoenix.architect.orchestrator import PhoenixArchitect
from phoenix.exceptions import UnsupportedURLError
from phoenix.router import URLRouter


@pytest.fixture
def router() -> URLRouter:
    return URLRouter()


@pytest.fixture
def architect(router: URLRouter) -> PhoenixArchitect:
    return PhoenixArchitect(router=router)


def test_find_existing_adapter_for_built_in(
    architect: PhoenixArchitect,
) -> None:
    url = "https://www.instagram.com/p/abc123/"
    adapter = architect.find_existing_adapter(url)
    assert adapter is not None
    assert "instagram" in adapter.manifest.platforms


def test_find_existing_adapter_for_generic(
    architect: PhoenixArchitect,
) -> None:
    url = "https://unknown-site.example.com/article/1"
    adapter = architect.find_existing_adapter(url)
    # Generic adapter is returned for any HTTP(S) URL.
    assert adapter is not None
    assert "generic" in adapter.manifest.platforms


def test_find_existing_adapter_rejects_malformed_url(
    architect: PhoenixArchitect,
) -> None:
    with pytest.raises(UnsupportedURLError):
        architect.find_existing_adapter("not-a-url")


@pytest.mark.asyncio
async def test_classify_uses_heuristic_high_confidence(
    architect: PhoenixArchitect,
) -> None:
    result = await architect.classify(
        "<html><title>Instagram post</title></html>",
        "https://www.instagram.com/p/abc123/",
    )
    assert result["platform"] == "instagram"
    assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_classify_falls_back_when_heuristic_uncertain(
    architect: PhoenixArchitect,
) -> None:
    # No URL hints and minimal HTML -> heuristic confidence is low.
    result = await architect.classify("<html></html>", "https://unknown.example.com/")
    assert result["platform"] == "generic"
    assert result["confidence"] < 0.8


@pytest.mark.asyncio
async def test_explore_uses_browser_explorer(
    architect: PhoenixArchitect,
) -> None:
    snapshot = MagicMock()
    snapshot.url = "https://example.com"
    snapshot.html = "<html></html>"
    snapshot.page_number = 1
    snapshot.title = "Example"

    with patch(
        "phoenix.architect.orchestrator.BrowserExplorer.explore",
        new=AsyncMock(return_value=[snapshot]),
    ) as mock_explore:
        snapshots = await architect.explore("https://example.com", max_pages=1)
        mock_explore.assert_awaited_once_with(
            "https://example.com",
            max_pages=1,
            scroll=True,
        )
        assert snapshots == [snapshot]


@pytest.mark.asyncio
async def test_discover_delegates_to_researcher(architect: PhoenixArchitect) -> None:
    with patch.object(
        architect._researcher,
        "discover",
        new=AsyncMock(return_value=[]),
    ) as mock_discover:
        await architect.discover("test goal", engine="duckduckgo", max_results=5)
        mock_discover.assert_awaited_once_with(
            "test goal",
            engine="duckduckgo",
            max_results=5,
        )
