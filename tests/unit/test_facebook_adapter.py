"""Unit tests for the Facebook platform adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from phoenix.adapters.facebook import FacebookAdapter
from phoenix.collectors.base import StubCollector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
PAGE_URL = "https://www.facebook.com/GreenCityGardens"
POST_URL = "https://www.facebook.com/GreenCityGardens/posts/1122334455667788"


@pytest.fixture
def adapter() -> FacebookAdapter:
    """Return a Facebook adapter instance."""
    return FacebookAdapter()


@pytest.fixture
def facebook_page_html() -> str:
    """Return synthetic Facebook page HTML."""
    return (FIXTURES_DIR / "facebook_page.html").read_text(encoding="utf-8")


@pytest.fixture
def facebook_post_html() -> str:
    """Return synthetic Facebook post HTML."""
    return (FIXTURES_DIR / "facebook_post.html").read_text(encoding="utf-8")


@pytest.fixture
def raw_page_response(facebook_page_html: str) -> RawResponse:
    """Return a RawResponse wrapping the page fixture."""
    return RawResponse(
        url=PAGE_URL,
        final_url=PAGE_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=facebook_page_html,
        strategy="browser",
    )


@pytest.fixture
def raw_post_response(facebook_post_html: str) -> RawResponse:
    """Return a RawResponse wrapping the post fixture."""
    return RawResponse(
        url=POST_URL,
        final_url=POST_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=facebook_post_html,
        strategy="browser",
    )


# ------------------------------------------------------------------
# Manifest and routing
# ------------------------------------------------------------------


def test_facebook_adapter_manifest(adapter: FacebookAdapter) -> None:
    """The manifest describes the Facebook adapter."""
    manifest = adapter.manifest

    assert manifest.name == "facebook"
    assert manifest.platforms == ["facebook"]
    assert manifest.requires_auth is True
    assert manifest.supports_ai_fallback is True
    assert manifest.strategies == ["browser", "http"]


def test_facebook_adapter_supported_patterns(adapter: FacebookAdapter) -> None:
    """Supported patterns match Facebook pages and posts."""
    patterns = adapter.supported_patterns()

    assert len(patterns) == len(adapter.manifest.url_patterns)
    assert any(p.match(PAGE_URL) for p in patterns)
    assert any(p.match(POST_URL) for p in patterns)
    assert any(p.match("https://facebook.com/pages/GreenCityGardens/123") for p in patterns)
    assert not any(p.match("https://twitter.com/user/status/123") for p in patterns)


def test_facebook_adapter_preferred_strategies(adapter: FacebookAdapter) -> None:
    """Facebook prefers browser rendering first."""
    assert adapter.preferred_strategies() == ["browser", "http"]


def test_facebook_adapter_health_check(adapter: FacebookAdapter) -> None:
    """Health check includes auth requirements."""
    health = adapter.health_check()

    assert health["adapter"] == "facebook"
    assert health["requires_auth"] is True
    assert health["supports_ai_fallback"] is True


# ------------------------------------------------------------------
# Collection
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_facebook_adapter_collect_delegates(
    adapter: FacebookAdapter,
    facebook_post_html: str,
) -> None:
    """Collect delegates to the supplied collector."""
    collector = StubCollector(strategy="browser", html=facebook_post_html)

    response = await adapter.collect(POST_URL, "browser", collector, ScrapingOptions())

    assert response.strategy == "browser"
    assert response.url == POST_URL
    assert response.error is None


@pytest.mark.asyncio
async def test_facebook_adapter_collect_flags_login_wall(
    adapter: FacebookAdapter,
) -> None:
    """Collect marks responses behind login walls with an error."""
    html = "<html><body>Please log in to view this content</body></html>"
    collector = StubCollector(strategy="browser", html=html)

    response = await adapter.collect(POST_URL, "browser", collector, ScrapingOptions())

    assert response.error is not None
    assert "authentication" in response.error["message"].lower()


@pytest.mark.asyncio
async def test_facebook_adapter_collect_flags_friends_only(
    adapter: FacebookAdapter,
) -> None:
    """Collect flags friends-only content as non-public."""
    html = "<html><body>This content is only available to friends.</body></html>"
    collector = StubCollector(strategy="browser", html=html)

    response = await adapter.collect(POST_URL, "browser", collector, ScrapingOptions())

    assert response.error is not None
    assert response.error["code"] == "SCR_061"


# ------------------------------------------------------------------
# Page extraction
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_facebook_adapter_extract_page(
    adapter: FacebookAdapter,
    raw_page_response: RawResponse,
) -> None:
    """Extract returns page metadata."""
    extracted = await adapter.extract(raw_page_response)

    assert extracted["content_type"] == "profile"
    assert extracted["name"] == "Green City Gardens"
    assert extracted["category"] == "Nonprofit Organization"
    assert extracted["followers_count"] == 12000
    assert extracted["likes_count"] == 8500
    assert "urban greening" in extracted["description"]
    assert extracted["website"] == "https://greencitygardens.example.org"
    assert len(extracted["recent_posts"]) == 2
    assert extracted["recent_posts"][0]["post_id"] == "1111111111111111"
    assert extracted["selectors_used"]


@pytest.mark.asyncio
async def test_facebook_adapter_extract_page_fallback_selectors(
    adapter: FacebookAdapter,
) -> None:
    """Fallback selectors are used when primary selectors are missing."""
    html = """
    <html><body>
      <div data-page-id="123"><h1>Fallback Page</h1></div>
      <div data-page-category="Community">Community</div>
      <div class="fb-page-about">
        <p>About text</p>
        <a href="/about">About</a>
      </div>
    </body></html>
    """
    raw = RawResponse(
        url=PAGE_URL,
        final_url=PAGE_URL,
        status_code=200,
        headers={},
        html=html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["name"] == "Fallback Page"
    assert extracted["category"] == "Community"
    assert extracted["description"] == "About text"


# ------------------------------------------------------------------
# Post extraction
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_facebook_adapter_extract_post(
    adapter: FacebookAdapter,
    raw_post_response: RawResponse,
) -> None:
    """Extract returns post metadata and engagement counts."""
    extracted = await adapter.extract(raw_post_response)

    assert extracted["content_type"] == "post"
    assert extracted["id"] == "1122334455667788"
    assert extracted["author"] == "Green City Gardens"
    assert extracted["author_url"] == "https://www.facebook.com/GreenCityGardens"
    assert "200 native seedlings" in extracted["text"]
    assert extracted["reaction_count"] == 1500
    assert extracted["comment_count"] == 87
    assert extracted["share_count"] == 24
    assert extracted["reactions_breakdown"]["like"] == 1200
    assert extracted["reactions_breakdown"]["love"] == 280
    assert extracted["reactions_breakdown"]["wow"] == 42
    assert extracted["media_urls"] == ["https://cdn.example.com/fb/garden.jpg"]
    assert extracted["timestamp"] is not None
    assert extracted["is_public"] is True
    assert extracted["selectors_used"]


@pytest.mark.asyncio
async def test_facebook_adapter_extract_post_id_from_url(
    adapter: FacebookAdapter,
) -> None:
    """Post ID falls back to URL when not present in HTML."""
    html = """
    <html><body>
      <article class="fb-story">
        <span class="fb-author">Author</span>
        <div class="fb-user-content post-caption"><p>Text</p></div>
        <time class="timestamp" datetime="2025-01-16T11:45:00+00:00"></time>
      </article>
    </body></html>
    """
    raw = RawResponse(
        url="https://www.facebook.com/page/posts/999888777666555",
        final_url="https://www.facebook.com/page/posts/999888777666555",
        status_code=200,
        headers={},
        html=html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["id"] == "999888777666555"


@pytest.mark.asyncio
async def test_facebook_adapter_extract_private_post(
    adapter: FacebookAdapter,
) -> None:
    """Private posts are detected and extraction notes non-public status."""
    html = "<html><body>This content is only available to friends.</body></html>"
    raw = RawResponse(
        url=POST_URL,
        final_url=POST_URL,
        status_code=200,
        headers={},
        html=html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["is_public"] is False


# ------------------------------------------------------------------
# Normalization
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_facebook_adapter_normalize_page(
    adapter: FacebookAdapter,
    raw_page_response: RawResponse,
) -> None:
    """Normalize maps page fields to UnifiedOutput."""
    extracted = await adapter.extract(raw_page_response)

    output = await adapter.normalize(extracted, PAGE_URL, "browser")

    assert isinstance(output, UnifiedOutput)
    assert output.url == PAGE_URL
    assert output.platform == "facebook"
    assert output.content_type == "profile"
    assert output.title == "Green City Gardens"
    assert output.author == "Green City Gardens"
    assert output.likes == 8500


@pytest.mark.asyncio
async def test_facebook_adapter_normalize_post(
    adapter: FacebookAdapter,
    raw_post_response: RawResponse,
) -> None:
    """Normalize maps post fields to UnifiedOutput."""
    extracted = await adapter.extract(raw_post_response)

    output = await adapter.normalize(extracted, POST_URL, "browser")

    assert isinstance(output, UnifiedOutput)
    assert output.url == POST_URL
    assert output.platform == "facebook"
    assert output.content_type == "post"
    assert output.author == "Green City Gardens"
    assert output.likes == 1500
    assert output.shares == 24
    assert output.comments == 87
    assert output.media_urls == ["https://cdn.example.com/fb/garden.jpg"]
    assert output.timestamp is not None
