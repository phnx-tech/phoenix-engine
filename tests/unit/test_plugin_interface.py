"""Unit tests for the adapter plugin interface."""

from __future__ import annotations

import re
from typing import Any

import pytest
from bs4 import BeautifulSoup

from phoenix.adapters.base import BaseAdapter, PluginInterface
from phoenix.collectors.base import Collector, StubCollector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import ScrapingOptions
from phoenix.plugins.manifest import PluginManifest

pytestmark = pytest.mark.unit


class MinimalAdapter(BaseAdapter):
    """Minimal concrete adapter for testing the interface contract."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="minimal",
            version="0.1.0",
            platforms=["minimal"],
            url_patterns=[r"https?://minimal\.example/.+"],
        )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        """Return the URL patterns supported by this adapter."""
        return [re.compile(pattern) for pattern in self.manifest.url_patterns]

    async def collect(
        self,
        url: str,
        strategy: str,
        collector: Collector,
        options: ScrapingOptions,
    ) -> RawResponse:
        """Collect the URL using the supplied collector."""
        return await collector.collect(url, options)

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract a minimal field from the raw response."""
        return {"text": raw_response.html}

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Normalize extracted fields into a UnifiedOutput."""
        return UnifiedOutput(
            url=url,
            platform="minimal",
            content_type="post",
            text=extracted.get("text"),
            scraping_strategy=strategy,
        )


def test_base_adapter_cannot_be_instantiated() -> None:
    """The abstract base class cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseAdapter()  # type: ignore[abstract]


def test_plugin_interface_is_base_adapter() -> None:
    """PluginInterface and BaseAdapter refer to the same contract."""
    assert PluginInterface is BaseAdapter


def test_partial_adapter_cannot_be_instantiated() -> None:
    """A subclass missing abstract methods cannot be instantiated."""

    class Partial(BaseAdapter):  # type: ignore[abstract]
        @property
        def manifest(self) -> PluginManifest:
            """Return a partial manifest."""
            return PluginManifest(name="partial", version="0.1.0")

    with pytest.raises(TypeError):
        Partial()  # type: ignore[abstract]


def test_adapter_manifest_property() -> None:
    """A concrete adapter exposes its manifest."""
    adapter = MinimalAdapter()

    assert adapter.manifest.name == "minimal"
    assert adapter.manifest.platforms == ["minimal"]


def test_adapter_supported_patterns() -> None:
    """supported_patterns returns compiled regex objects."""
    adapter = MinimalAdapter()
    patterns = adapter.supported_patterns()

    assert len(patterns) == 1
    assert patterns[0].match("https://minimal.example/post/1")
    assert patterns[0].match("http://minimal.example/post/1")
    assert not patterns[0].match("https://other.example/post/1")


def test_adapter_preferred_strategies_default() -> None:
    """Default preferred strategies order HTTP before browser."""
    adapter = MinimalAdapter()

    assert adapter.preferred_strategies() == ["http", "browser"]


def test_adapter_health_check_default() -> None:
    """health_check returns manifest-derived metadata by default."""
    adapter = MinimalAdapter()
    health = adapter.health_check()

    assert health["adapter"] == "minimal"
    assert health["version"] == "0.1.0"
    assert health["platforms"] == ["minimal"]
    assert health["url_patterns"] == 1
    assert health["strategies"] == ["http", "browser"]
    assert health["requires_auth"] is False
    assert health["supports_ai_fallback"] is True


@pytest.mark.asyncio
async def test_adapter_collect_delegates_to_collector() -> None:
    """Collect passes the URL and options through to the collector."""
    adapter = MinimalAdapter()
    collector = StubCollector(strategy="http", html="<p>hello</p>")

    response = await adapter.collect(
        "https://minimal.example/post/1",
        "http",
        collector,
        ScrapingOptions(),
    )

    assert response.strategy == "http"
    assert "hello" in response.html


@pytest.mark.asyncio
async def test_adapter_extract_and_normalize() -> None:
    """Extract and normalize produce a UnifiedOutput."""
    adapter = MinimalAdapter()
    raw = RawResponse(
        url="https://minimal.example/post/1",
        final_url="https://minimal.example/post/1",
        status_code=200,
        headers={},
        html="<p>hello</p>",
        strategy="http",
    )

    extracted = await adapter.extract(raw)
    output = await adapter.normalize(extracted, raw.url, "http")

    assert isinstance(output, UnifiedOutput)
    assert output.url == raw.url
    assert output.platform == "minimal"
    assert output.text == "<p>hello</p>"


class _UtilityAdapter(BaseAdapter):
    """Adapter subclass used only to access protected utility helpers."""

    @property
    def manifest(self) -> PluginManifest:
        """Return a utility manifest."""
        return PluginManifest(name="utility", version="0.1.0")

    def supported_patterns(self) -> list[re.Pattern[str]]:
        """Return no supported patterns."""
        return []

    async def collect(
        self,
        url: str,
        strategy: str,
        collector: Collector,
        options: ScrapingOptions,
    ) -> RawResponse:
        """Collect is not used in utility tests."""
        raise NotImplementedError

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract is not used in utility tests."""
        raise NotImplementedError

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Normalize is not used in utility tests."""
        raise NotImplementedError


@pytest.fixture
def utility_adapter() -> _UtilityAdapter:
    """Return a utility adapter for testing helper methods."""
    return _UtilityAdapter()  # type: ignore[abstract]


def test_is_public_content_true_for_public_html(utility_adapter: _UtilityAdapter) -> None:
    """Public article HTML is recognized as public."""
    html = "<html><body><article><h1>Public post</h1><p>Content</p></article></body></html>"

    assert utility_adapter._is_public_content(html) is True


@pytest.mark.parametrize(
    "indicator",
    [
        "Please log in to view this content",
        "Sign in to continue",
        "Authentication required",
        "This content isn't available",
        "Page not found",
        "This account is private",
    ],
)
def test_is_public_content_false_for_login_walls(
    utility_adapter: _UtilityAdapter,
    indicator: str,
) -> None:
    """HTML containing login or private indicators is flagged as non-public."""
    html = f"<html><body><p>{indicator}</p></body></html>"

    assert utility_adapter._is_public_content(html) is False


def test_extract_with_selectors_fallback_chain(utility_adapter: _UtilityAdapter) -> None:
    """_extract_with_selectors tries selectors in order."""
    html = "<html><body><h1>Title</h1><p class='summary'>Summary</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    selector_sets = {
        "title": ["h2", "h1"],
        "summary": [".missing", ".summary"],
    }

    results = utility_adapter._extract_with_selectors(soup, selector_sets)

    assert results["title"]["value"] == "Title"
    assert results["title"]["selector_used"] == "h1"
    assert results["title"]["matched"] is True
    assert results["summary"]["value"] == "Summary"
    assert results["summary"]["selector_used"] == ".summary"


def test_extract_with_selectors_no_match(utility_adapter: _UtilityAdapter) -> None:
    """_extract_with_selectors reports no match for missing elements."""
    soup = BeautifulSoup("<html><body></body></html>", "html.parser")

    results = utility_adapter._extract_with_selectors(soup, {"title": ["h1"]})

    assert results["title"]["value"] is None
    assert results["title"]["selector_used"] is None
    assert results["title"]["matched"] is False


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1.2K", 1200),
        ("3M", 3000000),
        ("1.5B", 1500000000),
        ("1,234", 1234),
        ("  42  ", 42),
        ("5k", 5000),
        ("0", 0),
        ("", None),
        ("not a number", None),
        (None, None),
    ],
)
def test_parse_engagement(
    utility_adapter: _UtilityAdapter,
    text: str | None,
    expected: int | None,
) -> None:
    """_parse_engagement handles suffixes and separators."""
    assert utility_adapter._parse_engagement(text) == expected
