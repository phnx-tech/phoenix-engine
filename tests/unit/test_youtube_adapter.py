"""Unit tests for the YouTube platform adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from phoenix.adapters.youtube import YouTubeAdapter
from phoenix.collectors.base import StubCollector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
SHORT_URL = "https://www.youtube.com/shorts/short123"
CHANNEL_URL = "https://www.youtube.com/@PhoenixEngine"


@pytest.fixture
def adapter() -> YouTubeAdapter:
    """Return a YouTube adapter instance."""
    return YouTubeAdapter()


@pytest.fixture
def youtube_video_html() -> str:
    """Return synthetic YouTube video HTML."""
    return (FIXTURES_DIR / "youtube_video.html").read_text(encoding="utf-8")


@pytest.fixture
def youtube_channel_html() -> str:
    """Return synthetic YouTube channel HTML."""
    return (FIXTURES_DIR / "youtube_channel.html").read_text(encoding="utf-8")


@pytest.fixture
def raw_video_response(youtube_video_html: str) -> RawResponse:
    """Return a RawResponse wrapping the video fixture."""
    return RawResponse(
        url=VIDEO_URL,
        final_url=VIDEO_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=youtube_video_html,
        strategy="http",
    )


@pytest.fixture
def raw_channel_response(youtube_channel_html: str) -> RawResponse:
    """Return a RawResponse wrapping the channel fixture."""
    return RawResponse(
        url=CHANNEL_URL,
        final_url=CHANNEL_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=youtube_channel_html,
        strategy="http",
    )


# ------------------------------------------------------------------
# Manifest and routing
# ------------------------------------------------------------------


def test_youtube_adapter_manifest(adapter: YouTubeAdapter) -> None:
    """The manifest describes the YouTube adapter."""
    manifest = adapter.manifest

    assert manifest.name == "youtube"
    assert manifest.platforms == ["youtube"]
    assert manifest.requires_auth is False
    assert manifest.supports_ai_fallback is True
    assert manifest.strategies == ["http", "browser"]


def test_youtube_adapter_supported_patterns(adapter: YouTubeAdapter) -> None:
    """Supported patterns match YouTube videos and channels."""
    patterns = adapter.supported_patterns()

    assert len(patterns) == len(adapter.manifest.url_patterns)
    assert any(p.match(VIDEO_URL) for p in patterns)
    assert any(p.match(SHORT_URL) for p in patterns)
    assert any(p.match(CHANNEL_URL) for p in patterns)
    assert any(p.match("https://www.youtube.com/channel/UCxxx") for p in patterns)
    assert any(p.match("https://youtu.be/dQw4w9WgXcQ") for p in patterns)
    assert not any(p.match("https://facebook.com/page/posts/123") for p in patterns)


def test_youtube_adapter_preferred_strategies(adapter: YouTubeAdapter) -> None:
    """YouTube prefers direct HTTP first."""
    assert adapter.preferred_strategies() == ["http", "browser"]


# ------------------------------------------------------------------
# Collection
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_youtube_adapter_collect_delegates(
    adapter: YouTubeAdapter,
    youtube_video_html: str,
) -> None:
    """Collect delegates to the supplied collector."""
    collector = StubCollector(strategy="http", html=youtube_video_html)

    response = await adapter.collect(VIDEO_URL, "http", collector, ScrapingOptions())

    assert response.strategy == "http"
    assert response.url == VIDEO_URL
    assert response.error is None


@pytest.mark.asyncio
async def test_youtube_adapter_collect_flags_login_wall(
    adapter: YouTubeAdapter,
) -> None:
    """Collect marks responses behind login walls with an error."""
    html = "<html><body>Please sign in to view this content</body></html>"
    collector = StubCollector(strategy="http", html=html)

    response = await adapter.collect(VIDEO_URL, "http", collector, ScrapingOptions())

    assert response.error is not None
    assert "authentication" in response.error["message"].lower()


# ------------------------------------------------------------------
# Video extraction
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_youtube_adapter_extract_video(
    adapter: YouTubeAdapter,
    raw_video_response: RawResponse,
) -> None:
    """Extract returns video metadata and engagement counts."""
    extracted = await adapter.extract(raw_video_response)

    assert extracted["content_type"] == "video"
    assert extracted["id"] == "dQw4w9WgXcQ"
    assert extracted["title"] == "Intro to Phoenix Engine"
    assert "structured data" in extracted["description"]
    assert extracted["channel"] == "Phoenix Engine"
    assert extracted["channel_url"] == "https://www.youtube.com/@PhoenixEngine"
    assert extracted["view_count"] == 1200000
    assert extracted["like_count"] == 45000
    assert extracted["comment_count"] == 1234
    assert extracted["duration"] == "12:34"
    assert extracted["category"] == "Education"
    assert extracted["tags"] == ["#scraping", "#opensource"]
    assert extracted["thumbnail_url"] == "https://cdn.example.com/yt/phoenix-thumb.jpg"
    assert extracted["media_urls"] == ["https://cdn.example.com/yt/phoenix.mp4"]
    assert len(extracted["transcript_segments"]) == 2
    assert extracted["transcript_segments"][0]["text"] == "Welcome to Phoenix Engine."
    assert extracted["timestamp"] is not None
    assert extracted["is_public"] is True
    assert extracted["selectors_used"]


@pytest.mark.asyncio
async def test_youtube_adapter_extract_video_comments_disabled(
    adapter: YouTubeAdapter,
) -> None:
    """Comments disabled are handled gracefully."""
    html = """
    <html><body>
      <article class="yt-video" data-video-id="abc123">
        <h1 class="yt-video-title">Title</h1>
        <div class="yt-video-description"><p>Description</p></div>
        <span class="yt-channel-name">Channel</span>
        <span class="yt-view-count">1K views</span>
      </article>
      <div class="yt-comments-disabled" style="">Comments are turned off</div>
    </body></html>
    """
    raw = RawResponse(
        url=VIDEO_URL,
        final_url=VIDEO_URL,
        status_code=200,
        headers={},
        html=html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["comments_disabled"] is True
    assert extracted["comment_count"] is None


@pytest.mark.asyncio
async def test_youtube_adapter_extract_short(
    adapter: YouTubeAdapter,
) -> None:
    """Short URLs are classified and the video ID is parsed."""
    html = """
    <html><body>
      <article class="yt-video" data-video-id="short123">
        <h1 class="yt-video-title">Short Title</h1>
      </article>
    </body></html>
    """
    raw = RawResponse(
        url=SHORT_URL,
        final_url=SHORT_URL,
        status_code=200,
        headers={},
        html=html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "short"
    assert extracted["id"] == "short123"


@pytest.mark.asyncio
async def test_youtube_adapter_extract_video_id_from_url(
    adapter: YouTubeAdapter,
) -> None:
    """Video ID can be parsed from URL when missing in HTML."""
    html = """
    <html><body>
      <article class="yt-video">
        <h1 class="yt-video-title">Fallback Title</h1>
      </article>
    </body></html>
    """
    raw = RawResponse(
        url=VIDEO_URL,
        final_url=VIDEO_URL,
        status_code=200,
        headers={},
        html=html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["id"] == "dQw4w9WgXcQ"


# ------------------------------------------------------------------
# Channel extraction
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_youtube_adapter_extract_channel(
    adapter: YouTubeAdapter,
    raw_channel_response: RawResponse,
) -> None:
    """Extract returns channel metadata and recent videos."""
    extracted = await adapter.extract(raw_channel_response)

    assert extracted["content_type"] == "profile"
    assert extracted["channel_id"] == "UCxxxxxxxxxxxxxxxxxxx"
    assert extracted["name"] == "Phoenix Engine"
    assert "ethical web scraping" in extracted["description"]
    assert extracted["subscriber_count"] == 50000
    assert extracted["video_count"] == 120
    assert extracted["view_count"] == 1500000
    assert extracted["joined_date"] == "Joined Jan 1, 2020"
    assert len(extracted["recent_videos"]) == 2
    assert extracted["recent_videos"][0]["video_id"] == "dQw4w9WgXcQ"
    assert extracted["recent_videos"][0]["view_count"] == 1200000
    assert extracted["selectors_used"]


@pytest.mark.asyncio
async def test_youtube_adapter_extract_channel_fallback_selectors(
    adapter: YouTubeAdapter,
) -> None:
    """Fallback selectors are used for channels when primary selectors are missing."""
    html = """
    <html><head>
      <meta property="og:title" content="Fallback Channel">
      <meta name="description" content="Fallback description">
    </head><body>
      <span class="yt-subscriber-count">1K subscribers</span>
    </body></html>
    """
    raw = RawResponse(
        url=CHANNEL_URL,
        final_url=CHANNEL_URL,
        status_code=200,
        headers={},
        html=html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["name"] == "Fallback Channel"
    assert extracted["description"] == "Fallback description"
    assert extracted["subscriber_count"] == 1000


# ------------------------------------------------------------------
# Normalization
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_youtube_adapter_normalize_video(
    adapter: YouTubeAdapter,
    raw_video_response: RawResponse,
) -> None:
    """Normalize maps video fields to UnifiedOutput."""
    extracted = await adapter.extract(raw_video_response)

    output = await adapter.normalize(extracted, VIDEO_URL, "http")

    assert isinstance(output, UnifiedOutput)
    assert output.url == VIDEO_URL
    assert output.platform == "youtube"
    assert output.content_type == "video"
    assert output.title == "Intro to Phoenix Engine"
    assert output.author == "Phoenix Engine"
    assert output.views == 1200000
    assert output.likes == 45000
    assert output.comments == 1234
    assert output.tags == ["#scraping", "#opensource"]


@pytest.mark.asyncio
async def test_youtube_adapter_normalize_channel(
    adapter: YouTubeAdapter,
    raw_channel_response: RawResponse,
) -> None:
    """Normalize maps channel fields to UnifiedOutput."""
    extracted = await adapter.extract(raw_channel_response)

    output = await adapter.normalize(extracted, CHANNEL_URL, "http")

    assert isinstance(output, UnifiedOutput)
    assert output.url == CHANNEL_URL
    assert output.platform == "youtube"
    assert output.content_type == "profile"
    assert output.title == "Phoenix Engine"
    assert output.author == "Phoenix Engine"
    assert output.views == 1500000
