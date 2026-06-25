"""Unit tests for the generic web adapter."""

from __future__ import annotations

import pytest

from phoenix.adapters.generic import GenericWebAdapter
from phoenix.collectors.base import StubCollector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit

URL = "https://example.com/article/123"


@pytest.fixture
def generic_html() -> str:
    """Return synthetic generic article HTML."""
    return """
    <html lang="en">
      <head>
        <title>Sample Article</title>
        <meta property="og:title" content="OG Article Title">
        <meta property="og:description" content="Article description.">
        <meta property="og:image" content="https://example.com/image.png">
        <meta property="og:site_name" content="Example Site">
        <script type="application/ld+json">
        {
          "@type": "Article",
          "headline": "JSON-LD Headline",
          "author": {"name": "Jane Doe"},
          "datePublished": "2025-01-15T10:00:00Z",
          "publisher": {"name": "Example Publisher"}
        }
        </script>
      </head>
      <body>
        <nav>Navigation</nav>
        <main>
          <article>
            <h1>Article Headline</h1>
            <p>This is the first paragraph.</p>
            <p>This is the second paragraph.</p>
          </article>
        </main>
        <footer>Footer</footer>
      </body>
    </html>
    """


@pytest.fixture
def adapter() -> GenericWebAdapter:
    """Return a generic web adapter instance."""
    return GenericWebAdapter()


def test_generic_adapter_manifest(adapter: GenericWebAdapter) -> None:
    """The generic adapter manifest describes the catch-all adapter."""
    manifest = adapter.manifest

    assert manifest.name == "generic_web"
    assert manifest.platforms == ["generic"]
    assert r"https?://.+" in manifest.url_patterns
    assert manifest.strategies == ["http", "browser"]
    assert manifest.requires_auth is False


def test_generic_adapter_supported_patterns(adapter: GenericWebAdapter) -> None:
    """The generic adapter matches any HTTP(S) URL."""
    patterns = adapter.supported_patterns()

    assert len(patterns) == 1
    assert patterns[0].match("https://example.com/article")
    assert patterns[0].match("http://anything.test/")
    assert not patterns[0].match("ftp://example.com/file")


def test_generic_adapter_preferred_strategies(adapter: GenericWebAdapter) -> None:
    """Generic adapter prefers HTTP over browser."""
    assert adapter.preferred_strategies() == ["http", "browser"]


def test_generic_adapter_health_check(adapter: GenericWebAdapter) -> None:
    """Health check marks the adapter as the catch-all."""
    health = adapter.health_check()

    assert health["adapter"] == "generic_web"
    assert health["catch_all"] is True


@pytest.mark.asyncio
async def test_generic_adapter_collect_delegates(
    adapter: GenericWebAdapter,
    generic_html: str,
) -> None:
    """Collect delegates to the provided collector."""
    collector = StubCollector(strategy="http", html=generic_html)

    response = await adapter.collect(URL, "http", collector, ScrapingOptions())

    assert isinstance(response, RawResponse)
    assert response.url == URL
    assert response.strategy == "http"
    assert adapter._is_public_content(response.html) is True


@pytest.mark.asyncio
async def test_generic_adapter_collect_flags_login_wall(
    adapter: GenericWebAdapter,
) -> None:
    """Collect marks responses behind login walls with an error."""
    html = "<html><body>Please log in to view this content</body></html>"
    collector = StubCollector(strategy="http", html=html)

    response = await adapter.collect(URL, "http", collector, ScrapingOptions())

    assert response.error is not None
    assert "authentication" in response.error["message"].lower()


@pytest.mark.asyncio
async def test_generic_adapter_extract(
    adapter: GenericWebAdapter,
    generic_html: str,
) -> None:
    """Extract returns generic article metadata."""
    raw = RawResponse(
        url=URL,
        final_url=URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=generic_html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert "title" in extracted
    assert "text" in extracted
    assert "author" in extracted
    assert "media_urls" in extracted
    assert "https://example.com/image.png" in extracted["media_urls"]
    assert "JSON-LD Headline" in extracted["title"] or "OG Article Title" in extracted["title"]
    assert "Navigation" not in extracted["text"]
    assert "Footer" not in extracted["text"]
    assert extracted.get("author") == "Jane Doe"


@pytest.mark.asyncio
async def test_generic_adapter_extract_jsonld_author_list(
    adapter: GenericWebAdapter,
) -> None:
    """Extract handles JSON-LD author arrays and publisher metadata."""
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "headline": "Headline",
          "author": [{"name": "Alice"}, {"name": "Bob"}],
          "publisher": {"name": "Pub Co"}
        }
        </script>
      </head>
      <body><p>Text</p></body>
    </html>
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

    assert extracted["author"] == "Alice"
    assert extracted["site_name"] == "Pub Co"


@pytest.mark.asyncio
async def test_generic_adapter_extract_ignores_broken_jsonld(
    adapter: GenericWebAdapter,
) -> None:
    """Extract skips malformed JSON-LD script tags."""
    html = """
    <html>
      <head>
        <title>Title</title>
        <script type="application/ld+json">not json</script>
      </head>
      <body><p>Text</p></body>
    </html>
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

    assert extracted["title"] == "Title"


@pytest.mark.asyncio
async def test_generic_adapter_extract_handles_no_body(
    adapter: GenericWebAdapter,
) -> None:
    """Extract handles HTML without body/main/article tags."""
    html = "<html><head><title>No Body</title></head></html>"
    raw = RawResponse(
        url=URL,
        final_url=URL,
        status_code=200,
        headers={},
        html=html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted["title"] == "No Body"
    assert extracted["text"] == "No Body"


@pytest.mark.asyncio
async def test_generic_adapter_normalize(
    adapter: GenericWebAdapter,
    generic_html: str,
) -> None:
    """Normalize produces a UnifiedOutput with generic platform metadata."""
    raw = RawResponse(
        url=URL,
        final_url=URL,
        status_code=200,
        headers={},
        html=generic_html,
        strategy="http",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, URL, "http")

    assert isinstance(output, UnifiedOutput)
    assert output.url == URL
    assert output.platform == "generic"
    assert output.scraping_strategy == "http"


@pytest.mark.asyncio
async def test_generic_adapter_extract_falls_back_to_title_tag(
    adapter: GenericWebAdapter,
) -> None:
    """Extract falls back to the <title> tag when Open Graph is absent."""
    html = "<html><head><title>Fallback Title</title></head><body><p>Text</p></body></html>"
    raw = RawResponse(
        url=URL,
        final_url=URL,
        status_code=200,
        headers={},
        html=html,
        strategy="http",
    )

    extracted = await adapter.extract(raw)

    assert extracted.get("title") == "Fallback Title"
