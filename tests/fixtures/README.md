# Test Fixtures

This directory holds static test data and HTML fixtures used by the Phoenix
Engine test suite.

## Organization

```
tests/fixtures/
├── README.md                 # This file
├── static_blog.html          # Minimal valid blog article
├── generic_page.html         # Minimal generic page
└── html/                     # Platform-specific HTML snapshots (future)
    ├── x_twitter/
    ├── instagram/
    ├── tiktok/
    ├── linkedin/
    ├── facebook/
    ├── youtube/
    └── generic/
```

### Static HTML files

Files in the root of `tests/fixtures/` are simple, hand-written HTML documents
used for unit and integration tests that need a controlled DOM.

- **`static_blog.html`** — a minimal valid blog article with `article`, `h1`,
  `time`, author, and main content elements.
- **`generic_page.html`** — a minimal generic page with basic structural
  elements and Open Graph-like meta tags.

### Platform HTML snapshots

Platform-specific fixtures live under `tests/fixtures/html/<platform>/`. These
are sanitized snapshots of real platform pages. They are intentionally empty in
Phase 0 and will be populated as platform adapters are implemented.

Each platform directory should also contain a `meta.yaml` describing the
fixture source URL, capture date, expected extraction values, and notes.

## Adding new fixtures

1. Create the HTML file in the appropriate directory.
2. Sanitize personal information and replace real identifiers with test values.
3. Add an entry to the platform `meta.yaml` with expected fields.
4. Add a test that loads the fixture via `load_html_fixture` and asserts the
   expected extraction results.

## Loading fixtures in tests

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def read_static_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")
```
