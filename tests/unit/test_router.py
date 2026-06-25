"""Unit tests for the Phoenix Engine URL router."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import pytest

from phoenix.adapters.base import BaseAdapter
from phoenix.exceptions import UnsupportedURLError
from phoenix.plugins.loader import PluginLoader
from phoenix.plugins.manifest import PluginManifest
from phoenix.router import URLRouter

if TYPE_CHECKING:
    from phoenix.collectors.base import Collector
    from phoenix.models.document import RawResponse
    from phoenix.models.output import UnifiedOutput
    from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit


class CustomAdapter(BaseAdapter):
    """Custom adapter for router plugin tests."""

    @property
    def manifest(self) -> PluginManifest:
        """Return a custom manifest."""
        return PluginManifest(
            name="custom",
            version="1.0.0",
            platforms=["custom"],
            url_patterns=[r"https?://custom\.example/.+"],
        )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        """Return custom URL patterns."""
        return [re.compile(pattern) for pattern in self.manifest.url_patterns]

    async def collect(
        self,
        url: str,
        strategy: str,
        collector: Collector,
        options: ScrapingOptions,
    ) -> RawResponse:
        """Collect is not exercised in router tests."""
        raise NotImplementedError

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract is not exercised in router tests."""
        raise NotImplementedError

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Normalize is not exercised in router tests."""
        raise NotImplementedError


@pytest.fixture
def router() -> URLRouter:
    """Return a configured URLRouter."""
    return URLRouter()


@pytest.mark.parametrize(
    ("url", "expected_platform", "expected_content_type"),
    [
        ("https://www.instagram.com/p/ABC123/", "instagram", "post"),
        ("https://instagram.com/reel/XYZ789/", "instagram", "reel"),
        ("https://instagram.com/someuser/", "instagram", "profile"),
        ("https://x.com/user/status/1234567890", "x", "post"),
        ("https://twitter.com/user/", "x", "profile"),
        ("https://www.tiktok.com/@user/video/123456", "tiktok", "video"),
        ("https://tiktok.com/@user/", "tiktok", "profile"),
        ("https://www.linkedin.com/posts/user_post-123", "linkedin", "post"),
        ("https://linkedin.com/in/someone/", "linkedin", "profile"),
        ("https://www.facebook.com/page/posts/123", "facebook", "post"),
        ("https://facebook.com/page/videos/123/", "facebook", "video"),
        ("https://facebook.com/page/", "facebook", "profile"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube", "video"),
        ("https://youtube.com/@channel/", "youtube", "profile"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube", "video"),
        ("https://example.com/article/123", "generic", "article"),
    ],
)
def test_router_classify(
    router: URLRouter,
    url: str,
    expected_platform: str,
    expected_content_type: str,
) -> None:
    """Router classifies known platform URLs correctly."""
    classification = router.classify(url)

    assert classification.platform == expected_platform
    assert classification.content_type == expected_content_type


def test_router_normalizes_url_strips_utm(router: URLRouter) -> None:
    """Normalization removes UTM tracking parameters."""
    raw = (
        "https://example.com/article/123"
        "?utm_source=newsletter&utm_medium=email&utm_campaign=summer"
        "&page=2"
    )
    normalized = router.normalize_url(raw)

    assert "utm_" not in normalized
    assert "page=2" in normalized


def test_router_rejects_unsupported_scheme(router: URLRouter) -> None:
    """Unsupported protocols raise UnsupportedURLError."""
    with pytest.raises(UnsupportedURLError):
        router.classify("ftp://example.com/file.txt")


def test_router_rejects_missing_scheme(router: URLRouter) -> None:
    """URLs without a scheme raise UnsupportedURLError."""
    with pytest.raises(UnsupportedURLError):
        router.classify("example.com/article")


def test_router_rejects_empty_url(router: URLRouter) -> None:
    """Empty URLs raise UnsupportedURLError."""
    with pytest.raises(UnsupportedURLError):
        router.classify("   ")


def test_router_match_returns_platform(router: URLRouter) -> None:
    """match() returns the platform identifier for a URL."""
    assert router.match("https://x.com/user/status/123") == "x"


def test_router_match_unknown_returns_none(router: URLRouter) -> None:
    """match() returns None when no pattern matches."""
    assert router.match("not-a-url") is None


def test_router_rejects_missing_host(router: URLRouter) -> None:
    """URLs with a scheme but no host raise UnsupportedURLError."""
    with pytest.raises(UnsupportedURLError, match="missing a host"):
        router.classify("https://")


def test_router_get_adapter_returns_generic_for_unknown(router: URLRouter) -> None:
    """get_adapter falls back to the generic adapter for unknown platforms."""
    adapter = router.get_adapter("unknown_platform")

    assert adapter.manifest.name == "generic_web"


def test_router_get_adapter_returns_generic_for_generic(router: URLRouter) -> None:
    """get_adapter returns the generic adapter for the generic platform."""
    adapter = router.get_adapter("generic")

    assert adapter.manifest.name == "generic_web"


def test_router_get_adapter_for_url_returns_generic_adapter(router: URLRouter) -> None:
    """get_adapter_for_url returns the generic adapter for unknown domains."""
    adapter = router.get_adapter_for_url("https://obscure-blog.example.com/article")

    assert adapter is not None
    assert adapter.manifest.name == "generic_web"


def test_router_get_adapter_for_url_returns_platform_adapter(router: URLRouter) -> None:
    """get_adapter_for_url returns the matching platform adapter."""
    adapter = router.get_adapter_for_url("https://x.com/user/status/123")

    assert adapter is not None
    assert adapter.manifest.name == "x_twitter"


def test_router_get_adapter_for_url_returns_none_for_non_url(router: URLRouter) -> None:
    """get_adapter_for_url returns None for strings that are not URLs."""
    assert router.get_adapter_for_url("not-a-url") is None


def test_router_get_adapter_for_url_returns_custom_plugin_adapter() -> None:
    """get_adapter_for_url returns a specific plugin adapter when matched."""
    loader = PluginLoader()
    loader.register(CustomAdapter())
    router = URLRouter(loader)

    adapter = router.get_adapter_for_url("https://custom.example/page/1")

    assert adapter is not None
    assert adapter.manifest.name == "custom"


def test_router_get_adapter_for_url_generic_has_generic_platform() -> None:
    """The generic adapter is recognized by its platform list."""
    adapter = URLRouter().get_adapter_for_url("https://example.com")

    assert adapter is not None
    assert "generic" in adapter.manifest.platforms


def test_router_generic_adapter_fallback_when_loader_empty() -> None:
    """Router creates a generic adapter even when the loader has no generic adapter."""
    empty_loader = PluginLoader()
    router = URLRouter(empty_loader)

    adapter = router.get_adapter("generic")
    assert adapter.manifest.name == "generic_web"
