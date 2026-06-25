# Phoenix Engine — Task Breakdown WBS

> **Document Version:** 2.0  
> **Last Updated:** 2025-01-21  
**Classification:** Pure Web Scraping Platform — NO Official APIs  
> **Total Tasks:** 84  
> **Total Story Points:** 560  

---

## Table of Contents

1. [WBS Summary](#wbs-summary)
2. [Phase 1 — Core Scraping Engine](#phase-1)
3. [Phase 2 — Platform HTML Scrapers](#phase-2)
4. [Phase 3 — Intelligence Layer](#phase-3)
5. [Phase 4 — Infrastructure](#phase-4)
6. [Phase 5 — Plugin System](#phase-5)
7. [Phase 6 — Integration & Launch](#phase-6)
8. [Phase 7 — PhoenixArchitect](#phase-7)
9. [Dependency Graph](#dependency-graph)
10. [Resource Loading Chart](#resource-loading)
11. [Risk Register](#risk-register)

---

## WBS Summary

| Phase | Name | Tasks | Story Points | Lead Agent |
|-------|------|-------|:------------:|------------|
| 1 | Core Scraping Engine | 1.1–1.12 | 135 | Ollama Dev-1 (Alpha) |
| 2 | Platform HTML Scrapers | 2.1–2.24 | 170 | Ollama Dev-2 (Beta) + Dev-3 (Gamma) |
| 2.5 | PhoenixArchitect | 2.5.1–2.5.8 | 40 | Ollama Dev-1 (Alpha) |
| 3 | Intelligence Layer | 3.1–3.6 | 75 | Ollama Dev-1 (Alpha) |
| 4 | Infrastructure | 4.1–4.15 | 100 | Ollama DevOps |
| 5 | Plugin System | 5.1–5.10 | 65 | Ollama Dev-3 (Gamma) |
| 6 | Integration & Launch | 6.1–6.11 | 55 | All |
| 7 | PhoenixArchitect | 7.1–7.6 | 40 | Ollama Dev-1 (Alpha) |
| | **TOTAL** | **84** | **560** | |

**Completed items already in the codebase**: stealth/anti-detection module ✅, `phoenix scrape --real` flag ✅, adaptive rate limiting ✅, extraction confidence scoring ✅, PhoenixArchitect autonomous adapter generation with persisted adapters (`src/phoenix/adapters/generated/`) ✅, Researcher search-driven discovery (`phoenix discover`, `phoenix architect generate`) ✅, interactive coding assistant (`scripts/scraping_assistant.py`) with `/agent` mode and `--yes` flag ✅.

---

## Phase 1 — Core Scraping Engine

**Phase Lead:** Kimi Dev-1 (Alpha)  
**Phase Goal:** Build the foundational scraping primitives that power all platform-specific scrapers  
**Phase Points:** 135

---

### 1.1 HTTP Scraper Module — Core Client
**Points:** 13 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.1.1 | Async HTTP client setup | 3 | Configure `httpx.AsyncClient` with connection pooling (limits: 100 max connections, 20 per host), HTTP/2 support, timeout defaults (connect: 5s, read: 30s) |
| 1.1.2 | Custom headers & identity | 2 | Rotating User-Agent strings (Chrome, Firefox, Safari desktop/mobile), Accept-Language negotiation, Referer chain simulation, DNT header |
| 1.1.3 | Response decoding | 2 | Automatic content-encoding handling (gzip, deflate, brotli, zstd), charset detection from headers + meta tags + chardet fallback, binary response handling |
| 1.1.4 | Redirect & URL handling | 2 | Follow redirects (max 10), preserve cookies across redirects, URL normalization (remove tracking params like `utm_*`, `fbclid`), canonical URL extraction |
| 1.1.5 | Cookie jar integration | 2 | `http.CookieJar` integration with external session store, cookie persistence per domain, cookie policy enforcement |
| 1.1.6 | Request signing & integrity | 2 | Request hash for deduplication, response fingerprinting, etag/last-modified support for conditional requests |

**Acceptance Criteria:**
- Successfully fetches 100 test URLs with <2% failure rate
- All response decodings produce valid text
- Cookies flow correctly through redirects
- Unit tests: 95%+ coverage

**Depends On:** — (foundational)  
**Blocks:** 1.3, 1.4, 1.7, 2.1–2.24

---

### 1.2 HTML Parsing Engine
**Points:** 12 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.2.1 | BeautifulSoup integration | 3 | `BeautifulSoup` parser with lxml backend, HTML5lib fallback for malformed HTML, document tree construction, pretty-print debugging output |
| 1.2.2 | lxml integration | 3 | `lxml.html` parser for speed-critical paths, xpath evaluation engine, cssselect translation (CSS → XPath), HTML cleaner for sanitization |
| 1.2.3 | Document navigation | 2 | DOM traversal helpers (parent, sibling, ancestor selectors), scoped searching (search within subtree), multiple root handling |
| 1.2.4 | Text extraction | 2 | Visible text extraction (exclude script/style), whitespace normalization, entity decoding (`&amp;` → `&`), Unicode normalization (NFKC) |
| 1.2.5 | Metadata extraction | 2 | OpenGraph tags (`og:title`, `og:image`, etc.), Twitter Cards, standard meta tags (`description`, `keywords`, `author`), JSON-LD structured data parsing, microdata/RDFa extraction |

**Acceptance Criteria:**
- Parses 20 diverse HTML structures (malformed, minified, XHTML, HTML5)
- Metadata extraction finds OG tags on 95%+ of pages that have them
- Text extraction excludes all script/style content
- Benchmark: parse 100KB HTML in <50ms

**Depends On:** — (foundational)  
**Blocks:** 1.3, 1.4, 1.7

---

### 1.3 CSS Selector Engine
**Points:** 11 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.3.1 | Core CSS selector support | 3 | Full CSS3 selector support via cssselect: class, ID, attribute, pseudo-class (`:nth-child`, `:not`, `:contains`), descendant, child, sibling combinators |
| 1.3.2 | Selector chain execution | 2 | Execute ordered list of selectors, return first match, track which selector succeeded for health monitoring |
| 1.3.3 | Selector health scoring | 2 | Track success rate per selector over time, detect degradation, auto-report when primary selector success drops below threshold |
| 1.3.4 | Structural selectors | 2 | Position-based selection (first/last/nth element), table cell extraction (row/column semantics), list item enumeration |
| 1.3.5 | Debug & introspection | 2 | Selector tester tool (try selector against HTML), match count reporting, execution trace, visual highlighting in debug output |

**Acceptance Criteria:**
- All CSS3 selectors execute correctly against test HTML
- Fallback chain activates when primary selector fails
- Health score accurately reflects selector reliability
- Debug tool shows selector execution trace

**Depends On:** 1.2  
**Blocks:** 1.4, 2.1–2.24

---

### 1.4 XPath Engine
**Points:** 8 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.4.1 | Core XPath support | 3 | Full XPath 1.0 via lxml: axes (`ancestor`, `descendant`, `following`), predicates, functions (`contains()`, `starts-with()`, `text()`), namespace handling |
| 1.4.2 | XPath fallback chains | 2 | Ordered XPath expression lists with fallback, automatic retry on empty result, hybrid CSS+XPath strategies |
| 1.4.3 | Attribute & text extraction | 2 | Extract `@href`, `@src`, `@datetime` attributes, normalize-space text extraction, conditional extraction based on attribute values |
| 1.4.4 | Namespace handling | 1 | XML namespace prefix resolution, default namespace handling, XHTML namespace awareness |

**Acceptance Criteria:**
- XPath 1.0 expressions execute correctly
- Fallback chains work as reliably as CSS chains
- Attribute extraction handles missing attributes gracefully

**Depends On:** 1.2, 1.3  
**Blocks:** 1.5, 2.1–2.24

---

### 1.5 Regex Extraction Helpers
**Points:** 6 | **Assignee:** Kimi Dev-1 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.5.1 | Pattern definition DSL | 2 | Named regex groups mapped to fields, pattern composition, pre-compiled pattern cache |
| 1.5.2 | JS variable extraction | 2 | Extract JSON from `<script>` variables (`window._sharedData = {...}`), parse `ytInitialPlayerResponse`, inline JSON-LD from script tags |
| 1.5.3 | Mixed-mode extraction | 2 | Combine regex with DOM parsing (regex to find JS data, then JSON parse), structural regex (multiline HTML patterns) |

**Acceptance Criteria:**
- Successfully extracts embedded JSON from Instagram, YouTube script tags
- Named groups produce correctly typed output
- Regex cache prevents re-compilation overhead

**Depends On:** 1.2  
**Blocks:** 2.2, 2.4, 2.6, 2.8

---

### 1.6 Browser Scraper Module — Playwright Integration
**Points:** 14 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.6.1 | Playwright setup | 3 | Browser launch (Chromium, Firefox, WebKit), headless/headed mode toggle, viewport configuration (1920x1080 default), locale emulation |
| 1.6.2 | Stealth plugin injection | 3 | `playwright-stealth` integration: patch `navigator.webdriver`, mock `chrome.runtime`, fake `navigator.plugins` and mimeTypes, consistent `navigator.languages`, webGL fingerprint consistency |
| 1.6.3 | Page automation | 2 | Page navigation with wait conditions (networkidle, domcontentloaded), scroll simulation (smooth scroll, random pauses), click interception, form filling |
| 1.6.4 | Content extraction | 2 | `page.content()` for full HTML, `page.evaluate()` for JS data access, element screenshot capture, iframe content access |
| 1.6.5 | Request interception | 2 | Intercept XHR/fetch requests to capture API responses, block unnecessary resources (images, fonts, media) for speed, mock responses for testing |
| 1.6.6 | Error handling | 2 | Timeout recovery, navigation error handling (net::ERR_*), page crash recovery, context isolation on failure |

**Acceptance Criteria:**
- Passes 50 stealth detection tests (FingerprintJS, CreepJS, bot.sannysoft.com)
- Successfully renders and extracts JS-heavy sites (React, Vue, Angular SPAs)
- Request interception captures XHR payloads correctly
- Page crash recovery restarts context automatically

**Depends On:** — (can parallel with 1.1–1.2)  
**Blocks:** 1.8, 2.1–2.24

---

### 1.7 Scraping Strategy Selector — HTTP vs Browser Auto-Detect
**Points:** 10 | **Assignee:** Kimi Dev-1 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.7.1 | Strategy detection | 3 | Analyze target site characteristics: check if content exists in static HTML vs requires JS execution, detect SPA frameworks (React, Vue, Angular), measure initial HTML vs rendered DOM difference |
| 1.7.2 | Automatic strategy selection | 2 | Rule-based: HTTP first for known static sites, browser for SPAs, hybrid: HTTP for initial + browser for details, ML-based classification (site → strategy mapping) |
| 1.7.3 | Performance optimization | 2 | Cache strategy decisions per domain, periodic re-evaluation, A/B test HTTP vs browser for new domains |
| 1.7.4 | Override system | 2 | Per-site manual override in config, per-task override in API call, force-browser patterns for known tricky sites |
| 1.7.5 | Strategy metrics | 1 | Track success rate per strategy per domain, cost comparison (time, resources), auto-recommendation on strategy failure |

**Acceptance Criteria:**
- Auto-detects correct strategy for 90%+ of test sites
- Caches strategy decisions and respects overrides
- Metrics show improved success rate vs fixed strategy

**Depends On:** 1.1, 1.2, 1.6  
**Blocks:** 2.1–2.24

---

### 1.8 Unified Output Normalizer
**Points:** 10 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.8.1 | Schema definition | 2 | Define `ScrapingResult` dataclass: `url`, `title`, `content`, `author`, `timestamp`, `media` (images, videos), `metadata` (platform-specific), `raw_html_ref` |
| 1.8.2 | Content normalization | 2 | HTML entity decoding, URL normalization (relative → absolute), timestamp normalization (any format → ISO 8601), text cleaning (deduplicate whitespace, strip boilerplate) |
| 1.8.3 | Media handling | 2 | Image URL extraction + proxy-through, video URL detection (MP4, HLS, DASH), thumbnail extraction, media metadata (dimensions when available) |
| 1.8.4 | Platform-specific fields | 2 | Extensible schema for platform additions (e.g., `tweet.mentions`, `video.view_count`, `post.reactions`), validation of required vs optional fields |
| 1.8.5 | Output serialization | 2 | JSON output (default), JSONL for streaming, optional HTML snippet inclusion, provenance tracking (which scraper, which selectors, when) |

**Acceptance Criteria:**
- All scrapers produce identical output schema regardless of source platform
- Timestamps consistently normalized to ISO 8601 UTC
- Media URLs are absolute and validated (HTTP 200 check)
- Unit tests for all normalization paths

**Depends On:** 1.1–1.5  
**Blocks:** 2.1–2.24, 6.2

---

### 1.9 Error Handling & Retry Logic
**Points:** 10 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.9.1 | Error classification | 2 | Transient errors (5xx, timeouts, connection reset) vs permanent errors (404, 410, NXDOMAIN), anti-bot indicators (403 with challenge, CAPTCHA signals, rate-limit headers), content errors (empty response, parsing failure) |
| 1.9.2 | Retry strategy | 2 | Exponential backoff: `delay = base * (2 ** attempt) + jitter`, configurable per domain, max retry attempts (default: 3), per-error-type retry policy |
| 1.9.3 | Circuit breaker | 2 | Track failure rate per domain, open circuit when >80% failure rate in 5-min window, half-open test after cooldown (60s), close on success recovery |
| 1.9.4 | Anti-bot response handling | 2 | Detect Cloudflare challenge pages, detect Akamai/Bot Management blocks, detect CAPTCHA presence, escalate to DevOps for proxy rotation |
| 1.9.5 | Graceful degradation | 2 | Partial extraction (some fields missing), return available data + error details, fallback to cached version if fresh fetch fails |

**Acceptance Criteria:**
- Transient failures retried with exponential backoff
- Circuit breaker opens within 30 seconds of sustained failure
- Anti-bot detection triggers proxy rotation request
- Partial results returned with clear error annotations

**Depends On:** 1.1  
**Blocks:** 1.10, 2.1–2.24

---

### 1.10 Audit Logging System
**Points:** 8 | **Assignee:** Kimi Dev-1 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.10.1 | Log schema | 2 | Structured JSON log: `timestamp`, `request_id`, `url`, `method`, `headers_sent`, `response_status`, `response_size_bytes`, `duration_ms`, `scraper_type`, `selectors_used`, `fields_extracted`, `errors`, `proxy_used` |
| 1.10.2 | Log storage | 2 | Async logging to rotating files, optional Redis Stream buffer, log compression (gzip after 24h), retention: hot 7d, warm 30d, cold 90d |
| 1.10.3 | Log querying | 2 | Query by URL pattern, status code range, time range, scraper type, error type, aggregation queries (success rate per domain, avg latency) |
| 1.10.4 | Privacy compliance | 2 | PII redaction in logs, session ID anonymization, configurable retention periods, GDPR-compliant data deletion |

**Acceptance Criteria:**
- Every request creates complete audit log entry
- Query interface answers all common diagnostic questions in <2s
- Log rotation and compression work automatically
- No PII in production logs

**Depends On:** 1.1, 1.9  
**Blocks:** 4.8, 6.2

---

### 1.11 Async Pipeline Controller
**Points:** 12 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.11.1 | Task queue | 2 | Async queue with priority levels (high/medium/low), FIFO within priority, task deduplication (URL + params hash), backpressure handling |
| 1.11.2 | Worker pool | 3 | Dynamic worker pool scaling (min: 5, max: 100), per-domain concurrency limits, semaphore-based resource control, worker health monitoring |
| 1.11.3 | Pipeline stages | 2 | Composable pipeline: Fetch → Parse → Extract → Normalize → Output, per-stage timeout and error handling, stage skip on error configuration |
| 1.11.4 | Event system | 2 | Async events: task_started, task_completed, task_failed, circuit_opened, emit to event bus, webhook callback support |
| 1.11.5 | Resource management | 3 | Memory usage monitoring, automatic GC triggers, connection pool management, browser context allocation/deallocation tracking |

**Acceptance Criteria:**
- Handles 1000 concurrent tasks without memory leaks
- Pipeline stages compose correctly with proper error propagation
- Event system delivers all events within 100ms
- Worker pool scales up and down based on queue depth

**Depends On:** 1.1, 1.6, 1.9  
**Blocks:** 2.1–2.24, 4.3

---

### 1.12 Regex Pattern Library
**Points:** 7 | **Assignee:** Kimi Dev-1 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 1.12.1 | Common patterns | 2 | URL pattern matching, email extraction, phone number extraction, date/time pattern matching (multiple formats), hashtag and mention extraction |
| 1.12.2 | Social platform patterns | 2 | Instagram: `window._sharedData` extraction, X/Twitter: tweet JSON in HTML, TikTok: `SIGI_STATE` extraction, YouTube: `ytInitialPlayerResponse` extraction |
| 1.12.3 | Pattern testing | 2 | Pattern validation against 100+ real HTML samples, false positive rate measurement, pattern performance benchmarking |
| 1.12.4 | Pattern registry | 1 | Named registry of patterns, per-domain pattern sets, pattern versioning |

**Acceptance Criteria:**
- Common patterns tested against diverse samples
- Platform-specific patterns extract embedded JSON correctly
- Pattern registry supports per-domain configuration
- <1% false positive rate on text extraction

**Depends On:** 1.2, 1.5  
**Blocks:** 2.2, 2.4, 2.6, 2.8

---

## Phase 2 — Platform HTML Scrapers

**Phase Lead:** Kimi Dev-2 (Beta) + Kimi Dev-3 (Gamma)  
**Phase Goal:** Build platform-specific scrapers using the core engine  
**Phase Points:** 170

---

### 2.1 Instagram HTML Scraper — Posts
**Points:** 14 | **Assignee:** Kimi Dev-2 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.1.1 | HTML structure analysis | 2 | Analyze Instagram post page DOM: `article` structure, `img` tags with srcset, caption location, engagement buttons, timestamp element |
| 2.1.2 | CSS selector mapping | 2 | Primary: `article img[srcset]` for images, `div[class*="caption"]` for text, `time[datetime]` for timestamp, `span[class*="likes"]` for engagement |
| 2.1.3 | HTTP-based scraper | 2 | Static HTML extraction for public posts, `window._sharedData` regex extraction from `<script>`, extract `graphql.shortcode_media` JSON |
| 2.1.4 | Browser-based scraper | 2 | Playwright for JS-rendered content, scroll to load comments, click "Load more comments" button, handle login-wall detection |
| 2.1.5 | Pagination | 2 | Profile page infinite scroll simulation, detect `has_next_page` in GraphQL response, cursor-based pagination from `end_cursor` |
| 2.1.6 | Auth/cookie handling | 2 | Session cookie import from browser, `ds_user_id` + `sessionid` validation, handle "Login to continue" interception |
| 2.1.7 | Data normalization | 2 | Map to unified schema: `post_url`, `caption`, `images[]`, `video_url?`, `like_count`, `comment_count`, `timestamp`, `username` |

**Acceptance Criteria:**
- Extracts post data from 50 public post URLs with >95% field coverage
- Handles both image and video posts
- Pagination fetches up to 50 posts from profile pages
- Graceful handling of login-wall (returns available data)

**Depends On:** 1.1–1.12  
**Blocks:** 6.2

---

### 2.2 Instagram HTML Scraper — Reels
**Points:** 10 | **Assignee:** Kimi Dev-2 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.2.1 | Reel page analysis | 2 | Reel-specific DOM structure, video player element, audio attribution, effect badges |
| 2.2.2 | Selector mapping | 2 | `meta[property="og:video"]` for video URL, `h1` or caption div for text, view/like/comment counters |
| 2.2.3 | Browser automation | 2 | Playwright required (heavy JS), autoplay handling, video metadata from `window._sharedData` |
| 2.2.4 | Data extraction | 2 | Video URL, caption, hashtags, view count, like count, comment count, audio info, creator username |
| 2.2.5 | Integration | 2 | Unified output with post scraper, shared auth handling, shared pagination |

**Acceptance Criteria:**
- Extracts reel metadata from 30 public reel URLs
- Video URL is direct MP4 link when available
- Handles both desktop and mobile reel page layouts

**Depends On:** 2.1  
**Blocks:** —

---

### 2.3 Instagram HTML Scraper — Profiles
**Points:** 10 | **Assignee:** Kimi Dev-2 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.3.1 | Profile page analysis | 2 | Header section, profile picture, bio, follower/following/post counts, highlight reels |
| 2.3.2 | Selector mapping | 2 | `meta[property="og:title"]` for name, `img[alt*="profile"]` for avatar, header section stats spans |
| 2.3.3 | HTTP + browser strategy | 2 | HTTP for basic info from `window._sharedData`, browser for posts grid with lazy loading |
| 2.3.4 | Profile data extraction | 2 | Username, full name, bio, website link, post count, follower count, following count, profile pic URL |
| 2.3.5 | Recent posts | 2 | Extract recent post grid (up to 12), link to full post scraper for details |

**Acceptance Criteria:**
- Extracts complete profile info from 30 public profiles
- Stats counts are numeric (not formatted strings like "1.2M")
- Post grid links resolve correctly

**Depends On:** 2.1  
**Blocks:** —

---

### 2.4 X/Twitter HTML Scraper — Tweets
**Points:** 15 | **Assignee:** Kimi Dev-2 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.4.1 | HTML structure analysis | 2 | Tweet article DOM: `article[data-testid="tweet"]` structure, user info section, tweet text div, media attachments, engagement bar |
| 2.4.2 | CSS selector mapping | 3 | `article[data-testid="tweet"]` for tweet container, `div[data-testid="tweetText"]` for text, `time[datetime]` for timestamp, `a[href*="status"]` for tweet ID, engagement metrics from `span` with aria-labels |
| 2.4.3 | HTTP-based scraper | 2 | Extract tweet data from initial HTML, parse `window.__INITIAL_STATE__` JSON, extract tweet objects from Redux state |
| 2.4.4 | Browser-based scraper | 3 | Playwright for thread loading, scroll to load reply threads, click "Show more replies", handle "Show additional replies" modal |
| 2.4.5 | Pagination | 2 | Profile timeline infinite scroll, search results pagination via scroll, cursor extraction from `min_position` in API responses |
| 2.4.6 | Media extraction | 2 | Image grid detection (1-4 images), video thumbnail + URL, GIF handling, external card previews |
| 2.4.7 | Reply & quote handling | 1 | Distinguish original tweets from replies, detect quote tweets, extract reply-to chain |

**Acceptance Criteria:**
- Extracts 100 tweets with >95% accuracy on text content
- Engagement metrics (replies, retweets, likes) are correct
- Thread pagination loads full conversation threads
- Media URLs extracted for image and video tweets

**Depends On:** 1.1–1.12  
**Blocks:** 6.2

---

### 2.5 X/Twitter HTML Scraper — Profiles
**Points:** 8 | **Assignee:** Kimi Dev-2 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.5.1 | Profile structure | 2 | Profile header, bio section, pinned tweet, follower/following counts, verified badge detection |
| 2.5.2 | Selector mapping | 2 | `div[data-testid="UserName"]` for name, `div[data-testid="UserDescription"]` for bio, profile image, stats from `a[href*="verified_followers"]` etc. |
| 2.5.3 | Data extraction | 2 | Username, display name, bio, location, website, join date, follower count, following count, tweet count, profile image |
| 2.5.4 | Recent tweets | 2 | Link to tweet scraper for timeline extraction, pinned tweet identification |

**Acceptance Criteria:**
- Extracts complete profile from 30 public profiles
- Verified badge status detected
- Stats are numeric, not formatted

**Depends On:** 2.4  
**Blocks:** —

---

### 2.6 TikTok HTML Scraper — Videos
**Points:** 14 | **Assignee:** Kimi Dev-2 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.6.1 | HTML structure analysis | 2 | TikTok video page: `SIGI_STATE` in `<script>`, video container, caption section, sound info, engagement metrics |
| 2.6.2 | CSS selector mapping | 2 | `div[data-e2e="title"]` for caption, `strong[data-e2e="like-count"]` for likes, `div[data-e2e="browse-video"]` for video |
| 2.6.3 | Browser-based scraper | 3 | Playwright required (heavy anti-bot), request interception for video CDN URLs, `SIGI_STATE` extraction from script tag |
| 2.6.4 | HTTP-based scraper | 2 | Extract metadata from `<meta>` tags (og:title, og:description), parse embedded JSON when available |
| 2.6.5 | Video metadata | 2 | Video URL (direct MP4 or HLS), caption text, hashtags, creator info, sound/music attribution, duration |
| 2.6.6 | Engagement extraction | 2 | Like count, comment count, share count, view count (if visible), bookmark count |
| 2.6.7 | Pagination | 1 | Profile video grid pagination via scroll, related videos sidebar |

**Acceptance Criteria:**
- Extracts video metadata from 30 public TikTok URLs
- Direct video URL or HLS playlist extracted
- Hashtags parsed as individual items
- Handles both desktop and mobile layouts

**Depends On:** 1.1–1.12  
**Blocks:** —

---

### 2.7 TikTok HTML Scraper — Profiles
**Points:** 8 | **Assignee:** Kimi Dev-2 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.7.1 | Profile analysis | 2 | Profile header, avatar, bio stats, video grid layout, follower/following/like counts |
| 2.7.2 | Selector mapping | 2 | `h1[data-e2e="user-title"]` for username, `h2[data-e2e="user-subtitle"]` for nickname, stats from `strong[data-e2e="following-count"]` etc. |
| 2.7.3 | Data extraction | 2 | Username, nickname, bio, follower count, following count, total likes, profile pic, verified status |
| 2.7.4 | Video grid | 2 | Extract video list from profile (links + thumbnails + view counts), pagination via infinite scroll |

**Acceptance Criteria:**
- Extracts profile info from 20 public TikTok profiles
- Video grid lists up to 30 videos with thumbnails
- Stats are numeric

**Depends On:** 2.6  
**Blocks:** —

---

### 2.8 LinkedIn HTML Scraper — Public Posts
**Points:** 12 | **Assignee:** Kimi Dev-2 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.8.1 | HTML structure analysis | 2 | Public post page: `article` or main content div, author info section, post text, engagement bar, comment section |
| 2.8.2 | CSS selector mapping | 2 | `.feed-shared-update-v2__description` for text, `.feed-shared-actor__name` for author, `.social-details-social-counts` for engagement |
| 2.8.3 | HTTP-based scraper | 2 | Extract from public view (no login), parse `<code>` blocks containing JSON data, `<meta>` tag extraction |
| 2.8.4 | Browser-based scraper | 2 | Playwright for full rendering, comment loading via scroll, "Load more comments" click |
| 2.8.5 | Data extraction | 2 | Post text, author name, author profile URL, timestamp, like count, comment count, share count, media attachments |
| 2.8.6 | Public vs auth-walled | 2 | Detect login wall (redirect to login page), return available data + error, handle "Sign in to view" gracefully |

**Acceptance Criteria:**
- Extracts data from 30 public LinkedIn post URLs
- Graceful handling of login-wall content
- Author info and engagement metrics accurate
- Only public posts — no authenticated scraping

**Depends On:** 1.1–1.12  
**Blocks:** —

---

### 2.9 LinkedIn HTML Scraper — Public Profiles
**Points:** 10 | **Assignee:** Kimi Dev-2 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.9.1 | Profile structure | 2 | Public profile layout: top card, about section, experience section, education section |
| 2.9.2 | Selector mapping | 2 | `.top-card-layout__title` for name, `.top-card-layout__headline` for headline, `section.experience` for work history |
| 2.9.3 | Data extraction | 2 | Name, headline, location, about summary, current position, experience list, education list, skills (if visible) |
| 2.9.4 | Public visibility only | 2 | Respect public profile visibility, detect partial visibility ("Sign in to see full profile"), return available sections only |
| 2.9.5 | Browser handling | 2 | Playwright for sections requiring interaction ("Show more" clicks), scroll to load all experience entries |

**Acceptance Criteria:**
- Extracts available data from 20 public profiles
- Respects visibility limits (no auth bypass attempts)
- All available sections extracted completely

**Depends On:** 2.8  
**Blocks:** —

---

### 2.10 Facebook HTML Scraper — Public Posts
**Points:** 13 | **Assignee:** Kimi Dev-3 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.10.1 | HTML structure analysis | 2 | Facebook post HTML: `div[role="article"]` structure, story container, user header, content area, engagement footer |
| 2.10.2 | CSS selector mapping | 2 | `div.story_body_container` for content, `h3` or `h4` for author name, `span[data-ft]` for timestamp, `span[aria-label]` for reactions |
| 2.10.3 | Browser-based scraper | 3 | Playwright required (heavy JS rendering), handle initial page load delay, scroll-triggered content loading |
| 2.10.4 | HTTP-based scraper | 2 | Basic meta tag extraction when available, parse server-rendered HTML fragments |
| 2.10.5 | Data extraction | 2 | Post text, author name, author URL, timestamp, reaction counts (like, love, wow, etc.), share count, comment count, media |
| 2.10.6 | Anti-bot handling | 2 | Detect checkpoint/interstitial pages, handle "Log in to continue" gracefully, rate limit detection |

**Acceptance Criteria:**
- Extracts post data from 30 public Facebook post URLs
- Handles both photo and text posts
- Graceful handling of login checkpoints
- Reaction breakdown (not just total) when visible

**Depends On:** 1.1–1.12  
**Blocks:** —

---

### 2.11 Facebook HTML Scraper — Pages
**Points:** 10 | **Assignee:** Kimi Dev-3 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.11.1 | Page structure | 2 | Page header, profile picture, cover photo, about section, page category, follower count |
| 2.11.2 | Selector mapping | 2 | `h1` for page name, `div[role="main"]` for content, about section divs |
| 2.11.3 | Data extraction | 2 | Page name, category, follower count, like count, website, phone, address (if public), about text |
| 2.11.4 | Recent posts | 2 | Extract recent posts timeline, link to post scraper for detail |
| 2.11.5 | Browser handling | 2 | Playwright for full rendering, handle page tabs (About, Posts, Photos) |

**Acceptance Criteria:**
- Extracts page info from 20 public pages
- Timeline shows up to 10 recent posts
- Stats are numeric

**Depends On:** 2.10  
**Blocks:** —

---

### 2.12 YouTube HTML Scraper — Video Metadata
**Points:** 13 | **Assignee:** Kimi Dev-3 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.12.1 | HTML structure analysis | 2 | Video watch page: `ytInitialPlayerResponse` in `<script>`, `ytInitialData` for page structure, meta tags, video player container |
| 2.12.2 | CSS selector mapping | 2 | `meta[name="title"]` for title, `span.yt-formatted-string` for description, `yt-formatted-string[aria-label]` for view count |
| 2.12.3 | Embedded JSON extraction | 3 | Regex extract `ytInitialPlayerResponse` from script tag, parse as JSON, extract: `videoDetails.title`, `videoDetails.author`, `videoDetails.viewCount`, `microformat.playerMicroformatRenderer` |
| 2.12.4 | HTTP-based scraper | 3 | Primary path: extract embedded JSON from static HTML, no browser needed for basic metadata, secondary: meta tag fallback |
| 2.12.5 | Browser-based scraper | 2 | Playwright for comments section, description "Show more" expansion, related videos sidebar |
| 2.12.6 | Data extraction | 1 | Title, description, channel name, channel URL, view count, like count, publish date, tags, category, duration, thumbnail URLs |

**Acceptance Criteria:**
- Extracts metadata from 50 public video URLs with >98% accuracy
- `ytInitialPlayerResponse` extraction works on all video pages
- View counts are numeric (not formatted)
- Thumbnail URLs at multiple resolutions

**Depends On:** 1.1–1.12, 1.5, 1.12  
**Blocks:** 2.13, 6.2

---

### 2.13 YouTube HTML Scraper — Transcript Extraction
**Points:** 10 | **Assignee:** Kimi Dev-3 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.13.1 | Transcript location | 2 | Parse `ytInitialPlayerResponse.videoDetails.captionTracks`, find caption track URLs (timedtext API), auto-generated vs manual caption detection |
| 2.13.2 | Transcript fetching | 2 | Fetch caption track XML, parse `<text>` elements with `start` and `dur` attributes, handle multiple language tracks |
| 2.13.3 | Format conversion | 2 | Convert to SRT format (sequential numbering, timecode formatting), convert to plain text with timestamps, convert to JSON with timing info |
| 2.13.4 | Language handling | 2 | Auto-detect available languages, default to auto-generated captions, language parameter support |
| 2.13.5 | Error handling | 2 | Handle videos with captions disabled, handle "unavailable in your country", fallback to description text if no captions |

**Acceptance Criteria:**
- Extracts transcripts from 30 videos that have captions
- Supports both auto-generated and manual captions
- SRT output has correct timecodes
- Handles disabled captions gracefully

**Depends On:** 2.12  
**Blocks:** —

---

### 2.14 YouTube HTML Scraper — Channels
**Points:** 10 | **Assignee:** Kimi Dev-3 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.14.1 | Channel structure | 2 | Channel page layout, header with banner, avatar, channel name, subscriber count, video tab |
| 2.14.2 | Selector mapping | 2 | `meta[property="og:title"]` for name, `yt-formatted-string#subscriber-count` for subs, `div#description-container` for description |
| 2.14.3 | ytInitialData extraction | 2 | Parse `ytInitialData` for channel metadata, `header.c4TabbedHeaderRenderer` for stats, `metadata.channelMetadataRenderer` for details |
| 2.14.4 | Data extraction | 2 | Channel name, handle, description, subscriber count, video count, total views, join date, links, avatar URL, banner URL |
| 2.14.5 | Video list | 2 | Extract recent uploads (video IDs, titles, thumbnails, view counts, publish dates), pagination via scroll/infinite load |

**Acceptance Criteria:**
- Extracts channel info from 20 public channels
- Video list shows up to 30 recent uploads
- Stats are numeric

**Depends On:** 2.12  
**Blocks:** —

---

### 2.15 YouTube HTML Scraper — Comments
**Points:** 8 | **Assignee:** Kimi Dev-3 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.15.1 | Comments section | 2 | Parse `ytInitialData` for continuation token, extract top-level comments and replies |
| 2.15.2 | Browser automation | 2 | Scroll to load more comments, click "Show more replies", sort by top/newest |
| 2.15.3 | Data extraction | 2 | Comment text, author name, author channel URL, timestamp, like count, reply count, is_reply flag |
| 2.15.4 | Pagination | 2 | Extract continuation tokens for pagination, configurable max comments to fetch |

**Acceptance Criteria:**
- Extracts comments from 15 videos
- Supports top-level and reply comments
- Configurable comment limit

**Depends On:** 2.12  
**Blocks:** —

---

### 2.16 Generic Web Scraper — Universal Article Extraction
**Points:** 15 | **Assignee:** Kimi Dev-3 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.16.1 | Content detection | 3 | Algorithm to detect main content area vs boilerplate (readability-style), density-based scoring, link-to-text ratio analysis, structural heuristics |
| 2.16.2 | Article extraction | 3 | Extract article title (`<h1>` or OG title), author detection (rel="author", meta tags, byline patterns), publish date extraction (meta tags, JSON-LD, structural patterns), article body (longest text block with paragraph structure) |
| 2.16.3 | Universal selectors | 2 | Platform-agnostic fallback chain: OG tags → semantic HTML (`<article>`, `<main>`) → readability algorithm → largest text block |
| 2.16.4 | Multi-site testing | 3 | Test on 50 diverse sites: news sites (CNN, BBC, NYT), blogs (Medium, Substack), corporate sites, forums — without any site-specific configuration |
| 2.16.5 | Edge case handling | 2 | Handle: multi-page articles, AMP pages, paywall detection, login-walled content, empty/error pages, non-article pages (redirect to generic metadata extraction) |
| 2.16.6 | Quality scoring ✅ | 2 | Content quality score (length, structure, metadata completeness), confidence score for each extracted field, recommendation when manual review needed |

**Acceptance Criteria:**
- Successfully extracts articles from 50 diverse sites
- Title, author, date, body extracted with >90% accuracy
- No site-specific configuration required
- Quality score accurately reflects extraction confidence

**Depends On:** 1.1–1.12  
**Blocks:** 5.4, 6.2

---

### 2.17 Generic Web Scraper — Metadata Extraction
**Points:** 8 | **Assignee:** Kimi Dev-3 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.17.1 | Meta tag extraction | 2 | Standard meta tags, OpenGraph tags, Twitter Cards, JSON-LD structured data, Dublin Core |
| 2.17.2 | Link extraction | 2 | All links on page (href + anchor text), external vs internal classification, canonical URL detection |
| 2.17.3 | Image extraction | 2 | All images (src + alt text), filter by size (exclude tiny icons), hero image detection |
| 2.17.4 | Structured data | 2 | Schema.org parsing (Article, Person, Organization, VideoObject, etc.), RDFa parsing, microdata extraction |

**Acceptance Criteria:**
- Extracts complete metadata from 30 diverse pages
- Structured data parsed for all common schema types
- Link classification (internal/external) is accurate

**Depends On:** 2.16  
**Blocks:** —

---

### 2.18–2.24 Pagination Handlers (Shared Component)
**Points:** 14 | **Assignee:** Kimi Dev-2 + Dev-3 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 2.18 | Infinite scroll handler | 2 | Detect scroll-triggered loading (mutation observer pattern), simulate scroll events, detect "no more content" signal, configurable max scroll depth |
| 2.19 | Load-more button handler | 2 | Detect "Load more" / "Show more" buttons, click via Playwright, retry on stale element, detect button disappearance |
| 2.20 | Page number handler | 2 | URL pattern pagination (`?page=2`, `/page/2/`), next/previous link detection, page count estimation, sequential or parallel fetching |
| 2.21 | Cursor/token pagination | 2 | Extract continuation tokens from JS variables or API responses (`cursor`, `offset`, `token`), append to subsequent requests, detect end-of-list |
| 2.22 | Pagination unification | 2 | Unified `Paginator` interface: `has_more()`, `next_page()`, `get_all()`, auto-detect pagination type per page |
| 2.23 | Pagination metrics | 2 | Track items per page, total items fetched, pagination failure rate, adaptive fetch sizing |
| 2.24 | Pagination tests | 2 | Test each pagination type with recorded HTML fixtures, simulate slow loading, test max depth enforcement |

**Acceptance Criteria:**
- All 4 pagination types work correctly
- Unified interface works across all platform scrapers
- Max depth and item limits enforced
- Tests cover edge cases (empty pages, stuck loaders)

**Depends On:** 1.6, 1.11  
**Blocks:** 2.1–2.17

---

## Phase 2.5 — PhoenixArchitect: Autonomous Adapter Generation

**Phase Lead:** PhoenixArchitect agent swarm (Planner, Researcher, Explorer, Inspector, Coder, Critic)  
**Phase Goal:** Enable Phoenix Engine to discover new listing platforms from a goal, browse candidate sites, inspect their HTML, generate a Python adapter, validate it, and export/register the adapter — all via local LLM multi-role agents.  
**Phase Points:** 55

| ID | Task | Points | Description |
|---|---|---|---|
| 2.5.1 | Search-dork builder | 4 | Translate a high-level goal ("scrape apartments in Cairo") into platform-agnostic search dorks for DuckDuckGo/Google, e.g. `apartments for rent cairo`. |
| 2.5.2 | Search client | 4 | Integrate a lightweight search client (duckduckgo-search or similar) with rate-limit/backoff; return ranked result URLs + titles/snippets. |
| 2.5.3 | Browser explorer | 6 | Spawn a headed/headless browser from the engine pool, navigate to each candidate URL, apply stealth headers/fingerprints, and record landing HTML + screenshot. |
| 2.5.4 | Page collector | 5 | Scroll, detect pagination, click "Next"/ numbered pages, and capture a representative sample of listing pages (category + detail) into HTML fixtures. |
| 2.5.5 | HTML inspector | 6 | Use `dolphincoder:7b`/`qwen2.5:7b` via Ollama to extract CSS selectors for listing containers, fields (title, price, location, image, detail URL), and pagination strategy. |
| 2.5.6 | Adapter coder | 8 | Generate a `BaseAdapter` subclass using Jinja template + LLM; produce `parse_listings`, `parse_detail`, `pagination`, and metadata conforming to existing adapter contract. |
| 2.5.7 | Critic validator | 6 | Compile/run generated adapter against collected fixtures; compare extracted records to expected schema; feed errors back to Coder for a fix loop (max 3 iterations). |
| 2.5.8 | Export & registration | 4 | Auto-format with ruff/black, type-check with mypy, write unit tests, and add adapter to `adapters/__init__.py` with dynamic registration support. |
| 2.5.9 | CLI integration | 5 | Add `phoenix architect --goal "..." [--auto-approve]` command that runs the full pipeline and emits generated artifacts to `src/phoenix/adapters/generated/`. |
| 2.5.10 | Safety guardrails | 4 | Robots.txt / Terms-of-Service check hints, domain allow-list/block-list, human-in-the-loop approval before publishing generated adapter. |
| 2.5.11 | PhoenixArchitect tests | 3 | Mock search results, browser snapshots, and LLM responses; assert the end-to-end loop emits a compilable adapter. |

**Acceptance Criteria:**
- A user can run `phoenix architect --goal "find rental apartments in Cairo"` and receive a generated adapter.
- Generated adapter passes ruff, black, mypy, and mocked HTML tests for the collected site samples.
- Critic loop reduces validation errors by ≥50% within 3 iterations on benchmark fixtures.

**Depends On:** 1.6, 1.11, 2.1–2.24  
**Blocks:** None

---

## Phase 3 — Intelligence Layer

**Phase Lead:** Kimi Dev-1 (Alpha)  
**Phase Goal:** AI-assisted capabilities for resilient and smart scraping  
**Phase Points:** 75

---

### 3.1 AI-Assisted HTML Structure Analysis
**Points:** 15 | **Assignee:** Kimi Dev-1 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 3.1.1 | DOM feature extraction | 3 | Extract structural features from DOM: tag distribution, class name patterns, id naming conventions, nesting depth, semantic tag usage |
| 3.1.2 | Content region detection | 3 | ML-based main content region detection using features: text density, link density, visual position hints, tag semantics |
| 3.1.3 | Dynamic content detection | 3 | Detect if content is JS-rendered: compare static HTML vs rendered DOM, detect framework signatures (React `data-reactroot`, Vue `__vue__`, Angular `ng-*`) |
| 3.1.4 | Structure change detection | 3 | Compare current DOM structure with known pattern, detect class name changes, detect element reordering, alert on significant structure drift |
| 3.1.5 | Selector recommendation | 3 | Given target content type (post, article, product), recommend selector strategy based on DOM analysis, suggest robust selectors over fragile ones |

**Acceptance Criteria:**
- Content region detection finds main content on 90%+ of test pages
- Framework detection correctly identifies React/Vue/Angular/None
- Structure change detection alerts within 1 hour of layout changes
- Selector recommendations are more robust than baseline

**Depends On:** 1.2, 1.3, 1.7  
**Blocks:** 3.2, 3.3

---

### 3.2 Smart Selector Fallback Chains
**Points:** 13 | **Assignee:** Kimi Dev-1 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 3.2.1 | Fallback chain definition | 2 | Declarative fallback chains: `primary` → `secondary` → `tertiary` → `heuristic`, each entry with strategy (CSS/XPath/regex/ML) and timeout |
| 3.2.2 | Chain execution engine | 2 | Execute chains in order, track which selector succeeded, record success distribution for optimization, parallel execution of multiple chains |
| 3.2.3 | Auto-fallback generation | 3 | Generate fallback selectors automatically from successful primary selector: class-only fallback, tag+parent fallback, positional fallback, content-based fallback |
| 3.2.4 | Chain optimization | 3 | Machine learning on selector success rates: reorder chain based on empirical success, remove consistently failing selectors, add newly discovered successful selectors |
| 3.2.5 | Fallback metrics | 3 | Track fallback activation rate per field, alert when primary selector success < 90%, recommend chain updates |

**Acceptance Criteria:**
- Fallback chains activate transparently when primary fails
- Auto-generated fallbacks are more robust than hand-written ones
- Chain optimization improves success rate by >5% over static chains
- Metrics accurately track selector health

**Depends On:** 1.3, 1.4, 3.1  
**Blocks:** 3.4

---

### 3.3 Content Type Classifier
**Points:** 12 | **Assignee:** Kimi Dev-1 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 3.3.1 | Feature extraction | 2 | HTML-based features: meta tags, OG type, structured data, URL patterns, domain, path structure |
| 3.3.2 | Classifier training | 3 | Train on labeled dataset: article, product, profile, post, video, forum_thread, homepage, category_page, using features + light ML model |
| 3.3.3 | Rule-based classifier | 3 | URL pattern rules (`/p/` = Instagram post, `/status/` = tweet, `/watch?v=` = YouTube video), meta tag rules (`og:type` mapping), domain-specific rules |
| 3.3.4 | Hybrid classification | 2 | Combine rule-based (fast, deterministic) with ML-based (accurate on edge cases), confidence scoring, human-review queue for low-confidence |
| 3.3.5 | Classification-driven extraction | 2 | Route to appropriate scraper based on classification, select selector set based on content type, adjust strategy (HTTP vs browser) based on type |

**Acceptance Criteria:**
- Classifies content type with >95% accuracy on test set
- Rule-based covers 80%+ of common cases instantly
- ML handles edge cases and new platforms
- Classification correctly routes to appropriate scraper

**Depends On:** 1.2, 1.8  
**Blocks:** 3.5

---

### 3.4 Anti-Bot Detection & Response
**Points:** 15 | **Assignee:** Kimi Dev-1 + DevOps | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 3.4.1 | Block page detection | 3 | Detect known block pages: Cloudflare challenge (IUAM, CAPTCHA), Akamai Bot Manager, PerimeterX/Human, DataDome, custom WAF pages |
| 3.4.2 | Response pattern analysis | 3 | Analyze response patterns: HTTP 403 with challenge cookie, 429 rate limit, redirect to /challenge, response time anomalies (block pages load fast), content length anomalies |
| 3.4.3 | Fingerprint randomization | 3 | Rotate: User-Agent (consistent with OS), Accept headers, viewport size, timezone, language, canvas/WebGL noise (via Playwright stealth) |
| 3.4.4 | Response strategy | 3 | On block detection: rotate proxy, rotate session, increase delay, switch to browser mode, escalate to manual review after N failures |
| 3.4.5 | Anti-bot metrics | 3 | Track block rate per domain per strategy, proxy block rate, session validity duration, time-to-block metrics |

**Acceptance Criteria:**
- Detects all major anti-bot systems with >95% accuracy
- Automatic response reduces block rate by >80%
- Fingerprint rotation maintains consistency per session
- Metrics dashboard shows anti-bot status

**Depends On:** 1.6, 1.9, 3.2, 4.2, 4.3  
**Blocks:** 6.2

---

### 3.5 Automatic Scraper Repair
**Points:** 12 | **Assignee:** Kimi Dev-1 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 3.5.1 | Failure detection | 2 | Detect when scraper returns empty/malformed data, compare output schema completeness against baseline, detect field-level null rate spikes |
| 3.5.2 | HTML diff analysis | 3 | Compare current HTML with last-known-good HTML, identify changed class names, moved elements, renamed attributes, structural changes |
| 3.5.3 | Selector regeneration | 3 | Generate new selector candidates from current HTML, rank by stability (avoid generated class names), test candidates against current HTML |
| 3.5.4 | Repair validation | 2 | Run repaired scraper against test fixtures, validate output schema completeness, regression test against known URLs |
| 3.5.5 | Human review queue | 2 | Queue suggested repairs for review, highlight confidence level, auto-apply high-confidence repairs after validation |

**Acceptance Criteria:**
- Detects scraper breakage within 1 hour
- Generates repair suggestions with >70% accuracy
- Validated repairs pass all regression tests
- Human review queue is manageable (< 10 items/day)

**Depends On:** 3.1, 3.2  
**Blocks:** —

---

### 3.6 Adaptive Rate Limiting
**Points:** 8 | **Assignee:** Kimi Dev-1 + DevOps | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 3.6.1 | Response-based adaptation ✅ | 2 | Monitor response codes: increase delay on 429, decrease delay on consistent 200s, detect soft blocks (200 with empty content) |
| 3.6.2 | Domain profiling | 2 | Build per-domain rate tolerance profile, learn from historical patterns, share profiles across instances |
| 3.6.3 | Aggressive site detection | 2 | Detect sites with strict rate limiting early, classify sites by tolerance (lenient/moderate/strict), apply appropriate default delays |
| 3.6.4 | Adaptive algorithm ✅ | 2 | Gradient-based rate adjustment: small increments on success, larger decrements on failure, floor/ceiling constraints, jitter addition |

**Acceptance Criteria:**
- Adapts to site tolerance within 10 requests
- No IP bans during normal operation
- Throughput optimized per domain
- Shared profiles improve cold-start behavior

**Depends On:** 1.9, 4.5  
**Blocks:** —

---

## Phase 4 — Infrastructure

**Phase Lead:** Kimi DevOps  
**Phase Goal:** Build resilient, scalable, observable scraping infrastructure  
**Phase Points:** 100

---

### 4.1 Cookie & Session Manager
**Points:** 12 | **Assignee:** Kimi DevOps | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.1.1 | Session storage | 3 | SQLite schema for sessions: `id`, `domain`, `cookies_json` (encrypted), `created_at`, `last_used`, `use_count`, `is_valid`, AES-256-GCM encryption with key rotation |
| 4.1.2 | Cookie jar management | 2 | Per-domain cookie jars, cookie expiration handling, secure flag enforcement, SameSite handling, automatic cookie refresh detection |
| 4.1.3 | Session rotation | 2 | Round-robin session selection per domain, session cooldown (min time between uses), session retirement after max uses, health-based selection (prefer valid sessions) |
| 4.1.4 | Session validation | 2 | Validate session by making test request, detect logout/session expiry, auto-mark invalid sessions, re-validation schedule |
| 4.1.5 | Import/export | 2 | Import cookies from browser (Netscape format, JSON), export for backup, session migration between instances |
| 4.1.6 | Privacy & security | 1 | Encrypted at rest, secure key management (environment variable), audit log of session access, automatic expiration |

**Acceptance Criteria:**
- Session storage with AES-256 encryption
- Rotation prevents session exhaustion
- Invalid sessions detected and retired automatically
- Import from Chrome/Firefox cookie format

**Depends On:** — (foundational)  
**Blocks:** 2.1–2.24, 4.3

---

### 4.2 Proxy Management Infrastructure
**Points:** 12 | **Assignee:** Kimi DevOps | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.2.1 | Proxy pool | 3 | Support: HTTP/HTTPS proxies, SOCKS4/5 proxies, authenticated proxies (user:pass), proxy chain support, pool configuration via file/ENV/API |
| 4.2.2 | Health checking | 2 | Periodic proxy health checks (HTTP GET to known endpoint), response time measurement, anonymity verification (header leak detection), geo-location verification |
| 4.2.3 | Rotation strategy | 2 | Per-request rotation, sticky sessions (same proxy for domain session), least-recently-used, performance-based selection (lowest latency), failure-based exclusion |
| 4.2.4 | Geographic targeting | 2 | Target specific countries/regions, ASN targeting, city-level targeting, fallback chain for geo preferences |
| 4.2.5 | Failover handling | 2 | Automatic failover on proxy failure, retry with different proxy, mark proxy as failed after N consecutive failures, automatic recovery testing |
| 4.2.6 | Proxy metrics | 1 | Success rate per proxy, average latency, bytes transferred, failure reasons, cost tracking |

**Acceptance Criteria:**
- Pool of 50+ proxies manageable
- Health check marks failed proxies within 60s
- Rotation prevents IP-based blocking
- Geographic targeting works accurately

**Depends On:** — (foundational)  
**Blocks:** 2.1–2.24, 3.4

---

### 4.3 Browser Instance Pool Management
**Points:** 10 | **Assignee:** Kimi DevOps | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.3.1 | Pool architecture | 2 | Context-per-task isolation, persistent browser process, dynamic pool sizing (min: 2, max: 20), queue for browser requests |
| 4.3.2 | Lifecycle management | 2 | Browser process start/stop/restart, automatic restart on crash, memory leak prevention (periodic context purge), graceful shutdown |
| 4.3.3 | Context fingerprinting | 2 | Per-context fingerprint configuration: viewport, user-agent, locale, timezone, color scheme, consistent fingerprint per session |
| 4.3.4 | Resource limits | 2 | Per-context memory limits, page count limits, timeout enforcement, CPU usage monitoring |
| 4.3.5 | Pool monitoring | 2 | Active contexts count, queue depth, average wait time, context creation time, crash rate |

**Acceptance Criteria:**
- 20 concurrent browser contexts without crashes
- Context isolation (cookies, localStorage separated)
- Automatic restart on memory >500MB per context
- Wait time <5s when pool at capacity

**Depends On:** 1.6, 4.1  
**Blocks:** 2.1–2.24

---

### 4.4 Browser Stealth Configuration
**Points:** 8 | **Assignee:** Kimi DevOps | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.4.1 | Stealth plugin management | 2 | `playwright-stealth` integration, custom stealth scripts, canvas fingerprint noise, WebGL vendor consistency |
| 4.4.2 | Consistent identity | 2 | Per-context consistent fingerprint: same User-Agent + viewport + locale throughout session, browser-level consistency (plugins, fonts, canvas) |
| 4.4.3 | Detection evasion | 2 | `navigator.webdriver = false`, mock `chrome.runtime`, consistent `navigator.plugins`, Permission API mock, WebDriver property removal |
| 4.4.4 | Stealth testing | 2 | Automated testing against fingerprinting libraries (FingerprintJS, CreepJS, BotD), score tracking per configuration, A/B testing stealth configurations |

**Acceptance Criteria:**
- Passes FingerprintJS with uniqueness < 1 in 1000
- Consistent identity throughout session
- All known automation leaks patched
- Stealth score tracked over time

**Depends On:** 1.6, 4.3  
**Blocks:** 2.1–2.24

---

### 4.5 Rate Controller
**Points:** 10 | **Assignee:** Kimi DevOps | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.5.1 | Per-domain configuration | 2 | Configurable: requests/second, concurrent requests, delay between requests, burst allowance, daily/hourly quotas |
| 4.5.2 | robots.txt compliance | 2 | Fetch and parse robots.txt, respect Crawl-delay, respect Disallow directives, cache robots.txt per domain |
| 4.5.3 | Distributed coordination | 2 | Redis-based distributed rate limiting, consistent across instances, token bucket algorithm, sliding window counting |
| 4.5.4 | Adaptive adjustment | 2 | Auto-increase delay on 429 responses, auto-decrease on consistent success, integrate with Phase 3.6 adaptive rate limiting |
| 4.5.5 | Rate metrics | 2 | Current RPS per domain, throttle events, queue wait time, quota exhaustion tracking |

**Acceptance Criteria:**
- Respects robots.txt for all domains
- Per-domain rate limits enforced accurately
- Distributed rate limiting consistent across 5 instances
- No rate limit violations during normal operation

**Depends On:** — (foundational)  
**Blocks:** 2.1–2.24, 3.6

---

### 4.6 Raw HTML Archive Storage
**Points:** 10 | **Assignee:** Kimi DevOps | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.6.1 | Storage format | 2 | Raw HTML + metadata stored together, zstd compression (ratio > 5:1), content-addressable (SHA-256 hash), deduplication |
| 4.6.2 | Retention policies | 2 | Tiered storage: hot (SSD, 7 days), warm (object storage, 30 days), cold (archive, 90 days), configurable per domain |
| 4.6.3 | Query interface | 2 | Query by URL, time range, domain, content hash, response status, full-text search on extracted text |
| 4.6.4 | Backup & recovery | 2 | Daily incremental backups, point-in-time recovery, cross-region replication for critical data, backup integrity verification |
| 4.6.5 | Storage metrics | 2 | Storage used per domain, compression ratio, dedup savings, retrieval latency, growth rate |

**Acceptance Criteria:**
- Compression ratio > 5:1
- Retrieval latency <100ms for hot storage
- Deduplication prevents identical re-storage
- Backup recovery tested monthly

**Depends On:** 1.10  
**Blocks:** 6.2

---

### 4.7 Structured Output Storage
**Points:** 8 | **Assignee:** Kimi DevOps | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.7.1 | JSON output storage | 2 | Structured scraping results in JSON, schema validation, indexed fields for querying, versioned schema |
| 4.7.2 | Export system | 2 | JSON export (default), CSV export (tabular data), JSONL export (streaming), XML export, Parquet export (analytics) |
| 4.7.3 | Query API | 2 | Filter by URL, domain, date range, content type, full-text search on content, aggregation queries |
| 4.7.4 | Data retention | 2 | Configurable retention per project, automatic purging, GDPR deletion support, data export for portability |

**Acceptance Criteria:**
- All export formats produce valid output
- Query API responds in <2s for common queries
- Schema validation rejects invalid data
- Retention policy automatically enforced

**Depends On:** 1.8  
**Blocks:** 6.2

---

### 4.8 Monitoring & Alerting
**Points:** 10 | **Assignee:** Kimi DevOps | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.8.1 | Metrics collection | 2 | Collect: requests/min, success rate, latency (p50/p95/p99), bytes transferred, selector success rate, proxy health, browser pool utilization |
| 4.8.2 | Dashboard | 2 | Grafana/Prometheus dashboard: per-domain status, overall health, top errors, queue depth, resource usage, trend graphs |
| 4.8.3 | Alerting rules | 2 | Alerts: success rate < 95%, latency p95 > 10s, queue depth > 1000, browser crash rate > 5%, proxy failure rate > 20%, disk usage > 80% |
| 4.8.4 | Log aggregation | 2 | Centralized log collection (Loki/ELK), structured log parsing, log-based alerting, log correlation across services |
| 4.8.5 | Health checks | 2 | `/health` endpoint, readiness/liveness probes, dependency health checks (Redis, storage), automated health reports |

**Acceptance Criteria:**
- Dashboard refreshes within 5 seconds
- Alerts fire within 30 seconds of threshold breach
- All logs queryable within 1 minute of generation
- Health endpoint accurately reflects system state

**Depends On:** 1.10, 4.6, 4.7  
**Blocks:** 6.2

---

### 4.9 Docker Deployment
**Points:** 8 | **Assignee:** Kimi DevOps | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.9.1 | Container images | 2 | Multi-stage Dockerfile (builder → runtime), Playwright browser installation, minimal attack surface image, image size < 500MB |
| 4.9.2 | Docker Compose | 2 | `docker-compose.yml` with all services, environment variable configuration, volume mounts for persistent data, network isolation |
| 4.9.3 | Health checks | 2 | Container health checks, restart policies, resource limits (CPU, memory), graceful shutdown handling |
| 4.9.4 | Environment parity | 2 | Dev/staging/prod parity via environment variables, feature flags, configuration management, secret management |

**Acceptance Criteria:**
- `docker-compose up` starts full stack
- Container starts in <30 seconds
- Health checks pass within 60 seconds
- Graceful shutdown preserves in-flight tasks

**Depends On:** 4.1–4.8  
**Blocks:** 6.4

---

### 4.10 CI/CD Pipeline
**Points:** 6 | **Assignee:** Kimi DevOps | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.10.1 | Build pipeline | 2 | Automated build on push, lint (ruff, mypy), unit tests, integration tests, Docker image build, security scan |
| 4.10.2 | Test automation | 2 | Run all test suites in CI, HTML fixture validation, selector regression tests, browser scraper tests with Playwright |
| 4.10.3 | Deployment | 2 | Automated staging deployment, manual production gate, blue-green deployment, rollback capability |

**Acceptance Criteria:**
- Build completes in <10 minutes
- All tests pass before deployment
- Staging auto-deploys on green build
- Rollback completes in <5 minutes

**Depends On:** 4.9  
**Blocks:** 6.4

---

### 4.11–4.15 Security & Compliance
**Points:** 14 | **Assignee:** Kimi DevOps | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 4.11 | Secret management | 3 | API keys, proxy credentials, encryption keys in environment variables or secret manager, rotation schedule, audit access |
| 4.12 | TLS/SSL | 2 | All external communication over HTTPS, certificate validation, custom CA support for proxies, cipher suite configuration |
| 4.13 | Input validation | 3 | URL validation (scheme, host, path), sanitize all inputs, prevent SSRF (block internal IPs, localhost), rate limit on API endpoints |
| 4.14 | Audit trail | 3 | All operations logged with timestamp + actor + action + result, tamper-resistant storage, retention compliance, audit report generation |
| 4.15 | GDPR/privacy | 3 | Data minimization (only collect requested fields), retention limits, data deletion API, privacy impact assessment, user consent tracking |

**Acceptance Criteria:**
- No secrets in code or logs
- SSRF prevention blocks all internal IP requests
- Audit trail is complete and tamper-resistant
- GDPR deletion completes within 30 days request

**Depends On:** 4.9  
**Blocks:** 6.4

---

## Phase 5 — Plugin System

**Phase Lead:** Kimi Dev-3 (Gamma)  
**Phase Goal:** Build extensible plugin architecture for custom scrapers  
**Phase Points:** 65

---

### 5.1 Plugin Interface Design
**Points:** 10 | **Assignee:** Kimi Dev-3 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 5.1.1 | Abstract base class | 2 | `BaseScraperPlugin` with methods: `can_handle(url)`, `scrape(url)`, `get_selectors()`, `get_config()`, type hints, docstring standards |
| 5.1.2 | URL pattern matching | 2 | Pattern registration: regex patterns, glob patterns, domain matching, path prefix matching, priority ordering |
| 5.1.3 | Selector registration | 2 | Declarative selector sets: CSS selectors, XPath expressions, regex patterns, fallback chains, selector documentation |
| 5.1.4 | Configuration schema | 2 | Per-plugin config: rate limits, auth requirements, browser vs HTTP preference, custom headers, timeout overrides |
| 5.1.5 | Lifecycle hooks | 2 | `on_load()`, `before_scrape()`, `after_scrape()`, `on_error()`, `on_unload()` hooks for plugin lifecycle management |

**Acceptance Criteria:**
- Base class is well-documented and type-hinted
- URL pattern matching resolves correct plugin for test URLs
- Selector registration supports all selector types
- Lifecycle hooks fire in correct order

**Depends On:** 1.1–1.12  
**Blocks:** 5.2–5.10

---

### 5.2 Plugin Loader & Registration
**Points:** 10 | **Assignee:** Kimi Dev-3 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 5.2.1 | Discovery mechanism | 2 | Auto-discover plugins from directory, package-based plugin loading, entry point registration (`setup.py` entry_points), explicit registration API |
| 5.2.2 | Dependency injection | 2 | Inject core engine components (HTTP client, browser pool, selector engine), inject config, inject logger, inject audit trail |
| 5.2.3 | Hot reload | 2 | Watch plugin files for changes, reload without engine restart, graceful degradation on reload failure, version tracking |
| 5.2.4 | Validation framework | 2 | Validate plugin on load: URL patterns compile, selectors are valid, required methods implemented, config schema validates |
| 5.2.5 | Plugin registry | 2 | In-memory registry of loaded plugins, conflict detection (multiple plugins for same URL), priority resolution, listing/query API |

**Acceptance Criteria:**
- Plugin discovered and loaded automatically from directory
- Hot reload updates plugin without restart
- Invalid plugins rejected with clear error messages
- Conflict resolution works for overlapping patterns

**Depends On:** 5.1  
**Blocks:** 5.3, 5.4

---

### 5.3 Plugin SDK & Documentation
**Points:** 10 | **Assignee:** Kimi Dev-3 | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 5.3.1 | SDK package | 2 | Publish `phoenix-plugin-sdk` package, base classes, utility functions, testing helpers, type stubs |
| 5.3.2 | CLI tooling | 2 | `phoenix-plugin create` — scaffold new plugin, `phoenix-plugin validate` — validate plugin, `phoenix-plugin test` — run plugin tests |
| 5.3.3 | Documentation | 2 | Plugin development guide, API reference, best practices, common patterns, troubleshooting guide |
| 5.3.4 | Testing utilities | 2 | Mock HTML fixtures for plugin tests, test HTTP client, test browser context, assertion helpers for scraper output |
| 5.3.5 | Example walkthrough | 2 | Step-by-step tutorial: create a plugin for a custom news site, from setup to deployment |

**Acceptance Criteria:**
- SDK installable via `pip install phoenix-plugin-sdk`
- CLI scaffolding creates working plugin template
- Documentation covers all plugin development topics
- Testing utilities reduce plugin test boilerplate by 80%

**Depends On:** 5.1, 5.2  
**Blocks:** 5.5

---

### 5.4 Example Custom Scraper Plugin
**Points:** 12 | **Assignee:** Kimi Dev-3 | **Priority:** P2

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 5.4.1 | News site plugin | 3 | Complete example: scrape a news site (e.g., Hacker News), URL pattern matching, article extraction, comment extraction |
| 5.4.2 | E-commerce product plugin | 3 | Product scraper example: extract product title, price, description, images, reviews from a product page |
| 5.4.3 | Forum thread plugin | 3 | Forum scraper example: extract thread title, posts (author, content, timestamp), pagination handling |
| 5.4.4 | Integration tests | 3 | Full integration tests for each example plugin, recorded HTML fixtures, CI pipeline integration |

**Acceptance Criteria:**
- All 3 example plugins pass integration tests
- Each plugin demonstrates different capabilities
- Plugins serve as reference implementations
- Tests use recorded HTML fixtures (no live requests in CI)

**Depends On:** 5.2, 5.3, 2.16  
**Blocks:** 5.5

---

### 5.5 Plugin Marketplace (Basic)
**Points:** 8 | **Assignee:** Kimi Dev-3 | **Priority:** P3

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 5.5.1 | Plugin manifest | 2 | `plugin.yaml` manifest: name, version, author, description, supported URLs, dependencies, documentation URL |
| 5.5.2 | Plugin directory | 2 | JSON/YAML registry of available plugins, search by domain/URL pattern, version history, popularity metrics |
| 5.5.3 | Installation | 2 | `phoenix-plugin install <name>` — download and install, dependency resolution, version pinning, uninstall support |
| 5.5.4 | Community guidelines | 2 | Contribution guide, code of conduct, review process, quality standards, security requirements |

**Acceptance Criteria:**
- Plugin manifest validates against schema
- Directory lists all available plugins
- Install command works end-to-end
- Contribution guide is complete

**Depends On:** 5.2, 5.3, 5.4  
**Blocks:** —

---

### 5.6–5.10 Plugin Testing Framework
**Points:** 15 | **Assignee:** Kimi Dev-3 + QA | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 5.6 | Plugin unit test helpers | 3 | Mock HTML loader, mock HTTP responses, mock browser contexts, assertion helpers for extracted data, fixture generators |
| 5.7 | Plugin integration tests | 3 | Test full plugin pipeline: URL matching → scraping → normalization → output, test error handling, test fallback selectors |
| 5.8 | Plugin validation suite | 3 | Automated validation: URL patterns compile and match, selectors are valid, config schema validates, no circular dependencies |
| 5.9 | Plugin performance tests | 3 | Benchmark plugin execution time, memory usage test, concurrent execution test, resource cleanup verification |
| 5.10 | Plugin regression tests | 3 | Record HTML fixtures for plugin targets, detect when target site changes, alert on selector breakage, auto-suggest fixes |

**Acceptance Criteria:**
- Unit test helpers reduce test code by 70%
- Integration tests cover all plugin paths
- Validation catches common plugin errors
- Regression tests detect breakage within 24 hours

**Depends On:** 5.2, 5.3, 5.4  
**Blocks:** —

---

## Phase 6 — Integration & Launch

**Phase Lead:** All Agents  
**Phase Goal:** Integrate all components, validate end-to-end, launch  
**Phase Points:** 55

---

### 6.1 Integration Testing — End to End
**Points:** 10 | **Assignee:** QA Lead | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 6.1.1 | HTTP scraper E2E | 2 | Test HTTP scraper against 50 live URLs across all platforms, validate output schema, measure success rate and latency |
| 6.1.2 | Browser scraper E2E | 2 | Test browser scraper against 30 JS-heavy pages, validate stealth detection pass rate, measure memory usage |
| 6.1.3 | Cross-platform validation | 2 | Run all platform scrapers against live targets, validate data completeness, cross-reference fields |
| 6.1.4 | Error scenario testing | 2 | Test error paths: 404, 403, timeout, network error, invalid URL, empty response — verify graceful handling |
| 6.1.5 | Load testing | 2 | 100 concurrent scrapes, sustained load for 1 hour, memory leak detection, resource cleanup verification |

**Acceptance Criteria:**
- E2E success rate > 95% across all platforms
- All error scenarios handled gracefully
- No memory leaks over 1-hour sustained load
- All output validates against schema

**Depends On:** 2.1–2.24, 4.1–4.15  
**Blocks:** 6.4

---

### 6.2 Documentation
**Points:** 10 | **Assignee:** All Dev | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 6.2.1 | API documentation | 2 | OpenAPI/Swagger spec for all endpoints, request/response examples, authentication guide, error code reference |
| 6.2.2 | Scraping guides | 2 | Per-platform scraping guides: Instagram, X/Twitter, TikTok, LinkedIn, Facebook, YouTube — with examples and limitations |
| 6.2.3 | Architecture docs | 2 | System architecture diagram, component interaction, data flow, deployment guide, configuration reference |
| 6.2.4 | Troubleshooting guide | 2 | Common errors and solutions, anti-bot mitigation guide, proxy configuration, debugging tips, FAQ |
| 6.2.5 | Changelog & versioning | 2 | Semantic versioning policy, changelog format, migration guides, deprecation policy |

**Acceptance Criteria:**
- API docs complete with examples
- All platforms have dedicated guide
- Architecture docs include diagrams
- Troubleshooting covers top 20 issues

**Depends On:** 1.1–1.12, 2.1–2.24, 4.1–4.15  
**Blocks:** 6.4

---

### 6.3 Performance Optimization
**Points:** 8 | **Assignee:** Kimi Dev-1 + DevOps | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 6.3.1 | Profiling | 2 | CPU profiling of hot paths, memory profiling for leaks, async bottleneck identification, database query optimization |
| 6.3.2 | Caching layer | 2 | Redis-based response cache, selector result cache, robots.txt cache, DNS resolution cache |
| 6.3.3 | Concurrency tuning | 2 | Optimal connection pool sizing, optimal worker count per CPU, async task batching, connection keep-alive tuning |
| 6.3.4 | Resource optimization | 2 | Browser context reuse, image loading suppression, minimal resource fetching, garbage collection tuning |

**Acceptance Criteria:**
- P95 latency < 5s for HTTP scrapes
- P95 latency < 15s for browser scrapes
- Memory usage stable over 24-hour run
- Cache hit rate > 30% for repeated URLs

**Depends On:** 6.1  
**Blocks:** 6.4

---

### 6.3b Operational Automation
**Points:** 8 | **Assignee:** Kimi Dev-1 + QA Lead | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 6.3b.1 | Persistent domain memory | 2 | Add `DomainMemoryRecord` schema, `DomainMemory` component, strategy/selector success tracking, and JSON fallback under `data_dir` |
| 6.3b.2 | Change detection & alerts | 2 | Add `HTMLBaselineRecord`/`ChangeAlertRecord` schema, `ChangeDetector` with structural fingerprint and selector degradation, `AuditLogger` for JSON/storage alerts |
| 6.3b.3 | Auto fixture/test generation | 2 | Add `FixtureGenerator` that writes `tests/fixtures/html/<platform>/`, `meta.yaml`, and `tests/unit/test_<platform>_adapter.py` from `PageSnapshot`s |
| 6.3b.4 | Pipeline & engine wiring | 1 | Inject `DomainMemory`, `ChangeDetector`, and `AuditLogger` into `PipelineController`/`PhoenixEngine`; skip learning when user overrides strategy |
| 6.3b.5 | Tests & documentation | 1 | Unit tests for all new components; update architecture/API/cli docs |

**Acceptance Criteria:**
- `DomainMemory` round-trips through SQLite and JSON fallback
- `ChangeDetector` emits alerts on DOM skeleton changes, selector degradation, and size anomalies
- `FixtureGenerator` produces compilable pytest files
- All quality gates green (≥85% coverage)

**Depends On:** 2.1–2.24, 4.1–4.15  
**Blocks:** 6.4

---

### 6.4 Production Deployment
**Points:** 10 | **Assignee:** Kimi DevOps | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 6.4.1 | Production environment | 2 | Production Docker Compose / K8s manifests, environment-specific configuration, SSL certificates, domain setup |
| 6.4.2 | Monitoring setup | 2 | Production monitoring dashboard, alert channels (email/Slack), on-call rotation, incident response runbook |
| 6.4.3 | Backup verification | 2 | Automated backup testing, disaster recovery drill, data integrity verification, RTO/RPO validation |
| 6.4.4 | Security hardening | 2 | Production security review, penetration testing, dependency vulnerability scan, secrets audit |
| 6.4.5 | Launch checklist | 2 | Pre-launch verification: all tests pass, docs complete, monitoring active, backups verified, rollback plan ready |

**Acceptance Criteria:**
- Production environment deployed and accessible
- Monitoring active with all alerts configured
- Backup recovery tested and documented
- Security scan passes with no critical findings

**Depends On:** 4.9, 4.10, 6.1, 6.2, 6.3  
**Blocks:** —

---

### 6.5–6.11 Post-Launch Operations
**Points:** 17 | **Assignee:** All | **Priority:** P1

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 6.5 | HTML fixture maintenance | 3 | Monthly refresh of recorded HTML fixtures, add fixtures for new page layouts, archive outdated fixtures |
| 6.6 | Selector health monitoring | 3 | Daily automated selector validation, health score dashboard, auto-alert on degradation, monthly selector review |
| 6.7 | Anti-bot adaptation | 2 | Monitor anti-bot landscape, update stealth techniques, rotate proxy strategies, browser patch management |
| 6.8 | Performance monitoring | 2 | Continuous performance tracking, latency trend analysis, capacity planning, scaling triggers |
| 6.9 | User feedback integration | 2 | Feedback collection mechanism, issue triage process, priority scoring, feedback-driven roadmap |
| 6.10 | Monthly reviews | 3 | Team retro on scraping challenges, selector breakage analysis, success rate trends, technical debt review |
| 6.11 | Quarterly planning | 2 | New platform evaluation, feature prioritization, technical debt paydown, infrastructure scaling |

**Acceptance Criteria:**
- Fixtures refreshed within 7 days of layout changes
- Selector health monitored daily
- Anti-bot techniques updated monthly
- User feedback reviewed weekly

**Depends On:** 6.4  
**Blocks:** —

---

## Phase 7 — PhoenixArchitect

**Phase Lead:** Kimi Dev-1 (Alpha)  
**Phase Goal:** Build an autonomous AI agent that discovers target sites, explores their structure, and generates validated Phoenix adapter plugins from natural-language goals  
**Phase Points:** 40

---

### 7.1 Planner Module
**Points:** 5 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 7.1.1 | Goal parsing | 2 | Parse natural-language scraping goal into structured objective, site type hint, and expected fields |
| 7.1.2 | JSON plan schema | 2 | Define plan steps (`search`, `explore`, `inspect`, `code`, `critique`, `register`) with inputs/outputs and approval gates |
| 7.1.3 | State tracking | 1 | Persist plan state, handle retries, expose status to CLI |

**Acceptance Criteria:**
- Any clear goal produces a valid multi-step plan
- Plan state is serializable and resumable
- Each step declares required inputs and expected outputs

**Depends On:** 3.1–3.6, 5.1–5.3  
**Blocks:** 7.2–7.6

---

### 7.2 Researcher — Search-Driven Discovery
**Points:** 7 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 7.2.1 | Query builder ✅ | 2 | Convert goal into effective search queries (site:, inurl:, intitle:) |
| 7.2.2 | DuckDuckGo backend ✅ | 3 | Search DuckDuckGo with polite rate limits, parse result HTML, return URL/title/snippet |
| 7.2.3 | SerpAPI fallback ✅ | 2 | Implement SerpAPI backend with API-key config and result caching |

**Acceptance Criteria:**
- ≥80% of top-10 results are relevant to goal
- Results cached and deduplicated
- Fallback to SerpAPI on DuckDuckGo failure

**Depends On:** 7.1  
**Blocks:** 7.3

---

### 7.3 Explorer — Browser Scroll & Pagination
**Points:** 8 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 7.3.1 | Pagination detection | 2 | Classify page as infinite-scroll, numbered, "Next" link, or single-page |
| 7.3.2 | Scroll automation | 2 | Smooth scroll with waits, detect new content load, stop on staleness or `max-pages` |
| 7.3.3 | Click pagination | 2 | Click numbered pages / Next links, capture snapshot after each load |
| 7.3.4 | Snapshot archiver | 2 | Save raw HTML + metadata (URL, page #, scroll depth) for Inspector |

**Acceptance Criteria:**
- Handles all three pagination patterns
- Never exceeds `max-pages` per site
- Snapshots stored with deterministic IDs

**Depends On:** 1.6, 4.3, 7.2  
**Blocks:** 7.4

---

### 7.4 Inspector — HTML Analysis with Ollama
**Points:** 7 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 7.4.1 | Site classification | 2 | Use local LLM to classify site type and list structure |
| 7.4.2 | Field identification | 3 | Identify fields (title, price, location, etc.) and propose CSS/XPath selectors |
| 7.4.3 | Selector validation | 2 | Validate proposed selectors against all snapshots and compute coverage |

**Acceptance Criteria:**
- ≥85% of expected fields identified on test snapshots
- Proposed selectors match at least one snapshot
- Inspector output consumed by Coder without manual editing

**Depends On:** 3.1, 7.3  
**Blocks:** 7.5

---

### 7.5 Coder — Adapter Auto-Generation
**Points:** 8 | **Assignee:** Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 7.5.1 | Template engine | 2 | Jinja/template-based adapter module generation with URL patterns, SelectorSet, parse method |
| 7.5.2 | Normalizer mapping | 2 | Generate content normalizer mapping from Inspector fields to UnifiedOutput |
| 7.5.3 | Code quality gate | 2 | Auto-format with black, lint with ruff, type-check with mypy before writing to disk |
| 7.5.4 | Versioning & metadata | 2 | Tag generated adapter with goal hash, source URLs, and generated timestamp |

**Acceptance Criteria:**
- Generated modules import without errors
- All generated code passes ruff/black/mypy
- Adapter implements `ScraperPlugin` interface

**Depends On:** 5.1, 7.4  
**Blocks:** 7.6

---

### 7.6 Critic — Validation & Registration
**Points:** 5 | **Assignee:** QA Lead + Kimi Dev-1 | **Priority:** P0

| ID | Subtask | Points | Description |
|----|---------|--------|-------------|
| 7.6.1 | Coverage metric ✅ | 2 | Run generated adapter against all snapshots, compute per-field and overall coverage |
| 7.6.2 | Retry loop ✅ | 2 | If coverage < threshold, send diagnostic context back to Coder for revision (max 3 iterations) |
| 7.6.3 | Registration ✅ | 1 | Register passing adapter in plugin registry with priority over generic fallback |

**Acceptance Criteria:**
- ≥70% of generated adapters pass validation after ≤3 iterations
- Registered adapter routes matching URLs correctly
- Failed generations produce actionable diagnostics

**Depends On:** 7.5  
**Blocks:** —

---

## Dependency Graph

```
PHASE 1: CORE ENGINE (Foundational — all other phases depend on this)
═══════════════════════════════════════════════════════════════════
1.1 HTTP Scraper ──────┬──► 1.7 Strategy Selector ────► 2.x All Platform Scrapers
1.2 HTML Parsing ──────┤                            ▲
1.3 CSS Selector ──────┤                            │
1.4 XPath Engine ──────┼──► 1.8 Output Normalizer ─┘
1.5 Regex Helpers ─────┤      ▲
1.6 Browser Scraper ───┘      │
1.9 Error/Retry ──────────────┤
1.10 Audit Logging ───────────┤
1.11 Pipeline Controller ─────┘
1.12 Regex Library ───────────► 2.12 YouTube, 2.x Social

                              PHASE 2: PLATFORM SCRAPERS
═══════════════════════════════════════════════════════════════════════════════
                              2.1 Instagram Posts ──► 2.2 Reels, 2.3 Profiles
                              2.4 X/Twitter Tweets ──► 2.5 Profiles
                              2.6 TikTok Videos ──► 2.7 Profiles
                              2.8 LinkedIn Posts ──► 2.9 Profiles
                              2.10 Facebook Posts ──► 2.11 Pages
                              2.12 YouTube Videos ──► 2.13 Transcripts, 2.14 Channels, 2.15 Comments
                              2.16 Generic Web ──► 2.17 Metadata
                              2.18–2.24 Pagination (shared by all)

                                                          PHASE 3: INTELLIGENCE
═════════════════════════════════════════════════════════════════════════════════════
                                                          3.1 Structure Analysis ──► 3.2 Fallback Chains
                                                          3.3 Content Classifier ──┤       │
                                                          3.4 Anti-Bot Detection ──┤       │
                                                                                  ▼       ▼
                                                          3.5 Auto Repair ◄──────────────┘
                                                          3.6 Adaptive Rate Limiting

PHASE 4: INFRASTRUCTURE
═══════════════════════════════════════════════════════════════════════════════════════════
4.1 Session Manager ──┬──► 4.3 Browser Pool ──► All browser scrapers
4.2 Proxy Mgmt ───────┤       ▲
4.4 Stealth Config ───┘       │
4.5 Rate Controller ──────────┤
4.6 HTML Archive ─────────────┤
4.7 Output Storage ───────────┤
4.8 Monitoring ───────────────┘
4.9 Docker ──► 4.10 CI/CD ──► 6.4 Deployment
4.11–4.15 Security

PHASE 5: PLUGIN SYSTEM
═════════════════════════════════════════════════════════════════════════
5.1 Interface ──► 5.2 Loader ──► 5.3 SDK ──► 5.4 Examples ──► 5.5 Marketplace
                                      │
                                      └──► 5.6–5.10 Testing Framework

PHASE 6: INTEGRATION & LAUNCH
═════════════════════════════════════════════════════════════════════════
All Phases 1–5 ──► 6.1 E2E Testing ──► 6.3 Performance ──► 6.4 Production
                   6.2 Documentation ──►           ▲            ▲
                                                   └────────────┘
                                            6.5–6.11 Post-Launch Ops

PHASE 7: PHOENIXARCHITECT
═════════════════════════════════════════════════════════════════════════
7.1 Planner ──► 7.2 Researcher ──► 7.3 Explorer ──► 7.4 Inspector
                                                       │
                                                       ▼
                                              7.5 Coder ──► 7.6 Critic
                                                       │
                                                       ▼
                                              Plugin Registry (5.2)
```

### Critical Path

```
1.1 HTTP Scraper → 1.2 HTML Parsing → 1.3 CSS Selector → 1.6 Browser Scraper
→ 1.7 Strategy Selector → 1.8 Output Normalizer → 1.11 Pipeline Controller
→ 2.1 Instagram / 2.4 X/Twitter / 2.12 YouTube / 2.16 Generic
→ 4.1 Session Manager / 4.2 Proxy / 4.3 Browser Pool / 4.5 Rate Controller
→ 6.1 E2E Testing → 6.4 Production Deployment
```

---

## Resource Loading

### Story Points by Agent

| Agent | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Phase 7 | Total |
|-------|:-------:|:-------:|:-------:|:-------:|:-------:|:-------:|:-------:|:-----:|
| **Dev-1** | 135 | — | 75 | — | — | 8 | 35 | **253** |
| **Dev-2** | — | 85 | — | — | — | — | — | **85** |
| **Dev-3** | — | 85 | — | — | 65 | — | — | **150** |
| **DevOps** | — | — | — | 100 | — | 20 | — | **120** |
| **QA** | — | — | — | — | — | 27 | 5 | **32** |

### Weekly Burndown Plan (8-Week Timeline)

| Week | Dev-1 | Dev-2 | Dev-3 | DevOps | QA | Total |
|:----:|:-----:|:-----:|:-----:|:------:|:--:|:-----:|
| 1 | 35 | 25 | 25 | 20 | — | 105 |
| 2 | 35 | 25 | 25 | 20 | — | 105 |
| 3 | 35 | 25 | 25 | 20 | — | 105 |
| 4 | 35 | 25 | 25 | 20 | 10 | 115 |
| 5 | 30 | 20 | 20 | 10 | 10 | 90 |
| 6 | 25 | 15 | 15 | 10 | 7 | 72 |
| 7 | 15 | 10 | 15 | — | — | 40 |
| 8 | 8 | — | — | — | — | 8 |

### Phase Timeline

```
Week:  1       2       3       4       5       6       7       8
       ├───────┤
       │  Phase 1: Core Engine (135 pts)  │
               ├───────────────────────────────┤
               │  Phase 2: Platform Scrapers (170 pts)  │
                       ├───────────────────────┤
                       │  Phase 3: Intelligence (75 pts)  │
       ├───────────────────────────────────────┤
       │  Phase 4: Infrastructure (100 pts)     │
                               ├───────────────┤
                               │  Phase 5: Plugins (65 pts)  │
                                       ├───────┤
                                       │ Phase 6: Integration (55 pts)│
```

---

## Risk Register

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|:-----------:|:------:|------------|-------|
| R1 | Target site HTML structure changes breaking selectors | High | High | Smart fallback chains (3.2), auto-repair (3.5), selector regression tests (QA) | Dev-1 |
| R2 | Anti-bot measures block scraping | High | High | Stealth configuration (4.4), proxy rotation (4.2), adaptive rate limiting (3.6), browser automation | DevOps |
| R3 | Browser automation performance issues | Medium | High | Browser pool management (4.3), HTTP-first strategy (1.7), resource optimization (6.3) | DevOps |
| R4 | Legal/ethical compliance issues | Medium | High | robots.txt compliance (4.5), public-only scraping, rate limiting, ethical scraping policy | DevOps |
| R5 | Proxy failure/depletion | Medium | Medium | Health checking (4.2), failover handling, multiple proxy providers | DevOps |
| R6 | Memory leaks in long-running scraper | Medium | High | Browser context lifecycle (4.3), memory monitoring (4.8), periodic restarts | Dev-1 |
| R7 | Plugin API instability | Low | Medium | Semantic versioning, deprecation policy, comprehensive tests (5.6–5.10) | Dev-3 |
| R8 | Target site requires authentication | Medium | Medium | Cookie/session management (4.1), graceful degradation, public-only scope | Dev-2 |
| R9 | Concurrent scraping causes IP bans | Medium | High | Rate limiting (4.5), proxy rotation, per-domain concurrency limits | DevOps |
| R10 | HTML parsing performance on large pages | Low | Medium | lxml for speed, streaming parser for huge pages, size limits | Dev-1 |
| R11 | Autonomous adapter generation produces brittle selectors | Medium | High | Critic validation loop (7.6), multi-snapshot testing, human approval gate | Dev-1 |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | System | Initial WBS with generic tasks |
| 2.0 | 2025-01-21 | System | Complete rewrite for pure scraping focus — 78 tasks, 520 points, 5 phases covering HTTP/browser scraping, social platform HTML scrapers, intelligence layer, infrastructure, and plugin system |
