"""Tests for ``phoenix.architect.explorer.BrowserExplorer``."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from phoenix.architect.explorer import BrowserExplorer, PageSnapshot


@pytest.fixture
def mock_page() -> MagicMock:
    """Return a mock Playwright page with async methods."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(return_value="<html></html>")
    page.title = AsyncMock(return_value="Test")
    page.url = "https://example.com/page1"
    page.viewport_size = {"width": 1280, "height": 720}
    page.query_selector = AsyncMock(return_value=None)
    page.click = AsyncMock()
    page.evaluate = AsyncMock(return_value=1000)
    page.is_visible = AsyncMock(return_value=True)
    page.close = AsyncMock()
    page.mouse.move = AsyncMock()
    page.mouse.wheel = AsyncMock()
    return page


@pytest.fixture
def mock_context(mock_page: MagicMock) -> MagicMock:
    """Return a mock browser context that yields ``mock_page``."""
    context = MagicMock()
    context.new_page = AsyncMock(return_value=mock_page)
    context.close = AsyncMock()
    return context


@pytest.fixture
def mock_pool(mock_context: MagicMock) -> MagicMock:
    """Return a mock browser pool that yields ``mock_context``."""
    pool = MagicMock()
    pool.acquire = AsyncMock(return_value=mock_context)
    pool.release = AsyncMock()
    return pool


@pytest.fixture
def explorer(mock_pool: MagicMock) -> BrowserExplorer:
    """Return a ``BrowserExplorer`` wired to ``mock_pool``."""
    return BrowserExplorer(mock_pool, page_load_wait=0.0)


@pytest.mark.asyncio
async def test_explore_single_page_no_pagination(
    explorer: BrowserExplorer,
    mock_page: MagicMock,
    mock_pool: MagicMock,
) -> None:
    """A single page is captured when no pagination exists."""
    snapshots = await explorer.explore("https://example.com/list", max_pages=1)

    assert len(snapshots) == 1
    assert snapshots[0].page_number == 1
    assert snapshots[0].url == "https://example.com/page1"
    mock_page.goto.assert_called_once()
    mock_pool.acquire.assert_awaited_once()
    mock_pool.release.assert_awaited_once()


@pytest.mark.asyncio
async def test_explore_follows_next_link(
    explorer: BrowserExplorer,
    mock_page: MagicMock,
) -> None:
    """The explorer follows a "Next" pagination link across pages."""
    next_button = MagicMock()
    next_button.is_visible = AsyncMock(return_value=True)

    async def query_selector(selector: str) -> MagicMock | None:
        if selector == 'a:has-text("Next")':
            return next_button
        return None

    mock_page.query_selector = query_selector
    mock_page.url = "https://example.com/page1"

    snapshots = await explorer.explore("https://example.com/list", max_pages=2)

    assert len(snapshots) == 2
    assert snapshots[0].page_number == 1
    assert snapshots[1].page_number == 2
    assert mock_page.click.await_count == 1


@pytest.mark.asyncio
async def test_explore_numbered_pagination(
    explorer: BrowserExplorer,
    mock_page: MagicMock,
) -> None:
    """The explorer prefers numbered pagination links."""
    page_two = MagicMock()
    page_two.is_visible = AsyncMock(return_value=True)

    async def query_selector(selector: str) -> MagicMock | None:
        if selector == 'a:has-text("2")':
            return page_two
        return None

    mock_page.query_selector = query_selector

    snapshots = await explorer.explore("https://example.com/list", max_pages=2)

    assert len(snapshots) == 2
    assert mock_page.click.await_count == 1


@pytest.mark.asyncio
async def test_explore_stops_when_no_pagination(
    explorer: BrowserExplorer,
    mock_page: MagicMock,
) -> None:
    """Exploration stops early if no further pagination is found."""
    snapshots = await explorer.explore("https://example.com/list", max_pages=5)

    assert len(snapshots) == 1
    mock_page.click.assert_not_awaited()


@pytest.mark.asyncio
async def test_explore_scrolls_page(
    explorer: BrowserExplorer,
    mock_page: MagicMock,
) -> None:
    """Scrolling is performed when ``scroll=True``."""
    # Stable scroll height after first attempt to keep the test fast.
    mock_page.evaluate = AsyncMock(return_value=1000)

    await explorer.explore("https://example.com/list", max_pages=1, scroll=True)

    assert mock_page.evaluate.await_count >= 1


@pytest.mark.asyncio
async def test_explore_invalid_max_pages(explorer: BrowserExplorer) -> None:
    """An invalid ``max_pages`` value raises immediately."""
    with pytest.raises(ValueError, match="max_pages must be >= 1"):
        await explorer.explore("https://example.com/list", max_pages=0)


@pytest.mark.asyncio
async def test_snapshot_dataclass() -> None:
    """``PageSnapshot`` stores captured page state."""
    snap = PageSnapshot(
        url="https://example.com/page1",
        html="<html></html>",
        page_number=1,
        title="Example",
    )
    assert snap.url == "https://example.com/page1"
    assert snap.html == "<html></html>"
    assert snap.page_number == 1
    assert snap.title == "Example"
