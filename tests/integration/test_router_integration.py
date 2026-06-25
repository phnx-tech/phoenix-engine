"""Integration tests for the Phoenix Engine URL router."""

from __future__ import annotations

import re

import pytest

from phoenix.exceptions import UnsupportedURLError
from phoenix.router import URLRouter

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("url", "expected_platform"),
    [
        ("https://www.instagram.com/p/ABC123/", "instagram"),
        ("https://instagram.com/reel/XYZ789/", "instagram"),
        ("https://x.com/TechObserver/status/1234567890", "x"),
        ("https://twitter.com/TechObserver/status/1234567890", "x"),
        ("https://www.tiktok.com/@chefmaria/video/1234567890123456789", "tiktok"),
        ("https://www.linkedin.com/posts/alexchen_activity-123", "linkedin"),
        ("https://www.facebook.com/GreenCityGardens/posts/112233", "facebook"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        ("https://example.com/article/123", "generic"),
    ],
)
def test_router_classifies_fixture_urls(url: str, expected_platform: str) -> None:
    """The router maps fixture platform URLs to the correct platform identifier."""
    router = URLRouter()
    classification = router.classify(url)

    assert classification.platform == expected_platform
    assert classification.url == url


@pytest.mark.parametrize(
    ("url", "expected_content_type"),
    [
        ("https://www.instagram.com/p/ABC123/", "post"),
        ("https://instagram.com/reel/XYZ789/", "reel"),
        ("https://instagram.com/travel_diaries/", "profile"),
        ("https://x.com/TechObserver/status/1234567890", "post"),
        ("https://x.com/TechObserver", "profile"),
        ("https://www.tiktok.com/@chefmaria/video/1234567890123456789", "video"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "video"),
        ("https://www.youtube.com/@PhoenixEngine", "profile"),
        ("https://example.com/article/123", "article"),
    ],
)
def test_router_infers_content_type(url: str, expected_content_type: str) -> None:
    """The router infers the content type from the URL path."""
    router = URLRouter()
    classification = router.classify(url)

    assert classification.content_type == expected_content_type


def test_router_normalizes_tracking_parameters() -> None:
    """Tracking query parameters are stripped while functional params remain."""
    router = URLRouter()
    raw_url = (
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        "&utm_source=tester&utm_medium=email&list=PLabc"
    )
    classification = router.classify(raw_url)

    assert classification.platform == "youtube"
    assert "utm_" not in classification.url
    assert "v=dQw4w9WgXcQ" in classification.url
    assert "list=PLabc" in classification.url


def test_router_invalid_url_raises() -> None:
    """Malformed URLs raise UnsupportedURLError."""
    router = URLRouter()

    with pytest.raises(UnsupportedURLError, match="URL is empty"):
        router.classify("   ")

    with pytest.raises(UnsupportedURLError, match="Unsupported URL scheme"):
        router.classify("ftp://example.com/file")


def test_router_custom_patterns() -> None:
    """Custom patterns can be injected and fall back to generic."""
    custom_patterns = {
        "custom": [r"https?://custom\.example/[^/]+"],
        "generic": [r"https?://.+"],
    }
    router = URLRouter()
    router._compiled = {
        platform: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for platform, patterns in custom_patterns.items()
    }

    assert router.classify("https://custom.example/page").platform == "custom"
    assert router.classify("https://unknown.example/page").platform == "generic"
