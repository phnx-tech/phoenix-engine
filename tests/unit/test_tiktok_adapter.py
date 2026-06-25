"""Unit tests for the TikTok adapter."""

from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from phoenix.adapters.tiktok import TikTokAdapter
from phoenix.collectors.base import StubCollector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

VIDEO_URL = "https://www.tiktok.com/@demochef/video/1234567890123456789"
PROFILE_URL = "https://www.tiktok.com/@demochef"


def _load_fixture(name: str) -> str:
    """Load a synthetic HTML fixture from disk."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def adapter() -> TikTokAdapter:
    """Return a TikTok adapter instance."""
    return TikTokAdapter()


@pytest.fixture
def video_html() -> str:
    """Return synthetic TikTok video HTML."""
    return _load_fixture("tiktok_video.html")


@pytest.fixture
def profile_html() -> str:
    """Return synthetic TikTok profile HTML."""
    return _load_fixture("tiktok_profile.html")


def test_tiktok_adapter_manifest(adapter: TikTokAdapter) -> None:
    """The TikTok adapter manifest describes the plugin correctly."""
    manifest = adapter.manifest

    assert manifest.name == "tiktok"
    assert manifest.platforms == ["tiktok"]
    assert manifest.requires_auth is False
    assert manifest.supports_ai_fallback is True
    assert len(manifest.url_patterns) == 3


def test_tiktok_adapter_supported_patterns(adapter: TikTokAdapter) -> None:
    """The adapter matches TikTok video and profile URLs."""
    patterns = adapter.supported_patterns()

    assert len(patterns) == 3
    assert patterns[0].match(VIDEO_URL)
    assert patterns[1].match("https://www.tiktok.com/video/1234567890")
    assert patterns[2].match(PROFILE_URL)
    assert not patterns[0].match("https://www.example.com/video/123")


def test_tiktok_adapter_preferred_strategies(adapter: TikTokAdapter) -> None:
    """TikTok adapter prefers browser over HTTP."""
    assert adapter.preferred_strategies() == ["browser", "http"]


def test_tiktok_adapter_health_check(adapter: TikTokAdapter) -> None:
    """Health check includes TikTok platform metadata."""
    health = adapter.health_check()

    assert health["adapter"] == "tiktok"
    assert health["platform"] == "tiktok"
    assert health["requires_auth"] is False
    assert health["supports_ai_fallback"] is True


@pytest.mark.asyncio
async def test_tiktok_adapter_collect_delegates(
    adapter: TikTokAdapter,
    video_html: str,
) -> None:
    """Collect delegates to the provided collector for public content."""
    collector = StubCollector(strategy="browser", html=video_html)

    response = await adapter.collect(VIDEO_URL, "browser", collector, ScrapingOptions())

    assert isinstance(response, RawResponse)
    assert response.url == VIDEO_URL
    assert response.strategy == "browser"
    assert response.error is None
    assert adapter._is_public_content(response.html) is True


@pytest.mark.asyncio
async def test_tiktok_adapter_collect_flags_login_wall(
    adapter: TikTokAdapter,
) -> None:
    """Collect marks responses behind login walls with an error."""
    html = "<html><body>Please log in to view this content</body></html>"
    collector = StubCollector(strategy="browser", html=html)

    response = await adapter.collect(VIDEO_URL, "browser", collector, ScrapingOptions())

    assert response.error is not None
    assert "authentication" in response.error["message"].lower()


@pytest.mark.asyncio
async def test_tiktok_adapter_extract_video(
    adapter: TikTokAdapter,
    video_html: str,
) -> None:
    """Extract returns structured video metadata."""
    raw = RawResponse(
        url=VIDEO_URL,
        final_url=VIDEO_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=video_html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "video"
    assert extracted["video_id"] == "1234567890123456789"
    assert extracted["author_username"] == "demochef"
    assert "Quick dinner idea" in extracted["description"]
    assert extracted["play_count"] == 1_200_000
    assert extracted["like_count"] == 85_400
    assert extracted["comment_count"] == 1_204
    assert extracted["share_count"] == 3_500
    assert extracted["duration"] == 45
    assert extracted["music_info"]["title"] == "original sound - demochef"
    assert "#foodtok" in extracted["hashtags"]
    assert "#easyrecipe" in extracted["hashtags"]
    assert extracted["timestamp"] is not None
    assert extracted["video_url"] == "https://cdn.example.com/tt/demo.mp4"
    assert extracted["thumbnail_url"] == "https://cdn.example.com/tt/demo-thumb.jpg"


@pytest.mark.asyncio
async def test_tiktok_adapter_extract_profile(
    adapter: TikTokAdapter,
    profile_html: str,
) -> None:
    """Extract returns structured profile metadata."""
    raw = RawResponse(
        url=PROFILE_URL,
        final_url=PROFILE_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=profile_html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "profile"
    assert extracted["username"] == "demochef"
    assert extracted["display_name"] == "Demo Chef"
    assert "quick and tasty" in extracted["bio"].lower()
    assert extracted["follower_count"] == 2_300_000
    assert extracted["following_count"] == 142
    assert extracted["likes_count"] == 18_500_000
    assert extracted["video_count"] == 84
    assert len(extracted["recent_videos"]) == 2
    assert extracted["recent_videos"][0]["video_id"] == "1111111111111111111"


@pytest.mark.asyncio
async def test_tiktok_adapter_extract_video_fallback_selectors(
    adapter: TikTokAdapter,
) -> None:
    """Extract falls back to alternative selectors when primary selectors fail."""
    html = """
    <html>
      <body>
        <main class="tt-video-page">
          <article class="tt-video post" data-video-id="999">
            <div class="tt-caption post-caption">
              <p>Fallback caption #fallback</p>
            </div>
            <a class="tt-author-link" href="/@fallbackuser">
              <span class="tt-username author-name">fallbackuser</span>
            </a>
            <section class="tt-stats">
              <span class="tt-views">5K views</span>
              <span class="tt-likes like-count">1.2K likes</span>
              <span class="tt-comments comment-count">50 comments</span>
              <span class="tt-shares share-count">10 shares</span>
            </section>
            <div class="tt-sound">
              <span class="tt-sound-title">fallback sound</span>
            </div>
            <time class="timestamp" datetime="2025-01-19T10:00:00+00:00">2025-01-19</time>
          </article>
        </main>
      </body>
    </html>
    """
    raw = RawResponse(
        url=VIDEO_URL,
        final_url=VIDEO_URL,
        status_code=200,
        headers={},
        html=html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["video_id"] == "999"
    assert "Fallback caption" in extracted["description"]
    assert extracted["author_username"] == "fallbackuser"
    assert extracted["play_count"] == 5_000
    assert extracted["like_count"] == 1_200
    assert extracted["comment_count"] == 50
    assert extracted["share_count"] == 10
    assert any("fallback" in warning for warning in extracted["_warnings"])


@pytest.mark.asyncio
async def test_tiktok_adapter_normalize_video(
    adapter: TikTokAdapter,
    video_html: str,
) -> None:
    """Normalize converts video extraction into UnifiedOutput."""
    raw = RawResponse(
        url=VIDEO_URL,
        final_url=VIDEO_URL,
        status_code=200,
        headers={},
        html=video_html,
        strategy="browser",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, VIDEO_URL, "browser")

    assert isinstance(output, UnifiedOutput)
    assert output.url == VIDEO_URL
    assert output.platform == "tiktok"
    assert output.content_type == "video"
    assert output.author == "demochef"
    assert output.likes == 85_400
    assert output.views == 1_200_000
    assert output.shares == 3_500
    assert output.comments == 1_204
    assert output.media_urls == ["https://cdn.example.com/tt/demo.mp4"]
    assert output.thumbnail_url == "https://cdn.example.com/tt/demo-thumb.jpg"
    assert output.scraping_strategy == "browser"
    assert any("data-e2e" in selector for selector in output.selectors_used)


@pytest.mark.asyncio
async def test_tiktok_adapter_normalize_profile(
    adapter: TikTokAdapter,
    profile_html: str,
) -> None:
    """Normalize converts profile extraction into UnifiedOutput."""
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
    assert output.platform == "tiktok"
    assert output.content_type == "profile"
    assert output.author == "demochef"
    assert output.title == "Demo Chef"
    assert output.likes == 18_500_000
    assert output.views == 84


def test_tiktok_adapter_detect_content_type(adapter: TikTokAdapter) -> None:
    """Content type detection distinguishes videos from profiles."""
    assert adapter._detect_content_type(VIDEO_URL, BeautifulSoup("", "html.parser")) == "video"
    assert adapter._detect_content_type(PROFILE_URL, BeautifulSoup("", "html.parser")) == "profile"

    profile_soup = BeautifulSoup(
        "<main class='tt-profile-page'></main>",
        "html.parser",
    )
    assert adapter._detect_content_type("https://example.com/", profile_soup) == "profile"
