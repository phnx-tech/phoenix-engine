"""Tests for the example Hacker News plugin."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the example plugin importable during tests.
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples" / "plugin"
sys.path.insert(0, str(EXAMPLES_DIR))

from hackernews import HackerNewsAdapter  # noqa: E402

pytestmark = pytest.mark.unit

URL = "https://news.ycombinator.com/item?id=12345"


@pytest.fixture
def adapter() -> HackerNewsAdapter:
    """Return a Hacker News adapter instance."""
    return HackerNewsAdapter()


def test_example_plugin_manifest(adapter: HackerNewsAdapter) -> None:
    """A plugin exposes a valid manifest."""
    manifest = adapter.manifest
    assert manifest.name == "hackernews"
    assert manifest.version == "0.1.0"
    assert "hackernews" in manifest.platforms
    assert manifest.requires_auth is False


def test_example_plugin_supported_patterns(adapter: HackerNewsAdapter) -> None:
    """The adapter matches Hacker News item URLs."""
    patterns = adapter.supported_patterns()
    assert any(p.match(URL) for p in patterns)
    assert not any(p.match("https://example.com/article/123") for p in patterns)


@pytest.mark.asyncio
async def test_example_plugin_extract(adapter: HackerNewsAdapter) -> None:
    """The adapter extracts fields from synthetic Hacker News HTML."""
    from phoenix.models.document import RawResponse

    html = """
    <html>
    <body>
        <tr class="athing">
            <td class="title">
                <span class="titleline"><a>Example Title</a></span>
            </td>
        </tr>
        <a class="hnuser">alice</a>
        <span class="score">128 points</span>
        <span class="age"><a>2 hours ago</a></span>
    </body>
    </html>
    """
    raw = RawResponse(
        url=URL,
        final_url=URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "post"
    assert extracted["title"] == "Example Title"
    assert extracted["author_username"] == "alice"
    assert extracted["score"] == 128
    assert extracted["timestamp"] is not None


@pytest.mark.asyncio
async def test_example_plugin_normalize(adapter: HackerNewsAdapter) -> None:
    """The adapter normalizes extracted fields to UnifiedOutput."""
    from phoenix.models.document import RawResponse
    from phoenix.models.output import UnifiedOutput

    html = """
    <html><body>
        <span class="titleline"><a>Example Title</a></span>
        <a class="hnuser">alice</a>
        <span class="score">128 points</span>
    </body></html>
    """
    raw = RawResponse(
        url=URL,
        final_url=URL,
        status_code=200,
        headers={},
        html=html,
        strategy="http",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, URL, "http")

    assert isinstance(output, UnifiedOutput)
    assert output.url == URL
    assert output.platform == "hackernews"
    assert output.author == "alice"
    assert output.likes == 128
