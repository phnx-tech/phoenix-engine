# Changelog

All notable changes to Phoenix Engine are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-06-25

### Added

- `phoenix setup` command to check Python, Playwright browsers, Ollama, and
  license key status.
- `phoenix chat` interactive AI assistant for scraping help.
- Client-facing README with install instructions, FAQ, and license setup.
- GitHub Actions release workflow now runs tests, linting, and metadata checks
  before building.
- `twine check` verification before PyPI uploads.
- Python 3.13 added to CI matrix with pip caching.

### Fixed

- PyPI publish workflow now includes `attestations: write` permission required
  by modern `gh-action-pypi-publish`.
- Package version bumped to match release tag.

## [0.1.0] - 2026-06-23

### Added

- Initial beta release of Phoenix Engine.
- Universal pure-web scraping via HTTP and headless browser.
- Built-in adapters for Instagram, Facebook, X/Twitter, LinkedIn, TikTok,
  YouTube, and generic pages.
- Offline HMAC-signed license-key enforcement.
- PhoenixArchitect autonomous adapter generation.
- Domain learning memory and change detection.
