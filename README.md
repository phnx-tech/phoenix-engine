# Phoenix Engine

Universal pure web scraping engine. Extracts structured data from public web
pages and social media platforms using raw HTML parsing and headless browser
automation. Phoenix Engine never uses official platform APIs.

## Features

- Pure web scraping via HTTP (`httpx`) and headless browser (`playwright`).
- CSS/XPath selector engine with fallback chains.
- Unified output schema across all platforms.
- Plugin-based platform scraper architecture.
- Ethical-by-default: transparent user-agent, rate limiting, audit logging.

## Install

### From PyPI (recommended for clients)

```bash
pip install phoenix-engine
```

> You must also set a license key before the engine will start. See
> [Client license setup](#client-license-setup) below.

### From a GitHub Release wheel

```bash
# Download the .whl from the latest release, then:
pip install phoenix_engine-0.1.0-py3-none-any.whl
```

### From source

```bash
git clone https://github.com/phnx-tech/phoenix-engine.git
cd phoenix-engine
pip install -e ".[dev]"
```

## Client license setup

Phoenix Engine supports offline HMAC-signed license keys. To distribute to a
client:

1. Generate a key (on your machine, using your private signing secret):

   ```bash
   export PHOENIX_LICENSE_SECRET="your-private-secret"
   phoenix license generate --expires 2026-07-31 --max-uses 100 --note "Client A"
   ```

2. Give the client the generated `phx.eyJ...` key and set these in their
   environment or config file:

   ```bash
   PHOENIX_LICENSE_ENFORCEMENT_ENABLED=true
   PHOENIX_LICENSE_SECRET="your-private-secret"
   PHOENIX_LICENSE_KEY="phx.eyJ..."
   ```

   Or in `phoenix.yaml`:

   ```yaml
   license_enforcement_enabled: true
   license_secret: "your-private-secret"
   license_key: "phx.eyJ..."
   ```

The engine will refuse to start if the key is missing, expired, tampered with,
or used up.

## Usage

### CLI

```bash
# Show version
python -m phoenix --version
phoenix --version

# Show help
phoenix --help

# Scrape a single URL
phoenix scrape "https://example.com/post/123"

# Scrape without archiving the raw source
phoenix scrape "https://example.com/post/123" --no-archive

# Scrape with Phoenix AI fallback extraction (requires local Ollama)
phoenix scrape "https://example.com/post/123" --ai

# Scrape multiple URLs concurrently
phoenix scrape-batch \
  "https://example.com/post/123" \
  "https://example.com/post/456" \
  --output results.json

# List installed scraper plugins
phoenix plugins list

# Inspect effective configuration (API key masked by default)
phoenix config show

# Use a custom configuration file
phoenix --config phoenix.yaml scrape "https://example.com/post/123"
```

> **Phoenix AI model:** The default local model is `qwen2.5:7b`. Make sure
> you have pulled it in Ollama (`ollama pull qwen2.5:7b`) before using
> `--ai`. You can override it with `PHOENIX_AI_MODEL` or in a config file.

### Library

```python
import asyncio
from phoenix import PhoenixEngine

async def main() -> None:
    async with PhoenixEngine() as engine:
        result = await engine.scrape("https://example.com/post/123")
        print(result)

asyncio.run(main())
```

## Development

```bash
# Formatting and linting
black src/ tests/
ruff check src/ tests/
mypy src/phoenix

# Tests
pytest tests/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## Build and release

```bash
# Build wheel + sdist
python -m build

# Tag a release (triggers the GitHub release workflow)
git tag v0.1.0
git push origin v0.1.0
```

The `Release` workflow uploads the wheel/sdist to GitHub Releases. If you have
configured a PyPI trusted publisher for the `pypi` environment, the
`Publish to PyPI` workflow will also publish the package when the release is
published.

## Architecture Decision Records

See [docs/architecture/decisions/](docs/architecture/decisions/).

## License

MIT
