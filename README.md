# Phoenix Engine

A universal pure-web scraping engine that turns public web pages into structured,
predictable data. No official APIs required — Phoenix Engine uses raw HTTP
requests and headless browser automation to extract posts, profiles, listings,
and articles from social platforms and websites.

> **Current status:** beta / early access. A license key is required to run the
> engine in production.

## What it does

- Scrapes public pages using **HTTP** or **headless browser** strategies.
- Returns a **unified JSON output** no matter what platform you target.
- Automatically adapts to site changes, anti-bot measures, and selector drift.
- Learns from past scrapes to pick the best strategy for each domain.
- Can be used from the command line or inside your Python application.

## Install

### From PyPI

```bash
pip install phoenix-engine
```

### From a GitHub Release wheel

Download the `.whl` from the latest release, then:

```bash
pip install phoenix_engine-0.1.0-py3-none-any.whl
```

## Activate your license

Phoenix Engine is distributed under license keys during beta. After installing,
set your key:

```bash
export PHOENIX_LICENSE_ENFORCEMENT_ENABLED=true
export PHOENIX_LICENSE_SECRET="your-signing-secret"
export PHOENIX_LICENSE_KEY="phx.eyJ..."
```

Or create a `phoenix.yaml` file:

```yaml
license_enforcement_enabled: true
license_secret: "your-signing-secret"
license_key: "phx.eyJ..."
```

If the key is missing, expired, tampered with, or over its use limit, the
engine will refuse to start.

## Quick start — CLI

```bash
# Scrape a single public page
phoenix scrape "https://example.com/post/123"

# Scrape without archiving the raw source
phoenix scrape "https://example.com/post/123" --no-archive

# Scrape multiple URLs in parallel
phoenix scrape-batch \
  "https://example.com/post/123" \
  "https://example.com/post/456" \
  --output results.json

# List built-in platform adapters
phoenix plugins list

# Inspect effective configuration (secrets are masked)
phoenix config show
```

## Quick start — Python library

```python
import asyncio
from phoenix import PhoenixEngine

async def main() -> None:
    async with PhoenixEngine() as engine:
        result = await engine.scrape("https://example.com/post/123")
        print(result.output.model_dump_json(indent=2))

asyncio.run(main())
```

## Configuration

Most settings can be controlled with environment variables or a config file
(`phoenix.yaml`, `phoenix.json`, `phoenix.toml`):

```yaml
timeout: 30
stealth_enabled: true
ai_enabled: false
rate_limits:
  example.com: 1.0
```

Run `phoenix config show` to see the active configuration.

## Supported platforms

Phoenix Engine ships with adapters for common public platforms and a generic
fallback for any HTML page:

- Instagram, Facebook, X/Twitter, LinkedIn, TikTok, YouTube
- Generic blogs, listings, and article pages

Adapters are plugin-based, so new platforms can be added without touching the
core engine.

## Ethical use

Phoenix Engine only scrapes **publicly available** content. Always respect:

- The target site's `robots.txt` and Terms of Service.
- Local laws and data-protection regulations (GDPR, CCPA, etc.).
- Rate limits — the engine includes built-in throttling to avoid overload.

## Support

- Issues: https://github.com/phnx-tech/phoenix-engine/issues
- Repository: https://github.com/phnx-tech/phoenix-engine

## License

Commercial beta license. See your license agreement for terms.
