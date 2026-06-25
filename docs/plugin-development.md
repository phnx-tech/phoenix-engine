# Plugin Development Guide

Phoenix Engine supports third-party adapters through a plugin system. Adapters can
be loaded from:

1. Built-in `phoenix.adapters` package (auto-discovered).
2. Python entry points in the `phoenix.plugins` group.
3. User-specified plugin directories.

This guide walks through building a minimal adapter from scratch.

## What Is an Adapter?

An adapter is a Python class that subclasses `BaseAdapter` and implements the
scraper plugin contract:

- `manifest` — metadata describing what the adapter handles.
- `supported_patterns()` — URL regex patterns.
- `preferred_strategies()` — ordered collection strategies (`http`, `browser`).
- `collect(url, strategy, collector, options)` — fetch raw HTML.
- `extract(raw_response)` — parse platform-specific fields.
- `normalize(extracted, url, strategy)` — return a `UnifiedOutput` instance.

## Step-by-Step Example: Hacker News Adapter

The complete example lives in `examples/plugin/hackernews.py`.

### 1. Import the base classes

```python
from phoenix.adapters.base import BaseAdapter
from phoenix.plugins.manifest import PluginManifest
```

### 2. Declare the manifest

```python
@property
def manifest(self) -> PluginManifest:
    return PluginManifest(
        name="hackernews",
        version="0.1.0",
        description="Example adapter for Hacker News item pages.",
        author="Your Name",
        platforms=["hackernews"],
        url_patterns=[r"https?://news\.ycombinator\.com/item\?id=\d+"],
        strategies=["http"],
        requires_auth=False,
        supports_ai_fallback=False,
    )
```

### 3. Implement URL matching

```python
def supported_patterns(self) -> list[re.Pattern[str]]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in self.manifest.url_patterns]
```

### 4. Implement `collect`

```python
async def collect(self, url, _strategy, collector, options):
    return await collector.collect(url, options)
```

### 5. Implement `extract`

Use CSS selector fallback chains via `_extract_with_selectors`:

```python
async def extract(self, raw_response):
    soup = BeautifulSoup(raw_response.html, "html.parser")
    selector_sets = {
        "title": [".titleline > a", ".athing .titleline a"],
        "author_username": [".hnuser", "a.hnuser"],
        "score": [".score"],
    }
    results = self._extract_with_selectors(soup, selector_sets)
    return {
        "title": results["title"]["value"],
        "author_username": results["author_username"]["value"],
        "score": self._parse_engagement(results["score"]["value"]),
    }
```

### 6. Implement `normalize`

```python
async def normalize(self, extracted, url, strategy):
    from phoenix.models.output import UnifiedOutput
    return UnifiedOutput(
        url=url,
        platform="hackernews",
        content_type="post",
        title=extracted.get("title"),
        author=extracted.get("author_username"),
        scraping_strategy=strategy,
    )
```

## Loading the Plugin

### Option A: Plugin Directory

```python
from phoenix.plugins.loader import PluginLoader

loader = PluginLoader(plugin_dirs=["/path/to/examples/plugin"])
loader.load_plugin_dirs()
adapter = loader.match_url("https://news.ycombinator.com/item?id=123")
```

### Option B: Entry Point

Add to your `pyproject.toml`:

```toml
[project.entry-points."phoenix.plugins"]
hackernews = "my_package.hackernews:HackerNewsAdapter"
```

Then install the package. `PluginLoader.load_entry_points()` will discover it.

## Testing Your Adapter

Use `StubCollector` to feed synthetic HTML without network calls:

```python
import pytest
from phoenix.adapters.base import StubCollector
from phoenix.models.document import RawResponse
from phoenix.options import ScrapingOptions

@pytest.mark.asyncio
async def test_hackernews_extract(adapter):
    html = """
    <html><body>
        <span class="titleline"><a>My Title</a></span>
        <a class="hnuser">alice</a>
        <span class="score">42 points</span>
    </body></html>
    """
    collector = StubCollector(strategy="http", html=html)
    raw = await adapter.collect("https://news.ycombinator.com/item?id=1", "http", collector, ScrapingOptions())
    extracted = await adapter.extract(raw)
    assert extracted["title"] == "My Title"
    assert extracted["score"] == 42
```

## Best Practices

- **Never use official platform APIs** — Phoenix Engine is a pure scraping engine.
- **Use selector fallback chains** for resilience against layout changes.
- **Call `_is_public_content(html)`** in `collect()` to detect login walls.
- **Keep parsers deterministic** — synthetic fixtures should be enough for CI.
- **Target ≥80% test coverage** per adapter.
- **Set `supports_ai_fallback=True`** only if the adapter benefits from AI extraction.

## See Also

- [Adapters Overview](adapters/README.md)
- `examples/plugin/hackernews.py`
- `src/phoenix/adapters/base.py`
