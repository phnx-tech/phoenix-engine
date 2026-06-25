"""Unit tests for the X/Twitter platform adapter."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from phoenix.adapters.x_twitter import XTwitterAdapter
from phoenix.collectors.base import StubCollector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

TWEET_URL = "https://x.com/TechObserver/status/1234567890"
PROFILE_URL = "https://x.com/TechObserver"


def _load_fixture(name: str) -> str:
    """Load a synthetic HTML fixture."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def adapter() -> XTwitterAdapter:
    """Return an X/Twitter adapter instance."""
    return XTwitterAdapter()


@pytest.fixture
def x_tweet_html() -> str:
    """Return synthetic X/Twitter tweet HTML."""
    return _load_fixture("x_tweet.html")


@pytest.fixture
def x_profile_html() -> str:
    """Return synthetic X/Twitter profile HTML."""
    return _load_fixture("x_profile.html")


def test_x_twitter_adapter_manifest(adapter: XTwitterAdapter) -> None:
    """The manifest describes the X/Twitter adapter."""
    manifest = adapter.manifest

    assert manifest.name == "x_twitter"
    assert manifest.version == "0.1.0"
    assert manifest.platforms == ["x", "x_twitter"]
    assert manifest.strategies == ["http", "browser"]
    assert manifest.requires_auth is False
    assert manifest.supports_ai_fallback is True


def test_x_twitter_adapter_supported_patterns(adapter: XTwitterAdapter) -> None:
    """Supported patterns match X/Twitter tweet and profile URLs."""
    patterns = adapter.supported_patterns()

    assert len(patterns) == 3
    assert all(isinstance(pattern, re.Pattern) for pattern in patterns)
    assert patterns[0].match(TWEET_URL)
    assert patterns[0].match("https://twitter.com/TechObserver/status/1234567890")
    assert patterns[1].match("https://x.com/i/web/status/1234567890")
    assert patterns[2].match(PROFILE_URL)
    assert not patterns[0].match("https://example.com/article/123")


def test_x_twitter_adapter_preferred_strategies(adapter: XTwitterAdapter) -> None:
    """X/Twitter prefers HTTP with browser fallback."""
    assert adapter.preferred_strategies() == ["http", "browser"]


def test_x_twitter_adapter_health_check(adapter: XTwitterAdapter) -> None:
    """Health check exposes X/Twitter metadata."""
    health = adapter.health_check()

    assert health["adapter"] == "x_twitter"
    assert health["version"] == "0.1.0"
    assert health["platforms"] == ["x", "x_twitter"]


@pytest.mark.asyncio
async def test_x_twitter_adapter_collect_delegates(
    adapter: XTwitterAdapter,
    x_tweet_html: str,
) -> None:
    """Collect delegates to the supplied collector."""
    collector = StubCollector(strategy="http", html=x_tweet_html)

    response = await adapter.collect(TWEET_URL, "http", collector, ScrapingOptions())

    assert isinstance(response, RawResponse)
    assert response.url == TWEET_URL
    assert response.strategy == "http"
    assert response.error is None
    assert adapter._is_public_content(response.html) is True


@pytest.mark.asyncio
async def test_x_twitter_adapter_collect_flags_private_content(
    adapter: XTwitterAdapter,
) -> None:
    """Collect marks private/login-wall X content with an error."""
    html = "<html><body>Please log in to view this content</body></html>"
    collector = StubCollector(strategy="http", html=html)

    response = await adapter.collect(PROFILE_URL, "http", collector, ScrapingOptions())

    assert response.error is not None
    assert "authentication" in response.error["message"].lower()


@pytest.mark.asyncio
async def test_x_twitter_adapter_extract_tweet(
    adapter: XTwitterAdapter,
    x_tweet_html: str,
) -> None:
    """Extract returns X/Twitter tweet fields."""
    raw = RawResponse(
        url=TWEET_URL,
        final_url=TWEET_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=x_tweet_html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "post"
    assert extracted["tweet_id"] == "1234567890"
    assert "open-source LLM" in extracted["text"]
    assert extracted["author_username"] == "TechObserver"
    assert extracted["like_count"] == "1.1K likes"
    assert extracted["retweet_count"] == "158 retweets"
    assert extracted["reply_count"] == "42 replies"
    assert extracted["timestamp"] == "2025-01-19T14:30:00+00:00"
    assert "https://cdn.example.com/x/benchmark.png" in extracted["media_urls"]
    assert extracted["selectors_used"]


@pytest.mark.asyncio
async def test_x_twitter_adapter_extract_profile(
    adapter: XTwitterAdapter,
    x_profile_html: str,
) -> None:
    """Extract returns X/Twitter profile fields."""
    raw = RawResponse(
        url=PROFILE_URL,
        final_url=PROFILE_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=x_profile_html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "profile"
    assert extracted["username"] == "@TechObserver"
    assert extracted["display_name"] == "TechObserver"
    assert "open-source AI" in extracted["bio"]
    assert extracted["location"] == "San Francisco, CA"
    assert extracted["website"] == "https://techobserver.example.com"
    assert extracted["join_date"] == "Joined March 2018"
    assert extracted["follower_count"] == "12.3K followers"
    assert extracted["following_count"] == "492 following"
    assert extracted["tweet_count"] == "4,205 posts"
    assert len(extracted["recent_tweets"]) == 2
    assert extracted["selectors_used"]


@pytest.mark.asyncio
async def test_x_twitter_adapter_normalize_tweet(
    adapter: XTwitterAdapter,
    x_tweet_html: str,
) -> None:
    """Normalize converts extracted tweet fields to UnifiedOutput."""
    raw = RawResponse(
        url=TWEET_URL,
        final_url=TWEET_URL,
        status_code=200,
        headers={},
        html=x_tweet_html,
        strategy="http",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, TWEET_URL, "http")

    assert isinstance(output, UnifiedOutput)
    assert output.url == TWEET_URL
    assert output.platform == "x"
    assert output.content_type == "post"
    assert output.author == "TechObserver"
    assert output.author_url == "https://x.com/TechObserver/"
    assert "open-source LLM" in output.text
    assert output.likes == 1100
    assert output.shares == 158
    assert output.comments == 42
    assert output.media_urls == ["https://cdn.example.com/x/benchmark.png"]
    assert output.tweet_id == "1234567890"
    assert output.timestamp is not None


@pytest.mark.asyncio
async def test_x_twitter_adapter_normalize_profile(
    adapter: XTwitterAdapter,
    x_profile_html: str,
) -> None:
    """Normalize converts extracted profile fields to UnifiedOutput."""
    raw = RawResponse(
        url=PROFILE_URL,
        final_url=PROFILE_URL,
        status_code=200,
        headers={},
        html=x_profile_html,
        strategy="http",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, PROFILE_URL, "http")

    assert isinstance(output, UnifiedOutput)
    assert output.url == PROFILE_URL
    assert output.platform == "x"
    assert output.content_type == "profile"
    assert output.author == "TechObserver"
    assert output.follower_count == 12300
    assert output.following_count == 492
    assert output.tweet_count == 4205
    assert output.website == "https://techobserver.example.com"
    assert len(output.recent_tweets) == 2


@pytest.mark.asyncio
async def test_x_twitter_adapter_extract_uses_fallback_selectors(
    adapter: XTwitterAdapter,
) -> None:
    """Extraction falls back to secondary selectors when the primary fails."""
    html = """
    <html><body>
    <article class="tweet" data-tweet-id="FB123">
        <div class="post-caption" lang="en">Fallback tweet text</div>
        <span class="like-count">7 likes</span>
        <span class="share-count">3 retweets</span>
        <span class="comment-count">1 reply</span>
        <time datetime="2025-04-01T09:00:00+00:00"></time>
        <img src="https://cdn.example.com/x/fb.png">
    </article>
    </body></html>
    """
    raw = RawResponse(
        url="https://x.com/user/status/FB123",
        final_url="https://x.com/user/status/FB123",
        status_code=200,
        headers={},
        html=html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["text"] == "Fallback tweet text"
    assert "div[lang='en']" in extracted["selectors_used"]
    assert ".tweet-text" not in extracted["selectors_used"]
