"""Unit tests for the Instagram adapter."""

from __future__ import annotations

import pytest

from phoenix.adapters.instagram import InstagramAdapter
from phoenix.collectors.base import StubCollector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit

POST_URL = "https://instagram.com/p/ABC123/"
PROFILE_URL = "https://instagram.com/sampleuser/"
REEL_URL = "https://instagram.com/reel/DEF456/"


@pytest.fixture
def adapter() -> InstagramAdapter:
    """Return an Instagram adapter instance."""
    return InstagramAdapter()


@pytest.fixture
def post_html() -> str:
    """Return synthetic Instagram post HTML."""
    return """
    <html>
    <head>
        <meta property="og:title" content="A sample Instagram post caption #sample #phoenix">
        <meta property="og:image" content="https://instagram.com/static/sample-image.jpg">
    </head>
    <body>
        <article class="_aatb">
            <header><a href="/sampleuser/">sampleuser</a></header>
            <div class="_a9zs"><h1>A sample Instagram post caption #sample #phoenix</h1></div>
            <time datetime="2025-01-15T10:30:00+00:00">January 15</time>
            <section><span class="_aacl">1,234 likes</span></section>
            <a href="/p/ABC123/comments/"><span>56 comments</span></a>
            <img src="https://instagram.com/static/sample-image.jpg" alt="Post">
        </article>
    </body>
    </html>
    """


@pytest.fixture
def profile_html() -> str:
    """Return synthetic Instagram profile HTML."""
    return """
    <html>
    <head>
        <meta property="og:title" content="Sample User (@sampleuser) • Instagram">
        <meta property="og:description" content="This is a sample Instagram bio.">
    </head>
    <body>
        <header>
            <h2>Sample User</h2>
            <div class="_aa_c"><span>This is a sample Instagram bio.</span></div>
            <ul>
                <li><span>1.2M</span> followers</li>
                <li><span>500</span> following</li>
                <li><span>150</span> posts</li>
            </ul>
        </header>
        <main>
            <img src="https://instagram.com/static/post1.jpg" alt="Post 1">
            <img src="https://instagram.com/static/post2.jpg" alt="Post 2">
        </main>
    </body>
    </html>
    """


@pytest.fixture
def reel_html() -> str:
    """Return synthetic Instagram Reel HTML."""
    return """
    <html>
    <head>
        <meta property="og:title" content="Sample Reel by sampleuser">
        <meta property="og:image" content="https://instagram.com/static/reel-cover.jpg">
    </head>
    <body>
        <header><a href="/sampleuser/">sampleuser</a></header>
        <div class="_a9zs"><span>Sample reel caption #reel #phoenix</span></div>
        <div class="views-section"><span class="_aacl">1.2M views</span></div>
        <section><span class="_aacl">45.6K likes</span></section>
        <time datetime="2025-02-20T18:45:00+00:00">February 20</time>
        <img src="https://instagram.com/static/reel-cover.jpg" alt="Reel cover">
    </body>
    </html>
    """


@pytest.fixture
def post_fallback_html() -> str:
    """Return synthetic post HTML that exercises fallback selectors."""
    return """
    <html>
    <head>
        <meta property="og:title" content="Fallback caption #fallback">
        <meta property="og:image" content="https://instagram.com/static/fallback.jpg">
    </head>
    <body>
        <article>
            <header><a href="/fallbackuser/">fallbackuser</a></header>
            <div class="_a9zs"><span>Fallback caption #fallback</span></div>
            <time datetime="2025-03-10T12:00:00+00:00">March 10</time>
            <section><span class="_aacl">789 likes</span></section>
            <a href="/p/XYZ/comments/"><span>12 comments</span></a>
            <img src="https://instagram.com/static/fallback.jpg" alt="Fallback post">
        </article>
    </body>
    </html>
    """


def test_instagram_adapter_manifest(adapter: InstagramAdapter) -> None:
    """The Instagram manifest describes the adapter."""
    manifest = adapter.manifest
    assert manifest.name == "instagram"
    assert "instagram" in manifest.platforms
    assert manifest.requires_auth is False
    assert manifest.supports_ai_fallback is True


def test_instagram_adapter_patterns(adapter: InstagramAdapter) -> None:
    """The adapter matches Instagram URLs."""
    patterns = adapter.supported_patterns()
    assert any(p.match(POST_URL) for p in patterns)
    assert any(p.match(PROFILE_URL) for p in patterns)
    assert any(p.match(REEL_URL) for p in patterns)


def test_instagram_adapter_preferred_strategies(adapter: InstagramAdapter) -> None:
    """Instagram prefers browser rendering."""
    assert adapter.preferred_strategies() == ["browser", "http"]


@pytest.mark.asyncio
async def test_instagram_post_extract(adapter: InstagramAdapter, post_html: str) -> None:
    """Extract returns post fields from synthetic HTML."""
    raw = RawResponse(
        url=POST_URL,
        final_url=POST_URL,
        status_code=200,
        headers={},
        html=post_html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "post"
    assert "sample Instagram post" in extracted["caption"]
    assert extracted["author_username"] == "sampleuser"
    assert extracted["likes_count"] == 1234
    assert extracted["comments_count"] == 56
    assert "#sample" in extracted["tags"]
    assert "https://instagram.com/static/sample-image.jpg" in extracted["media_urls"]
    assert extracted["timestamp"] is not None


@pytest.mark.asyncio
async def test_instagram_profile_extract(adapter: InstagramAdapter, profile_html: str) -> None:
    """Extract returns profile fields from synthetic HTML."""
    raw = RawResponse(
        url=PROFILE_URL,
        final_url=PROFILE_URL,
        status_code=200,
        headers={},
        html=profile_html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "profile"
    assert extracted["author_username"] == "sampleuser"
    assert extracted["follower_count"] == 1_200_000
    assert extracted["following_count"] == 500
    assert extracted["posts_count"] == 150
    assert any("post1.jpg" in url for url in extracted["recent_post_thumbnails"])


@pytest.mark.asyncio
async def test_instagram_reel_extract(adapter: InstagramAdapter, reel_html: str) -> None:
    """Extract returns Reel fields from synthetic HTML."""
    raw = RawResponse(
        url=REEL_URL,
        final_url=REEL_URL,
        status_code=200,
        headers={},
        html=reel_html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "reel"
    assert "Sample reel caption" in extracted["caption"]
    assert extracted["author_username"] == "sampleuser"
    assert extracted["views_count"] == 1_200_000
    assert extracted["likes_count"] == 45_600
    assert "#reel" in extracted["tags"]
    assert extracted["timestamp"] is not None


@pytest.mark.asyncio
async def test_instagram_normalize(adapter: InstagramAdapter, post_html: str) -> None:
    """Normalize converts extracted post fields to UnifiedOutput."""
    raw = RawResponse(
        url=POST_URL,
        final_url=POST_URL,
        status_code=200,
        headers={},
        html=post_html,
        strategy="browser",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, POST_URL, "browser")

    assert isinstance(output, UnifiedOutput)
    assert output.url == POST_URL
    assert output.platform == "instagram"
    assert output.content_type == "post"
    assert output.author == "sampleuser"
    assert output.likes == 1234


@pytest.mark.asyncio
async def test_instagram_profile_normalize(
    adapter: InstagramAdapter,
    profile_html: str,
) -> None:
    """Normalize converts extracted profile fields to UnifiedOutput."""
    raw = RawResponse(
        url=PROFILE_URL,
        final_url=PROFILE_URL,
        status_code=200,
        headers={},
        html=profile_html,
        strategy="browser",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, PROFILE_URL, "browser")

    assert isinstance(output, UnifiedOutput)
    assert output.url == PROFILE_URL
    assert output.platform == "instagram"
    assert output.content_type == "profile"
    assert output.author == "sampleuser"
    assert output.follower_count == 1_200_000
    assert output.following_count == 500


@pytest.mark.asyncio
async def test_instagram_reel_normalize(adapter: InstagramAdapter, reel_html: str) -> None:
    """Normalize converts extracted Reel fields to UnifiedOutput."""
    raw = RawResponse(
        url=REEL_URL,
        final_url=REEL_URL,
        status_code=200,
        headers={},
        html=reel_html,
        strategy="browser",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, REEL_URL, "browser")

    assert isinstance(output, UnifiedOutput)
    assert output.url == REEL_URL
    assert output.platform == "instagram"
    assert output.content_type == "reel"
    assert output.views == 1_200_000
    assert output.likes == 45_600


@pytest.mark.asyncio
async def test_instagram_post_extract_fallback_selectors(
    adapter: InstagramAdapter,
    post_fallback_html: str,
) -> None:
    """Extraction falls back to non-_aatb selectors when primary selectors fail."""
    raw = RawResponse(
        url="https://instagram.com/p/XYZ/",
        final_url="https://instagram.com/p/XYZ/",
        status_code=200,
        headers={},
        html=post_fallback_html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "post"
    assert "Fallback caption" in extracted["caption"]
    assert extracted["author_username"] == "fallbackuser"
    assert extracted["likes_count"] == 789
    assert extracted["comments_count"] == 12


@pytest.mark.asyncio
async def test_instagram_collect_flags_private(adapter: InstagramAdapter) -> None:
    """Collect flags private/login-wall content."""
    html = "<html><body>Please log in to view this content</body></html>"
    collector = StubCollector(strategy="browser", html=html)

    response = await adapter.collect(POST_URL, "browser", collector, ScrapingOptions())

    assert response.error is not None
    message = response.error["message"].lower()
    assert "private" in message or "authentication" in message
