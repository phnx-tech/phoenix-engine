# Phoenix Engine -- Pure Web Scraping Architecture

**Version:** 2.0.0
**Date:** 2025-01-20
**Status:** Authoritative Scraping-Only Specification
**Audience:** AI Development Agents (Kimi Code), Senior Engineers, Technical Leads
**Constraint:** NO OFFICIAL SOCIAL MEDIA APIs ARE EVER USED. All data is extracted from raw HTML via HTTP requests or headless browser rendering.

---

## 1. System Overview

### 1.1 Purpose

Phoenix Engine is a universal **pure web scraping engine** built in Python. It extracts clean, structured data from websites and social media platforms through raw HTML parsing and headless browser automation. It operates as both a command-line utility and an importable Python library, designed for developers, researchers, and data analysts who need reliable, ethical, and programmatic access to public web content.

The core principle is absolute: **we never use official APIs from Instagram, X/Twitter, TikTok, LinkedIn, Facebook, YouTube, or any other platform.** All data collection is performed through:
- Direct HTTP requests with HTML parsing (BeautifulSoup4, lxml, cssselect)
- Headless browser automation (Playwright) for JavaScript-rendered pages
- CSS selectors, XPath expressions, and regex patterns to extract data from raw HTML
- Ethical rate limiting and transparent user-agent identification

The engine implements a **Route --> Fetch HTML --> Parse --> Extract --> Normalize --> Deliver** pipeline. A URL is routed to the appropriate platform scraper, raw HTML is fetched via HTTP or browser, structured content is extracted using CSS selectors and XPath, and results are delivered in a standardized format regardless of source platform.

### 1.2 Design Philosophy

**Scraping-Only by Principle**
No official API keys, no API client libraries (no `instagrapi`, no `tweepy`, no `yt-dlp` API mode), no rate-limit bypass techniques. Every byte of data comes from parsing raw HTML responses rendered by servers or browsers. This ensures the engine works anywhere, for any public page, without requiring platform approval or API access tiers.

**HTML-First Extraction**
The primary extraction mechanism is CSS selector and XPath-based parsing of HTML documents. Each platform scraper maintains a curated selector set that maps HTML elements to structured fields. When selectors fail due to layout changes, fallback selector chains and AI-assisted pattern recognition take over.

**Modular by Design**
Every component is self-contained with explicit interface contracts. Components communicate only through well-defined data structures. No component may reach into another component's internal state. This modularity enables independent development, testing, and replacement of any subsystem.

**Extensible by Default**
The platform scraper system is built on a plugin architecture. New platforms are added without modifying core code. A platform scraper plugin is a Python package implementing the `ScraperPlugin` abstract base class, registering URL patterns and CSS/XPath selector sets. The core engine discovers, registers, and orchestrates plugins at runtime.

**Ethical-by-Default**
All operations respect robots.txt, implement polite rate limiting, identify themselves with transparent user-agent strings, and collect only publicly accessible data. No CAPTCHA bypass, no account automation, no private data access, no impersonation. Every scraping action generates an immutable audit trail.

**Fail-Safe and Transparent**
When primary selectors fail (due to page layout changes), the engine automatically attempts fallback selector chains, then alternative parsing strategies, and finally AI-assisted pattern recognition. If all strategies exhaust, the failure is captured with full diagnostic context -- HTML snippet, attempted selectors, stack traces, and suggested resolution.

**Async-First**
All I/O-bound operations use `asyncio` and `async`/`await` patterns. This maximizes throughput for batch operations, enables concurrent scraping from multiple sources, and keeps the CLI responsive during long-running browser automation tasks.

### 1.3 Core Scraping Flow

```
+---------+    +----------+    +-----------+    +----------+    +---------+
|   URL   |--->|  Router  |--->|   Fetch   |--->|  Parse   |--->| Deliver |
| Receive |    | + Select |    |  HTML via |    | + Extract|    |  Output |
+---------+    | Strategy |    | HTTP/Browser   | Selectors|    +---------+
               +----------+    +-----------+    +----------+
                                        |
                                        v
                               +------------------+
                               | Fallback Chain:  |
                               | 1. Alt selectors |
                               | 2. XPath backup  |
                               | 3. AI pattern    |
                               |    recognition   |
                               +------------------+
```

1. **Receive**: URL is passed via CLI argument or library API call.
2. **Route + Select Strategy**: `URLRouter` matches the URL to a platform scraper. `StrategySelector` determines whether to use direct HTTP or headless browser based on URL patterns, JavaScript requirements, and configuration.
3. **Fetch HTML**: The selected scraping engine (HTTP or Browser) fetches the raw HTML document from the target URL.
4. **Parse + Extract**: `HTMLExtractor` parses the HTML using BeautifulSoup/lxml and applies CSS selectors/XPath expressions registered by the platform scraper to extract structured data.
5. **Normalize**: `ContentNormalizer` transforms extracted data into the `UnifiedOutput` schema with consistent types and formats.
6. **Deliver**: Results are returned as typed Python objects or serialized to JSON. `SourceArchiver` preserves the raw HTML source for audit.

### 1.4 Scope Boundaries

**In Scope:**
- Publicly accessible web pages and social media content via HTML scraping
- Platforms: Instagram, X/Twitter, TikTok, LinkedIn, Facebook, YouTube, Generic Web
- Plugin-based extension for additional platforms (each plugin brings its own selectors)
- Session management (cookies) for authenticated public data access via browser
- Source archiving and audit logging of all scraped HTML
- AI-assisted selector generation for unknown or changed page structures
- Selector versioning and fallback chains for resilience against layout changes

**Out of Scope:**
- Official APIs from any platform (Instagram API, X API, etc.)
- API client libraries (`instagrapi`, `tweepy`, etc.)
- CAPTCHA solving or bypass mechanisms
- Private data, direct messages, or restricted content
- Account creation or automated registration
- Distributed/scraping-at-scale infrastructure (future consideration)
- Real-time streaming data collection

---

## 2. Architecture Diagram

### 2.1 Six-Layer Scraping Architecture

Phoenix Engine is organized into six architectural layers, each with a single, well-defined responsibility. Dependencies flow downward -- a layer may depend only on layers below it, never above.

```
+===========================================================================+
|  LAYER 1 -- INTERFACES                                                    |
|  +---------------------+  +---------------------+                       |
|  |   CLI Module        |  |   Library API       |                       |
|  |   (Typer)           |  |   (Python Package)  |                       |
|  +---------------------+  +---------------------+                       |
+===========================================================================+
|  LAYER 2 -- ORCHESTRATION                                                 |
|  +-------------+  +------------------+  +-----------------+              |
|  | URL Router  |  | Strategy Selector|  |Pipeline Controller|             |
|  +-------------+  +------------------+  +-----------------+              |
+===========================================================================+
|  LAYER 3 -- SCRAPING ENGINES                                              |
|  +----------------+ +------------------+ +-------------------+           |
|  | DirectCollector| | BrowserCollector | | Selector Engine   |           |
|  | (HTTP/httpx +  | | (Playwright      | | (CSS/XPath mgmt,  |           |
|  |  BeautifulSoup)| |  + BrowserPool,  | |  fallback chains) |           |
|  | strategy `http`| |  stealth config) | |                   |           |
|  +----------------+ +------------------+ +-------------------+           |
+===========================================================================+
|  LAYER 4 -- PLATFORM SCRAPERS                                             |
|  +--------+ +--------+ +--------+ +----------+ +----------+ +----------+|
|  |Insta-  | |   X    | | TikTok | | LinkedIn | | Facebook | | YouTube  ||
|  |gramScraper| |Scraper | |Scraper | | Scraper  | | Scraper  | | Scraper  ||
|  +--------+ +--------+ +--------+ +----------+ +----------+ +----------+|
|  +----------+ +-------------------------------------------------------+   |
|  | Generic  | | Plugin Loader -- discovers and registers scraper      |   |
|  | Web      | | plugins at runtime, each with URL patterns + selectors|   |
|  | Scraper  | +-------------------------------------------------------+   |
|  +----------+                                                             |
+===========================================================================+
|  LAYER 5 -- PROCESSING                                                    |
|  +--------------+ +--------------+ +--------------------+ +--------------+  |
|  | HTML Extractor| |  Content     | |  Ollama AI Engine  | |Source Archiver|  |
|  | (BeautifulSoup| |  Normalizer  | |  (HTML parsing,    | |(raw HTML      |  |
|  |  lxml)        | |              | |   selector repair, | |  storage)    |  |
|  +--------------+ +--------------+ |   classification,  | +--------------+  |
|                                     |   entity resolution|                   |
|                                     |   model mgmt,      |                   |
|                                     |   hardware monitor)|                   |
|                                     +--------------------+                   |
+===========================================================================+
|  LAYER 6 -- INFRASTRUCTURE                                                |
|  +--------------+ +----------+ +--------------+ +----------+ +---------+|
|  |Session Manager| | Storage  | |Rate Controller| | Config   | | Audit   ||
|  | (cookie jar,  | |(SQLite/  | | (token bucket | | Manager  | | Logger  ||
|  |  auth state)  | |  JSON)   | | + robots.txt) | |(Pydantic | |         ||
|  |               | |          | |               | | Settings)| |         ||
|  +--------------+ +----------+ +--------------+ +----------+ +---------+|
+===========================================================================+
```

### 2.2 Layer Responsibilities

| Layer | Name | Responsibility |
|-------|------|----------------|
| 1 | Interfaces | User-facing entry points -- CLI commands and Python library API |
| 2 | Orchestration | Route URLs to scrapers, select HTTP vs Browser strategy, manage pipeline execution |
| 3 | Scraping Engines | Execute HTTP requests or browser automation; manage CSS/XPath selector fallback chains |
| 4 | Platform Scrapers | Platform-specific HTML extraction -- curated selector sets, URL pattern matching |
| 5 | Processing | Transform raw extracted HTML data into unified output, archive HTML sources, Ollama AI-powered extraction, selector repair, content classification, model management, hardware monitoring |
| 6 | Infrastructure | Cross-cutting concerns -- cookie/auth sessions, storage, rate limiting, config, audit logging |
| 7 | PhoenixArchitect | Autonomous adapter generation: Planner → Researcher → Explorer → Inspector → Coder → Critic; discovers sites, collects snapshots, and generates validated Phoenix adapters |

### 2.2a PhoenixArchitect Layer

**PhoenixArchitect** is a cross-layer autonomous agent module that sits alongside the core pipeline. It accepts a natural-language scraping goal, discovers candidate sites via DuckDuckGo/SerpAPI search dorks, explores result pages with the `BrowserCollector` (handling scroll and numbered pagination), analyzes collected HTML with the local Ollama model, generates a Phoenix adapter module, validates it against the collected snapshots before registering it with priority over the generic fallback, and falls back to a deterministic template generator when the LLM Coder cannot reach the score threshold. It is implemented by the `PhoenixArchitect` controller (`phoenix.architect`) and exposed through the `phoenix discover` and `phoenix architect generate` CLI commands.

### 2.2b Operational Automation Layer

The **Operational Automation** layer adds self-improving, observability, and test-automation capabilities to the engine:

- **`DomainMemory`** (`phoenix.processing.domain_memory`): persists per-domain strategy success (HTTP vs browser) and selector match rates via the configured `StorageBackend`, falling back to a local JSON file under `data_dir`. `StrategySelector` loads persisted memory when choosing a strategy, so the engine improves across restarts.
- **`ChangeDetector`** (`phoenix.intelligence.change_detector`): compares each successful scrape against a stored structural baseline (DOM skeleton fingerprint, selector snapshot, critical-field hash, HTML size). When structural drift or selector degradation is detected, it returns a `ChangeAlert` that is attached to `Diagnostics` and logged.
- **`AuditLogger`** (`phoenix.infrastructure.audit_logger`): emits structured JSON audit events and persists `ChangeAlert`s through storage when available.
- **`FixtureGenerator`** (`phoenix.architect.fixture_generator`): turns `BrowserExplorer` snapshots into pytest fixtures (`tests/fixtures/html/<platform>/`) plus a generated adapter unit test (`tests/unit/test_<platform>_adapter.py`), including a `meta.yaml` with expected field metadata.

These components are wired into `PipelineController` and `PhoenixEngine` and are enabled by default; they degrade gracefully when storage is not configured.

### 2.3 Inter-Layer Communication

Communication between layers uses explicit data contracts defined as Pydantic models. No layer passes raw dicts or untyped data upward. Every cross-layer call is typed, documented, and validated.

```python
# Layer communication contract example
class PipelineInput(BaseModel):
    """Input passed from Layer 2 (Orchestration) to Layer 3 (Scraping)."""
    url: HttpUrl
    platform: str
    scraping_strategy: ScrapingStrategy
    session: Optional[Session] = None
    options: ScrapingOptions = Field(default_factory=ScrapingOptions)

class PipelineOutput(BaseModel):
    """Output returned from Layer 5 (Processing) to Layer 2 (Orchestration)."""
    result: Optional[UnifiedOutput] = None
    diagnostics: Diagnostics
    archived_path: Optional[Path] = None
    selectors_used: list[str] = Field(default_factory=list)
```

---

## 3. Component Specifications

### 3.1 Layer 1 -- Interfaces

#### 3.1.1 CLI Module (`phoenix.cli`)

**Purpose:** Provides the command-line interface for Phoenix Engine using Typer. All user-facing CLI commands are defined here.

**Responsibilities:**
- Define and register CLI commands and subcommands
- Parse and validate command-line arguments
- Load configuration and initialize the engine
- Format and display output (JSON, table, or human-readable)
- Handle CLI-specific error presentation

**Dependencies:** `PhoenixEngine` (Layer 2), `Config` (Layer 6)

**Dependents:** None (top-level entry point)

**Interface Contract:**
```python
# Entry point: phoenix/__main__.py
def main() -> None: ...

# Core CLI app
app = typer.Typer(name="phoenix", help="Universal pure web scraping engine")

@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL to scrape data from"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: OutputFormat = typer.Option(OutputFormat.json, "--format", "-f"),
    strategy: Optional[ScrapingStrategy] = typer.Option(None, "--strategy", "-s"),
    archive: bool = typer.Option(True, "--archive/--no-archive"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None: ...

@app.command()
def discover(
    query: str = typer.Argument(..., help="Search query describing the target data"),
    engine: str = typer.Option("duckduckgo", "--engine", help="Search backend: duckduckgo or serpapi"),
    max_results: int = typer.Option(10, "--max-results", help="Maximum result URLs to return"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None: ...

@app.command()
def architect(
    goal: str = typer.Argument(..., help="Natural-language scraping goal"),
    max_pages: int = typer.Option(5, "--max-pages", help="Maximum pages to explore per site"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Directory for generated adapter"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-approve non-destructive agent steps"),
) -> None: ...
```

**Key Modules:**
- `phoenix/cli/main.py` -- Typer app definition and command registration
- `phoenix/cli/formatters.py` -- Output formatting (JSON, table, pretty-print)
- `phoenix/cli/utils.py` -- CLI utilities (config loading, error handling)

---

#### 3.1.2 Library API Module (`phoenix.engine`)

**Purpose:** Provides the programmable Python interface. All public API classes are importable from the `phoenix` package root.

**Responsibilities:**
- Expose a clean, typed Python API for embedding in other applications
- Manage engine lifecycle (init --> use --> shutdown)
- Provide synchronous and asynchronous entry points
- Resource cleanup (browser contexts, connection pools, cookie sessions)

**Dependencies:** `PipelineController`, `Config`, `PluginLoader`

**Dependents:** CLI Module, user applications

**Interface Contract:**
```python
# Primary public API
from phoenix import PhoenixEngine, UnifiedOutput, ScrapingResult

engine = PhoenixEngine(config=Config())
result: ScrapingResult = await engine.scrape("https://example.com/post/123")
```

**Key Classes:**
- `PhoenixEngine` -- Main engine class, public API entry point

---

### 3.2 Layer 2 -- Orchestration

#### 3.2.1 URL Router (`phoenix.router`)

**Purpose:** Analyzes input URLs and routes them to the appropriate platform scraper based on domain and path pattern matching.

**Responsibilities:**
- Parse and normalize input URLs
- Match URLs against registered platform scraper URL patterns (regex)
- Return the matching platform scraper identifier
- Validate URL scheme (http/https only)
- Reject malformed or unsupported URLs with descriptive errors

**Dependencies:** `PluginLoader` (to get URL patterns), `ScraperPlugin`

**Dependents:** `PipelineController`

**Interface Contract:**
```python
class URLRouter:
    def __init__(self, plugin_loader: PluginLoader) -> None: ...

    async def route(self, url: str) -> str:
        """Return platform scraper identifier for the given URL.

        Raises:
            UnsupportedURLError: If no scraper plugin matches the URL.
        """
        ...

    def get_scraper_for_domain(self, domain: str) -> Optional[str]: ...
```

**Router Fix**: `URLRouter` prioritizes registered plugin adapters (including AI-generated adapters persisted to `src/phoenix/adapters/generated/`) before falling back to the generic web scraper. This ensures that site-specific adapters take precedence over the generic fallback for matching URL patterns.

**Key Class:** `URLRouter`

---

#### 3.2.2 Strategy Selector (`phoenix.strategy_selector`)

**Purpose:** Determines the optimal scraping strategy (HTTP vs Browser) for a given URL and platform.

**Responsibilities:**
- Evaluate URL characteristics (JavaScript rendering needs, single-page app indicators)
- Check cookie session availability (authenticated sessions enable better data)
- Respect user override (`--strategy` flag)
- Apply platform scraper preferences (e.g., Instagram needs browser)
- Return a ranked list of scraping strategies (primary + fallbacks)

**Dependencies:** `Config`, `SessionManager`, `ScraperPlugin`

**Dependents:** `PipelineController`

**Interface Contract:**
```python
class StrategySelector:
    def __init__(
        self,
        config: Config,
        session_manager: SessionManager,
    ) -> None: ...

    async def select_strategy(
        self,
        url: str,
        platform: str,
        user_override: Optional[ScrapingStrategy] = None,
    ) -> StrategySelection:
        """Return prioritized scraping strategy.

        Returns:
            StrategySelection with primary strategy (HTTP or Browser) and fallback chain.
        """
        ...
```

**Key Class:** `StrategySelector`, `StrategySelection`

---

#### 3.2.3 Pipeline Controller (`phoenix.pipeline`)

**Purpose:** Orchestrates the entire scraping pipeline from URL input to output delivery.

**Responsibilities:**
- Coordinate the sequential execution of pipeline stages
- Manage fallback chains -- try primary strategy, then fallbacks
- Handle errors at each stage, deciding whether to retry or fail
- Collect diagnostics from every stage (HTTP status, selectors tried, timing)
- Return a `ScrapingResult` with success/failure, output, and diagnostics
- Execute AI-assisted extraction as a final fallback when all selectors fail

**Dependencies:** `URLRouter`, `StrategySelector`, HTTP Scraper, Browser Scraper, `HTMLExtractor`, `ContentNormalizer`, `SourceArchiver`, `AuditLogger`

**Dependents:** `PhoenixEngine`, CLI Module

**Interface Contract:**
```python
class PipelineController:
    def __init__(
        self,
        router: URLRouter,
        strategy_selector: StrategySelector,
        http_scraper: HTTPScraper,
        browser_scraper: BrowserScraper,
        html_extractor: HTMLExtractor,
        normalizer: ContentNormalizer,
        archiver: SourceArchiver,
        ai_assistant: Optional[AIAssistant] = None,
        audit_logger: AuditLogger = ...,  # injected
    ) -> None: ...

    async def execute(self, url: str, options: ScrapingOptions) -> ScrapingResult:
        """Execute the full scraping pipeline for a single URL."""
        ...

    async def execute_batch(
        self,
        urls: list[str],
        options: ScrapingOptions,
        max_concurrency: int = 5,
    ) -> list[ScrapingResult]:
        """Execute pipeline for multiple URLs with concurrency control."""
        ...
```

**Key Class:** `PipelineController`

---

### 3.2.4 PhoenixArchitect Controller (`phoenix.architect`)

**Purpose:** Autonomous AI agent that discovers target websites, explores their page structures, and generates ready-to-use Phoenix adapter plugins from real HTML. It is the implementation of the **Adapter Auto-Generation** capability and operates as a cross-layer orchestrator that drives search, browser exploration, LLM analysis, code generation, and validation.

**Responsibilities:**
- Accept a natural-language scraping goal (e.g., "scrape Egypt property listings")
- Build and execute search queries to discover candidate URLs (Researcher role)
- Visit candidate URLs with the browser or HTTP scraper and capture page snapshots (Explorer role)
- Detect and handle pagination / infinite scroll, respecting `max-pages`
- Analyze collected HTML with the local Ollama engine to classify site type and identify data fields (Inspector role)
- Generate a Phoenix adapter module (URL patterns, selectors, normalizer) via the local LLM (Coder role)
- Validate the generated adapter against collected snapshots and retry if coverage is insufficient (Critic role)
- Register the validated adapter with the plugin registry so it is prioritized over the generic fallback
- Provide CLI commands `phoenix discover` and `phoenix architect`

**Agent Roles:**
| Role | Responsibility |
|------|----------------|
| **Planner** | Decomposes the user goal into a multi-step JSON plan and tracks execution state |
| **Researcher** | Builds dork-style queries and calls DuckDuckGo / SerpAPI to collect candidate URLs |
| **Explorer** | Navigates discovered URLs, handles scroll/pagination, and stores HTML snapshots |
| **Inspector** | Uses Ollama to classify site type and propose fields/selectors from snapshots |
| **Coder** | Generates adapter Python code (class, patterns, selectors, normalizer) from Inspector output |
| **Critic** | Runs generated adapter against snapshots, measures field coverage, and requests fixes |

**Dependencies:** `URLRouter`, `StrategySelector`, `HTTPScraper`, `BrowserScraper`, `HTMLExtractor`, `OllamaAIEngine`, `PluginLoader`, `SourceArchiver`

**Dependents:** CLI Module (`phoenix discover`, `phoenix architect`)

**Interface Contract:**
```python
class PhoenixArchitect:
    """Autonomous adapter generation agent."""

    async def discover(
        self,
        query: str,
        engine: str = "duckduckgo",
        max_results: int = 10,
    ) -> list[SearchResult]: ...

    async def architect(
        self,
        goal: str,
        max_pages: int = 5,
        auto_approve: bool = False,
    ) -> AdapterGenerationResult: ...
```

---

### 3.3 Layer 3 -- Scraping Engines

#### 3.3.1 HTTP Scraper (`phoenix.scrapers.http`)

**Purpose:** Fast, lightweight scraping using asynchronous HTTP requests with HTML parsing via BeautifulSoup4 and lxml. Best for static pages and platforms that return meaningful HTML server-side.

**Responsibilities:**
- Send HTTP GET/POST requests via `httpx`
- Handle headers, cookies, redirects with transparent user-agent
- Parse response HTML using BeautifulSoup4 or lxml for fast structured extraction
- Return raw HTML document with metadata (status, headers, timing)
- Implement connection pooling and keep-alive
- Follow redirects up to configured limit

**Dependencies:** `httpx.AsyncClient`, `RateLimiter`, `Config`, `beautifulsoup4`, `lxml`

**Dependents:** `PipelineController`

**Notes:** In CLI configuration and older code this component is sometimes referred to as `DirectCollector` or the `http` strategy. The current implementation is `HTTPScraper` and the strategy identifier is `http`.

**Interface Contract:**
```python
class HTTPScraper:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        rate_limiter: RateLimiter,
    ) -> None: ...

    async def fetch(self, url: str, session: Optional[Session] = None) -> HTMLDocument:
        """Fetch URL via direct HTTP request and parse HTML.

        Returns:
            HTMLDocument with parsed DOM (BeautifulSoup tree), status, headers, timing.

        Raises:
            ScrapingError: On HTTP errors, timeouts, connection failures.
        """
        ...
```

---

#### 3.3.2 Browser Scraper (`phoenix.scrapers.browser`)

**Purpose:** Full browser automation for JavaScript-rendered content. Uses Playwright to control headless Chromium, rendering the full DOM before extraction.

**Responsibilities:**
- Launch and manage headless browser context via Playwright
- Navigate to URL, wait for page readiness (networkidle/domcontentloaded)
- Execute platform-specific wait strategies (e.g., wait for tweet element by CSS selector)
- Return rendered DOM HTML and page metadata
- Manage browser instance pooling for performance
- Handle SPA (Single Page Application) dynamic content loading
- Support cookie injection from SessionManager for authenticated scraping

**Dependencies:** `playwright.async_api`, `BrowserPool`, `RateLimiter`

**Dependents:** `PipelineController`

**Interface Contract:**
```python
class BrowserScraper:
    def __init__(
        self,
        browser_pool: BrowserPool,
        rate_limiter: RateLimiter,
    ) -> None: ...

    async def fetch(
        self,
        url: str,
        session: Optional[Session] = None,
        wait_for: Optional[str] = None,  # CSS selector to wait for
    ) -> HTMLDocument:
        """Fetch URL via browser automation and return rendered HTML.

        Returns:
            HTMLDocument with rendered DOM, page metadata, screenshot path (optional).

        Raises:
            ScrapingError: On navigation timeout, browser crash.
        """
        ...
```

---

#### 3.3.2a BrowserPool (`phoenix.browser.pool`)

**Purpose:** Manage a pool of Playwright browser contexts to amortize startup cost and enforce concurrency limits for JavaScript-rendered scraping.

**Responsibilities:**
- Maintain a bounded pool of browser contexts (default 3)
- Acquire/release contexts to `BrowserScraper` instances
- Apply per-context stealth/anti-detection profiles (user-agent, viewport, locale)
- Recycle contexts after a configurable number of uses to reduce fingerprint entropy
- Track pool metrics (active, available, total created)

**Dependencies:** `playwright.async_api`, `StealthModule`

**Dependents:** `BrowserScraper`

**Interface Contract:**
```python
class BrowserPool:
    def __init__(self, max_contexts: int = 3, stealth: Optional[StealthModule] = None) -> None: ...

    async def acquire(self) -> BrowserContext: ...
    async def release(self, context: BrowserContext) -> None: ...
    async def close(self) -> None: ...
```

---

#### 3.3.2b Stealth / Anti-Detection Module (`phoenix.browser.stealth`)

**Purpose:** Reduce the likelihood of detection and blocking by target sites through fingerprint masking, header rotation, and human-like interaction patterns.

**Responsibilities:**
- Rotate realistic user-agent strings and accept-language headers
- Mask WebGL/Canvas/Navigator fingerprints per context
- Inject randomized but polite delays between requests and scrolls
- Provide "CAPTCHA warming" hints (pause on challenge pages, log warning, never bypass)
- Combine with `RateLimiter` to stay within polite per-domain throughput

**Dependencies:** `playwright.async_api`, `Config`

**Dependents:** `BrowserPool`, `BrowserScraper`

**Note:** This module is intentionally defensive. It does not bypass CAPTCHA, evade ToS, or circumvent authentication barriers.

---

#### 3.3.3 Selector Engine (`phoenix.scrapers.selectors`)

**Purpose:** Manages CSS selector and XPath expression sets for each platform, including fallback chains and selector versioning. This is the heart of the extraction system.

**Responsibilities:**
- Store and organize CSS selector sets per platform and page type
- Maintain ordered fallback chains: primary selector -> alternative selectors -> XPath backup
- Track selector versioning (when a selector stops matching, log and flag for update)
- Support dynamic selector evaluation against parsed HTML
- Provide selector health metrics (match rates, last successful use)
- Enable selector registration from plugins

**Dependencies:** `beautifulsoup4`, `lxml`, `cssselect`

**Dependents:** `HTMLExtractor`, all Platform Scrapers

**Interface Contract:**
```python
class SelectorEngine:
    def __init__(self) -> None: ...

    def register_selectors(
        self,
        platform: str,
        selectors: SelectorSet,
    ) -> None:
        """Register a CSS/XPath selector set for a platform."""
        ...

    def extract(
        self,
        soup: BeautifulSoup,
        platform: str,
        field: str,
    ) -> SelectorResult:
        """Extract a field value using registered selectors with fallback chain.

        Tries primary selector first, then fallback chain, then XPath backup.
        Returns first successful match with metadata about which selector worked.
        """
        ...

    def get_selector_health(self, platform: str) -> dict[str, SelectorHealth]:
        """Return health metrics for all selectors of a platform."""
        ...

class SelectorSet(BaseModel):
    """A set of CSS selectors and XPath fallbacks for a platform."""
    platform: str
    version: str  # e.g., "2025.01.15"
    selectors: dict[str, SelectorChain]  # field_name -> chain of selectors
    xpath_backups: dict[str, str]  # field_name -> XPath expression

class SelectorChain(BaseModel):
    """Ordered chain of CSS selectors for a single field."""
    field: str
    primary: str  # e.g., "article[data-testid='tweet'] div[lang]"
    fallbacks: list[str]  # ordered alternatives
    attribute: Optional[str] = None  # e.g., "content", "src", None for text

class SelectorResult(BaseModel):
    """Result of a selector extraction attempt."""
    value: Optional[str]
    selector_used: Optional[str]
    selector_type: Literal["css_primary", "css_fallback", "xpath", "none"]
    matched: bool
```

---

### 3.4 Layer 4 -- Platform Scrapers

#### 3.4.1 Scraper Plugin Base (`phoenix.scrapers.base`)

**Purpose:** Abstract base class defining the contract all platform scrapers must implement. Each scraper is a self-contained plugin that brings its own URL patterns and CSS/XPath selector sets.

**Responsibilities:**
- Define the `ScraperPlugin` abstract base class
- Specify required methods: `supported_patterns()`, `get_selectors()`, `parse(html)`
- Define lifecycle hooks: `initialize()`, `shutdown()`, `health_check()`
- Provide common utility methods for scraper plugin authors

**Dependencies:** `abc.ABC`, `PluginManifest`, `SelectorEngine`

**Dependents:** All platform-specific scrapers, custom plugins

**Interface Contract:**
```python
class ScraperPlugin(ABC):
    """Abstract base class for all platform scraper plugins.

    Each scraper plugin encapsulates:
    - URL patterns it handles
    - CSS selector sets for HTML extraction
    - Platform-specific parsing logic
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest: ...

    @abstractmethod
    def supported_patterns(self) -> list[re.Pattern]:
        """Return list of URL regex patterns this scraper handles."""
        ...

    @abstractmethod
    def get_selectors(self) -> SelectorSet:
        """Return the CSS/XPath selector set for this platform."""
        ...

    @abstractmethod
    async def parse(
        self,
        html_doc: HTMLDocument,
        selector_engine: SelectorEngine,
    ) -> PlatformData:
        """Parse HTML document and extract structured data using selectors."""
        ...
```

---

#### 3.4.2 Platform-Specific Scrapers

| Scraper | Module | URL Patterns | Primary Strategy | Key Selectors |
|---------|--------|-------------|------------------|---------------|
| **InstagramScraper** | `phoenix.scrapers.instagram` | `/p/`, `/reel/`, `/tv/` | Browser (JS-rendered) | `article img`, `h1 + div span`, `meta[property="og:description"]` |
| **XScraper** | `phoenix.scrapers.x_twitter` | `/status/`, `x.com/i/web` | HTTP + Browser fallback | `article[data-testid="tweet"]`, `div[lang]`, `time[datetime]`, `a[href*="/status/"]` |
| **TikTokScraper** | `phoenix.scrapers.tiktok` | `/video/`, `/@[user]/video/` | Browser (heavy JS) | `h1[data-e2e="browse-video-desc"]`, `strong[data-e2e="like-count"]` |
| **LinkedInScraper** | `phoenix.scrapers.linkedin` | `/posts/`, `/pulse/`, `/activity/` | Browser (auth wall) | `article[data-urn]`, `div.feed-shared-update-v2__description`, `span.social-details-social-counts__reactions-count` |
| **FacebookScraper** | `phoenix.scrapers.facebook` | `/posts/`, `/photos/`, `/videos/`, `/reel/` | Browser (heavy JS) | `div[data-ad-rendering-role="story"]`, `div[role="article"]`, `span.x193iq5w` |
| **YouTubeScraper** | `phoenix.scrapers.youtube` | `/watch?v=`, `/shorts/`, `/embed/` | HTTP (meta tags) + Browser | `meta[name="description"]`, `span.yt-core-attributed-string`, `yt-formatted-string#text` |
| **GenericWebScraper** | `phoenix.scrapers.generic` | Any HTTP(S) URL | HTTP | Open Graph: `meta[property="og:*"]`, article extraction, heading hierarchy |

Each scraper is an independent Python module implementing `ScraperPlugin`, bundled with its own selector set (versioned), URL pattern list, and parsing logic.

**Example: X/Twitter Scraper Selector Set**
```python
# phoenix/scrapers/x_twitter/selectors.py
X_TWITTER_SELECTORS = SelectorSet(
    platform="x_twitter",
    version="2025.01.15",
    selectors={
        "tweet_text": SelectorChain(
            field="tweet_text",
            primary='article[data-testid="tweet"] div[lang]',
            fallbacks=[
                'article div[dir="auto"][data-testid="tweetText"]',
                'article div[dir="auto"]',
                '[data-testid="tweet"] div[lang]',
            ],
            attribute=None,  # extract text content
        ),
        "author": SelectorChain(
            field="author",
            primary='article[data-testid="tweet"] a[role="link"][href^="/"] div[dir="ltr"] span',
            fallbacks=[
                'article a[href^="/"] div[dir="ltr"] span',
                'meta[property="og:title"]',
            ],
            attribute=None,
        ),
        "timestamp": SelectorChain(
            field="timestamp",
            primary='article[data-testid="tweet"] time[datetime]',
            fallbacks=[
                'article time[datetime]',
                'time[datetime]',
            ],
            attribute="datetime",
        ),
        "likes": SelectorChain(
            field="likes",
            primary='article[data-testid="tweet"] button[data-testid="like"] span',
            fallbacks=[
                'button[data-testid="like"] span',
                'a[href*="/likes"] span',
            ],
            attribute=None,
        ),
    },
    xpath_backups={
        "tweet_text": "//article//div[@lang]//text()",
        "author": "//article//a[@role='link'][starts-with(@href, '/')]//span//text()",
        "timestamp": "//article//time/@datetime",
    },
)
```

---

#### 3.4.3 Plugin Loader (`phoenix.plugins.loader`)

**Purpose:** Discovers, loads, and registers platform scraper plugins at engine initialization.

**Responsibilities:**
- Scan `phoenix.scrapers` package for built-in scrapers
- Scan plugin directories for third-party scraper packages
- Validate plugin manifests and selector sets
- Register scrapers by URL pattern
- Handle plugin loading errors gracefully

**Dependencies:** `importlib`, `PluginManifest`, `SelectorEngine`

**Dependents:** `URLRouter`, `PhoenixEngine`

---

### 3.5 Layer 5 -- Processing

#### 3.5.1 HTML Extractor (`phoenix.processing.html_extractor`)

**Purpose:** Extracts structured data from parsed HTML documents using the `SelectorEngine` and platform-specific selector sets.

**Responsibilities:**
- Parse raw HTML with BeautifulSoup4 or lxml
- Apply platform-specific CSS selectors via `SelectorEngine`
- Extract text, metadata, media URLs, engagement metrics from HTML elements
- Handle extraction failures with detailed error context (which selectors were tried)
- Fall back to alternative selectors and XPath when primary selectors fail
- Return structured `PlatformData` with extraction confidence scores

**Dependencies:** `beautifulsoup4`, `lxml`, `cssselect`, `SelectorEngine`, Platform Scrapers

**Dependents:** `PipelineController`

**Interface Contract:**
```python
class HTMLExtractor:
    def __init__(self, selector_engine: SelectorEngine) -> None: ...

    async def extract(
        self,
        html_doc: HTMLDocument,
        scraper: ScraperPlugin,
    ) -> PlatformData:
        """Extract structured data from HTML using the scraper's selector set.

        Process:
        1. Parse HTML into BeautifulSoup tree
        2. For each field in scraper's selector set:
           a. Try primary CSS selector
           b. Try fallback CSS selectors in order
           c. Try XPath backup
           d. Record which selector succeeded
        3. Return PlatformData with all extracted fields + selector usage metadata

        Raises:
            ExtractionError: If critical fields cannot be extracted.
        """
        ...
```

---

#### 3.5.2 Content Normalizer (`phoenix.processing.normalizer`)

**Purpose:** Transforms platform-specific extracted data into the unified `UnifiedOutput` schema.

**Responsibilities:**
- Map platform-specific fields to `UnifiedOutput` fields
- Normalize date/time formats to ISO 8601 UTC
- Normalize engagement metrics to consistent numeric types (convert "1.2K" to 1200)
- Deduplicate media URLs
- Validate output against `UnifiedOutput` schema
- Handle missing fields with defaults or nulls
- Compute per-field and overall extraction confidence scores (`field_confidences`, `confidence`); apply penalties when fallback strategies or AI assistance are used

**Dependencies:** `UnifiedOutput` Pydantic model

**Dependents:** `PipelineController`

---

#### 3.5.3 Ollama AI Engine (`phoenix.processing.ollama_engine`)

**Purpose:** Core AI-powered HTML parsing and data extraction using a **local Ollama server**. When standard CSS selectors and XPath expressions fail to extract data from HTML, the Ollama AI Engine sends the raw HTML to a locally-running Ollama instance which intelligently analyzes the structure and returns structured JSON extractions. It also provides selector repair, content classification, anti-bot recovery suggestions, entity resolution, model management, and hardware monitoring. All AI inference runs locally -- no external API calls, no API keys, no token costs.

**Responsibilities:**
- Send raw HTML + extraction context to local Ollama API (`http://localhost:11434`) for intelligent data extraction
- Parse and validate Ollama responses into structured `OllamaExtractionResult` objects
- Suggest updated CSS selectors when existing selectors fail (Selector Repair)
- Classify page content type (article, product, profile, post, video, comment)
- Analyze anti-bot block pages and suggest alternative scraping strategies
- Perform cross-platform entity resolution ("Is this the same user across platforms?")
- Auto-select optimal model tier (7b/14b/32b) based on HTML size, task complexity, and available VRAM
- Monitor GPU/CPU hardware resources and recommend model sizing
- Manage model lifecycle (pull, verify, unload) via `ModelManager`
- Cache AI responses locally to reduce redundant inference calls
- Manage HTML chunking for large pages that exceed context limits
- Maintain fallback chain: Primary selectors -> Secondary selectors -> Ollama AI -> Error
- Generate platform scraper plugins / adapters from example pages (PhoenixArchitect adapter auto-generation)

**Dependencies:** `httpx` (direct HTTP to `localhost:11434`), `psutil` (hardware monitoring), `nvidia-ml-py` (GPU monitoring, optional), local Ollama server

**Dependents:** `PipelineController`, `HTMLExtractor`, `SelectorEngine`

**Interface Contract:**
```python
class OllamaAIEngine:
    """Core AI engine using local Ollama for intelligent HTML extraction.

    All inference runs locally via Ollama at http://localhost:11434.
    No external API calls. No API keys. No token costs.
    Primary model: dolphincoder:7b (128K context, structured output).
    Fallback model: qwen2.5:7b.
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
            default_model: Default model for extraction.
                           "dolphincoder:7b" for most tasks.
                           "qwen2.5:7b" for small/fast tasks or fallback.
                           "qwen2.5-coder:14b" for larger context.
                           "qwen2.5-coder:32b" for maximum accuracy.
                           "deepseek-coder-v2:16b" as alternative.
            cache: Optional cache for AI responses (local filesystem or memory).
            hardware_monitor: Optional hardware monitor for VRAM/RAM tracking.
            model_manager: Optional model manager for pull/verify/unload.
        """

    async def extract(
        self,
        html: str,
        context: ExtractionContext,
        model: Optional[str] = None,
    ) -> OllamaExtractionResult:
        """Extract structured data from raw HTML using local Ollama inference.

        Sends the HTML (chunked if necessary) to the local Ollama API with a
        system prompt tuned for HTML extraction. The model returns structured
        JSON which is parsed and validated against the extraction schema.

        Temperature: 0.1-0.3 (deterministic extraction).

        Parameters:
            html: Raw HTML string to extract data from.
            context: ExtractionContext with URL, platform hint, schema, etc.
            model: Override model for this extraction. Auto-selected if None.

        Returns:
            OllamaExtractionResult with extracted data, confidence score,
            model used, inference time, and GPU memory usage.

        Raises:
            OllamaNotRunningError: If Ollama server is not reachable.
            OllamaModelNotFoundError: If requested model is not pulled.
            OllamaOutOfMemoryError: If GPU/CPU out of memory.
            OllamaTimeoutError: If local inference exceeds timeout.
            OllamaJSONParseError: If response cannot be parsed.
        """

    async def suggest_selectors(
        self,
        html: str,
        old_selectors: list[str],
        model: Optional[str] = None,
    ) -> list[SelectorSuggestion]:
        """Ask Ollama to suggest updated CSS selectors for changed HTML.

        Sends the new HTML structure along with the old (failed) selectors.
        Ollama analyzes the DOM and proposes new selectors that match
        the current layout.

        Temperature: 0.2 (focused, deterministic).

        Parameters:
            html: Current HTML with the new structure.
            old_selectors: Selectors that previously worked but now fail.
            model: Override model. Auto-selected if None.

        Returns:
            List of SelectorSuggestion with new selector, field mapping,
            confidence score, and sample matched content.
        """

    async def classify_content(
        self,
        html: str,
        url: str,
        model: Optional[str] = None,
    ) -> ContentClassification:
        """Classify the content type of an HTML page using Ollama.

        Temperature: 0.1 (highly deterministic).

        Parameters:
            html: HTML snippet (can be truncated for speed).
            url: The page URL for additional context.
            model: Override model. Auto-selected if None.

        Returns:
            ContentClassification with type (article, product, profile,
            post, video, comment, etc.) and confidence score.
        """

    async def suggest_recovery_strategy(
        self,
        html: str,
        http_status: int,
        platform: str,
        model: Optional[str] = None,
    ) -> AntiBotRecoverySuggestion:
        """Analyze an anti-bot block page and suggest recovery strategies.

        Sends the block page HTML to Ollama. The model identifies the
        blocking mechanism and suggests countermeasures.

        Temperature: 0.3 (some creativity needed for strategy diversity).

        Parameters:
            html: The block page HTML (Cloudflare, captcha, etc.).
            http_status: HTTP status code received.
            platform: Target platform identifier.
            model: Override model. Auto-selected if None.

        Returns:
            AntiBotRecoverySuggestion with strategy type, recommended
            actions, and confidence score.
        """

    async def resolve_entities(
        self,
        entities: list[EntityProfile],
        model: Optional[str] = None,
    ) -> list[EntityResolutionResult]:
        """Cross-reference entities across multiple scraped pages.

        Sends multiple entity profiles to Ollama and asks whether
        they represent the same real-world entity.

        Temperature: 0.2 (analytical, deterministic).

        Parameters:
            entities: List of entity profiles from different sources.
            model: Override model. Auto-selected if None.

        Returns:
            List of EntityResolutionResult with match pairs and
            confidence scores.
        """

    async def health_check(self) -> dict[str, Any]:
        """Check Ollama service health and model availability.

        Returns:
            Dict with status, available models, loaded model, GPU info,
            and recent inference statistics.
        """

    def list_available_models(self) -> list[ModelInfo]:
        """List all models available in the local Ollama instance.

        Returns:
            List of ModelInfo with name, size, parameter count,
            quantization level, and VRAM requirements.
        """
```

---

#### 3.5.4 Source Archiver (`phoenix.processing.archiver`)

**Purpose:** Preserves the original raw HTML source of every scrape for audit, debugging, and reprocessing.

**Responsibilities:**
- Save raw HTML responses and rendered DOM to storage
- Generate deterministic archive IDs (SHA-256 of URL + timestamp)
- Store with metadata (URL, timestamp, platform, scraping strategy, selectors used)
- Support retrieval by archive ID
- Respect `archive_enabled` configuration flag

**Dependencies:** `Storage`, `Config`

**Dependents:** `PipelineController`

---

#### 3.5.5 Ollama Client (`phoenix.processing.ollama_client`)

**Purpose:** Low-level HTTP client for communicating with the local Ollama REST API at `http://localhost:11434`. Handles request formatting, response parsing, retry logic, and error handling. Uses `httpx` directly -- no OpenAI SDK.

**Responsibilities:**
- Send HTTP POST requests to Ollama `/api/generate` and `/api/chat` endpoints
- Format requests with model, system prompt, user prompt (HTML + context), and options
- Handle HTTP-level errors (connection failures, timeouts, 5xx responses)
- Parse JSON responses from Ollama into Pydantic models
- Support streaming and non-streaming responses
- Manage request timeouts appropriate for local inference speed
- Support model management endpoints (`/api/tags`, `/api/pull`, `/api/delete`, `/api/show`)

**Interface Contract:**
```python
class OllamaClient:
    """Low-level HTTP client for Ollama API via direct httpx calls."""

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
        max_retries: int = 2,
    ) -> None:
        """Initialize Ollama client.

        Parameters:
            base_url: Ollama server URL. Override for remote Ollama.
            timeout: Request timeout in seconds (local inference can be slow).
            max_retries: Maximum retry attempts for transient failures.
        """

    async def generate(
        self,
        prompt: str,
        model: str = "dolphincoder:7b",
        system: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
        stream: bool = False,
    ) -> OllamaGenerateResponse:
        """Send a generation request to Ollama /api/generate.

        Parameters:
            prompt: User prompt containing HTML and context.
            model: Ollama model identifier.
            system: System prompt for the model.
            options: Generation options (temperature, num_ctx, etc.).
            stream: Whether to stream the response.

        Returns:
            OllamaGenerateResponse with generated text and metadata.

        Raises:
            OllamaNotRunningError: If Ollama server is not reachable.
            OllamaModelNotFoundError: If model is not available.
            OllamaTimeoutError: On request timeout.
        """

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "dolphincoder:7b",
        options: Optional[dict[str, Any]] = None,
        stream: bool = False,
    ) -> OllamaChatResponse:
        """Send a chat completion request to Ollama /api/chat.

        Parameters:
            messages: List of message dicts with role and content.
            model: Ollama model identifier.
            options: Generation options.
            stream: Whether to stream the response.

        Returns:
            OllamaChatResponse with message content and metadata.
        """

    async def list_models(self) -> list[ModelInfo]:
        """List all pulled models from Ollama /api/tags."""

    async def pull_model(self, name: str) -> AsyncIterator[dict]:
        """Download a model from Ollama registry via /api/pull.

        Yields progress updates. Can take several minutes for large models.
        """

    async def delete_model(self, name: str) -> None:
        """Delete a model from Ollama via /api/delete."""

    async def model_info(self, name: str) -> ModelInfo:
        """Get detailed info about a model via /api/show."""

    async def check_health(self) -> bool:
        """Check if Ollama server is running and responsive."""


class OllamaGenerateResponse(BaseModel):
    """Parsed response from Ollama /api/generate."""

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
    """Parsed response from Ollama /api/chat."""

    message: dict[str, str]
    model: str
    created_at: str
    done: bool
    total_duration_ms: int
    prompt_eval_count: int
    eval_count: int


class HTMLChunker:
    """Splits large HTML documents into context-safe chunks for Ollama submission."""

    def __init__(
        self,
        max_chars: int = 48000,  # ~16K tokens at 3 chars/token (qwen2.5)
        overlap_chars: int = 3000,  # Context overlap between chunks
    ) -> None: ...

    def chunk(self, html: str, preserve_structure: bool = True) -> list[str]:
        """Split HTML into chunks that fit within context limits.

        Preserves DOM structure by splitting at element boundaries
        when possible. Includes overlap for context continuity.

        Returns:
            List of HTML chunks, each within the context limit.
        """


class AIResponseCache:
    """Cache for Ollama responses to reduce redundant inference calls."""

    def __init__(
        self,
        backend: str = "memory",  # "memory", "disk"
        ttl: int = 3600,  # Default 1 hour
        cache_dir: Optional[str] = None,
    ) -> None: ...

    async def get(self, key: str) -> Optional[OllamaExtractionResult]: ...
    async def set(self, key: str, value: OllamaExtractionResult, ttl: Optional[int] = None) -> None: ...
    async def invalidate(self, pattern: str) -> int: ...
```

---

#### 3.5.6 Model Manager (`phoenix.processing.model_manager`)

**Purpose:** Manages Ollama model lifecycle -- pulling, verifying, selecting, and unloading models. Ensures the right model is available for each task and hardware constraints are respected.

**Responsibilities:**
- Pull (download) models from the Ollama registry on demand
- List installed models and their metadata
- Verify a model is available before inference
- Auto-select optimal model tier (7b/14b/32b) based on HTML size and task complexity
- Unload models to free GPU memory
- Track model download progress

**Interface Contract:**
```python
class ModelManager:
    """Manages Ollama model lifecycle: pull, verify, select, unload."""

    # Model tier definitions with VRAM requirements
    MODEL_TIERS: dict[str, ModelTier] = {
        "fast": ModelTier(
            name="dolphincoder:7b",
            param_count="7B",
            vram_required_gb=4.5,
            context_length=128000,
            best_for=["classification", "simple_extraction", "small_html"],
        ),
        "standard": ModelTier(
            name="qwen2.5-coder:14b",
            param_count="14B",
            vram_required_gb=9.0,
            context_length=128000,
            best_for=["standard_extraction", "selector_repair", "medium_html"],
        ),
        "premium": ModelTier(
            name="qwen2.5-coder:32b",
            param_count="32B",
            vram_required_gb=20.0,
            context_length=128000,
            best_for=["complex_extraction", "entity_resolution", "large_html"],
        ),
        "alternative": ModelTier(
            name="deepseek-coder-v2:16b",
            param_count="16B",
            vram_required_gb=10.0,
            context_length=128000,
            best_for=["code_heavy_extraction", "alternative_to_dolphincoder"],
        ),
    }

    def __init__(self, client: OllamaClient) -> None:
        """Initialize ModelManager.

        Parameters:
            client: OllamaClient for API communication.
        """

    async def pull(self, model_name: str) -> None:
        """Download a model from Ollama registry.

        Parameters:
            model_name: Name of the model to pull (e.g., "dolphincoder:7b").

        Raises:
            OllamaError: If download fails.
        """

    async def list(self) -> list[ModelInfo]:
        """Show all installed models.

        Returns:
            List of ModelInfo with name, size, digest, and modification date.
        """

    async def verify(self, model_name: str) -> bool:
        """Check if a model is pulled and ready for inference.

        Parameters:
            model_name: Model name to check.

        Returns:
            True if model is available, False otherwise.
        """

    async def select_for_task(
        self,
        html_size_bytes: int,
        task_type: str,
        hardware_profile: Optional[HardwareProfile] = None,
    ) -> str:
        """Auto-select the best model tier for a task.

        Parameters:
            html_size_bytes: Size of HTML to process.
            task_type: Type of task ("extraction", "classification",
                      "repair", "resolution").
            hardware_profile: Optional hardware constraints.

        Returns:
            Model name string (e.g., "dolphincoder:7b").
        """

    async def unload(self, model_name: str) -> None:
        """Unload a model from GPU memory to free VRAM.

        Parameters:
            model_name: Model to unload.
        """

    async def ensure_pulled(self, model_name: str) -> None:
        """Pull a model if not already present.

        Parameters:
            model_name: Model name to ensure availability.
        """


class ModelTier(BaseModel):
    """Definition of a model tier with capabilities and requirements."""

    name: str
    param_count: str
    vram_required_gb: float
    context_length: int
    best_for: list[str]


class ModelInfo(BaseModel):
    """Information about an installed Ollama model."""

    name: str
    size: int  # Size in bytes
    parameter_count: str  # e.g., "14B"
    quant_level: str  # e.g., "Q4_K_M"
    vram_required_gb: float
    digest: str
    modified_at: str
```

---

#### 3.5.7 Model Selector (`phoenix.processing.model_selector`)

**Purpose:** Intelligently selects the optimal Ollama model for each task based on HTML size, available hardware resources, and task complexity. Ensures best performance without exceeding hardware limits.

**Responsibilities:**
- Analyze HTML content size and complexity
- Check available GPU VRAM and system RAM
- Match task requirements to model capabilities
- Fall back to smaller models if hardware is constrained
- Support manual model override for testing

**Interface Contract:**
```python
class ModelSelector:
    """Selects the optimal Ollama model based on content and hardware."""

    # HTML size thresholds (bytes)
    SIZE_SMALL = 50000    # < 50KB -> 7b model
    SIZE_MEDIUM = 200000  # 50KB-200KB -> 7b model (14b optional)
    SIZE_LARGE = 500000   # > 200KB -> 32b model

    # Task complexity multipliers
    TASK_COMPLEXITY: dict[str, float] = {
        "classification": 0.5,
        "extraction": 1.0,
        "repair": 1.0,
        "resolution": 1.5,
        "recovery": 1.2,
    }

    def __init__(
        self,
        model_manager: ModelManager,
        hardware_monitor: HardwareMonitor,
    ) -> None: ...

    async def select_model(
        self,
        html_content: str,
        task_type: str = "extraction",
        preferred_tier: Optional[str] = None,
    ) -> str:
        """Select the best model for a task.

        Parameters:
            html_content: HTML content to process.
            task_type: Type of AI task.
            preferred_tier: Optional preferred tier ("fast", "standard",
                           "premium"). Auto-selected if None.

        Returns:
            Model name string (e.g., "dolphincoder:7b").
        """

    def _html_complexity_score(self, html: str) -> float:
        """Calculate complexity score based on HTML structure."""

    def _can_run_model(self, model_name: str) -> bool:
        """Check if hardware can run the specified model."""
```

---

#### 3.5.8 Hardware Monitor (`phoenix.processing.hardware_monitor`)

**Purpose:** Monitors local hardware resources (GPU VRAM, system RAM, CPU) to ensure Ollama models can run without exhausting system resources. Provides recommendations for optimal model selection.

**Responsibilities:**
- Detect GPU availability (NVIDIA via nvidia-ml-py, Apple Silicon via system profiler)
- Monitor GPU VRAM usage, temperature, and availability
- Monitor system RAM usage and availability
- Determine if a specific model can run on current hardware
- Recommend the best model tier for current hardware configuration
- Support CPU-only mode when no GPU is available

**Interface Contract:**
```python
class HardwareMonitor:
    """Monitors local GPU and system resources for Ollama inference."""

    def __init__(self) -> None:
        """Initialize hardware monitor and detect available hardware."""

    def get_gpu_info(self) -> Optional[GPUInfo]:
        """Get GPU information including VRAM usage and temperature.

        Returns:
            GPUInfo if GPU is available, None for CPU-only systems.
        """

    def get_ram_info(self) -> RAMInfo:
        """Get system RAM information.

        Returns:
            RAMInfo with total, available, used, and percentage.
        """

    def can_load_model(self, model_name: str) -> tuple[bool, str]:
        """Check if current hardware can load a specific model.

        Parameters:
            model_name: Model to check (e.g., "dolphincoder:7b").

        Returns:
            Tuple of (can_run, reason). If False, reason explains why.
        """

    def get_optimal_model(self) -> str:
        """Recommend the best model for current hardware.

        Returns:
            Model name string for the largest model that fits
            in available VRAM (or RAM for CPU-only).
        """

    def is_gpu_available(self) -> bool:
        """Check if a GPU is available for inference."""

    def get_hardware_profile(self) -> HardwareProfile:
        """Get complete hardware profile.

        Returns:
            HardwareProfile with GPU and RAM information.
        """


class GPUInfo(BaseModel):
    """GPU information for inference capacity planning."""

    name: str
    vram_total_mb: int
    vram_used_mb: int
    vram_available_mb: int
    temperature_c: Optional[float] = None
    utilization_percent: Optional[float] = None
    cuda_version: Optional[str] = None


class RAMInfo(BaseModel):
    """System RAM information."""

    total_mb: int
    available_mb: int
    used_mb: int
    percent_used: float


class HardwareProfile(BaseModel):
    """Complete hardware profile for model selection decisions."""

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

### 3.6 Layer 6 -- Infrastructure

#### 3.6.1 Session Manager (`phoenix.infrastructure.session`)

**Purpose:** Manages authenticated browser sessions (cookies) for platforms that require login for public data access.

**Responsibilities:**
- Store and retrieve session cookies per platform
- Encrypt cookie data at rest using `cryptography` library
- Support login-once-use-many workflow via browser automation
- Track session freshness and validity
- Provide logout/session cleanup

**Dependencies:** `cryptography`, `Storage`

**Dependents:** `BrowserScraper`, `HTTPScraper`, `StrategySelector`

**Interface Contract:**
```python
class SessionManager:
    def __init__(self, storage: Storage, encryption_key: Optional[str] = None) -> None: ...

    async def login_browser(self, platform: str) -> Session:
        """Open browser for interactive login, capture cookies after user signs in."""
        ...

    async def get_session(self, platform: str) -> Optional[Session]: ...
    async def logout(self, platform: str) -> None: ...
    async def is_session_valid(self, platform: str) -> bool: ...
```

---

#### 3.6.2 Storage (`phoenix.infrastructure.storage`)

**Purpose:** Abstracts all persistent storage operations -- results, archives, sessions, configuration.

**Responsibilities:**
- Provide unified storage interface (save, get, query, delete)
- Support SQLite backend (default, local/desktop use)
- Support JSON file backend (simple deployments)
- Store scraped results and archived HTML sources
- Handle connection pooling and transaction management

**Dependencies:** `sqlalchemy` (optional), `aiosqlite`

**Dependents:** `SessionManager`, `SourceArchiver`, `AuditLogger`

---

#### 3.6.3 Rate Controller (`phoenix.infrastructure.rate`)

**Purpose:** Enforces polite rate limiting per domain with robots.txt awareness.

**Responsibilities:**
- Token-bucket rate limiter per domain
- Fetch and parse robots.txt for crawl-delay directives
- Enforce minimum delays between requests to the same domain
- Record per-request latency, HTTP status, and errors via `record_outcome()`
- Adapt effective request rate based on recent error rate, 429/403/503 responses, anti-bot errors, and average latency
- Separate buckets for HTTP scraper and browser scraper

**Dependencies:** `httpx`, `Config`, collector timing metadata (`response_time_ms`)

**Dependents:** `HTTPScraper`, `BrowserScraper`

---

#### 3.6.4 Config Manager (`phoenix.infrastructure.config`)

**Purpose:** Manages application configuration via Pydantic Settings with TOML file support.

**Responsibilities:**
- Load configuration from TOML file, environment variables, and defaults
- Provide typed access to all settings
- Validate configuration on startup
- Support per-platform overrides

**Dependencies:** `pydantic_settings`, `tomli`

**Dependents:** All components

---

#### 3.6.5 Audit Logger (`phoenix.infrastructure.audit`)

**Purpose:** Records every scraping action for transparency, compliance, and debugging.

**Responsibilities:**
- Log every URL scraped, with timestamp, strategy used, and outcome
- Record selectors that succeeded/failed
- Store diagnostics for failed scrapes
- Write to SQLite/JSON storage for easy querying
- Ensure logs are append-only and tamper-evident

**Dependencies:** `Storage`, `structlog`

**Dependents:** `PipelineController`

---

## 4. Data Flow

### 4.1 Happy Path Flow

```
User Input: URL
  |
  v
+--------------------------------------------------------+
| 1. URLRouter: Parse URL, match against scraper patterns |
|    Result: platform="x_twitter", scraper=XScraper       |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 2. StrategySelector: HTTP (primary) -> Browser (fallback)
|    X/Twitter: server returns HTML with tweet data      |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 3. HTTPScraper: httpx GET url                          |
|    - Set transparent User-Agent                        |
|    - Check rate limit for x.com                        |
|    - Receive HTML response (status 200)                |
|    - Parse HTML with BeautifulSoup                     |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 4. HTMLExtractor: Apply X_TWITTER_SELECTORS            |
|    - tweet_text: primary selector MATCHED              |
|    - author: primary selector MATCHED                  |
|    - timestamp: primary selector MATCHED               |
|    - likes: fallback[0] selector MATCHED               |
|    - All critical fields extracted                     |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 5. ContentNormalizer: Transform to UnifiedOutput       |
|    - Map fields: tweet_text -> text                     |
|    - Normalize: "1.2K" -> 1200                         |
|    - Parse timestamp to ISO 8601                       |
|    - Validate against UnifiedOutput schema             |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 6. SourceArchiver: Save raw HTML + metadata            |
|    Archive ID: sha256(url + timestamp)                 |
+--------------------------------------------------------+
  |
  v
Output: ScrapingResult(success=True, data=UnifiedOutput, selectors_used=[...])
```

### 4.2 Fallback Flow (Selectors Fail Due to Layout Change)

```
...after step 3 (HTML fetched)...
  |
  v
+--------------------------------------------------------+
| 4. HTMLExtractor: Apply X_TWITTER_SELECTORS            |
|    - tweet_text: primary selector FAILED (no match)    |
|    - tweet_text: fallback[0] FAILED                    |
|    - tweet_text: fallback[1] FAILED                    |
|    - tweet_text: xpath_backup FAILED                   |
|    - CRITICAL: Not enough fields extracted             |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 4b. StrategySelector: Switch to Browser strategy       |
|     BrowserScraper: Playwright renders full page       |
|     (JavaScript executes, DOM is fully populated)      |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 4c. HTMLExtractor: Re-apply selectors on rendered DOM  |
|     - tweet_text: fallback[2] MATCHED on rendered DOM  |
|     - Other fields: various selectors MATCHED          |
+--------------------------------------------------------+
  |
  v
...continue to step 5 (Normalize)...
  |
  v
Output: ScrapingResult(success=True, data=UnifiedOutput,
                       selectors_used=[...], fallback_triggered=True)
```

### 4.3 AI Fallback Flow (All Selectors Fail)

```
...after all selector attempts exhausted...
  |
  v
+--------------------------------------------------------+
| 4d. OllamaAIEngine.extract() called                    |
|     - ModelSelector picks best model for HTML size     |
|     - HardwareMonitor confirms sufficient VRAM         |
|     - Send HTML snippet to local Ollama                |
|     - LLM extracts text, author, timestamp, metrics    |
|     - Validate output against UnifiedOutput            |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 4e. OllamaAIEngine.suggest_selectors() called          |
|     - Ask LLM to suggest new CSS selectors             |
|     - Validate suggested selectors against HTML        |
|     - Store suggestions for human review               |
+--------------------------------------------------------+
  |
  v
Output: ScrapingResult(success=True, data=UnifiedOutput,
                       ai_assisted=True, suggested_selectors=...)
```

### 4.4 Error Flow (All Strategies Exhausted)

```
...after all strategies and fallbacks exhausted...
  |
  v
+--------------------------------------------------------+
| 5. Error Handler: Compile diagnostics                  |
|    - HTTP status codes and response snippets            |
|    - All selectors tried and their results             |
|    - Stack traces and timing data                      |
|    - Suggested resolution steps                        |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 6. AuditLogger: Record failure with full context       |
+--------------------------------------------------------+
  |
  v
Output: ScrapingResult(success=False, error=ScrapingError,
                       diagnostics=Diagnostics, suggested_fix=...)
```

### 4.5 PhoenixArchitect Flow (Autonomous Adapter Generation)

```
User Input: goal = "scrape Egypt property listings"
  |
  v
+--------------------------------------------------------+
| 1. Planner: Parse goal, define success criteria        |
|    Result: plan=[search, explore, inspect, code, crit] |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 2. Researcher: Build query "Egypt apartment listings"  |
|    DuckDuckGo/SerpAPI -> ranked URL list               |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 3. Explorer: Visit top URLs                            |
|    - Detect pagination / infinite scroll               |
|    - Capture N <= max-pages snapshots per URL          |
|    - Archive raw HTML for inspection                   |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 4. Inspector: Ollama analyzes snapshots                |
|    - Classify site type (real_estate, e-commerce, ...) |
|    - Propose fields: title, price, location, ...       |
|    - Suggest CSS/XPath selectors                       |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 5. Coder: Generate adapter module                      |
|    - URL patterns, SelectorSet, parse() method         |
|    - ContentNormalizer mapping                         |
|    - Write to src/phoenix/scrapers/generated/...       |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 6. Critic: Validate adapter against snapshots            |
|    - Run generated selectors on archived HTML          |
|    - Measure field coverage                            |
|    - If coverage < threshold, loop to step 5           |
+--------------------------------------------------------+
  |
  v
+--------------------------------------------------------+
| 7. Register adapter via PluginLoader                   |
|    - Prioritize over GenericWebScraper                 |
+--------------------------------------------------------+
  |
  v
Output: AdapterGenerationResult(adapter_path, coverage, urls_explored)
```

---

## 5. Technology Stack

### 5.1 Core Dependencies

| Component | Technology | Purpose |
|-----------|------------|---------|
| HTTP Client | `httpx` 0.27+ | Async HTTP/2 requests with connection pooling |
| HTML Parsing | `beautifulsoup4` 4.12+ | DOM tree construction from HTML |
| HTML Parsing | `lxml` 5.0+ | Fast XML/HTML parsing with XPath support |
| CSS Selectors | `cssselect` 1.2+ | Translate CSS selectors to XPath |
| Browser Automation | `playwright` 1.40+ | Headless Chromium for JS-rendered pages |
| Data Validation | `pydantic` 2.5+ | Data models, config validation, output schemas |
| CLI Framework | `typer` 0.12+ | Type-hinted CLI commands |
| Configuration | `pydantic-settings` 2.1+ | TOML + env var configuration |
| Rate Limiting | `pyrate-limiter` 3.0+ | Token bucket rate limiting |
| Logging | `structlog` 24.1+ | Structured logging |
| Encryption | `cryptography` 42+ | Cookie/session encryption at rest |
| Database | `aiosqlite` 0.20+ | Async SQLite for local storage |
| AI HTTP Client | `httpx` 0.27+ | Direct HTTP to Ollama at localhost:11434 |
| Hardware Monitoring | `psutil` 5.9+ | System RAM and CPU monitoring |
| GPU Monitoring | `nvidia-ml-py` 12.0+ | NVIDIA GPU VRAM monitoring (optional) |

### 5.2 Development Dependencies

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Language runtime |
| Black | 24.4+ | Code formatting |
| Ruff | 0.5+ | Linting (replaces flake8, pylint, isort) |
| mypy | 1.10+ | Static type checking (--strict) |
| pytest | 8.2+ | Test framework |
| pytest-asyncio | 0.23+ | Async test support |
| pytest-html | 4.1+ | HTML test reports |
| responses | 0.25+ | Mock HTTP responses (sync) |
| aioresponses | 0.7+ | Mock async HTTP responses |
| respx | 0.21+ | Mock httpx responses |
| freezegun | 1.5+ | Freeze time in tests |
| pyfakefs | 5.6+ | Mock filesystem |

### 5.3 Explicitly NOT Used (Scraping-Only Principle)

The following are **never** used in Phoenix Engine:

| Library | Why Excluded |
|---------|-------------|
| `instagrapi` | Instagram private API -- violates scraping-only principle |
| `tweepy` | X/Twitter official API -- violates scraping-only principle |
| `yt-dlp` (API mode) | YouTube API access -- violates scraping-only principle |
| `praw` | Reddit official API -- violates scraping-only principle |
| `snscrape` | Mixes scraping with API calls -- inconsistent approach |
| `requests` | Replaced by async `httpx` |
| `selenium` | Replaced by faster `playwright` |
| `scrapy` | Full framework -- Phoenix is a focused scraping engine |
| `openai` | Not needed -- Ollama uses direct httpx, not OpenAI SDK |
| `tiktoken` | Not needed -- local inference has no token costs |
| `redis` | Not needed -- AI cache uses local disk or memory |

---

## 6. Data Models (Pydantic)

### 6.1 UnifiedOutput -- The Standard Output Format

```python
class UnifiedOutput(BaseModel):
    """Standardized output format for all scraped content, regardless of source platform."""

    # Core content fields
    url: HttpUrl = Field(..., description="Canonical URL of the scraped content")
    platform: str = Field(..., description="Source platform identifier")
    content_type: str = Field(..., description="Type: post, article, video, profile, etc.")
    title: Optional[str] = Field(None, description="Content title or headline")
    text: Optional[str] = Field(None, description="Main text content")
    author: Optional[str] = Field(None, description="Content author/creator")
    author_url: Optional[HttpUrl] = Field(None, description="Author profile URL")
    timestamp: Optional[datetime] = Field(None, description="Publication time (UTC)")

    # Engagement metrics
    likes: Optional[int] = Field(None, description="Like/reaction count")
    shares: Optional[int] = Field(None, description="Share/repost count")
    comments: Optional[int] = Field(None, description="Comment count")
    views: Optional[int] = Field(None, description="View count")

    # Media
    media_urls: list[HttpUrl] = Field(default_factory=list, description="URLs of images/videos")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Thumbnail/preview image")

    # Metadata
    language: Optional[str] = Field(None, description="Detected content language")
    tags: list[str] = Field(default_factory=list, description="Hashtags, mentions, topics")
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    scraping_strategy: str = Field(..., description="HTTP or Browser")
    selectors_used: list[str] = Field(default_factory=list, description="CSS selectors that matched")

    # AI assistance flag
    ai_assisted: bool = Field(False, description="Whether AI was used for extraction")

    # Source reference
    archive_id: Optional[str] = Field(None, description="Reference to archived raw HTML")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://x.com/user/status/1234567890",
                "platform": "x_twitter",
                "content_type": "post",
                "text": "This is a sample tweet content.",
                "author": "username",
                "timestamp": "2025-01-15T10:30:00Z",
                "likes": 42,
                "shares": 7,
                "scraped_at": "2025-01-20T14:00:00Z",
                "scraping_strategy": "HTTP",
            }
        }
```

### 6.2 ScrapingResult -- Operation Result

```python
class ScrapingResult(BaseModel):
    """Result of a scraping operation."""

    success: bool = Field(..., description="Whether scraping succeeded")
    url: str = Field(..., description="URL that was scraped")
    output: Optional[UnifiedOutput] = Field(None, description="Extracted data if successful")
    error: Optional[ScrapingError] = Field(None, description="Error details if failed")
    diagnostics: Diagnostics = Field(default_factory=Diagnostics)
    archived_path: Optional[Path] = Field(None, description="Path to archived HTML")
    selectors_used: list[str] = Field(default_factory=list)
    fallback_triggered: bool = Field(False, description="Whether fallback strategy was used")
    ai_assisted: bool = Field(False, description="Whether AI assisted extraction")
    timing_ms: dict[str, float] = Field(default_factory=dict)
```

### 6.3 HTMLDocument -- Parsed HTML Container

```python
class HTMLDocument(BaseModel):
    """Container for a fetched and parsed HTML document."""

    url: str = Field(..., description="Original URL")
    final_url: Optional[str] = Field(None, description="URL after redirects")
    status_code: int = Field(..., description="HTTP status code")
    headers: dict[str, str] = Field(default_factory=dict)
    raw_html: str = Field(..., description="Raw HTML string")
    soup: Any = Field(..., description="Parsed BeautifulSoup tree (excluded from serialization)")
    content_type: Optional[str] = Field(None)
    cookies: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    strategy: ScrapingStrategy = Field(..., description="HTTP or Browser")
    timing_ms: dict[str, float] = Field(default_factory=dict)
    screenshot_path: Optional[str] = Field(None, description="Browser screenshot path")
```

### 6.4 Session -- Authenticated Session

```python
class Session(BaseModel):
    """Authenticated browser session with cookies for a platform."""

    platform: str = Field(..., description="Platform identifier")
    cookies: list[dict] = Field(default_factory=list, description="Browser cookies")
    user_agent: str = Field(..., description="User agent string used")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = Field(None, description="Session expiration")
    is_valid: bool = Field(True, description="Whether session is still valid")
```

### 6.5 PluginManifest -- Scraper Plugin Metadata

```python
class PluginManifest(BaseModel):
    """Metadata for a scraper plugin."""

    name: str = Field(..., description="Plugin name (e.g., 'x_twitter')")
    version: str = Field(..., description="Plugin version (semver)")
    description: str = Field(..., description="Human-readable description")
    author: str = Field(..., description="Plugin author")
    url_patterns: list[str] = Field(..., description="URL regex patterns")
    primary_strategy: ScrapingStrategy = Field(..., description="Preferred HTTP or Browser")
    selector_version: str = Field(..., description="Version of CSS selector set")
    requires_auth: bool = Field(False, description="Whether login is needed for public data")
    dependencies: list[str] = Field(default_factory=list)
```

### 6.6 Config -- Application Configuration

```python
class Config(BaseSettings):
    """Phoenix Engine configuration loaded from TOML file and environment variables."""

    # General
    app_name: str = "Phoenix Engine"
    log_level: str = "INFO"
    user_agent: str = "PhoenixEngine/1.0 (+https://github.com/phoenix/engine; bot for research)"

    # Scraping
    default_timeout: int = 30
    browser_timeout: int = 60
    max_redirects: int = 5
    follow_redirects: bool = True

    # Rate limiting
    requests_per_second: float = 1.0
    per_domain_limits: dict[str, float] = Field(default_factory=dict)
    respect_robots_txt: bool = True

    # Browser
    browser_pool_size: int = 3
    browser_headless: bool = True
    browser_viewport: dict = Field(default_factory=lambda: {"width": 1920, "height": 1080})

    # Ollama AI Engine (Local Inference)
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "dolphincoder:7b"
    ollama_fallback_model: str = "qwen2.5:7b"
    ollama_enterprise_model: str = "qwen2.5-coder:32b"
    ollama_alternative_model: str = "deepseek-coder-v2:16b"
    ollama_temperature_extraction: float = 0.2
    ollama_temperature_analysis: float = 0.5
    ollama_num_ctx: int = 16384
    ollama_timeout: float = 120.0
    ollama_max_retries: int = 2
    ollama_cache_enabled: bool = True
    ollama_cache_ttl: int = 3600
    ollama_cache_backend: str = "memory"  # "memory" or "disk"
    ollama_cache_dir: Optional[str] = None
    ollama_auto_select_model: bool = True
    ollama_gpu_layers: Optional[int] = None  # Auto if None
    ollama_keep_alive: str = "5m"

    # Storage
    storage_backend: str = "sqlite"  # sqlite or json
    database_url: str = "sqlite:///phoenix.db"
    archive_enabled: bool = True
    archive_dir: str = "./archive"

    # Session
    encrypt_sessions: bool = True

    model_config = SettingsConfigDict(
        env_prefix="PHOENIX_",
        toml_file="phoenix.toml",
    )
```

### 6.7 ScrapingStrategy -- Strategy Enum

```python
class ScrapingStrategy(str, Enum):
    """Available scraping strategies."""
    HTTP = "http"           # Direct HTTP request + BeautifulSoup parsing
    BROWSER = "browser"     # Playwright headless browser rendering
    AI_ASSIST = "ai_assist" # Ollama AI-powered extraction (fallback only)
```

### 6.8 OllamaExtractionResult -- Ollama AI Extraction Output

```python
class OllamaExtractionResult(BaseModel):
    """Result of an Ollama-powered local HTML extraction.

    Contains the structured data extracted by the local Ollama model
    along with metadata about the extraction process, confidence,
    hardware usage, and inference timing.
    """

    success: bool = Field(..., description="Whether extraction succeeded")
    extracted_data: dict = Field(default_factory=dict, description="Structured data extracted from HTML")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    model_used: str = Field("dolphincoder:7b", description="Ollama model used for inference")
    inference_time_ms: int = Field(0, description="Local inference duration in milliseconds")
    gpu_memory_mb: int = Field(0, description="GPU memory used during inference in MB")
    prompt_tokens: int = Field(0, description="Tokens in the prompt")
    completion_tokens: int = Field(0, description="Tokens in the completion")
    total_duration_ms: int = Field(0, description="Total request duration including model load")
    load_duration_ms: int = Field(0, description="Model loading duration in milliseconds")
    cached: bool = Field(False, description="Whether result was served from cache")
    chunks_processed: int = Field(1, description="Number of HTML chunks processed")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    hardware_profile: Optional[HardwareProfile] = Field(None, description="Hardware state during inference")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "extracted_data": {
                    "text": "Tweet content here...",
                    "author": "username",
                    "timestamp": "2025-01-15T10:30:00Z",
                    "likes": 42,
                },
                "confidence": 0.94,
                "model_used": "dolphincoder:7b",
                "inference_time_ms": 2847,
                "gpu_memory_mb": 5120,
                "total_duration_ms": 3420,
            }
        }
```

### 6.9 ExtractionContext -- Input Context for AI Extraction

```python
class ExtractionContext(BaseModel):
    """Context passed to OllamaAIEngine.extract() to guide extraction.

    Provides the local AI model with hints about the page structure,
    platform conventions, and desired output format.
    """

    url: str = Field(..., description="URL of the page being scraped")
    source_platform: Optional[str] = Field(None, description="Platform: x_twitter, instagram, etc.")
    content_type_hint: Optional[str] = Field(None, description="Expected type: article, product, profile, post, video, comment")
    previous_selectors: list[str] = Field(default_factory=list, description="Selectors that already failed")
    extraction_schema: Optional[dict] = Field(None, description="Desired JSON output schema (JSON Schema format)")
    fields_required: list[str] = Field(default_factory=list, description="Fields that must be extracted")
    html_size_bytes: int = Field(0, description="Original HTML size for chunking decisions")
    browser_rendered: bool = Field(False, description="Whether HTML was rendered by browser")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://x.com/user/status/1871234567890",
                "source_platform": "x_twitter",
                "content_type_hint": "post",
                "previous_selectors": [
                    'article[data-testid="tweet"] div[lang]',
                    'article div[dir="auto"]',
                ],
                "fields_required": ["text", "author", "timestamp", "likes"],
            }
        }
```

### 6.10 ContentClassification -- Ollama Content Type Classifier Output

```python
class ContentClassification(BaseModel):
    """Result of Ollama content type classification."""

    content_type: str = Field(..., description="Classified type: article, product, profile, post, video, comment, story, reel, short, listing, unknown")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    platform_detected: Optional[str] = Field(None, description="Platform detected from HTML analysis")
    schema_suggested: Optional[dict] = Field(None, description="Suggested extraction schema for this content type")
    reasoning: str = Field("", description="Brief explanation of classification decision")
```

### 6.11 EntityResolutionResult -- Cross-Platform Entity Match

```python
class EntityResolutionResult(BaseModel):
    """Result of cross-platform entity resolution via Ollama."""

    entity_ids: list[str] = Field(..., description="IDs of entities compared")
    is_same_entity: bool = Field(..., description="Whether entities represent the same real-world entity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence")
    matching_fields: list[str] = Field(default_factory=list, description="Fields that support the match")
    conflicting_fields: list[str] = Field(default_factory=list, description="Fields that contradict the match")
    reasoning: str = Field("", description="Explanation of the resolution decision")
```

---

## 7. Design Patterns

### 7.1 Strategy Pattern -- Scraping Strategy Selection

The `StrategySelector` uses the Strategy pattern to choose between `HTTPScraper` and `BrowserScraper` at runtime based on URL characteristics, platform requirements, and user preferences.

```python
# Context
class PipelineController:
    def __init__(self, scrapers: dict[ScrapingStrategy, HTMLScraper]) -> None: ...

    async def execute(self, url: str) -> ScrapingResult:
        strategy = await self.strategy_selector.select(url)
        scraper = self.scrapers[strategy.primary]  # HTTP or Browser
        html_doc = await scraper.fetch(url)
        ...
```

### 7.2 Template Method -- Platform Scraper Base

Each platform scraper inherits from `ScraperPlugin` which defines the template: get selectors, parse HTML, extract data. Concrete scrapers override selector definitions and parsing logic.

```python
class ScraperPlugin(ABC):
    async def scrape(self, html_doc: HTMLDocument, engine: SelectorEngine) -> PlatformData:
        # Template method
        selectors = self.get_selectors()
        data = await self.parse(html_doc, engine)
        return self.post_process(data)

    @abstractmethod
    def get_selectors(self) -> SelectorSet: ...

    @abstractmethod
    async def parse(self, html_doc: HTMLDocument, engine: SelectorEngine) -> PlatformData: ...
```

### 7.3 Plugin Pattern -- Scraper Registration

Platform scrapers are loaded dynamically via `PluginLoader`. New platforms are added by dropping a Python package implementing `ScraperPlugin` into the plugin directory.

```python
# Plugin auto-discovery
loader = PluginLoader(plugin_dirs=["./plugins"])
scrapers = await loader.discover()  # Finds all ScraperPlugin implementations

for scraper in scrapers:
    engine.register(scraper)  # Registers URL patterns + selectors
```

### 7.4 Pipeline Pattern -- Data Flow

The `PipelineController` chains processing stages: Fetch HTML --> Extract with Selectors --> Normalize --> Archive. Each stage is independent and can be replaced.

### 7.5 Factory Pattern -- Scraper Creation

```python
class ScraperFactory:
    @staticmethod
    def create(platform: str) -> ScraperPlugin:
        scrapers = {
            "instagram": InstagramScraper,
            "x_twitter": XScraper,
            "tiktok": TikTokScraper,
            # ...
        }
        return scrapers[platform]()
```

### 7.6 Repository Pattern -- Storage

`Storage` abstracts all persistence. Code uses the repository interface without knowing if the backend is SQLite, PostgreSQL, or JSON files.

---

## 8. Security

### 8.1 Cookie/Session Storage
- Session cookies are encrypted at rest using AES-256-GCM
- Encryption key is derived from OS keyring or user-provided passphrase
- Cookies are never logged or printed
- Session files have restrictive permissions (600)

### 8.2 No Credentials in Code
- No hardcoded API keys (no API keys exist -- Ollama runs locally without authentication)
- No embedded credentials
- Browser login is interactive only -- user enters credentials in browser window

### 8.3 Transparent Identification
- User-Agent clearly identifies as `PhoenixEngine/1.0` with project URL
- No impersonation of popular browsers (unless required for compatibility, documented)
- Robots.txt is fetched and respected

### 8.4 Audit Trail
- Every scrape is logged with: URL, timestamp, strategy, selectors used, outcome
- Logs are append-only with integrity checksums
- Failed scrapes include full diagnostic context (HTML snippet, selectors tried)

### 8.5 Local AI Privacy
- All AI inference runs on local hardware -- no data leaves the machine
- No external API calls for AI extraction
- No API keys or authentication tokens required
- HTML content never sent to cloud services

---

## 9. Error Handling

### 9.1 Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
    before_sleep=log_retry_attempt,
)
async def fetch_with_retry(self, url: str) -> HTMLDocument:
    ...
```

### 9.2 Selector Versioning
When a selector fails to match, the system:
1. Logs the failure with HTML snippet context
2. Attempts fallback selectors in order
3. Flags the selector set for review in health metrics
4. If AI is enabled, requests new selector suggestions

### 9.3 Graceful Degradation
- If engagement metrics (likes, shares) cannot be extracted, they are set to `None` (not a failure)
- If optional fields are missing, output is still returned
- Only "critical fields" (text, author for most platforms) cause hard failures

### 9.4 Error Types

| Error | Cause | Handling |
|-------|-------|----------|
| `HTTPError` | Network failure, timeout | Retry with exponential backoff |
| `SelectorNotFoundError` | All selectors failed | Try browser fallback, then AI |
| `PageChangedError` | HTML structure changed | Log diagnostics, flag selectors |
| `BlockedError` | 403/429 response | Back off, increase delay |
| `BrowserError` | Playwright failure | Retry once, then fail |
| `NormalizationError` | Data validation failed | Return partial data with warnings |
| `OllamaNotRunningError` | Ollama service not available | Prompt user to start Ollama; skip AI fallback |
| `OllamaModelNotFoundError` | Requested model not pulled | Auto-pull model or suggest `ollama pull` |
| `OllamaOutOfMemoryError` | GPU/CPU out of memory | Try smaller model (32b -> 14b -> 7b); unload other models |
| `OllamaTimeoutError` | Local inference timeout | Increase timeout; reduce context window; check GPU load |
| `OllamaJSONParseError` | Response parsing failed | Retry with lower temperature; log raw response |

### 9.5 Ollama Error Handling

```python
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
```

### 9.6 Ollama Retry Strategy

```python
@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((
        OllamaTimeoutError, OllamaOutOfMemoryError
    )),
    before_sleep=log_ollama_retry,
)
async def ollama_call_with_retry(
    client: OllamaClient,
    prompt: str,
    model: str,
) -> OllamaGenerateResponse:
    """Call Ollama with automatic retry for transient failures.

    On OllamaOutOfMemoryError: falls back to smaller model.
    On OllamaTimeoutError: retries with increased timeout.
    """
    return await client.generate(prompt=prompt, model=model)
```

---

## 10. Performance

### 10.1 Async HTTP
- `httpx.AsyncClient` with HTTP/2 and connection pooling
- Default pool: 20 connections per host
- Keep-alive enabled for repeated requests to same domain

### 10.2 Browser Pool
- Fixed-size pool of browser contexts (default: 3)
- Contexts are reused across requests to same platform
- Pages are recycled, not recreated per request

### 10.3 Connection Pooling
```python
# HTTP client configuration
self.http_client = httpx.AsyncClient(
    http2=True,
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    timeout=httpx.Timeout(30.0),
    follow_redirects=True,
)
```

### 10.4 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| HTTP scrape | < 5 seconds | Includes fetch + parse + extract |
| Browser scrape | < 15 seconds | Includes render + wait + extract |
| Batch concurrent | 100 URLs | With default rate limits |
| Memory per scrape | < 50 MB | HTTP mode |
| Memory per browser | < 200 MB | Chromium process |
| Selector evaluation | < 100ms | Per field, per document |
| Ollama inference (7b) | < 15s | End-to-end: prompt -> generation -> parse |
| Ollama inference (7b) | < 8s | Faster model for small tasks |
| Ollama inference (32b) | < 30s | Premium model for complex tasks |
| Ollama cache hit retrieval | < 50ms | Local cache lookup |
| HTML chunking | < 200ms | Split large HTML into context-safe chunks |
| Model load time (7b) | < 5s | First call after Ollama start |
| VRAM usage (7b) | ~4.5GB | GPU memory for dolphincoder:7b |

### 10.5 Ollama Local Inference Optimization

**HTML Chunking for Large Pages:**
When HTML exceeds the model's context window (128K tokens for `dolphincoder:7b`), the `HTMLChunker` splits the document at element boundaries while preserving DOM context overlap between chunks:

```python
# Chunking example
chunker = HTMLChunker(max_chars=48000, overlap_chars=3000)
chunks = chunker.chunk(large_html)  # Returns 1-3 chunks depending on size

# Each chunk is processed sequentially
results = []
for chunk in chunks:
    result = await ollama_engine.extract(chunk, context)
    results.append(result)

# Merge results from all chunks
merged = merge_extraction_results(results)
```

**GPU Layer Offloading Configuration:**
Ollama automatically manages GPU layer offloading. For fine-grained control:

```python
# In phoenix.toml
[ai]
gpu_layers = 35  # Number of layers to offload to GPU (auto-detect if null)

# Or via environment
# OLLAMA_GPU_LAYERS=35
```

**Context Window Management:**
The `num_ctx` option controls the context window size. Smaller contexts load faster and use less VRAM:

```python
# Ollama generate API call with context management
response = await ollama_client.generate(
    prompt=prompt,
    model="dolphincoder:7b",
    options={
        "temperature": 0.1,
        "num_ctx": 8192,  # Smaller context for faster inference
        "num_predict": 4096,  # Max tokens to generate
    },
)
```

**Batch Processing for Multiple Pages:**
Process multiple pages efficiently by managing model keep-alive and batching:

```python
# Batch processing with model keep-alive
async def batch_extract(urls: list[str]) -> list[OllamaExtractionResult]:
    results = []
    for url in urls:
        html = await fetch_html(url)
        result = await ollama_engine.extract(
            html,
            context=ExtractionContext(url=url),
        )
        results.append(result)
    return results
```

**Model Keep-Alive Settings:**
Prevent model from unloading between requests for faster consecutive calls:

```toml
# phoenix.toml
[ai]
keep_alive = "5m"  # Keep model loaded for 5 minutes after last use
```

**Concurrent Inference with Semaphore Control:**
A semaphore limits concurrent Ollama calls to prevent VRAM exhaustion:

```python
ollama_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent inference calls

async def extract_with_semaphore(html, context):
    async with ollama_semaphore:
        return await ollama_engine.extract(html, context)
```

**Response Caching Strategy:**
Identical HTML (hashed by SHA-256) returns cached results, skipping redundant inference:

```python
cache_key = sha256(html + str(context.extraction_schema)).hexdigest()
cached = await cache.get(cache_key)
if cached:
    return cached  # Skip inference entirely

result = await ollama_client.generate(...)
await cache.set(cache_key, result, ttl=3600)
```

**Model Selection Strategy:**
| HTML Size | Model | Reason |
|-----------|-------|--------|
| < 50KB | `dolphincoder:7b` | Fast, low VRAM for small pages |
| 50KB-200KB | `dolphincoder:7b` | Balanced speed/accuracy |
| > 200KB | `qwen2.5-coder:32b` | Maximum accuracy for complex pages |
| Classification only | `dolphincoder:7b` | Small prompt, fast response |
| Selector repair | `dolphincoder:7b` | Focused task, moderate context |
| Entity resolution | `dolphincoder:7b` | Analytical, moderate context |

**Hardware-Based Model Selection:**
| Available VRAM | Recommended Model | Notes |
|----------------|-------------------|-------|
| < 6GB | `dolphincoder:7b` | GPU-only or CPU fallback |
| 6-12GB | `dolphincoder:7b` | Comfortable fit |
| 12-24GB | `qwen2.5-coder:32b` | Premium accuracy |
| 24GB+ | `qwen2.5-coder:32b` | Full capability |
| CPU only | `qwen2.5:7b` | Slower but functional |

---

## 11. File Structure

```
phoenix/
|____ init__.py                    # Public API exports
|____ __main__.py                  # CLI entry point
|____ engine.py                    # PhoenixEngine class
|____ exceptions.py                # Custom exceptions
|
|____ cli/                         # Layer 1: Interfaces
|   |____ main.py                  # Typer app definition
|   |____ formatters.py            # Output formatting
|   |____ utils.py                 # CLI utilities
|
|____ router.py                    # Layer 2: URLRouter
|____ strategy_selector.py         # Layer 2: StrategySelector
|____ pipeline.py                  # Layer 2: PipelineController
|
|____ scrapers/                    # Layer 3 + 4: Scraping Engines + Platform Scrapers
|   |____ __init__.py
|   |____ base.py                  # ScraperPlugin ABC
|   |____ http.py                  # HTTPScraper
|   |____ browser.py               # BrowserScraper
|   |____ browser_pool.py          # Browser pool management
|   |____ selectors.py             # SelectorEngine
|   |
|   |____ instagram/               # InstagramScraper
|   |   |____ __init__.py
|   |   |____ scraper.py
|   |   |____ selectors.py         # Versioned CSS/XPath selector set
|   |   |____ parser.py            # Instagram-specific parsing
|   |
|   |____ x_twitter/               # XScraper
|   |   |____ __init__.py
|   |   |____ scraper.py
|   |   |____ selectors.py         # Versioned CSS/XPath selector set
|   |   |____ parser.py
|   |
|   |____ tiktok/                  # TikTokScraper
|   |____ linkedin/                # LinkedInScraper
|   |____ facebook/                # FacebookScraper
|   |____ youtube/                 # YouTubeScraper
|   |____ generic_web/             # GenericWebScraper
|
|____ plugins/                     # Plugin system
|   |____ loader.py                # PluginLoader
|   |____ manifest.py              # PluginManifest model
|
|____ processing/                  # Layer 5: Processing
|   |____ html_extractor.py        # HTMLExtractor (BeautifulSoup + selectors)
|   |____ normalizer.py            # ContentNormalizer
|   |____ ollama_engine.py         # OllamaAIEngine (HTML extraction, selector repair)
|   |____ ollama_client.py         # OllamaClient (httpx HTTP to localhost:11434)
|   |____ model_manager.py         # ModelManager (pull/verify/select/unload models)
|   |____ model_selector.py        # ModelSelector (auto-select model tier)
|   |____ hardware_monitor.py      # HardwareMonitor (GPU/VRAM/RAM monitoring)
|   |____ html_chunker.py          # HTMLChunker (context-safe HTML splitting)
|   |____ ai_cache.py              # AIResponseCache (local disk or memory caching)
|   |____ archiver.py              # SourceArchiver
|
|____ models/                      # Data models
|   |____ output.py                # UnifiedOutput, ScrapingResult
|   |____ document.py              # HTMLDocument
|   |____ session.py               # Session
|   |____ config.py                # Config
|   |____ selectors.py             # SelectorSet, SelectorChain, etc.
|   |____ plugin.py                # PluginManifest
|   |____ diagnostics.py           # Diagnostics, ScrapingError
|   |____ ollama.py                # OllamaExtractionResult, ModelInfo, HardwareProfile
|
|____ infrastructure/              # Layer 6: Infrastructure
|   |____ session_manager.py       # Cookie/session management
|   |____ storage.py               # SQLite/JSON storage
|   |____ rate_limiter.py          # Token bucket rate limiting
|   |____ config_manager.py        # TOML configuration
|   |____ audit_logger.py          # Audit trail logging
|
|____ utils/                       # Utilities
    |____ url.py                   # URL parsing utilities
    |____ html.py                  # HTML cleaning utilities
    |____ retry.py                 # Retry decorators
```
