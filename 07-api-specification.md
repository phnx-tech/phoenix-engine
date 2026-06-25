# Phoenix Engine -- Pure Scraping API Specification

**Version:** 2.0.0
**Date:** 2025-01-20
**Status:** Authoritative Specification
**Audience:** AI Development Agents (Kimi Code), Senior Engineers, Plugin Authors
**Constraint:** NO OFFICIAL SOCIAL MEDIA APIs ARE EVER USED. All data is extracted from raw HTML.

---

## Table of Contents

1. [Library Public API](#1-library-public-api)
2. [Scraper Classes](#2-scraper-classes)
3. [Selector Engine API](#3-selector-engine-api)
4. [Session Manager API](#4-session-manager-api)
5. [Ollama AI Engine API](#5-ollama-ai-engine-api)
6. [Model Manager API](#6-model-manager-api)
7. [Hardware Monitor API](#7-hardware-monitor-api)
8. [Model Selector API](#8-model-selector-api)
9. [CLI Command Reference](#9-cli-command-reference)
10. [Plugin Interface Contract](#10-plugin-interface-contract)
11. [Configuration Schema](#11-configuration-schema)
12. [Data Output Schema](#12-data-output-schema)
13. [Error Codes & Exceptions](#13-error-codes--exceptions)

---

## 1. Library Public API

All public API classes are importable from the `phoenix` package root. The primary entry point is the `PhoenixEngine` class.

### 1.1 PhoenixEngine -- Main Engine Class

```python
class PhoenixEngine:
    """Primary entry point for the Phoenix Engine scraping library.

    Initialize once and reuse across multiple scraping operations.
    Supports async context manager protocol for automatic cleanup.

    Pure scraping: all data comes from HTML parsing via HTTP requests
    or headless browser rendering. No official APIs are used.

    Example:
        async with PhoenixEngine() as engine:
            result = await engine.scrape("https://x.com/user/status/123")
            print(result.output.text)
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        *,
        plugin_dirs: Optional[list[str]] = None,
    ) -> None:
        """Initialize the Phoenix Engine.

        Parameters:
            config: Application configuration. If None, loads from defaults
                   and environment variables.
            plugin_dirs: Additional directories to scan for scraper plugins.

        Raises:
            ConfigurationError: If configuration is invalid.
            PluginLoadError: If a scraper plugin fails to load.
        """

    async def scrape(
        self,
        url: str,
        *,
        strategy: Optional[ScrapingStrategy] = None,
        archive: bool = True,
        options: Optional[ScrapingOptions] = None,
    ) -> ScrapingResult:
        """Scrape data from a single URL.

        Executes the full scraping pipeline:
        route URL --> select strategy (HTTP/Browser) --> fetch HTML
        --> parse with CSS selectors --> normalize --> archive.

        All data is extracted from raw HTML. No official APIs are called.

        Parameters:
            url: The URL to scrape. Must be a valid HTTP(S) URL.
            strategy: Override the scraping strategy (http/browser).
                     If None, the engine auto-selects the best strategy.
            archive: Whether to archive the raw HTML source. Default True.
            options: Additional scraping options (timeouts, wait selectors, etc.).

        Returns:
            ScrapingResult containing the scraped data or error information.

        Raises:
            UnsupportedURLError: If no scraper plugin can handle the URL.
            ConfigurationError: If the engine is misconfigured.

        Example:
            result = await engine.scrape("https://instagram.com/p/ABC123/")
            if result.success:
                print(f"Post by {result.output.author}: {result.output.text}")
            else:
                print(f"Failed: {result.error.message}")
        """

    async def scrape_batch(
        self,
        urls: list[str],
        *,
        max_concurrency: int = 5,
        strategy: Optional[ScrapingStrategy] = None,
        archive: bool = True,
        options: Optional[ScrapingOptions] = None,
    ) -> list[ScrapingResult]:
        """Scrape data from multiple URLs concurrently.

        Parameters:
            urls: List of URLs to scrape. Invalid URLs are skipped with errors.
            max_concurrency: Maximum number of concurrent scrapes. Default 5.
            strategy: Override strategy for all URLs. If None, auto-select per URL.
            archive: Whether to archive raw HTML sources. Default True.
            options: Additional scraping options applied to all URLs.

        Returns:
            List of ScrapingResult, one per URL, in the same order as input.

        Raises:
            ValueError: If urls is empty or max_concurrency < 1.

        Example:
            urls = ["https://x.com/a/1", "https://x.com/b/2"]
            results = await engine.scrape_batch(urls, max_concurrency=3)
            for url, result in zip(urls, results):
                print(f"{url}: {'OK' if result.success else 'FAIL'}")
        """

    def register_plugin(self, plugin: ScraperPlugin) -> None:
        """Register a scraper plugin at runtime.

        Parameters:
            plugin: ScraperPlugin implementation to register.

        Raises:
            PluginError: If plugin registration fails (duplicate name, invalid manifest).

        Example:
            engine.register_plugin(MyCustomScraper())
        """

    async def login(self, platform: str, *, interactive: bool = True) -> Session:
        """Authenticate with a platform via browser and store cookies.

        Opens a headless (or headed) browser for the user to log in
        interactively. Captures session cookies after successful login
        for subsequent scraping. No credentials are accepted as parameters --
        the user always enters them in the browser window.

        Parameters:
            platform: Platform identifier (instagram, x, linkedin, etc.).
            interactive: If True, opens visible browser for user interaction.

        Returns:
            Session object containing the authenticated browser cookies.

        Raises:
            AuthenticationError: If login process fails.
            UnsupportedPlatformError: If platform has no login support.

        Example:
            session = await engine.login("instagram")
            # User logs in via browser window...
            # Session cookies are now stored for future scrapes
        """

    async def logout(self, platform: str) -> None:
        """Log out from a platform and destroy stored session cookies.

        Parameters:
            platform: Platform identifier to log out from.
        """

    async def get_session(self, platform: str) -> Optional[Session]:
        """Get the current stored session for a platform.

        Returns:
            Session if one exists and is valid, None otherwise.
        """

    async def health_check(self) -> dict[str, Any]:
        """Check engine health and component status.

        Returns:
            Dict with status, version, loaded plugins, and component diagnostics.
            Includes selector health metrics for each platform and Ollama status.
        """

    async def close(self) -> None:
        """Close the engine and release all resources.

        Must be called when done, or use async context manager.
        """

    async def __aenter__(self) -> "PhoenixEngine": ...
    async def __aexit__(self, *args) -> None: ...
```

#### PhoenixEngine Parameters Table

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `config` | `Config` | No | `None` (auto-load) | Application configuration object |
| `plugin_dirs` | `list[str]` | No | `None` | Extra directories to scan for scraper plugins |

#### scrape() Parameters Table

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `str` | Yes | -- | Target URL to scrape |
| `strategy` | `ScrapingStrategy` | No | `None` (auto) | Override: `http` or `browser` |
| `archive` | `bool` | No | `True` | Whether to save raw HTML to archive |
| `options` | `ScrapingOptions` | No | `None` | Additional scraping parameters |

---

## 2. Scraper Classes

### 2.1 HTMLScraper -- Abstract Base

```python
class HTMLScraper(ABC):
    """Abstract base class for all HTML scraping strategies.

    Concrete implementations: HTTPScraper, BrowserScraper.
    The PipelineController selects and instantiates the appropriate scraper
    based on the StrategySelector's decision.

    All scrapers return an HTMLDocument containing parsed BeautifulSoup DOM
    and raw HTML. No API calls are made -- only HTTP requests or browser rendering.
    """

    @abstractmethod
    async def fetch(
        self,
        url: str,
        *,
        session: Optional[Session] = None,
        options: Optional[ScrapingOptions] = None,
    ) -> HTMLDocument:
        """Fetch and parse HTML from the given URL.

        Parameters:
            url: The URL to fetch.
            session: Optional authenticated session (cookies) for the platform.
            options: Scraping options (timeouts, wait selectors, etc.).

        Returns:
            HTMLDocument containing parsed DOM (BeautifulSoup tree) and metadata.

        Raises:
            HTTPError: On HTTP-level failures (HTTPScraper).
            BrowserError: On browser automation failures (BrowserScraper).
            RateLimitExceededError: If rate limit is exceeded.
        """

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check scraper health and readiness.

        Returns:
            Dict with status, version, and diagnostic info.
        """
```

---

### 2.2 HTTPScraper -- Direct HTTP Fetching

```python
class HTTPScraper(HTMLScraper):
    """Fast, lightweight HTML scraping via asynchronous HTTP requests.

    Best for static pages and platforms that return meaningful HTML server-side.
    Parses HTML with BeautifulSoup4 and lxml for fast structured extraction.

    Technology: httpx (async HTTP/2) + beautifulsoup4 + lxml
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        rate_limiter: RateLimiter,
        user_agent: str = "PhoenixEngine/1.0",
    ) -> None:
        """Initialize HTTPScraper.

        Parameters:
            http_client: Configured httpx.AsyncClient with connection pooling.
            rate_limiter: Domain rate limiter.
            user_agent: User-Agent string sent with every request.
        """

    async def fetch(
        self,
        url: str,
        *,
        session: Optional[Session] = None,
        options: Optional[ScrapingOptions] = None,
    ) -> HTMLDocument:
        """Fetch URL via HTTP GET and parse HTML response.

        Process:
        1. Check rate limit for target domain
        2. Build request headers (User-Agent, Accept, cookies from session)
        3. Send HTTP GET via httpx
        4. Validate response status (2xx expected)
        5. Parse response body HTML with BeautifulSoup
        6. Return HTMLDocument with parsed DOM

        Returns:
            HTMLDocument with soup (BeautifulSoup tree), raw_html, status, headers.

        Raises:
            HTTPError: On non-2xx status codes, network errors, timeouts.
        """

    async def health_check(self) -> dict[str, Any]:
        """Verify HTTP client and connection pool health."""
```

#### HTTPScraper Configuration

```python
class HTTPScraperConfig(BaseModel):
    """Configuration for HTTPScraper."""
    timeout: float = 30.0
    max_redirects: int = 5
    follow_redirects: bool = True
    http2: bool = True
    max_connections: int = 20
    max_keepalive: int = 10
    headers: dict[str, str] = Field(default_factory=lambda: {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    })
```

---

### 2.3 BrowserScraper -- Headless Browser Rendering

```python
class BrowserScraper(HTMLScraper):
    """Full browser automation for JavaScript-rendered HTML content.

    Uses Playwright to control headless Chromium, executing JavaScript
    and waiting for dynamic content to load before returning the DOM.

    Best for SPAs, platforms with heavy client-side rendering (Instagram,
    TikTok, Facebook), and pages requiring authenticated sessions.

    Technology: playwright (async) + headless Chromium
    """

    def __init__(
        self,
        browser_pool: BrowserPool,
        rate_limiter: RateLimiter,
        config: BrowserConfig = Field(default_factory=BrowserConfig),
    ) -> None:
        """Initialize BrowserScraper.

        Parameters:
            browser_pool: Pool of reusable browser contexts.
            rate_limiter: Domain rate limiter.
            config: Browser-specific configuration.
        """

    async def fetch(
        self,
        url: str,
        *,
        session: Optional[Session] = None,
        options: Optional[ScrapingOptions] = None,
    ) -> HTMLDocument:
        """Fetch URL via headless browser and return rendered DOM.

        Process:
        1. Acquire browser context from pool
        2. Inject session cookies if provided
        3. Navigate to URL
        4. Wait for page load (networkidle or domcontentloaded)
        5. If options.wait_for is set, wait for specific CSS selector
        6. Scroll page if needed for lazy-loaded content
        7. Extract rendered HTML from page.content()
        8. Parse HTML with BeautifulSoup
        9. Optional: take screenshot for debugging
        10. Return HTMLDocument with rendered DOM

        Parameters:
            url: The URL to fetch.
            session: Optional authenticated session for cookie injection.
            options: Scraping options including:
                - wait_for: CSS selector to wait for before extraction
                - scroll: Whether to scroll for lazy-loaded content
                - screenshot: Whether to capture screenshot
                - timeout: Browser navigation timeout

        Returns:
            HTMLDocument with rendered DOM, screenshot path (if requested).

        Raises:
            BrowserError: On navigation timeout, browser crash, page load failure.
        """

    async def health_check(self) -> dict[str, Any]:
        """Verify browser pool health and Chromium availability."""
```

#### BrowserConfig Model

```python
class BrowserConfig(BaseModel):
    """Configuration for BrowserScraper."""
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    pool_size: int = 3
    timeout: float = 60.0
    wait_until: str = "networkidle"  # "load" | "domcontentloaded" | "networkidle"
    user_agent: Optional[str] = None  # None = use default Chromium UA
    args: list[str] = Field(default_factory=lambda: [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
    ])
```

---

### 2.4 ScrapingOptions -- Request Options

```python
class ScrapingOptions(BaseModel):
    """Options that can be passed to scrape() calls."""

    # HTTP-specific
    timeout: Optional[float] = None  # Override default timeout
    headers: dict[str, str] = Field(default_factory=dict)  # Additional headers
    follow_redirects: Optional[bool] = None

    # Browser-specific
    wait_for: Optional[str] = None  # CSS selector to wait for
    scroll: bool = False  # Whether to scroll for lazy-loaded content
    screenshot: bool = False  # Whether to capture screenshot
    viewport: Optional[dict] = None  # Override viewport size

    # Extraction
    fields: Optional[list[str]] = None  # Specific fields to extract (None = all)
    selector_hints: dict[str, str] = Field(default_factory=dict)  # Custom CSS selectors

    # General
    archive: Optional[bool] = None  # Override archive setting
    max_retries: Optional[int] = None  # Override retry count
```

---

## 3. Selector Engine API

### 3.1 SelectorEngine -- CSS/XPath Management and Fallback Chains

The `SelectorEngine` is the heart of the HTML extraction system. It manages CSS selector sets for each platform, executes fallback chains when selectors fail, and tracks selector health.

```python
class SelectorEngine:
    """Manages CSS selector and XPath expression sets with fallback chains.

    Each platform scraper registers a SelectorSet containing ordered chains
    of CSS selectors and XPath backup expressions for each data field.
    When extracting data, the engine tries selectors in order until one matches.

    Example:
        engine = SelectorEngine()
        engine.register_selectors("x_twitter", X_TWITTER_SELECTORS)

        result = engine.extract(soup, "x_twitter", "tweet_text")
        # result.value = "The tweet content"
        # result.selector_used = 'article[data-testid="tweet"] div[lang]'
        # result.selector_type = "css_primary"
    """

    def __init__(self) -> None:
        """Initialize with empty selector registry."""

    def register_selectors(self, platform: str, selectors: SelectorSet) -> None:
        """Register a CSS/XPath selector set for a platform.

        Parameters:
            platform: Platform identifier (e.g., "x_twitter").
            selectors: SelectorSet containing CSS chains and XPath backups.

        Raises:
            ValueError: If selectors are invalid or duplicate platform.
        """

    def extract(
        self,
        soup: BeautifulSoup,
        platform: str,
        field: str,
    ) -> SelectorResult:
        """Extract a field value using registered selectors with fallback chain.

        Tries selectors in this order:
        1. Primary CSS selector
        2. Fallback CSS selectors (in order)
        3. XPath backup expression

        Parameters:
            soup: Parsed BeautifulSoup tree.
            platform: Platform identifier.
            field: Field name to extract (e.g., "tweet_text").

        Returns:
            SelectorResult with extracted value and metadata about which
            selector succeeded, or None values if all failed.
        """

    def extract_all(
        self,
        soup: BeautifulSoup,
        platform: str,
    ) -> dict[str, SelectorResult]:
        """Extract all registered fields for a platform.

        Parameters:
            soup: Parsed BeautifulSoup tree.
            platform: Platform identifier.

        Returns:
            Dict mapping field names to SelectorResult objects.
        """

    def get_selector_health(self, platform: str) -> dict[str, SelectorHealth]:
        """Return health metrics for all selectors of a platform.

        Returns:
            Dict mapping "platform:field:selector" to health metrics
            (match rate, last success, last failure, total attempts).
        """

    def update_selector_stats(
        self,
        platform: str,
        field: str,
        selector: str,
        matched: bool,
    ) -> None:
        """Update usage statistics for a selector.

        Called after each extraction attempt to track selector health.
        """

    def get_failed_selectors(self, platform: str) -> list[str]:
        """Return selectors that have recently failed to match.

        Used for alerting when page layouts change.
        """
```

### 3.2 SelectorSet -- Selector Registration Bundle

```python
class SelectorSet(BaseModel):
    """A complete set of CSS selectors and XPath fallbacks for a platform.

    Each platform scraper defines one SelectorSet that is registered
    with the SelectorEngine at plugin load time.
    """

    platform: str = Field(..., description="Platform identifier")
    version: str = Field(..., description="Selector set version (ISO date recommended)")
    description: str = Field("", description="Human-readable description")
    selectors: dict[str, SelectorChain] = Field(
        ...,
        description="Map of field names to CSS selector chains"
    )
    xpath_backups: dict[str, str] = Field(
        default_factory=dict,
        description="Map of field names to XPath backup expressions"
    )
    critical_fields: list[str] = Field(
        default_factory=list,
        description="Fields that must be extracted for success"
    )

    def validate_selectors(self) -> list[str]:
        """Validate that all CSS selectors are syntactically valid.

        Returns:
            List of validation error messages (empty if all valid).
        """

class SelectorChain(BaseModel):
    """Ordered chain of CSS selectors for extracting a single field.

    When extracting, each selector is tried in order until one matches.
    """

    field: str = Field(..., description="Field name this chain extracts")
    description: str = Field("", description="What this field represents")
    primary: str = Field(..., description="Primary CSS selector")
    fallbacks: list[str] = Field(
        default_factory=list,
        description="Ordered list of fallback CSS selectors"
    )
    attribute: Optional[str] = Field(
        None,
        description="HTML attribute to extract (None = text content)"
    )
    transform: Optional[str] = Field(
        None,
        description="Optional transform: 'strip', 'lower', 'int', 'parse_count'"
    )

    def all_selectors(self) -> list[str]:
        """Return all selectors in order: primary + fallbacks."""
        return [self.primary] + self.fallbacks

class SelectorResult(BaseModel):
    """Result of a single field extraction attempt."""

    value: Optional[str] = Field(None, description="Extracted value")
    field: str = Field(..., description="Field name")
    selector_used: Optional[str] = Field(None, description="Selector that matched")
    selector_type: Literal["css_primary", "css_fallback", "xpath", "none"] = Field(
        "none", description="Which selector type succeeded"
    )
    fallback_index: int = Field(-1, description="Index in fallback chain (-1 = primary)")
    matched: bool = Field(False, description="Whether any selector matched")
    transform_applied: Optional[str] = Field(None, description="Transform that was applied")

class SelectorHealth(BaseModel):
    """Health metrics for a single selector."""

    selector: str = Field(..., description="The CSS selector string")
    field: str = Field(..., description="Field this selector extracts")
    total_attempts: int = Field(0)
    total_matches: int = Field(0)
    match_rate: float = Field(1.0, ge=0.0, le=1.0)
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = Field(0)
    status: Literal["healthy", "degraded", "failed"] = "healthy"
```

### 3.3 Selector Engine Usage Example

```python
from phoenix.scrapers.selectors import SelectorEngine, SelectorSet, SelectorChain
from bs4 import BeautifulSoup

# Define selectors for a platform
selectors = SelectorSet(
    platform="example_blog",
    version="2025.01.15",
    selectors={
        "title": SelectorChain(
            field="title",
            primary="article h1.entry-title",
            fallbacks=["h1", "article h1", ".post-title"],
            attribute=None,
            transform="strip",
        ),
        "author": SelectorChain(
            field="author",
            primary="span.author-name a",
            fallbacks=["span.author-name", ".byline a", "meta[name='author']"],
            attribute=None,
        ),
        "publish_date": SelectorChain(
            field="publish_date",
            primary="time.entry-date",
            fallbacks=["time[datetime]", "meta[property='article:published_time']"],
            attribute="datetime",
        ),
    },
    xpath_backups={
        "title": "//article//h1//text()",
        "author": "//span[contains(@class,'author')]//text()",
    },
    critical_fields=["title"],
)

# Register and use
engine = SelectorEngine()
engine.register_selectors("example_blog", selectors)

# Extract from HTML
html = "<article><h1 class='entry-title'>  My Post  </h1>...</article>"
soup = BeautifulSoup(html, "lxml")

result = engine.extract(soup, "example_blog", "title")
assert result.value == "My Post"
assert result.selector_used == "article h1.entry-title"
assert result.selector_type == "css_primary"
assert result.transform_applied == "strip"
```

---

## 4. Session Manager API

### 4.1 SessionManager -- Cookie and Auth State

Manages authenticated browser sessions stored as encrypted cookies. Used for platforms that require login to access public content.

```python
class SessionManager:
    """Manages authenticated browser sessions (cookies) for scraping.

    Sessions are stored encrypted at rest. Login is always done via
    interactive browser -- credentials are never accepted as code parameters.
    """

    def __init__(
        self,
        storage: Storage,
        *,
        encryption_key: Optional[str] = None,
    ) -> None:
        """Initialize SessionManager.

        Parameters:
            storage: Storage backend for session persistence.
            encryption_key: Optional key for cookie encryption.
                           If None, derives key from OS keyring.
        """

    async def login_browser(
        self,
        platform: str,
        *,
        headless: bool = False,
        timeout: float = 300.0,
    ) -> Session:
        """Open browser for interactive login and capture cookies.

        Launches a Playwright browser window pointing to the platform's
        login page. The user manually enters credentials and completes
        any 2FA. The engine captures session cookies after successful login.

        Parameters:
            platform: Platform identifier.
            headless: If False, opens visible browser for user interaction.
            timeout: Maximum time to wait for login completion.

        Returns:
            Session with captured cookies.

        Raises:
            AuthenticationError: If login times out or fails.
        """

    async def get_session(self, platform: str) -> Optional[Session]:
        """Retrieve stored session for a platform.

        Returns:
            Session if one exists and is still valid, None otherwise.
        """

    async def is_session_valid(self, platform: str) -> bool:
        """Check if stored session is still valid.

        Validates by checking expiration time and optionally making
        a lightweight HTTP request with the session cookies.
        """

    async def refresh_session(self, platform: str) -> Session:
        """Refresh an expired session if possible.

        For most platforms, this re-opens the browser for re-authentication.
        """

    async def logout(self, platform: str) -> None:
        """Destroy stored session for a platform."""

    async def list_sessions(self) -> list[SessionInfo]:
        """List all stored sessions (without sensitive cookie data)."""

class SessionInfo(BaseModel):
    """Non-sensitive session metadata."""
    platform: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_valid: bool
```

---

## 5. Ollama AI Engine API

The `OllamaAIEngine` is the core AI-powered extraction component that uses a **local Ollama server** to intelligently parse HTML when standard selectors fail. All inference runs locally at `http://localhost:11434` -- no external API calls, no API keys, no token costs. All classes are importable from `phoenix.ollama`.

### 5.1 OllamaAIEngine -- AI-Powered HTML Extraction

```python
class OllamaAIEngine:
    """Core AI engine using local Ollama for intelligent HTML extraction.

    When standard CSS selectors and XPath expressions fail to parse HTML,
    the OllamaAIEngine sends the raw HTML to the local Ollama server which
    analyzes the DOM structure and returns structured JSON data.

    Uses direct httpx calls to Ollama REST API at http://localhost:11434.
    No OpenAI SDK. No cloud API. Everything runs on local hardware.

    Primary model: dolphincoder:7b (128K context, structured output)
    Fallback model: qwen2.5:7b (for smaller pages, faster inference)
    Enterprise model: qwen2.5-coder:32b (for maximum accuracy)
    Alternative: deepseek-coder-v2:16b (if qwen unavailable)

    Example:
        engine = OllamaAIEngine()  # Uses http://localhost:11434

        result = await engine.extract(
            html=raw_html,
            context=ExtractionContext(
                url="https://x.com/user/status/123",
                source_platform="x_twitter",
                content_type_hint="post",
            )
        )
        print(result.extracted_data)  # {"text": "...", "author": "...", ...}
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "dolphincoder:7b",
        cache: Optional[AIResponseCache] = None,
        hardware_monitor: Optional[HardwareMonitor] = None,
        model_manager: Optional[ModelManager] = None,
    ) -> None:
        """Initialize the Ollama AI Engine.

        Parameters:
            base_url: Ollama server URL. Default: http://localhost:11434
            default_model: Default Ollama model for extraction.
                           "dolphincoder:7b" for most tasks.
                           "qwen2.5:7b" for small/fast tasks or fallback.
                           "qwen2.5-coder:32b" for maximum accuracy.
            cache: Optional AIResponseCache for response caching.
            hardware_monitor: Optional HardwareMonitor for VRAM/RAM tracking.
            model_manager: Optional ModelManager for pull/verify/unload.

        Raises:
            OllamaNotRunningError: If Ollama server is not reachable.

        Example:
            # Default local Ollama
            engine = OllamaAIEngine()

            # Custom Ollama URL (e.g., remote or different port)
            engine = OllamaAIEngine(base_url="http://192.168.1.100:11434")

            # With hardware monitoring and caching
            engine = OllamaAIEngine(
                hardware_monitor=HardwareMonitor(),
                cache=AIResponseCache(backend="disk", ttl=3600),
            )
        """

    async def extract(
        self,
        html: str,
        context: ExtractionContext,
        model: Optional[str] = None,
    ) -> OllamaExtractionResult:
        """Extract structured data from raw HTML using local Ollama inference.

        Process:
        1. Check cache for identical HTML (SHA-256 hash)
        2. Auto-select model based on HTML size and available VRAM (if auto-select enabled)
        3. Verify model is pulled, pull if needed
        4. Chunk HTML if it exceeds model context window
        5. Build system prompt for HTML extraction
        6. Call Ollama /api/generate with temperature 0.1-0.3 (deterministic)
        7. Parse and validate JSON response
        8. Cache result and track inference metrics

        Parameters:
            html: Raw HTML string to extract data from.
            context: ExtractionContext with URL, platform, schema hints.
            model: Override model for this extraction. Auto-selected if None.

        Returns:
            OllamaExtractionResult with extracted data, confidence,
            model used, inference time, and GPU memory usage.

        Raises:
            OllamaNotRunningError: If Ollama server is not reachable.
            OllamaModelNotFoundError: If requested model is not pulled.
            OllamaOutOfMemoryError: If GPU/CPU out of memory.
            OllamaTimeoutError: If local inference exceeds timeout.
            OllamaJSONParseError: If response cannot be parsed as JSON.

        Example:
            context = ExtractionContext(
                url="https://instagram.com/p/ABC123/",
                source_platform="instagram",
                content_type_hint="post",
                fields_required=["caption", "likes", "author", "timestamp"],
            )
            result = await engine.extract(html, context)
            if result.success:
                print(f"Extracted: {result.extracted_data}")
                print(f"Confidence: {result.confidence}")
                print(f"Model: {result.model_used}")
                print(f"Inference time: {result.inference_time_ms}ms")
                print(f"GPU memory: {result.gpu_memory_mb}MB")
        """

    async def suggest_selectors(
        self,
        html: str,
        old_selectors: list[str],
        model: Optional[str] = None,
    ) -> list[SelectorSuggestion]:
        """Request updated CSS selectors from Ollama when existing ones fail.

        Sends the new HTML structure along with previously-working selectors.
        Ollama analyzes the DOM and proposes new selectors matching the layout.

        Parameters:
            html: Current HTML with the new/changed structure.
            old_selectors: CSS selectors that previously worked but now fail.
            model: Override model. Auto-selected if None.

        Returns:
            List of SelectorSuggestion objects, each containing:
            - new_selector: The proposed CSS selector string
            - field: The data field this selector targets
            - confidence: Match confidence (0.0-1.0)
            - sample: Sample of content the selector would match

        Raises:
            OllamaError: If inference fails.

        Example:
            old = ['article[data-testid="tweet"] div[lang]']
            suggestions = await engine.suggest_selectors(new_html, old)
            for s in suggestions:
                print(f"{s.field}: {s.new_selector} (confidence: {s.confidence})")
        """

    async def classify_content(
        self,
        html: str,
        url: str,
        model: Optional[str] = None,
    ) -> ContentClassification:
        """Classify page content type using Ollama.

        Sends a truncated HTML snippet to Ollama for fast classification.
        Temperature: 0.1 (highly deterministic).

        Parameters:
            html: HTML content (truncated to ~8K tokens internally).
            url: Page URL for additional classification context.
            model: Override model. Auto-selected if None.

        Returns:
            ContentClassification with content_type, confidence,
            platform_detected, and suggested extraction schema.

        Example:
            classification = await engine.classify_content(html, url)
            print(f"Type: {classification.content_type}")  # "post"
            print(f"Confidence: {classification.confidence}")  # 0.96
        """

    async def health_check(self) -> dict[str, Any]:
        """Check Ollama service health and model availability.

        Returns:
            Dict with keys:
            - status: "ok" | "degraded" | "unavailable"
            - models_available: List of pulled models
            - default_model_loaded: Whether default model is in memory
            - gpu_info: GPU name, VRAM total, VRAM used (if available)
            - recent_latency_ms: Average inference latency over last 10 calls

        Example:
            health = await engine.health_check()
            print(f"Ollama: {health['status']}")
            print(f"Models: {health['models_available']}")
            print(f"GPU: {health['gpu_info']}")
        """

    def list_available_models(self) -> list[ModelInfo]:
        """List all models available in the local Ollama instance.

        Returns:
            List of ModelInfo with name, size, parameter count,
            quantization level, and VRAM requirements.
        """
```

#### OllamaAIEngine Parameters Table

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | `str` | No | `"http://localhost:11434"` | Ollama server URL |
| `default_model` | `str` | No | `"dolphincoder:7b"` | Default Ollama model |
| `cache` | `AIResponseCache` | No | `None` | Response cache (memory or disk) |
| `hardware_monitor` | `HardwareMonitor` | No | `None` | GPU/VRAM/RAM monitoring |
| `model_manager` | `ModelManager` | No | `None` | Model lifecycle management |

#### extract() Parameters Table

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `html` | `str` | Yes | -- | Raw HTML string to extract from |
| `context` | `ExtractionContext` | Yes | -- | Extraction context with URL, platform, schema |
| `model` | `str` | No | `None` (auto-select) | Override model for this extraction |

#### ExtractionContext Model

```python
class ExtractionContext(BaseModel):
    """Context passed to OllamaAIEngine.extract() to guide extraction."""

    url: str
    source_platform: Optional[str] = None
    content_type_hint: Optional[str] = None  # "article", "product", "profile", "post", etc.
    previous_selectors: list[str] = []
    extraction_schema: Optional[dict] = None  # JSON Schema for desired output
    fields_required: list[str] = []
    html_size_bytes: int = 0
    browser_rendered: bool = False
```

#### OllamaExtractionResult Model

```python
class OllamaExtractionResult(BaseModel):
    """Result of Ollama-powered local HTML extraction."""

    success: bool
    extracted_data: dict
    confidence: float  # 0.0-1.0
    model_used: str  # e.g., "qwen2.5:7b"
    inference_time_ms: int
    gpu_memory_mb: int
    prompt_tokens: int
    completion_tokens: int
    total_duration_ms: int
    load_duration_ms: int
    cached: bool = False
    chunks_processed: int = 1
    error: Optional[str] = None
    hardware_profile: Optional[HardwareProfile] = None
```

#### SelectorSuggestion Model

```python
class SelectorSuggestion(BaseModel):
    """A single CSS selector suggestion from Ollama."""

    field: str
    new_selector: str
    old_selector: Optional[str] = None
    confidence: float  # 0.0-1.0
    sample: str  # Sample content the selector would match
    selector_type: str  # "css", "xpath"
```

#### ContentClassification Model

```python
class ContentClassification(BaseModel):
    """Result of Ollama content type classification."""

    content_type: str  # "article", "product", "profile", "post", "video", etc.
    confidence: float  # 0.0-1.0
    platform_detected: Optional[str] = None
    schema_suggested: Optional[dict] = None
    reasoning: str = ""
```

---

### 5.2 OllamaClient -- Direct HTTP Client

```python
class OllamaClient:
    """Low-level HTTP client for Ollama REST API.

    Uses httpx for direct HTTP requests to localhost:11434.
    No OpenAI SDK. No external dependencies.

    Endpoints:
    - POST /api/generate     -- Single-turn generation
    - POST /api/chat         -- Multi-turn chat completion
    - GET  /api/tags         -- List pulled models
    - POST /api/pull         -- Download model
    - DELETE /api/delete     -- Remove model
    - POST /api/show         -- Model info
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
        max_retries: int = 2,
    ) -> None:
        """Initialize OllamaClient.

        Parameters:
            base_url: Ollama server URL. Default: http://localhost:11434
            timeout: Request timeout in seconds (local inference can be slow).
            max_retries: Max retries for transient failures.
        """

    async def generate(
        self,
        prompt: str,
        model: str = "dolphincoder:7b",
        system: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
        stream: bool = False,
    ) -> OllamaGenerateResponse:
        """Send generation request to /api/generate.

        Parameters:
            prompt: User prompt with HTML and context.
            model: Ollama model identifier.
            system: System prompt.
            options: Generation options (temperature, num_ctx, etc.).
            stream: Whether to stream response.

        Returns:
            OllamaGenerateResponse with generated text and metadata.

        Raises:
            OllamaNotRunningError: If Ollama is not reachable.
            OllamaModelNotFoundError: If model not available.
            OllamaTimeoutError: On timeout.

        Example:
            response = await client.generate(
                prompt="Extract data from: <html>...</html>",
                model="dolphincoder:7b",
                system="You are a data extraction engine.",
                options={"temperature": 0.1, "num_ctx": 16384},
            )
            print(response.response)  # Extracted JSON string
        """

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "dolphincoder:7b",
        options: Optional[dict[str, Any]] = None,
        stream: bool = False,
    ) -> OllamaChatResponse:
        """Send chat request to /api/chat.

        Parameters:
            messages: List of {role, content} dicts.
            model: Ollama model identifier.
            options: Generation options.
            stream: Whether to stream response.

        Returns:
            OllamaChatResponse with message content and metadata.
        """

    async def list_models(self) -> list[ModelInfo]:
        """List all pulled models via GET /api/tags.

        Returns:
            List of ModelInfo with name, size, digest, etc.
        """

    async def pull_model(self, name: str) -> AsyncIterator[dict]:
        """Download model via POST /api/pull.

        Yields progress updates. Can take minutes for large models.

        Example:
            async for progress in client.pull_model("qwen2.5:7b"):
                print(f"{progress.get('completed', 0)}/{progress.get('total', 0)}")
        """

    async def delete_model(self, name: str) -> None:
        """Delete model via DELETE /api/delete."""

    async def model_info(self, name: str) -> ModelInfo:
        """Get model info via POST /api/show."""

    async def check_health(self) -> bool:
        """Check if Ollama server is running."""


class OllamaGenerateResponse(BaseModel):
    """Response from Ollama /api/generate."""

    response: str
    model: str
    created_at: str
    done: bool
    total_duration_ms: int
    load_duration_ms: int
    prompt_eval_count: int
    prompt_eval_duration_ms: int
    eval_count: int
    eval_duration_ms: int


class OllamaChatResponse(BaseModel):
    """Response from Ollama /api/chat."""

    message: dict[str, str]
    model: str
    created_at: str
    done: bool
    total_duration_ms: int
    prompt_eval_count: int
    eval_count: int
```

#### OllamaClient Parameters Table

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | `str` | No | `"http://localhost:11434"` | Ollama server URL |
| `timeout` | `float` | No | `120.0` | Request timeout in seconds |
| `max_retries` | `int` | No | `2` | Max retries for transient failures |

---

### 5.3 HTMLChunker -- Large HTML Splitting

```python
class HTMLChunker:
    """Splits large HTML documents into context-safe chunks for Ollama.

    When HTML exceeds the model's context window, the HTMLChunker splits
    the document at element boundaries while preserving DOM context overlap.

    Example:
        chunker = HTMLChunker(max_chars=48000)
        chunks = chunker.chunk(large_html, preserve_structure=True)
        for i, chunk in enumerate(chunks):
            result = await ollama_engine.extract(chunk, context)
    """

    def __init__(
        self,
        max_chars: int = 48000,
        overlap_chars: int = 3000,
    ) -> None:
        """Initialize HTMLChunker.

        Parameters:
            max_chars: Maximum characters per chunk (~16K tokens for qwen2.5).
            overlap_chars: Character overlap between chunks for context.
        """

    def chunk(self, html: str, preserve_structure: bool = True) -> list[str]:
        """Split HTML into context-safe chunks.

        Parameters:
            html: Raw HTML string.
            preserve_structure: If True, splits at element boundaries.
                               If False, splits at character boundaries.

        Returns:
            List of HTML chunks, each within the context limit.
        """

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: chars / 3 for qwen2.5)."""

    @property
    def max_chars(self) -> int:
        """Return the configured max chars per chunk."""
```

#### HTMLChunker Parameters Table

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_chars` | `int` | No | `48000` | Max chars per chunk (~16K tokens) |
| `overlap_chars` | `int` | No | `3000` | Overlap between chunks |

---

### 5.4 AIResponseCache -- Ollama Response Caching

```python
class AIResponseCache:
    """Cache for Ollama responses to reduce redundant inference calls.

    Supports two backends: in-memory and disk. Cache keys are
    SHA-256 hashes of the HTML content + extraction schema.

    Example:
        # In-memory cache (default, non-persistent)
        cache = AIResponseCache(backend="memory", ttl=3600)

        # Disk cache (persistent across restarts)
        cache = AIResponseCache(backend="disk", ttl=86400, cache_dir="~/.cache/phoenix")
    """

    def __init__(
        self,
        backend: str = "memory",  # "memory" | "disk"
        ttl: int = 3600,
        cache_dir: Optional[str] = None,
    ) -> None:
        """Initialize AI response cache.

        Parameters:
            backend: Cache storage backend.
            ttl: Time-to-live in seconds for cached entries.
            cache_dir: Directory for disk cache (required if backend="disk").
        """

    async def get(self, key: str) -> Optional[OllamaExtractionResult]:
        """Retrieve cached result by key.

        Parameters:
            key: Cache key (SHA-256 hash of HTML + schema).

        Returns:
            Cached OllamaExtractionResult if found and not expired, else None.
        """

    async def set(
        self,
        key: str,
        value: OllamaExtractionResult,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache an extraction result.

        Parameters:
            key: Cache key.
            value: OllamaExtractionResult to cache.
            ttl: Override default TTL for this entry.
        """

    async def invalidate(self, pattern: str) -> int:
        """Invalidate cached entries matching a pattern.

        Parameters:
            pattern: Glob pattern to match cache keys against.

        Returns:
            Number of entries invalidated.
        """

    def generate_key(self, html: str, schema: Optional[dict] = None) -> str:
        """Generate a cache key from HTML content and schema.

        Returns:
            SHA-256 hex digest string.
        """
```

#### AIResponseCache Parameters Table

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `backend` | `str` | No | `"memory"` | Storage: `"memory"`, `"disk"` |
| `ttl` | `int` | No | `3600` | Default TTL in seconds |
| `cache_dir` | `str` | No | `None` | Cache directory (for disk backend) |

---

## 6. Model Manager API

### 6.1 ModelManager -- Ollama Model Lifecycle

```python
class ModelManager:
    """Manages Ollama model lifecycle: pull, verify, select, unload.

    Ensures the right model is available for each task and that
    hardware constraints are respected.
    """

    def __init__(self, client: OllamaClient) -> None:
        """Initialize ModelManager.

        Parameters:
            client: OllamaClient for API communication.
        """

    async def pull(self, model_name: str) -> None:
        """Download a model from Ollama registry.

        Parameters:
            model_name: Name of model to pull (e.g., "qwen2.5:7b").

        Raises:
            OllamaError: If download fails.

        Example:
            await model_manager.pull("qwen2.5:7b")
        """

    async def list(self) -> list[ModelInfo]:
        """List all installed models.

        Returns:
            List of ModelInfo with name, size, digest, modification date.
        """

    async def verify(self, model_name: str) -> bool:
        """Check if a model is pulled and ready.

        Parameters:
            model_name: Model name to check.

        Returns:
            True if model is available.

        Example:
            if not await model_manager.verify("qwen2.5:7b"):
                await model_manager.pull("qwen2.5:7b")
        """

    async def select_for_task(
        self,
        html_size_bytes: int,
        task_type: str,
        hardware_profile: Optional[HardwareProfile] = None,
    ) -> str:
        """Auto-select best model for a task.

        Parameters:
            html_size_bytes: Size of HTML to process.
            task_type: Type of task ("extraction", "classification",
                      "repair", "resolution").
            hardware_profile: Optional hardware constraints.

        Returns:
            Model name string (e.g., "qwen2.5:7b").
        """

    async def unload(self, model_name: str) -> None:
        """Unload a model from GPU memory.

        Parameters:
            model_name: Model to unload.
        """

    async def ensure_pulled(self, model_name: str) -> None:
        """Pull model if not already present.

        Parameters:
            model_name: Model name to ensure.
        """

    async def get_installed_models(self) -> list[ModelInfo]:
        """Get list of installed models.

        Returns:
            List of ModelInfo.
        """

    async def get_recommended_model(
        self,
        html_size: int,
        task_type: str = "extraction",
    ) -> str:
        """Get recommended model for HTML size and task.

        Parameters:
            html_size: HTML size in bytes.
            task_type: Task type.

        Returns:
            Model name string.
        """
```

#### ModelInfo Model

```python
class ModelInfo(BaseModel):
    """Information about an Ollama model."""

    name: str  # e.g., "qwen2.5:7b"
    size: int  # Size in bytes
    parameter_count: str  # e.g., "14B"
    quant_level: str  # e.g., "Q4_K_M"
    vram_required_gb: float
    digest: str
    modified_at: str
```

---

## 7. Hardware Monitor API

### 7.1 HardwareMonitor -- GPU/VRAM/RAM Monitoring

```python
class HardwareMonitor:
    """Monitors local GPU and system resources for Ollama inference."""

    def __init__(self) -> None:
        """Initialize and detect available hardware."""

    def get_gpu_info(self) -> Optional[GPUInfo]:
        """Get GPU information.

        Returns:
            GPUInfo if GPU available, None for CPU-only.
        """

    def get_ram_info(self) -> RAMInfo:
        """Get system RAM information.

        Returns:
            RAMInfo with total, available, used, percentage.
        """

    def can_run_model(self, model_name: str) -> tuple[bool, str]:
        """Check if hardware can run a model.

        Parameters:
            model_name: Model to check.

        Returns:
            Tuple of (can_run, reason).
        """

    def get_optimal_model(self) -> str:
        """Recommend best model for current hardware.

        Returns:
            Model name for largest model that fits available VRAM.
        """

    def get_hardware_profile(self) -> HardwareProfile:
        """Get complete hardware profile.

        Returns:
            HardwareProfile with GPU and RAM info.
        """
```

#### GPUInfo Model

```python
class GPUInfo(BaseModel):
    """GPU information."""

    name: str
    vram_total_mb: int
    vram_used_mb: int
    vram_available_mb: int
    temperature_c: Optional[float] = None
    utilization_percent: Optional[float] = None
```

#### RAMInfo Model

```python
class RAMInfo(BaseModel):
    """System RAM information."""

    total_mb: int
    available_mb: int
    used_mb: int
    percent_used: float
```

#### HardwareProfile Model

```python
class HardwareProfile(BaseModel):
    """Complete hardware profile."""

    gpu_name: Optional[str] = None
    vram_total_mb: int = 0
    vram_available_mb: int = 0
    ram_total_mb: int
    ram_available_mb: int
    cpu_count: int
    is_apple_silicon: bool = False
    is_nvidia: bool = False
    is_cpu_only: bool = False
    recommended_max_model_gb: float
```

---

## 8. Model Selector API

### 8.1 ModelSelector -- Auto Model Selection

```python
class ModelSelector:
    """Selects optimal Ollama model based on content and hardware."""

    def __init__(
        self,
        model_manager: ModelManager,
        hardware_monitor: HardwareMonitor,
    ) -> None:
        """Initialize ModelSelector.

        Parameters:
            model_manager: For listing available models.
            hardware_monitor: For checking hardware constraints.
        """

    async def select_model(
        self,
        html_content: str,
        task_type: str = "extraction",
        preferred_tier: Optional[str] = None,
    ) -> str:
        """Select best model for a task.

        Parameters:
            html_content: HTML to process.
            task_type: Type of AI task.
            preferred_tier: Optional preferred tier ("fast", "standard",
                           "premium"). Auto-selected if None.

        Returns:
            Model name string (e.g., "dolphincoder:7b").

        Selection Logic:
        - HTML < 50KB + classification -> dolphincoder:7b
        - HTML 50KB-200KB + extraction -> dolphincoder:7b
        - HTML > 200KB + complex -> qwen2.5-coder:32b
        - VRAM < 6GB -> fall back to 7b regardless (dolphincoder:7b or qwen2.5:7b)
        - CPU only -> dolphincoder:7b (or qwen2.5:7b fallback)
        """
```

---

## 9. CLI Command Reference

### 9.1 Command Overview

```bash
phoenix --help                          # Show top-level help
phoenix scrape <url> [options]          # Scrape a single URL
phoenix scrape --real <url> [opts]       # Scrape live site (skip fixtures)
phoenix scrape-batch <urls...> [opts]   # Scrape multiple URLs
phoenix scrape-file <file> [opts]       # Scrape URLs from file
phoenix discover <query> [opts]         # Search-driven site discovery
phoenix architect generate [opts]       # Autonomous adapter generation
phoenix login <platform> [options]      # Interactive browser login
phoenix logout <platform>               # Clear session
phoenix sessions                        # List active sessions
phoenix health                          # Check engine health
phoenix config [get|set|show]           # Manage configuration
phoenix plugins [list|install]          # Manage scraper plugins
phoenix selectors <platform>            # Show selector health
phoenix archive <id>                    # Retrieve archived HTML
phoenix ai-extract <url> [options]      # Force Ollama AI-powered extraction
phoenix ai-status                       # Check Ollama status, GPU, loaded models
phoenix ai-models list                  # List installed Ollama models
phoenix ai-models pull <model>          # Download model from Ollama registry
phoenix ai-models remove <model>        # Delete model from Ollama
phoenix ai-hardware                     # Show GPU/RAM info
phoenix version                         # Show version info
```

---

### 9.2 phoenix scrape

Scrape data from a single URL.

```bash
phoenix scrape <URL> [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `URL` | Yes | Target URL to scrape |

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | stdout | Output file path |
| `--format` | `-f` | `json` | Output format: `json`, `jsonl`, `csv`, `table`, `pretty` |
| `--strategy` | `-s` | auto | Strategy override: `http`, `browser` |
| `--no-archive` | | False | Skip archiving raw HTML |
| `--wait-for` | | None | CSS selector to wait for (browser mode) |
| `--scroll` | | False | Scroll for lazy-loaded content |
| `--screenshot` | | False | Capture browser screenshot |
| `--fields` | | all | Comma-separated fields to extract |
| `--timeout` | `-t` | 30 | Request timeout in seconds |
| `--verbose` | `-v` | False | Show detailed progress and diagnostics |
| `--silent` | | False | Suppress all output except result |
| `--pretty` | `-p` | False | Pretty-print JSON output |
| `--real` | | False | Use live site data instead of recorded fixtures (bypasses test-mode replay) |

**Examples:**

```bash
# Basic scrape
phoenix scrape "https://x.com/elonmusk/status/1871234567890"

# Scrape with browser (for JS-rendered content)
phoenix scrape "https://instagram.com/p/ABC123/" --strategy browser

# Scrape and save to file
phoenix scrape "https://example.com/article" -o result.json --format json

# Scrape with verbose diagnostics
phoenix scrape "https://tiktok.com/@user/video/123" -v

# Scrape specific fields only
phoenix scrape "https://x.com/user/status/123" --fields text,author,likes

# Scrape with screenshot for debugging
phoenix scrape "https://instagram.com/p/ABC123/" --strategy browser --screenshot

# Scrape live site (skip recorded fixtures)
phoenix scrape "https://quotes.toscrape.com/" --real
```

**Output Example (JSON):**
```json
{
  "success": true,
  "url": "https://x.com/user/status/1871234567890",
  "output": {
    "url": "https://x.com/user/status/1871234567890",
    "platform": "x_twitter",
    "content_type": "post",
    "text": "This is the tweet text content...",
    "author": "username",
    "author_url": "https://x.com/username",
    "timestamp": "2025-01-15T10:30:00+00:00",
    "likes": 42,
    "shares": 7,
    "comments": 3,
    "media_urls": [],
    "tags": ["#hashtag", "@mention"],
    "scraped_at": "2025-01-20T14:00:00+00:00",
    "scraping_strategy": "http",
    "selectors_used": [
      "article[data-testid=\"tweet\"] div[lang]",
      "article[data-testid=\"tweet\"] time[datetime]"
    ],
    "ai_assisted": false,
    "archive_id": "a1b2c3d4..."
  },
  "selectors_used": [...],
  "fallback_triggered": false,
  "ai_assisted": false,
  "timing_ms": {
    "fetch": 1250,
    "extract": 85,
    "normalize": 12,
    "archive": 45
  }
}
```

---

### 9.3 phoenix scrape-batch

Scrape multiple URLs concurrently.

```bash
phoenix scrape-batch <URL...> [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `URL...` | Yes | One or more URLs to scrape (space-separated) |

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | stdout | Output file path |
| `--format` | `-f` | `jsonl` | Output format: `json`, `jsonl`, `csv` |
| `--strategy` | `-s` | auto | Strategy override: `http`, `browser` |
| `--max-concurrency` | `-c` | 5 | Maximum concurrent scrapes |
| `--no-archive` | | False | Skip archiving |
| `--timeout` | `-t` | 30 | Per-request timeout |
| `--verbose` | `-v` | False | Show progress |

**Examples:**

```bash
# Scrape multiple URLs
phoenix scrape-batch \
  "https://x.com/user1/status/1" \
  "https://x.com/user2/status/2" \
  "https://instagram.com/p/ABC/" \
  -o results.jsonl --format jsonl -c 3

# Scrape from file (one URL per line)
cat urls.txt | xargs phoenix scrape-batch -o results.json
```

---

### 9.4 phoenix scrape-file

Scrape URLs from a file (one URL per line).

```bash
phoenix scrape-file <FILE> [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `FILE` | Yes | Path to file containing URLs (one per line) |

**Options:** Same as `scrape-batch`.

**Examples:**
```bash
# URLs file
phoenix scrape-file urls.txt -o results.jsonl -c 5 -v
```

---

### 9.4a phoenix discover

Search for candidate sites using a query and rank the resulting URLs.

```bash
phoenix discover "QUERY" [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `QUERY` | Yes | Free-text goal or search query, e.g. "apartments for rent in Cairo" |

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--engine` | `-e` | `duckduckgo` | Search engine backend: `duckduckgo`, `serpapi` |
| `--max-results` | `-n` | 10 | Maximum search results to return |

**Examples:**
```bash
# Discover property listing sites
phoenix discover "apartments for rent in Cairo Egypt"

# Use DuckDuckGo and return top 20 results
phoenix discover "used cars for sale in Dubai" -e duckduckgo -n 20
```

**Output Example (JSON):**
```json
[
  {
    "rank": 0,
    "title": "Quotes to Scrape",
    "url": "https://quotes.toscrape.com/",
    "snippet": "A site with famous quotes for testing scrapers.",
    "engine": "duckduckgo"
  }
]
```

---

### 9.4b phoenix architect generate

Run the PhoenixArchitect autonomous pipeline to discover, inspect, and generate a site-specific adapter.

```bash
phoenix architect generate --goal "GOAL" [OPTIONS]
phoenix architect generate --url "URL" [OPTIONS]
```

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--goal` | `-g` | None | High-level objective; triggers search discovery |
| `--url` | `-u` | None | Single target URL; skips discovery |
| `--engine` | `-e` | `duckduckgo` | Search backend when `--goal` is used |
| `--max-results` | `-n` | 3 | Number of candidate sites to evaluate when `--goal` is used |
| `--max-pages` | | 2 | Maximum listing/detail pages to collect per candidate |
| `--force` | | False | Regenerate even if an adapter already exists |
| `--with-fixtures` | | False | Generate pytest fixtures and a unit test for each adapter |
| `--fixtures-dir` | | `tests/fixtures/html` | Directory for generated HTML fixtures |
| `--tests-dir` | | `tests/unit` | Directory for generated unit tests |

**Examples:**
```bash
# Generate an adapter from a known URL
phoenix architect generate --url "https://quotes.toscrape.com/"

# Discover and generate from a goal
phoenix architect generate -g "find used cars in Dubai" -n 3
```

**Output Artifacts:**
1. `src/phoenix/adapters/generated/<platform>_adapter.py`
2. Summary report printed to stdout
3. When `--with-fixtures` is used:
   - `tests/fixtures/html/<platform>/<page_N>.html`
   - `tests/fixtures/html/<platform>/meta.yaml`
   - `tests/unit/test_<platform>_adapter.py`

---

### 9.4c phoenix architect fixtures

Generate pytest fixtures and a unit test from existing HTML snapshots without re-running exploration.

```bash
phoenix architect fixtures <PLATFORM> --snapshot-dir <DIR> [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `PLATFORM` | Yes | Platform identifier (snake_case) for the fixture set |

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--snapshot-dir` | — | Directory containing `.html` snapshot files |
| `--fixtures-dir` | `tests/fixtures/html` | Directory for generated HTML fixtures |
| `--tests-dir` | `tests/unit` | Directory for generated unit tests |

**Example:**
```bash
phoenix architect fixtures example_site --snapshot-dir ./snapshots/example_site
```

---

### 9.5 phoenix login

Authenticate with a platform via interactive browser login.

```bash
phoenix login <PLATFORM> [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `PLATFORM` | Yes | Platform to login to: `instagram`, `x`, `linkedin`, `facebook`, `tiktok` |

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--headless` | | False | If set, use headless browser (not recommended for login) |
| `--timeout` | `-t` | 300 | Login timeout in seconds |
| `--verbose` | `-v` | False | Show debug output |

**Examples:**
```bash
# Login to Instagram (opens visible browser)
phoenix login instagram

# Login to X/Twitter
phoenix login x

# Login with custom timeout
phoenix login linkedin --timeout 600
```

**Process:**
1. Launch browser pointing to platform login page
2. User manually enters username/password in browser
3. User completes any 2FA/challenge
4. Engine detects successful login via URL redirect
5. Session cookies are captured and encrypted at rest
6. Browser closes, session is ready for scraping

---

### 9.6 phoenix logout

Clear stored session for a platform.

```bash
phoenix logout <PLATFORM>
```

**Examples:**
```bash
phoenix logout instagram
phoenix logout x
```

---

### 9.7 phoenix sessions

List all stored sessions with metadata.

```bash
phoenix sessions [OPTIONS]
```

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--format` | `-f` | `table` | Output format: `table`, `json` |

**Example Output:**
```
Platform    Created At           Expires At           Valid
----------  -------------------  -------------------  -----
instagram   2025-01-15 10:30:00  2025-02-15 10:30:00  Yes
x           2025-01-18 14:22:00  2025-02-18 14:22:00  Yes
linkedin    --                   --                   No
```

---

### 9.8 phoenix health

Check engine health and component status.

```bash
phoenix health [OPTIONS]
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--format` | `-f` | Output format: `table`, `json` |
| `--verbose` | `-v` | Show full diagnostics |

**Example Output:**
```
Component           Status    Details
------------------  --------  ----------------------------------------
Engine              OK        v1.0.0, 7 plugins loaded
HTTP Scraper        OK        httpx v0.27, pool: 20 connections
Browser Scraper     OK        Playwright v1.40, pool: 3/3 available
Selector Engine     OK        7 platforms registered
Instagram Scrapers  OK        selectors v2025.01.15, health: 98%
X/Twitter Scrapers  OK        selectors v2025.01.15, health: 95%
TikTok Scrapers     WARNING   selectors v2025.01.10, 2 degraded
LinkedIn Scrapers   OK        selectors v2025.01.15, health: 100%
Facebook Scrapers   OK        selectors v2025.01.15, health: 92%
YouTube Scrapers    OK        selectors v2025.01.15, health: 100%
Session Manager     OK        2 active sessions
Storage             OK        SQLite: phoenix.db (2.3 MB)
Rate Limiter        OK        6 domains tracked
Ollama AI           DISABLED  Enable with ollama_enabled=true in config
```

---

### 9.9 phoenix config

Manage configuration.

```bash
# Show current configuration
phoenix config show

# Get a specific setting
phoenix config get storage_backend

# Set a setting
phoenix config set rate_limit.requests_per_second 2.0

# Edit config file directly
phoenix config edit
```

---

### 9.10 phoenix plugins

Manage scraper plugins.

```bash
# List loaded plugins
phoenix plugins list

# Show plugin details
phoenix plugins show x_twitter

# Install a plugin from directory
phoenix plugins install ./my_custom_scraper
```

---

### 9.11 phoenix selectors

View and manage selector health.

```bash
# Show selector health for a platform
phoenix selectors x_twitter

# Show all platforms
phoenix selectors --all

# Export selector set
phoenix selectors x_twitter --export selectors.json
```

**Example Output:**
```
Field        Selector                                      Status    Match Rate
-----------  --------------------------------------------  --------  ----------
tweet_text   article[data-testid="tweet"] div[lang]        HEALTHY   99.2%
tweet_text   article div[dir="auto"][data-testid="tweetT... HEALTHY   95.1%
author       article a[role="link"][href^="/"] div[dir=... HEALTHY   98.5%
timestamp    article[data-testid="tweet"] time[datetime]   HEALTHY   99.8%
likes        button[data-testid="like"] span               DEGRADED  72.3%
likes        a[href*="/likes"] span                        HEALTHY   91.0%
```

---

### 9.12 phoenix version

```bash
phoenix version
# Output: Phoenix Engine v1.0.0
```

---

### 9.13 phoenix ai-extract

Force AI-powered extraction using local Ollama, bypassing standard selectors.
Useful for testing Ollama extraction or scraping pages where selectors are known to be broken.

```bash
phoenix ai-extract <URL> [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `URL` | Yes | Target URL to extract using Ollama |

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--model` | `-m` | `dolphincoder:7b` | Ollama model: `dolphincoder:7b`, `qwen2.5:7b`, `qwen2.5-coder:32b` |
| `--temperature` | `-t` | `0.2` | Sampling temperature (0.0-1.0) |
| `--num-ctx` | | `16384` | Context window size |
| `--output` | `-o` | stdout | Output file path |
| `--format` | `-f` | `json` | Output format: `json`, `jsonl` |
| `--fields` | | all | Comma-separated fields to extract |
| `--schema` | `-s` | None | JSON schema file for structured output |
| `--verbose` | `-v` | False | Show Ollama diagnostics (model, inference time, GPU memory) |
| `--no-cache` | | False | Bypass cache for fresh extraction |
| `--strategy` | | `auto` | HTML fetch strategy: `http`, `browser`, `auto` |

**Examples:**

```bash
# Basic AI extraction with default model
phoenix ai-extract "https://x.com/user/status/1871234567890"

# With specific model and verbose output
phoenix ai-extract "https://instagram.com/p/ABC123/" \
  --model qwen2.5:7b \
  --temperature 0.1 \
  --verbose

# Extract specific fields only
phoenix ai-extract "https://example.com/article" \
  --fields title,author,date,content \
  -o article.json

# With custom JSON schema
phoenix ai-extract "https://example.com/product/123" \
  --schema product_schema.json \
  -o product.json

# Use premium model for maximum accuracy
phoenix ai-extract "https://example.com/complex-page" \
  --model qwen2.5-coder:32b \
  --verbose
```

**Output Example (verbose):**
```json
{
  "success": true,
  "url": "https://x.com/user/status/1871234567890",
  "extracted_data": {
    "text": "This is the tweet content...",
    "author": "username",
    "timestamp": "2025-01-15T10:30:00Z",
    "likes": 42,
    "shares": 7
  },
  "confidence": 0.95,
  "model_used": "qwen2.5:7b",
  "inference_time_ms": 2847,
  "gpu_memory_mb": 5120,
  "total_duration_ms": 3420,
  "cached": false
}
```

---

### 9.14 phoenix ai-status

Check Ollama service health, loaded models, GPU usage, and recent inference statistics.

```bash
phoenix ai-status [OPTIONS]
```

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--format` | `-f` | `table` | Output format: `table`, `json` |
| `--verbose` | `-v` | False | Show detailed inference history |

**Example Output:**
```
Ollama Status:          RUNNING
Endpoint:               http://localhost:11434
Default Model:          dolphincoder:7b
Loaded in Memory:       dolphincoder:7b

GPU:                    NVIDIA RTX 4090 (24GB)
VRAM Used:              9.2GB / 24.0GB
VRAM Available:         14.8GB
GPU Temperature:        62C

Installed Models:
  dolphincoder:7b     4.4GB   Q4_0   [default]
  qwen2.5:7b          8.7GB   Q4_K_M
  qwen2.5-coder:32b   19.3GB  Q4_K_M

Recent Inference:
  Last 10 avg latency:  3.2s
  Cache hit rate:       34.2%
  Consecutive Errors:   0
```

---

### 9.15 phoenix ai-models

Manage Ollama models: list, pull, and remove.

#### 9.15.1 phoenix ai-models list

List all installed Ollama models.

```bash
phoenix ai-models list [OPTIONS]
```

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--format` | `-f` | `table` | Output format: `table`, `json` |

**Example Output:**
```
Name                     Size    Quant    VRAM Required    Default
-----------------------  ------  -------  ---------------  -------
qwen2.5:7b         4.4GB   Q4_0     ~4.5GB           
qwen2.5:7b        8.7GB   Q4_K_M   ~9.0GB           *
qwen2.5-coder:32b        19.3GB  Q4_K_M   ~20.0GB          
deepseek-coder-v2:16b    9.8GB   Q4_K_M   ~10.0GB          
```

#### 9.15.2 phoenix ai-models pull

Download a model from the Ollama registry.

```bash
phoenix ai-models pull <MODEL> [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `MODEL` | Yes | Model name to pull (e.g., `qwen2.5:7b`) |

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--verbose` | `-v` | False | Show download progress |

**Examples:**
```bash
# Pull default model
phoenix ai-models pull qwen2.5:7b

# Pull fast model
phoenix ai-models pull qwen2.5:7b

# Pull premium model
phoenix ai-models pull qwen2.5-coder:32b

# Pull alternative model
phoenix ai-models pull deepseek-coder-v2:16b
```

**Example Output:**
```
Pulling qwen2.5:7b...
[████████████████████] 100%  8.7GB / 8.7GB
Model qwen2.5:7b ready.
VRAM required: ~9.0GB
```

#### 9.15.3 phoenix ai-models remove

Delete a model from Ollama to free disk space.

```bash
phoenix ai-models remove <MODEL>
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `MODEL` | Yes | Model name to remove |

**Examples:**
```bash
phoenix ai-models remove qwen2.5-coder:32b
```

---

### 9.16 phoenix ai-hardware

Show GPU and system RAM information for Ollama capacity planning.

```bash
phoenix ai-hardware [OPTIONS]
```

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--format` | `-f` | `table` | Output format: `table`, `json` |

**Example Output (with GPU):**
```
GPU Information:
  Name:                 NVIDIA GeForce RTX 4090
  VRAM Total:           24.0 GB
  VRAM Used:            9.2 GB
  VRAM Available:       14.8 GB
  Temperature:          62 C
  Utilization:          35%

System RAM:
  Total:                64.0 GB
  Available:            42.3 GB
  Used:                 21.7 GB

Ollama Capacity:
  Can run 7b model:     YES  (dolphincoder:7b, ~4.5GB VRAM) [default]
  Can run 7b model:     YES  (qwen2.5:7b, ~4.5GB VRAM) [fallback]
  Can run 32b model:    YES  (qwen2.5-coder:32b, ~20.0GB VRAM)
```

**Example Output (CPU only):**
```
GPU Information:
  No GPU detected. Running in CPU mode.

System RAM:
  Total:                16.0 GB
  Available:            8.4 GB
  Used:                 7.6 GB

Ollama Capacity:
  Can run 7b model:     YES  (slow, ~4.5GB RAM)
  Can run 7b model:    NO   (insufficient RAM)
  Can run 32b model:    NO   (insufficient RAM)

Recommendation: Add a GPU or upgrade RAM for better performance.
```

---

## 10. Plugin Interface Contract

### 10.1 ScraperPlugin ABC

All platform scrapers must implement the `ScraperPlugin` abstract base class. Each plugin is a self-contained unit that brings its own URL patterns, CSS/XPath selector sets, and parsing logic.

```python
class ScraperPlugin(ABC):
    """Abstract base class for all platform scraper plugins.

    To create a new platform scraper:
    1. Subclass ScraperPlugin
    2. Define url_patterns, selector_set, and parse() logic
    3. Place in plugins/ directory or register at runtime
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return plugin metadata.

        Must include: name, version, description, url_patterns,
        primary_strategy, and selector_version.
        """

    @abstractmethod
    def supported_patterns(self) -> list[re.Pattern]:
        """Return list of URL regex patterns this scraper handles.

        Example:
            return [
                re.compile(r"https?://(www\.)?instagram\.com/p/[^/]+"),
                re.compile(r"https?://(www\.)?instagram\.com/reel/[^/]+"),
            ]
        """

    @abstractmethod
    def get_selectors(self) -> SelectorSet:
        """Return the CSS/XPath selector set for this platform.

        The selector set defines how to extract each field from
        the platform's HTML. It includes primary selectors,
        fallback chains, and XPath backups.
        """

    @abstractmethod
    async def parse(
        self,
        html_doc: HTMLDocument,
        selector_engine: SelectorEngine,
    ) -> PlatformData:
        """Parse HTML document and extract structured data.

        This method is called after HTML has been fetched (via HTTP
        or browser). It should use the selector_engine to extract
        fields and perform any platform-specific processing.

        Parameters:
            html_doc: The fetched and parsed HTML document.
            selector_engine: The selector engine for applying CSS/XPath selectors.

        Returns:
            PlatformData with extracted fields.

        Raises:
            ExtractionError: If critical fields cannot be extracted.
        """

    def health_check(self) -> dict[str, Any]:
        """Return plugin health status.

        Optional override. Default returns manifest + selector count.
        """
        return {
            "plugin": self.manifest.name,
            "version": self.manifest.version,
            "selector_version": self.manifest.selector_version,
            "url_patterns": len(self.manifest.url_patterns),
        }
```

### 10.2 PluginManifest

```python
class PluginManifest(BaseModel):
    """Metadata for a scraper plugin. Required for all plugins."""

    name: str = Field(..., description="Plugin identifier (lowercase, snake_case)")
    version: str = Field(..., description="Plugin version (semver)")
    description: str = Field(..., description="Human-readable description")
    author: str = Field(..., description="Plugin author name/email")
    url_patterns: list[str] = Field(..., description="URL regex patterns as strings")
    primary_strategy: ScrapingStrategy = Field(
        ..., description="Preferred: ScrapingStrategy.HTTP or ScrapingStrategy.BROWSER"
    )
    selector_version: str = Field(..., description="Version of CSS selector set (ISO date)")
    requires_auth: bool = Field(False, description="Whether login needed for public data")
    dependencies: list[str] = Field(default_factory=list, description="PyPI dependencies")
    python_version: str = ">=3.11"
```

### 10.3 PlatformData -- Scraper's Output

```python
class PlatformData(BaseModel):
    """Intermediate data format -- extracted from HTML but not yet normalized.

    Each scraper returns PlatformData with platform-specific field names.
    The ContentNormalizer then maps these to the unified UnifiedOutput schema.
    """

    platform: str = Field(..., description="Source platform identifier")
    extraction_confidence: float = Field(
        1.0, ge=0.0, le=1.0,
        description="Confidence in extraction quality"
    )
    raw_fields: dict[str, Any] = Field(
        ...,
        description="Platform-specific extracted fields"
    )
    selector_results: dict[str, SelectorResult] = Field(
        default_factory=dict,
        description="Detailed results for each selector attempt"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extraction metadata (timing, strategy, etc.)"
    )
```

### 10.4 Plugin Registration Example

```python
# my_platform/__init__.py
from phoenix.scrapers.base import ScraperPlugin
from phoenix.scrapers.selectors import SelectorSet, SelectorChain
from phoenix.models import PluginManifest, PlatformData, HTMLDocument
from phoenix.scrapers.selectors import SelectorEngine
import re

class MyPlatformScraper(ScraperPlugin):
    """Scraper for my-platform.com."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="my_platform",
            version="1.0.0",
            description="Scraper for my-platform.com articles and profiles",
            author="developer@example.com",
            url_patterns=[
                r"https?://(www\.)?my-platform\.com/article/[^/]+",
                r"https?://(www\.)?my-platform\.com/user/[^/]+",
            ],
            primary_strategy=ScrapingStrategy.HTTP,
            selector_version="2025.01.15",
        )

    def supported_patterns(self) -> list[re.Pattern]:
        return [re.compile(p) for p in self.manifest.url_patterns]

    def get_selectors(self) -> SelectorSet:
        return SelectorSet(
            platform="my_platform",
            version="2025.01.15",
            selectors={
                "title": SelectorChain(
                    field="title",
                    primary="h1.article-title",
                    fallbacks=["h1", "meta[property='og:title']"],
                    transform="strip",
                ),
                "content": SelectorChain(
                    field="content",
                    primary="div.article-body p",
                    transform="strip",
                ),
            },
            xpath_backups={
                "title": "//h1//text()",
            },
            critical_fields=["title"],
        )

    async def parse(
        self,
        html_doc: HTMLDocument,
        selector_engine: SelectorEngine,
    ) -> PlatformData:
        results = selector_engine.extract_all(html_doc.soup, "my_platform")

        return PlatformData(
            platform="my_platform",
            raw_fields={
                "title": results["title"].value,
                "content": results["content"].value,
            },
            selector_results=results,
            metadata={
                "url": html_doc.url,
                "strategy": html_doc.strategy,
            },
        )

# Register
engine.register_plugin(MyPlatformScraper())
```

### 10.5 Plugin Discovery

Plugins are discovered from:
1. Built-in scrapers: `phoenix.scrapers.*` subpackages
2. Plugin directories: Configured `plugin_dirs` paths
3. Runtime registration: `engine.register_plugin()`

Discovery scans for classes implementing `ScraperPlugin` and validates their manifests.

---

## 11. Configuration Schema

### 11.1 Configuration File (phoenix.toml)

```toml
# Phoenix Engine Configuration
# Place this file at ~/.config/phoenix/phoenix.toml or ./phoenix.toml

[general]
app_name = "Phoenix Engine"
log_level = "INFO"
user_agent = "PhoenixEngine/1.0 (+https://github.com/phoenix/engine; research bot)"

[scraping]
default_timeout = 30
browser_timeout = 60
max_redirects = 5
follow_redirects = true

# Per-platform timeout overrides
[scraping.timeouts]
instagram = 45
tiktok = 45
facebook = 45
x_twitter = 20
linkedin = 30
youtube = 15

[rate_limit]
requests_per_second = 1.0
respect_robots_txt = true

# Per-domain rate limits (requests per second)
[rate_limit.domains]
"x.com" = 0.5
"instagram.com" = 0.3
"tiktok.com" = 0.3
"linkedin.com" = 0.3
"facebook.com" = 0.3
"youtube.com" = 1.0

[browser]
headless = true
pool_size = 3
viewport_width = 1920
viewport_height = 1080
wait_until = "networkidle"

[ai]
enabled = false
base_url = "http://localhost:11434"
default_model = "dolphincoder:7b"
fallback_model = "qwen2.5:7b"
enterprise_model = "qwen2.5-coder:32b"
alternative_model = "deepseek-coder-v2:16b"
temperature_extraction = 0.2
temperature_analysis = 0.5
num_ctx = 16384
timeout = 120.0
max_retries = 2
auto_select_model = true
gpu_layers = null  # Auto-detect if null
keep_alive = "5m"

[ai.cache]
enabled = true
ttl = 3600
backend = "memory"  # "memory" or "disk"
cache_dir = null

# Per-platform AI settings
[ai.platforms.x_twitter]
preferred_model = "dolphincoder:7b"

[ai.platforms.instagram]
preferred_model = "dolphincoder:7b"

[storage]
backend = "sqlite"  # "sqlite" or "json"
database_url = "sqlite:///phoenix.db"
archive_enabled = true
archive_dir = "~/.local/share/phoenix/archive"

[session]
encrypt_sessions = true
# encryption_key loaded from PHOENIX_SESSION_KEY env var

[operational_automation]
data_dir = ".phoenix"                       # Local directory for JSON fallback stores
learning_memory_enabled = true             # Persist per-domain strategy/selector memory
change_detection_enabled = true            # Detect structural drift and selector degradation
change_alert_size_threshold = 0.3          # Fractional HTML size delta that triggers an alert
change_alert_webhook_url = null            # Optional webhook URL for change alerts
```

### 11.2 Environment Variables

All config values can be overridden via environment variables with `PHOENIX_` prefix:

| Variable | Description | Example |
|----------|-------------|---------|
| `PHOENIX_LOG_LEVEL` | Logging level | `DEBUG` |
| `PHOENIX_USER_AGENT` | Custom User-Agent string | `MyBot/1.0` |
| `PHOENIX_REQUESTS_PER_SECOND` | Global rate limit | `2.0` |
| `PHOENIX_BROWSER_HEADLESS` | Browser headless mode | `false` |
| `PHOENIX_OLLAMA_ENABLED` | Enable Ollama AI engine | `true` |
| `PHOENIX_OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `PHOENIX_OLLAMA_DEFAULT_MODEL` | Default Ollama model | `dolphincoder:7b` |
| `PHOENIX_OLLAMA_NUM_CTX` | Context window size | `16384` |
| `PHOENIX_OLLAMA_TIMEOUT` | Inference timeout (seconds) | `120` |
| `PHOENIX_OLLAMA_KEEP_ALIVE` | Model keep-alive duration | `5m` |
| `PHOENIX_STORAGE_BACKEND` | Storage backend | `json` |
| `PHOENIX_SESSION_KEY` | Session encryption key | `base64...` |
| `PHOENIX_DATA_DIR` | Local directory for JSON fallback stores | `.phoenix` |
| `PHOENIX_LEARNING_MEMORY_ENABLED` | Enable domain learning memory | `true` |
| `PHOENIX_CHANGE_DETECTION_ENABLED` | Enable structural drift alerts | `true` |
| `PHOENIX_CHANGE_ALERT_SIZE_THRESHOLD` | HTML size delta threshold | `0.3` |
| `PHOENIX_CHANGE_ALERT_WEBHOOK_URL` | Change-alert webhook URL | — |

---

## 12. Data Output Schema

### 12.1 UnifiedOutput -- Final Output Format

Every scrape produces a `UnifiedOutput` regardless of source platform. This is the contract that consuming applications depend on.

```python
class UnifiedOutput(BaseModel):
    """Standardized output format for all scraped content.

    This is the canonical schema that all platform scrapers ultimately produce.
    Consuming applications can depend on this stable schema regardless of
    whether the source was X, Instagram, TikTok, YouTube, or generic web.
    """

    # Identification
    url: HttpUrl
    platform: str  # "x_twitter", "instagram", "tiktok", "linkedin", "facebook", "youtube", "generic_web"
    content_type: str  # "post", "article", "video", "profile", "comment", "story", "reel", "short"

    # Content
    title: Optional[str] = None
    text: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[HttpUrl] = None
    timestamp: Optional[datetime] = None  # ISO 8601 UTC

    # Engagement (always integers, None if unavailable)
    likes: Optional[int] = None
    shares: Optional[int] = None
    comments: Optional[int] = None
    views: Optional[int] = None

    # Media
    media_urls: list[HttpUrl] = Field(default_factory=list)
    thumbnail_url: Optional[HttpUrl] = None

    # Metadata
    language: Optional[str] = None  # ISO 639-1 code
    tags: list[str] = Field(default_factory=list)  # hashtags, mentions

    # Provenance
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    scraping_strategy: str = "http"  # "http" or "browser"
    selectors_used: list[str] = Field(default_factory=list)
    ai_assisted: bool = False
    archive_id: Optional[str] = None

    # Confidence
    field_confidences: dict[str, float] = Field(default_factory=dict)
    confidence: float = 0.0  # Overall extraction confidence (0.0-1.0)
```

### 12.2 Field Mapping by Platform

| UnifiedOutput Field | X/Twitter Source | Instagram Source | TikTok Source | YouTube Source |
|--------------------|--------------------|--------------------|--------------------|--------------------|
| `text` | tweet text | caption | video description | video description |
| `author` | display name | username | display name | channel name |
| `author_url` | profile URL | profile URL | profile URL | channel URL |
| `timestamp` | `<time datetime>` | `meta[datetime]` | `<time>` | `meta[datePublished]` |
| `likes` | likes count | likes count | likes count | likes count |
| `shares` | retweets | shares | shares | -- |
| `comments` | replies count | comments count | comments count | comments count |
| `views` | impressions | views | play count | view count |
| `media_urls` | image URLs | image/video URLs | video URL | thumbnail |

### 12.3 ScrapingResult -- Operation Result

```python
class ScrapingResult(BaseModel):
    """Complete result of a scraping operation."""

    success: bool
    url: str
    output: Optional[UnifiedOutput] = None
    error: Optional[ScrapingError] = None
    diagnostics: Diagnostics = Field(default_factory=Diagnostics)
    archived_path: Optional[Path] = None
    selectors_used: list[str] = Field(default_factory=list)
    fallback_triggered: bool = False
    ai_assisted: bool = False
    timing_ms: dict[str, float] = Field(default_factory=dict)
    adapter_confidence: Optional[float] = None  # Adapter-level confidence for generated adapters

class ScrapingError(BaseModel):
    """Structured error information."""

    code: str  # Error code (see Section 13)
    message: str  # Human-readable description
    url: str  # URL that failed
    strategy: Optional[str] = None  # Strategy that failed
    selectors_tried: list[str] = Field(default_factory=list)
    http_status: Optional[int] = None
    html_snippet: Optional[str] = None  # Relevant HTML for debugging
    suggested_fix: Optional[str] = None

class Diagnostics(BaseModel):
    """Diagnostic information for debugging."""

    url: str
    platform: Optional[str] = None
    strategy_used: Optional[str] = None
    strategies_attempted: list[str] = Field(default_factory=list)
    selectors_tried: list[str] = Field(default_factory=list)
    selector_health: dict[str, SelectorHealth] = Field(default_factory=dict)
    http_status: Optional[int] = None
    response_headers: dict[str, str] = Field(default_factory=dict)
    html_size_bytes: Optional[int] = None
    timing: dict[str, float] = Field(default_factory=dict)
    retries: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    change_alert: Optional[dict] = None  # Populated when drift is detected
```

---

## 13. Error Codes & Exceptions

### 13.1 Error Code Reference

| Code | Name | HTTP Status | Description | Suggested Fix |
|------|------|-------------|-------------|---------------|
| `SCR_001` | `UnsupportedURL` | -- | No scraper plugin handles this URL | Check URL format or install plugin |
| `SCR_002` | `InvalidURL` | -- | URL is malformed or not HTTP(S) | Check URL syntax |
| `SCR_003` | `EmptyURL` | -- | URL is empty or whitespace only | Provide a valid URL |
| `SCR_010` | `HTTPError` | 4xx/5xx | HTTP request failed | Check URL, retry later |
| `SCR_011` | `TimeoutError` | -- | Request timed out | Increase timeout, check connectivity |
| `SCR_012` | `NetworkError` | -- | DNS or connection failure | Check internet connection |
| `SCR_013` | `RedirectLoop` | -- | Too many redirects | Check URL, increase max_redirects |
| `SCR_014` | `SSLError` | -- | TLS certificate validation failed | Check system clock, certificates |
| `SCR_020` | `BrowserError` | -- | Browser automation failed | Check Playwright installation |
| `SCR_021` | `BrowserTimeout` | -- | Browser navigation timed out | Increase browser_timeout |
| `SCR_022` | `BrowserCrashed` | -- | Browser process crashed | Restart engine |
| `SCR_023` | `ElementNotFound` | -- | CSS selector wait_for not found | Check selector, increase timeout |
| `SCR_030` | `SelectorNotFound` | -- | All selectors failed to match | Page layout changed, run selector update |
| `SCR_031` | `CriticalFieldsMissing` | -- | Required fields could not be extracted | Try browser strategy, check login |
| `SCR_032` | `PageChanged` | -- | Page structure differs from expected | Selectors need updating |
| `SCR_040` | `Blocked` | 403 | Access blocked (403 Forbidden) | Increase delays, check robots.txt |
| `SCR_041` | `RateLimited` | 429 | Rate limited by target (429) | Wait and retry with longer delays |
| `SCR_042` | `CloudflareBlocked` | 403 | Cloudflare challenge detected | Try browser strategy with stealth |
| `SCR_050` | `NormalizationError` | -- | Extracted data failed validation | Check scraper output format |
| `SCR_060` | `SessionExpired` | -- | Authenticated session expired | Re-run phoenix login |
| `SCR_061` | `LoginRequired` | -- | Platform requires login for this content | Use phoenix login first |
| `SCR_070` | `PluginError` | -- | Scraper plugin failed to load | Check plugin dependencies |
| `SCR_080` | `AIAssistFailed` | -- | AI fallback extraction failed | Check Ollama status, verify model |
| `OLLAMA_001` | `OllamaError` | -- | Ollama inference failed | Check Ollama logs; try smaller model |
| `OLLAMA_002` | `OllamaNotRunning` | -- | Ollama server not reachable | Start Ollama: `ollama serve` |
| `OLLAMA_003` | `OllamaModelNotFound` | -- | Requested model not pulled | Pull model: `ollama pull <model>` |
| `OLLAMA_004` | `OllamaOutOfMemory` | -- | GPU/CPU out of memory | Try smaller model; unload others |
| `OLLAMA_005` | `OllamaTimeout` | -- | Local inference timed out | Increase timeout; reduce context |
| `OLLAMA_006` | `OllamaJSONParse` | -- | Response parsing failed | Retry; check model output quality |
| `SCR_090` | `ConfigError` | -- | Invalid configuration | Check phoenix.toml syntax |
| `SCR_099` | `UnknownError` | -- | Unclassified error | Check diagnostics, report issue |

### 13.2 Exception Hierarchy

```python
# Base exception
class PhoenixError(Exception):
    """Base exception for all Phoenix Engine errors."""
    code: str = "SCR_099"

# URL errors
class URLError(PhoenixError): code = "SCR_002"
class UnsupportedURLError(URLError): code = "SCR_001"
class EmptyURLError(URLError): code = "SCR_003"

# HTTP errors
class HTTPFetchError(PhoenixError):
    """HTTP request failed."""
    code = "SCR_010"
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        self.status_code = status_code
        super().__init__(message)

class TimeoutError(HTTPFetchError): code = "SCR_011"
class NetworkError(HTTPFetchError): code = "SCR_012"

# Browser errors
class BrowserError(PhoenixError): code = "SCR_020"
class BrowserTimeoutError(BrowserError): code = "SCR_021"
class BrowserCrashedError(BrowserError): code = "SCR_022"

# Extraction errors
class ExtractionError(PhoenixError): code = "SCR_030"
class SelectorNotFoundError(ExtractionError): code = "SCR_030"
class CriticalFieldsMissingError(ExtractionError): code = "SCR_031"
class PageChangedError(ExtractionError): code = "SCR_032"

# Blocking errors
class BlockedError(PhoenixError):
    """Access blocked by target site."""
    code = "SCR_040"
    def __init__(self, message: str, http_status: int) -> None:
        self.http_status = http_status
        super().__init__(message)

class RateLimitedError(BlockedError): code = "SCR_041"

# Session errors
class SessionError(PhoenixError): code = "SCR_060"
class SessionExpiredError(SessionError): code = "SCR_060"
class LoginRequiredError(SessionError): code = "SCR_061"

# Plugin errors
class PluginError(PhoenixError): code = "SCR_070"

# AI errors
class AIAssistError(PhoenixError): code = "SCR_080"

# Ollama errors
class OllamaError(PhoenixError):
    """Base error for Ollama local inference issues."""
    code = "OLLAMA_001"
    def __init__(self, message: str, http_status: Optional[int] = None) -> None:
        self.http_status = http_status
        super().__init__(message)

class OllamaNotRunningError(OllamaError):
    """Ollama server is not running or not reachable."""
    code = "OLLAMA_002"
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        super().__init__(
            f"Ollama is not running at {base_url}. "
            "Start it with: ollama serve"
        )

class OllamaModelNotFoundError(OllamaError):
    """Requested model has not been pulled."""
    code = "OLLAMA_003"
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        super().__init__(
            f"Model '{model_name}' not found. "
            f"Pull it with: ollama pull {model_name}"
        )

class OllamaOutOfMemoryError(OllamaError):
    """GPU or system RAM exhausted during inference."""
    code = "OLLAMA_004"
    def __init__(self, model_name: str, vram_required_gb: float, vram_available_gb: float) -> None:
        self.model_name = model_name
        self.vram_required_gb = vram_required_gb
        self.vram_available_gb = vram_available_gb
        super().__init__(
            f"Out of memory loading '{model_name}'. "
            f"Required: {vram_required_gb:.1f}GB, Available: {vram_available_gb:.1f}GB. "
            "Try a smaller model: dolphincoder:7b requires ~4.5GB."
        )

class OllamaTimeoutError(OllamaError):
    """Local inference request timed out."""
    code = "OLLAMA_005"
    def __init__(self, timeout: float, model_name: str) -> None:
        self.timeout = timeout
        self.model_name = model_name
        super().__init__(
            f"Ollama inference timed out after {timeout}s "
            f"with model '{model_name}'. "
            "Try increasing timeout or reducing context window."
        )

class OllamaJSONParseError(OllamaError):
    """Failed to parse Ollama response as valid JSON."""
    code = "OLLAMA_006"
    def __init__(self, message: str, raw_response: Optional[str] = None) -> None:
        self.raw_response = raw_response
        super().__init__(message)

# Config errors
class ConfigurationError(PhoenixError): code = "SCR_090"
```

### 13.3 Error Handling in Client Code

```python
from phoenix import PhoenixEngine
from phoenix.exceptions import *

async with PhoenixEngine() as engine:
    result = await engine.scrape("https://x.com/user/status/123")

    if not result.success:
        error = result.error
        match error.code:
            case "SCR_030":  # SelectorNotFound
                print(f"Page layout changed. Selectors tried: {error.selectors_tried}")
                # Try with browser strategy
                result = await engine.scrape(url, strategy=ScrapingStrategy.BROWSER)
            case "SCR_040":  # Blocked
                print(f"Access blocked (HTTP {error.http_status}). Will retry later.")
            case "SCR_060":  # SessionExpired
                print("Session expired. Please run: phoenix login x")
            case "OLLAMA_002":  # OllamaNotRunning
                print("Ollama is not running. Start it with: ollama serve")
            case "OLLAMA_004":  # OllamaOutOfMemory
                print("Out of GPU memory. Try: phoenix ai-hardware")
            case _:
                print(f"Error {error.code}: {error.message}")
                print(f"Suggested fix: {error.suggested_fix}")
```

---

## 14. Type Summary

### 14.1 Core Type Aliases

```python
from typing import TypeAlias

PlatformName: TypeAlias = str  # "x_twitter", "instagram", etc.
URLPattern: TypeAlias = re.Pattern
SelectorString: TypeAlias = str  # CSS selector like "div.class > span"
XPathString: TypeAlias = str  # XPath like "//div[@class='x']//text()"
FieldName: TypeAlias = str  # "tweet_text", "author", etc.
ArchiveID: TypeAlias = str  # SHA-256 hash string
```

### 14.2 Enum Definitions

```python
from enum import Enum

class ScrapingStrategy(str, Enum):
    """Available scraping strategies."""
    HTTP = "http"
    BROWSER = "browser"

class OutputFormat(str, Enum):
    """CLI output formats."""
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    TABLE = "table"
    PRETTY = "pretty"

class ContentType(str, Enum):
    """Types of content that can be scraped."""
    POST = "post"
    ARTICLE = "article"
    VIDEO = "video"
    PROFILE = "profile"
    COMMENT = "comment"
    STORY = "story"
    REEL = "reel"
    SHORT = "short"
```

---

## 15. Quick Reference Card

### Library API (Python)

```python
from phoenix import PhoenixEngine, ScrapingStrategy, ScrapingOptions

# Initialize
engine = PhoenixEngine()

# Basic scrape
result = await engine.scrape("https://x.com/user/status/123")

# With options
result = await engine.scrape(
    "https://instagram.com/p/ABC/",
    strategy=ScrapingStrategy.BROWSER,
    options=ScrapingOptions(wait_for="article", scroll=True),
)

# Batch scrape
results = await engine.scrape_batch(urls, max_concurrency=5)

# Login for authenticated content
session = await engine.login("instagram")  # Opens browser for interactive login

# Register custom scraper
engine.register_plugin(MyScraper())

# Cleanup
await engine.close()
```

### CLI Quick Reference

```bash
# Single URL
phoenix scrape <URL> [-o file] [-f json|jsonl|csv|table] [-s http|browser] [-v]

# Batch
phoenix scrape-batch <URL...> [-c concurrency] [-o file]
phoenix scrape-file <file.txt> [-c concurrency] [-o file]

# Discovery & autonomous adapter generation
phoenix discover -q "<query>" [-e duckduckgo|google] [-n max_results]
phoenix architect -g "<goal>" [--auto-approve] [-n max_results]

# Auth
phoenix login <platform>          # Interactive browser login
phoenix logout <platform>         # Clear session
phoenix sessions                  # List sessions

# System
phoenix health                    # Check health + selector status + Ollama status
phoenix selectors <platform>      # View selector health
phoenix config show               # Show configuration
phoenix version                   # Show version

# Ollama AI
phoenix ai-extract <url> [-m model] [-v]       # Force AI extraction
phoenix ai-status                              # Check Ollama + GPU status
phoenix ai-models list                         # List installed models
phoenix ai-models pull <model>                 # Download model
phoenix ai-models remove <model>               # Delete model
phoenix ai-hardware                            # Show GPU/RAM info
```

### Ollama Setup Quick Start

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama
ollama serve

# 3. Pull models (in another terminal)
ollama pull dolphincoder:7b
ollama pull qwen2.5:7b

# 4. Verify it works
ollama run dolphincoder:7b "Say hello"

# 5. Enable in Phoenix
cat >> phoenix.toml << 'EOF'
[ai]
enabled = true
EOF

# 6. Check status
phoenix ai-status
phoenix ai-hardware
```
