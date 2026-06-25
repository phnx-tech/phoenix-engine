# Phoenix Engine — Team Structure & Roles

> **Document Version:** 3.0
> **Last Updated:** 2025-01-21
> **Classification:** Pure Web Scraping Platform — NO Official APIs
> **Principle:** All data collection through HTTP requests + HTML parsing, headless browser automation (Playwright), CSS selectors, XPath, and regex extraction from raw HTML only.

---

## 1. Team Overview

The Phoenix Engine development team is organized around the unique demands of **large-scale web scraping infrastructure**. Unlike conventional API-first platforms, every role is designed around the challenges of:

- **Site structure volatility** — HTML layouts change without notice
- **Anti-bot countermeasures** — CAPTCHA, rate limiting, fingerprinting, WAFs
- **JavaScript-rendered content** — Single-page apps, lazy loading, infinite scroll
- **Ethical compliance** — Rate limiting, robots.txt respect, legal boundaries
- **Selector fragility** — CSS/XPath selectors break when layouts change
- **Local AI inference** — Ollama runs entirely on local hardware with zero external dependencies

The team consists of **5 AI specialized roles**, each owning distinct technical domains within the scraping pipeline.

---

## 2. Organizational Chart

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PHOENIX ENGINE TEAM                              │
│              Pure Web Scraping Platform Development                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  Ollama Dev-1   │    │   Ollama Dev-2   │    │   Ollama Dev-3   │
│  (Alpha)        │    │   (Beta)         │    │   (Gamma)        │
│                 │    │                  │    │                  │
│ Core Scraping   │    │ Social Platform  │    │ Web Scrapers +   │
│ + Local AI      │    │ HTML Scrapers    │    │ Plugin System    │
│ Engine          │    │                  │    │                  │
│                 │    │                  │    │                  │
│ • HTTP scraper  │    │ • Instagram      │    │ • Facebook       │
│ • Browser scraper│   │ • X/Twitter      │    │ • YouTube        │
│ • Selector eng. │    │ • TikTok         │    │ • Generic web    │
│ • Pipeline ctrl │    │ • LinkedIn       │    │ • Plugin SDK     │
│ • Ollama AI eng.│    │                  │    │                  │
│ • Model mgmt    │    │                  │    │                  │
│ • HW monitoring │    │                  │    │                  │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                       │
         └──────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │      Ollama DevOps      │
                    │  (Scraping + AI Infra)  │
                    │                        │
                    │ • Ollama service mgmt  │
                    │ • GPU/CPU monitoring   │
                    │ • Cookie/session mgmt  │
                    │ • Proxy infrastructure │
                    │ • Browser instance pool│
                    │ • Rate limiting        │
                    │ • Storage & deployment │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │      Ollama QA Lead     │
                    │ (Scraping + AI QA)      │
                    │                        │
                    │ • Mock HTML fixtures    │
                    │ • Ollama integration QA │
                    │ • Selector regression   │
                    │ • Hardware compat.      │
                    │ • Model accuracy QA     │
                    └────────────────────────┘
```

### Communication Flows

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Dev-1    │◄───►│ Dev-2    │◄───►│ Dev-3    │
│(Engine)  │     │(Social)  │     │(Web+Plug)│
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     └────────────────┼────────────────┘
                      │
                      ▼
               ┌────────────┐
               │  DevOps    │◄─── Infrastructure support
               │(Infra)     │     for all dev agents
               └─────┬──────┘
                     │
                     ▼
               ┌────────────┐
               │    QA      │◄─── Testing support
               │(QA Lead)   │     for all dev agents
               └────────────┘

Key Communication Patterns:
───► Direct collaboration
═══► Escalation / review
```

---

## 3. Role Definitions & Responsibilities

---

### 3.1 AI Backend Engineer Alpha — Ollama Dev-1 (Core Scraping Engine + Local AI)

**Role:** Core scraping infrastructure, local AI engine integration, and model lifecycle management
**Agent Name:** `ollama-dev-1`
**Model:** Ollama (qwen2.5:7b via localhost:11434)
**Primary Focus:** Universal scraping primitives that power all platform-specific scrapers, plus the entire Ollama local AI layer

#### Detailed Responsibilities

| Area | Responsibility | Scraping-Specific Detail |
|------|---------------|-------------------------|
| **HTTP Scraper** | Build HTTP-based scraping module | `httpx` async client with custom headers, user-agent rotation, redirect handling, cookie jar integration, response decoding (gzip, brotli), timeout management per domain |
| **Browser Scraper** | Build Playwright integration | Headless Chromium/Firefox/WebKit automation, stealth plugin injection, viewport emulation, navigator.webdriver patch, canvas fingerprint randomization |
| **Selector Engine** | HTML parsing and extraction engine | CSS selector chains with fallback, XPath support, regex extraction helpers, multi-strategy fallback (CSS → XPath → regex → structural heuristics), selector health scoring |
| **Pipeline Controller** | Async orchestration layer | Coroutine-based task scheduling, backpressure handling, circuit breaker pattern for failed domains, priority queuing, pipeline stage composition |
| **Retry Logic** | Intelligent retry system | Exponential backoff with jitter, domain-specific retry policies, transient failure detection (5xx, timeouts), permanent failure detection (404, 403 patterns) |
| **Output Normalizer** | Unified data normalization | Raw HTML → structured JSON transformation schema, content-type detection, metadata extraction (title, author, timestamp, images), consistent output format across all scrapers |
| **Audit Logging** | Comprehensive audit trail | Every request logged with URL, method, timestamp, response status, bytes received, selector used, extraction result count, errors encountered |
| **Ollama Client Wrapper** | Build Ollama HTTP client (httpx → localhost:11434) | Async httpx client communicating with Ollama API at `http://localhost:11434`, JSON mode, streaming support, timeout handling, connection pooling |
| **ModelManager** | Build model lifecycle manager (pull, verify, select, unload models) | `ollama pull qwen2.5:7b`, model verification via `ollama show`, auto-pull on first run, model unloading via `ollama rm`, garbage collection |
| **HardwareMonitor** | Build hardware detection and VRAM tracking | GPU detection (nvidia-smi, rocm-smi), CPU fallback detection, VRAM monitoring, available RAM tracking, temperature throttling detection |
| **ModelSelector** | Build hardware-aware model selector (auto-select 7b/14b/32b based on hardware) | VRAM-based tier selection: ≥16GB → 7b (optional), ≥8GB → 7b, CPU-only → 7b with quantization awareness, override via config |
| **OllamaAIEngine** | Build Ollama AI extraction, classification, repair, entity resolution engines | Structured JSON extraction via `/api/generate`, content type classification, broken selector repair suggestions, cross-platform entity resolution, low temperature (0.1) for deterministic output |
| **HTML Chunker** | Build HTML chunker for Ollama context window limits | Split large HTML to fit qwen2.5:7b context window (16384 tokens), semantic boundary detection, chunk overlap for coherence |

#### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|------------|---------------------|
| D1.1 | HTTP scraper module | Successfully fetches and parses 100 test URLs with <2% failure rate |
| D1.2 | Browser scraper module | Playwright automation passes 50 stealth detection tests |
| D1.3 | Selector engine | CSS/XPath/regex fallback chains work on 20 diverse HTML structures |
| D1.4 | Pipeline controller | Handles 1000 concurrent tasks without memory leaks |
| D1.5 | Output normalizer | All scrapers produce identical JSON schema regardless of source |
| D1.6 | Audit logger | Every request/response cycle fully logged with searchable fields |
| D1.7 | Ollama client wrapper | Successful HTTP communication with localhost:11434, JSON parsing, error handling |
| D1.8 | ModelManager | Model pull/verify/unload works, auto-pull on first run succeeds |
| D1.9 | HardwareMonitor | Accurate GPU/CPU/VRAM detection on test hardware profiles |
| D1.10 | ModelSelector | Correct tier selection (7b/14b) based on VRAM availability |
| D1.11 | OllamaAIEngine | ≥80% extraction accuracy, <10s inference time on target hardware |
| D1.12 | HTML chunker | Large HTML split without tag breakage, fits context window |

#### Agent Configuration

```yaml
agent: ollama-dev-1
name: "Core Scraping Engine + Local AI Developer"
model: "qwen2.5:7b"  # Runs via Ollama on localhost:11434
system_prompt: |
  You are an expert Python developer specializing in web scraping infrastructure
  and local AI integration with Ollama. You build high-performance, resilient
  scraping engines using httpx, Playwright, BeautifulSoup, lxml, and cssselect.
  You also build Ollama integration components: HTTP client wrappers, model
  lifecycle management, hardware detection, and AI-powered extraction pipelines.

  Core principles:
  - All extraction from raw HTML only (no official APIs)
  - Resilient selector fallback chains
  - Async/await patterns for concurrency
  - Comprehensive error handling and retry logic
  - Audit logging for every operation
  - Local AI-first: Ollama runs at localhost:11434 with zero external dependencies
  - Hardware-aware: auto-detect GPU/CPU, select appropriate model tier
  - Graceful degradation: selectors → browser → Ollama (local AI) → error

  You work on: HTTP scraper, browser scraper, selector engine, pipeline controller,
  Ollama client wrapper, ModelManager, HardwareMonitor, ModelSelector,
  OllamaAIEngine, HTML chunker for context window limits.
context_window: 16384  # qwen2.5:7b context window
temperature: 0.2  # Low temperature for consistent code generation
specialization: [async_python, web_scraping, playwright, beautifulsoup, lxml, ollama, local_ai, gpu_computing]
```

---

### 3.2 AI Backend Engineer Beta — Ollama Dev-2 (Social Platform HTML Scrapers)

**Role:** Social media platform scraper development
**Agent Name:** `ollama-dev-2`
**Model:** Ollama (qwen2.5:7b via localhost:11434)
**Primary Focus:** HTML structure analysis and scraper implementation for social platforms

#### Detailed Responsibilities

| Area | Responsibility | Scraping-Specific Detail |
|------|---------------|-------------------------|
| **Instagram Scraper** | Extract posts, reels, profiles from HTML | CSS selectors for post grids, reel metadata, profile headers, story highlights; handle both static HTML and JS-rendered content; pagination through scroll simulation |
| **X/Twitter Scraper** | Extract tweets and profiles from HTML | Selectors for tweet text, timestamps, engagement metrics, media attachments, reply chains; profile bio, follower counts, pinned tweets; handle dynamic loading |
| **TikTok Scraper** | Extract videos and profiles from HTML | Selectors for video metadata, captions, hashtags, view counts, creator info; handle heavy JavaScript rendering via Playwright; pagination through load-more buttons |
| **LinkedIn Scraper** | Extract public posts and profiles from HTML | Selectors for post content, engagement metrics, profile sections, experience/education; respect public visibility only; handle auth-walled content gracefully |
| **HTML Analysis** | Reverse-engineer site structures | Manual HTML inspection, DOM tree analysis, minified JS parsing for data locations, network request interception for XHR/fetch API calls containing structured data |
| **Selector Maintenance** | Keep selectors current | Document selector rationale, version selectors per site layout version, monitor selector health across scraping runs |
| **Pagination** | Handle all pagination patterns | Infinite scroll detection and simulation, load-more button clicking, page number URL patterns, cursor-based pagination from JS variables |

#### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|------------|---------------------|
| D2.1 | Instagram scraper | Extracts posts, reels, profiles with >95% field coverage from public pages |
| D2.2 | X/Twitter scraper | Extracts tweets, profiles with full metadata (text, time, engagement, media) |
| D2.3 | TikTok scraper | Extracts video metadata, profiles with caption, hashtag, view count accuracy |
| D2.4 | LinkedIn scraper | Extracts public posts, profile sections from public visibility pages |
| D2.5 | Selector documentation | Each selector documented with HTML context, fallback chain, and last verified date |
| D2.6 | Pagination handlers | All 4 pagination types (scroll, load-more, page-number, cursor) working |

#### Agent Configuration

```yaml
agent: ollama-dev-2
name: "Social Platform Scraper Developer"
model: "qwen2.5:7b"  # Runs via Ollama on localhost:11434
system_prompt: |
  You are an expert web scraping developer specializing in social media platforms.
  You extract data from raw HTML using CSS selectors, XPath, and browser automation.
  You NEVER use official APIs — all extraction is through HTML parsing and
  headless browser automation.

  Platform expertise: Instagram, X/Twitter, TikTok, LinkedIn
  Techniques: CSS selector chains, XPath, Playwright automation, infinite scroll
  simulation, load-more button handling, cookie-based auth session management.

  You analyze HTML structure, build robust selector fallback chains, and handle
  the unique anti-bot measures of each platform through stealth techniques and
  realistic browsing patterns.
specialization: [social_media_scraping, instagram, twitter, tiktok, linkedin, css_selectors]
```

---

### 3.3 AI Backend Engineer Gamma — Ollama Dev-3 (Web Scrapers + Plugin System)

**Role:** General web scrapers and extensible plugin architecture
**Agent Name:** `ollama-dev-3`
**Model:** Ollama (qwen2.5:7b via localhost:11434)
**Primary Focus:** Broader web scraping, content extraction, and developer-extensible plugin framework

#### Detailed Responsibilities

| Area | Responsibility | Scraping-Specific Detail |
|------|---------------|-------------------------|
| **Facebook Scraper** | Extract posts, pages, groups from HTML | Handle heavy JS rendering, selectors for post content, reactions, comments, page about sections; handle login-state dependent content gracefully |
| **YouTube Scraper** | Extract videos, channels, transcripts from HTML | Video metadata from page source, channel info, **transcript extraction from page source HTML** (caption tracks in ytInitialPlayerResponse), comment thread handling |
| **Generic Web Scraper** | Universal article/content extraction from any HTML | Smart content extraction from arbitrary HTML pages — article body, title, author, publish date, main images; works on any news site, blog, or content page without site-specific configuration |
| **Plugin System** | Extensible scraper plugin architecture | URL pattern matching → selector registration system, plugin loader with hot-reload, plugin development SDK with base classes, validation framework for custom scrapers |
| **Plugin SDK** | Developer experience for plugin authors | Documentation, example plugins, template project, testing utilities, selector debugging tools |
| **Content Normalization** | Cross-site content standardization | Unified content schema regardless of source platform, media URL normalization, timestamp standardization (ISO 8601), text cleaning and entity decoding |

#### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|------------|---------------------|
| D3.1 | Facebook scraper | Extracts posts, pages with content, reactions, timestamps |
| D3.2 | YouTube scraper | Extracts video metadata, channel info, transcripts from HTML source |
| D3.3 | Generic web scraper | Successfully extracts articles from 50 diverse sites without custom config |
| D3.4 | Plugin interface | URL pattern → selector set registration working, validated with 3 example plugins |
| D3.5 | Plugin loader | Hot-reload of plugins without engine restart, dependency injection |
| D3.6 | Plugin SDK + docs | Complete documentation with working example custom scraper |

#### Agent Configuration

```yaml
agent: ollama-dev-3
name: "Web Scraper & Plugin System Developer"
model: "qwen2.5:7b"  # Runs via Ollama on localhost:11434
system_prompt: |
  You are an expert web scraping developer and framework architect. You build
  both specific scrapers for major platforms and an extensible plugin system
  that lets developers add custom scrapers. You NEVER use official APIs — all
  data extraction is through raw HTML parsing, CSS selectors, XPath, regex,
  and browser automation.

  Responsibilities: Facebook scraper, YouTube scraper (including transcript
  extraction from page source), generic universal web scraper, and a plugin
  system for custom scrapers with URL patterns and selector registration.

  You think in terms of: extensible architectures, clean interfaces,
  developer experience, and universal extraction patterns.
specialization: [web_scraping, plugin_architecture, facebook, youtube, universal_extractor, sdk_design]
```

---

### 3.4 AI DevOps Engineer — Ollama DevOps (Scraping + Local AI Infrastructure)

**Role:** Scraping-specific infrastructure, Ollama service management, deployment, and operations
**Agent Name:** `ollama-devops`
**Model:** Ollama (qwen2.5:7b via localhost:11434)
**Primary Focus:** The operational backbone that keeps scraping reliable at scale, plus Ollama local AI service lifecycle

#### Detailed Responsibilities

| Area | Responsibility | Scraping-Specific Detail |
|------|---------------|-------------------------|
| **Ollama Service Setup** | Ollama service installation and configuration | Automated Ollama installation, service auto-start, `ollama pull qwen2.5:7b` orchestration, health check endpoint polling, version pinning |
| **GPU/CPU Resource Monitoring** | GPU/CPU resource monitoring and alerting | nvidia-smi/rocm-smi polling, VRAM utilization tracking, GPU temperature alerts, CPU fallback detection, resource exhaustion prevention |
| **Model Lifecycle Management** | Model download, update, and cleanup | `ollama pull` for updates, `ollama rm` for cleanup, disk space monitoring, model verification post-download, scheduled update checks |
| **Docker Compose with Ollama + Phoenix Engine** | Container orchestration for combined stack | Docker Compose with Ollama service + Phoenix Engine, GPU passthrough (NVIDIA Container Toolkit), shared volumes, network configuration, health checks |
| **Cookie/Session Management** | Persistent encrypted session storage | SQLite/Redis-backed cookie jars per domain, AES-256 encryption at rest, session refresh detection, login-state validation, session rotation to avoid fingerprinting |
| **Proxy Management** | Proxy infrastructure for IP rotation | Proxy pool management (datacenter, residential, mobile), health checking, geographic targeting, sticky sessions for authenticated scraping, automatic failover on blocks |
| **Browser Instance Pool** | Lifecycle management of browser instances | Playwright browser context pooling, context isolation per task, memory leak prevention, automatic restart on crash, pool scaling based on queue depth, context fingerprint rotation |
| **Rate Limiting** | Ethical and configurable rate control | Per-domain delay configuration (from robots.txt parsing), adaptive rate adjustment based on response patterns (429 detection), distributed rate limiting across instances, burst handling with token bucket |
| **Storage Layer** | Raw HTML archive and structured output | Raw HTML storage with compression (zstd), structured JSON output storage, content-addressable deduplication, retention policies, backup strategy |
| **Deployment** | Container orchestration and monitoring | Docker containerization, Docker Compose for local dev, health checks, log aggregation, alerting on scraping failures, metrics collection (requests/min, success rate, latency) |
| **Monitoring** | Scraping-specific observability | Dashboard for per-domain success rates, selector failure tracking, proxy health, queue depth, browser pool utilization, anti-bot trigger detection, Ollama inference latency, GPU utilization |

#### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|------------|---------------------|
| D4.1 | Ollama service setup script | Automated install, model pull, health check — works on fresh Ubuntu 22.04 |
| D4.2 | GPU/CPU monitoring dashboard | Real-time VRAM/CPU usage, alerts at 90% utilization |
| D4.3 | Model lifecycle automation | Auto-pull on new model availability, cleanup of old versions |
| D4.4 | Docker Compose stack | Ollama + Phoenix Engine start with `docker compose up`, GPU passthrough works |
| D4.5 | Session manager | Encrypted cookie persistence, automatic rotation, >99.5% session validity |
| D4.6 | Proxy infrastructure | Automatic rotation, health checks, <1% block rate with proper configuration |
| D4.7 | Browser pool | Context isolation, automatic restart, handles 500 concurrent contexts |
| D4.8 | Rate controller | Per-domain config, 429 adaptation, no IP bans during normal operation |
| D4.9 | Storage system | Raw HTML archived, structured output queryable, compression ratio >5:1 |
| D4.10 | Deployment stack | Dockerized, health checks, monitoring dashboard, log aggregation |

#### Agent Configuration

```yaml
agent: ollama-devops
name: "Scraping + Local AI Infrastructure Engineer"
model: "qwen2.5:7b"  # Runs via Ollama on localhost:11434
system_prompt: |
  You are an expert DevOps engineer specializing in web scraping infrastructure
  and local AI deployment with Ollama. You build and operate the systems that
  make large-scale scraping and local AI inference reliable: Ollama service
  management, GPU/CPU monitoring, model lifecycle, proxy management, browser
  instance pooling, session/cookie rotation, rate limiting, storage, and monitoring.

  Core focus: Ollama service setup and configuration, GPU/CPU resource monitoring,
  model lifecycle management (download, update, cleanup), Docker Compose with
  Ollama + Phoenix Engine, cookie persistence, proxy rotation, browser lifecycle
  management, rate limiting per domain, raw HTML archive storage, containerized
  deployment, and scraping-specific monitoring.

  You ensure: ethical scraping (rate limits, robots.txt compliance),
  operational resilience (auto-restart, failover), local AI availability
  (Ollama health checks, model verification, hardware monitoring), and
  observability (per-domain metrics, anti-bot detection, inference latency).
specialization: [devops, ollama, gpu_management, scraping_infrastructure, proxy_management, docker, monitoring, redis, sqlite]
```

---

### 3.5 AI QA Lead — Ollama QA (Scraping + Local AI QA)

**Role:** Quality assurance tailored to the unique challenges of scraping and local AI inference
**Agent Name:** `ollama-qa`
**Model:** Ollama (qwen2.5:7b via localhost:11434)
**Primary Focus:** Ensuring scraper reliability amid constantly changing target sites, and Ollama integration accuracy

#### Detailed Responsibilities

| Area | Responsibility | Scraping-Specific Detail |
|------|---------------|-------------------------|
| **Mock HTML Fixtures** | Recorded HTML test fixtures | Curated library of real HTML snapshots per platform, anonymized and compressed, versioned by observed date, representative of different page states (logged in/out, different content types) |
| **Playwright Test Server** | Browser scraper testing environment | Local HTTP server serving recorded HTML fixtures, Playwright-based test harness that runs scrapers against fixtures, visual comparison for structural changes |
| **Selector Regression Tests** | Automated selector validation | Daily automated tests that run all selectors against latest recorded HTML, alert on selector misses, track selector health score over time, detect when selectors return empty or malformed data |
| **Layout Change Simulation** | HTML mutation testing | Programmatically modify HTML structures (class name changes, element reordering, attribute changes) to test selector resilience, validate fallback chain activation |
| **Cross-Site Validation** | Multi-site scraping verification | End-to-end tests across all supported platforms, data completeness validation (expected fields present), data quality checks (timestamps parseable, URLs valid, text non-empty) |
| **Anti-Bot Detection Tests** | Stealth validation | Run scrapers through bot detection services (FingerprintJS, CreepJS), verify navigator.webdriver patch, verify canvas/font fingerprint consistency, header authenticity checks |
| **Performance Tests** | Load and stress testing | Concurrent scraping load tests, memory leak detection over long runs, browser instance pool stress tests, proxy rotation under load |
| **Ollama Integration Testing** | Ollama integration testing (service mock, model stub) | Mock Ollama API server for CI, model stub for testing without GPU, HTTP client unit tests, error handling validation (service down, timeout, invalid model) |
| **Hardware Compatibility Matrix Testing** | Validate on different hardware profiles | Test matrix: GPU (NVIDIA 8GB, 16GB, 24GB) → CPU-only → Docker, verify ModelSelector picks correct tier, verify graceful CPU fallback |
| **Inference Accuracy Validation** | Model accuracy testing on local deployment | Golden test set for extraction accuracy, structured JSON validation, hallucination detection, benchmark inference latency per hardware tier |

#### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|------------|---------------------|
| D5.1 | Mock HTML fixture library | 200+ fixtures across all platforms, versioned, anonymized |
| D5.2 | Playwright test harness | Automated scraper tests against fixtures in CI/CD pipeline |
| D5.3 | Selector regression suite | Daily automated selector validation with health score dashboard |
| D5.4 | Layout change simulator | HTML mutation tests verifying fallback chain activation |
| D5.5 | Cross-site validation | End-to-end tests for all platforms, data completeness checks |
| D5.6 | Stealth validation | Passes major bot detection fingerprinting checks |
| D5.7 | Ollama integration test suite | Mock Ollama server, all integration tests pass in CI without GPU |
| D5.8 | Hardware compatibility matrix | Tested on min 3 hardware profiles: GPU 8GB, GPU 16GB, CPU-only |
| D5.9 | Inference accuracy report | ≥80% extraction accuracy on golden test set, ≤5% hallucination rate |

#### Agent Configuration

```yaml
agent: ollama-qa
name: "Scraping + Local AI QA Lead"
model: "qwen2.5:7b"  # Runs via Ollama on localhost:11434
system_prompt: |
  You are an expert QA engineer specializing in web scraping systems and
  local AI inference with Ollama. You understand that scraping is uniquely
  challenging because target sites change their HTML structure without notice,
  breaking selectors and extractors. You also validate that local AI
  inference (Ollama at localhost:11434) produces accurate, structured output.

  Your mission: Build comprehensive testing systems that catch failures before
  they reach production — both in scraping pipelines and local AI inference.

  Techniques: Mock HTML fixtures (recorded real pages), Playwright-based test
  servers, selector regression testing, HTML layout change simulation,
  cross-site validation, anti-bot stealth detection, performance testing,
  Ollama integration testing (service mock, model stub), hardware compatibility
  matrix testing, inference accuracy validation on local models.

  You create: Reliable test harnesses, HTML fixture libraries, automated
  regression detection, Ollama integration tests, hardware compatibility
  validation suites, and quality gates for CI/CD.
specialization: [qa_engineering, web_scraping_testing, playwright_testing, regression_testing, mock_fixtures, ollama_testing, hardware_validation]
```

---

## 4. RACI Matrix

### Legend: R=Responsible, A=Accountable, C=Consulted, I=Informed

#### Phase 1 — Core Scraping Engine

| Task | Dev-1 (Alpha) | Dev-2 (Beta) | Dev-3 (Gamma) | DevOps | QA |
|------|:-----------:|:----------:|:-----------:|:----:|:--:|
| HTTP scraper module (httpx + BeautifulSoup/lxml) | **R/A** | C | C | C | I |
| Browser scraper module (Playwright) | **R/A** | C | C | C | I |
| HTML selector engine (CSS + XPath + fallback) | **R/A** | C | C | C | I |
| Pipeline controller (async orchestration) | **R/A** | C | C | C | I |
| Unified output normalizer | **R/A** | C | C | C | I |
| Error handling & retry logic | **R/A** | I | I | C | C |
| Audit logging system | **R/A** | I | I | C | C |

#### Phase 2 — Platform HTML Scrapers

| Task | Dev-1 (Alpha) | Dev-2 (Beta) | Dev-3 (Gamma) | DevOps | QA |
|------|:-----------:|:----------:|:-----------:|:----:|:--:|
| Instagram HTML scraper | C | **R/A** | I | C | C |
| X/Twitter HTML scraper | C | **R/A** | I | C | C |
| TikTok HTML scraper | C | **R/A** | I | C | C |
| LinkedIn HTML scraper | C | **R/A** | I | C | C |
| Facebook HTML scraper | C | I | **R/A** | C | C |
| YouTube HTML scraper | C | I | **R/A** | C | C |
| Generic web scraper | C | I | **R/A** | C | C |
| HTML structure analysis | C | **R/A** | **R/A** | I | C |
| Pagination handlers | C | **R** | **R** | I | **A** |
| Auth/cookie flow simulation | C | **R** | **R** | **A** | C |
| Platform-specific HTML fixtures | I | **R** | **R** | I | **A** |

#### Phase 3 — Local AI Intelligence Layer (Ollama)

| Task | Dev-1 (Alpha) | Dev-2 (Beta) | Dev-3 (Gamma) | DevOps | QA |
|------|:-----------:|:----------:|:-----------:|:----:|:--:|
| Ollama client wrapper (httpx → localhost:11434) | **R/A** | I | I | C | C |
| ModelManager (pull, verify, select, unload) | **R/A** | I | I | **C** | C |
| HardwareMonitor (GPU/CPU detection, VRAM tracking) | **R/A** | I | I | **C** | C |
| ModelSelector (auto-select 7b/14b based on hardware) | **R/A** | I | I | C | **C** |
| OllamaAIEngine (extraction, classification, repair) | **R/A** | C | C | I | **A** |
| HTML chunker for Ollama context window limits | **R/A** | I | I | I | C |
| Smart fallback orchestrator (selectors → Ollama → error) | **R/A** | C | C | I | **A** |
| Ollama service setup and configuration | C | I | I | **R/A** | C |
| Model auto-pull on first run | **R** | I | I | **R/A** | C |
| Hardware-aware model selection validation | **R** | I | I | C | **A** |
| OOM handling and model fallback | **R/A** | I | I | **C** | C |

#### Phase 4 — Infrastructure

| Task | Dev-1 (Alpha) | Dev-2 (Beta) | Dev-3 (Gamma) | DevOps | QA |
|------|:-----------:|:----------:|:-----------:|:----:|:--:|
| Ollama service setup and configuration | C | I | I | **R/A** | C |
| GPU/CPU resource monitoring and alerting | C | I | I | **R/A** | C |
| Model lifecycle management (download, update, cleanup) | C | I | I | **R/A** | C |
| Docker Compose with Ollama + Phoenix Engine | C | I | I | **R/A** | C |
| Cookie/session manager (encrypted) | C | I | I | **R/A** | C |
| Browser instance pool management | C | I | I | **R/A** | C |
| Proxy rotation infrastructure | I | I | I | **R/A** | C |
| Rate controller (per-domain delays) | C | I | I | **R/A** | C |
| Raw HTML archive storage | I | I | I | **R/A** | C |
| Export system (JSON, CSV) | I | I | C | **R/A** | C |
| Docker deployment | I | I | I | **R/A** | I |
| Monitoring & alerting | I | I | I | **R/A** | C |

#### Phase 5 — Plugin System

| Task | Dev-1 (Alpha) | Dev-2 (Beta) | Dev-3 (Gamma) | DevOps | QA |
|------|:-----------:|:----------:|:-----------:|:----:|:--:|
| Plugin interface design | C | I | **R/A** | I | C |
| Plugin loader & registration | I | I | **R/A** | C | C |
| Plugin SDK development | I | I | **R/A** | I | C |
| Example custom scraper plugin | C | C | **R/A** | I | **A** |
| Plugin validation framework | I | I | **R** | I | **A** |

---

## 5. Communication Flows & Protocols

### 5.1 Daily Standup Pattern

```
Time: Async, daily
Format:
  1. What HTML structures changed since last check?
  2. What selectors broke and were fixed?
  3. What anti-bot measures were encountered?
  4. Ollama service health and inference status?
  5. GPU/VRAM utilization and model performance?
  6. Blockers that need cross-team help?
  7. Proxy/session health status?
```

### 5.2 Cross-Agent Collaboration Patterns

| Scenario | Primary | Secondary | Protocol |
|----------|---------|-----------|----------|
| New platform scraper needed | Dev-2/3 | Dev-1 | Dev-2/3 requests engine feature → Dev-1 implements primitive → Dev-2/3 builds scraper |
| Selector breaking in production | Dev-2/3 | QA | Dev-2/3 gets QA alert → fixes selector → QA validates with fixtures |
| Anti-bot blocking | Dev-2/3 | DevOps | Dev-2/3 reports pattern → DevOps adjusts proxy/session strategy |
| Browser automation bug | Dev-1 | DevOps | Dev-1 diagnoses → DevOps adjusts pool config if infrastructure-related |
| Plugin API change | Dev-3 | Dev-1 | Dev-3 proposes interface change → Dev-1 reviews engine impact |
| HTML layout overhaul on target | Dev-2/3 | All | Dev-2/3 analyzes new structure → updates selectors → QA adds new fixtures |
| Ollama service down | DevOps | Dev-1, QA | DevOps restores service → Dev-1 verifies AI pipeline → QA runs accuracy tests |
| Model inference failure | Dev-1 | DevOps, QA | Dev-1 diagnoses model/config issue → DevOps checks GPU → QA validates output |
| New Ollama model release | DevOps | Dev-1, QA | DevOps pulls new model → Dev-1 runs extraction tests → QA validates accuracy |

### 5.3 Escalation Path

```
Level 1: Individual agent solves within their domain
    │
    ▼ (if cross-domain impact)
Level 2: Direct collaboration between 2 agents
    │
    ▼ (if architectural decision needed)
Level 3: All dev agents + DevOps discussion
    │
    ▼ (if fundamental approach question)
Level 4: Full team review including QA
```

### 5.4 Code Review Requirements

| Component | Reviewer Required | Focus Areas |
|-----------|------------------|-------------|
| Core engine changes (Dev-1) | Dev-2 or Dev-3 + QA | API stability, performance impact, backward compatibility |
| Platform scraper changes (Dev-2) | Dev-1 + QA | Selector quality, reuse of engine primitives, fixture coverage |
| Web scraper/plugin changes (Dev-3) | Dev-1 + QA | Plugin API consistency, generic extractor patterns |
| Infrastructure changes (DevOps) | Any dev agent | Impact on scraping operations, Ollama service, monitoring coverage |
| Test additions (QA) | Relevant dev agent | Fixture quality, test coverage, selector scenarios |
| Ollama AI changes (Dev-1) | DevOps + QA | Hardware compatibility, inference accuracy, service health |

---

## 6. Technical Standards

### 6.1 Scraping Code Standards

```python
# Example: Standard scraper structure following team conventions
class BaseScraper:
    """All scrapers extend this base class."""

    # Selector chains with fallbacks — REQUIRED
    SELECTORS = {
        "post_text": [
            "div[data-testid='tweetText']",           # Primary CSS
            "//div[contains(@class, 'tweet-text')]",  # Fallback XPath
            r'"text":"([^"]{10,})"',                  # Fallback regex in JS
        ],
        "timestamp": [
            "time[datetime]",
            "//time/@datetime",
        ]
    }

    # Per-domain configuration — REQUIRED
    CONFIG = {
        "rate_limit_delay": 2.0,      # seconds between requests
        "retry_attempts": 3,
        "use_browser": False,          # HTTP vs Browser auto-detect
        "selector_timeout": 10,        # seconds to wait for element
    }

    # Audit logging — REQUIRED for every operation
    async def scrape(self, url: str) -> ScrapingResult:
        self.audit_log.start(url)
        try:
            html = await self.fetch(url)
            data = await self.extract(html)
            self.audit_log.success(url, data.fields_found)
            return ScrapingResult.success(data)
        except SelectorNotFound as e:
            self.audit_log.selector_failed(url, e.selector)
            raise
        except Exception as e:
            self.audit_log.error(url, str(e))
            raise
```

### 6.2 Selector Documentation Standard

```yaml
# Every selector must be documented with this metadata
selectors:
  post_text:
    description: "Main post/tweet text content"
    primary: "div[data-testid='tweetText']"
    fallback_1: "//div[contains(@class, 'tweet-text')]"
    fallback_2: 'regex:r"text\":\"([^\"]{10,})\"'
    last_verified: "2025-01-15"
    html_context: "<div data-testid='tweetText'>...</div>"
    expected_cardinality: "1 per post"
    platforms: ["x", "twitter"]
```

### 6.3 Ethical Scraping Policy

All team members adhere to:

1. **Respect robots.txt** — Check and honor directives for all domains
2. **Rate limiting** — Default 1 req/sec minimum, configurable per domain
3. **No authenticated scraping of private content** — Public pages only
4. **Minimal resource usage** — No unnecessary requests, cache when possible
5. **Identify via User-Agent** — Clear identification in custom User-Agent string
6. **Handle blocks gracefully** — Back off on 429/403, never aggressively retry
7. **Data retention limits** — Raw HTML purged per retention policy, extracted data only

### 6.4 Ollama Integration Standards

```python
# Example: Ollama client integration pattern
class OllamaAIEngine:
    """Ollama AI extraction engine — local AI fallback."""

    # Ollama endpoint and model configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "qwen2.5:7b"
    FALLBACK_MODEL = "qwen2.5:7b"
    MAX_CONTEXT_TOKENS = 16384
    TEMPERATURE = 0.1

    async def extract(
        self,
        html: str,
        url: str,
        platform: str,
        schema_description: str,
    ) -> dict[str, Any]:
        """Extract structured data using local Ollama inference."""
        # Hardware-aware model selection
        model = await self.model_selector.select_best_model()

        # Chunk HTML to fit context window
        chunks = self.html_chunker.chunk(html, max_tokens=self.MAX_CONTEXT_TOKENS)

        # Build extraction prompt
        prompt = self._build_extraction_prompt(chunks[0], url, platform, schema_description)

        # Call Ollama via HTTP
        response = await self._call_ollama_generate(model, prompt)

        # Parse and validate JSON
        return self._parse_json_response(response)

    async def _call_ollama_generate(self, model: str, prompt: str) -> dict[str, Any]:
        """Call Ollama /api/generate endpoint via httpx."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": self.TEMPERATURE,
                        "num_ctx": self.MAX_CONTEXT_TOKENS,
                    },
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()
```

---

## 7. Agent Summary Table

| Agent | Role | Key Technologies | Primary Output |
|-------|------|-----------------|----------------|
| **Ollama Dev-1** (Alpha) | Core Scraping Engine + Local AI | httpx, Playwright, BeautifulSoup, lxml, cssselect, XPath, asyncio, Ollama API, GPU computing | Scraping engine modules, Ollama client, ModelManager, HardwareMonitor, ModelSelector, OllamaAIEngine |
| **Ollama Dev-2** (Beta) | Social Platform Scrapers | Playwright, CSS selectors, XPath, cookie management | Instagram, X, TikTok, LinkedIn scrapers |
| **Ollama Dev-3** (Gamma) | Web Scrapers + Plugin System | Universal extraction, plugin architecture, SDK | Facebook, YouTube, generic scraper, plugin system |
| **Ollama DevOps** | Scraping + Local AI Infrastructure | Ollama, Docker, GPU management, Redis, SQLite, proxy management, monitoring | Infrastructure stack, Ollama service, deployment, GPU monitoring |
| **Ollama QA** | Scraping + Local AI QA | Playwright testing, mock fixtures, regression testing, Ollama integration testing, hardware validation | Test suites, fixture library, Ollama integration tests, hardware compat matrix, quality gates |

---

## 8. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | System | Initial team structure |
| 2.0 | 2025-01-21 | System | Complete rewrite for pure scraping focus, updated all 5 roles with scraping-specific responsibilities, added RACI matrix, communication flows, ethical scraping policy |
| 3.0 | 2025-01-22 | System | Migrated from Kimi API (Moonshot AI) to Ollama (Local AI): renamed all roles (Ollama Dev-1/2/3/DevOps/QA), added Ollama-specific responsibilities (ModelManager, HardwareMonitor, ModelSelector, OllamaAIEngine, HTML chunker), updated agent YAML configs with Ollama context, added Ollama integration standards, expanded RACI matrix for Phase 3 with Ollama tasks |
