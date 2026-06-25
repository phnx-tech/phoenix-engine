# Phoenix Engine -- Development Standards & Guidelines

**Version:** 2.0.0
**Date:** 2025-01-20
**Status:** Authoritative Specification
**Audience:** AI Development Agents (Kimi Code), Contributing Engineers, Plugin Authors
**Constraint:** NO OFFICIAL SOCIAL MEDIA APIs ARE EVER USED. All data comes from raw HTML parsing.

---

## Table of Contents

1. [Code Style](#1-code-style)
2. [Git Workflow](#2-git-workflow)
3. [Testing Standards](#3-testing-standards)
4. [Documentation Standards](#4-documentation-standards)
5. [Plugin Development Guide](#5-plugin-development-guide)
6. [AI Agent Coding Prompts](#6-ai-agent-coding-prompts)

---

## 1. Code Style

### 1.1 PEP 8 Compliance

All code must comply with [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/) with the following explicit exceptions and extensions:

| Rule | Standard | Our Choice | Rationale |
|------|----------|------------|-----------|
| Line length | 79 chars | **100 chars** | Modern displays, readable diffs, matches Black default |
| Docstring quotes | `"""` or `'''` | **`"""` only** | Consistency, Google-style requirement |
| Import grouping | PEP 8 groups | **Ruff isort** | Automated, consistent enforcement |
| Type hints | Optional | **Mandatory** | Static analysis safety, IDE support, self-documenting |
| Trailing commas | Optional | **Required** in multi-line | Cleaner diffs when adding items |

### 1.2 Black Formatter

Black is the mandatory code formatter. All committed code must pass Black formatting.

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ["py311", "py312"]
include = "\\.pyi?$"
extend-exclude = """
/(
    migrations
  | archive
  | \.venv
)/
"""
```

**Pre-commit integration:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3.12
```

### 1.3 Ruff Linter

Ruff replaces flake8, pylint, pydocstyle, and isort. Configuration is centralized in `pyproject.toml`.

```toml
# pyproject.toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    # Conventions we intentionally relax
    "D105",     # Missing docstring in magic method (__init__, etc.)
    "D107",     # Missing docstring in __init__
    "ANN101",   # Missing type annotation for `self`
    "ANN102",   # Missing type annotation for `cls`
    "CPY001",   # Missing copyright notice
    "TD003",    # Missing issue link in TODO
    "FIX002",   # Line contains TODO -- we allow inline TODOs
    "ERA001",   # Found commented-out code -- false positives common
    "EM101",    # Exception must not use f-string literal (EM)
    "EM102",    # Exception must not use string literal (EM)
    "TRY003",   # Raise with message outside exception class
    # Docstring style -- we use Google-style, not numpy
    "D407",     # Missing dashed underline after section
    "D413",     # Missing blank line after last section
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.mccabe]
max-complexity = 12  # Slightly relaxed from default 10

[tool.ruff.lint.per-file-ignores]
# Tests have different standards
"tests/*" = [
    "S101",     # Use of assert (pytest uses assert)
    "D100",     # Missing docstring in public module
    "D103",     # Missing docstring in public function
    "SLF001",   # Access to private members (testing internals)
    "ARG001",   # Unused function argument (pytest fixtures)
    "PLR2004",  # Magic value in comparison
]
"tests/fixtures/*" = ["ALL"]  # Fixture files are exempt
"*/__init__.py" = ["D104"]
```

### 1.4 Import Ordering

Imports are organized into three groups, separated by blank lines:

```python
"""Module docstring."""

# 1. Standard library imports
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# 2. Third-party imports
import httpx
import structlog
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# 3. First-party (Phoenix) imports
from phoenix.exceptions import ScrapingError, HTTPError
from phoenix.models import ScrapingResult, UnifiedOutput
```

**Rules:**
- Use absolute imports within the same package: `from phoenix.models import X` not `from .models import X`
- Each import on its own line (no `import os, sys`)
- Sort alphabetically within groups
- `__future__` imports (if any) go above standard library

### 1.5 Type Hints -- Mandatory

All function parameters and return values must have type annotations. The codebase runs under `mypy --strict`.

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true
warn_unreachable = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_configs = true
show_error_codes = true
```

**Type hint requirements:**

```python
# CORRECT -- fully typed
def extract_field(
    soup: BeautifulSoup,
    selector_chain: SelectorChain,
    field_name: str,
) -> SelectorResult:
    ...

# INCORRECT -- missing types
def extract_field(soup, selector_chain, field_name):
    ...

# CORRECT -- async with typed parameters and return
async def scrape_url(
    self,
    url: str,
    *,
    strategy: ScrapingStrategy = ScrapingStrategy.HTTP,
) -> ScrapingResult:
    ...
```

### 1.6 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `HTMLExtractor`, `SelectorEngine` |
| Functions/Methods | snake_case | `extract_field()`, `fetch_html()` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT`, `MAX_RETRIES` |
| Private members | Leading underscore | `_parse_html()`, `_internal_cache` |
| Type variables | PascalCase, descriptive | `ScraperType`, `ResultT` |
| Module names | snake_case | `html_extractor.py`, `selector_engine.py` |
| Abstract bases | Leading `ABC` or suffix `Base` | `ScraperPlugin(ABC)`, `HTMLScraper` |

### 1.7 Scraping-Specific Conventions

**CSS Selectors as Constants:**
Platform selector strings must be defined as module-level constants with clear naming:

```python
# GOOD: Clear, named, with platform prefix
X_TWITTER_SELECTORS_V20250115 = SelectorSet(
    platform="x_twitter",
    version="2025.01.15",
    selectors={
        "tweet_text": SelectorChain(
            field="tweet_text",
            primary='article[data-testid="tweet"] div[lang]',
            fallbacks=[
                'article div[dir="auto"][data-testid="tweetText"]',
                'article div[dir="auto"]',
            ],
            attribute=None,
        ),
    },
)

# BAD: Inline strings, no version, no fallbacks
text = soup.select_one("div[lang]").get_text()  # Fragile!
```

**No Official API References:**
```python
# FORBIDDEN: Official API clients
from instagrapi import Client  # NEVER
import tweepy  # NEVER
from googleapiclient.discovery import build  # NEVER

# CORRECT: Pure HTML scraping
from bs4 import BeautifulSoup
from phoenix.scrapers.selectors import SelectorEngine, SelectorSet
```

**HTML Parsing Pattern:**
Always use the SelectorEngine for extraction -- never inline `soup.select_one()` calls in scraper logic:

```python
# CORRECT: Use SelectorEngine with registered selector sets
async def parse(self, html_doc: HTMLDocument, engine: SelectorEngine) -> PlatformData:
    results = engine.extract_all(html_doc.soup, "x_twitter")
    return PlatformData(
        platform="x_twitter",
        raw_fields={
            "text": results["tweet_text"].value,
            "author": results["author"].value,
        },
        selector_results=results,
    )

# BAD: Hardcoded selectors scattered in code
def bad_parse(html):
    soup = BeautifulSoup(html, "lxml")
    text = soup.select_one('div[lang]').get_text()  # No fallback, no tracking
    return {"text": text}
```

---

## 2. Git Workflow

### 2.1 Trunk-Based Development

Phoenix Engine uses trunk-based development. All changes flow through short-lived feature branches into `main`.

```
main (always deployable)
  |
  |-- feature/selector-update-x
  |-- feature/instagram-reels-support
  |-- bugfix/linkedin-timeout
  |-- docs/api-spec-update
```

**Rules:**
- `main` is always deployable and passing all tests
- Feature branches live for maximum 3 days
- No long-lived feature branches
- All changes merged via Pull Request
- Squash merge preferred for clean history

### 2.2 Branch Naming

```
feature/<short-description>      # New features
feature/<platform>-<thing>       # e.g., feature/x-thread-scraping
bugfix/<short-description>       # Bug fixes
bugfix/<platform>-<issue>        # e.g., bugfix/instagram-selector-fail
hotfix/<short-description>       # Critical production fixes
refactor/<short-description>     # Code refactoring
docs/<short-description>         # Documentation updates
test/<short-description>         # Test additions/improvements
selector/<platform>-<version>    # Selector set updates
```

### 2.3 Commit Message Format

```
<type>(<scope>): <short summary>

<body: explain what and why, not how>

<footer: references #issues, breaking changes>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `selector`: Selector set update
- `scraper`: Scraper plugin change
- `docs`: Documentation only
- `test`: Test addition or fix
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance (deps, config)

**Examples:**
```
selector(x-twitter): update selectors for new layout v2025.02.01

X/Twitter changed their DOM structure on Jan 30. Updated primary
selectors for tweet_text, author, and timestamp fields. Added new
fallback selectors for the changed layout.

Fixes #42

---

feat(scraper): add TikTok profile scraping support

Added TikTokProfileScraper with selectors for bio, follower count,
and recent videos. Uses browser strategy due to heavy JS rendering.

Closes #55

---

fix(http): increase default timeout for JS-heavy platforms

Instagram and TikTok pages often take >30s to render. Increased
default browser timeout from 30s to 45s for these platforms.
```

### 2.4 Pull Request Process

1. **Branch:** Create feature branch from latest `main`
2. **Code:** Implement changes following all standards
3. **Test:** All tests pass locally (`pytest`, `mypy`, `ruff`, `black`)
4. **Commit:** Follow commit message conventions
5. **Push:** Push branch and create PR with template
6. **Review:** Require 1 approval for standard changes, 2 for architectural
7. **CI:** All CI checks must pass
8. **Merge:** Squash merge to `main`

### 2.5 Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Selector update
- [ ] Breaking change
- [ ] Documentation

## Platforms Affected
- [ ] Instagram
- [ ] X/Twitter
- [ ] TikTok
- [ ] LinkedIn
- [ ] Facebook
- [ ] YouTube
- [ ] Generic Web
- [ ] Core/Infrastructure

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Tested against real HTML (provide URL)
- [ ] Selectors tested on live page

## Checklist
- [ ] Code follows style guide (black, ruff, mypy)
- [ ] Selectors have fallback chains
- [ ] No hardcoded API keys or credentials
- [ ] Error handling implemented
- [ ] Documentation updated
```

---

## 3. Testing Standards

### 3.1 Testing Philosophy for Scraping Code

Scraping code has unique testing challenges: target websites change, HTML structure evolves, and network calls must be mocked. Our testing strategy addresses these:

1. **Mock all HTTP:** Never make live network calls in tests
2. **Use HTML fixtures:** Store real HTML snapshots as test fixtures
3. **Test selector chains:** Verify primary + fallback selectors work
4. **Test against change:** Simulate layout changes by modifying fixtures
5. **Property-based tests:** Verify output schema compliance

### 3.2 Test File Structure

```
tests/
|____ conftest.py                    # Global fixtures and config
|____ __init__.py
|____
|____ fixtures/                      # HTML fixtures and test data
|   |____ html/
|   |   |____ x_twitter/
|   |   |   |____ tweet_v1.html      # Real tweet page HTML snapshot
|   |   |   |____ tweet_v2.html      # Updated layout (for change testing)
|   |   |   |____ profile.html       # Profile page HTML
|   |   |____ instagram/
|   |   |   |____ post.html
|   |   |   |____ reel.html
|   |   |____ tiktok/
|   |   |   |____ video.html
|   |   |____ generic/
|   |   |   |____ article.html
|   |   |   |____ og_tags.html
|   |____ selectors/
|   |   |____ x_twitter_selectors.yaml  # Selector set fixtures
|   |____ sessions/
|   |   |____ mock_session.json
|   |____ config/
|   |   |____ test_config.toml
|
|____ unit/                          # Unit tests (70% of test suite)
|   |____ __init__.py
|   |____ conftest.py
|   |____ test_url_router.py         # ~40 tests
|   |____ test_strategy_selector.py  # ~35 tests
|   |____ test_http_scraper.py       # ~50 tests
|   |____ test_browser_scraper.py    # ~40 tests
|   |____ test_selector_engine.py    # ~60 tests
|   |____ test_html_extractor.py     # ~40 tests
|   |____ test_normalizer.py         # ~30 tests
|   |____ test_session_manager.py    # ~40 tests
|   |____ test_rate_limiter.py       # ~30 tests
|   |____ test_config.py             # ~20 tests
|   |____ test_archiver.py           # ~25 tests
|   |____ scrapers/
|   |   |____ __init__.py
|   |   |____ test_x_twitter.py      # ~60 tests
|   |   |____ test_instagram.py      # ~60 tests
|   |   |____ test_tiktok.py         # ~50 tests
|   |   |____ test_linkedin.py       # ~50 tests
|   |   |____ test_facebook.py       # ~40 tests
|   |   |____ test_youtube.py        # ~40 tests
|   |   |____ test_generic_web.py    # ~40 tests
|   |____ plugins/
|   |   |____ test_plugin_loader.py  # ~25 tests
|   |   |____ test_base_scraper.py   # ~20 tests
|   |____ processing/
|   |   |____ test_ai_assistant.py   # ~30 tests
|   |____ cli/
|   |   |____ test_scrape_command.py # ~30 tests
|   |   |____ test_batch_command.py  # ~25 tests
|   |   |____ test_login_command.py  # ~20 tests
|   |   |____ test_health_command.py # ~15 tests
|
|____ integration/                   # Integration tests (20%)
|   |____ __init__.py
|   |____ conftest.py
|   |____ test_http_to_extractor.py  # HTTP scraper + HTML extractor
|   |____ test_browser_to_extractor.py  # Browser scraper + extractor
|   |____ test_selector_to_normalizer.py
|   |____ test_pipeline_full.py      # Full pipeline integration
|   |____ test_plugin_integration.py # Plugin load + scrape
|   |____ test_session_to_scraper.py # Auth session + scrape
|   |____ test_rate_limit_http.py    # Rate limiting with real delays
|   |____ test_archive_pipeline.py   # Full scrape + archive flow
|
|____ e2e/                           # End-to-end tests (10%)
|   |____ __init__.py
|   |____ conftest.py
|   |____ test_happy_path.py         # Basic scrape flows
|   |____ test_fallback_chain.py     # Selector failure + fallback
|   |____ test_layout_change.py      # Simulated page layout change
|   |____ test_batch_scraping.py     # Concurrent batch operations
|   |____ test_auth_flow.py          # Login + scrape flow
|   |____ test_cli_workflows.py      # CLI command workflows
```

### 3.3 HTML Fixture Standards

HTML fixtures are real HTML snapshots saved from target platforms. They are the foundation of scraping tests.

**Creating Fixtures:**
```bash
# Save HTML snapshot for fixture creation
curl -s -A "PhoenixEngine/1.0" https://x.com/user/status/123 > tests/fixtures/html/x_twitter/tweet_v1.html

# Or use the engine itself
phoenix scrape "https://x.com/user/status/123" --strategy http --no-archive > /dev/null
# Raw HTML will be in the archive directory
```

**Fixture Requirements:**
- Minimum 3 fixtures per platform: post, profile, error page
- Fixtures must be sanitized: remove personal info, replace real usernames with test values
- Include both old and new layout versions for change-testing
- Store metadata alongside HTML: URL, date captured, platform version

**Fixture Metadata Format:**
```yaml
# tests/fixtures/html/x_twitter/tweet_v1.meta.yaml
url: "https://x.com/testuser/status/1234567890"
captured_at: "2025-01-15T10:30:00Z"
platform_version: "2025.01.14"
html_size_bytes: 45230
strategy: "http"
status_code: 200
selectors_validated: true
notes: "Standard tweet layout, all selectors match"
```

### 3.4 Mocking HTTP Responses

All HTTP requests in tests must be mocked using `respx` (for httpx):

```python
# test_http_scraper.py
import respx
from httpx import Response

@respx.mock
def test_http_scraper_success():
    """HTTPScraper fetches and parses HTML successfully."""
    # Arrange: Mock HTTP response with HTML fixture
    html_fixture = load_fixture("html/x_twitter/tweet_v1.html")
    route = respx.get("https://x.com/testuser/status/123").mock(
        return_value=Response(200, text=html_fixture)
    )

    # Act: Scrape
    scraper = HTTPScraper(http_client=get_test_client(), rate_limiter=mock_limiter())
    result = await scraper.fetch("https://x.com/testuser/status/123")

    # Assert
    assert result.status_code == 200
    assert result.soup is not None
    assert route.called

@respx.mock
def test_http_scraper_rate_limited():
    """HTTPScraper handles 429 rate limit response."""
    respx.get("https://x.com/testuser/status/123").mock(
        return_value=Response(429, headers={"Retry-After": "60"})
    )

    with pytest.raises(RateLimitedError) as exc_info:
        await scraper.fetch("https://x.com/testuser/status/123")

    assert exc_info.value.code == "SCR_041"
```

### 3.5 Selector Testing Pattern

Every selector in every selector set must be tested against HTML fixtures:

```python
# test_x_twitter_selectors.py
import pytest
from bs4 import BeautifulSoup
from phoenix.scrapers.x_twitter.selectors import X_TWITTER_SELECTORS
from phoenix.scrapers.selectors import SelectorEngine

class TestXTwitterSelectors:
    """Test X/Twitter selector set against HTML fixtures."""

    @pytest.fixture
    def engine(self) -> SelectorEngine:
        engine = SelectorEngine()
        engine.register_selectors("x_twitter", X_TWITTER_SELECTORS)
        return engine

    @pytest.fixture
    def tweet_soup(self) -> BeautifulSoup:
        html = load_fixture("html/x_twitter/tweet_v1.html")
        return BeautifulSoup(html, "lxml")

    def test_tweet_text_primary_selector(self, engine: SelectorEngine, tweet_soup: BeautifulSoup):
        """Primary selector for tweet_text matches."""
        result = engine.extract(tweet_soup, "x_twitter", "tweet_text")
        assert result.matched is True
        assert result.selector_type == "css_primary"
        assert result.value is not None
        assert len(result.value) > 0

    def test_tweet_text_fallback_chain(self, engine: SelectorEngine, tweet_soup: BeautifulSoup):
        """If primary fails, fallback selectors are tried."""
        # This test validates the fallback chain is ordered correctly
        selectors = X_TWITTER_SELECTORS.selectors["tweet_text"]
        assert len(selectors.fallbacks) >= 2, "Must have at least 2 fallback selectors"

    def test_timestamp_attribute_extraction(self, engine: SelectorEngine, tweet_soup: BeautifulSoup):
        """Timestamp is extracted from datetime attribute, not text."""
        result = engine.extract(tweet_soup, "x_twitter", "timestamp")
        assert result.matched is True
        assert result.value is not None
        # Should be a valid ISO datetime
        assert "T" in result.value or "+" in result.value

    def test_all_critical_fields_extracted(self, engine: SelectorEngine, tweet_soup: BeautifulSoup):
        """All critical fields must be successfully extracted."""
        results = engine.extract_all(tweet_soup, "x_twitter")

        for field in X_TWITTER_SELECTORS.critical_fields:
            assert results[field].matched is True, (
                f"Critical field '{field}' not extracted. "
                f"Selector tried: {results[field].selector_used}"
            )

    def test_engagement_metrics_numeric(self, engine: SelectorEngine, tweet_soup: BeautifulSoup):
        """Engagement metrics are extracted as numeric strings."""
        results = engine.extract_all(tweet_soup, "x_twitter")

        for field in ["likes", "shares", "comments"]:
            if results[field].matched and results[field].value:
                # Should be parseable as a number (may have K, M suffix)
                value = results[field].value.replace("K", "").replace("M", "").replace(",", "")
                assert value.replace(".", "").isdigit(), f"{field} value '{results[field].value}' is not numeric"
```

### 3.6 Testing Against Layout Changes

Simulate page layout changes to verify fallback chains work:

```python
def test_layout_change_fallback(self, engine: SelectorEngine):
    """When primary selector fails, fallback selectors match on new layout."""
    # Load HTML with different layout version
    new_layout_html = load_fixture("html/x_twitter/tweet_v2.html")
    soup = BeautifulSoup(new_layout_html, "lxml")

    # Primary selector may fail on new layout
    results = engine.extract_all(soup, "x_twitter")

    # But critical fields should still be extracted via fallbacks
    for field in X_TWITTER_SELECTORS.critical_fields:
        assert results[field].matched is True, (
            f"Critical field '{field}' not extracted after layout change. "
            f"May need selector update."
        )
```

### 3.7 Playwright Browser Testing

Browser scraper tests use a local test server to serve HTML fixtures:

```python
# test_browser_scraper.py
import pytest
from playwright.async_api import async_playwright

@pytest.fixture(scope="session")
async def test_server() -> TestHTTPServer:
    """Local HTTP server for serving test HTML fixtures."""
    server = TestHTTPServer(port=8765)
    server.add_route("/tweet", load_fixture("html/x_twitter/tweet_v1.html"))
    server.start()
    yield server
    server.stop()

async def test_browser_renders_js_content(test_server: TestHTTPServer):
    """Browser scraper renders JavaScript and extracts dynamic content."""
    scraper = BrowserScraper(browser_pool=mock_pool(), rate_limiter=mock_limiter())

    result = await scraper.fetch(
        f"{test_server.url}/tweet",
        options=ScrapingOptions(wait_for="article[data-testid='tweet']"),
    )

    assert result.soup is not None
    # Verify JS-rendered content is present
    assert result.soup.select_one("article[data-testid='tweet']") is not None
```

### 3.8 Test Coverage Requirements

| Module | Minimum Coverage | Notes |
|--------|-----------------|-------|
| `phoenix.scrapers.http` | 95% | All HTTP paths, errors, retries |
| `phoenix.scrapers.browser` | 90% | Browser pool, page operations |
| `phoenix.scrapers.selectors` | 95% | All selector chain combinations |
| `phoenix.scrapers.x_twitter` | 90% | Selectors, parser, edge cases |
| `phoenix.scrapers.instagram` | 90% | Selectors, parser, auth handling |
| `phoenix.scrapers.tiktok` | 85% | Heavy JS rendering paths |
| `phoenix.scrapers.*` | 85% | All platform scrapers |
| `phoenix.processing.*` | 90% | Extractor, normalizer, AI |
| `phoenix.infrastructure.*` | 85% | Sessions, storage, rate limiting |
| `phoenix.cli` | 80% | All commands and options |
| **Overall** | **>= 85%** | |

---

## 4. Documentation Standards

### 4.1 Google-Style Docstrings

All public modules, classes, methods, and functions must have docstrings in Google format:

```python
def extract_all(
    self,
    soup: BeautifulSoup,
    platform: str,
) -> dict[str, SelectorResult]:
    """Extract all registered fields for a platform from parsed HTML.

    Iterates through all fields defined in the platform's SelectorSet
    and attempts extraction using the registered CSS selector chains
    and XPath fallbacks.

    Args:
        soup: Parsed BeautifulSoup tree representing the HTML document.
        platform: Platform identifier string (e.g., "x_twitter", "instagram").

    Returns:
        Dictionary mapping field names to their SelectorResult objects.
        Each result indicates whether extraction succeeded and which
        selector was used.

    Raises:
        KeyError: If no selectors are registered for the given platform.

    Example:
        >>> results = engine.extract_all(soup, "x_twitter")
        >>> results["tweet_text"].value
        'This is the tweet content'
        >>> results["tweet_text"].selector_used
        'article[data-testid="tweet"] div[lang]'
    """
```

### 4.2 Module Docstrings

Every module must have a docstring at the top:

```python
"""X/Twitter platform scraper for Phoenix Engine.

Extracts tweet content, engagement metrics, and metadata from
X/Twitter pages using CSS selectors and XPath fallbacks.

All data is extracted from raw HTML -- no official X API is used.

Selectors:
    Tweet text: article[data-testid="tweet"] div[lang]
    Author: article a[role="link"][href^="/"] div[dir="ltr"] span
    Timestamp: article[data-testid="tweet"] time[datetime]
    Engagement: button[data-testid="like|reply|retweet"] span

Selector version: 2025.01.15
"""
```

### 4.3 Type Hint Documentation

Complex types should be documented:

```python
def register_selectors(
    self,
    platform: str,
    selectors: SelectorSet,
) -> None:
    """Register a CSS/XPath selector set for a platform.

    Args:
        platform: Platform identifier (e.g., "x_twitter", "instagram").
            Must be lowercase with underscores.
        selectors: Complete selector set containing:
            - CSS selector chains (primary + fallbacks) per field
            - XPath backup expressions
            - Critical field declarations
            - Version information

    Raises:
        ValueError: If selectors are syntactically invalid CSS.
        DuplicatePlatformError: If selectors already registered.
    """
```

### 4.4 README Requirements for Plugins

Every plugin directory must contain a `README.md`:

```markdown
# X/Twitter Scraper Plugin

## Overview
Extracts tweets, profiles, and threads from x.com using HTML scraping.

## Selectors
| Field | Primary Selector | Status |
|-------|-----------------|--------|
| tweet_text | `article[data-testid="tweet"] div[lang]` | Healthy (99%) |
| author | `article a[role="link"] div[dir="ltr"] span` | Healthy (98%) |
| timestamp | `article[data-testid="tweet"] time[datetime]` | Healthy (100%) |

## Supported URLs
- `https://x.com/{user}/status/{id}` -- Single tweet
- `https://x.com/{user}` -- Profile page

## Strategy
- Primary: HTTP (server renders tweet HTML)
- Fallback: Browser (for JS-heavy threads)

## Selector Version
2025.01.15

## Testing
```bash
pytest tests/unit/scrapers/test_x_twitter.py -v
```
```

---

## 5. Plugin Development Guide

### 5.1 Creating a New Platform Scraper

This guide walks through creating a scraper plugin for a hypothetical platform.

#### Step 1: Create Plugin Directory Structure

```
phoenix/scrapers/my_platform/
|____ __init__.py              # Export scraper class
|____ scraper.py               # ScraperPlugin implementation
|____ selectors.py             # SelectorSet definition
|____ parser.py                # Platform-specific parsing logic
|____ README.md                # Plugin documentation
```

#### Step 2: Define the Selector Set (`selectors.py`)

```python
"""CSS/XPath selector set for my-platform.com."""

from phoenix.scrapers.selectors import SelectorSet, SelectorChain

MY_PLATFORM_SELECTORS = SelectorSet(
    platform="my_platform",
    version="2025.01.15",  # Update when selectors change
    description="Selectors for my-platform.com articles and profiles",
    selectors={
        "title": SelectorChain(
            field="title",
            primary="h1.article-title",
            fallbacks=[
                "h1",
                "meta[property='og:title']",
                ".post-header h1",
            ],
            attribute=None,  # Extract text content
            transform="strip",
        ),
        "content": SelectorChain(
            field="content",
            primary="div.article-body p",
            fallbacks=[
                "article p",
                "div.content p",
                "main p",
            ],
            transform="strip",
        ),
        "author": SelectorChain(
            field="author",
            primary="span.author-name a",
            fallbacks=[
                "span.author-name",
                ".byline a",
                "meta[name='author']",
            ],
            transform="strip",
        ),
        "publish_date": SelectorChain(
            field="publish_date",
            primary="time[datetime]",
            fallbacks=[
                "meta[property='article:published_time']",
                "meta[name='publishedDate']",
            ],
            attribute="datetime",  # Extract datetime attribute, not text
        ),
        "likes": SelectorChain(
            field="likes",
            primary="button.like-count span",
            fallbacks=[
                ".engagement .likes",
                "span[data-count='likes']",
            ],
            transform="parse_count",  # Handles "1.2K" -> 1200
        ),
    },
    xpath_backups={
        "title": "//h1//text()",
        "content": "//article//p//text()",
        "author": "//span[contains(@class,'author')]//text()",
        "publish_date": "//time/@datetime",
        "likes": "//button[contains(@class,'like')]//span//text()",
    },
    critical_fields=["title", "content"],  # Must extract these for success
)
```

**Selector Design Rules:**
1. **Always include fallbacks:** Minimum 2 fallbacks per critical field
2. **Prefer stable attributes:** Use `data-testid`, `role`, semantic HTML over classes
3. **Avoid overly specific selectors:** `'article div[lang]'` not `'article > div > div > span > div[lang]'`
4. **XPath backups:** Always provide XPath for critical fields
5. **Version your selectors:** Use ISO date format for selector_version

#### Step 3: Implement the Scraper (`scraper.py`)

```python
"""My Platform scraper implementation."""

import re
from phoenix.scrapers.base import ScraperPlugin
from phoenix.scrapers.selectors import SelectorEngine
from phoenix.models import (
    HTMLDocument,
    PlatformData,
    PluginManifest,
    ScrapingStrategy,
)
from phoenix.scrapers.my_platform.selectors import MY_PLATFORM_SELECTORS


class MyPlatformScraper(ScraperPlugin):
    """Scraper for my-platform.com articles and user profiles.

    Extracts article content, author information, and engagement
    metrics from raw HTML. No official API is used.
    """

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="my_platform",
            version="1.0.0",
            description="Scraper for my-platform.com",
            author="developer@example.com",
            url_patterns=[
                r"https?://(www\.)?my-platform\.com/article/[^/]+",
                r"https?://(www\.)?my-platform\.com/user/[^/]+",
            ],
            primary_strategy=ScrapingStrategy.HTTP,
            selector_version="2025.01.15",
            requires_auth=False,
        )

    def supported_patterns(self) -> list[re.Pattern]:
        return [re.compile(p) for p in self.manifest.url_patterns]

    def get_selectors(self) -> SelectorSet:
        return MY_PLATFORM_SELECTORS

    async def parse(
        self,
        html_doc: HTMLDocument,
        selector_engine: SelectorEngine,
    ) -> PlatformData:
        """Parse HTML and extract structured data."""
        # Extract all fields using the selector engine
        results = selector_engine.extract_all(html_doc.soup, "my_platform")

        # Platform-specific post-processing
        # Join multiple paragraphs for content
        content_parts = []
        if results["content"].value:
            # Content selector may match multiple <p> elements
            content_elements = html_doc.soup.select(
                MY_PLATFORM_SELECTORS.selectors["content"].primary
            )
            content_parts = [el.get_text(strip=True) for el in content_elements]

        return PlatformData(
            platform="my_platform",
            extraction_confidence=self._calculate_confidence(results),
            raw_fields={
                "title": results["title"].value,
                "content": "\n\n".join(content_parts) if content_parts else results["content"].value,
                "author": results["author"].value,
                "publish_date": results["publish_date"].value,
                "likes": results["likes"].value,
            },
            selector_results=results,
            metadata={
                "url": html_doc.url,
                "strategy": html_doc.strategy,
                "html_size": len(html_doc.raw_html),
            },
        )

    def _calculate_confidence(
        self,
        results: dict[str, SelectorResult],
    ) -> float:
        """Calculate extraction confidence based on selector match rates."""
        critical = MY_PLATFORM_SELECTORS.critical_fields
        matched_critical = sum(
            1 for f in critical if results.get(f) and results[f].matched
        )
        return matched_critical / len(critical) if critical else 1.0
```

#### Step 4: Create `__init__.py`

```python
"""My Platform scraper plugin."""

from phoenix.scrapers.my_platform.scraper import MyPlatformScraper

__all__ = ["MyPlatformScraper"]
```

#### Step 5: Write Tests

```python
# tests/unit/scrapers/test_my_platform.py
import pytest
from bs4 import BeautifulSoup
from phoenix.scrapers.my_platform import MyPlatformScraper
from phoenix.scrapers.my_platform.selectors import MY_PLATFORM_SELECTORS
from phoenix.scrapers.selectors import SelectorEngine

class TestMyPlatformScraper:
    @pytest.fixture
    def scraper(self) -> MyPlatformScraper:
        return MyPlatformScraper()

    @pytest.fixture
    def engine(self) -> SelectorEngine:
        engine = SelectorEngine()
        engine.register_selectors("my_platform", MY_PLATFORM_SELECTORS)
        return engine

    @pytest.fixture
    def article_html(self) -> str:
        return """
        <html><body>
            <article>
                <h1 class="article-title">Test Article Title</h1>
                <span class="author-name"><a href="/author/jane">Jane Doe</a></span>
                <time datetime="2025-01-15T10:30:00Z">Jan 15, 2025</time>
                <div class="article-body">
                    <p>First paragraph of content.</p>
                    <p>Second paragraph with more detail.</p>
                </div>
                <button class="like-count"><span>42</span></button>
            </article>
        </body></html>
        """

    def test_manifest(self, scraper: MyPlatformScraper):
        assert scraper.manifest.name == "my_platform"
        assert scraper.manifest.primary_strategy == ScrapingStrategy.HTTP

    def test_url_patterns(self, scraper: MyPlatformScraper):
        patterns = scraper.supported_patterns()
        assert any(p.match("https://my-platform.com/article/test-123") for p in patterns)
        assert any(p.match("https://www.my-platform.com/article/another") for p in patterns)
        assert not any(p.match("https://other-site.com/article/test") for p in patterns)

    async def test_parse_extracts_all_fields(
        self,
        scraper: MyPlatformScraper,
        engine: SelectorEngine,
        article_html: str,
    ):
        soup = BeautifulSoup(article_html, "lxml")
        html_doc = HTMLDocument(
            url="https://my-platform.com/article/test",
            status_code=200,
            raw_html=article_html,
            soup=soup,
            strategy=ScrapingStrategy.HTTP,
        )

        result = await scraper.parse(html_doc, engine)

        assert result.raw_fields["title"] == "Test Article Title"
        assert result.raw_fields["author"] == "Jane Doe"
        assert result.raw_fields["publish_date"] == "2025-01-15T10:30:00Z"
        assert "First paragraph" in result.raw_fields["content"]
        assert "Second paragraph" in result.raw_fields["content"]
        assert result.raw_fields["likes"] == "42"
        assert result.extraction_confidence == 1.0

    def test_critical_fields_defined(self):
        assert len(MY_PLATFORM_SELECTORS.critical_fields) > 0
        assert "title" in MY_PLATFORM_SELECTORS.critical_fields
```

### 5.2 Selector Set Update Workflow

When a platform changes its HTML layout:

1. **Detect:** Health check shows degraded selector match rates
2. **Capture:** Save new HTML snapshot as fixture
3. **Analyze:** Run `phoenix selectors <platform>` to see failures
4. **Update:** Modify selector set with new selectors
5. **Test:** Run selector tests against new fixture
6. **Fallback:** Add old selectors as fallbacks (for gradual rollout)
7. **Version:** Update selector_version in SelectorSet
8. **Document:** Update README.md with new selector info
9. **Commit:** `selector(x-twitter): update selectors for layout change v2025.02.01`

### 5.3 Plugin Registration Checklist

- [ ] Plugin implements `ScraperPlugin` ABC
- [ ] All abstract methods implemented
- [ ] SelectorSet has >= 2 fallbacks per critical field
- [ ] XPath backups provided for all critical fields
- [ ] URL patterns are specific (don't over-match)
- [ ] README.md documents selectors and URLs
- [ ] Unit tests cover all selectors against fixtures
- [ ] Tests cover fallback chain behavior
- [ ] No official API clients imported
- [ ] mypy --strict passes
- [ ] ruff check passes
- [ ] black formatting applied

---


## 6. AI Agent Coding Prompts

### 6.1 Prompt: Implement a New Platform Scraper

```
You are implementing a new platform scraper for Phoenix Engine, a pure web scraping platform.

CONTEXT:
- Phoenix Engine scrapes ONLY from raw HTML -- NO official APIs are ever used
- Each platform has a ScraperPlugin that registers URL patterns and CSS/XPath selectors
- The SelectorEngine applies selector chains (primary + fallbacks) to extract data
- All HTML is parsed with BeautifulSoup4 or lxml

TASK:
Implement a scraper plugin for {PLATFORM_NAME}.

REQUIREMENTS:
1. Create directory: phoenix/scrapers/{platform_name}/
2. Implement scraper.py with a class extending ScraperPlugin
3. Define selectors.py with a SelectorSet containing:
   - Primary CSS selector for each field
   - At least 2 fallback selectors per critical field
   - XPath backups for critical fields
   - Version string (current date in ISO format)
4. URL patterns must match:
   {URL_PATTERN_EXAMPLES}
5. Fields to extract:
   {FIELD_LIST}
6. Critical fields: {CRITICAL_FIELDS}
7. Primary strategy: {STRATEGY} (HTTP or Browser)

CONSTRAINTS:
- NO API clients (no instagrapi, tweepy, etc.)
- Use only BeautifulSoup4, lxml, cssselect for HTML parsing
- All selectors must be tested with HTML fixtures
- Include proper error handling for missing fields
- Follow Google-style docstrings
- Use type hints everywhere

DELIVERABLES:
- phoenix/scrapers/{platform}/__init__.py
- phoenix/scrapers/{platform}/scraper.py
- phoenix/scrapers/{platform}/selectors.py
- phoenix/scrapers/{platform}/parser.py (if needed)
- phoenix/scrapers/{platform}/README.md
- tests/unit/scrapers/test_{platform}.py (comprehensive tests)
- tests/fixtures/html/{platform}/ (sample HTML fixtures)

REFERENCE:
Look at existing scrapers in phoenix/scrapers/x_twitter/ as a model.
```

### 6.2 Prompt: Update Selectors After Layout Change

```
You are updating CSS selectors for Phoenix Engine after a platform layout change.

CONTEXT:
- The platform {PLATFORM} changed their HTML structure
- Current selector version: {CURRENT_VERSION}
- Health check shows these selectors failing: {FAILED_SELECTORS}

TASK:
Update the selector set in phoenix/scrapers/{platform}/selectors.py

REQUIREMENTS:
1. Update primary selectors that are failing
2. Add old working selectors to the fallback chain (don't remove them)
3. Update selector_version to today's date
4. Ensure all critical fields still have working selectors
5. Add any new fields that are now available on the page

PROCESS:
1. Read the current selector set
2. Read sample HTML fixtures (old and new layout)
3. Identify the new DOM structure
4. Write new selectors targeting the new structure
5. Test selectors against the new HTML fixture
6. Move old primary selectors to fallback positions

CONSTRAINTS:
- Prefer stable attributes (data-testid, role, semantic HTML) over CSS classes
- Keep fallback chains -- never remove old selectors entirely
- XPath backups must still work
- Update version string

DELIVERABLES:
- Updated selectors.py with new selector set
- Updated tests with new HTML fixture
- README.md updated with new selector documentation
```

### 6.3 Prompt: Implement HTML Extraction Feature

```
You are implementing a core HTML extraction feature for Phoenix Engine.

CONTEXT:
- Phoenix Engine is a pure web scraping platform using CSS selectors and XPath
- The SelectorEngine manages selector sets and executes extraction with fallback chains
- HTML is parsed with BeautifulSoup4

TASK:
Implement {FEATURE_NAME} in the HTML extraction pipeline.

REQUIREMENTS:
{FEATURE_REQUIREMENTS}

TECHNOLOGY:
- beautifulsoup4 for HTML parsing
- cssselect for CSS-to-XPath translation
- lxml for fast XPath evaluation
- Pydantic for data models
- pytest for testing with HTML fixtures

CONSTRAINTS:
- All functions must be fully typed
- Google-style docstrings required
- No official API usage
- HTML fixtures required for all tests
- Handle edge cases (empty HTML, missing elements, malformed HTML)

DELIVERABLES:
- Implementation file(s)
- Unit tests with HTML fixtures
- Documentation updates
```

### 6.4 Prompt: Debug Failing Scraper

```
You are debugging a failing scraper in Phoenix Engine.

CONTEXT:
- The {PLATFORM} scraper is failing with error: {ERROR_CODE}
- Last successful scrape: {LAST_SUCCESS_DATE}
- Error details: {ERROR_DETAILS}

DIAGNOSTIC PROCESS:
1. Read the current selector set from phoenix/scrapers/{platform}/selectors.py
2. Read the test fixtures and current tests
3. Analyze the error to determine root cause:
   - SCR_030 (SelectorNotFound): Page layout changed
   - SCR_040 (Blocked): IP/rate limiting
   - SCR_020 (BrowserError): Browser automation issue
   - SCR_031 (CriticalFieldsMissing): Selectors match but wrong elements

4. Based on root cause:
   - Layout change: Update selectors, add new HTML fixture
   - Blocked: Check User-Agent, add delay, verify robots.txt
   - Browser: Check Playwright version, update wait strategy
   - Fields missing: Debug selector target, check element visibility

5. Write a regression test that would have caught this issue

DELIVERABLES:
- Root cause analysis
- Fix implementation
- Regression test
- Updated documentation if needed
```

### 6.5 Prompt: Code Review Checklist

```
Review this Phoenix Engine scraping code against the following standards:

SCRAPING-SPECIFIC CHECKS:
[ ] No official API clients imported (instagrapi, tweepy, etc.)
[ ] CSS selectors have fallback chains (min 2 fallbacks for critical fields)
[ ] XPath backups provided for critical fields
[ ] SelectorEngine used for all extraction (no inline soup.select_one())
[ ] Selectors are versioned with ISO date
[ ] HTML fixtures exist for all selector tests
[ ] Tests verify fallback chain behavior
[ ] Tests simulate layout changes

CODE QUALITY:
[ ] Black formatting applied
[ ] Ruff passes with no errors
[ ] mypy --strict passes
[ ] Google-style docstrings on all public items
[ ] Type hints on all parameters and returns
[ ] No bare except clauses
[ ] Proper error handling with custom exceptions
[ ] Async/await used correctly

ARCHITECTURE:
[ ] ScraperPlugin ABC properly implemented
[ ] SelectorSet registered with SelectorEngine
[ ] URL patterns are specific enough
[ ] Critical fields declared
[ ] Error handling for missing fields
[ ] No hardcoded values (use constants/config)
[ ] Ollama AI fallback configured for critical extraction paths

TESTING:
[ ] Unit tests for all selectors
[ ] Tests for happy path and error cases
[ ] HTML fixtures from real pages (sanitized)
[ ] Mock HTTP responses (no live network calls)
[ ] Coverage > 85% for new code
[ ] Ollama extraction path tested with mocked Ollama responses
```

### 6.6 Prompt: Ollama Integration

```
You are implementing a feature that uses Ollama for local AI inference.
Ollama runs at http://localhost:11434.
Primary model: qwen2.5:7b.
Use httpx for HTTP requests to the Ollama API.
Handle cases where Ollama is not running or model is not pulled.

CONTEXT:
- Phoenix Engine uses Ollama as the final fallback in the selector extraction chain
- Ollama is a local AI server running at http://localhost:11434
- Primary model: qwen2.5:7b (128K context, structured output, Apache 2.0)
- Fallback model: qwen2.5:7b (for smaller pages, faster inference)
- Enterprise model: qwen2.5-coder:32b (for maximum accuracy)
- Alternative: deepseek-coder-v2:16b (if qwen unavailable)
- All Ollama interactions go through the OllamaClient class (httpx-based)
- No API keys needed -- Ollama runs locally without authentication

REQUIREMENTS:
1. Use httpx for direct HTTP to Ollama REST API:
   - base_url: "http://localhost:11434"
   - endpoints: /api/generate, /api/chat, /api/tags, /api/pull
   - timeout: configurable (default 120s for local inference)

2. Implement proper error handling:
   - OllamaNotRunningError: Ollama not started -- prompt to run `ollama serve`
   - OllamaModelNotFoundError: model not pulled -- auto-pull or suggest `ollama pull`
   - OllamaOutOfMemoryError: GPU/CPU OOM -- try smaller model (32b -> 14b -> 7b)
   - OllamaTimeoutError: local inference slow -- increase timeout or reduce context
   - JSON parse errors: attempt markdown stripping, then fail gracefully

3. Include inference metrics tracking:
   - Track inference_time_ms per request
   - Track gpu_memory_mb usage (via hardware monitor)
   - Track model_used for each extraction
   - Expose metrics via OllamaClient.inference_stats

4. Cache responses:
   - LRU cache with TTL (default 3600 seconds)
   - Cache key: SHA256 of HTML hash + schema hash
   - Only cache successful extractions
   - Use local disk or memory (no Redis needed)

5. HTML chunking for large pages:
   - Split HTML at tag boundaries when exceeding context limits
   - Target context: ~16K tokens for qwen2.5-coder (48000 chars at ~3 chars/token)
   - Send most relevant chunk first (body content over head/scripts)
   - Track chunk index for multi-chunk strategies

6. Model selection logic:
   - qwen2.5:7b: simple tasks (classification, short queries), low VRAM
   - qwen2.5:7b: standard extraction, selector repair (DEFAULT)
   - qwen2.5-coder:32b: large pages, complex extraction, maximum accuracy
   - deepseek-coder-v2:16b: alternative when qwen unavailable

CONSTRAINTS:
- No OpenAI SDK -- use httpx directly
- No API keys or authentication needed
- Set reasonable num_ctx limits to prevent OOM
- Implement per-request VRAM checking via HardwareMonitor
- Log all inference calls with timing for performance monitoring
- Handle Ollama failures gracefully -- Ollama is a fallback, not a hard dependency
- Support CPU-only mode when no GPU is available

DELIVERABLES:
- OllamaClient class with generate(), chat(), list_models(), pull_model()
- Error handling with custom exceptions (OllamaError hierarchy)
- Inference metrics tracking
- Response caching implementation
- Model selection logic
- Hardware-based model fallback
- Unit tests with mocked Ollama responses (mock httpx to localhost:11434)
- Configuration TOML section for ai.ollama settings
```

### 6.7 Prompt: Ollama HTML Extraction

```
You are implementing the HTML extraction feature that sends raw HTML to the local Ollama server
and receives structured JSON data back.

CONTEXT:
- This is the final stage of the selector fallback chain
- HTML arrives here ONLY when all CSS/XPath selectors have failed
- The OllamaClient.generate() method handles the API communication
- Output must be valid JSON matching the expected schema
- Everything runs locally -- no data leaves the machine

TASK:
Implement the extraction prompt builder and response parser for Ollama HTML extraction.

REQUIREMENTS:

1. System prompt (sent as "system" parameter):

SYSTEM_PROMPT = """You are an expert web data extraction engine running locally via Ollama.
Parse the provided HTML and extract structured data according to the schema.
Return ONLY valid JSON. No markdown, no explanation. If a field is not found, use null."""

2. User prompt template (sent as "prompt" parameter):

USER_PROMPT_TEMPLATE = """Extract data from this HTML page.

URL: {url}
Platform: {platform}
Content Type: {content_type}

HTML:
```html
{html_chunk}
```

Extract the following fields as JSON:
{schema_description}

Return ONLY valid JSON. No markdown, no explanation."""

3. Ollama /api/generate call:

```python
import httpx

async def extract_with_ollama(
    html: str,
    context: ExtractionContext,
    ollama_base_url: str = "http://localhost:11434",
    model: str = "qwen2.5:7b",
) -> dict[str, Any]:
    """Extract structured data from HTML using local Ollama.

    Args:
        html: Raw HTML string to extract from.
        context: Extraction context with URL, platform, schema hints.
        ollama_base_url: Ollama server URL.
        model: Ollama model to use.

    Returns:
        Parsed JSON dict with extracted data.

    Raises:
        OllamaNotRunningError: If Ollama is not reachable.
        OllamaModelNotFoundError: If model is not pulled.
        OllamaJSONParseError: If response cannot be parsed.
    """
    # Build the prompt
    system_prompt = (
        "You are an expert web data extraction engine running locally via Ollama. "
        "Parse the provided HTML and extract structured data according to the schema. "
        "Return ONLY valid JSON. No markdown, no explanation. "
        "If a field is not found, use null."
    )

    user_prompt = (
        f"Extract data from this HTML page.\n\n"
        f"URL: {context.url}\n"
        f"Platform: {context.source_platform}\n"
        f"Content Type: {context.content_type_hint}\n\n"
        f"HTML:\n```html\n{html[:40000]}\n```\n\n"  # Truncate to fit context
        f"Extract the following fields as JSON:\n"
        f"{schema_description}\n\n"
        f"Return ONLY valid JSON. No markdown, no explanation."
    )

    # Call Ollama /api/generate
    try:
        response = await httpx.AsyncClient(timeout=120.0).post(
            f"{ollama_base_url}/api/generate",
            json={
                "model": model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_ctx": 16384,
                    "num_predict": 4096,
                },
            },
        )
        response.raise_for_status()
    except httpx.ConnectError:
        raise OllamaNotRunningError(ollama_base_url)
    except httpx.TimeoutException:
        raise OllamaTimeoutError(120.0, model)

    result = response.json()
    raw_response = result.get("response", "")

    # Parse JSON from response
    return parse_extraction_response(raw_response)
```

4. Response parser with markdown stripping:

```python
def parse_extraction_response(raw_content: str) -> dict[str, Any]:
    """Parse Ollama response, handling markdown code fences.

    Ollama may wrap JSON in markdown code blocks. This function
    strips them and returns parsed JSON.

    Args:
        raw_content: Raw string content from Ollama response.

    Returns:
        Parsed JSON dict.

    Raises:
        OllamaJSONParseError: If content cannot be parsed as JSON.
    """
    content = raw_content.strip()

    # Strip markdown code fences
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Last resort: try to extract JSON from the response
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            try:
                return json.loads(content[json_start:json_end])
            except json.JSONDecodeError:
                pass
        raise OllamaJSONParseError(
            f"Failed to parse Ollama response as JSON: {e}\n"
            f"Response preview: {content[:200]}"
        )
```

5. Schema description generator:

```python
def generate_schema_description(fields: list[dict[str, Any]]) -> str:
    """Generate a human-readable schema description for the prompt.

    Args:
        fields: List of field dicts with 'name', 'type', 'description' keys.

    Returns:
        Formatted schema description string for the prompt.
    """
    lines = []
    for field in fields:
        line = f'- "{field["name"]}" ({field["type"]})'
        if field.get("description"):
            line += f': {field["description"]}'
        if field.get("example"):
            line += f' Example: {field["example"]}'
        lines.append(line)
    return "\n".join(lines)
```

CONSTRAINTS:
- HTML must be chunked before sending (max ~48K chars per request)
- Always include URL, platform, and content type for context
- Schema description must be clear and unambiguous
- Response parser must handle markdown-wrapped JSON
- Never return partial JSON -- either full valid JSON or raise error
- Handle Ollama not running gracefully
- Track inference_time_ms and model_used in result

DELIVERABLES:
- Prompt builder function
- Response parser with markdown stripping
- Schema description generator
- Unit tests with mock Ollama responses (including markdown-wrapped)
- Integration test with real HTML fixture
- Mock Ollama server for testing (httpx mock to localhost:11434)
```

### 6.8 Prompt: Ollama Selector Repair

```
You are implementing the selector repair feature that uses Ollama to suggest
new CSS selectors when a platform changes its HTML layout.

CONTEXT:
- Platforms periodically change their HTML structure
- When selectors fail, Ollama can analyze the new HTML and suggest updated selectors
- This reduces manual selector maintenance time significantly
- Suggested selectors must still follow Phoenix Engine standards (fallbacks, XPath backups)
- Everything runs locally via Ollama

TASK:
Implement the selector repair prompt and parser that sends old selectors + new HTML
to Ollama and receives updated selector suggestions.

REQUIREMENTS:

1. Selector repair prompt template:

SELECTOR_REPAIR_PROMPT = """The following CSS selectors no longer match the HTML (the page layout changed).

Old selectors: {old_selectors}

Current HTML structure:
```html
{html_sample}
```

Suggest new CSS selectors that extract the same data.
Return as JSON array: [{"field": "name", "old": "...", "new": "...", "confidence": 0.95}]"""

2. Implementation:

```python
async def repair_selectors(
    self,
    html_sample: str,
    old_selectors: dict[str, str],
    platform: str,
) -> list[dict[str, Any]]:
    """Use Ollama to suggest new selectors after layout change.

    Sends old selectors + new HTML sample to Ollama and parses
    the suggested replacements with confidence scores.

    Args:
        html_sample: Representative HTML from the new layout.
        old_selectors: Dict mapping field names to old selector strings.
        platform: Platform identifier for context.

    Returns:
        List of suggestion dicts with keys:
        - field: Field name
        - old: Old selector that failed
        - new: Suggested new selector
        - confidence: Float 0.0-1.0 indicating confidence

    Raises:
        OllamaError: If inference fails.
        OllamaJSONParseError: If response cannot be parsed.
    """
    prompt = (
        "The following CSS selectors no longer match the HTML "
        "(the page layout changed).\n\n"
        f"Platform: {platform}\n\n"
        f"Old selectors: {json.dumps(old_selectors, indent=2)}\n\n"
        "Current HTML structure:\n```html\n"
        f"{html_sample[:8000]}\n"  # Truncate to stay within context limits
        "```\n\n"
        "Suggest new CSS selectors that extract the same data. "
        "Prefer stable attributes (data-testid, role, semantic HTML) "
        "over CSS classes. "
        'Return as JSON array: [{"field": "name", "old": "...", '
        '"new": "...", "confidence": 0.95}]'
    )

    system_prompt = (
        "You are a CSS selector expert specializing in web scraping. "
        "Suggest precise, robust selectors that will work across minor layout changes. "
        "Always prefer these stability attributes in order: "
        "data-testid > role > semantic HTML (article, main, header) > class. "
        "Avoid overly specific selectors with many child combinators. "
        "Return ONLY a valid JSON array. No markdown, no explanation."
    )

    # Call Ollama via httpx
    response = await httpx.AsyncClient(timeout=120.0).post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 16384},
        },
    )
    result = response.json()
    content = result["response"].strip()

    # Parse JSON array response
    try:
        suggestions = json.loads(content)
    except json.JSONDecodeError:
        # Strip markdown fences if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        suggestions = json.loads(content.strip())

    # Validate suggestion format
    for suggestion in suggestions:
        required_keys = {"field", "old", "new", "confidence"}
        if not required_keys.issubset(suggestion.keys()):
            raise OllamaJSONParseError(
                f"Suggestion missing required keys: {required_keys - suggestion.keys()}"
            )
        if not (0.0 <= suggestion["confidence"] <= 1.0):
            suggestion["confidence"] = max(0.0, min(1.0, suggestion["confidence"]))

    # Sort by confidence (highest first)
    suggestions.sort(key=lambda x: x["confidence"], reverse=True)

    return suggestions
```

3. Selector repair integration workflow:

```python
async def handle_selector_failure(
    engine: SelectorEngine,
    platform: str,
    html_doc: HTMLDocument,
    ollama: OllamaClient,
) -> SelectorSet:
    """Handle selector failure by attempting AI-powered repair.

    This is the intelligent fallback path when selectors fail.
    It uses Ollama to analyze the new HTML and suggest updated selectors.

    Args:
        engine: SelectorEngine with current (failing) selector set.
        platform: Platform identifier.
        html_doc: HTML document that selectors failed against.
        ollama: OllamaClient instance for local inference.

    Returns:
        Updated SelectorSet with repaired selectors.
    """
    # Get current (failing) selectors
    current_set = engine.get_selector_set(platform)
    old_selectors = {
        field: chain.primary
        for field, chain in current_set.selectors.items()
    }

    # Get HTML sample (body only, truncated)
    body_html = html_doc.soup.body.decode_contents() if html_doc.soup.body else html_doc.raw_html
    sample = body_html[:8000]  # Context-safe sample

    # Call Ollama for selector suggestions
    suggestions = await repair_selectors(sample, old_selectors, platform)

    # Apply high-confidence suggestions (confidence >= 0.8)
    updated_selectors = dict(current_set.selectors)
    for suggestion in suggestions:
        if suggestion["confidence"] >= 0.8:
            field = suggestion["field"]
            if field in updated_selectors:
                old_primary = updated_selectors[field].primary
                updated_selectors[field] = SelectorChain(
                    field=field,
                    primary=suggestion["new"],
                    fallbacks=[old_primary] + updated_selectors[field].fallbacks,
                    attribute=updated_selectors[field].attribute,
                    transform=updated_selectors[field].transform,
                )

    # Create updated selector set
    new_set = SelectorSet(
        platform=current_set.platform,
        version=datetime.now().strftime("%Y.%m.%d"),
        description=f"{current_set.description} (AI-repaired)",
        selectors=updated_selectors,
        xpath_backups=current_set.xpath_backups,
        critical_fields=current_set.critical_fields,
    )

    return new_set
```

CONSTRAINTS:
- Only apply suggestions with confidence >= 0.8
- Always keep old selectors in the fallback chain
- Truncate HTML to 8000 chars to stay within context limits
- Validate all suggestions have required fields
- Sort suggestions by confidence before applying
- Update selector version after repair
- Log all repairs for auditing
- Handle Ollama not running gracefully (return original selectors)

DELIVERABLES:
- repair_selectors() function using Ollama
- handle_selector_failure() integration function
- Suggestion validation and confidence filtering
- Unit tests with mock selector repair responses
- Integration test with layout-changed HTML fixture
```

### 6.9 Prompt: Ollama Model Management

```
You are implementing model management for Ollama integration in Phoenix Engine.
Ollama models must be tracked, pulled on demand, and selected based on hardware.

MODEL MANAGEMENT REQUIREMENTS:

1. Check Ollama installation and status:

```python
import httpx

async def check_ollama_status(base_url: str = "http://localhost:11434") -> dict[str, Any]:
    """Check if Ollama is installed and running.

    Args:
        base_url: Ollama server URL.

    Returns:
        Dict with status, version, and available models.

    Raises:
        OllamaNotRunningError: If Ollama is not reachable.
    """
    try:
        response = await httpx.AsyncClient(timeout=5.0).get(f"{base_url}/api/tags")
        response.raise_for_status()
        data = response.json()
        return {
            "running": True,
            "models": [m["name"] for m in data.get("models", [])],
            "model_count": len(data.get("models", [])),
        }
    except httpx.ConnectError:
        return {
            "running": False,
            "models": [],
            "model_count": 0,
            "suggestion": "Install Ollama: curl -fsSL https://ollama.com/install.sh | sh",
        }
```

2. Pull models on demand:

```python
async def ensure_model_pulled(
    model_name: str,
    base_url: str = "http://localhost:11434",
) -> bool:
    """Ensure a model is pulled and ready.

    Args:
        model_name: Model to check/pull (e.g., "qwen2.5:7b").
        base_url: Ollama server URL.

    Returns:
        True if model is available.
    """
    # Check if already pulled
    response = await httpx.AsyncClient(timeout=10.0).get(f"{base_url}/api/tags")
    data = response.json()
    available = [m["name"] for m in data.get("models", [])]

    if model_name in available:
        return True

    # Pull the model
    async with httpx.AsyncClient(timeout=600.0) as client:
        async with client.stream(
            "POST",
            f"{base_url}/api/pull",
            json={"name": model_name, "stream": True},
        ) as response:
            async for line in response.aiter_lines():
                progress = json.loads(line)
                if progress.get("status") == "success":
                    return True
                if "error" in progress:
                    raise OllamaError(f"Failed to pull {model_name}: {progress['error']}")

    return False
```

3. Hardware requirements documentation:

| Model | Parameters | VRAM (GPU) | RAM (CPU) | Best For |
|-------|-----------|------------|-----------|----------|
| qwen2.5:7b | 7B | ~4.5GB | ~6GB | Fast tasks, small HTML |
| qwen2.5:7b | 14B | ~9.0GB | ~12GB | Standard extraction (DEFAULT) |
| qwen2.5-coder:32b | 32B | ~20.0GB | ~24GB | Complex extraction, max accuracy |
| deepseek-coder-v2:16b | 16B | ~10.0GB | ~14GB | Alternative to qwen |

4. Model verification in CI:

```python
# In CI/test environments, mock Ollama or skip
def get_ollama_client_for_environment() -> Optional[OllamaClient]:
    """Get Ollama client based on environment.

    In CI: returns mock client or None (skips AI tests)
    In dev: returns real client pointing to localhost
    """
    if os.environ.get("CI") == "true":
        # Use mock Ollama for CI
        return MockOllamaClient()

    # Try to connect to real Ollama
    try:
        return OllamaClient(base_url="http://localhost:11434")
    except OllamaNotRunningError:
        # Skip AI features if Ollama not available
        return None
```

5. Model selection based on hardware:

```python
def select_model_for_hardware(
    hardware_profile: HardwareProfile,
    task_complexity: str = "standard",
) -> str:
    """Select best model for available hardware.

    Args:
        hardware_profile: GPU/VRAM/RAM information.
        task_complexity: "fast", "standard", or "premium".

    Returns:
        Model name string.
    """
    vram = hardware_profile.vram_available_mb

    if task_complexity == "premium" and vram >= 20000:
        return "qwen2.5-coder:32b"

    if vram >= 9000 or (task_complexity == "standard" and vram >= 4500):
        return "qwen2.5:7b"

    if vram >= 4500 or hardware_profile.ram_available_mb >= 6000:
        return "qwen2.5:7b"

    # CPU fallback
    return "qwen2.5:7b"
```

CONSTRAINTS:
- Always check Ollama is running before operations
- Handle model pull failures gracefully
- Provide clear error messages for hardware constraints
- Support CI/testing with mock Ollama
- Document hardware requirements clearly
- Auto-select models based on available resources

DELIVERABLES:
- Ollama status checker
- Model pull with progress tracking
- Hardware-based model selector
- CI mock configuration
- Hardware requirements documentation
- Unit tests with mocked Ollama responses
```

### 6.10 Prompt: Ollama Error Handling

```
You are implementing comprehensive error handling for all Ollama interactions
in Phoenix Engine. Ollama is a fallback mechanism -- failures must be graceful
and never break the core scraping pipeline.

ERROR HANDLING REQUIREMENTS:

1. Exception hierarchy:

```python
class OllamaError(Exception):
    """Base exception for all Ollama errors."""
    pass

class OllamaExtractionError(OllamaError):
    """Raised when Ollama extraction fails after all retries.

    This is the catch-all for inference failures (OOM, timeouts,
    server errors) after the retry policy has been exhausted.
    """
    pass

class OllamaJSONParseError(OllamaError):
    """Raised when Ollama response cannot be parsed as valid JSON.

    This usually means the model returned markdown, explanatory text,
    or malformed JSON instead of the expected structured output.
    """
    pass

class OllamaNotRunningError(OllamaError):
    """Raised when Ollama server is not running or not reachable."""
    pass

class OllamaModelNotFoundError(OllamaError):
    """Raised when requested model has not been pulled."""
    pass

class OllamaOutOfMemoryError(OllamaError):
    """Raised when GPU or system RAM is exhausted during inference."""
    pass

class OllamaTimeoutError(OllamaError):
    """Raised when local inference exceeds timeout."""
    pass
```

2. Retry logic with model fallback:

```python
import asyncio
import random
import httpx


async def _call_with_retry(
    self,
    prompt: str,
    model: str,
    max_retries: int = 2,
    base_delay: float = 2.0,
) -> dict[str, Any]:
    """Call Ollama with retry and model fallback.

    On OllamaOutOfMemoryError: falls back to smaller model.
    On OllamaTimeoutError: retries with increased timeout.

    Args:
        prompt: Generation prompt.
        model: Model name to use.
        max_retries: Maximum retry attempts.
        base_delay: Initial delay in seconds.

    Returns:
        Ollama API response dict.

    Raises:
        OllamaExtractionError: After all retries exhausted.
    """
    for attempt in range(max_retries):
        try:
            response = await httpx.AsyncClient(timeout=self.timeout).post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_ctx": self.num_ctx},
                },
            )
            return response.json()

        except httpx.TimeoutException:
            # Retry with longer timeout
            if attempt < max_retries - 1:
                self.timeout *= 1.5
                await asyncio.sleep(base_delay)
                continue
            raise OllamaTimeoutError(self.timeout, model)

        except OllamaOutOfMemoryError:
            # Fall back to smaller model
            fallback_model = self._get_smaller_model(model)
            if fallback_model and fallback_model != model:
                model = fallback_model
                continue
            raise  # No smaller model available

        except httpx.ConnectError:
            raise OllamaNotRunningError(self.base_url)

        except Exception as e:
            raise OllamaExtractionError(
                f"Unexpected error calling Ollama: {type(e).__name__}: {e}"
            )


def _get_smaller_model(self, model: str) -> Optional[str]:
    """Get next smaller model for OOM fallback."""
    fallback_chain = {
        "qwen2.5-coder:32b": "qwen2.5:7b",
        "qwen2.5:7b": "qwen2.5:7b",
        "deepseek-coder-v2:16b": "qwen2.5:7b",
    }
    return fallback_chain.get(model)
```

3. Pipeline integration with graceful fallback:

```python
async def extract_with_fallback(
    self,
    html_doc: HTMLDocument,
    platform: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Extract data with full fallback chain including Ollama.

    This is the main extraction entry point that tries selectors first,
    then falls back to Ollama, then to partial extraction.

    Args:
        html_doc: Parsed HTML document.
        platform: Platform identifier.
        schema: Extraction schema defining expected fields.

    Returns:
        Extracted data dict. May contain null values for missing fields.
    """
    # Stage 1: Try CSS/XPath selectors (primary path)
    selector_results = self.selector_engine.extract_all(
        html_doc.soup, platform
    )
    if all(
        selector_results[field].matched
        for field in schema.get("critical_fields", [])
    ):
        return self._selector_results_to_dict(selector_results)

    # Stage 2: Try Ollama (AI-powered local fallback)
    try:
        # Check hardware can handle inference
        if not self.hardware_monitor.can_load_model(self.default_model):
            raise OllamaOutOfMemoryError(self.default_model, 0, 0)

        # Select optimal model based on HTML size and hardware
        model = await self.model_selector.select_model(
            html_doc.raw_html,
            task_type="extraction",
        )

        # Call Ollama
        ollama_result = await self.ollama_client.generate(
            prompt=build_extraction_prompt(html_doc.raw_html, schema),
            model=model,
            options={"temperature": 0.1, "num_ctx": 16384},
        )

        # Parse response
        extracted = parse_extraction_response(ollama_result["response"])

        return extracted

    except (OllamaExtractionError, OllamaJSONParseError,
            OllamaOutOfMemoryError, OllamaNotRunningError) as e:
        # Stage 3: Partial extraction fallback
        # Return whatever selectors managed to extract
        partial = self._selector_results_to_dict(selector_results)
        partial["_extraction_meta"] = {
            "ollama_invoked": True,
            "ollama_error": type(e).__name__,
            "ollama_message": str(e),
            "fallback": "partial_selector_extraction",
        }
        return partial
```

4. Error logging and monitoring:

```python
import structlog

logger = structlog.get_logger(__name__)

# Log patterns for Ollama errors
async def log_ollama_error(
    error: OllamaError,
    url: str,
    platform: str,
    attempt: int,
) -> None:
    """Log Ollama errors with full context for debugging."""
    logger.error(
        "ollama_extraction_failed",
        error_type=type(error).__name__,
        error_message=str(error),
        url=url,
        platform=platform,
        attempt=attempt,
        base_url=OllamaClient.DEFAULT_BASE_URL,
    )

# Metrics emission
async def emit_ollama_metrics(
    success: bool,
    response_time_ms: float,
    model_used: str,
    gpu_memory_mb: int,
) -> None:
    """Emit metrics for monitoring."""
    metrics = {
        "phoenix_ollama_requests_total": 1,
        "phoenix_ollama_request_duration_ms": response_time_ms,
        "phoenix_ollama_model_used": model_used,
        "phoenix_ollama_gpu_memory_mb": gpu_memory_mb,
        "phoenix_ollama_success": 1 if success else 0,
    }
    for name, value in metrics.items():
        logger.info("metric", name=name, value=value)
```

5. Circuit breaker pattern (optional but recommended):

```python
class OllamaCircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    Opens after threshold failures, preventing further inference calls
    until the reset timeout passes.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout_seconds: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open

    def can_execute(self) -> bool:
        """Check if inference call is allowed."""
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
                return True
            return False
        return True  # half-open

    def record_success(self) -> None:
        """Record successful inference."""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self) -> None:
        """Record failed inference."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
```

6. Hardware Detection Guidelines:

```python
# Detect GPU availability
def detect_gpu() -> Optional[GPUInfo]:
    """Detect GPU and return info.

    Returns:
        GPUInfo if GPU available, None for CPU-only.
    """
    try:
        import nvidia_ml_py as nvml
        nvml.nvmlInit()
        handle = nvml.nvmlDeviceGetHandleByIndex(0)
        mem = nvml.nvmlDeviceGetMemoryInfo(handle)
        return GPUInfo(
            name=nvml.nvmlDeviceGetName(handle),
            vram_total_mb=mem.total // 1024 // 1024,
            vram_used_mb=mem.used // 1024 // 1024,
            vram_available_mb=mem.free // 1024 // 1024,
        )
    except ImportError:
        # nvidia-ml-py not installed, try Apple Silicon
        return detect_apple_silicon()
    except Exception:
        return None  # No GPU detected


# Auto-select model based on VRAM
def auto_select_model(gpu_info: Optional[GPUInfo]) -> str:
    """Auto-select model based on available VRAM.

    Args:
        gpu_info: GPU information or None for CPU-only.

    Returns:
        Model name string.
    """
    if gpu_info is None:
        # CPU-only mode
        return "qwen2.5:7b"

    vram_gb = gpu_info.vram_available_mb / 1024

    if vram_gb >= 20:
        return "qwen2.5-coder:32b"
    elif vram_gb >= 9:
        return "qwen2.5:7b"
    elif vram_gb >= 4.5:
        return "qwen2.5:7b"
    else:
        return "qwen2.5:7b"  # Will run slowly
```

ERROR HANDLING CHECKLIST:
[ ] All Ollama calls wrapped in try/except
[ ] OllamaTimeoutError triggers retry with increased timeout
[ ] OllamaOutOfMemoryError triggers fallback to smaller model
[ ] OllamaNotRunningError prompts user to start Ollama
[ ] JSON parse errors attempt markdown stripping before failing
[ ] All errors logged with structlog (structured JSON logging)
[ ] Metrics emitted for monitoring (request count, latency, model, GPU memory)
[ ] Circuit breaker prevents cascading failures
[ ] Graceful degradation: Ollama failure never breaks core pipeline
[ ] Hardware detection auto-selects appropriate model
[ ] CPU-only mode supported when no GPU available
[ ] CI/testing can use mock Ollama responses

DELIVERABLES:
- Complete exception hierarchy (6 exception classes)
- _call_with_retry() with model fallback chain
- extract_with_fallback() pipeline integration
- Error logging with full context
- Metrics emission for monitoring
- Circuit breaker implementation
- Hardware detection and auto-selection
- Unit tests for all error scenarios
- Integration test simulating OOM and timeout cascades
```
