# ADR-001: Pure Scraping / Zero Official API Integration

## Status

**Accepted** — foundational architectural decision for Phoenix Engine.

## Context

Phoenix Engine extracts structured data from public web pages and social media
platforms such as Instagram, X/Twitter, TikTok, LinkedIn, Facebook, and
YouTube. There are two primary ways to access this data:

1. **Official platform APIs** (e.g., X API, Instagram Graph API, YouTube Data
   API). These require platform approval, API keys, often have restrictive rate
   limits and terms of service, and are not universally available.
2. **Public HTML scraping**. Public pages are available to any browser or HTTP
   client. Data can be extracted from the raw HTML using CSS selectors, XPath,
   and headless browser rendering.

The project must decide which approach to adopt as its core data collection
strategy.

## Decision

Phoenix Engine will use **pure web scraping only**. The engine will never use
official APIs from any social media platform or website.

All data collection will be performed through:

- Direct asynchronous HTTP requests using `httpx` and HTML parsing with
  `beautifulsoup4`, `lxml`, and `cssselect`.
- Headless browser automation using `playwright` for JavaScript-rendered pages.
- CSS selectors, XPath expressions, and regex patterns applied to raw HTML.

This decision applies to every built-in platform scraper, plugin, and
integration. The following are explicitly forbidden:

- Official API client libraries such as `tweepy`, `instagrapi`,
  `google-api-python-client`, or similar.
- Any form of authenticated API endpoint that bypasses public HTML.
- CAPTCHA-solving services, account automation, or private-data access
  mechanisms.

## Consequences

### Positive

- **Universal availability**: The engine works on any public page without
  requiring API approval, keys, or platform-specific access tiers.
- **No API rate limits**: Politeness is enforced by the engine's own rate
  controller rather than external API quotas.
- **Consistency**: A single extraction model (HTML selectors) applies across
  all platforms.
- **Transparency**: All requests identify themselves with a transparent
  user-agent and are logged in an immutable audit trail.

### Negative

- **Fragility**: Target websites can change HTML layouts without notice,
  breaking selectors. This is mitigated by selector versioning, fallback
  chains, AI-assisted selector generation, and regular fixture updates.
- **Legal and ethical risk**: Scraping must respect robots.txt, terms of
  service, and applicable laws. The engine includes robots.txt parsing,
  polite rate limiting, and public-data-only enforcement to reduce this risk.
- **Performance**: Browser-based scraping is slower and heavier than API
  calls. This is accepted as a trade-off for universality.

## Related documents

- `06-technical-architecture.md`
- `07-api-specification.md`
- `08-development-standards.md`
