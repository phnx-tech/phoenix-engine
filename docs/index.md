# Phoenix Engine

Welcome to the Phoenix Engine documentation.

Phoenix Engine is a universal **pure web scraping engine** built in Python. It
extracts clean, structured data from websites and social media platforms
through raw HTML parsing and headless browser automation. The engine operates
as both a command-line utility and an importable Python library.

## Core principle

**No official social media APIs are ever used.** All data collection is
performed through direct HTTP requests or headless browser rendering, with
extraction driven by CSS selectors, XPath expressions, and regex patterns.

## Documentation sections

- [Architecture Decision Records](architecture/decisions/ADR-001-pure-scraping.md)
- [Platform Adapters](adapters/README.md)
- [Plugin Development Guide](plugin-development.md)
- [Phoenix AI Extraction](features/phoenix-ai-extraction.md)

For usage and development instructions, see the project `README.md`.
