# Phoenix Engine — Risk Management Plan

## Universal Web Scraping Platform v1.0 — Ollama Local AI Edition

**Status**: Draft | **Version**: 2.0 | **Last Updated**: 2025-01-20

---

## 1. Document Purpose

This Risk Management Plan identifies, assesses, and defines mitigation strategies for all significant risks facing the Phoenix Engine universal web scraping platform. Risk management is a continuous process integrated into every phase of product development, deployment, and operation. This document establishes the risk register, monitoring framework, issue resolution process, and lessons learned capture methodology.

**AI Architecture Update**: Phoenix Engine now uses **Ollama** with locally-hosted models (`qwen2.5:7b` and `qwen2.5:7b`) for all AI-powered features. All inference runs locally on the user's machine — no external AI APIs, no API keys, no usage costs, no rate limits, full privacy. This eliminates the Kimi API dependency, token cost, and external data residency risks while introducing hardware-related risks.

**Scope**: This plan covers technical risks inherent to web scraping and local AI inference, legal and compliance risks associated with automated data collection, and operational risks related to platform maintenance and hardware management.

---

## 2. Risk Assessment Methodology

### 2.1 Probability Scale (1-5)

| Rating | Level | Description |
|--------|-------|-------------|
| 1 | Rare | Unlikely to occur; may happen in exceptional circumstances (< 5% likelihood) |
| 2 | Unlikely | Could occur but is not expected (5-20% likelihood) |
| 3 | Possible | May occur under certain conditions (20-50% likelihood) |
| 4 | Likely | Will probably occur in most circumstances (50-80% likelihood) |
| 5 | Almost Certain | Expected to occur regularly (> 80% likelihood) |

### 2.2 Impact Scale (1-5)

| Rating | Level | Description |
|--------|-------|-------------|
| 1 | Negligible | Minimal impact; easily absorbed by normal operations |
| 2 | Minor | Limited impact; manageable with minor adjustments |
| 3 | Moderate | Noticeable impact; requires dedicated resources to address |
| 4 | Major | Significant impact; threatens project timelines or major functionality |
| 5 | Critical | Severe impact; could halt operations, cause legal liability, or endanger project viability |

### 2.3 Risk Score Matrix

| | Impact 1 | Impact 2 | Impact 3 | Impact 4 | Impact 5 |
|---|----------|----------|----------|----------|----------|
| **Probability 5** | 5 (Low) | 10 (Med) | 15 (High) | 20 (Crit) | **25 (Crit)** |
| **Probability 4** | 4 (Low) | 8 (Med) | 12 (High) | **16 (High)** | **20 (Crit)** |
| **Probability 3** | 3 (Low) | 6 (Med) | 9 (Med) | **12 (High)** | **15 (High)** |
| **Probability 2** | 2 (Low) | 4 (Low) | 6 (Med) | 8 (Med) | **10 (Med)** |
| **Probability 1** | 1 (Low) | 2 (Low) | 3 (Low) | 4 (Low) | 5 (Low) |

**Legend**: 1-5 Low (Green) | 6-10 Medium (Yellow) | 12-16 High (Orange) | 20-25 Critical (Red)

---

## 3. Risk Register

### 3.1 Technical Risks

#### R-T01: Website Layout Changes Breaking CSS Selectors

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T01 |
| **Category** | Technical |
| **Description** | Social media platforms and websites frequently redesign their HTML structure, class names, and DOM hierarchy. When this occurs, our carefully crafted CSS selectors no longer match the intended elements, causing scrapers to fail or return empty/partial data. This is the single most persistent and impactful risk in any web scraping operation. Instagram, X, and TikTok are particularly aggressive about HTML changes for anti-scraping purposes. |
| **Probability** | 5 (Almost Certain) |
| **Impact** | 5 (Critical) |
| **Risk Score** | **25 — Critical** |
| **Owner** | Lead Scraping Engineer |
| **Trigger** | Selector match rate drops below 80%; user reports empty extraction; monitoring alerts for repeated fallback selector activation |

**Mitigation Strategy**:
1. Implement 3-tier selector fallback system (F13) where primary, secondary, and tertiary selector sets are attempted before failure
2. Design selectors to target semantic HTML structure and data attributes rather than auto-generated class names where possible
3. Maintain versioned selector configurations in easily updatable YAML files with hot-reload capability
4. Deploy automated HTML structure monitoring that periodically fetches target pages and validates selector match rates
5. Use data-testid attributes and ARIA labels as more stable selector anchors when available
6. Maintain relationships with community scraper projects to share selector intelligence

**Contingency Plan**:
1. If primary selectors fail across a platform, immediately activate fallback selector sets and alert the team
2. Deploy emergency selector updates via configuration hot-reload within 4 hours of detection
3. For severe breakage, temporarily reduce scrape frequency for affected platform to avoid wasted requests
4. If all selector sets fail, queue scrape jobs and retry every 6 hours until selectors are updated
5. Engage Ollama Local AI Extraction (F14) to generate candidate selectors from changed HTML for rapid validation

---

#### R-T02: Anti-Bot Detection Blocking Scrapers

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T02 |
| **Category** | Technical |
| **Description** | Websites employ anti-bot measures including Cloudflare challenges, rate limiting, IP blocking, JavaScript challenges, fingerprinting, and behavioral analysis. When triggered, these systems block or challenge scraper requests, resulting in failed scrapes, CAPTCHA pages, 403 Forbidden responses, or IP bans. Major platforms (Instagram, X, TikTok) invest heavily in anti-scraping technology. |
| **Probability** | 5 (Almost Certain) |
| **Impact** | 4 (Major) |
| **Risk Score** | **20 — Critical** |
| **Owner** | Infrastructure Engineer |
| **Trigger** | HTTP 403/429 response rates exceed 10%; repeated Cloudflare challenge pages detected; IP block notifications |

**Mitigation Strategy**:
1. Implement respectful rate limiting with configurable per-domain delays (F15); default to conservative values
2. Use transparent user-agent strings that clearly identify as Phoenix Engine, not browser impersonation
3. Implement proper HTTP header sets (Accept, Accept-Language, Accept-Encoding) that match legitimate traffic patterns
4. Support proxy rotation configuration for users who need to distribute requests across IPs
5. Implement exponential backoff on rate limit responses (HTTP 429 Retry-After header respect)
6. Use Playwright's stealth mode options to reduce fingerprinting surface while maintaining transparency
7. Cache and reuse sessions/cookies to appear as returning visitors rather than new connections

**Contingency Plan**:
1. On detection of anti-bot blocking, immediately increase delays for affected domain by 2x
2. If IP-level blocking is detected, pause scraping for 1 hour and notify user of block status
3. Switch to browser automation mode (if HTTP was being used) as browser rendering can bypass simpler anti-bot measures
4. If persistent blocking occurs, queue affected URLs and retry with increased delays after cooldown period
5. Document anti-bot encounter patterns and adjust default rate limits for affected domains platform-wide

---

#### R-T03: JavaScript-Heavy Pages Requiring Browser Automation

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T03 |
| **Category** | Technical |
| **Description** | Modern websites, particularly social media platforms, rely heavily on JavaScript for content rendering. Initial HTML responses may contain minimal or no actual content data, with all meaningful data loaded dynamically via XHR/fetch requests after page load. This necessitates browser automation which is significantly slower and more resource-intensive than direct HTTP requests. |
| **Probability** | 5 (Almost Certain) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **15 — High** |
| **Owner** | Lead Scraping Engineer |
| **Trigger** | HTTP scrape returns empty content despite 200 OK; page source shows `<script>` tags with no content divs; target platform known for JS rendering |

**Mitigation Strategy**:
1. Implement intelligent strategy selection (F2) that probes pages with HTTP first and falls back to browser only when necessary
2. Maintain a domain-strategy knowledge base that records which domains require browser automation
3. For known JS-heavy platforms (Instagram, TikTok), default directly to browser mode to avoid wasted HTTP attempts
4. Optimize browser automation with parallel page contexts, request interception to block unnecessary resources (images, CSS, fonts), and early content detection
5. Implement "browser mode but intercept API calls" optimization where XHR responses containing JSON data are captured directly

**Contingency Plan**:
1. If browser resource usage exceeds capacity, implement a priority queue with higher priority for time-sensitive scrapes
2. If a platform unexpectedly shifts from static to JS rendering, update domain knowledge base immediately
3. Explore reverse-engineering of internal API endpoints called by JavaScript to potentially bypass full browser rendering
4. Scale horizontally by adding more browser worker nodes if resource constraints are hit

---

#### R-T04: Selectors Becoming Outdated as Sites Redesign

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T04 |
| **Category** | Technical |
| **Description** | Even with fallback selector systems, gradual divergence between stored selectors and actual site HTML leads to declining extraction quality over time. Selectors that once matched perfectly may start matching wrong elements, extracting partial data, or missing new content types added by platforms. This is a chronic maintenance challenge distinct from sudden breakage (R-T01). |
| **Probability** | 4 (Likely) |
| **Impact** | 4 (Major) |
| **Risk Score** | **16 — High** |
| **Owner** | QA Engineer |
| **Trigger** | Data quality scores decline; extracted field completeness drops below 90%; selector match confidence scores trend downward over 7-day period |

**Mitigation Strategy**:
1. Implement automated "selector health checks" that run daily against known-good test pages for each platform
2. Track match rates and extraction confidence per selector per platform over time
3. Maintain "golden reference" HTML snapshots from each platform for regression testing selector changes
4. Use semantic extraction as backup — when selectors underperform, fall back to content-density heuristics
5. Schedule monthly proactive selector review cycles for all P0 platform scrapers

**Contingency Plan**:
1. When selector health check fails, flag the platform for immediate review and temporarily mark as "degraded"
2. If extraction completeness drops below 80%, activate emergency selector review within 24 hours
3. For fields that become unextractable, mark as `null` with clear `partial_reasons` so downstream consumers know data is missing
4. Deploy Ollama-assisted selector generation (F14/F21) to propose updated selectors from current HTML for rapid review and deployment

---

#### R-T05: Cookie/Auth Session Expiration Requiring Re-Authentication

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T05 |
| **Category** | Technical |
| **Description** | Session cookies imported from browsers have finite lifetimes. When sessions expire, scrapers that rely on authenticated access (for content behind login walls) will begin receiving redirect-to-login responses. Users must periodically re-export and re-import fresh cookies. Some platforms aggressively expire sessions from unrecognized devices or IP addresses. |
| **Probability** | 4 (Likely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **12 — High** |
| **Owner** | Backend Engineer |
| **Trigger** | Authenticated scrape returns redirect to login page; HTTP 401 responses; cookie expiry dates passed |

**Mitigation Strategy**:
1. Proactively monitor cookie expiry dates and warn users 48 hours before expiration
2. Implement session validity checks that test a single lightweight request before full batch jobs
3. Store multiple cookie sets per domain as backup sessions
4. Gracefully degrade to public-content-only scraping when sessions expire rather than failing entirely
5. Document cookie export/import procedures clearly for users with step-by-step browser-specific guides

**Contingency Plan**:
1. On session expiry detection, immediately notify the user with specific re-authentication instructions for the affected platform
2. Switch scraping mode to "public only" for affected platform, skipping authenticated-only content
3. Queue authenticated-content scrape jobs with a flag to retry once user refreshes cookies
4. If session expiry is widespread (platform policy change), update documentation and communicate to all users

---

#### R-T06: Infinite Scroll / Dynamic Loading Complications

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T06 |
| **Category** | Technical |
| **Description** | Social media platforms use infinite scroll and dynamic loading patterns where content is fetched via background requests as the user scrolls. This complicates scraping because: (1) content doesn't exist in initial HTML, (2) scroll triggers must be simulated precisely, (3) loading indicators and race conditions can cause missed content, (4) some platforms randomize or deduplicate infinite scroll results, (5) excessive scrolling may trigger anti-bot detection. |
| **Probability** | 4 (Likely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **12 — High** |
| **Owner** | Frontend/Scraping Engineer |
| **Trigger** | Paginated scrapes return fewer items than expected; scroll simulation hangs; duplicate content in paginated results |

**Mitigation Strategy**:
1. Implement scroll simulation with configurable parameters (scroll amount, wait time between scrolls, max scrolls)
2. Detect loading indicators and wait for them to disappear before extracting content
3. Implement deduplication logic using content IDs to prevent storing the same item twice from scroll overlap
4. Use MutationObserver via Playwright to detect when new content is added to DOM rather than blind scrolling
5. Monitor network requests during scroll to detect and optionally intercept the underlying data API calls
6. Set conservative scroll limits by default with user-configurable maximums

**Contingency Plan**:
1. If scroll-based pagination is unreliable, switch to extracting data from intercepted XHR responses instead of DOM
2. If excessive scrolling triggers anti-bot measures, reduce scroll depth and document maximum safe scroll per platform
3. If dynamic loading hangs, implement a timeout with extracted content returned up to the hang point
4. For critical data completeness, support "resume from last position" using stored scroll state

---

#### R-T07: Proxy Requirements for High-Volume Scraping

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T07 |
| **Category** | Technical |
| **Description** | High-volume scraping operations may require proxy rotation to distribute requests across multiple IP addresses. However, proxy management introduces complexity: proxy reliability varies, some proxies are already blacklisted by target platforms, proxy latency affects scrape speed, and proxy costs scale with volume. Additionally, some proxy types (datacenter) are more easily detected than residential proxies. |
| **Probability** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **9 — Medium** |
| **Owner** | Infrastructure Engineer |
| **Trigger** | IP-based rate limiting encountered; need to scrape >1000 URLs/day from single domain; user requests proxy support |

**Mitigation Strategy**:
1. Design proxy support as optional configuration, not required for normal operation
2. Support HTTP, HTTPS, and SOCKS5 proxy protocols
3. Implement proxy health checks that validate proxies against target platforms before use
4. Allow per-domain proxy configuration so different platforms can use different proxy pools
5. Track proxy success rates per platform and automatically deprioritize failing proxies
6. Respect proxy provider terms of service and don't rotate excessively fast

**Contingency Plan**:
1. If configured proxy fails, fall back to direct connection and alert user
2. If proxy is blacklisted by a platform, mark it as failed for that domain and try next proxy
3. If proxy costs become prohibitive, recommend reducing scrape frequency or focusing on essential data
4. Document proxy configuration best practices including recommended providers and configurations

---

#### R-T08: Browser Automation Memory/Resource Consumption

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T08 |
| **Category** | Technical |
| **Description** | Playwright browser instances consume significant memory (100-300MB per page context). At scale, concurrent browser scrapes can exhaust system memory, leading to OOM kills, swap thrashing, and degraded performance. Browser processes also consume CPU for JavaScript execution and rendering. Resource leaks from improperly closed browser contexts compound the issue over time. |
| **Probability** | 4 (Likely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **12 — High** |
| **Owner** | Infrastructure Engineer |
| **Trigger** | Memory usage exceeds 80% of available RAM; OOM errors in logs; browser process count growing unbounded; scrape latency increases over time |

**Mitigation Strategy**:
1. Implement browser context pooling with maximum context limits per worker
2. Use resource interception to block unnecessary assets (images, CSS, fonts, media) during scraping
3. Implement strict browser context lifecycle management with guaranteed cleanup via context managers
4. Monitor memory usage and scale down concurrent browser operations when thresholds are reached
5. Support headless mode exclusively (no headed browser instances in production)
6. Implement periodic browser process recycling (restart every N scrapes to prevent memory accumulation)

**Contingency Plan**:
1. If memory threshold is exceeded, queue new browser scrapes and process HTTP-only scrapes until memory frees
2. If OOM occurs, implement automatic recovery with browser process restart and job retry
3. If persistent resource issues occur, recommend increasing system RAM or reducing `max_concurrent` setting
4. Add resource usage metrics to diagnostics so users can self-diagnose resource constraints

---

#### R-T09: Network Instability and Timeouts

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T09 |
| **Category** | Technical |
| **Description** | Network-level issues including DNS resolution failures, TCP connection timeouts, TLS handshake failures, intermittent packet loss, and CDN edge node issues can cause scrape failures. These issues may be transient (network blip) or persistent (target site outage, regional blocking). Distinguishing between transient and persistent failures is important for retry behavior. |
| **Probability** | 4 (Likely) |
| **Impact** | 2 (Minor) |
| **Risk Score** | **8 — Medium** |
| **Owner** | Backend Engineer |
| **Trigger** | Connection timeout errors; DNS resolution failures; TLS errors; elevated error rates from specific geographic regions |

**Mitigation Strategy**:
1. Implement configurable timeout values per domain with sensible defaults (10s connect, 30s read)
2. Use exponential backoff retry with jitter for transient network failures (max 3 retries)
3. Implement DNS caching to reduce resolution overhead and failures
4. Distinguish between timeout types (DNS, connect, read) in error reporting for targeted response
5. Monitor network error patterns to identify persistent vs transient issues

**Contingency Plan**:
1. For transient failures, retry with exponential backoff up to maximum attempts
2. For persistent failures on a domain, temporarily mark domain as degraded and reduce scrape frequency
3. If regional issues are suspected, document alternative DNS resolvers or proxy configurations
4. For complete target site outages, queue jobs and retry every 15 minutes until recovery

---

#### R-T10: HTML Parsing Edge Cases and Malformed Markup

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T10 |
| **Category** | Technical |
| **Description** | Real-world HTML often deviates from standards — unclosed tags, nested elements that violate spec, encoding issues, mixed content types, and JavaScript-injected HTML that doesn't exist in source. HTML parsers must handle malformed markup gracefully without crashing or extracting incorrect data. Social media platforms may intentionally introduce parsing challenges. |
| **Probability** | 3 (Possible) |
| **Impact** | 2 (Minor) |
| **Risk Score** | **6 — Medium** |
| **Owner** | Scraping Engineer |
| **Trigger** | Parser exceptions in logs; extracted content contains unexpected HTML fragments; encoding errors in output |

**Mitigation Strategy**:
1. Use lenient HTML parsers (lxml with recovery mode, BeautifulSoup) that handle malformed markup gracefully
2. Normalize HTML encoding to UTF-8 before parsing
3. Sanitize extracted text content to remove any remaining HTML tags or entities
4. Implement defensive extraction that handles missing or unexpectedly structured elements
5. Test parsers against a corpus of real-world HTML samples from each target platform

**Contingency Plan**:
1. If parser fails on a specific page, log the HTML snippet for analysis and skip that field/page
2. If systemic parsing issues are detected, switch to browser-based extraction which handles JavaScript-generated HTML
3. Maintain a "parsing quirks" registry documenting platform-specific HTML oddities and workarounds

---

#### R-T11: Ollama Service Not Running

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T11 |
| **Category** | Technical |
| **Description** | Phoenix Engine's AI-powered features (extraction, selector repair, content classification, anti-bot recovery, entity resolution) all depend on the Ollama service running locally on `localhost:11434`. If Ollama is not installed, not started, or crashes, all AI fallback capabilities become unavailable. This is the most common failure mode for first-time users who haven't installed Ollama yet. The risk is heightened because Ollama is a separate dependency that users must install manually from ollama.com. |
| **Probability** | 3 (Possible) |
| **Impact** | 4 (Major) |
| **Risk Score** | **12 — High** |
| **Owner** | Lead Engineer / Infrastructure Engineer |
| **Trigger** | Connection refused to `localhost:11434`; Ollama process not found; `ollama serve` not running; Ollama crash during inference |

**Mitigation Strategy**:
1. Auto-detect Ollama availability at Phoenix Engine startup via health check to `http://localhost:11434/api/tags`
2. Display clear, actionable error message with installation instructions if Ollama is not detected
3. Provide a setup guide link (ollama.com/download) and quick-start command (`ollama serve`) in error output
4. Implement `phoenix ollama status` CLI command for easy health checking
5. Gracefully degrade all AI features when Ollama is unavailable — core scraping continues with selector/heuristic extraction
6. Cache Ollama health status and re-check periodically (every 30 seconds) to detect when service comes back online
7. Include Ollama installation check in first-run wizard / setup flow

**Contingency Plan**:
1. If Ollama is not running, skip all AI fallback steps and continue with heuristic extraction; log clear warning
2. If Ollama crashes during inference, mark service as degraded, skip remaining AI operations for current batch, retry health check after 30 seconds
3. If Ollama is not installed, display persistent banner with installation instructions until resolved
4. If Ollama service repeatedly crashes, recommend: (a) updating Ollama to latest version, (b) checking system RAM, (c) using smaller 7b model
5. Document manual Ollama troubleshooting steps in FAQ

---

#### R-T12: Insufficient Hardware

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T12 |
| **Category** | Technical |
| **Description** | The qwen2.5:7b model requires an NVIDIA GPU with at least 8GB VRAM for acceptable performance. The 7b model can run on CPU but requires 16GB+ system RAM and inference takes significantly longer (30-60s vs <15s on GPU). Users with older hardware, integrated graphics, or limited RAM may be unable to run AI features effectively. Hardware diversity across user base makes this a likely occurrence. |
| **Probability** | 4 (Likely) |
| **Impact** | 4 (Major) |
| **Risk Score** | **16 — High** |
| **Owner** | Infrastructure Engineer |
| **Trigger** | GPU VRAM < 8GB detected; no GPU detected; system RAM < 16GB; inference time > 60 seconds; OOM errors during model loading |

**Mitigation Strategy**:
1. Auto-detect hardware at startup: GPU name, VRAM size, CUDA version, CPU cores, system RAM
2. Select optimal model tier automatically: 7b default for all configurations; 14b optional on >=16GB VRAM
3. Display hardware detection results and model selection on first run with explanation
4. Allow manual model override via `phoenix ollama models set` for advanced users
5. Implement progressive fallback chain: 7b → 7b → CPU 7b → skip AI
6. Document minimum and recommended hardware requirements prominently
7. Provide `phoenix ollama status` command for hardware visibility

**Contingency Plan**:
1. If GPU VRAM is insufficient for 7b model, automatically fall back to 7b model and log: "GPU VRAM insufficient for 7b ({vram}GB < 8GB). Using 7b model."
2. If 7b model fails on GPU due to VRAM, fall back to CPU inference with 7b
3. If inference is consistently slow (> 60s on CPU), log recommendation: "Consider upgrading to GPU for AI features, or disable AI with `--no-ai`"
4. If hardware is completely insufficient (RAM < 8GB), disable AI features entirely and document: "AI features require minimum 8GB RAM. Current: {ram}GB."
5. Provide `--no-ai` CLI flag to skip all AI operations for users who prefer faster scraping without AI

---

#### R-T13: Model Download Failure

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T13 |
| **Category** | Technical |
| **Description** | Ollama model downloads (pulls) can fail due to: network interruption, insufficient disk space, model not found in registry, corrupted download, or proxy/firewall blocking access to the Ollama model registry. The 7b model is approximately 4.5GB, making downloads lengthy and prone to interruption. Failed downloads leave partial files that may cause subsequent load attempts to fail. |
| **Probability** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **9 — Medium** |
| **Owner** | Infrastructure Engineer |
| **Trigger** | `ollama pull` returns error; download progress stalls; disk space insufficient; network timeout during pull; partial model file detected |

**Mitigation Strategy**:
1. Pre-flight disk space check before model download: require 6GB free for 7b
2. Verify model exists in Ollama registry before attempting download
3. Ollama's built-in resume capability handles interrupted downloads automatically
4. Display download progress with ETA during `phoenix ollama models pull`
5. Implement download timeout with retry (3 attempts with exponential backoff)
6. Check network connectivity to Ollama registry before download

**Contingency Plan**:
1. If 7b download fails, automatically attempt smaller model or CPU fallback as fallback
2. If download repeatedly fails, guide user to manual download: `ollama pull qwen2.5:7b`
3. If disk space is insufficient, display: "Insufficient disk space: {free}GB free, {required}GB required. Free up space or use a smaller model."
4. If network blocks Ollama registry, document proxy configuration for Ollama and alternative download methods
5. If model file is corrupted, run `ollama rm` to remove partial file and re-download

---

#### R-T14: Ollama Out of Memory During Inference

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T14 |
| **Category** | Technical |
| **Description** | GPU VRAM can be exhausted during local inference, especially when: (1) a 7b model is loaded and a large HTML page is processed, (2) multiple applications compete for GPU memory, (3) the system has shared GPU memory (integrated graphics), (4) a browser or other GPU-intensive application is running concurrently. OOM errors cause inference to fail and may crash the Ollama service, requiring a restart. |
| **Probability** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **9 — Medium** |
| **Owner** | Infrastructure Engineer |
| **Trigger** | Ollama returns OOM error; GPU VRAM usage exceeds 100%; inference fails mid-generation; Ollama service crashes; CUDA out-of-memory errors in logs |

**Mitigation Strategy**:
1. Monitor GPU VRAM before each inference call; estimate required memory based on input size
2. Implement automatic model unloading after idle period (configurable, default 5 minutes)
3. Manage context window size based on available VRAM — reduce for limited GPUs
4. Pre-process HTML to minimize token count before sending to Ollama (strip scripts, styles, comments)
5. Queue inference requests to prevent concurrent calls from exhausting VRAM
6. Warn users when VRAM usage exceeds 80% during operation

**Contingency Plan**:
1. On OOM error: (1) unload current model from GPU, (2) load 7b model instead, (3) retry inference. Log each step.
2. If 7b also OOMs on GPU: switch to CPU inference mode with 7b model
3. If OOM persists on CPU: reduce context window to 32K tokens and retry
4. If all options exhausted: skip AI for this request, return heuristic extraction, log: "OOM — AI skipped for this request"
5. If Ollama service crashed due to OOM, auto-restart detection via health monitor (F26)

---

#### R-T15: Local Inference Too Slow

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T15 |
| **Category** | Technical |
| **Description** | CPU inference with the 7b model can take 30-60 seconds per page, which is significantly slower than GPU inference (<15s). For batch operations processing hundreds of URLs, this creates unacceptable throughput. Users may not realize their hardware is CPU-bound until they experience slow performance. Slow inference also increases the perceived risk of the scraping process hanging. |
| **Probability** | 3 (Possible) |
| **Impact** | 2 (Minor) |
| **Risk Score** | **6 — Medium** |
| **Owner** | Product Manager / Infrastructure Engineer |
| **Trigger** | Inference time > 60 seconds; batch job ETA exceeds expectations; user reports slow AI features; CPU at 100% during inference |

**Mitigation Strategy**:
1. Display hardware detection results on first run, including expected inference time estimate
2. Recommend GPU for users planning heavy AI usage (provide minimum GPU recommendations)
3. Implement async inference that doesn't block the scraping pipeline
4. Cache inference results aggressively to avoid redundant slow calls
5. Provide `--no-ai` flag for users who want maximum scraping speed without AI
6. Document performance expectations: GPU <15s, CPU 30-60s per AI operation

**Contingency Plan**:
1. If inference exceeds 60 seconds, log: "Slow inference detected ({time}s on CPU). Consider using GPU for better performance."
2. For batch operations with slow inference, skip AI after first N slow calls and use heuristic extraction for remaining URLs
3. Provide configuration to disable AI for batch operations while keeping it for interactive use
4. If user consistently experiences slow inference, recommend 7b model (already default on CPU) or hardware upgrade

---

#### R-T16: Search API Rate Limits or Blocks Discovery

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T16 |
| **Category** | Technical |
| **Description** | PhoenixArchitect relies on external search engines (DuckDuckGo, Google) to discover candidate listing sites. These services may impose rate limits, require CAPTCHA challenges, block automated queries, or change their result-page HTML without notice. If discovery fails, the autonomous adapter-generation pipeline cannot find target sites and stops before generating any code. |
| **Probability** | 4 (Likely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **12 — High** |
| **Owner** | Intelligence Engineer |
| **Trigger** | Empty result sets despite valid query; HTTP 429/403 from search endpoint; repeated CAPTCHA pages; sudden change in result HTML structure |

**Mitigation Strategy**:
1. Implement polite per-engine rate limiting and exponential backoff
2. Support multiple search backends (DuckDuckGo primary, Google fallback, Bing optional)
3. Cache recent search results to avoid repeated identical queries
4. Parse organic results robustly with fallback selectors for result title, URL, and snippet
5. Allow users to seed the pipeline with a known `--start-url` to bypass search entirely

**Contingency Plan**:
1. If search engine blocks queries, switch to fallback engine automatically
2. If all engines fail, prompt user for a manual list of candidate URLs
3. Log the failure and skip the discovery step; continue with user-provided sites

---

#### R-T17: Pagination Detection Fails on Unfamiliar Site Layouts

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-T17 |
| **Category** | Technical |
| **Description** | Listing sites use diverse pagination patterns (numbered links, "Next" buttons, "Load more", infinite scroll, cursor/token APIs). PhoenixArchitect's Inspector/Coder agents may misidentify or fail to detect the correct pattern on a previously unseen site, producing an adapter that only extracts the first page. This limits coverage and yields incomplete datasets. |
| **Probability** | 4 (Likely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **12 — High** |
| **Owner** | Intelligence Engineer |
| **Trigger** | Generated adapter returns no `next_page_url` on a multi-page site; Critic reports missing items across fixtures; manual inspection shows unhandled pagination controls |

**Mitigation Strategy**:
1. Train the Inspector with a taxonomy of common pagination patterns and example selectors
2. Collect multiple sample pages during exploration so the Critic can verify navigation
3. Generate defensive pagination code that tries multiple strategies before giving up
4. Score each detected pattern by consistency across collected samples
5. Default to conservative behavior: report "single page" rather than fabricate a broken pagination URL

**Contingency Plan**:
1. If pagination is uncertain, emit a `WARNING` in generated adapter docstring and logs
2. Provide a `--manual-pagination` override for users to supply a known selector or URL template
3. Mark adapter as "detail-only" if list pagination cannot be validated

---

### 3.2 Legal and Compliance Risks

#### R-L01: Website Terms of Service Prohibiting Scraping

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-L01 |
| **Category** | Legal/Compliance |
| **Description** | Most social media platforms and many websites include clauses in their Terms of Service that prohibit automated data collection, scraping, or crawling. Violating these terms can result in account termination, legal cease-and-desist letters, or in extreme cases, civil litigation. Users of Phoenix Engine must be aware that scraping against a site's ToS carries legal risk, even when scraping public data. |
| **Probability** | 4 (Likely) |
| **Impact** | 4 (Major) |
| **Risk Score** | **16 — High** |
| **Owner** | Product Manager / Legal Advisor |
| **Trigger** | Cease-and-desist communication received; account termination notice; legal complaint filed |

**Mitigation Strategy**:
1. Clearly document in Terms of Service that Phoenix Engine is a tool for accessing publicly available data and users are responsible for ensuring their use complies with applicable laws and website terms
2. Provide prominent warnings in documentation about ToS considerations for each supported platform
3. Only scrape publicly accessible content that does not require authentication bypass or paywall circumvention
4. Respect robots.txt directives as evidence of site owner preferences
5. Include ToS awareness acknowledgment in first-time setup flow
6. Maintain transparent user-agent identification so platforms can identify and contact scraper operators

**Contingency Plan**:
1. If cease-and-desist received, immediately comply with request and document the interaction
2. If platform blocks Phoenix Engine at legal level, remove or suspend scraper for that platform
3. Provide users with guidance on assessing their specific use case against relevant ToS and legal frameworks
4. Consult legal counsel before responding to any legal communication regarding scraping activities

---

#### R-L02: robots.txt Restrictions

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-L02 |
| **Category** | Legal/Compliance |
| **Description** | The robots.txt standard allows website owners to specify which parts of their site should not be crawled by automated agents. While not legally binding in most jurisdictions, ignoring robots.txt is widely considered bad practice and may be cited as evidence of bad faith in legal proceedings. Some platforms use robots.txt to signal scraping restrictions. |
| **Probability** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **9 — Medium** |
| **Owner** | Lead Scraping Engineer |
| **Trigger** | robots.txt crawl-delay directive present; Disallow rules matching scrape URLs; robots.txt explicitly targets Phoenix Engine user-agent |

**Mitigation Strategy**:
1. robots.txt parsing and compliance enabled by default and cannot be fully disabled (only overridden with explicit user warning)
2. Parse robots.txt before first scrape of a domain and cache results for 24 hours
3. Honor Crawl-delay directives with automatic rate limit adjustment
4. Log robots.txt compliance decisions for audit trail
5. If robots.txt blocks a requested URL, return clear error: "robots.txt restricts scraping of this URL"

**Contingency Plan**:
1. If robots.txt changes to block previously allowed URLs, immediately respect new restrictions and notify affected users
2. If a user explicitly overrides robots.txt compliance, require written acknowledgment of risk and log the override
3. If robots.txt is malformed or unreachable, apply conservative default rate limits and proceed with caution

---

#### R-L03: GDPR/CCPA Considerations for Scraped Personal Data

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-L03 |
| **Category** | Legal/Compliance |
| **Description** | The EU General Data Protection Regulation (GDPR) and California Consumer Privacy Act (CCPA) regulate the collection and processing of personal data. Scraped social media content may include personally identifiable information (PII) such as usernames, real names, profile photos, locations, and biographical information. Depending on jurisdiction and use case, scraping this data may create compliance obligations including data subject rights (access, erasure), lawful basis for processing, and data protection impact assessments. |
| **Probability** | 3 (Possible) |
| **Impact** | 5 (Critical) |
| **Risk Score** | **15 — High** |
| **Owner** | Product Manager / Legal Advisor |
| **Trigger** | Data subject requests erasure of scraped data; regulatory inquiry received; processing scraped personal data at scale |

**Mitigation Strategy**:
1. Document that Phoenix Engine is a technical tool; users are responsible for ensuring their scraping activities comply with applicable data protection laws
2. Provide guidance on GDPR considerations in documentation including lawful basis assessment, data minimization, and storage limitation principles
3. Recommend users conduct a Data Protection Impact Assessment (DPIA) before large-scale scraping of personal data
4. Support data deletion capabilities — users can delete archived HTML and extracted data on request
5. Include privacy considerations in user documentation with recommended best practices
6. Do not collect or store more personal data than the user explicitly requests

**Contingency Plan**:
1. If a data subject exercise request (access, erasure) is received, provide tools and documentation to comply
2. If regulatory inquiry is received, consult legal counsel immediately and preserve all relevant records
3. If processing basis is uncertain, recommend users seek independent legal advice on their specific use case
4. Maintain records of data processing activities performed through Phoenix Engine for accountability

---

#### R-L04: Copyright on Scraped Content

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-L04 |
| **Category** | Legal/Compliance |
| **Description** | Content scraped from websites and social media (text, images, videos) is typically protected by copyright. While factual data and short excerpts may fall under fair use or fair dealing doctrines, reproducing substantial content without permission may constitute copyright infringement. Users who scrape and republish content face copyright risk. |
| **Probability** | 2 (Unlikely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **6 — Medium** |
| **Owner** | Product Manager |
| **Trigger** | DMCA takedown notice received; copyright holder complaint; content republished without attribution |

**Mitigation Strategy**:
1. Document that scraped content may be subject to copyright and users should understand applicable fair use/fair dealing provisions
2. Recommend users only extract data necessary for their specific purpose (data minimization)
3. Suggest proper attribution when scraped content is referenced or analyzed
4. Clarify that Phoenix Engine extracts data but does not grant any rights to the underlying content
5. Provide guidance on transformative use (analysis, research) vs. republication

**Contingency Plan**:
1. If DMCA notice received, comply with takedown requirements promptly
2. If copyright dispute arises, recommend user seek legal counsel; Phoenix Engine is a tool provider not a content publisher
3. Document all copyright-related communications for legal defense if needed

---

#### R-L05: CFAA (US) Legal Uncertainty Around Scraping

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-L05 |
| **Category** | Legal/Compliance |
| **Description** | In the United States, the Computer Fraud and Abuse Act (CFAA) has been used in scraping-related litigation, though interpretations vary across circuit courts. The Supreme Court's Van Buren decision narrowed CFAA's scope for unauthorized access, but uncertainty remains regarding whether scraping public websites violates CFAA when done against ToS. This legal ambiguity creates risk for US-based scraping operations. |
| **Probability** | 2 (Unlikely) |
| **Impact** | 5 (Critical) |
| **Risk Score** | **10 — Medium** |
| **Owner** | Legal Advisor |
| **Trigger** | CFAA-related legal action in scraping context; unfavorable circuit court ruling; legislative changes |

**Mitigation Strategy**:
1. Stay informed about CFAA jurisprudence and legal developments in scraping case law
2. Only access publicly available data that requires no authentication, authorization, or technical circumvention
3. Never attempt to bypass access controls, authentication, or paywalls
4. Maintain transparent user-agent identification to demonstrate good faith
5. Document the public nature of all scraped data (no authentication required, no paywall)

**Contingency Plan**:
1. If adverse CFAA ruling affects scraping operations, consult legal counsel immediately
2. If necessary, suspend scraping of affected platforms pending legal clarity
3. Communicate any legal developments to users with guidance on implications
4. Maintain legal defense fund and appropriate insurance coverage

---

#### R-L06: Different Jurisdictional Treatment of Scraping

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-L06 |
| **Category** | Legal/Compliance |
| **Description** | Web scraping is treated differently across jurisdictions. The EU generally permits scraping of public data under database rights exceptions. The US has mixed case law (hiQ v. LinkedIn established that scraping public data doesn't violate CFAA, but appeals continue). Some countries have stricter regulations. Users operating across borders face complex legal compliance requirements. |
| **Probability** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **9 — Medium** |
| **Owner** | Legal Advisor |
| **Trigger** | User operates in jurisdiction with restrictive scraping laws; cross-border data transfer issues; conflicting legal requirements |

**Mitigation Strategy**:
1. Document known jurisdictional considerations for major markets (US, EU, UK, Canada, Australia)
2. Recommend users consult local legal counsel to understand applicable laws in their jurisdiction
3. Structure product to only access public data, which has stronger legal protection across jurisdictions
4. Maintain compliance with EU data protection requirements for EU users
5. Monitor legal developments in key jurisdictions and update guidance accordingly

**Contingency Plan**:
1. If legal restrictions change in a key jurisdiction, update documentation and user guidance
2. If necessary, implement jurisdiction-specific compliance features (e.g., EU data residency options)
3. If a jurisdiction becomes legally inhospitable to scraping, restrict service availability with clear explanation

---

#### R-L08: Local AI Data Residency (Risk Eliminated)

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-L08 |
| **Category** | Legal/Compliance |
| **Description** | **RISK ELIMINATED BY OLLAMA ARCHITECTURE.** Previous versions of Phoenix Engine sent scraped HTML containing personal data to external AI APIs (Kimi/Moonshot AI), creating GDPR, CCPA, and cross-border data transfer compliance obligations. With the migration to Ollama local inference, ALL AI processing happens on the user's machine. No scraped data — including personal data, usernames, bios, or any HTML content — is ever transmitted to external AI services. This eliminates: (1) Third-party data processor agreements, (2) Cross-border data transfer restrictions, (3) AI service privacy policy dependencies, (4) Data retention concerns with external providers, (5) PII amplification risks from cloud AI processing. |
| **Probability** | 1 (Rare — only if user misconfigures) |
| **Impact** | 1 (Negligible) |
| **Risk Score** | **1 — Low** |
| **Owner** | Product Manager / Legal Advisor |
| **Trigger** | User manually configures external AI endpoint; verification that data stays local |

**Mitigation Strategy**:
1. Ollama runs entirely on localhost — no network egress for AI operations
2. Document the local-only architecture as a key privacy feature
3. Verify no external API calls are made during AI operations (network monitoring)
4. Include privacy architecture in security documentation for compliance reviewers
5. Maintain audit capability: log all AI operations with local-only confirmation

**Contingency Plan**:
1. If user reports concern about data being sent externally, demonstrate with `phoenix ollama status` showing localhost-only operation
2. If compliance review requires proof of local processing, provide network capture documentation
3. If future versions add optional cloud AI, require explicit opt-in with clear data flow disclosure

---

#### R-L07: Data Residency and Cross-Border Transfer Restrictions

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-L07 |
| **Category** | Legal/Compliance |
| **Description** | Scraped data containing personal information may be subject to data residency requirements (data must remain within certain geographic boundaries) or cross-border transfer restrictions. EU GDPR restricts transfers of personal data outside the EEA unless appropriate safeguards are in place. Other jurisdictions have similar requirements. |
| **Probability** | 2 (Unlikely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **6 — Medium** |
| **Owner** | Infrastructure Engineer / Legal Advisor |
| **Trigger** | User stores scraped personal data across borders; data residency audit; regulatory inquiry on data transfers |

**Mitigation Strategy**:
1. Default to local-only storage of scraped data — Phoenix Engine stores data on user's machine, not cloud servers
2. Document that users are responsible for ensuring their storage and processing of scraped data complies with data residency requirements
3. Provide guidance on data residency considerations for scraped personal data
4. If cloud features are added, ensure data residency options are available

**Contingency Plan**:
1. If data residency requirements are identified, guide user on local storage and processing approaches
2. If cloud processing is required, implement region-specific processing options
3. Maintain data processing records to demonstrate compliance efforts

---

### 3.3 Operational Risks

#### R-O01: AI Agent Context Limits for Complex HTML Parsing Code

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O01 |
| **Category** | Operational |
| **Description** | When using AI-assisted features (F14) for selector generation or complex HTML parsing, large and complex HTML documents may exceed the context window of the LLM. This limits the AI's ability to see the full page structure, potentially resulting in incomplete or incorrect selector suggestions. Nested DOM structures, minified HTML, and pages with thousands of elements are particularly challenging. |
| **Probability** | 4 (Likely) |
| **Impact** | 2 (Minor) |
| **Risk Score** | **8 — Medium** |
| **Owner** | ML/AI Engineer |
| **Trigger** | HTML document exceeds token limit; AI returns incomplete selectors; AI suggests selectors for wrong page sections |

**Mitigation Strategy**:
1. Pre-process HTML before AI analysis — remove scripts, styles, and non-semantic elements to reduce size
2. Use targeted HTML extraction — send only relevant page sections to AI rather than full document
3. Implement chunking strategies for large pages with semantic-aware splitting
4. Cache successful AI-generated selectors to reduce repeated AI calls for similar pages
5. Use AI for selector suggestions, not automated deployment — human review catches context limit issues

**Contingency Plan**:
1. If HTML exceeds AI context limits, fall back to heuristic-based extraction for that page
2. If AI generates incorrect selectors due to truncated context, flag for human review before deployment
3. If persistent context limit issues occur for a platform, document manual selector development process

---

#### R-O02: Test Environment HTML Diverging from Production Sites

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O02 |
| **Category** | Operational |
| **Description** | Testing scrapers against saved HTML snapshots or test environments risks creating selectors that work on test data but fail on production sites. Social media platforms may serve different HTML structures to different user agents, regions, or account types. A/B testing of UI changes means even live production HTML can vary between requests. |
| **Probability** | 4 (Likely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **12 — High** |
| **Owner** | QA Engineer |
| **Trigger** | Selectors pass all tests but fail in production; HTML snapshots differ from live pages; regional HTML variations detected |

**Mitigation Strategy**:
1. Maintain a continuously updated library of HTML snapshots from live production pages for each supported platform
2. Run automated selector validation against live pages (at reduced frequency) in addition to snapshot tests
3. Test selectors against multiple user-agent strings and viewport sizes
4. Monitor for A/B test indicators (variant IDs in HTML, cookie-based assignments)
5. Use semantic selector patterns rather than brittle structural selectors that may vary

**Contingency Plan**:
1. If production divergence is detected, immediately capture fresh HTML snapshots and compare with test baselines
2. If A/B testing is suspected, test selectors against multiple HTML variants
3. If selectors fail in production, activate fallback selector sets (F13) and schedule emergency selector review

---

#### R-O03: Selector Maintenance Overhead as Sites Evolve

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O03 |
| **Category** | Operational |
| **Description** | Each supported platform requires ongoing selector maintenance as sites evolve. With 6+ social platforms and generic web scraping, the cumulative maintenance burden is significant. Each platform change requires: detecting the change, analyzing new HTML, updating selectors, testing, and deploying. This ongoing cost must be factored into platform sustainability. |
| **Probability** | 5 (Almost Certain) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **15 — High** |
| **Owner** | Product Manager |
| **Trigger** | Hours spent on selector maintenance exceed development capacity; platform scrapers remain broken for extended periods; user complaints about data quality |

**Mitigation Strategy**:
1. Design selectors for maximum resilience using semantic and stable HTML attributes
2. Invest in Ollama-assisted selector generation (F14/F21) to reduce manual analysis time
3. Maintain comprehensive selector test suites that catch breakage early
4. Build community contributions into the selector update process
5. Prioritize P0 platform scrapers (Instagram, X, TikTok, LinkedIn) for fastest maintenance response
6. Document selector patterns and platform HTML structure for faster onboarding of maintenance engineers

**Contingency Plan**:
1. If maintenance overhead exceeds capacity, temporarily degrade less-critical scrapers (P1) to focus on P0 platforms
2. If a platform requires excessive maintenance, evaluate whether continued support is viable
3. If AI-assisted tools prove effective, increase investment to further reduce manual maintenance
4. Consider community-driven selector updates with validation pipeline

---

#### R-O04: User Skill Gap in Selector Configuration

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O04 |
| **Category** | Operational |
| **Description** | Users who want to write custom plugins or modify selectors need understanding of CSS selectors, HTML structure, and web scraping concepts. Many potential users (researchers, journalists, marketers) may lack these technical skills, limiting adoption of advanced features. Poorly written selectors can cause extraction failures or incorrect data. |
| **Probability** | 3 (Possible) |
| **Impact** | 2 (Minor) |
| **Risk Score** | **6 — Medium** |
| **Owner** | Technical Writer / UX Designer |
| **Trigger** | User support requests about selector syntax; plugin validation failures; incorrect data from user-configured selectors |

**Mitigation Strategy**:
1. Provide comprehensive documentation with examples for common selector patterns
2. Include built-in selector validation that checks syntax and warns about overly broad/narrow selectors
3. Implement `phoenix diagnose` command that shows which selectors matched and what they extracted
4. Create tutorial content for non-technical users covering CSS selector basics
5. Provide pre-built plugins for common sites so users don't need to write custom selectors
6. Include Ollama-assisted selector suggestion for plugin development

**Contingency Plan**:
1. If users struggle with selector configuration, expand documentation with more examples
2. If validation shows common error patterns, add specific linting rules and helpful error messages
3. If skill gap prevents adoption of advanced features, consider visual selector builder tool

---

#### R-O05: Dependency on Third-Party Browser Automation

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O05 |
| **Category** | Operational |
| **Description** | Phoenix Engine relies on Playwright for browser automation. Changes to Playwright APIs, browser engine updates (Chromium, Firefox), or Playwright maintenance issues could impact scraping functionality. Browser versions frequently update and may introduce breaking changes or alter rendering behavior. |
| **Probability** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **9 — Medium** |
| **Owner** | Lead Scraping Engineer |
| **Trigger** | Playwright API deprecation; browser version incompatibility; rendering differences after browser update |

**Mitigation Strategy**:
1. Pin Playwright to tested versions and update only after validation
2. Maintain compatibility layer that abstracts Playwright APIs for Phoenix Engine internal use
3. Test all scrapers against new Playwright/browser versions before deployment
4. Monitor Playwright release notes and deprecation announcements
5. Support fallback to alternative browser engines if primary has issues

**Contingency Plan**:
1. If Playwright breaking change is introduced, pin to last known good version and schedule migration
2. If browser rendering changes affect extraction, update selectors or adjust wait conditions
3. If Playwright becomes unmaintained, evaluate migration to Puppeteer, Selenium, or other alternatives

---

#### R-O06: Scaling Challenges with Concurrent Scrapes

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O06 |
| **Category** | Operational |
| **Description** | Supporting 100+ concurrent scrapes while respecting per-domain rate limits requires careful resource management. Concurrent scrapes compete for: browser contexts, memory, CPU, network bandwidth, and disk I/O for archiving. Poor resource management leads to degraded performance, timeouts, and failures at scale. |
| **Probability** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **9 — Medium** |
| **Owner** | Infrastructure Engineer |
| **Trigger** | Batch job duration increases non-linearly with URL count; resource utilization exceeds thresholds; scrape timeouts increase under load |

**Mitigation Strategy**:
1. Implement per-domain rate limit queues that enforce delays independently for each domain
2. Use asyncio for concurrent HTTP scrapes to minimize resource overhead
3. Implement browser context pooling with configurable limits
4. Monitor resource utilization and apply backpressure when thresholds are reached
5. Allow users to configure max concurrency based on their system capabilities

**Contingency Plan**:
1. If resource constraints are hit, reduce concurrent browser operations and prioritize HTTP-mode scrapes
2. If performance degrades under load, implement automatic scaling recommendations for users
3. If persistent scaling issues occur, recommend distributed deployment across multiple nodes

---

#### R-O07: Data Quality Degradation Going Unnoticed

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O07 |
| **Category** | Operational |
| **Description** | Scrapers may continue running and producing output even when extraction quality degrades — selectors matching wrong elements, new page structures causing partial extraction, or site changes introducing data format changes. Without active monitoring, degraded data quality can go unnoticed for extended periods, compromising downstream analysis. |
| **Probability** | 3 (Possible) |
| **Impact** | 4 (Major) |
| **Risk Score** | **12 — High** |
| **Owner** | QA Engineer / Data Engineer |
| **Trigger** | Downstream analysis shows anomalous data patterns; user reports suspicious data; field completeness metrics trend downward |

**Mitigation Strategy**:
1. Implement data quality monitoring that tracks: field completeness, data type consistency, value range checks, and temporal patterns
2. Alert when field extraction rates drop below thresholds (e.g., <90% of posts have captions)
3. Maintain data quality dashboards showing extraction metrics per platform per field
4. Implement anomaly detection on extracted values (sudden spikes/drops in numeric fields)
5. Require human review of AI-generated selectors before deployment to production

**Contingency Plan**:
1. If data quality degradation is detected, flag affected platform for immediate selector review
2. If degradation is severe, pause automated scrapes and require manual validation before resuming
3. If downstream analysis was affected by bad data, provide capability to re-scrape affected date ranges
4. Document data quality incident with root cause and preventive measures

---

#### R-O08: Insufficient Documentation Leading to Misuse

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O08 |
| **Category** | Operational |
| **Description** | Users who don't understand Phoenix Engine's capabilities, limitations, and ethical boundaries may misuse the tool — scraping too aggressively, attempting to bypass protections, scraping non-public content, or using scraped data in ways that create legal exposure. Poor documentation also increases support burden and reduces adoption. |
| **Probability** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | **9 — Medium** |
| **Owner** | Technical Writer / Product Manager |
| **Trigger** | User support requests about basic functionality; reports of misuse; complaints about tool limitations that are documented |

**Mitigation Strategy**:
1. Create comprehensive documentation covering: installation, configuration, all CLI commands, library API, platform-specific guides, ethical scraping practices, and legal considerations
2. Include quick-start tutorial that demonstrates correct usage patterns
3. Document each platform scraper with expected output format, known limitations, and rate limit recommendations
4. Include prominent ethical scraping guidelines and legal disclaimers
5. Implement in-tool help (`--help`, error message suggestions) that guides users toward correct usage

**Contingency Plan**:
1. If documentation gaps are identified, prioritize filling them based on support request frequency
2. If misuse patterns emerge, add safeguards and clearer warnings in the tool itself
3. If legal issues arise from misuse, strengthen disclaimers and consider requiring acknowledgment

---

#### R-O09: Security Vulnerability in HTML Parsing Pipeline

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O09 |
| **Category** | Operational |
| **Description** | Processing untrusted HTML from arbitrary websites creates security risks. Malicious HTML could exploit vulnerabilities in HTML parsers (XXE, buffer overflow), JavaScript execution in browser automation could trigger malicious scripts, and crafted content could cause denial of service through resource exhaustion (billion laughs attack, deeply nested HTML). |
| **Probability** | 2 (Unlikely) |
| **Impact** | 4 (Major) |
| **Risk Score** | **8 — Medium** |
| **Owner** | Security Engineer |
| **Trigger** | Security audit finding; vulnerability disclosure in dependency; suspicious HTML causing parser crash |

**Mitigation Strategy**:
1. Keep all dependencies (lxml, BeautifulSoup, Playwright) updated to latest security patches
2. Run HTML parsing in isolated subprocesses with resource limits (memory, CPU time)
3. Sanitize all extracted content before including in output (escape HTML entities, strip scripts)
4. Use Playwright's sandbox mode and restrict browser capabilities (no file downloads, no popups)
5. Run regular security audits of the parsing pipeline
6. Implement input size limits on HTML responses to prevent memory exhaustion

**Contingency Plan**:
1. If security vulnerability is discovered, immediately assess impact and deploy patch
2. If parser vulnerability is exploited, isolate affected systems and review all processed content
3. If security incident occurs, follow incident response plan and notify affected users

---

#### R-O10: Loss of Archived HTML Data

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O10 |
| **Category** | Operational |
| **Description** | The source archive (F12) stores raw HTML snapshots for audit and replay purposes. Loss of this data eliminates the ability to debug historical extraction issues, verify past scrapes, or replay extractions with updated selectors. Data loss can occur through: disk failure, accidental deletion, archive rotation bugs, or storage corruption. |
| **Probability** | 2 (Unlikely) |
| **Impact** | 2 (Minor) |
| **Risk Score** | **4 — Low** |
| **Owner** | Backend Engineer |
| **Trigger** | Disk space alerts; archive files missing or corrupted; user unable to replay historical scrape |

**Mitigation Strategy**:
1. Archive storage uses atomic writes (write to temp, rename) to prevent corruption
2. Implement archive integrity verification with checksums stored alongside HTML files
3. Configurable archive retention with FIFO rotation and size limits
4. Optional archive backup to secondary storage location
5. Graceful handling of missing archives — log warning but don't fail operations

**Contingency Plan**:
1. If archive corruption is detected, remove corrupted files and log the event
2. If storage is exhausted, apply FIFO rotation more aggressively
3. If critical archives are lost, they cannot be recovered — document the limitation

---

#### R-O11: Reputation Risk from User Misuse

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O11 |
| **Category** | Operational |
| **Description** | If users misuse Phoenix Engine to scrape in ways that violate laws or website terms, the reputation of the project and its maintainers may be damaged. Public perception of "scraping tools" is often negative, associating them with data theft, privacy violations, or competitive intelligence gathering. A high-profile incident could lead to platform blocking or legal scrutiny of the tool itself. |
| **Probability** | 2 (Unlikely) |
| **Impact** | 4 (Major) |
| **Risk Score** | **8 — Medium** |
| **Owner** | Product Manager |
| **Trigger** | Public incident involving Phoenix Engine misuse; negative media coverage; platform specifically blocks Phoenix Engine user-agent |

**Mitigation Strategy**:
1. Prominently position Phoenix Engine as an ethical, public-data-only scraping tool
2. Include clear documentation on acceptable use cases and ethical boundaries
3. Design tool to make misuse difficult (no CAPTCHA bypass, no auth bypass, rate limits enforced)
4. Engage transparently with the scraping community and platform operators
5. Respond quickly and responsibly to any misuse reports

**Contingency Plan**:
1. If misuse incident occurs, investigate and take corrective action (update safeguards, documentation)
2. If reputation damage occurs, engage in transparent communication about tool's legitimate uses
3. If platform blocks Phoenix Engine specifically, engage in dialogue to resolve concerns

---

#### R-O12: Autonomous AI Writes Broken or Incomplete Adapters

| Attribute | Value |
|-----------|-------|
| **Risk ID** | R-O12 |
| **Category** | Operational |
| **Description** | PhoenixArchitect delegates HTML inspection, selector extraction, and adapter code generation to local LLM agents. The model may produce syntactically invalid Python, hallucinate CSS selectors, omit required `BaseAdapter` methods, or fail to handle edge cases (missing fields, encoding issues, anti-bot pages). Unchecked, this could pollute the codebase with non-functional generated adapters and waste user time. |
| **Probability** | 4 (Likely) |
| **Impact** | 4 (Major) |
| **Risk Score** | **16 — High** |
| **Owner** | Intelligence Engineer / QA Lead |
| **Trigger** | Generated adapter fails `ruff`/`black`/`mypy`; Critic loop exhausts max iterations; extracted records are empty or schema-invalid; generated code references non-existent selectors |

**Mitigation Strategy**:
1. Enforce a multi-role agent loop (Planner → Researcher → Explorer → Inspector → Coder → Critic) with clear contracts
2. Require the Critic to run deterministic validation: compile, static analysis, selector coverage, schema conformance, pagination probe
3. Cap fix iterations at 3; abort and report failure if the adapter still does not pass
4. Stage generated code in `src/phoenix/adapters/generated/` and require explicit `--promote` before registration
5. Provide deterministic Jinja templates for adapter scaffolding to reduce model creativity
6. Use the stronger/fallback model (`qwen2.5:7b`) for code-generation steps if `dolphincoder:7b` produces poor results

**Contingency Plan**:
1. If Critic rejects the adapter, surface a detailed error report and ask the user for a manual seed selector or URL template
2. If the model consistently fails on a domain, blacklist that domain from auto-generation until the pipeline improves
3. Allow users to edit the generated adapter in the staging directory before promotion

---

## 4. Risk Summary Matrix

| Risk ID | Category | Description | P | I | Score | Level |
|---------|----------|-------------|---|---|-------|-------|
| R-T01 | Technical | Website layout changes breaking CSS selectors | 5 | 5 | **25** | **Critical** |
| R-T02 | Technical | Anti-bot detection blocking scrapers | 5 | 4 | **20** | **Critical** |
| R-T04 | Technical | Selectors becoming outdated as sites redesign | 4 | 4 | **16** | **High** |
| R-T12 | Technical | Insufficient hardware for local AI | 4 | 4 | **16** | **High** |
| R-T03 | Technical | JavaScript-heavy pages requiring browser automation | 5 | 3 | **15** | **High** |
| R-L03 | Legal | GDPR/CCPA for scraped personal data | 3 | 5 | **15** | **High** |
| R-O03 | Operational | Selector maintenance overhead | 5 | 3 | **15** | **High** |
| R-T08 | Technical | Browser automation memory/resource consumption | 4 | 3 | **12** | **High** |
| R-T05 | Technical | Cookie/auth session expiration | 4 | 3 | **12** | **High** |
| R-T06 | Technical | Infinite scroll / dynamic loading complications | 4 | 3 | **12** | **High** |
| R-T11 | Technical | Ollama service not running | 3 | 4 | **12** | **High** |
| R-O02 | Operational | Test HTML diverging from production | 4 | 3 | **12** | **High** |
| R-O07 | Operational | Data quality degradation unnoticed | 3 | 4 | **12** | **High** |
| R-T09 | Technical | Network instability and timeouts | 4 | 2 | **8** | **Medium** |
| R-T10 | Technical | HTML parsing edge cases and malformed markup | 3 | 2 | **6** | **Medium** |
| R-T07 | Technical | Proxy requirements for high-volume scraping | 3 | 3 | **9** | **Medium** |
| R-T13 | Technical | Model download failure | 3 | 3 | **9** | **Medium** |
| R-T14 | Technical | Ollama out of memory during inference | 3 | 3 | **9** | **Medium** |
| R-T15 | Technical | Local inference too slow | 3 | 2 | **6** | **Medium** |
| R-L01 | Legal | Website ToS prohibiting scraping | 4 | 4 | **16** | **High** |
| R-L05 | Legal | CFAA legal uncertainty | 2 | 5 | **10** | **Medium** |
| R-L06 | Legal | Different jurisdictional treatment | 3 | 3 | **9** | **Medium** |
| R-L02 | Legal | robots.txt restrictions | 3 | 3 | **9** | **Medium** |
| R-L04 | Legal | Copyright on scraped content | 2 | 3 | **6** | **Medium** |
| R-L07 | Legal | Data residency and cross-border transfer | 2 | 3 | **6** | **Medium** |
| R-L08 | Legal | Local AI data residency (risk eliminated) | 1 | 1 | **1** | **Low** |
| R-O01 | Operational | AI context limits for complex HTML | 4 | 2 | **8** | **Medium** |
| R-O05 | Operational | Dependency on Playwright/browser automation | 3 | 3 | **9** | **Medium** |
| R-O06 | Operational | Scaling challenges with concurrent scrapes | 3 | 3 | **9** | **Medium** |
| R-O08 | Operational | Insufficient documentation leading to misuse | 3 | 3 | **9** | **Medium** |
| R-O09 | Operational | Security vulnerability in parsing pipeline | 2 | 4 | **8** | **Medium** |
| R-O04 | Operational | User skill gap in selector configuration | 3 | 2 | **6** | **Medium** |
| R-O11 | Operational | Reputation risk from user misuse | 2 | 4 | **8** | **Medium** |
| R-O10 | Operational | Loss of archived HTML data | 2 | 2 | **4** | **Low** |
| R-O12 | Operational | Autonomous AI writes broken or incomplete adapters | 4 | 4 | **16** | **High** |
| R-T16 | Technical | Search API rate limits or blocks discovery | 4 | 3 | **12** | **High** |
| R-T17 | Technical | Pagination detection fails on unfamiliar site layouts | 4 | 3 | **12** | **High** |

**Summary by Category**:

| Category | Count | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Technical | 17 | 2 | 11 | 4 | 0 |
| Legal/Compliance | 8 | 1 | 2 | 4 | 1 |
| Operational | 12 | 0 | 4 | 7 | 1 |
| **Total** | **37** | **3** | **17** | **15** | **2** |

---

## 5. Risk Monitoring Framework

### 5.1 Continuous Monitoring

| Metric | Measurement | Threshold | Action |
|--------|-------------|-----------|--------|
| Selector match rate | % of primary selectors matching per platform | <80% → Warning; <60% → Critical | Activate fallback selectors; schedule selector review |
| Scrape success rate | % of URLs returning full data | <90% → Warning; <75% → Critical | Investigate failures; check for anti-bot measures |
| HTTP error rate | % of requests returning 4xx/5xx | >10% → Warning; >25% → Critical | Reduce rate; check for blocks; review selectors |
| Browser resource usage | Memory/CPU per browser context | >300MB → Warning | Reduce concurrency; recycle browser processes |
| Extraction completeness | % of expected fields successfully extracted | <90% → Warning; <70% → Critical | Selector review; HTML structure analysis |
| Rate limit responses | Count of HTTP 429 responses per hour | >5 → Warning; >20 → Critical | Increase delays; implement backoff |
| Session cookie expiry | Days until earliest cookie expiration | <2 days → Warning | Notify user to re-import cookies |
| Data quality anomalies | Statistical deviation in extracted values | 2 std dev → Warning | Investigate source; validate selectors |
| **Ollama service status** | Ollama process running on localhost:11434 | Not running → Warning | Prompt user to start Ollama; disable AI features gracefully |
| **Ollama model loaded** | Currently loaded model name and size | Wrong model loaded → Warning | Auto-select correct model; notify user |
| **GPU VRAM usage** | VRAM utilization during inference | >80% → Warning; >95% → Critical | Trigger model fallback (7b→CPU 7b); suggest hardware upgrade |
| **Inference time** | Time per Ollama inference call | GPU >15s → Warning; CPU >60s → Warning | Check hardware; suggest GPU upgrade; enable caching |
| **Model cache hit rate** | % of AI requests served from cache | < 20% → Warning | Investigate cache config; increase TTL |
| **AI extraction accuracy** | AI extraction confidence scores | < 0.7 avg confidence → Warning | Review prompts; validate against golden set |
| **AI hallucination rate** | % of AI-extracted fields found incorrect | > 10% → Warning; > 25% → Critical | Disable AI for affected platform; manual review |
| **Ollama health score** | Composite: service up + model loaded + VRAM OK + inference OK | Degraded → Warning; Critical → Critical | Auto-fallback chain; notify user; skip AI if needed |

### 5.2 Monitoring Tools

1. **Automated Health Checks**: Daily validation of all P0 platform selectors against live pages
2. **Scrape Metrics Dashboard**: Per-platform success rates, field completeness, timing distributions
3. **Alert System**: Automated notifications when thresholds are breached
4. **Archive Integrity Scanner**: Weekly verification of archived HTML checksums
5. **Rate Limit Monitor**: Per-domain request tracking with automatic delay adjustment
6. **Ollama Health Monitor (F26)**: Continuous monitoring of Ollama service status, GPU VRAM, inference times, model loading status
7. **Hardware Resource Tracker**: Real-time GPU VRAM, CPU, RAM monitoring during local inference

### 5.3 Reporting Cadence

| Report | Frequency | Audience | Content |
|--------|-----------|----------|---------|
| Risk Status | Weekly | Engineering Team | Open risks, new risks, mitigated risks, score changes |
| Platform Health | Daily | Scraping Team | Per-platform selector health, success rates, issues |
| Ollama Health | Daily | Infrastructure Team | Ollama service status, inference times, hardware utilization |
| Risk Review | Monthly | Product + Legal | Full risk register review, mitigation effectiveness, new threats |
| Incident Post-Mortem | Ad-hoc (after incident) | Full Team | Root cause, impact, corrective actions, preventive measures |

---

## 6. Issue Resolution Process

### 6.1 Severity Classification

| Severity | Definition | Response Time | Resolution Target |
|----------|-----------|---------------|-------------------|
| **Critical** | All scrapers broken for a platform; legal issue; security vulnerability | 2 hours | 24 hours |
| **High** | Major platform scraper degraded; selector fallback active for multiple fields | 8 hours | 72 hours |
| **Medium** | Single field extraction failure; performance degradation; documentation gap | 24 hours | 1 week |
| **Low** | Minor feature request; cosmetic issue; enhancement suggestion | 72 hours | Next release |

### 6.2 Resolution Workflow

```
Detection → Triage → Assignment → Investigation → Fix → Validate → Deploy → Monitor
```

1. **Detection**: Automated monitoring, user report, or proactive review identifies issue
2. **Triage**: Classify severity, identify risk IDs impacted, determine if incident response needed
3. **Assignment**: Assign to risk owner and relevant engineers
4. **Investigation**: Root cause analysis, scope assessment, impact evaluation
5. **Fix**: Implement mitigation or contingency plan from risk register
6. **Validate**: Test fix against live pages and snapshot regression suite
7. **Deploy**: Deploy via hot-reload (selectors) or scheduled release (code changes)
8. **Monitor**: Monitor for 48 hours post-deployment to confirm resolution

### 6.3 Escalation Path

| Level | Role | Trigger |
|-------|------|---------|
| L1 | Scraping Engineer | Standard technical issues; selector updates |
| L2 | Lead Engineer + Product Manager | Cross-platform issues; legal concerns; resource constraints |
| L3 | Engineering Director + Legal Advisor | Critical incidents; regulatory matters; major strategic decisions |

---

## 7. Lessons Learned Process

### 7.1 Capture Triggers

Lessons learned are captured after:
- Any Critical or High severity incident
- Monthly risk review meetings
- Major platform HTML structure changes
- Legal or compliance developments
- New platform scraper additions
- Ollama/hardware-related incidents

### 7.2 Documentation Template

Each lessons learned entry includes:
- **Date**: When the lesson was captured
- **Context**: Background and circumstances
- **What Happened**: Description of the event
- **Root Cause**: Underlying cause analysis
- **Impact**: What was affected and how severely
- **Response**: What was done to address it
- **Prevention**: What can prevent recurrence
- **Risk ID**: Related risk register entries
- **Action Items**: Specific follow-up tasks with owners and deadlines

### 7.3 Lessons Learned Log

| Date | Lesson | Category | Risk ID | Action Item | Owner | Status |
|------|--------|----------|---------|-------------|-------|--------|
| 2025-01-20 | Migrated from Kimi API to Ollama local inference | Architecture | All | Eliminated external AI dependency, token cost, and data residency risks; introduced hardware management risks | Product Manager | Complete |
| 2025-01-20 | Initial risk register creation | Process | All | Establish baseline; begin weekly risk monitoring | Product Manager | Active |

### 7.4 Knowledge Sharing

1. **Incident Post-Mortems**: Shared with full team within 48 hours of incident resolution
2. **Monthly Risk Reviews**: Summarized and distributed to stakeholders
3. **Runbook Updates**: Operational procedures updated based on lessons learned
4. **Selector Playbook**: Platform-specific HTML quirks and selector patterns documented
5. **Ollama Troubleshooting Guide**: Hardware-specific issues and resolutions documented

---

## 8. Appendices

### Appendix A: Key Platform-Specific Risk Notes

| Platform | Primary Risk | Secondary Risk | Monitoring Approach |
|----------|-------------|----------------|---------------------|
| Instagram | R-T01 (frequent HTML changes) | R-T02 (aggressive anti-bot) | Daily selector validation; aggressive fallback testing |
| X/Twitter | R-T01 (HTML changes) | R-T03 (JS rendering) | Monitor for A/B tests; test both old and new UI versions |
| TikTok | R-T03 (heavy JS) | R-T06 (infinite scroll) | Browser-only strategy; scroll limit monitoring |
| LinkedIn | R-L01 (ToS enforcement) | R-T02 (anti-bot) | Public-content-only restriction; conservative rate limits |
| Facebook | R-T02 (anti-bot) | R-T01 (HTML changes) | Reduced scrape frequency; robust fallback selectors |
| YouTube | R-T09 (network/CDN) | R-T03 (JS for comments) | CDN endpoint monitoring; transcript extraction validation |
| **Ollama AI** | **R-T11 (service not running)** | **R-T12 (insufficient hardware)** | **Health check every 30s; hardware detection at startup; VRAM monitoring during inference** |

### Appendix B: Legal Jurisdiction Summary

| Jurisdiction | Scraping Legal Framework | Key Considerations |
|-------------|-------------------------|-------------------|
| United States | hiQ v. LinkedIn precedent; CFAA uncertainty | Public data scraping generally permitted; ToS violations may not be criminal |
| European Union | Database Directive; GDPR for personal data | Public data extraction generally allowed; GDPR compliance required for personal data |
| United Kingdom | Similar to EU; UK GDPR applies | Database right considerations; UK GDPR for personal data |
| Canada | CASL for commercial electronic messages | Federal and provincial privacy laws apply to scraped personal data |
| Australia | Spam Act; Privacy Act | APP privacy principles apply to scraped personal information |

### Appendix C: Ollama Hardware Requirements Matrix

| Hardware Tier | GPU | VRAM | RAM | Model | Inference Time | Risk Level |
|--------------|-----|------|-----|-------|----------------|------------|
| **Optimal** | NVIDIA RTX 3060 12GB+ | >= 8GB | 16GB+ | qwen2.5:7b | < 15s | Low (R-T12) |
| **Good** | NVIDIA RTX 2060/3060 6GB | 4-8GB | 16GB+ | qwen2.5:7b | < 15s | Low (R-T12) |
| **Acceptable** | Integrated GPU / No GPU | 0GB | 16GB+ | qwen2.5:7b (CPU) | 30-60s | Medium (R-T15) |
| **Marginal** | Integrated GPU / No GPU | 0GB | 8-16GB | qwen2.5:7b (CPU, limited) | 60s+ | High (R-T12, R-T15) |
| **Insufficient** | Any | Any | < 8GB | AI features disabled | N/A | N/A |

### Appendix D: Risk Register Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-01-20 | **v2.0 Migration**: Replaced Kimi API risks with Ollama local AI risks | Product Manager |
| 2025-01-20 | **Removed**: R-T11 (Kimi API dependency), R-T12 (AI accuracy/hallucination), R-L08 (AI processing of personal data), R-O12 (token cost management) | Product Manager |
| 2025-01-20 | **Added**: R-T11 (Ollama service not running), R-T12 (insufficient hardware), R-T13 (model download failure), R-T14 (Ollama OOM), R-T15 (inference too slow) | Product Manager |
| 2025-01-20 | **Added**: R-L08 (local AI data residency — risk eliminated by architecture) | Product Manager |
| 2025-01-20 | **Updated**: Monitoring framework with Ollama-specific metrics (service status, VRAM, inference time, model cache) | Product Manager |
| 2025-01-20 | **Updated**: Platform-specific notes with Ollama section; Added hardware requirements matrix | Product Manager |
| 2025-01-20 | Initial risk register creation with 28 risks | Product Manager |

---

*This document is a living document and should be reviewed and updated monthly or whenever significant changes occur to the platform, target websites, hardware requirements, or legal landscape.*
