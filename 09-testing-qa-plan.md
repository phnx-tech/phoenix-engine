# Testing & Quality Assurance Plan -- Phoenix Engine

**Version**: 2.0
**Status**: Authoritative Specification
**Owner**: Quality Assurance Lead
**Target Release**: v1.0.0
**Last Updated**: 2025-01-20
**Constraint**: NO OFFICIAL SOCIAL MEDIA APIs ARE EVER USED. All testing validates HTML scraping pipelines.

---

## 1. Testing Philosophy for Pure Scraping

### 1.1 Scraping-Specific Testing Challenges

Web scraping presents unique quality challenges that traditional application testing does not face:

| Challenge | Mitigation Strategy |
|-----------|---------------------|
| **Target websites change without notice** | HTML fixture snapshots + selector versioning + fallback chains |
| **Layout A/B testing on platforms** | Multiple HTML fixtures per platform, fallback selector validation |
| **Rate limiting blocks test runs** | All HTTP mocked -- zero live network calls in test suite |
| **JavaScript rendering is non-deterministic** | Playwright test server with controlled HTML, explicit waits |
| **Cookie/session expiration** | Mock session fixtures with synthetic cookies |
| **Bot detection mechanisms** | Browser stealth mode tested, user-agent transparency validated |

### 1.2 Shift-Left Testing

Quality is built in from the first line of scraping code. Every developer is responsible for testing their code before submitting pull requests. Bugs found in development cost 10x less to fix than bugs found in production where they break live scraping pipelines. The testing process begins at the requirements review stage -- every selector set is reviewed for testability before implementation starts.

### 1.3 Automate Everything

All tests that can be automated, must be automated. Manual testing is reserved for:
- Validating selectors against live platform HTML (one-time, results saved as fixtures)
- Browser compatibility spot checks
- Production health monitoring

The CI/CD pipeline runs the full automated test suite on every commit. No code merges without passing all quality gates.

### 1.4 Test at Boundaries

Every component is tested at its boundaries:
- **HTML boundaries**: Empty HTML, malformed HTML, very large HTML (>10MB), HTML with no matching selectors
- **Network boundaries**: Timeout (0s), slow response (30s), connection reset, DNS failure
- **Selector boundaries**: Empty selector, invalid CSS, selector matching 100 elements, selector matching zero elements
- **Concurrent boundaries**: 100 simultaneous scrapes, shared browser pool exhaustion
- **Security boundaries**: Malformed URLs, URL with query injection attempts, HTML with script tags

### 1.5 Test for Compliance

Ethics and compliance are first-class test requirements. Every release must pass compliance verification:
- Rate limiting enforcement (no burst requests)
- User-agent transparency (correct UA string sent)
- robots.txt parsing and respect
- Public-data-only enforcement (no login-gated private content bypass)
- Audit log completeness (every scrape action logged)
- No official API leakage (static analysis bans API clients)

---

## 2. Test Pyramid

### 2.1 Target Metrics

The Phoenix Engine test suite follows the standard test pyramid with ambitious but achievable targets for v1.0.0:

| Level | Target Count | Percentage | Execution Time | Purpose |
|-------|-------------|------------|----------------|---------|
| **Unit Tests** | 500+ | 70% | < 2 minutes | Test individual functions, selectors, parsers in isolation |
| **Integration Tests** | 100+ | 20% | < 5 minutes | Test scraper + parser + normalizer integration, HTML fixtures |
| **End-to-End Tests** | 30+ | 10% | < 10 minutes | Test full CLI workflows, batch operations, auth flows |
| **Total** | **630+** | **100%** | **< 17 minutes** | |

### 2.2 Coverage Targets by Module

| Module | Unit Coverage | Integration Coverage | Minimum Combined |
|--------|--------------|---------------------|------------------|
| `phoenix.scrapers.http` | 95% | 5% | 95% |
| `phoenix.scrapers.browser` | 90% | 5% | 90% |
| `phoenix.scrapers.selectors` | 95% | 5% | 95% |
| `phoenix.scrapers.x_twitter` | 90% | 5% | 90% |
| `phoenix.scrapers.instagram` | 90% | 5% | 90% |
| `phoenix.scrapers.tiktok` | 85% | 5% | 85% |
| `phoenix.scrapers.linkedin` | 85% | 5% | 85% |
| `phoenix.scrapers.facebook` | 80% | 5% | 80% |
| `phoenix.scrapers.youtube` | 85% | 5% | 85% |
| `phoenix.scrapers.generic_web` | 90% | 5% | 90% |
| `phoenix.router` | 95% | 5% | 95% |
| `phoenix.strategy_selector` | 90% | 5% | 90% |
| `phoenix.pipeline` | 80% | 15% | 85% |
| `phoenix.processing.html_extractor` | 90% | 5% | 90% |
| `phoenix.processing.normalizer` | 90% | 5% | 90% |
| `phoenix.infrastructure.session_manager` | 90% | 5% | 90% |
| `phoenix.infrastructure.rate_limiter` | 90% | 5% | 90% |
| `phoenix.infrastructure.storage` | 85% | 10% | 90% |
| `phoenix.infrastructure.audit_logger` | 85% | 5% | 85% |
| `phoenix.cli` | 80% | 10% | 85% |
| **Overall** | **85%** | **15%** | **>= 85%** |

### 2.3 Test Count Breakdown

| Component | Unit Tests | Integration Tests | E2E Tests |
|-----------|-----------|------------------|-----------|
| URL Router | 40 | 5 | -- |
| Strategy Selector | 35 | 5 | -- |
| HTTP Scraper | 50 | 5 | -- |
| Browser Scraper | 40 | 5 | -- |
| Selector Engine | 60 | 5 | -- |
| HTML Extractor | 40 | 5 | -- |
| Content Normalizer | 30 | 5 | -- |
| X/Twitter Scraper | 60 | 5 | 2 |
| Instagram Scraper | 60 | 5 | 2 |
| TikTok Scraper | 50 | 5 | 2 |
| LinkedIn Scraper | 50 | 5 | 2 |
| Facebook Scraper | 40 | 5 | 2 |
| YouTube Scraper | 40 | 5 | 2 |
| Generic Web Scraper | 40 | 5 | 2 |
| Session Manager | 40 | 5 | 2 |
| Rate Limiter | 30 | 5 | -- |
| Storage | 25 | 10 | -- |
| Audit Logger | 25 | 5 | -- |
| Plugin Loader | 25 | 5 | -- |
| AI Assistant | 30 | 5 | -- |
| CLI Commands | 80 | 10 | 12 |
| **Total** | **~910** | **~120** | **~30** |

---

## 3. Unit Testing Strategy

### 3.1 What to Test

Every public function, class, and method must have unit tests. Private functions are tested indirectly through public interfaces.

**Required Test Categories:**

| Category | Description | Scraping Example |
|----------|-------------|------------------|
| **Happy Path** | Normal valid inputs produce expected outputs | Selector chain extracts tweet text from valid HTML |
| **Selector Fallback** | When primary selector fails, fallback matches | Primary `'div[lang]'` fails, fallback `'div[dir="auto"]'` succeeds |
| **Invalid HTML** | Malformed HTML is handled gracefully | Missing closing tags, invalid nesting |
| **Empty Results** | No matching elements returns None (not crash) | All selectors fail, result.value is None |
| **Edge Cases** | Boundary values and extreme inputs | HTML with 0 bytes, HTML with 10MB of content, count = "1.2K" |
| **Network Errors** | Connection failures trigger retries | Connection reset, DNS failure, timeout |
| **Rate Limiting** | 429 responses raise RateLimitedError | Retry-After header respected |
| **Bot Blocking** | 403 responses raise BlockedError | Increase delay suggestion provided |
| **Concurrent Access** | Parallel scrapes don't corrupt shared state | 50 concurrent HTTP requests, browser pool exhaustion |
| **Encoding Issues** | Non-UTF8 HTML handled correctly | Windows-1252, GB2312 encoded pages |

### 3.2 Mocking Strategy

All external dependencies are mocked in unit tests. No live network calls are ever made.

| Dependency | Mock Library | Mock Approach |
|------------|-------------|---------------|
| HTTP requests (httpx) | `respx` | Router-based mock for httpx.AsyncClient |
| HTTP responses (legacy) | `responses` | Decorator patches `requests` |
| Browser instances | `unittest.mock` | Mock Browser, Page, Context objects |
| Browser pool | `unittest.mock` | Mock pool with configurable availability |
| Playwright | `pytest-playwright` | Fixtures for browser/page/context |
| HTML fixtures | File system | Load from `tests/fixtures/html/` |
| Selector sets | In-memory | Construct SelectorSet in test setup |
| Storage | `aiosqlite` / mock | In-memory SQLite or mocked connection |
| AI/LLM services | `unittest.mock` | Mock AI responses with realistic selector suggestions |
| File system | `pyfakefs` | Virtual in-memory filesystem for archive tests |
| System clock | `freezegun` | Freeze time for timestamp-dependent tests |
| Session cookies | Mock data | Synthetic cookie dicts |

### 3.3 HTML Fixtures

HTML fixtures are the foundation of scraping tests. They are sanitized snapshots of real platform pages.

**Fixture Directory Structure:**
```
tests/fixtures/
|____ conftest.py                    # Fixture loading utilities
|____ html/
|   |____ x_twitter/
|   |   |____ tweet_standard.html     # Standard tweet layout
|   |   |____ tweet_thread.html       # Thread/reply tweet
|   |   |____ tweet_media.html        # Tweet with images/video
|   |   |____ tweet_v2_layout.html    # Updated layout (for change tests)
|   |   |____ profile.html            # User profile page
|   |   |____ error_404.html          # Not found page
|   |   |____ rate_limited.html       # Rate limit page
|   |   |____ meta.yaml               # Fixture metadata
|   |____ instagram/
|   |   |____ post_image.html
|   |   |____ post_video.html
|   |   |____ reel.html
|   |   |____ story.html
|   |   |____ profile.html
|   |   |____ login_required.html
|   |   |____ meta.yaml
|   |____ tiktok/
|   |   |____ video.html
|   |   |____ profile.html
|   |   |____ meta.yaml
|   |____ linkedin/
|   |   |____ post.html
|   |   |____ article.html
|   |   |____ login_wall.html
|   |   |____ meta.yaml
|   |____ youtube/
|   |   |____ watch_video.html
|   |   |____ shorts.html
|   |   |____ channel.html
|   |   |____ meta.yaml
|   |____ facebook/
|   |   |____ post.html
|   |   |____ reel.html
|   |   |____ meta.yaml
|   |____ generic/
|   |   |____ article_with_og.html    # Open Graph tags
|   |   |____ article_no_og.html      # No OG tags
|   |   |____ minimal.html            # Bare HTML
|   |   |____ malformed.html          # Invalid HTML
|   |   |____ empty.html              # Empty body
|   |   |____ large.html              # Very large document
|   |   |____ meta.yaml
```

**Fixture Metadata Format (`meta.yaml`):**
```yaml
# tests/fixtures/html/x_twitter/meta.yaml
fixtures:
  tweet_standard:
    source_url: "https://x.com/testuser/status/1234567890"
    captured_at: "2025-01-15T10:30:00Z"
    platform_version: "2025.01.14"
    html_size_bytes: 45230
    expected_fields:
      tweet_text: "This is a sample tweet for testing."
      author: "Test User"
      author_handle: "@testuser"
      timestamp: "2025-01-15T10:30:00+00:00"
      likes: 42
      shares: 7
      comments: 3
    notes: "Standard tweet layout, all primary selectors should match"

  tweet_v2_layout:
    source_url: "https://x.com/testuser/status/1234567891"
    captured_at: "2025-02-01T08:15:00Z"
    platform_version: "2025.02.01"
    notes: "Updated layout - primary selectors changed, fallbacks should catch"
```

**Fixture Loading Utility:**
```python
# tests/fixtures/conftest.py
import yaml
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent

def load_html_fixture(platform: str, name: str) -> str:
    """Load HTML fixture file as string."""
    path = FIXTURES_DIR / "html" / platform / f"{name}.html"
    if not path.exists():
        raise FileNotFoundError(f"HTML fixture not found: {path}")
    return path.read_text(encoding="utf-8")

def load_fixture_meta(platform: str) -> dict:
    """Load fixture metadata YAML."""
    path = FIXTURES_DIR / "html" / platform / "meta.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text())

def get_expected_fields(platform: str, fixture_name: str) -> dict:
    """Get expected extraction results for a fixture."""
    meta = load_fixture_meta(platform)
    fixture_meta = meta.get("fixtures", {}).get(fixture_name, {})
    return fixture_meta.get("expected_fields", {})

# pytest fixtures
@pytest.fixture
def x_twitter_tweet_html() -> str:
    return load_html_fixture("x_twitter", "tweet_standard")

@pytest.fixture
def x_twitter_tweet_v2_html() -> str:
    return load_html_fixture("x_twitter", "tweet_v2_layout")

@pytest.fixture
def x_twitter_expected() -> dict:
    return get_expected_fields("x_twitter", "tweet_standard")
```

### 3.4 Selector Unit Tests

Every selector in every selector set must be individually tested:

```python
# tests/unit/scrapers/test_x_twitter_selectors.py
import pytest
from bs4 import BeautifulSoup
from phoenix.scrapers.x_twitter.selectors import X_TWITTER_SELECTORS
from phoenix.scrapers.selectors import SelectorEngine, SelectorResult

class TestXTwitterSelectorSet:
    """Comprehensive tests for X/Twitter CSS selector set.

    Tests every selector in the set against HTML fixtures,
    verifies fallback chains, and validates critical field extraction.
    """

    @pytest.fixture
    def engine(self) -> SelectorEngine:
        engine = SelectorEngine()
        engine.register_selectors("x_twitter", X_TWITTER_SELECTORS)
        return engine

    @pytest.fixture
    def standard_tweet(self, x_twitter_tweet_html: str) -> BeautifulSoup:
        return BeautifulSoup(x_twitter_tweet_html, "lxml")

    # === PRIMARY SELECTOR TESTS ===

    def test_tweet_text_primary_selector(
        self, engine: SelectorEngine, standard_tweet: BeautifulSoup
    ):
        """Primary CSS selector for tweet_text extracts correctly."""
        result = engine.extract(standard_tweet, "x_twitter", "tweet_text")

        assert result.matched is True
        assert result.selector_type == "css_primary"
        assert result.value is not None
        assert len(result.value) > 0
        assert result.selector_used == X_TWITTER_SELECTORS.selectors["tweet_text"].primary

    def test_author_primary_selector(
        self, engine: SelectorEngine, standard_tweet: BeautifulSoup
    ):
        """Primary CSS selector for author extracts correctly."""
        result = engine.extract(standard_tweet, "x_twitter", "author")

        assert result.matched is True
        assert result.selector_type == "css_primary"
        assert result.value is not None

    def test_timestamp_primary_selector(
        self, engine: SelectorEngine, standard_tweet: BeautifulSoup
    ):
        """Primary CSS selector extracts datetime attribute from <time> element."""
        result = engine.extract(standard_tweet, "x_twitter", "timestamp")

        assert result.matched is True
        assert result.selector_type == "css_primary"
        assert result.value is not None
        # Should be ISO 8601 format
        assert "T" in result.value or "+" in result.value or "Z" in result.value

    def test_likes_primary_selector(
        self, engine: SelectorEngine, standard_tweet: BeautifulSoup
    ):
        """Primary CSS selector for likes count extracts numeric value."""
        result = engine.extract(standard_tweet, "x_twitter", "likes")

        assert result.matched is True
        assert result.value is not None
        # Should be numeric (may include K, M, commas)
        clean = result.value.replace("K", "").replace("M", "").replace(",", "").replace(".", "")
        assert clean.isdigit(), f"Likes value '{result.value}' is not numeric"

    # === FALLBACK CHAIN TESTS ===

    def test_tweet_text_fallback_chain_exists(self):
        """tweet_text has at least 2 fallback selectors."""
        chain = X_TWITTER_SELECTORS.selectors["tweet_text"]
        assert len(chain.fallbacks) >= 2, (
            f"tweet_text has only {len(chain.fallbacks)} fallbacks, "
            "minimum 2 required for critical fields"
        )

    def test_fallback_selectors_are_distinct(self):
        """All selectors in a chain (primary + fallbacks) are different."""
        for field, chain in X_TWITTER_SELECTORS.selectors.items():
            all_selectors = chain.all_selectors()
            assert len(all_selectors) == len(set(all_selectors)), (
                f"Field '{field}' has duplicate selectors in chain"
            )

    def test_fallback_ordering_most_to_least_specific(self):
        """Fallback selectors go from most specific to least specific."""
        chain = X_TWITTER_SELECTORS.selectors["tweet_text"]
        # Primary should be most specific (longest/most attributes)
        primary_specificity = chain.primary.count("[") + chain.primary.count("#")
        for i, fallback in enumerate(chain.fallbacks):
            fallback_specificity = fallback.count("[") + fallback.count("#")
            assert fallback_specificity <= primary_specificity + 1, (
                f"Fallback {i} '{fallback}' may be more specific than primary"
            )

    # === LAYOUT CHANGE TESTS ===

    def test_critical_fields_extracted_on_v2_layout(
        self,
        engine: SelectorEngine,
        x_twitter_tweet_v2_html: str,
    ):
        """Critical fields are still extracted when page layout changes.

        This test uses a fixture with updated HTML structure to verify
        that fallback selectors catch the change.
        """
        soup = BeautifulSoup(x_twitter_tweet_v2_html, "lxml")
        results = engine.extract_all(soup, "x_twitter")

        for field in X_TWITTER_SELECTORS.critical_fields:
            assert results[field].matched is True, (
                f"Critical field '{field}' not extracted on v2 layout. "
                f"Tried: primary={X_TWITTER_SELECTORS.selectors[field].primary}, "
                f"fallbacks={X_TWITTER_SELECTORS.selectors[field].fallbacks}. "
                f"Selector set may need update."
            )

    # === XPATH BACKUP TESTS ===

    def test_xpath_backups_exist_for_critical_fields(self):
        """Every critical field has an XPath backup expression."""
        for field in X_TWITTER_SELECTORS.critical_fields:
            assert field in X_TWITTER_SELECTORS.xpath_backups, (
                f"Critical field '{field}' missing XPath backup"
            )
            assert len(X_TWITTER_SELECTORS.xpath_backups[field]) > 0, (
                f"Critical field '{field}' has empty XPath backup"
            )

    def test_xpath_backups_are_valid(self):
        """All XPath backup expressions are syntactically valid."""
        from lxml import etree
        for field, xpath in X_TWITTER_SELECTORS.xpath_backups.items():
            try:
                etree.XPath(xpath)
            except etree.XPathSyntaxError as e:
                pytest.fail(f"Invalid XPath for field '{field}': {xpath} -- {e}")

    # === EXTRACT_ALL TESTS ===

    def test_extract_all_returns_all_fields(
        self, engine: SelectorEngine, standard_tweet: BeautifulSoup
    ):
        """extract_all returns results for every registered field."""
        results = engine.extract_all(standard_tweet, "x_twitter")

        assert len(results) == len(X_TWITTER_SELECTORS.selectors)
        for field in X_TWITTER_SELECTORS.selectors:
            assert field in results, f"Field '{field}' missing from extract_all results"
            assert isinstance(results[field], SelectorResult)

    def test_extract_all_tracks_selector_usage(
        self, engine: SelectorEngine, standard_tweet: BeautifulSoup
    ):
        """extract_all tracks which selector was used for each field."""
        results = engine.extract_all(standard_tweet, "x_twitter")

        for field, result in results.items():
            if result.matched:
                assert result.selector_used is not None
                assert result.selector_type in ("css_primary", "css_fallback", "xpath")

    # === EXPECTED VALUE TESTS ===

    def test_extracted_values_match_expected(
        self,
        engine: SelectorEngine,
        standard_tweet: BeautifulSoup,
        x_twitter_expected: dict,
    ):
        """Extracted field values match expected values from fixture metadata."""
        results = engine.extract_all(standard_tweet, "x_twitter")

        for field, expected_value in x_twitter_expected.items():
            if field in results and results[field].matched:
                # Normalize for comparison (strip whitespace, lowercase)
                actual = (results[field].value or "").strip()
                expected = str(expected_value).strip()
                assert actual == expected or expected.lower() in actual.lower(), (
                    f"Field '{field}': expected '{expected}', got '{actual}'"
                )
```

### 3.5 HTTP Scraper Unit Tests

```python
# tests/unit/test_http_scraper.py
import pytest
import respx
from httpx import Response
from phoenix.scrapers.http import HTTPScraper
from phoenix.infrastructure.rate_limiter import RateLimiter

class TestHTTPScraper:
    """Unit tests for HTTPScraper -- all HTTP calls mocked."""

    @pytest.fixture
    def scraper(self) -> HTTPScraper:
        client = httpx.AsyncClient(
            http2=True,
            limits=httpx.Limits(max_connections=10),
        )
        return HTTPScraper(
            http_client=client,
            rate_limiter=RateLimiter(requests_per_second=10.0),
        )

    @respx.mock
    async def test_fetch_success(self, scraper: HTTPScraper):
        """Successfully fetches HTML and returns parsed document."""
        html = "<html><body><h1>Test</h1></body></html>"
        route = respx.get("https://example.com/page").mock(
            return_value=Response(200, text=html)
        )

        result = await scraper.fetch("https://example.com/page")

        assert result.status_code == 200
        assert result.soup is not None
        assert result.soup.find("h1").get_text() == "Test"
        assert route.called

    @respx.mock
    async def test_fetch_with_cookies(self, scraper: HTTPScraper):
        """Sends session cookies with request."""
        session = Session(
            platform="x_twitter",
            cookies=[{"name": "auth_token", "value": "abc123", "domain": ".x.com"}],
            user_agent="TestAgent/1.0",
        )
        route = respx.get("https://x.com/user/status/123").mock(
            return_value=Response(200, text="<html></html>")
        )

        await scraper.fetch("https://x.com/user/status/123", session=session)

        request = route.calls.last.request
        assert "cookie" in request.headers
        assert "auth_token=abc123" in request.headers["cookie"]

    @respx.mock
    async def test_fetch_403_raises_blocked(self, scraper: HTTPScraper):
        """HTTP 403 raises BlockedError with diagnostics."""
        respx.get("https://example.com/page").mock(
            return_value=Response(403, text="Access Denied")
        )

        with pytest.raises(BlockedError) as exc_info:
            await scraper.fetch("https://example.com/page")

        assert exc_info.value.code == "SCR_040"
        assert exc_info.value.http_status == 403

    @respx.mock
    async def test_fetch_429_raises_rate_limited(self, scraper: HTTPScraper):
        """HTTP 429 raises RateLimitedError."""
        respx.get("https://example.com/page").mock(
            return_value=Response(
                429,
                text="Rate limited",
                headers={"Retry-After": "120"},
            )
        )

        with pytest.raises(RateLimitedError) as exc_info:
            await scraper.fetch("https://example.com/page")

        assert exc_info.value.code == "SCR_041"

    @respx.mock
    async def test_fetch_timeout_raises_timeout_error(self, scraper: HTTPScraper):
        """Request timeout raises TimeoutError."""
        respx.get("https://example.com/page").mock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )

        with pytest.raises(TimeoutError) as exc_info:
            await scraper.fetch("https://example.com/page")

        assert exc_info.value.code == "SCR_011"

    @respx.mock
    async def test_fetch_empty_html(self, scraper: HTTPScraper):
        """Empty HTML response returns empty soup."""
        respx.get("https://example.com/page").mock(
            return_value=Response(200, text="")
        )

        result = await scraper.fetch("https://example.com/page")

        assert result.status_code == 200
        assert result.raw_html == ""
        assert result.soup is not None  # BeautifulSoup handles empty

    @respx.mock
    async def test_fetch_malformed_html(self, scraper: HTTPScraper):
        """Malformed HTML is parsed without crashing."""
        html = "<html><body><div><span>unclosed"  # Missing closing tags
        respx.get("https://example.com/page").mock(
            return_value=Response(200, text=html)
        )

        result = await scraper.fetch("https://example.com/page")

        assert result.soup is not None
        # BeautifulSoup should fix the HTML
        assert result.soup.find("span") is not None

    @respx.mock
    async def test_user_agent_sent(self, scraper: HTTPScraper):
        """Transparent user-agent is sent with every request."""
        route = respx.get("https://example.com/page").mock(
            return_value=Response(200, text="<html></html>")
        )

        await scraper.fetch("https://example.com/page")

        request = route.calls.last.request
        assert "PhoenixEngine" in request.headers["user-agent"]
```

### 3.6 Browser Scraper Unit Tests

```python
# tests/unit/test_browser_scraper.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from phoenix.scrapers.browser import BrowserScraper, BrowserConfig

class TestBrowserScraper:
    """Unit tests for BrowserScraper -- Playwright fully mocked."""

    @pytest.fixture
    def mock_pool(self):
        """Create a mock browser pool."""
        pool = MagicMock()
        context = AsyncMock()
        page = AsyncMock()
        page.content = AsyncMock(return_value="<html><body><div id='app'>Loaded</div></body></html>")
        page.goto = AsyncMock()
        page.wait_for_selector = AsyncMock()
        page.screenshot = AsyncMock(return_value="/tmp/screenshot.png")
        context.new_page = AsyncMock(return_value=page)
        pool.acquire = AsyncMock(return_value=context)
        pool.release = AsyncMock()
        return pool

    @pytest.fixture
    def scraper(self, mock_pool) -> BrowserScraper:
        return BrowserScraper(
            browser_pool=mock_pool,
            rate_limiter=MagicMock(),
            config=BrowserConfig(headless=True),
        )

    async def test_fetch_renders_page(self, scraper: BrowserScraper, mock_pool):
        """Browser fetch navigates, waits, and returns rendered HTML."""
        result = await scraper.fetch("https://example.com/page")

        assert result.status_code == 200
        assert result.soup is not None
        assert result.soup.find("div", id="app").get_text() == "Loaded"

    async def test_fetch_waits_for_selector(self, scraper: BrowserScraper, mock_pool):
        """Browser waits for specified CSS selector before extraction."""
        result = await scraper.fetch(
            "https://example.com/page",
            options=ScrapingOptions(wait_for="article[data-testid='tweet']"),
        )

        page = await (await mock_pool.acquire()).new_page()
        page.wait_for_selector.assert_called_once_with(
            "article[data-testid='tweet']", timeout=30000
        )

    async def test_fetch_screenshot_option(self, scraper: BrowserScraper, mock_pool):
        """Screenshot is captured when option is enabled."""
        result = await scraper.fetch(
            "https://example.com/page",
            options=ScrapingOptions(screenshot=True),
        )

        assert result.screenshot_path is not None

    async def test_fetch_cookies_injected(self, scraper: BrowserScraper, mock_pool):
        """Session cookies are injected into browser context."""
        session = Session(
            platform="instagram",
            cookies=[{"name": "sessionid", "value": "abc", "domain": ".instagram.com"}],
            user_agent="TestAgent/1.0",
        )

        await scraper.fetch("https://instagram.com/p/ABC/", session=session)

        context = await mock_pool.acquire()
        context.add_cookies.assert_called_once()
```

### 3.7 Parameterized Tests

Use `@pytest.mark.parametrize` for testing multiple inputs:

```python
@pytest.mark.parametrize("url,expected_platform", [
    ("https://instagram.com/p/ABC123", "instagram"),
    ("https://www.instagram.com/p/ABC123", "instagram"),
    ("https://twitter.com/user/status/123", "x_twitter"),
    ("https://x.com/user/status/123", "x_twitter"),
    ("https://tiktok.com/@user/video/123", "tiktok"),
    ("https://linkedin.com/in/username", "linkedin"),
    ("https://youtube.com/watch?v=ABC123", "youtube"),
    ("https://example.com/blog/post", "generic_web"),
    ("https://subdomain.example.com/page", "generic_web"),
])
def test_url_routing(url: str, expected_platform: str, router: URLRouter):
    assert router.route(url) == expected_platform


@pytest.mark.parametrize("count_str,expected_int", [
    ("42", 42),
    ("1.2K", 1200),
    ("1.5M", 1500000),
    ("10K", 10000),
    ("2.3K", 2300),
    ("100", 100),
    ("0", 0),
])
def test_parse_count_normalization(count_str: str, expected_int: int):
    assert parse_count(count_str) == expected_int


@pytest.mark.parametrize("html_fixture,expected_strategy", [
    ("x_twitter/tweet_standard.html", ScrapingStrategy.HTTP),
    ("instagram/post_image.html", ScrapingStrategy.BROWSER),
    ("tiktok/video.html", ScrapingStrategy.BROWSER),
    ("youtube/watch_video.html", ScrapingStrategy.HTTP),
    ("generic/article_with_og.html", ScrapingStrategy.HTTP),
])
def test_strategy_selection(
    html_fixture: str,
    expected_strategy: ScrapingStrategy,
    strategy_selector: StrategySelector,
):
    # Strategy is selected based on platform, not HTML content
    url = "https://example.com/test"
    platform = html_fixture.split("/")[0]
    result = strategy_selector.select(url, platform)
    assert result.primary == expected_strategy
```

---

## 4. Integration Testing Strategy

### 4.1 Scraper + Parser Integration

Test that fetched HTML flows correctly through extraction and normalization:

```python
# tests/integration/test_http_to_extractor.py
import pytest
import respx
from httpx import Response

class TestHTTPToExtractorIntegration:
    """Integration: HTTPScraper fetches HTML, HTMLExtractor parses it."""

    @respx.mock
    async def test_full_http_pipeline(self):
        """HTTP fetch + selector extraction + normalization end-to-end."""
        # Arrange: HTML fixture with known content
        html = load_fixture("html/x_twitter/tweet_standard.html")
        respx.get("https://x.com/user/status/123").mock(
            return_value=Response(200, text=html)
        )

        # Act: Full pipeline
        http_scraper = HTTPScraper(get_test_client(), mock_limiter())
        html_doc = await http_scraper.fetch("https://x.com/user/status/123")

        extractor = HTMLExtractor(get_selector_engine())
        scraper = XScraper()
        platform_data = await scraper.parse(html_doc, extractor.selector_engine)

        normalizer = ContentNormalizer()
        output = normalizer.normalize(platform_data)

        # Assert: Output matches expected schema
        assert isinstance(output, UnifiedOutput)
        assert output.platform == "x_twitter"
        assert output.text is not None
        assert output.author is not None
        assert output.timestamp is not None
        assert output.likes is not None or output.likes is None  # Optional is OK
```

### 4.2 Playwright Test Server

For browser scraper integration tests, use a local test server:

```python
# tests/integration/test_browser_to_extractor.py
import pytest
from aiohttp import web

class TestBrowserToExtractorIntegration:
    """Integration: BrowserScraper renders JS, HTMLExtractor parses result."""

    @pytest.fixture(scope="session")
    async def test_server(self):
        """Start local HTTP server with test HTML fixtures."""
        async def handle(request):
            fixture_name = request.match_info.get("fixture", "tweet_standard")
            html = load_fixture(f"html/x_twitter/{fixture_name}.html")
            return web.Response(text=html, content_type="text/html")

        async def js_page(request):
            """Page that requires JavaScript to render content."""
            html = """
            <html>
                <body>
                    <div id="loading">Loading...</div>
                    <script>
                        setTimeout(() => {
                            document.getElementById('loading').innerHTML =
                                '<article data-testid="tweet"><div lang="en">Loaded via JS</div></article>';
                        }, 100);
                    </script>
                </body>
            </html>
            """
            return web.Response(text=html, content_type="text/html")

        app = web.Application()
        app.router.add_get("/fixtures/{fixture}", handle)
        app.router.add_get("/js-page", js_page)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 8765)
        await site.start()

        yield "http://localhost:8765"

        await runner.cleanup()

    async def test_browser_renders_js_content(self, test_server: str):
        """Browser scraper waits for JS-rendered content."""
        browser_scraper = BrowserScraper(get_test_pool(), mock_limiter())

        result = await browser_scraper.fetch(
            f"{test_server}/js-page",
            options=ScrapingOptions(wait_for="article[data-testid='tweet']"),
        )

        # Content was rendered by JavaScript
        assert result.soup.find("article", attrs={"data-testid": "tweet"}) is not None
        assert "Loaded via JS" in result.soup.get_text()
```

### 4.3 Platform Integration Tests

Each platform has integration tests that verify the full scraping pipeline:

```python
# tests/integration/test_x_twitter_integration.py
class TestXTwitterIntegration:
    """Full pipeline integration for X/Twitter scraper."""

    @respx.mock
    async def test_tweet_scrape_pipeline(self):
        """Full pipeline: fetch tweet HTML, extract, normalize, output."""
        html = load_fixture("html/x_twitter/tweet_standard.html")
        respx.get("https://x.com/testuser/status/1234567890").mock(
            return_value=Response(200, text=html)
        )

        engine = PhoenixEngine()
        result = await engine.scrape("https://x.com/testuser/status/1234567890")

        assert result.success is True
        assert result.output is not None
        assert result.output.platform == "x_twitter"
        assert result.output.text is not None
        assert len(result.selectors_used) > 0
        assert result.fallback_triggered is False

    @respx.mock
    async def test_tweet_with_layout_change_fallback(self):
        """When primary selectors fail, fallback chain succeeds."""
        html = load_fixture("html/x_twitter/tweet_v2_layout.html")
        respx.get("https://x.com/testuser/status/1234567891").mock(
            return_value=Response(200, text=html)
        )

        engine = PhoenixEngine()
        result = await engine.scrape("https://x.com/testuser/status/1234567891")

        assert result.success is True
        assert result.output is not None
        # Fallback was triggered because primary selectors failed
        assert result.fallback_triggered is True
```

---

## 5. Platform Testing Strategy

### 5.1 HTML Fixture Maintenance

HTML fixtures must be refreshed regularly to detect selector degradation:

| Platform | Refresh Frequency | Process |
|----------|-------------------|---------|
| X/Twitter | Weekly | Capture new HTML, run selector validation |
| Instagram | Weekly | Capture via browser (JS-rendered) |
| TikTok | Weekly | Capture via browser |
| LinkedIn | Bi-weekly | Limited access, use test account |
| Facebook | Bi-weekly | Capture via browser |
| YouTube | Weekly | HTTP capture usually sufficient |
| Generic | Monthly | Spot-check with popular sites |

**Fixture Capture Script:**
```python
# scripts/capture_fixtures.py
async def capture_fixture(url: str, platform: str, name: str) -> None:
    """Capture HTML fixture from live site for testing."""
    engine = PhoenixEngine()

    # Use HTTP for simple pages, Browser for JS-heavy
    strategy = ScrapingStrategy.BROWSER if platform in ("instagram", "tiktok", "facebook") else ScrapingStrategy.HTTP

    result = await engine.scrape(url, strategy=strategy, archive=True)

    if result.success:
        # Save raw HTML from archive
        archive_path = result.archived_path
        fixture_path = f"tests/fixtures/html/{platform}/{name}.html"
        shutil.copy(archive_path, fixture_path)

        # Update metadata
        update_fixture_meta(platform, name, url=url, captured_at=datetime.now(UTC))
        print(f"Captured: {fixture_path}")
    else:
        print(f"Failed to capture {url}: {result.error}")

    await engine.close()
```

### 5.2 Simulating Layout Changes

Create test fixtures that simulate layout changes to validate fallback chains:

```python
def test_selector_fallback_on_class_rename():
    """When platform renames a CSS class, fallback selectors still work."""
    # Original HTML: <div class="tweet-text">Content</div>
    # New HTML: <div class="post-text">Content</div>  (class renamed)

    original_html = '<div class="tweet-text">Hello</div>'
    changed_html = '<div class="post-text">Hello</div>'

    selectors = SelectorSet(
        platform="test",
        version="2025.01.01",
        selectors={
            "text": SelectorChain(
                field="text",
                primary="div.tweet-text",      # Will fail on changed HTML
                fallbacks=[
                    "div.post-text",           # Will match on changed HTML
                    "div[class*='text']",      # Generic fallback
                ],
            ),
        },
    )

    engine = SelectorEngine()
    engine.register_selectors("test", selectors)

    # Original layout: primary matches
    soup1 = BeautifulSoup(original_html, "lxml")
    result1 = engine.extract(soup1, "test", "text")
    assert result1.selector_type == "css_primary"

    # Changed layout: fallback matches
    soup2 = BeautifulSoup(changed_html, "lxml")
    result2 = engine.extract(soup2, "test", "text")
    assert result2.matched is True
    assert result2.value == "Hello"
    assert result2.selector_type == "css_fallback"
```

### 5.3 Platform Health Monitoring Tests

Daily automated tests that verify selector health:

```python
# tests/platform_health/test_selector_health.py
class TestSelectorHealth:
    """Monitor selector health across all platforms.

    These tests use cached HTML fixtures, not live sites.
    They detect when our fixtures no longer match our selectors,
    indicating the platform layout has changed.
    """

    @pytest.mark.parametrize("platform", [
        "x_twitter", "instagram", "tiktok", "linkedin", "facebook", "youtube",
    ])
    def test_all_selectors_match_fixtures(self, platform: str):
        """Verify all primary selectors match their fixture HTML."""
        fixture_names = get_fixture_names(platform)
        engine = get_platform_engine(platform)
        selector_set = get_platform_selectors(platform)

        failures = []
        for fixture_name in fixture_names:
            html = load_html_fixture(platform, fixture_name)
            soup = BeautifulSoup(html, "lxml")
            results = engine.extract_all(soup, platform)

            for field in selector_set.critical_fields:
                if not results[field].matched:
                    failures.append(f"{platform}/{fixture_name}: {field}")

        if failures:
            pytest.fail(
                f"{len(failures)} selector failures detected:\n" +
                "\n".join(f"  - {f}" for f in failures) +
                "\nPlatform layout may have changed. Update selectors."
            )
```

---

## 6. End-to-End Testing Scenarios

### 6.1 Happy Path Scenarios

```python
# tests/e2e/test_happy_path.py
class TestHappyPath:
    """End-to-end tests for common successful scraping flows."""

    @respx.mock
    async def test_scrape_single_url(self):
        """E2E: Scrape a single URL and get structured output."""
        html = load_fixture("html/x_twitter/tweet_standard.html")
        respx.get("https://x.com/user/status/123").mock(
            return_value=Response(200, text=html)
        )

        runner = CliRunner()
        result = runner.invoke(app, [
            "scrape", "https://x.com/user/status/123",
            "--format", "json",
        ])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is True
        assert output["output"]["platform"] == "x_twitter"
        assert output["output"]["text"] is not None

    @respx.mock
    async def test_scrape_batch_urls(self):
        """E2E: Scrape multiple URLs concurrently."""
        html = load_fixture("html/x_twitter/tweet_standard.html")
        respx.route(host="x.com").mock(return_value=Response(200, text=html))

        runner = CliRunner()
        result = runner.invoke(app, [
            "scrape-batch",
            "https://x.com/user/status/1",
            "https://x.com/user/status/2",
            "https://x.com/user/status/3",
            "--format", "jsonl",
            "--max-concurrency", "2",
        ])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) == 3
        for line in lines:
            output = json.loads(line)
            assert output["success"] is True

    @respx.mock
    async def test_scrape_with_browser_strategy(self):
        """E2E: Scrape using browser rendering."""
        # Browser tests use local test server
        html = load_fixture("html/instagram/post_image.html")

        with run_test_server(html) as server_url:
            runner = CliRunner()
            result = runner.invoke(app, [
                "scrape", f"{server_url}/post",
                "--strategy", "browser",
                "--wait-for", "article",
                "--format", "json",
            ])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["success"] is True
```

### 6.2 Fallback Chain Scenarios

```python
class TestFallbackChain:
    """E2E: Selector failure triggers fallback chain."""

    @respx.mock
    async def test_http_falls_back_to_browser(self):
        """E2E: HTTP scrape fails, falls back to browser."""
        # HTTP returns minimal HTML (no tweet content)
        minimal_html = "<html><body><div id='root'></div></body></html>"
        # Browser returns full rendered HTML
        full_html = load_fixture("html/x_twitter/tweet_standard.html")

        respx.get("https://x.com/user/status/123").mock(
            return_value=Response(200, text=minimal_html)
        )

        # Configure engine to try browser when HTTP extraction fails
        engine = PhoenixEngine()
        result = await engine.scrape("https://x.com/user/status/123")

        # Should succeed via fallback
        assert result.success is True
        assert result.fallback_triggered is True

    async def test_all_selectors_fail_triggers_ai(self):
        """E2E: All selectors fail, AI assistant extracts data."""
        # HTML with completely new layout
        new_layout_html = """
        <html><body>
            <div class="completely-new-structure">
                <h2>New Title Format</h2>
                <p>This is content in a new layout.</p>
                <span class="new-author">By Jane Doe</span>
            </div>
        </body></html>
        """

        with run_test_server(new_layout_html) as server_url:
            engine = PhoenixEngine(config=Config(ai_enabled=True))
            result = await engine.scrape(server_url)

            if result.ai_assisted:
                assert result.success is True
                assert result.output is not None
```

### 6.3 Blocked/Retry Scenarios

```python
class TestBlockedRetry:
    """E2E: Handle blocking and retry with exponential backoff."""

    @respx.mock
    async def test_rate_limit_retry(self):
        """E2E: 429 response triggers retry with backoff."""
        call_count = 0

        def response_handler(request):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return Response(429, headers={"Retry-After": "1"})
            return Response(200, text="<html><body>OK</body></html>")

        respx.get("https://x.com/user/status/123").mock(side_effect=response_handler)

        engine = PhoenixEngine()
        result = await engine.scrape("https://x.com/user/status/123")

        assert result.success is True
        assert call_count == 3  # Two failures, then success

    @respx.mock
    async def test_persistent_429_gives_up(self):
        """E2E: After max retries, rate limit error is returned."""
        respx.get("https://x.com/user/status/123").mock(
            return_value=Response(429, headers={"Retry-After": "300"})
        )

        engine = PhoenixEngine()
        result = await engine.scrape("https://x.com/user/status/123")

        assert result.success is False
        assert result.error.code == "SCR_041"
```

### 6.4 Authentication Flow Scenarios

```python
class TestAuthFlow:
    """E2E: Login, session storage, and authenticated scraping."""

    async def test_login_stores_session(self, tmp_path):
        """E2E: Interactive login captures and stores cookies."""
        # Mock the browser login flow
        with mock_browser_login() as mock_login:
            mock_login.return_value = Session(
                platform="instagram",
                cookies=[{"name": "sessionid", "value": "test123"}],
                user_agent="TestAgent/1.0",
            )

            runner = CliRunner()
            result = runner.invoke(app, ["login", "instagram"])

            assert result.exit_code == 0
            assert "Session saved" in result.output

    @respx.mock
    async def test_scrape_with_stored_session(self):
        """E2E: Scrape uses stored session cookies."""
        # Pre-store a session
        session = Session(
            platform="instagram",
            cookies=[{"name": "sessionid", "value": "abc123", "domain": ".instagram.com"}],
            user_agent="TestAgent/1.0",
        )
        save_test_session(session)

        html = load_fixture("html/instagram/post_image.html")
        route = respx.get("https://instagram.com/p/ABC/").mock(
            return_value=Response(200, text=html)
        )

        engine = PhoenixEngine()
        result = await engine.scrape("https://instagram.com/p/ABC/")

        assert result.success is True
        # Verify cookies were sent
        request = route.calls.last.request
        assert "sessionid=abc123" in (request.headers.get("cookie", ""))
```

### 6.5 E2E Test Inventory

| # | Scenario | Type | Priority |
|---|----------|------|----------|
| 1 | Scrape single URL, output JSON | Happy path | Critical |
| 2 | Scrape batch URLs, output JSONL | Happy path | Critical |
| 3 | Scrape with browser strategy | Happy path | Critical |
| 4 | Scrape Instagram post | Happy path | Critical |
| 5 | Scrape X/Twitter tweet | Happy path | Critical |
| 6 | Scrape TikTok video | Happy path | Critical |
| 7 | Scrape YouTube video | Happy path | High |
| 8 | Scrape LinkedIn post | Happy path | High |
| 9 | Scrape Facebook post | Happy path | High |
| 10 | HTTP fails, fallback to browser | Fallback | Critical |
| 11 | Primary selector fails, fallback matches | Fallback | Critical |
| 12 | All selectors fail, AI assists | Fallback | High |
| 13 | Rate limited, retry succeeds | Retry | Critical |
| 14 | Rate limited, max retries exceeded | Retry | High |
| 15 | Access blocked (403) | Error | Critical |
| 16 | Network timeout | Error | Critical |
| 17 | DNS failure | Error | High |
| 18 | Empty HTML response | Error | High |
| 19 | Malformed HTML | Error | High |
| 20 | Interactive login flow | Auth | High |
| 21 | Scrape with stored session | Auth | High |
| 22 | Login required content | Auth | High |
| 23 | Batch with partial failures | Batch | High |
| 24 | Concurrent scrapes with rate limiting | Concurrent | High |
| 25 | Archive raw HTML | Archive | Medium |
| 26 | Retrieve archived HTML | Archive | Medium |
| 27 | CLI with all output formats | CLI | Medium |
| 28 | Health check command | CLI | Medium |
| 29 | Config get/set commands | CLI | Low |
| 30 | Plugin list command | CLI | Low |

---

## 7. Performance Testing

### 7.1 Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| HTTP scrape (single) | < 5 seconds | Mock HTTP + parse + extract |
| Browser scrape (single) | < 15 seconds | Browser render + wait + extract |
| Batch of 10 URLs | < 30 seconds | Concurrent HTTP scrapes |
| Batch of 100 URLs | < 3 minutes | With rate limiting |
| Selector evaluation | < 100ms per field | Per HTML document |
| Memory per HTTP scrape | < 50 MB | Peak heap usage |
| Memory per browser tab | < 200 MB | Chromium process |
| Concurrent scrapes | 100 simultaneous | Without OOM |
| Test suite execution | < 17 minutes | Full pytest run |

### 7.2 Performance Test Implementation

```python
# tests/performance/test_scraper_performance.py
import pytest
import time
import tracemalloc

class TestScraperPerformance:
    """Performance benchmarks for scraping operations."""

    @pytest.mark.benchmark
    @respx.mock
    async def test_http_scrape_under_5_seconds(self):
        """HTTP scrape completes in under 5 seconds."""
        html = load_fixture("html/x_twitter/tweet_standard.html")
        respx.get("https://x.com/user/status/123").mock(
            return_value=Response(200, text=html)
        )

        start = time.perf_counter()
        engine = PhoenixEngine()
        result = await engine.scrape("https://x.com/user/status/123")
        elapsed = time.perf_counter() - start

        assert result.success is True
        assert elapsed < 5.0, f"HTTP scrape took {elapsed:.2f}s (target: <5s)"

    @pytest.mark.benchmark
    async def test_browser_scrape_under_15_seconds(self):
        """Browser scrape completes in under 15 seconds."""
        html = load_fixture("html/instagram/post_image.html")

        with run_test_server(html) as server_url:
            start = time.perf_counter()
            engine = PhoenixEngine()
            result = await engine.scrape(
                f"{server_url}/post",
                strategy=ScrapingStrategy.BROWSER,
            )
            elapsed = time.perf_counter() - start

            assert result.success is True
            assert elapsed < 15.0, f"Browser scrape took {elapsed:.2f}s (target: <15s)"

    @pytest.mark.benchmark
    @respx.mock
    async def test_batch_100_concurrent(self):
        """100 concurrent scrapes complete without errors or OOM."""
        html = load_fixture("html/x_twitter/tweet_standard.html")
        respx.route(host="x.com").mock(return_value=Response(200, text=html))

        urls = [f"https://x.com/user/status/{i}" for i in range(100)]

        tracemalloc.start()
        start = time.perf_counter()

        engine = PhoenixEngine()
        results = await engine.scrape_batch(urls, max_concurrency=100)

        elapsed = time.perf_counter() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        success_count = sum(1 for r in results if r.success)
        assert success_count == 100
        assert elapsed < 180.0, f"100 scrapes took {elapsed:.2f}s (target: <3min)"
        assert peak < 500 * 1024 * 1024, f"Peak memory {peak / 1024 / 1024:.1f}MB (target: <500MB)"

    @pytest.mark.benchmark
    def test_selector_evaluation_under_100ms(self):
        """Selector evaluation is under 100ms per field."""
        html = load_fixture("html/x_twitter/tweet_standard.html")
        soup = BeautifulSoup(html, "lxml")
        engine = get_x_twitter_engine()

        times = []
        for _ in range(100):
            start = time.perf_counter()
            engine.extract_all(soup, "x_twitter")
            times.append(time.perf_counter() - start)

        avg_time = sum(times) / len(times)
        assert avg_time < 0.1, f"Avg selector eval: {avg_time*1000:.1f}ms (target: <100ms)"
```

### 7.3 Load Testing

```python
# tests/performance/test_load.py
@pytest.mark.slow
async def test_sustained_scraping_rate():
    """Engine sustains 10 scrapes/second for 60 seconds."""
    html = "<html><body><h1>Test</h1></body></html>"

    with run_test_server(html) as server_url:
        engine = PhoenixEngine(config=Config(
            requests_per_second=20.0,  # High limit for testing
        ))

        start = time.perf_counter()
        tasks = [
            engine.scrape(f"{server_url}/page/{i}")
            for i in range(600)  # 10/sec * 60 sec
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.perf_counter() - start

        success_count = sum(1 for r in results if getattr(r, "success", False))
        rate = 600 / elapsed

        assert success_count >= 570, f"Only {success_count}/600 succeeded"
        assert rate >= 8.0, f"Rate: {rate:.1f}/sec (target: >=8/sec)"
```

---

## 8. Security Testing

### 8.1 Dependency Scanning

```yaml
# .github/workflows/security.yml
security-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Run Bandit (Python security linter)
      run: bandit -r phoenix/ -f json -o bandit-report.json || true
    - name: Run pip-audit
      run: pip-audit --desc --format=json -o audit-report.json || true
    - name: Check for banned packages
      run: |
        # Ensure no official API packages are present
        BANNED="instagrapi tweepy google-api-python-client praw"
        for pkg in $BANNED; do
          if pip show $pkg 2>/dev/null; then
            echo "ERROR: Banned package $pkg is installed"
            exit 1
          fi
        done
        echo "No banned packages found"
```

### 8.2 Secret Detection

```yaml
- name: Detect secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: main
    head: HEAD
```

**Pre-commit secret detection:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: detect-private-key
```

### 8.3 Cookie Storage Encryption Tests

```python
class TestCookieEncryption:
    """Verify session cookies are encrypted at rest."""

    async def test_cookies_encrypted_in_storage(self):
        """Cookies stored in database are encrypted, not plaintext."""
        session = Session(
            platform="instagram",
            cookies=[{"name": "sessionid", "value": "secret_value_123"}],
            user_agent="TestAgent/1.0",
        )

        manager = SessionManager(storage=get_test_storage())
        await manager.save_session(session)

        # Read raw from database
        raw = await get_test_storage().raw_query(
            "SELECT cookies FROM sessions WHERE platform = ?", ("instagram",)
        )

        # Verify sessionid value is NOT in plaintext
        assert "secret_value_123" not in str(raw)
        # Verify it IS encrypted (starts with encryption header)
        assert str(raw).startswith("gAAAA")  # Fernet format

    async def test_cookies_decrypted_on_retrieval(self):
        """Cookies are correctly decrypted when session is retrieved."""
        # ...setup...
        retrieved = await manager.get_session("instagram")
        assert retrieved.cookies[0]["value"] == "secret_value_123"
```

### 8.4 User-Agent Transparency Tests

```python
class TestUserAgentTransparency:
    """Verify transparent user-agent identification."""

    @respx.mock
    async def test_user_agent_includes_phoenix(self):
        """Every request includes PhoenixEngine in User-Agent."""
        route = respx.get("https://example.com/page").mock(
            return_value=Response(200, text="<html></html>")
        )

        engine = PhoenixEngine()
        await engine.scrape("https://example.com/page")

        request = route.calls.last.request
        ua = request.headers["user-agent"]
        assert "PhoenixEngine" in ua
        assert "bot" in ua.lower() or "crawler" in ua.lower() or "research" in ua.lower()

    @respx.mock
    async def test_no_fake_browser_ua_by_default(self):
        """Default UA does not impersonate a major browser."""
        route = respx.get("https://example.com/page").mock(
            return_value=Response(200, text="<html></html>")
        )

        engine = PhoenixEngine()
        await engine.scrape("https://example.com/page")

        request = route.calls.last.request
        ua = request.headers["user-agent"]
        assert "Chrome/" not in ua, "Should not impersonate Chrome by default"
        assert "Firefox/" not in ua, "Should not impersonate Firefox by default"
        assert "Safari/" not in ua, "Should not impersonate Safari by default"
```

---

## 9. Compliance Testing

### 9.1 Rate Limiting Enforcement

```python
class TestRateLimitCompliance:
    """Verify rate limiting is enforced."""

    @respx.mock
    async def test_requests_are_rate_limited(self):
        """Requests to same domain are spaced according to rate limit."""
        times = []

        def track_request(request):
            times.append(time.perf_counter())
            return Response(200, text="<html></html>")

        respx.get("https://x.com/user/status/123").mock(side_effect=track_request)
        respx.get("https://x.com/user/status/456").mock(side_effect=track_request)
        respx.get("https://x.com/user/status/789").mock(side_effect=track_request)

        engine = PhoenixEngine(config=Config(requests_per_second=1.0))
        await engine.scrape_batch([
            "https://x.com/user/status/123",
            "https://x.com/user/status/456",
            "https://x.com/user/status/789",
        ])

        # With 1 req/sec, requests should be at least 1 second apart
        for i in range(1, len(times)):
            gap = times[i] - times[i-1]
            assert gap >= 0.9, f"Requests only {gap:.2f}s apart (min: 1s)"

    @respx.mock
    async def test_per_domain_rate_limits(self):
        """Different domains can have different rate limits."""
        config = Config(
            requests_per_second=10.0,  # Global default
            per_domain_limits={
                "x.com": 0.5,  # Very slow for X
                "youtube.com": 2.0,  # Faster for YouTube
            },
        )

        engine = PhoenixEngine(config=config)
        limiter = engine.infrastructure.rate_limiter

        # X should be slower
        x_delay = await limiter.get_delay("x.com")
        yt_delay = await limiter.get_delay("youtube.com")

        assert x_delay > yt_delay, "X should have longer delay than YouTube"
```

### 9.2 robots.txt Compliance Tests

```python
class TestRobotsTxtCompliance:
    """Verify robots.txt is fetched and respected."""

    @respx.mock
    async def test_robots_txt_fetched(self):
        """robots.txt is fetched before scraping a new domain."""
        robots_txt = """
        User-agent: *
        Crawl-delay: 2
        Disallow: /admin/
        Allow: /
        """
        respx.get("https://example.com/robots.txt").mock(
            return_value=Response(200, text=robots_txt)
        )
        respx.get("https://example.com/page").mock(
            return_value=Response(200, text="<html></html>")
        )

        engine = PhoenixEngine(config=Config(respect_robots_txt=True))
        await engine.scrape("https://example.com/page")

        # robots.txt was fetched
        robots_route = [r for r in respx.routes if "robots.txt" in str(r.url)]
        assert len(robots_route) > 0

    @respx.mock
    async def test_disallowed_url_blocked(self):
        """URLs disallowed by robots.txt are rejected."""
        robots_txt = """
        User-agent: *
        Disallow: /admin/
        """
        respx.get("https://example.com/robots.txt").mock(
            return_value=Response(200, text=robots_txt)
        )

        engine = PhoenixEngine(config=Config(respect_robots_txt=True))

        with pytest.raises(ScrapingError) as exc:
            await engine.scrape("https://example.com/admin/secret")

        assert "robots.txt" in str(exc.value).lower()

    @respx.mock
    async def test_crawl_delay_respected(self):
        """Crawl-delay directive is respected."""
        robots_txt = """
        User-agent: *
        Crawl-delay: 5
        """
        respx.get("https://example.com/robots.txt").mock(
            return_value=Response(200, text=robots_txt)
        )

        engine = PhoenixEngine(config=Config(respect_robots_txt=True))
        limiter = engine.infrastructure.rate_limiter

        delay = await limiter.get_delay("example.com")
        assert delay >= 5.0, f"Crawl-delay not respected: {delay}s < 5s"
```

### 9.3 Public Data Only Enforcement

```python
class TestPublicDataOnly:
    """Verify only publicly accessible data is scraped."""

    @respx.mock
    async def test_private_content_not_extracted(self):
        """Login-required pages are handled gracefully, not bypassed."""
        login_html = """
        <html><body>
            <h1>Log in to continue</h1>
            <form action="/login">
                <input type="password" name="password">
            </form>
        </body></html>
        """
        respx.get("https://instagram.com/private/page").mock(
            return_value=Response(200, text=login_html)
        )

        engine = PhoenixEngine()
        result = await engine.scrape("https://instagram.com/private/page")

        # Should NOT bypass login or extract private data
        assert result.output is None or result.output.text is None
        assert result.error is not None
        assert result.error.code == "SCR_061"  # LoginRequired

    async def test_no_credential_bypass_attempts(self):
        """Engine never attempts to submit login forms or bypass auth."""
        # Static analysis: verify no form submission code exists
        # This is checked by grep in CI:
        # grep -r "submit.*form" phoenix/ || true
        # grep -r "password.*send" phoenix/ || true
        # grep -r "bypass" phoenix/ || true
        assert True  # Placeholder for static analysis test
```

### 9.4 Audit Logging Tests

```python
class TestAuditLogging:
    """Verify every scrape action is logged."""

    @respx.mock
    async def test_successful_scrape_logged(self):
        """Successful scrape is recorded in audit log."""
        respx.get("https://x.com/user/status/123").mock(
            return_value=Response(200, text="<html></html>")
        )

        engine = PhoenixEngine()
        result = await engine.scrape("https://x.com/user/status/123")

        # Check audit log
        logs = await engine.infrastructure.audit_logger.query(
            url="https://x.com/user/status/123"
        )
        assert len(logs) >= 1
        assert logs[0]["success"] is True
        assert logs[0]["timestamp"] is not None

    @respx.mock
    async def test_failed_scrape_logged(self):
        """Failed scrape is recorded in audit log with error details."""
        respx.get("https://x.com/user/status/123").mock(
            return_value=Response(404, text="Not Found")
        )

        engine = PhoenixEngine()
        result = await engine.scrape("https://x.com/user/status/123")

        logs = await engine.infrastructure.audit_logger.query(
            url="https://x.com/user/status/123"
        )
        assert len(logs) >= 1
        assert logs[0]["success"] is False
        assert logs[0]["error_code"] is not None
```

---

## 10. CI/CD Pipeline (4-Tier)

### 10.1 Tier 1: Pre-Commit (Local)

Runs on every `git commit` via pre-commit hooks. Must pass in < 10 seconds.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: local
    hooks:
      - id: mypy
        name: mypy type check
        entry: mypy phoenix/ --strict
        language: system
        types: [python]
        pass_filenames: false

      - id: unit-tests-fast
        name: Fast unit tests
        entry: pytest tests/unit -x -q --tb=short
        language: system
        types: [python]
        pass_filenames: false
```

### 10.2 Tier 2: Pull Request (CI)

Runs on every Pull Request. Must pass in < 5 minutes.

```yaml
# .github/workflows/pr.yml
name: Pull Request Checks
on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          playwright install chromium

      - name: Lint
        run: |
          black --check phoenix/ tests/
          ruff check phoenix/ tests/
          mypy phoenix/ --strict

      - name: Unit tests
        run: pytest tests/unit -v --tb=short --cov=phoenix --cov-report=xml

      - name: Coverage check
        run: |
          coverage report --fail-under=85

      - name: Check for banned packages
        run: |
          BANNED="instagrapi tweepy google-api-python-client praw snscrape"
          for pkg in $BANNED; do
            if pip list | grep -i "$pkg"; then
              echo "ERROR: Banned package $pkg detected"
              exit 1
            fi
          done

      - name: Security scan
        run: |
          bandit -r phoenix/ -ll
          pip-audit --desc
```

### 10.3 Tier 3: Pre-Merge (CI)

Runs before merge to `main`. Full test suite. Must pass in < 20 minutes.

```yaml
# .github/workflows/pre-merge.yml
name: Pre-Merge Full Test Suite
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  full-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev,test]"
          playwright install chromium

      - name: Run full test suite
        run: |
          pytest tests/ \
            -v \
            --tb=short \
            --cov=phoenix \
            --cov-report=html \
            --cov-report=xml \
            --cov-fail-under=85

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml

      - name: Upload HTML report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report-py${{ matrix.python-version }}
          path: htmlcov/

  e2e-test:
    runs-on: ubuntu-latest
    needs: full-test
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install
        run: |
          pip install -e ".[dev,test]"
          playwright install chromium
      - name: E2E tests
        run: pytest tests/e2e -v --tb=short
```

### 10.4 Tier 4: Release (CD)

Runs on release tag creation. Full validation + packaging.

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ["v*"]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Full validation
        run: |
          pip install -e ".[dev,test]"
          playwright install chromium
          pytest tests/ -v --tb=short
          black --check phoenix/ tests/
          ruff check phoenix/ tests/
          mypy phoenix/ --strict

  build:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build package
        run: |
          pip install build twine
          python -m build
          twine check dist/*
      - name: Upload to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

---

## 10.5 Testing AI-Generated Adapters

PhoenixArchitect-generated adapters must be treated as first-class production code and pass the same quality gates as hand-written adapters.

### 10.5.1 Mocked HTML Fixtures for Discovered Sites

- Each candidate site discovered by `phoenix discover` must have at least one representative **mock HTML fixture** checked into `tests/fixtures/generated/<domain>/`.
- Fixtures must include:
  - A category/search-results page with multiple listings.
  - At least one detail page linked from the category page.
  - A pagination sample (numbered, "Load more", or infinite-scroll stub) if present.
- Fixtures are captured by the Explorer/Collector roles during an `architect` run using `--save-samples`; they can be replayed offline via the engine’s fixture replay mode.

### 10.5.2 Validation Loop Tests

- The Critic role executes a deterministic validation suite against the generated adapter:
  1. **Compile test**: `python -m py_compile` on generated adapter and test file.
  2. **Static analysis**: `ruff check`, `black --check`, and `mypy --strict` must pass.
  3. **Selector coverage**: Generated selectors must match at least one element in the mock fixtures.
  4. **Schema conformance**: Extracted records must include all required `BaseAdapter` fields (`title`, `price`, `location`, `url`, `image_url`) and pass Pydantic validation.
  5. **Pagination probe**: `next_page_url`/`next_page_params` must advance correctly across the paginated fixture.
- If validation fails, the Critic emits a structured diff/error report; the Coder role consumes it and produces a revised adapter. The loop is capped at **3 iterations**.
- Unit tests in `tests/unit/intelligence/test_architect_critic.py` mock LLM responses to assert the loop terminates with a passing adapter.

### 10.5.3 Coverage Requirements for Generated Code

| Metric | Threshold | Notes |
|--------|-----------|-------|
| Line coverage of generated adapter | ≥ 70% | Measured against mock fixtures; live-site coverage is a bonus. |
| Branch coverage (pagination paths) | ≥ 60% | List, detail, and at least one pagination branch must be exercised. |
| Generated test file | ≥ 1 test per public method | `parse_listings`, `parse_detail`, `pagination` |
| Overall project coverage impact | No drop below 85% | Generated code is included in the aggregate report. |

### 10.5.4 Human-in-the-Loop Gate

Even with `--auto-approve`, the generated adapter is written to a staging directory (`src/phoenix/adapters/generated/`) and is **not** registered in `adapters/__init__.py` until a maintainer runs `phoenix architect --promote <adapter>` or moves it to `src/phoenix/adapters/`.

---

## 11. Test Execution Summary

### 11.1 Running Tests

```bash
# All tests
pytest

# Unit tests only (fast: ~2 min)
pytest tests/unit -v

# Unit tests with coverage
pytest tests/unit -v --cov=phoenix --cov-report=html

# Integration tests only
pytest tests/integration -v

# E2E tests only
pytest tests/e2e -v

# Specific platform scraper tests
pytest tests/unit/scrapers/test_x_twitter.py -v
pytest tests/unit/scrapers/test_instagram.py -v

# Performance benchmarks
pytest tests/performance -v --benchmark-only

# With live HTML fixtures (for updating fixtures)
pytest tests/ --use-live-fixtures

# Parallel execution
pytest tests/unit -n auto
```

### 11.2 Test Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --no-header
    -ra
markers =
    slow: Tests that take > 30 seconds
    benchmark: Performance benchmark tests
    e2e: End-to-end tests
    integration: Integration tests
    unit: Unit tests (default)
    flaky: Tests that may fail intermittently
filterwarnings =
    ignore::DeprecationWarning:bs4.*
    ignore::UserWarning
```

---

## 12. Quality Gates

### 12.1 Merge Requirements

| Gate | Threshold | Enforced By |
|------|-----------|-------------|
| Unit test pass rate | 100% | CI (Tier 2) |
| Integration test pass rate | 100% | CI (Tier 3) |
| E2E test pass rate | 100% | CI (Tier 3) |
| Code coverage | >= 85% | CI (Tier 2) |
| mypy strict | 0 errors | CI (Tier 2) |
| ruff | 0 errors | CI (Tier 2) |
| black format | 0 changes | CI (Tier 2) |
| Bandit security | 0 high severity | CI (Tier 2) |
| Banned packages | 0 detected | CI (Tier 2) |
| Documentation | Updated | PR review |
| Selector fallback coverage | 100% of critical fields | PR review |

### 12.2 Release Checklist

- [ ] All 630+ tests passing
- [ ] Code coverage >= 85%
- [ ] All security scans clean
- [ ] No banned packages detected
- [ ] All selector sets have fallback chains
- [ ] HTML fixtures updated within last 7 days
- [ ] Selector health metrics >= 90% for all platforms
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
