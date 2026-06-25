# Phoenix Engine Platform Adapters

Phoenix Engine uses a plugin-style adapter architecture. Each adapter is responsible for:

1. Detecting whether it can handle a given URL.
2. Collecting the raw HTML (via HTTP or headless browser).
3. Extracting platform-specific structured data using CSS selector fallback chains.
4. Normalizing the extracted data into the unified `UnifiedOutput` schema.

All adapters live in `src/phoenix/adapters/` and are auto-discovered by `PluginLoader`.

## Built-in Adapters

| Adapter | Platforms | URL Types | Strategies |
|---------|-----------|-----------|------------|
| `InstagramAdapter` | `instagram` | Posts (`/p/`), Reels (`/reel/`), Profiles | `browser`, `http` |
| `XTwitterAdapter` | `x`, `x_twitter` | Tweets (`/status/`, `/i/web/status/`), Profiles | `http`, `browser` |
| `TikTokAdapter` | `tiktok` | Videos (`/video/`, `/t/`), Profiles | `browser`, `http` |
| `LinkedInAdapter` | `linkedin` | Posts, Profiles, Companies | `browser`, `http` |
| `FacebookAdapter` | `facebook` | Pages, Posts, Events | `browser`, `http` |
| `YouTubeAdapter` | `youtube` | Videos, Shorts, Channels | `http`, `browser` |
| `GenericWebAdapter` | `generic` | Any HTTP(S) URL fallback | `http`, `browser` |

## Adapter Contract

Every adapter subclasses `BaseAdapter` and implements:

- `manifest` — `PluginManifest` with name, version, platforms, URL patterns, strategies.
- `supported_patterns()` — compiled regex patterns for URL matching.
- `preferred_strategies()` — ordered list of collection strategies.
- `collect(url, strategy, collector, options)` — delegates to a `Collector` and flags non-public content.
- `extract(raw_response)` — returns a platform-specific dictionary.
- `normalize(extracted, url, strategy)` — returns a validated `UnifiedOutput`.

## Public-Content Guard

Each adapter calls `BaseAdapter._is_public_content(html)` to detect login walls,
private accounts, or removed pages. When non-public content is detected, the adapter
sets a structured error on the `RawResponse` instead of attempting extraction.

## Selector Fallback Chains

Adapters use `_extract_with_selectors(soup, selector_sets)` to try multiple CSS
selectors per field. This makes extraction resilient to minor layout changes.

Example from `InstagramAdapter`:

```python
{
    "caption": [
        "article._aatb div._a9zs h1",
        "article div[class*='_a9zs'] span",
        "meta[property='og:title']",
    ],
    "author_username": [
        "article._aatb header a",
        "article header a[href^='/']",
        "meta[property='og:title']",
    ],
}
```

## Pure Scraping Constraint

Phoenix Engine adapters **never** use official platform APIs. They rely solely on:

- Direct HTTP requests (`httpx`)
- Headless browser rendering (`playwright`)
- HTML parsing (`beautifulsoup4`, `lxml`, `cssselect`)

## AI Fallback

When selector chains fail to produce structured data, the engine can fall back to the
`PhoenixAIExtractor` (local Ollama by default). This is configured per-adapter via the manifest's
`supports_ai_fallback` flag and is triggered by the pipeline after selector exhaustion.

## Adding a Custom Adapter

1. Create a module in `src/phoenix/adapters/` or a separate package.
2. Subclass `BaseAdapter`.
3. Implement the required abstract methods.
4. Register it via entry point `phoenix.plugins` or place it in a user plugin directory.

See [Plugin Development Guide](../plugin-development.md) for a complete walkthrough.

## Testing

Each adapter ships with synthetic HTML fixture tests in `tests/unit/`:

- `test_instagram_adapter.py`
- `test_x_twitter_adapter.py`
- `test_tiktok_adapter.py`
- `test_linkedin_adapter.py`
- `test_facebook_adapter.py`
- `test_youtube_adapter.py`
- `test_generic_adapter.py`

Run adapter-only tests:

```bash
pytest tests/unit/test_*_adapter.py --cov=src/phoenix/adapters --cov-report=term
```

## Coverage Gate

Phase 2 requires **≥80% coverage per adapter**. The current adapter suite is tracked
via `pytest-cov` and enforced in CI.
