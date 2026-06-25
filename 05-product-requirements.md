# Phoenix Engine — Product Requirements Document (PRD)

## Universal Web Scraping Platform v1.0 — Ollama Local AI Edition

**Status**: Draft | **Version**: 2.0 | **Last Updated**: 2025-01-20

---

## 1. Document Purpose

This Product Requirements Document (PRD) defines the complete feature set, user experience, non-functional requirements, and acceptance criteria for **Phoenix Engine** — a universal, pure web scraping platform that extracts structured data from any website or social media platform entirely through web scraping techniques. Phoenix Engine never uses official platform APIs. All data collection is performed via direct HTTP requests with HTML parsing or headless browser automation, extracting data through CSS selectors, XPath expressions, and regex patterns.

**AI Architecture**: Phoenix Engine uses **Ollama** with locally-hosted models (`dolphincoder:7b` default and `qwen2.5:7b` fallback/alternative) for all AI-powered features. All inference runs locally on the user's machine — no external AI APIs, no API keys, no costs, no rate limits, full privacy.

---

## 2. Product Overview

### 2.1 Vision Statement

> A single, unified tool that can scrape structured data from any website on the internet — from social media platforms to news sites to e-commerce stores — using only web scraping techniques, delivering clean, consistent output regardless of source complexity, with privacy-preserving local AI augmentation.

### 2.2 Core Scraping Flow

```
Receive URL → Classify Domain/Pattern → Select Scraping Strategy
    → Fetch Raw HTML (HTTP or Browser) → Parse with Selectors/XPath
    → Extract Structured Data → Deliver Unified JSON Output
```

### 2.3 Target Users

| User Persona | Role | Primary Need |
|-------------|------|-------------|
| Data Analyst | Business intelligence | Extract social media data for trend analysis |
| Researcher | Academic/Policy | Scrape public posts, comments, articles for research |
| Developer | Software engineer | Integrate scraping into applications via library API |
| Journalist | Media professional | Collect public social media content for stories |
| Marketer | Brand monitoring | Track public brand mentions and competitor activity |

### 2.4 Fundamental Constraint

**Phoenix Engine NEVER uses official social media APIs.** All data collection is performed exclusively through:
- Direct HTTP requests with HTML response parsing (BeautifulSoup/lxml/cssselect)
- Headless browser automation (Playwright) for JavaScript-rendered pages
- CSS selectors, XPath expressions, and regex for data extraction from raw HTML
- Ethical rate limiting with transparent user-agent strings

### 2.5 AI Architecture — Ollama Local Inference

```
┌─────────────────────────────────────────────────────┐
│                  Phoenix Engine                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Selectors  │  │   Ollama    │  │  Heuristics │ │
│  │   (F13)     │→ │  AI Engine  │→ │  (F9/ F14)  │ │
│  └─────────────┘  └──────┬──────┘  └─────────────┘ │
│                          │                          │
│              ┌───────────┴───────────┐              │
│              │   Ollama Service      │              │
│              │   localhost:11434     │              │
│              └───────────┬───────────┘              │
│                          │                          │
│         ┌────────────────┼────────────────┐         │
│         ▼                ▼                ▼         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ dolphin    │  │ qwen2.5    │  │  CPU/GPU   │    │
│  │ coder:7b   │  │ :7b        │  │ Auto-Select│    │
│  │ (default)  │  │ (fallback) │  │  (F25/F26) │    │
│  └────────────┘  └────────────┘  └────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Key Principles**:
- All AI inference runs locally via Ollama — zero data leaves the user's machine
- No API keys, no usage costs, no rate limits, no internet dependency for AI
- Hardware auto-detection selects optimal model (GPU → 7b (14b optional on high-end), CPU → 7b)
- Graceful degradation: 7b → CPU 7b → skip AI → heuristic extraction

---

## 3. Feature Specifications

### F1 — Universal URL Processing

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F1 |
| **Name** | Universal URL Processing |
| **Priority** | P0 — Critical |
| **Story Points** | 8 |
| **Description** | Accept any valid URL, classify it by domain and URL pattern, and automatically route it to the appropriate scraper module. The system maintains a registry of URL patterns mapped to scraper implementations, with a fallback to the generic web scraper for unrecognized domains. |
| **Dependencies** | None |

#### User Stories

**US-F1-01**: As a data analyst, I want to paste any URL into Phoenix Engine so that it automatically recognizes the site type and routes to the correct scraper without manual configuration.

**US-F1-02**: As a developer, I want the system to validate URLs before attempting to scrape so that invalid or malformed URLs fail fast with a clear error message.

**US-F1-03**: As a researcher, I want URLs from unknown or unsupported domains to fall back to a generic scraper so that I can still extract basic structured data from any public webpage.

**US-F1-04**: As a developer, I want to register custom URL patterns for internal or niche websites so that Phoenix Engine can route them to custom scraper plugins.

#### Acceptance Criteria

**AC-F1-01**: Given a valid Instagram post URL, when submitted to Phoenix Engine, then the system shall classify it as "instagram-post" and route to the Instagram scraper within 100ms.

**AC-F1-02**: Given an invalid URL (malformed protocol, missing domain, etc.), when submitted, then the system shall reject it immediately with an error message: "Invalid URL format" and HTTP 400 status.

**AC-F1-03**: Given a URL from a domain not in the scraper registry (e.g., `https://obscure-blog.example.com/article`), when submitted, then the system shall route it to the generic web scraper (F9) with a classification of "generic-webpage".

**AC-F1-04**: Given a URL pattern registered via the plugin system (F16), when a matching URL is submitted, then the system shall route it to the registered plugin scraper.

**AC-F1-05**: Given any URL with query parameters and fragments, when classified, then the system shall strip irrelevant tracking parameters (e.g., UTM tags) while preserving functional parameters (e.g., pagination, post IDs).

---

### F2 — Scraping Strategy Selection

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F2 |
| **Name** | Scraping Strategy Selection |
| **Priority** | P0 — Critical |
| **Story Points** | 13 |
| **Description** | Automatically detect the optimal scraping approach for each target URL without requiring user configuration. The system selects between fast HTTP request + HTML parsing (for static pages) and headless browser automation (for JavaScript-rendered content) based on domain knowledge, content-type headers, and lightweight probing. |
| **Dependencies** | F1 |

#### User Stories

**US-F2-01**: As a data analyst, I want Phoenix Engine to automatically choose the fastest scraping method that works for a given page so that I don't need to understand HTML vs JavaScript rendering differences.

**US-F2-02**: As a developer, I want to override the automatic strategy selection for specific domains so that I can force HTTP or browser mode based on my knowledge of the target site.

**US-F2-03**: As a researcher, I want the system to retry with browser automation if an HTTP scrape fails to extract content so that transient JavaScript dependencies don't cause data loss.

**US-F2-04**: As a data analyst, I want the system to benchmark and remember which strategy works best for each domain so that subsequent scrapes of the same site are optimally fast.

#### Acceptance Criteria

**AC-F2-01**: Given a static HTML blog page, when scraped, then the system shall use HTTP request mode and complete within 5 seconds.

**AC-F2-02**: Given an Instagram page requiring JavaScript rendering, when scraped, then the system shall automatically switch to browser mode and complete within 15 seconds.

**AC-F2-03**: Given a domain with no strategy history, when first scraped, then the system shall perform a lightweight HTTP probe (fetch headers only) to check for JavaScript indicators before selecting the full scraping strategy.

**AC-F2-04**: Given a failed HTTP scrape (no content extracted by primary selectors), when retries are enabled, then the system shall automatically retry with browser automation and log the strategy switch.

**AC-F2-05**: Given a user configuration override (`--force-browser` or `--force-http`), when specified, then the system shall use the forced strategy regardless of automatic detection.

---

### F3 — Instagram Scraper

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F3 |
| **Name** | Instagram Scraper |
| **Priority** | P0 — Critical |
| **Story Points** | 21 |
| **Description** | Scrape public Instagram content — posts (images, captions, likes, timestamps), Reels, public profiles (bio, follower counts, post grids), and comments — entirely through HTML parsing and browser automation. Handle Instagram's pagination via scroll/load-more mechanisms. Extract all data using CSS selectors targeting Instagram's HTML structure. No Instagram API is used. |
| **Dependencies** | F1, F2 |

#### User Stories

**US-F3-01**: As a marketer, I want to scrape a public Instagram post's caption, images, like count, and timestamp so that I can analyze brand engagement without using the Instagram API.

**US-F3-02**: As a researcher, I want to scrape all comments on a public Instagram post so that I can perform sentiment analysis on audience reactions.

**US-F3-03**: As a data analyst, I want to scrape a public Instagram profile's bio, follower count, following count, and recent posts grid so that I can track influencer metrics over time.

**US-F3-04**: As a journalist, I want to scrape Instagram Reels metadata (views, likes, caption, audio) from a public Reel URL so that I can report on trending content.

**US-F3-05**: As a developer, I want to handle Instagram's infinite scroll pagination so that I can scrape all posts from a profile or all comments on a post, not just the first page.

**US-F3-06**: As a data analyst, I want the scraper to gracefully handle Instagram's HTML structure changes by trying fallback selector sets so that temporary breakages don't require immediate code deployment.

#### Acceptance Criteria

**AC-F3-01**: Given a public Instagram post URL, when scraped, then the system shall return: post ID, caption text, image URLs (all carousel images), like count, comment count, timestamp, and author username — all extracted from HTML via CSS selectors.

**AC-F3-02**: Given a public Instagram post with comments enabled, when comment scraping is requested, then the system shall extract all visible comments (username, text, timestamp, like count) and handle "load more comments" pagination via scroll simulation.

**AC-F3-03**: Given a public Instagram profile URL, when scraped, then the system shall return: username, display name, bio text, follower count, following count, post count, and the 12 most recent post thumbnails with their URLs.

**AC-F3-04**: Given a public Instagram Reel URL, when scraped, then the system shall return: Reel ID, caption, view count, like count, comment count, timestamp, video URL, and audio attribution — all parsed from the HTML structure.

**AC-F3-05**: Given an Instagram profile with more than 12 posts, when "load all" is requested, then the system shall simulate scroll events to trigger pagination and continue scraping until no new posts load or a configurable maximum is reached.

**AC-F3-06**: Given Instagram's HTML structure has changed, when primary CSS selectors fail to match, then the system shall attempt up to 3 fallback selector sets (F13) before failing and logging the structure change.

---

### F4 — X/Twitter Scraper

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F4 |
| **Name** | X/Twitter Scraper |
| **Priority** | P0 — Critical |
| **Story Points** | 21 |
| **Description** | Scrape public X/Twitter content — tweets, public profiles, threads, replies, retweets, likes — entirely through HTML parsing and browser automation. Handle X's infinite scroll timeline and dynamic content loading. Extract tweet text, timestamps, engagement metrics, media attachments, and author information using CSS selectors targeting X's HTML structure. No X API is used. |
| **Dependencies** | F1, F2 |

#### User Stories

**US-F4-01**: As a journalist, I want to scrape a public tweet's text, timestamp, like count, retweet count, and reply count so that I can cite it in reporting without API access.

**US-F4-02**: As a researcher, I want to scrape a public Twitter/X profile's bio, follower count, tweet count, and recent tweets so that I can study communication patterns.

**US-F4-03**: As a data analyst, I want to scrape an entire tweet thread (original tweet + all replies in the conversation) so that I can analyze the full discourse.

**US-F4-04**: As a marketer, I want to scrape all tweets from a public profile timeline with pagination so that I can perform historical brand mention analysis.

**US-F4-05**: As a developer, I want to extract media attachments (images, videos) from tweets so that I can build media galleries from scraped content.

#### Acceptance Criteria

**AC-F4-01**: Given a public X/Tweet URL, when scraped, then the system shall return: tweet ID, text content, author username, author display name, timestamp, like count, retweet count, reply count, quote count, and media attachment URLs — all extracted from HTML via CSS selectors.

**AC-F4-02**: Given a public X profile URL, when scraped, then the system shall return: username, display name, bio, location, website URL, join date, follower count, following count, tweet count, and the 20 most recent tweets with full metadata.

**AC-F4-03**: Given a tweet that is part of a thread, when thread scraping is requested, then the system shall extract the original tweet and all reply tweets in the conversation, maintaining parent-child relationships in the output.

**AC-F4-04**: Given a profile timeline with more than 20 tweets, when pagination is enabled, then the system shall simulate scroll events to load older tweets and continue scraping until no new tweets load or a configurable maximum is reached.

**AC-F4-05**: Given a tweet with embedded images, when scraped, then the system shall extract all image URLs at maximum available resolution from the HTML `src` attributes.

**AC-F4-06**: Given X's HTML structure has changed, when primary selectors fail, then the system shall attempt fallback selector sets (F13) and log the failure for maintenance review.

---

### F5 — TikTok Scraper

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F5 |
| **Name** | TikTok Scraper |
| **Priority** | P0 — Critical |
| **Story Points** | 21 |
| **Description** | Scrape public TikTok content — videos, profiles, comments — entirely through HTML parsing and browser automation. Handle TikTok's heavy JavaScript rendering and lazy loading mechanisms. Extract video metadata, engagement metrics, captions, hashtags, audio information, and comment threads using CSS selectors. No TikTok API is used. |
| **Dependencies** | F1, F2 |

#### User Stories

**US-F5-01**: As a marketer, I want to scrape a TikTok video's caption, hashtags, view count, like count, and share count so that I can measure campaign reach without API access.

**US-F5-02**: As a researcher, I want to scrape all comments on a TikTok video so that I can analyze audience sentiment and engagement patterns.

**US-F5-03**: As a data analyst, I want to scrape a TikTok profile's bio, follower count, like count, and recent videos so that I can track creator growth metrics.

**US-F5-04**: As a developer, I want to extract TikTok video download URLs (where publicly accessible) and audio attribution so that I can catalog content metadata.

**US-F5-05**: As a journalist, I want to handle TikTok's lazy loading so that I can scrape all videos from a profile or all comments from a video, not just the initially visible content.

#### Acceptance Criteria

**AC-F5-01**: Given a public TikTok video URL, when scraped, then the system shall return: video ID, caption text, hashtags (as array), view count, like count, comment count, share count, author username, timestamp, video URL, and audio title — all parsed from HTML.

**AC-F5-02**: Given a TikTok video with comments enabled, when comment scraping is requested, then the system shall extract all visible comments (username, text, timestamp, like count, reply count) and handle "load more" pagination.

**AC-F5-03**: Given a public TikTok profile URL, when scraped, then the system shall return: username, display name, bio, follower count, following count, total like count, and recent video list with metadata.

**AC-F5-04**: Given TikTok's JavaScript-heavy page structure, when scraped, then the system shall use browser automation mode and wait for all lazy-loaded content to render before extraction.

**AC-F5-05**: Given a profile with more videos than initially loaded, when pagination is enabled, then the system shall trigger scroll events to load additional videos and continue extraction.

---

### F6 — LinkedIn Scraper

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F6 |
| **Name** | LinkedIn Scraper |
| **Priority** | P0 — Critical |
| **Story Points** | 13 |
| **Description** | Scrape publicly visible LinkedIn content — public posts, public profile summaries, and public company pages — entirely through HTML parsing and browser automation. Only content that is publicly accessible without authentication is targeted. Extract post text, engagement metrics, author information, profile summaries, and company page details using CSS selectors. No LinkedIn API is used. |
| **Dependencies** | F1, F2 |

#### User Stories

**US-F6-01**: As a researcher, I want to scrape a public LinkedIn post's text, like count, and comment count so that I can analyze professional discourse on public topics.

**US-F6-02**: As a data analyst, I want to scrape a public LinkedIn profile's headline, summary, current position, and company so that I can build professional network insights (public data only).

**US-F6-03**: As a marketer, I want to scrape a public LinkedIn company page's description, follower count, and recent posts so that I can benchmark competitor presence.

**US-F6-04**: As a developer, I want to respect LinkedIn's session requirements so that the scraper maintains appropriate session state for accessing public content.

#### Acceptance Criteria

**AC-F6-01**: Given a public LinkedIn post URL (no login required), when scraped, then the system shall return: post ID, text content, author name, author headline, timestamp, like count, and comment count — all from HTML.

**AC-F6-02**: Given a public LinkedIn profile URL, when scraped, then the system shall return: name, headline, summary text, current position, company, location, and connection count (if publicly displayed).

**AC-F6-03**: Given a public LinkedIn company page URL, when scraped, then the system shall return: company name, description, industry, company size, follower count, and recent public posts.

**AC-F6-04**: Given a LinkedIn page that requires authentication to view, when scraped without valid session cookies, then the system shall return a clear error: "Authentication required — this content is not publicly accessible" and skip the URL.

---

### F7 — Facebook Scraper

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F7 |
| **Name** | Facebook Scraper |
| **Priority** | P1 — High |
| **Story Points** | 13 |
| **Description** | Scrape publicly visible Facebook content — public posts from public pages — entirely through HTML parsing and browser automation. Target only content that is explicitly public (no login required). Facebook group scraping is out of scope (violates Meta ToS). Extract post text, reactions count, comment counts, timestamps, and shared links using CSS selectors. No Facebook API is used. |
| **Dependencies** | F1, F2 |

#### User Stories

**US-F7-01**: As a marketer, I want to scrape public posts from a public Facebook page so that I can monitor brand mentions and competitor activity.

**US-F7-02**: As a researcher, I want to scrape post text, reaction counts, and share counts from public Facebook posts so that I can measure public engagement on topics.

**US-F7-03**: As a journalist, I want to scrape public posts and their visible comments from public pages so that I can understand public discourse on news stories.

#### Acceptance Criteria

**AC-F7-01**: Given a public Facebook page post URL, when scraped, then the system shall return: post ID, text content, timestamp, reaction count, comment count, share count, and page name — all from HTML.

**AC-F7-02**: Given a public Facebook page's posts feed, when scraped with pagination, then the system shall extract recent public posts and handle scroll-based pagination to load older posts.

**AC-F7-03**: Given a Facebook post that requires login to view, when scraped, then the system shall return: "Authentication required — this content is not publicly accessible" and skip the URL.

**AC-F7-04**: Given a Facebook post with varied reaction types, when scraped, then the system shall extract the total reaction count and individual reaction breakdowns (like, love, wow, etc.) if visible in the HTML.

---

### F8 — YouTube Scraper

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F8 |
| **Name** | YouTube Scraper |
| **Priority** | P1 — High |
| **Story Points** | 13 |
| **Description** | Scrape public YouTube content — videos, channels, comments — entirely through HTML parsing. Leverage YouTube's relatively static initial HTML load for basic metadata. Extract video titles, descriptions, view counts, like/dislike indicators, channel info, upload dates, tags, and comment threads using CSS selectors. Include transcript extraction capability where available. No YouTube API is used. |
| **Dependencies** | F1, F2 |

#### User Stories

**US-F8-01**: As a researcher, I want to scrape a YouTube video's title, description, view count, upload date, and channel name so that I can catalog video content for analysis.

**US-F8-02**: As a data analyst, I want to scrape all comments on a YouTube video so that I can perform sentiment analysis on viewer reactions.

**US-F8-03**: As a journalist, I want to scrape a YouTube channel's public videos list with metadata so that I can track content output from news channels.

**US-F8-04**: As a developer, I want to extract auto-generated or community transcripts from YouTube videos where available so that I can perform text analysis on video content.

#### Acceptance Criteria

**AC-F8-01**: Given a YouTube video URL, when scraped, then the system shall return: video ID, title, description, view count, like count, upload date, channel name, channel URL, tags (as array), and category — all from HTML parsing.

**AC-F8-02**: Given a YouTube video with comments enabled, when comment scraping is requested, then the system shall extract all top-level comments (author, text, timestamp, like count) and handle "show more replies" pagination for nested replies.

**AC-F8-03**: Given a YouTube channel URL, when scraped, then the system shall return: channel name, description, subscriber count, video count, and recent video list with basic metadata.

**AC-F8-04**: Given a YouTube video with transcript available, when transcript extraction is requested, then the system shall parse the transcript panel HTML and return timestamped transcript segments (time, text).

---

### F9 — Generic Web Scraper

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F9 |
| **Name** | Generic Web Scraper |
| **Priority** | P0 — Critical |
| **Story Points** | 13 |
| **Description** | A universal article/blog/e-commerce scraper that extracts standard structured data from any HTML page — title, author, publication date, main content body, images, and metadata. Uses heuristics and common HTML patterns (`<article>`, `<main>`, schema.org markup, Open Graph tags) to intelligently extract content without site-specific configuration. |
| **Dependencies** | F1 |

#### User Stories

**US-F9-01**: As a researcher, I want to paste any news article URL and get clean extracted text so that I don't need to write custom scrapers for every news site.

**US-F9-02**: As a data analyst, I want the generic scraper to detect and extract article metadata (author, date, site name) automatically so that I can catalog scraped articles.

**US-F9-03**: As a developer, I want the generic scraper to handle schema.org JSON-LD structured data when present so that extraction is more reliable on standards-compliant sites.

**US-F9-04**: As a journalist, I want the generic scraper to extract all images from an article with their captions so that I can reference visual content.

**US-F9-05**: As a researcher, I want the generic scraper to remove navigation, ads, and footer content so that I get clean article text only.

#### Acceptance Criteria

**AC-F9-01**: Given any valid article/blog URL, when scraped with the generic scraper, then the system shall return: title, author (if detectable), publication date (if detectable), main content text (clean, no navigation/ads), site name, language, and all content image URLs.

**AC-F9-02**: Given a page with schema.org Article JSON-LD markup, when scraped, then the system shall prefer the structured data for title, author, date, and description extraction over HTML heuristic detection.

**AC-F9-03**: Given a page with Open Graph meta tags, when scraped, then the system shall extract og:title, og:description, og:image, and og:site_name as fallback metadata sources.

**AC-F9-04**: Given a page with no semantic markup, when scraped, then the system shall use content density heuristics to identify the main article body and extract text from the largest content block.

**AC-F9-05**: Given an e-commerce product page, when scraped, then the system shall attempt to extract: product name, price, description, and main product image using common e-commerce HTML patterns.

---

### F10 — Unified Output Format

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F10 |
| **Name** | Unified Output Format |
| **Priority** | P0 — Critical |
| **Story Points** | 8 |
| **Description** | Standardize all scraped data across all sources into a consistent JSON schema. Regardless of whether data came from Instagram, X, TikTok, LinkedIn, YouTube, Facebook, or a generic webpage, the output uses the same field naming conventions, data types, timestamp formats, and envelope structure. |
| **Dependencies** | None (all scrapers depend on this) |

#### User Stories

**US-F10-01**: As a developer, I want all scrapers to return data in the same JSON structure so that I can write one parser for all Phoenix Engine output.

**US-F10-02**: As a data analyst, I want consistent timestamp formatting (ISO 8601) across all scraped sources so that I can compare temporal data without conversion.

**US-F10-03**: As a developer, I want the output to include scrape metadata (URL, timestamp, scraper version, strategy used) alongside the extracted data so that I can audit and debug scrapes.

**US-F10-04**: As a researcher, I want URLs in output to be normalized (absolute, tracking params stripped) so that I can reliably compare and deduplicate content.

#### Acceptance Criteria

**AC-F10-01**: Given any scrape result from any scraper, when output, then the JSON envelope shall contain: `source_url`, `scraped_at` (ISO 8601), `scraper_version`, `scraper_name`, `strategy` (http|browser), `status` (success|partial|error), and `data` object.

**AC-F10-02**: Given a timestamp extracted from any source, when output, then it shall be converted to ISO 8601 UTC format (e.g., `2025-01-15T14:30:00Z`).

**AC-F10-03**: Given URLs in extracted content (image URLs, profile links, etc.), when output, then they shall be converted to absolute URLs with UTM and tracking parameters removed.

**AC-F10-04**: Given numeric counts (likes, followers, views), when output, then they shall be returned as integers (with suffix parsing: "1.2K" → 1200, "3M" → 3000000).

**AC-F10-05**: Given a partial scrape (some selectors succeeded, some failed), when output, then the system shall include successfully extracted fields and mark missing fields with `null` and a `partial_reasons` log.

---

### F11 — Session/Cookie Management

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F11 |
| **Name** | Session/Cookie Management |
| **Priority** | P0 — Critical |
| **Story Points** | 13 |
| **Description** | Persistent, encrypted cookie jar storage for authenticated scraping. Users can import browser cookies (from Chrome/Firefox) to enable scraping of content that requires a login session. All cookies are stored encrypted at rest and associated with specific domains. Session state is maintained across scrapes for continuity. |
| **Dependencies** | None |

#### User Stories

**US-F11-01**: As a researcher, I want to import my browser's cookies for a specific site so that I can scrape content that requires being logged in.

**US-F11-02**: As a developer, I want cookies to be stored encrypted so that my session data is secure even if the storage file is accessed by unauthorized parties.

**US-F11-03**: As a data analyst, I want sessions to persist across multiple scrapes so that I don't need to re-import cookies for every scraping job.

**US-F11-04**: As a security-conscious user, I want to see which domains have stored cookies and be able to delete them individually so that I maintain control over my authentication data.

#### Acceptance Criteria

**AC-F11-01**: Given a user imports cookies from a Chrome cookie export file, when the cookies are loaded, then the system shall parse and store them encrypted by domain, associating each cookie with its exact domain and path.

**AC-F11-02**: Given a scrape request for a domain with stored cookies, when the request is made, then the system shall automatically include relevant cookies in the HTTP headers or browser context.

**AC-F11-03**: Given a session that has expired (cookie rejected by server, redirect to login), when detected, then the system shall report: "Session expired for [domain] — please re-import cookies" and fail gracefully.

**AC-F11-04**: Given the cookie storage, when queried via CLI (`phoenix cookies list`), then the system shall display: domain, cookie count, and expiry date for each stored session (not cookie values).

**AC-F11-05**: Given a user requests deletion of cookies for a specific domain (`phoenix cookies remove instagram.com`), when executed, then all cookies for that domain shall be permanently deleted from storage.

---

### F12 — Source Archive

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F12 |
| **Name** | Source Archive |
| **Priority** | P1 — High |
| **Story Points** | 5 |
| **Description** | Save a complete raw HTML snapshot of every page scraped, creating an immutable audit trail. Archived HTML is stored with scrape metadata (timestamp, URL, scraper used) for future reference, debugging, and compliance verification. |
| **Dependencies** | F10 |

#### User Stories

**US-F12-01**: As a researcher, I want the raw HTML of every scraped page saved so that I can verify extracted data against the original source if questions arise.

**US-F12-02**: As a developer, I want to replay a scrape from archived HTML so that I can debug selector failures without re-hitting the live site.

**US-F12-03**: As a compliance officer, I want an immutable record of what content was scraped and when so that I can demonstrate ethical scraping practices.

#### Acceptance Criteria

**AC-F12-01**: Given any successful scrape, when completed, then the system shall save the complete raw HTML response to the archive directory with filename format: `{timestamp}_{domain}_{hash}.html`.

**AC-F12-02**: Given an archived HTML file, when requested for replay, then the system shall parse the archived HTML with current selectors and return results as if it were a live scrape.

**AC-F12-03**: Given archive storage limits, when the configured maximum archive size is reached, then the system shall apply FIFO rotation (oldest archives deleted first) and log the rotation event.

---

### F13 — Smart Selector Fallback

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F13 |
| **Name** | Smart Selector Fallback |
| **Priority** | P1 — High |
| **Story Points** | 8 |
| **Description** | When primary CSS selectors fail to match elements (indicating a site structure change), automatically attempt alternative selector sets in priority order. Each scraper maintains multiple selector versions for critical data points, allowing graceful degradation when sites redesign. |
| **Dependencies** | None (all scrapers depend on this) |

#### User Stories

**US-F13-01**: As a developer, I want the system to try alternative selectors when the primary ones fail so that minor site changes don't immediately break all scrapes.

**US-F13-02**: As a data analyst, I want to be notified when fallback selectors are used so that I know a site may have changed and primary extraction needs updating.

**US-F13-03**: As a developer, I want selector sets to be versioned and easily updatable via configuration files so that I can deploy selector updates without code changes.

#### Acceptance Criteria

**AC-F13-01**: Given a scraper with 3 selector sets for "post caption" (primary, fallback-1, fallback-2), when the primary selector returns no matches, then the system shall automatically try fallback-1, and if that also fails, fallback-2.

**AC-F13-02**: Given a fallback selector succeeds where the primary failed, when the scrape completes, then the output shall include a `warnings` array with: "Used fallback selector [name] for [field] — primary selector may need updating."

**AC-F13-03**: Given all selector sets for a field fail, when the scrape completes, then the field shall be set to `null` in output with `partial_reasons` noting: "No matching selectors found for [field] — site structure may have changed."

**AC-F13-04**: Given selector definitions stored in YAML configuration files, when a file is updated, then the system shall reload selectors on the next scrape without requiring process restart.

---

### F14 — Ollama Local AI Extraction

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F14 |
| **Name** | Ollama Local AI Extraction |
| **Priority** | P1 — High |
| **Story Points** | 13 |
| **Description** | The Ollama AI Engine provides intelligent HTML parsing and data extraction when standard CSS selectors and XPath expressions fail. Raw HTML is sent to the locally-hosted Ollama service (`http://localhost:11434`) running `dolphincoder:7b` by default (with `qwen2.5:7b` as fallback), which analyzes the DOM structure and returns structured JSON extractions. The engine supports HTML chunking for large pages, response caching to reduce redundant inference, hardware auto-detection for model selection (GPU → dolphincoder:7b, CPU → dolphincoder:7b or qwen2.5:7b fallback), and automatic Ollama health checking. Temperature is set to 0.1-0.3 for deterministic extraction results. All inference runs locally — no data leaves the user's machine. |
| **Dependencies** | F13, F25, F26 |

#### User Stories

**US-F14-01**: As a developer, I want the local Ollama model to extract structured data from HTML when all CSS selectors fail so that scraping continues working even after site redesigns, without sending my data to external APIs.

**US-F14-02**: As a data analyst, I want the local AI to suggest updated CSS selectors when a known site changes its HTML structure so that scrapes can be restored quickly without manual HTML inspection.

**US-F14-03**: As a developer, I want Ollama-extracted data to be validated against a schema and include a confidence score so that I can trust or review the results.

**US-F14-04**: As a system operator, I want Ollama inference responses to be cached so that identical HTML doesn't trigger redundant local inference calls, improving speed.

**US-F14-05**: As a privacy-conscious user, I want all AI processing to happen locally on my machine so that no scraped data is sent to external cloud services.

**US-F14-06**: As a developer, I want large HTML pages to be automatically chunked before sending to Ollama so that pages exceeding the model's context window can still be processed.

#### Acceptance Criteria

**AC-F14-01**: Given all CSS selectors for a page have failed, when the Ollama AI Engine is invoked with the raw HTML and `ExtractionContext`, then it shall call the local Ollama API (`dolphincoder:7b` on GPU, or `dolphincoder:7b`/`qwen2.5:7b` on CPU, temperature 0.2) and return structured data matching the `UnifiedOutput` schema within 15 seconds on GPU or 60 seconds on CPU.

**AC-F14-02**: Given a known site where primary selectors fail, when `OllamaAIEngine.suggest_selectors()` is called with the new HTML and old selectors, then the local model shall return proposed CSS selectors with confidence scores (0.0-1.0) and sample matched content within 15 seconds on GPU or 60 seconds on CPU.

**AC-F14-03**: Given Ollama extraction results, when the data is returned, then each field shall include a confidence score, and fields with confidence < 0.7 shall be flagged for human review.

**AC-F14-04**: Given identical HTML is submitted twice for AI extraction, when the second request is made within the cache TTL (default 1 hour), then the result shall be served from cache with zero inference overhead.

**AC-F14-05**: Given Ollama service is not running, when AI extraction is requested, then the system shall skip the AI fallback gracefully and return heuristic extraction with a clear warning: "Ollama service not available — install from ollama.com and run `ollama serve`".

**AC-F14-06**: Given an HTML page exceeding the model's context window, when sent to the Ollama AI Engine, then the `HTMLChunker` shall split it into overlapping chunks at element boundaries, process each chunk, and merge the results.

**AC-F14-07**: Given Ollama returns an out-of-memory error during inference, when the error occurs, then the system shall automatically fall back to CPU mode or skip AI and retry before failing.

**AC-F14-08**: Given the Ollama service is running but the required model is not pulled, when the engine initializes, then it shall automatically trigger `ollama pull dolphincoder:7b` (with `qwen2.5:7b` fallback if needed) and wait for download completion with progress reporting.

---

### F15 — Rate Control

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F15 |
| **Name** | Rate Control |
| **Priority** | P0 — Critical |
| **Story Points** | 8 |
| **Description** | Configurable per-domain rate limiting to ensure respectful, ethical scraping. Polite defaults are enforced (1 request per second per domain minimum). Rate limits are configurable per domain, per scraper type, and globally. The system tracks request timing and enforces delays between requests to the same domain. |
| **Dependencies** | None |

#### User Stories

**US-F15-01**: As a developer, I want Phoenix Engine to enforce polite scraping delays by default so that I don't accidentally overwhelm target servers.

**US-F15-02**: As a data analyst, I want to configure different rate limits for different domains so that I can scrape faster from sites that allow it and slower from sensitive ones.

**US-F15-03**: As an ethical scraper, I want the system to respect and check robots.txt so that I can ensure compliance with site owner preferences.

**US-F15-04**: As a developer, I want a global concurrent request limit so that I can control overall resource usage.

#### Acceptance Criteria

**AC-F15-01**: Given the default configuration, when scraping any domain, then the system shall enforce a minimum 1-second delay between consecutive requests to the same domain.

**AC-F15-02**: Given a per-domain rate configuration (e.g., `instagram.com: 3s`, `example.com: 0.5s`), when scraping, then the system shall apply the domain-specific delay.

**AC-F15-03**: Given a robots.txt file at a target domain's root, when scraping is initiated, then the system shall check for crawl-delay directives and apply them if present (unless overridden by explicit user configuration).

**AC-F15-04**: Given a global concurrent limit of 100 URLs, when batch scraping (F19) is active, then the system shall process at most 100 simultaneous requests across all domains, queueing additional requests.

**AC-F15-05**: Given a scrape request would exceed the rate limit, when evaluated, then the system shall queue the request and process it after the rate limit window has elapsed, logging the delay.

---

### F16 — Plugin System

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F16 |
| **Name** | Plugin System |
| **Priority** | P1 — High |
| **Story Points** | 8 |
| **Description** | Extensible plugin architecture allowing users to register custom scrapers for new websites. A plugin consists of: URL pattern matching rules, CSS/XPath selector definitions, optional custom parsing logic, and output field mappings. Plugins are loaded dynamically at runtime from a designated directory. |
| **Dependencies** | F1, F13 |

#### User Stories

**US-F16-01**: As a developer, I want to write a custom scraper plugin for an internal company website so that Phoenix Engine can extract data from our proprietary platforms.

**US-F16-02**: As a data analyst, I want to share scraper plugins with my team so that we can standardize scraping across our organization.

**US-F16-03**: As a developer, I want plugins to be hot-reloadable so that I can update selector definitions without restarting Phoenix Engine.

#### Acceptance Criteria

**AC-F16-01**: Given a plugin file placed in the plugins directory with valid URL patterns and selectors, when Phoenix Engine starts, then the plugin shall be loaded and URLs matching its patterns shall be routed to it.

**AC-F16-02**: Given a plugin with custom selector definitions, when a matching URL is scraped, then the plugin's selectors shall be used for data extraction and the plugin's output fields shall be included in the unified output.

**AC-F16-03**: Given a running Phoenix Engine instance, when a plugin file is modified, then the system shall detect the change and reload the plugin on the next scrape request.

**AC-F16-04**: Given a plugin with malformed configuration, when loaded, then the system shall reject it with a clear error message indicating the validation failure and continue loading other plugins.

---

### F17 — CLI Interface

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F17 |
| **Name** | CLI Interface |
| **Priority** | P0 — Critical |
| **Story Points** | 13 |
| **Description** | Full-featured command-line interface for the Phoenix Engine scraping platform. Supports single URL scraping, batch URL files, output format selection, configuration overrides, session management, and diagnostic commands. The CLI is the primary interface for direct usage and scripting integration. |
| **Dependencies** | All scrapers (F1-F9), F11, F15 |

#### User Stories

**US-F17-01**: As a data analyst, I want to run a quick scrape from the command line with a single URL so that I can get structured data without writing code.

**US-F17-02**: As a developer, I want to specify output format (JSON, JSONL, CSV) via CLI so that I can integrate scrapes into data pipelines.

**US-F17-03**: As a researcher, I want to scrape multiple URLs from a file so that I can process batches of content efficiently.

**US-F17-04**: As a developer, I want verbose logging and diagnostic output so that I can debug scraping issues.

#### Acceptance Criteria

**AC-F17-01**: Given the command `phoenix scrape https://instagram.com/p/ABC123`, when executed, then the system shall scrape the URL and output structured JSON to stdout with extracted data.

**AC-F17-02**: Given the command `phoenix scrape --input urls.txt --format jsonl`, when executed, then the system shall scrape all URLs in the file and output one JSON object per line.

**AC-F17-03**: Given the command `phoenix scrape --cookies chrome_export.json https://example.com/private`, when executed, then the system shall load the specified cookies and include them in the scraping session.

**AC-F17-04**: Given the command `phoenix diagnose https://example.com`, when executed, then the system shall output: URL classification, selected strategy, response time, HTTP status, content-type, detected selectors (with match counts), and any warnings.

---

### F18 — Library API

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F18 |
| **Name** | Library API |
| **Priority** | P0 — Critical |
| **Story Points** | 13 |
| **Description** | Python library interface for programmatic access to all Phoenix Engine capabilities. Provides a clean, async-compatible API for embedding scraping functionality into Python applications. Supports both synchronous and asynchronous usage patterns. |
| **Dependencies** | All scrapers (F1-F9), F11, F15 |

#### User Stories

**US-F18-01**: As a developer, I want to import Phoenix Engine as a Python library so that I can integrate scraping into my applications.

**US-F18-02**: As a developer, I want async/await support so that I can perform non-blocking scrapes in my async applications.

**US-F18-03**: As a developer, I want to configure scraping options programmatically so that I can build dynamic scraping workflows.

**US-F18-04**: As a developer, I want to receive structured Python objects (dataclasses) from scrapes so that I get type safety and IDE autocomplete.

#### Acceptance Criteria

**AC-F18-01**: Given `import phoenix` in a Python script, when `phoenix.scrape("https://example.com")` is called, then it shall return a Python dict matching the unified output schema.

**AC-F18-02**: Given an async context, when `await phoenix.scrape_async("https://example.com")` is called, then it shall perform the scrape without blocking the event loop.

**AC-F18-03**: Given a configuration object `ScrapeConfig(strategy="browser", cookies=cookie_jar)`, when passed to `phoenix.scrape(url, config=config)`, then the system shall apply all specified options.

**AC-F18-04**: Given the library API, when a scrape fails, then it shall raise a specific exception (`ScrapeError`, `SelectorError`, `RateLimitError`, etc.) with descriptive message and context.

---

### F19 — Batch Scraping

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F19 |
| **Name** | Batch Scraping |
| **Priority** | P1 — High |
| **Story Points** | 8 |
| **Description** | Process multiple URLs asynchronously with concurrency control, per-domain rate limiting, and progress tracking. Batch jobs can be submitted via file input, URL list, or programmatically. Results are streamed as they complete, with per-URL status tracking and error isolation (one URL's failure doesn't block others). |
| **Dependencies** | F15, F17, F18 |

#### User Stories

**US-F19-01**: As a data analyst, I want to submit a list of 100 URLs and have them processed in parallel so that I can get results faster than sequential scraping.

**US-F19-02**: As a developer, I want per-domain rate limiting in batch mode so that even with 100 concurrent requests, each domain is scraped respectfully.

**US-F19-03**: As a researcher, I want results streamed as they complete so that I don't need to wait for the slowest URL before seeing any output.

**US-F19-04**: As a developer, I want one failed URL in a batch to not affect the others so that partial failures don't lose all progress.

#### Acceptance Criteria

**AC-F19-01**: Given a batch of 100 URLs across 5 different domains, when submitted, then the system shall process up to the configured concurrency limit simultaneously, respecting per-domain rate limits.

**AC-F19-02**: Given a batch job in progress, when individual URLs complete, then results (or errors) shall be emitted immediately in the configured output format.

**AC-F19-03**: Given a batch where one URL fails (timeout, blocked, etc.), when processed, then the failure shall be logged, the URL marked with `status: "error"` and `error_message`, and remaining URLs shall continue processing.

**AC-F19-04**: Given a batch job, when complete, then the system shall output a summary: total URLs, successful, failed, partial, total duration, and average time per URL.

---

### F20 — Transparent Diagnostics

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F20 |
| **Name** | Transparent Diagnostics |
| **Priority** | P1 — High |
| **Story Points** | 5 |
| **Description** | Comprehensive logging and diagnostic output for every scrape operation. Each scrape produces a detailed log including: URL classification decision, strategy selection reasoning, HTTP request details, selector match results, extraction timing per field, warnings, errors, and final output summary. Diagnostics are available via CLI and programmatically. |
| **Dependencies** | All scrapers |

#### User Stories

**US-F20-01**: As a developer, I want detailed logs of every scrape so that I can debug why a particular URL failed to extract expected data.

**US-F20-02**: As a data analyst, I want to see which selectors matched and which didn't so that I can assess data completeness confidence.

**US-F20-03**: As a developer, I want scrape timing breakdowns (DNS, connect, TTFB, render, extract) so that I can identify performance bottlenecks.

#### Acceptance Criteria

**AC-F20-01**: Given any scrape operation, when completed, then the diagnostic log shall include: URL, classification, strategy, HTTP status, response time, selectors attempted (with match counts per selector), fields extracted, fields missing, warnings, and errors.

**AC-F20-02**: Given the `phoenix diagnose` CLI command, when executed, then the output shall include a human-readable report of the scrape pipeline with decision rationale at each step.

**AC-F20-03**: Given a scrape with warnings (fallback selectors used, partial extraction), when output, then warnings shall be prominently displayed in both CLI and programmatic output.

**AC-F20-04**: Given a failed scrape, when output, then the error message shall include: failure type, suspected cause, recommended action, and relevant log excerpt.

---

### F21 — Ollama Selector Repair

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F21 |
| **Name** | Ollama Selector Repair |
| **Priority** | P1 — High |
| **Story Points** | 8 |
| **Description** | When existing CSS selectors fail to match (indicating a site layout change), the Ollama Selector Repair feature sends the old (broken) selectors along with the new HTML structure to the locally-hosted Ollama model. The local model analyzes the DOM, identifies where the content has moved, and suggests updated CSS selectors that match the new layout. Suggested selectors are validated against the live HTML before being presented to the user for approval. Works entirely offline — no external API calls. |
| **Dependencies** | F13, F14, F25, F26 |

#### User Stories

**US-F21-01**: As a developer, I want the local Ollama model to automatically detect why my selectors broke and suggest fixes so that I don't need to manually inspect the new HTML structure, even when working offline.

**US-F21-02**: As a data analyst, I want selector repair suggestions to include a confidence score and sample matched content so that I can quickly assess if the fix is correct.

**US-F21-03**: As a developer, I want repaired selectors to be validated against the live HTML before being saved so that only working selectors are deployed.

**US-F21-04**: As a system operator, I want selector repair to trigger automatically when fallback selectors are activated so that breakages are addressed proactively.

#### Acceptance Criteria

**AC-F21-01**: Given a set of failed selectors and new HTML, when `OllamaAIEngine.suggest_selectors()` is called, then the local Ollama model (`qwen2.5:7b` on GPU or `qwen2.5:7b` on CPU, temperature 0.2) shall return new CSS selectors with confidence scores within 15 seconds on GPU or 60 seconds on CPU.

**AC-F21-02**: Given Ollama-suggested selectors, when received, then each suggestion shall include: the new selector string, the target field name, a confidence score (0.0-1.0), and a sample of content that would be matched.

**AC-F21-03**: Given selector suggestions with confidence >= 0.85, when validated against the live HTML, then the system shall automatically test each selector and report match/no-match results.

**AC-F21-04**: Given validated selector suggestions, when presented to the user via `phoenix selectors repair --platform x_twitter`, then the user can approve individual selectors or all suggestions; approved selectors are saved to the selector configuration file.

**AC-F21-05**: Given selector repair is triggered automatically, when fallback selectors activate for more than 3 scrapes of the same platform within 1 hour, then the system shall initiate automatic selector repair and log the event.

---

### F22 — Ollama Content Classifier

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F22 |
| **Name** | Ollama Content Classifier |
| **Priority** | P2 — Medium |
| **Story Points** | 5 |
| **Description** | The Ollama Content Classifier sends an HTML snippet to the locally-hosted Ollama model and receives a content type classification with confidence score. Supported types include: article, product, profile, post, video, comment, story, reel, short, listing, and unknown. Model auto-selection based on HTML size (7b for most tasks, 14b for large/complex pages). This enables the router to select the appropriate scraper and extraction schema even for unrecognized or changed page layouts. Temperature is set to 0.1 for highly deterministic classification. |
| **Dependencies** | F1, F14, F25, F26 |

#### User Stories

**US-F22-01**: As a developer, I want the local Ollama model to classify any HTML page by content type so that the system can route it to the correct scraper even for unknown sites, without sending data externally.

**US-F22-02**: As a data analyst, I want content classification to return a confidence score so that low-confidence classifications can be flagged for manual review.

**US-F22-03**: As a developer, I want the classifier to suggest an extraction schema for the detected content type so that Ollama extraction can use the optimal output structure.

#### Acceptance Criteria

**AC-F22-01**: Given any valid HTML snippet and URL, when `OllamaAIEngine.classify_content()` is called, then the local Ollama model (`qwen2.5:7b` for snippets < 10K tokens, `qwen2.5:7b` for larger pages, temperature 0.1) shall return a content type classification within 10 seconds on GPU or 45 seconds on CPU.

**AC-F22-02**: Given the classification result, when returned, then it shall include: content_type (one of: article, product, profile, post, video, comment, story, reel, short, listing, unknown), confidence (0.0-1.0), platform_detected (optional), and schema_suggested (JSON Schema for extraction).

**AC-F22-03**: Given a confidence score below 0.6, when the classifier returns, then the system shall log a warning: `Low confidence classification ({type}: {confidence}) for {url} — manual review recommended`.

**AC-F22-04**: Given classification is complete, when the content type is determined, then the system shall select the corresponding extraction schema and pass it to the Ollama AI Engine for structured extraction.

---

### F23 — Ollama Anti-Bot Recovery

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F23 |
| **Name** | Ollama Anti-Bot Recovery |
| **Priority** | P2 — Medium |
| **Story Points** | 8 |
| **Description** | When scraping is blocked by anti-bot measures (Cloudflare, CAPTCHA, rate limiting, IP blocking), the Ollama Anti-Bot Recovery feature sends the block page HTML to the locally-hosted Ollama model for analysis. The local model identifies the type of blocking mechanism and suggests specific recovery strategies such as: changing user-agent, adding delays, switching to browser mode, adjusting request headers, or recommending proxy usage. Works entirely offline. Temperature is set to 0.3 for a balance of creativity and reliability in strategy suggestions. |
| **Dependencies** | F2, F14, F25, F26 |

#### User Stories

**US-F23-01**: As a developer, when my scraper is blocked, I want the local Ollama model to analyze the block page and tell me what type of protection is being used so that I can choose the right countermeasure, without sending the block page to external services.

**US-F23-02**: As a data analyst, I want the system to automatically try recovery strategies suggested by the local model so that blocked scrapes can self-heal without manual intervention.

**US-F23-03**: As a system operator, I want anti-bot recovery attempts to be logged with the strategy used and success/failure outcome so that I can tune recovery parameters over time.

#### Acceptance Criteria

**AC-F23-01**: Given an anti-bot block page (HTTP 403, 429, or Cloudflare challenge), when `OllamaAIEngine.suggest_recovery_strategy()` is called with the HTML and status code, then the local Ollama model (`qwen2.5:7b`, temperature 0.3) shall return a recovery suggestion within 10 seconds on GPU or 45 seconds on CPU.

**AC-F23-02**: Given a recovery suggestion, when received, then it shall include: strategy_type ("user_agent_change", "increase_delay", "switch_to_browser", "add_headers", "use_proxy", "cooldown", "unknown"), confidence (0.0-1.0), recommended_actions (ordered list), and estimated_success_probability.

**AC-F23-03**: Given a recovery strategy with confidence >= 0.75, when auto-recovery is enabled, then the system shall automatically apply the suggested strategy and retry the scrape, logging the attempt and outcome.

**AC-F23-04**: Given recovery fails after 3 attempts using different strategies, when the final attempt fails, then the system shall mark the URL as blocked, queue it for retry after a cooldown period (1 hour), and notify the user.

**AC-F23-05**: Given recovery succeeds, when the successful strategy is identified, then the system shall record the strategy-platform mapping so that future blocks on the same platform try the successful strategy first.

---

### F24 — Ollama Entity Resolution

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F24 |
| **Name** | Ollama Entity Resolution |
| **Priority** | P3 — Low |
| **Story Points** | 8 |
| **Description** | The Ollama Entity Resolution feature cross-references entities (users, brands, organizations) across multiple scraped pages from different platforms. By sending profile data from multiple sources to the locally-hosted Ollama model, the engine can determine whether they represent the same real-world entity. For example: "Is the Instagram user '@elonmusk' the same entity as the X/Twitter user '@elonmusk'?" The local model compares profile names, bios, images, URLs, and cross-references to return a match confidence score. All processing happens locally — no entity data is sent externally. Temperature is set to 0.2 for analytical, deterministic comparisons. |
| **Dependencies** | F10, F14, F25, F26 |

#### User Stories

**US-F24-01**: As a researcher, I want to know if social media profiles across different platforms belong to the same person so that I can build unified entity profiles, with all analysis happening locally on my machine.

**US-F24-02**: As a data analyst, I want entity resolution to provide a confidence score and reasoning for each match so that I can decide whether to merge the profiles.

**US-F24-03**: As a developer, I want the system to store entity resolution results so that repeated comparisons don't require additional local inference calls.

#### Acceptance Criteria

**AC-F24-01**: Given two or more entity profiles from different platforms, when `OllamaAIEngine.resolve_entities()` is called, then the local Ollama model (`qwen2.5:7b`, temperature 0.2) shall return match results with confidence scores within 10 seconds on GPU or 45 seconds on CPU.

**AC-F24-02**: Given an entity resolution result, when returned, then it shall include: entity_ids compared, is_same_entity (boolean), confidence (0.0-1.0), matching_fields (list of fields that support the match), conflicting_fields (list of fields that contradict), and reasoning (text explanation).

**AC-F24-03**: Given a match confidence >= 0.85, when the result is returned, then the system shall automatically link the entities in the output with a `canonical_entity_id` referencing the unified profile.

**AC-F24-04**: Given entity resolution results, when stored, then identical entity pairs shall be served from cache for 24 hours, bypassing redundant local inference calls.

---

### F25 — Ollama Model Manager

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F25 |
| **Name** | Ollama Model Manager |
| **Priority** | P1 — High |
| **Story Points** | 8 |
| **Description** | The Ollama Model Manager handles automatic model lifecycle management for Phoenix Engine's local AI capabilities. It auto-detects available hardware (GPU VRAM, CPU cores, system RAM), selects the optimal model tier (7b for GPU or CPU), auto-downloads required models on first run, monitors model status, and provides update notifications. Users can view installed models, check their sizes, and switch between model tiers via CLI. The Model Manager ensures the right model is available and loaded before any AI operation. |
| **Dependencies** | F26 |

#### User Stories

**US-F25-01**: As a first-time user, I want Phoenix Engine to automatically download the required Ollama model on first run so that I don't need to manually run `ollama pull` commands.

**US-F25-02**: As a developer, I want the system to auto-detect my GPU and select the 7b model, or fall back to the 7b model on CPU, so that I get optimal performance without manual configuration.

**US-F25-03**: As a system operator, I want to see which Ollama models are installed, their sizes, and which one is currently active so that I can manage disk space.

**US-F25-04**: As a developer, I want to manually override the model selection (e.g., force 7b on GPU for faster inference) so that I can tune performance for my use case.

**US-F25-05**: As a user, I want to receive notifications when a newer version of the model is available so that I can benefit from improvements.

#### Acceptance Criteria

**AC-F25-01**: Given Phoenix Engine starts and the required Ollama model is not pulled, when the Model Manager initializes, then it shall automatically run `ollama pull dolphincoder:7b` (or `qwen2.5:7b` fallback) and display download progress.

**AC-F25-02**: Given a system with an NVIDIA GPU with >= 8GB VRAM, when hardware detection runs, then the Model Manager shall select `dolphincoder:7b` and report: "GPU detected: {name}, {vram}GB VRAM — using dolphincoder:7b model".

**AC-F25-03**: Given a system with no GPU or < 8GB VRAM, when hardware detection runs, then the Model Manager shall select `dolphincoder:7b` (or `qwen2.5:7b` fallback) and report: "No GPU detected (or insufficient VRAM) — using dolphincoder:7b model on CPU".

**AC-F25-04**: Given the command `phoenix ollama models list`, when executed, then the system shall display: model name, size, parameter count, quantization, and active status for each installed model.

**AC-F25-05**: Given the command `phoenix ollama models set dolphincoder:7b` (or `qwen2.5:7b`), when executed, then the system shall switch to the specified model for all subsequent AI operations and validate that the model is available.

**AC-F25-06**: Given a model update is available (newer quantization or patch version), when detected, then the system shall log a notification: "Model update available: {model} {old_version} → {new_version}. Run `phoenix ollama models update` to upgrade."

**AC-F25-07**: Given a user requests model removal via `phoenix ollama models remove dolphincoder:7b` (or `qwen2.5:7b`), when executed, then the system shall run `ollama rm` for the specified model and confirm freeing of disk space.

---

### F26 — Ollama Health Monitor

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F26 |
| **Name** | Ollama Health Monitor |
| **Priority** | P1 — High |
| **Story Points** | 8 |
| **Description** | The Ollama Health Monitor continuously checks the status of the Ollama service, monitors hardware utilization during inference (GPU VRAM, CPU, RAM), alerts when hardware is insufficient for the selected model, and implements auto-fallback to smaller models or CPU mode on out-of-memory errors. It provides CLI commands for health checks and integrates with the diagnostic system for real-time status reporting. |
| **Dependencies** | None (foundational for all Ollama features) |

#### User Stories

**US-F26-01**: As a developer, I want Phoenix Engine to check if Ollama is running before attempting AI operations so that I get clear guidance if the service needs to be started.

**US-F26-02**: As a system operator, I want to monitor GPU VRAM and RAM usage during local inference so that I can identify resource bottlenecks.

**US-F26-03**: As a user, I want the system to alert me if my hardware is insufficient for the selected model so that I know to switch to a smaller model or upgrade.

**US-F26-04**: As a developer, I want automatic fallback to a smaller model if the current model runs out of memory so that AI operations continue without crashing.

**US-F26-05**: As a system operator, I want a CLI command to check full Ollama health status so that I can quickly diagnose AI-related issues.

#### Acceptance Criteria

**AC-F26-01**: Given Phoenix Engine initializes, when the Health Monitor starts, then it shall ping `http://localhost:11434/api/tags` and report: "Ollama: running" or "Ollama: not running — start with `ollama serve`".

**AC-F26-02**: Given Ollama is not running, when an AI feature is requested, then the system shall log: "Ollama service unavailable. Install from ollama.com and start with `ollama serve`. AI features disabled." and continue without AI.

**AC-F26-03**: Given local inference is in progress, when monitored, then the Health Monitor shall track: GPU VRAM usage (% and MB), GPU utilization (%), system RAM usage (% and GB), and CPU utilization (%), logging these at DEBUG level.

**AC-F26-04**: Given GPU VRAM usage exceeds 95% during inference, when detected, then the system shall log a warning: "GPU VRAM critically high ({used}/{total}MB). Consider using 7b model or CPU mode." and trigger auto-fallback if configured.

**AC-F26-05**: Given a model fails to load due to insufficient VRAM (Ollama OOM error), when the error occurs, then the system shall automatically: (1) try `dolphincoder:7b`, (2) if still OOM, try `qwen2.5:7b`, (3) if still OOM, try CPU mode with `qwen2.5:7b`, (4) if still failing, skip AI with warning. Each fallback step is logged.

**AC-F26-06**: Given the command `phoenix ollama status`, when executed, then the system shall display: Ollama service status (running/not running), currently loaded model, GPU info (name, VRAM total/used/free), system RAM (total/used/free), and health score (healthy/degraded/critical).

**AC-F26-07**: Given inference time exceeds 60 seconds on CPU, when detected, then the system shall log: "Inference slow ({time}s on CPU). Consider using GPU for better performance." and continue processing.

**AC-F26-08**: Given the Ollama service crashes or becomes unresponsive during inference, when detected (request timeout > 120s), then the system shall mark Ollama as degraded, skip remaining AI operations for the current batch, and retry Ollama health check after 30 seconds.

---

### F27 — AI Coding Assistant

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F27 |
| **Name** | AI Coding Assistant |
| **Priority** | P1 — High |
| **Story Points** | 13 |
| **Description** | Interactive local Ollama assistant (`scripts/scraping_assistant.py`) that helps developers inspect code, search the project, run checks, and apply edits. Supports `/read`, `/search`, `/tree`, `/model`, `/apply`, `/check`, `/help`, `/quit`, and `/agent <task>` autonomous multi-step mode. All operations run against the local `dolphincoder:7b` model (with `qwen2.5:7b` fallback) and never leave the machine. |
| **Dependencies** | F25, F26 |

#### User Stories

**US-F27-01**: As a developer, I want an interactive assistant that can read project files and answer questions about Phoenix Engine code so that I can onboard faster without external search.

**US-F27-02**: As a developer, I want the assistant to search the codebase and summarize relevant files so that I can find implementation details quickly.

**US-F27-03**: As a developer, I want the assistant to run project checks (`/check`) and propose edits (`/apply`) so that routine maintenance tasks are automated.

#### Acceptance Criteria

**AC-F27-01**: Given the command `python scripts/scraping_assistant.py`, when started, then the assistant shall load the configured local Ollama model and present a `>` prompt accepting `/read`, `/search`, `/tree`, `/model`, `/apply`, `/check`, `/help`, `/quit`, and `/agent <task>`.

**AC-F27-02**: Given `/agent "add a retry decorator to the HTTP client"`, when executed, then the assistant shall produce a multi-step plan, confirm actions, apply file edits, and run `/check` to validate.

**AC-F27-03**: Given the assistant proposes a code change, when the user provides `--yes`/`-y`, then the assistant shall auto-approve and apply the change without interactive confirmation.

**AC-F27-04**: Given the assistant is asked about project structure, when `/tree` is used, then it shall return a concise directory tree respecting `.gitignore`.

---

### F28 — Agent Mode

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F28 |
| **Name** | Agent Mode |
| **Priority** | P1 — High |
| **Story Points** | 13 |
| **Description** | Multi-step autonomous JSON plan execution inside the coding assistant. The assistant parses a high-level task into ordered actions (read, search, edit, check), executes them with optional per-action approval, and retries on failure. Experimental; requires human oversight for destructive operations. |
| **Dependencies** | F27 |

#### User Stories

**US-F28-01**: As a developer, I want the assistant to break a complex task into a JSON plan so that I can review steps before execution.

**US-F28-02**: As a developer, I want per-action approval during agent execution so that I can stop unsafe operations.

**US-F28-03**: As a developer, I want the agent to retry failed checks automatically so that transient issues do not abort the task.

#### Acceptance Criteria

**AC-F28-01**: Given `/agent <task>`, when the task is parsed, then the assistant shall output a JSON plan with `action`, `file`, and `description` fields before execution.

**AC-F28-02**: Given a plan step that modifies a file, when approval mode is enabled, then the assistant shall prompt "Approve? (y/n)" and only proceed on `y`.

**AC-F28-03**: Given a plan step that runs `/check` and fails, when retry is configured, then the agent shall attempt to fix the issue and rerun the check up to a configured maximum.

**AC-F28-04**: Given `--yes`/`-y` flag, when agent mode runs, then all non-destructive steps shall be auto-approved; destructive steps still require explicit confirmation.

---

### F29 — Search-Driven Discovery

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F29 |
| **Name** | Search-Driven Discovery |
| **Priority** | P2 — Medium |
| **Story Points** | 8 |
| **Description** | PhoenixArchitect researcher role. Builds dork-style search queries from a natural-language goal, executes them via DuckDuckGo or SerpAPI, and returns ranked result URLs for the Explorer to visit. Respects rate limits and caches result lists. |
| **Dependencies** | F1 |

#### User Stories

**US-F29-01**: As a data analyst, I want to discover candidate sites for a scraping goal ("Egypt real estate listings") so that I do not need to know URLs in advance.

**US-F29-02**: As a developer, I want the search engine to be pluggable (DuckDuckGo default, SerpAPI fallback) so that I can adapt to API availability.

**US-F29-03**: As a user, I want search results cached so that repeated exploration does not hit search engines unnecessarily.

#### Acceptance Criteria

**AC-F29-01**: Given `phoenix discover --query "Egypt apartment listings" --engine duckduckgo --max-results 10`, when executed, then the system shall return up to 10 result URLs with titles and snippets.

**AC-F29-02**: Given SerpAPI is configured, when DuckDuckGo returns no results, then the system shall fall back to SerpAPI automatically and log the fallback.

**AC-F29-03**: Given an identical query within the cache TTL, when `phoenix discover` is run, then results shall be served from cache with no external search call.

**AC-F29-04**: Given search results, when passed to PhoenixArchitect, then the system shall filter URLs by scheme (http/https only) and skip known blocked domains.

---

### F30 — Browser Scroll & Pagination

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F30 |
| **Name** | Browser Scroll & Pagination |
| **Priority** | P2 — Medium |
| **Story Points** | 8 |
| **Description** | PhoenixArchitect explorer role. Opens discovered URLs in a headless browser, detects infinite scroll vs numbered pagination vs "Next" links, scrolls or clicks to collect multiple page snapshots, and stores them for the Inspector. Enforces a configurable `max-pages` limit. |
| **Dependencies** | F2, F29 |

#### User Stories

**US-F30-01**: As a data analyst, I want the explorer to scroll an infinite-scroll listing page so that I can capture more than the first viewport of results.

**US-F30-02**: As a data analyst, I want the explorer to click numbered pagination buttons (`1,2,3,...`) so that I can capture structured listing pages.

**US-F30-03**: As a developer, I want a `max-pages` limit so that exploration terminates predictably and respectfully.

#### Acceptance Criteria

**AC-F30-01**: Given a page with infinite scroll, when the Explorer runs, then it shall detect the scroll mechanism, scroll incrementally, wait for new content, and stop when no new items load or `max-pages` is reached.

**AC-F30-02**: Given a page with numbered pagination links, when the Explorer runs, then it shall click `2,3,4...` in order, capture each page snapshot, and stop at `max-pages`.

**AC-F30-03**: Given a page with a "Next" button, when the Explorer runs, then it shall follow the next link iteratively until the button disappears or `max-pages` is reached.

**AC-F30-04**: Given `max-pages N`, when exploration completes, then the system shall return exactly N or fewer snapshots and include metadata (URL, page number, scroll depth) for each.

---

### F31 — Adapter Auto-Generation

| Attribute | Value |
|-----------|-------|
| **Feature ID** | F31 |
| **Name** | Adapter Auto-Generation |
| **Priority** | P2 — Medium |
| **Story Points** | 13 |
| **Description** | PhoenixArchitect inspector/coder/critic roles. The Inspector analyzes collected HTML snapshots with the local LLM to classify site type and identify fields. The Coder generates a Phoenix adapter (URL patterns, selectors, normalizer) and registers it. The Critic validates the adapter output against collected pages and retries if fields are missing. |
| **Dependencies** | F14, F16, F27, F29, F30 |

#### User Stories

**US-F31-01**: As a developer, I want PhoenixArchitect to generate a working adapter from a few example pages so that I can scrape new sites without hand-writing selectors.

**US-F31-02**: As a developer, I want generated adapters validated against collected HTML fixtures so that I know they extract expected fields.

**US-F31-03**: As a user, I want the Critic to retry generation when validation fails so that the adapter improves automatically.

#### Acceptance Criteria

**AC-F31-01**: Given `phoenix architect --goal "scrape Egypt property listings" --max-pages 5`, when executed, then the system shall discover candidate URLs, collect snapshots, analyze HTML, generate an adapter, register it, and output the adapter module path.

**AC-F31-02**: Given generated adapter code, when the Critic runs, then it shall execute the adapter against collected snapshots and report field coverage; if coverage is below a threshold, the Coder shall retry with adjusted selectors.

**AC-F31-03**: Given a generated adapter, when it passes validation, then it shall be registered in the plugin registry and prioritized over the generic fallback for matching URLs.

**AC-F31-04**: Given generated adapter code, when written to disk, then it shall pass `ruff`, `black`, and `mypy` checks before registration.

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| HTTP scrape latency | < 5 seconds | Time from URL submission to structured output for static HTML pages |
| Browser scrape latency | < 15 seconds | Time from URL submission to structured output for JS-rendered pages |
| Ollama GPU inference latency | < 15 seconds | End-to-end: HTML chunking → local inference → response parsing on GPU (RTX 4090 class) |
| Ollama CPU inference latency | < 60 seconds | End-to-end inference on modern CPU (acceptable but slower) |
| Ollama content classification latency | < 10 seconds (GPU) / < 45 seconds (CPU) | Content type classification via local 7b model |
| Ollama selector repair latency | < 15 seconds (GPU) / < 60 seconds (CPU) | Selector suggestion generation via local model |
| AI cache hit retrieval | < 50ms | Time to retrieve cached AI extraction result |
| HTML chunking latency | < 200ms | Time to split large HTML into context-safe chunks |
| Concurrent URL processing | 100 URLs | Maximum simultaneous scrape operations across all domains |
| Ollama concurrent inference | 1 call | Maximum simultaneous Ollama calls (single-model loading); queue additional requests |
| Per-domain throughput | 1 request/sec (default) | Configurable; polite default enforced |
| Batch processing rate | 60 URLs/minute | Throughput for mixed-domain batches at default rate limits |
| Selector matching | < 100ms | Time to apply all selectors to parsed HTML |
| Plugin loading | < 2 seconds | Time to load and validate all plugins at startup |
| Archive write | < 500ms | Time to save raw HTML snapshot to archive |
| Ollama model loading | < 30 seconds | Time to load model into GPU VRAM on first inference |

### 4.2 Reliability Requirements

| Requirement | Target |
|-------------|--------|
| HTTP scrape success rate | > 95% for static HTML pages |
| Browser scrape success rate | > 85% for JS-rendered pages |
| Ollama extraction success rate | > 85% when AI fallback is invoked |
| Selector fallback success | Primary selectors work > 90% of the time; fallback covers remaining 10% |
| Ollama inference retry success | > 80% of Ollama failures recover after model fallback (7b → 7b → CPU) |
| Cache hit rate | > 30% for repeated HTML patterns (reduces local inference overhead) |
| Uptime | No single point of failure in core scraping pipeline |
| Recovery | Automatic retry with exponential backoff for transient failures (max 3 retries) |
| Ollama service recovery | Auto-detect Ollama restart; resume AI features when service returns |
| Data integrity | Checksums on archived HTML; extraction reproducibility from archives |
| Graceful degradation | 100% of Ollama failures fall back to heuristic extraction without crashing |
| Fallback when Ollama unavailable | If Ollama is not running, skip AI fallback and return heuristic extraction with warning |

### 4.3 Selector Maintenance

| Requirement | Specification |
|-------------|---------------|
| Selector versioning | Each selector set is versioned with date and semantic version |
| Hot reload | Selector configuration files reload without process restart |
| Change detection | Warnings emitted when fallback selectors are activated |
| Update deployment | Selector updates deployable via configuration file changes only |
| Validation | Selector syntax validation on load; test extraction on sample HTML before deployment |
| Rollback | Ability to revert to previous selector version if update causes regressions |

### 4.4 Security Requirements

| Requirement | Specification |
|-------------|---------------|
| Cookie encryption | AES-256-GCM encryption for all stored cookies; key derived from user passphrase |
| User-agent transparency | Default user-agent clearly identifies as Phoenix Engine scraper |
| No credential storage | Passwords are never stored; only session cookies are persisted |
| HTTPS enforcement | All requests use HTTPS; HTTP URLs are upgraded automatically |
| Data minimization | Only requested data fields are extracted; no bulk data collection |
| Local AI privacy | All AI inference runs locally; no scraped data transmitted to external AI services |

### 4.5 Ethical Scraping Requirements

| Requirement | Specification |
|-------------|---------------|
| robots.txt compliance | robots.txt checked and respected by default; crawl-delay directives honored |
| Rate limiting | Polite defaults enforced; configurable but cannot be disabled entirely |
| Public data only | Only publicly accessible content (no authentication bypass, no paywall circumvention) |
| Transparent identification | Scraping requests include identifiable user-agent string |
| No CAPTCHA bypass | CAPTCHA challenges result in graceful failure, not circumvention |
| Respect noindex | Pages with `<meta name="robots" content="noindex">` are skipped |

### 4.6 Compatibility Requirements

| Requirement | Specification |
|-------------|---------------|
| Python version | 3.9, 3.10, 3.11, 3.12 |
| Operating systems | Linux, macOS, Windows (via WSL) |
| Browser engine | Playwright with Chromium, Firefox, WebKit support |
| Output formats | JSON, JSONL, CSV |
| Cookie import | Chrome, Firefox export formats |
| Ollama requirement | Ollama 0.2.x or later; available at ollama.com |

### 4.7 AI-Specific Requirements

#### 4.7.1 Ollama Integration Requirements

| Requirement | Specification |
|-------------|---------------|
| Ollama endpoint | `http://localhost:11434/api` (Ollama native API) |
| Client library | `ollama` Python package or direct HTTP to Ollama API |
| Authentication | None required (local service) |
| Primary model | `dolphincoder:7b` (128K context, structured JSON output, GPU recommended) |
| Fallback model | `qwen2.5:7b` (alternative/fallback on CPU) |
| Temperature extraction | 0.1-0.3 (deterministic, reproducible results) |
| Temperature analysis | 0.3-0.5 (creative for strategy suggestions) |
| Temperature classification | 0.1 (highly deterministic) |
| Response format | Structured JSON output via system prompt instructions |
| Model auto-selection | GPU with >= 8GB VRAM → 7b (14b optional); else → 7b (configurable override) |

#### 4.7.2 Hardware Requirements

| Requirement | Specification |
|-------------|---------------|
| GPU recommended | NVIDIA GPU with >= 8GB VRAM for 7b model (RTX 3060 12GB, RTX 4060, RTX 4090 class) |
| CPU minimum | 4+ cores, 16GB+ system RAM for 7b model on CPU |
| GPU minimum | NVIDIA GPU with >= 4GB VRAM for 7b model |
| Disk space | ~9GB for 7b model, ~4.5GB for 7b model |
| Hardware auto-detection | Auto-detect GPU/CPU, VRAM, RAM; select optimal model tier |
| Hardware alerts | Warn if insufficient resources for selected model |

#### 4.7.3 HTML Chunking Requirements

| Requirement | Specification |
|-------------|---------------|
| Chunk size | Max 120,000 tokens per chunk (leaves 8K for response within 128K context) |
| Overlap | 1,000 tokens overlap between chunks for context continuity |
| Split strategy | Element boundary-aware splitting when possible |
| Chunk merge | Intelligent merge of extraction results from multiple chunks |
| Model selection | Auto-select 7b; optionally 14b when HTML > 30K tokens |

#### 4.7.4 Response Caching Requirements

| Requirement | Specification |
|-------------|---------------|
| Cache key | SHA-256 of HTML content + extraction schema |
| Backends | In-memory (default), disk (persistent), Redis (shared) |
| Default TTL | 3,600 seconds (1 hour) |
| Cache invalidation | By pattern matching; manual clear via CLI |
| Cache metrics | Hit rate, miss rate, inference savings tracked |

#### 4.7.5 Fallback Chain Requirements

| Requirement | Specification |
|-------------|---------------|
| Extraction order | Primary selectors → Secondary selectors → Ollama AI → Heuristic extraction → Error |
| Ollama unavailable | Skip AI step, continue to heuristic extraction with warning logged |
| Hardware insufficient | Auto-downgrade 7b → CPU 7b → skip AI |
| Context length exceeded | Auto-chunk HTML and retry; if still fails, skip AI step |
| OOM during inference | Auto-fallback to smaller model; log warning; retry |
| All fallbacks exhausted | Return error with full diagnostics and suggested fix |

---

## 5. User Interface Specifications

### 5.1 CLI Command Reference

```bash
# Core scraping commands
phoenix scrape <url>                          # Single URL scrape
phoenix scrape --input urls.txt               # Batch from file (one URL per line)
phoenix scrape --input urls.txt --format jsonl # Batch with JSONL output
phoenix scrape --output results.json <url>    # Save to file instead of stdout
phoenix scrape --strategy browser <url>       # Force browser automation
phoenix scrape --strategy http <url>          # Force HTTP mode
phoenix scrape --cookies cookies.json <url>   # Use imported cookies
phoenix scrape --max-pages 5 <url>            # Limit pagination depth
phoenix scrape --archive --no-archive <url>   # Toggle HTML archiving

# Diagnostic commands
phoenix diagnose <url>                        # Full diagnostic output
phoenix diagnose --selectors <url>            # Show selector matching details
phoenix diagnose --timing <url>               # Show timing breakdown

# Session management
phoenix cookies import chrome_export.json     # Import browser cookies
phoenix cookies list                          # List stored cookie domains
phoenix cookies remove instagram.com          # Remove cookies for domain
phoenix cookies clear                         # Remove all stored cookies

# Plugin management
phoenix plugins list                          # List loaded plugins
phoenix plugins validate /path/to/plugin.yaml # Validate plugin config
phoenix plugins reload                        # Hot-reload all plugins

# Ollama management
phoenix ollama status                         # Check Ollama health & hardware
phoenix ollama models list                    # List installed models
phoenix ollama models set <model>             # Switch active model
phoenix ollama models pull <model>            # Download a model
phoenix ollama models remove <model>          # Remove a model
phoenix ollama models update                  # Update models to latest

# System commands
phoenix config show                           # Show current configuration
phoenix config set rate.default 2s            # Update config value
phoenix --version                             # Show version
phoenix --help                                # Show help
```

### 5.2 Configuration File Format

```toml
# ~/.phoenix/config.toml

# Rate limiting
[rate_control]
default_delay = 1.0           # seconds between requests to same domain
max_concurrent = 100          # global concurrent request limit

[rate_control.per_domain]
"instagram.com" = 3.0
"twitter.com" = 2.0
"tiktok.com" = 3.0
"linkedin.com" = 4.0
"youtube.com" = 1.0

# Browser settings
[browser]
engine = "chromium"           # chromium | firefox | webkit
headless = true
viewport_width = 1920
viewport_height = 1080
timeout = 15000               # milliseconds
wait_for = "networkidle"      # load | domcontentloaded | networkidle

# Scraping behavior
[scraping]
follow_redirects = true
max_redirects = 5
max_retries = 3
retry_backoff = "exponential" # fixed | exponential
user_agent = "PhoenixEngine/1.0 (+https://phoenixengine.dev/bot)"
archive_enabled = true
archive_max_size_mb = 1000
archive_retention_days = 90

# Selector fallback
[selectors]
fallback_enabled = true
fallback_attempts = 3
hot_reload = true

# Ollama Local AI Engine
[ollama]
enabled = true
host = "http://localhost:11434"   # Ollama service endpoint

[ollama.models]
primary = "dolphincoder:7b"     # GPU model (auto-selected if GPU detected)
fallback = "qwen2.5:7b"     # CPU model / fallback (auto-selected if no GPU)
auto_select = true                # Auto-detect hardware and select model

[ollama.inference]
temperature_extraction = 0.2
temperature_analysis = 0.5
temperature_classification = 0.1
max_tokens = 4096
timeout = 120                     # seconds (longer for local inference)
max_retries = 2

[ollama.cache]
enabled = true
ttl = 3600                        # seconds
backend = "memory"                # "memory", "disk", "redis"

[ollama.hardware]
gpu_min_vram_mb = 8192            # Minimum VRAM for 7b model
cpu_min_ram_mb = 16384            # Minimum RAM for 7b CPU inference
auto_fallback = true              # Auto-downgrade on OOM
monitor_resources = true          # Track GPU/CPU/RAM during inference

# Output
[output]
default_format = "json"           # json | jsonl | csv
pretty_print = false
include_diagnostics = false

# Plugin directory
[plugins]
directory = "~/.phoenix/plugins"
auto_reload = true
```

### 5.3 Library API Code Examples

```python
# Basic usage
import phoenix

result = phoenix.scrape("https://www.instagram.com/p/example/")
print(result["data"]["caption"])
print(result["data"]["like_count"])

# Async usage
import asyncio
import phoenix

async def scrape_multiple():
    urls = [
        "https://twitter.com/user/status/123456",
        "https://www.tiktok.com/@user/video/789",
    ]
    results = await asyncio.gather(
        *[phoenix.scrape_async(url) for url in urls]
    )
    return results

results = asyncio.run(scrape_multiple())

# With configuration
from phoenix import ScrapeConfig

config = ScrapeConfig(
    strategy="browser",
    cookies="./instagram_cookies.json",
    max_pages=10,
    output_format="jsonl"
)

result = phoenix.scrape("https://instagram.com/p/example/", config=config)

# Batch scraping
from phoenix import BatchConfig

batch_config = BatchConfig(
    max_concurrent=50,
    per_domain_delay=2.0,
    continue_on_error=True
)

urls = open("urls.txt").read().splitlines()
for result in phoenix.scrape_batch(urls, config=batch_config):
    if result["status"] == "success":
        print(f"OK: {result['source_url']}")
    else:
        print(f"FAIL: {result['source_url']} — {result.get('error')}")

# Error handling
from phoenix import ScrapeError, RateLimitError, SelectorError

try:
    result = phoenix.scrape("https://example.com")
except RateLimitError as e:
    print(f"Rate limited: {e.retry_after}s")
except SelectorError as e:
    print(f"Selectors failed: {e.failed_selectors}")
except ScrapeError as e:
    print(f"Scrape failed: {e.message}")

# Ollama status check
from phoenix import OllamaHealth

health = OllamaHealth.check()
print(f"Ollama running: {health.is_running}")
print(f"Active model: {health.active_model}")
print(f"GPU: {health.gpu_name} ({health.gpu_vram_used}/{health.gpu_vram_total}MB)")
```

### 5.4 Output Format Examples

```json
{
  "source_url": "https://www.instagram.com/p/ABC123/",
  "scraped_at": "2025-01-20T10:30:00Z",
  "scraper_version": "1.0.0",
  "scraper_name": "instagram-post",
  "strategy": "browser",
  "status": "success",
  "data": {
    "platform": "instagram",
    "content_type": "post",
    "id": "ABC123",
    "url": "https://www.instagram.com/p/ABC123/",
    "author": {
      "username": "example_user",
      "display_name": "Example User"
    },
    "caption": "Check out this amazing view! #travel #photography",
    "hashtags": ["travel", "photography"],
    "media": [
      {
        "type": "image",
        "url": "https://instagram.com/.../image1.jpg",
        "dimensions": [1080, 1350]
      }
    ],
    "engagement": {
      "like_count": 15420,
      "comment_count": 342,
      "share_count": null
    },
    "timestamp": "2025-01-18T14:22:00Z"
  },
  "diagnostics": {
    "url_classification": "instagram-post",
    "strategy_selection": "browser (JavaScript required)",
    "http_status": 200,
    "response_time_ms": 4200,
    "selectors_matched": 8,
    "selectors_fallback_used": 0,
    "ollama_used": false,
    "warnings": [],
    "archive_path": "/archive/2025-01-20_instagram_abc123.html"
  }
}
```

---

## 6. Acceptance Criteria Summary

| Feature | Stories | ACs | Key AC |
|---------|---------|-----|--------|
| F1 — Universal URL Processing | 4 | 5 | Auto-classify any URL within 100ms |
| F2 — Scraping Strategy Selection | 4 | 5 | Auto-detect HTTP vs Browser; <5s HTTP, <15s Browser |
| F3 — Instagram Scraper | 6 | 6 | Extract posts, reels, profiles, comments from HTML |
| F4 — X/Twitter Scraper | 5 | 6 | Extract tweets, profiles, threads from HTML |
| F5 — TikTok Scraper | 5 | 5 | Extract videos, profiles, comments with lazy loading |
| F6 — LinkedIn Scraper | 4 | 4 | Extract public posts, profiles, company pages from HTML |
| F7 — Facebook Scraper | 3 | 4 | Extract public posts from public pages from HTML |
| F8 — YouTube Scraper | 4 | 4 | Extract videos, channels, comments, transcripts from HTML |
| F9 — Generic Web Scraper | 5 | 5 | Extract title, author, date, content from any HTML page |
| F10 — Unified Output Format | 4 | 5 | Standardized JSON envelope across all sources |
| F11 — Session/Cookie Management | 4 | 5 | Encrypted cookie jar with import, list, remove |
| F12 — Source Archive | 3 | 3 | Raw HTML snapshot for every scrape with audit trail |
| F13 — Smart Selector Fallback | 3 | 4 | 3-tier fallback; hot-reload YAML configs |
| F14 — Ollama Local AI Extraction | 6 | 8 | Local model extracts data when selectors fail; caching; chunking; hardware auto-detection |
| F15 — Rate Control | 4 | 5 | Per-domain delays; robots.txt; max 100 concurrent |
| F16 — Plugin System | 3 | 4 | URL patterns + selectors; hot-reloadable |
| F17 — CLI Interface | 4 | 4 | Full CLI with scrape, diagnose, cookies, plugins, ollama |
| F18 — Library API | 4 | 4 | Python sync/async API with typed config |
| F19 — Batch Scraping | 4 | 4 | Async batch with per-domain rate limits |
| F20 — Transparent Diagnostics | 3 | 4 | Full decision logging, timing, selector match counts |
| F21 — Ollama Selector Repair | 4 | 5 | Auto-detect broken selectors; local AI suggests fixes; validate before deploy |
| F22 — Ollama Content Classifier | 3 | 4 | Classify page type with confidence; suggest extraction schema; model auto-select |
| F23 — Ollama Anti-Bot Recovery | 3 | 5 | Analyze block pages locally; suggest recovery strategies; auto-retry |
| F24 — Ollama Entity Resolution | 3 | 4 | Cross-platform entity matching with confidence scores; privacy-preserving |
| F25 — Ollama Model Manager | 5 | 7 | Auto-download; hardware detection; model switching; update notifications |
| F26 — Ollama Health Monitor | 5 | 8 | Service health checks; resource monitoring; auto-fallback on OOM |

**Totals**: 103 User Stories | 140 Acceptance Criteria

---

## 7. Release Criteria

### 7.1 Minimum Viable Product (MVP)

The MVP release includes all P0 features:
- F1, F2: Universal URL Processing and Strategy Selection
- F3, F4, F5, F6: Core social platform scrapers (Instagram, X, TikTok, LinkedIn)
- F9: Generic Web Scraper
- F10: Unified Output Format
- F11: Session/Cookie Management
- F15: Rate Control
- F17: CLI Interface
- F18: Library API

### 7.2 v1.1 Release

- F7, F8: Facebook and YouTube scrapers
- F12: Source Archive
- F13: Smart Selector Fallback
- F16: Plugin System
- F19: Batch Scraping

### 7.3 v1.2 Release

- F14: Ollama Local AI Extraction
- F21: Ollama Selector Repair
- F22: Ollama Content Classifier
- F23: Ollama Anti-Bot Recovery
- F25: Ollama Model Manager
- F26: Ollama Health Monitor
- F20: Enhanced Transparent Diagnostics
- F24: Ollama Entity Resolution
- Performance optimizations

---

## 8. Glossary

| Term | Definition |
|------|-----------|
| **CSS Selector** | A pattern used to select and extract elements from HTML documents (e.g., `div.article > h1`) |
| **XPath** | A query language for navigating and selecting nodes in XML/HTML documents |
| **Headless Browser** | A web browser without a graphical UI, controlled programmatically (e.g., Playwright) |
| **Infinite Scroll** | A pagination pattern where new content loads as the user scrolls down |
| **Lazy Loading** | A technique where content is only loaded when it becomes visible in the viewport |
| **Selector Fallback** | Attempting alternative CSS selectors when primary selectors fail to match |
| **Cookie Jar** | Persistent storage for HTTP cookies used to maintain session state |
| **robots.txt** | A file at a website's root that specifies scraping/crawling rules |
| **Unified Output** | A standardized JSON schema used for all scraped data regardless of source |
| **HTTP Scrape** | Scraping using direct HTTP requests without browser rendering |
| **Browser Scrape** | Scraping using a headless browser to execute JavaScript and render dynamic content |
| **Ollama** | A local LLM inference server that runs open-source models on the user's hardware (ollama.com) |
| **dolphincoder** | DolphinCoder 7B model optimized for code and structured data tasks; default for Phoenix AI features |
| **qwen2.5** | Alibaba's Qwen2.5 model (7B) used as fallback/alternative when `dolphincoder:7b` is unavailable or on limited hardware |
| **Local Inference** | Running AI models directly on the user's machine without sending data to external APIs |
| **GPU VRAM** | Video RAM on the graphics card, the limiting factor for which model size can be loaded |
| **Model Auto-Selection** | Automatic choice of 7b (GPU or CPU) model based on detected hardware capabilities |
| **Graceful Degradation** | Progressive fallback from 7b → CPU 7b → skip AI when hardware constraints are encountered |
| **TOML** | Tom's Obvious Minimal Language, a configuration file format used for Phoenix Engine settings |
