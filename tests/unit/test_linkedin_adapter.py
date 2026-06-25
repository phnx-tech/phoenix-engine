"""Unit tests for the LinkedIn adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from phoenix.adapters.linkedin import LinkedInAdapter
from phoenix.collectors.base import StubCollector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

POST_URL = "https://www.linkedin.com/posts/jordansmith_data-pipeline-migration-activity-123456789"
PROFILE_URL = "https://www.linkedin.com/in/jordansmith/"
COMPANY_URL = "https://www.linkedin.com/company/cloudscale/"


def _load_fixture(name: str) -> str:
    """Load a synthetic HTML fixture from disk."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def adapter() -> LinkedInAdapter:
    """Return a LinkedIn adapter instance."""
    return LinkedInAdapter()


@pytest.fixture
def post_html() -> str:
    """Return synthetic LinkedIn post HTML."""
    return _load_fixture("linkedin_post.html")


@pytest.fixture
def profile_html() -> str:
    """Return synthetic LinkedIn profile HTML."""
    return _load_fixture("linkedin_profile.html")


@pytest.fixture
def company_html() -> str:
    """Return synthetic LinkedIn company HTML."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta property="og:title" content="CloudScale | LinkedIn">
        <title>CloudScale | LinkedIn</title>
    </head>
    <body>
        <main class="li-company-page">
            <section class="top-card-layout">
                <h1 class="top-card-layout__title">CloudScale</h1>
                <p class="top-card-layout__first-subline">Cloud Computing</p>
                <p class="top-card-layout__second-subline">1,001-5,000 employees</p>
            </section>
            <div class="company-description">
                CloudScale builds modern data infrastructure for enterprises.
            </div>
            <span class="company-follower-count">45.2K followers</span>
            <ul class="company-specialties">
                <li>Cloud Computing</li>
                <li>Data Engineering</li>
                <li>Machine Learning</li>
            </ul>
            <div class="company-headquarters">San Francisco, CA</div>
            <a class="company-website" href="https://cloudscale.example.com">Website</a>
        </main>
    </body>
    </html>
    """


def test_linkedin_adapter_manifest(adapter: LinkedInAdapter) -> None:
    """The LinkedIn adapter manifest describes the plugin correctly."""
    manifest = adapter.manifest

    assert manifest.name == "linkedin"
    assert manifest.platforms == ["linkedin"]
    assert manifest.requires_auth is True
    assert manifest.supports_ai_fallback is True
    assert len(manifest.url_patterns) == 5


def test_linkedin_adapter_supported_patterns(adapter: LinkedInAdapter) -> None:
    """The adapter matches LinkedIn post, profile, and company URLs."""
    patterns = adapter.supported_patterns()

    assert len(patterns) == 5
    assert patterns[0].match(POST_URL)
    assert patterns[3].match(PROFILE_URL)
    assert patterns[4].match(COMPANY_URL)
    assert not patterns[0].match("https://www.example.com/posts/123")


def test_linkedin_adapter_preferred_strategies(adapter: LinkedInAdapter) -> None:
    """LinkedIn adapter prefers browser over HTTP."""
    assert adapter.preferred_strategies() == ["browser", "http"]


def test_linkedin_adapter_health_check(adapter: LinkedInAdapter) -> None:
    """Health check includes LinkedIn platform metadata."""
    health = adapter.health_check()

    assert health["adapter"] == "linkedin"
    assert health["platform"] == "linkedin"
    assert health["requires_auth"] is True


@pytest.mark.asyncio
async def test_linkedin_adapter_collect_delegates(
    adapter: LinkedInAdapter,
    post_html: str,
) -> None:
    """Collect delegates to the provided collector for public content."""
    collector = StubCollector(strategy="browser", html=post_html)

    response = await adapter.collect(POST_URL, "browser", collector, ScrapingOptions())

    assert isinstance(response, RawResponse)
    assert response.url == POST_URL
    assert response.strategy == "browser"
    assert response.error is None


@pytest.mark.asyncio
async def test_linkedin_adapter_collect_flags_login_wall(
    adapter: LinkedInAdapter,
) -> None:
    """Collect marks responses behind LinkedIn auth walls with an error."""
    html = "<html><body>Sign in to view this post</body></html>"
    collector = StubCollector(strategy="browser", html=html)

    response = await adapter.collect(POST_URL, "browser", collector, ScrapingOptions())

    assert response.error is not None
    assert "authentication" in response.error["message"].lower()


@pytest.mark.asyncio
async def test_linkedin_adapter_extract_post(
    adapter: LinkedInAdapter,
    post_html: str,
) -> None:
    """Extract returns structured post metadata."""
    raw = RawResponse(
        url=POST_URL,
        final_url=POST_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=post_html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "post"
    assert extracted["id"] == "urn:li:activity:123456789"
    assert extracted["author"] == "Jordan Smith"
    assert "Senior Software Engineer" in extracted["author_headline"]
    assert "data pipeline" in extracted["text"].lower()
    assert extracted["reaction_count"] == 856
    assert extracted["comment_count"] == 34
    assert extracted["repost_count"] == 18
    assert extracted["timestamp"] is not None


@pytest.mark.asyncio
async def test_linkedin_adapter_extract_profile(
    adapter: LinkedInAdapter,
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
    assert extracted["name"] == "Jordan Smith"
    assert "Senior Software Engineer" in extracted["headline"]
    assert "San Francisco" in extracted["location"]
    assert extracted["industry"] == "Computer Software"
    assert extracted["current_position"] == "Senior Software Engineer"
    assert extracted["education"] == "State University"
    assert extracted["connections_count"] == 500


@pytest.mark.asyncio
async def test_linkedin_adapter_extract_company(
    adapter: LinkedInAdapter,
    company_html: str,
) -> None:
    """Extract returns structured company page metadata."""
    raw = RawResponse(
        url=COMPANY_URL,
        final_url=COMPANY_URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html=company_html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["content_type"] == "company"
    assert extracted["name"] == "CloudScale"
    assert extracted["industry"] == "Cloud Computing"
    assert "1,001-5,000" in extracted["company_size"]
    assert "data infrastructure" in extracted["description"].lower()
    assert extracted["follower_count"] == 45_200
    assert extracted["specialties"] == ["Cloud Computing", "Data Engineering", "Machine Learning"]
    assert extracted["headquarters"] == "San Francisco, CA"
    assert extracted["website"] == "https://cloudscale.example.com"


@pytest.mark.asyncio
async def test_linkedin_adapter_extract_post_fallback_selectors(
    adapter: LinkedInAdapter,
) -> None:
    """Extract falls back to alternative selectors when primary selectors fail."""
    html = """
    <html>
      <body>
        <main class="li-feed-page">
          <article class="li-post post" data-id="fallback-id">
            <header>
              <a class="li-actor-link" href="/in/fallback/">
                <span class="li-name author-name">Fallback Author</span>
                <span class="li-headline author-headline">Engineer</span>
              </a>
              <time class="li-timestamp timestamp" datetime="2025-01-21T09:00:00+00:00">1d</time>
            </header>
            <div class="li-content post-caption">
              <p>Fallback post text.</p>
            </div>
            <section class="li-social-summary">
              <span class="li-reactions like-count">100 likes</span>
              <span class="li-comments comment-count">5 comments</span>
              <span class="li-shares share-count">2 reposts</span>
            </section>
          </article>
        </main>
      </body>
    </html>
    """
    raw = RawResponse(
        url=POST_URL,
        final_url=POST_URL,
        status_code=200,
        headers={},
        html=html,
        strategy="browser",
    )

    extracted = await adapter.extract(raw)

    assert extracted["id"] == "fallback-id"
    assert extracted["author"] == "Fallback Author"
    assert extracted["text"] == "Fallback post text."
    assert extracted["reaction_count"] == 100
    assert extracted["comment_count"] == 5
    assert extracted["repost_count"] == 2
    assert any("fallback" in warning for warning in extracted["_warnings"])


@pytest.mark.asyncio
async def test_linkedin_adapter_normalize_post(
    adapter: LinkedInAdapter,
    post_html: str,
) -> None:
    """Normalize converts post extraction into UnifiedOutput."""
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
    assert output.platform == "linkedin"
    assert output.content_type == "post"
    assert output.author == "Jordan Smith"
    assert output.likes == 856
    assert output.comments == 34
    assert output.shares == 18
    assert output.scraping_strategy == "browser"


@pytest.mark.asyncio
async def test_linkedin_adapter_normalize_profile(
    adapter: LinkedInAdapter,
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
    assert output.platform == "linkedin"
    assert output.content_type == "profile"
    assert output.title == "Jordan Smith"
    assert output.author == "Jordan Smith"


@pytest.mark.asyncio
async def test_linkedin_adapter_normalize_company(
    adapter: LinkedInAdapter,
    company_html: str,
) -> None:
    """Normalize converts company extraction into UnifiedOutput."""
    raw = RawResponse(
        url=COMPANY_URL,
        final_url=COMPANY_URL,
        status_code=200,
        headers={},
        html=company_html,
        strategy="browser",
    )
    extracted = await adapter.extract(raw)

    output = await adapter.normalize(extracted, COMPANY_URL, "browser")

    assert isinstance(output, UnifiedOutput)
    assert output.url == COMPANY_URL
    assert output.platform == "linkedin"
    assert output.content_type == "company"
    assert output.title == "CloudScale"
    assert output.author == "CloudScale"
    assert output.tags == ["Cloud Computing", "Data Engineering", "Machine Learning"]


def test_linkedin_adapter_detect_content_type(adapter: LinkedInAdapter) -> None:
    """Content type detection distinguishes posts, profiles, and companies."""
    assert adapter._detect_content_type(POST_URL) == "post"
    assert adapter._detect_content_type(PROFILE_URL) == "profile"
    assert adapter._detect_content_type(COMPANY_URL) == "company"
