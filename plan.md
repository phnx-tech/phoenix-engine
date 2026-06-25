# Phoenix Engine — Complete AI-Driven Project Management Documentation Plan

## Project Overview
**Phoenix Engine** is an active Python scraping project with a working core engine, real collectors, and local Ollama AI integration. The codebase currently passes 526 tests with ~90% coverage. The default local model is `dolphincoder:7b` (with `qwen2.5:7b` as fallback); Ollama runs on a 100% GPU-backed NVIDIA setup. Implemented components include: HTTP (`DirectCollector`/`http`) and browser (`BrowserCollector` with `BrowserPool`) collectors, a stealth/anti-detection module, unified output normalizer with per-field confidence scoring, adaptive per-domain rate limiting, plugin-priority router, a PhoenixArchitect autonomous adapter-generation layer (Explorer, Inspector, Coder, Critic loop, deterministic template fallback, and Researcher-driven URL discovery) that persists generated adapters to `src/phoenix/adapters/generated/`, and an interactive `scripts/scraping_assistant.py` coding helper. Real e2e scrapes have been validated against `httpbin.org/html` and `quotes.toscrape.com`. This documentation package tracks both completed reality and the upcoming advanced-differentiator roadmap.

## Documentation Goals
Produce a complete project management package that enables an AI-driven development team (Kimi Code) to execute Phoenix Engine end-to-end — from architecture through QA, deployment, and maintenance. Every document a real engineering management team would need.

## Skill Loading
- Stage 1 (Research/Analysis): Deep-research-swarm (for best practices on data collection platforms, compliance frameworks, architecture patterns)
- Stage 2 (Documentation Writing): Report-writing skill (for structured, professional documents)
- Stage 3 (Artifact Production): docx skill (for final Word document delivery)

---

## Stage 1 — Research & Architecture Analysis
**Objective**: Gather technical intelligence on best practices for web scraping platforms, compliance requirements, and architecture patterns before writing docs.

**Sub-agents**:
1. **Tech_Researcher**: Research web scraping platform architectures, anti-detection patterns, ethical compliance frameworks (GDPR/CCPA), Python CLI tool best practices, plugin system patterns
2. **Compliance_Researcher**: Research data collection legal frameworks, platform ToS compliance, CAPTCHA avoidance ethics, rate limiting standards, audit trail requirements
3. **Market_Researcher**: Research competitor architectures (Scrapy, Playwright, Puppeteer, Apify), pricing models, feature gaps, differentiators

**Output**: Research briefs fed into Stage 2

---

## Current Status & Roadmap

### Completed Work

The following items are implemented and green in the Phoenix Engine codebase:

- **Local AI model**: default is now `dolphincoder:7b`; `qwen2.5:7b` is available as fallback/alternative.
- **Hardware**: NVIDIA driver active; Ollama uses 100% GPU.
- **Stealth/anti-detection module** implemented and tested — covers profiles, rotators, humanizer, and CAPTCHA warming.
- **Real e2e scrape validated** on `httpbin.org/html` and `quotes.toscrape.com`.
- **CLI wired to real collectors** via `--real` flag.
- **Direct collector strategy** renamed/aligned to `http`.
- **Browser collector** uses `BrowserPool`.
- **PhoenixArchitect autonomous adapter generation** implemented: `BrowserExplorer`, `Inspector`, `Coder`, `AdapterCritic`, and `PhoenixArchitect.generate_adapter()`; generated adapters are persisted to `src/phoenix/adapters/generated/` and registered at runtime.
- **Standalone real-estate learning scraper** exists at `/home/salazar/Projects/realstate/`.
- **`scripts/scraping_assistant.py`** created with commands: `/read`, `/search`, `/tree`, `/model`, `/apply`, `/check`, `/help`, `/quit`, and new `/agent <task>` autonomous multi-step mode.
- Assistant supports `--yes`/`-y` auto-approve flag.
- **Quality gates green**: `559 passed, 1 skipped, ~91% coverage`.
- **Confidence scoring**: every `UnifiedOutput` now carries `field_confidences` and an overall `confidence` score; fallback/AI-assisted extraction applies a penalty.
- **Adaptive throttling**: `RateLimiter` records per-domain latency and errors and adjusts request pacing automatically.
- **Researcher role / search-driven discovery**: `phoenix discover` and `phoenix architect generate --goal` use DuckDuckGo (with optional SerpAPI) to find candidate URLs.
- **Operational automation (Priority 2)**: persistent per-domain learning memory (`DomainMemory`), structural-drift / selector-degradation alerts (`ChangeDetector` + `AuditLogger`), and automated pytest fixture/test generation (`FixtureGenerator`) from collected snapshots.
- **PyYAML dependency** added to support `meta.yaml` fixture metadata.

### Active Limitations / Known Issues

- Generated adapter quality depends on the local 7B model; the deterministic template fallback mitigates imperfect LLM output.
- Domain-memory JSON fallback writes to `.phoenix/domain_memory.json`; test suites that rely on clean defaults should either use a fresh `data_dir` or remove the file between runs.
- **pytest-asyncio deprecation warning** is non-fatal.
- **Assistant/agent features** are experimental; human oversight required for destructive operations.
- **Facebook group scraping** is explicitly out of scope (violates Meta ToS); only public Facebook pages/posts are targeted.

### PhoenixArchitect Roadmap

**PhoenixArchitect** is the next major capability: an autonomous AI agent module that generates Phoenix adapters for discovered websites with minimal human intervention.

#### Agent Roles

1. **Planner** — understand a high-level goal (e.g., "scrape apartment listings from a real-estate site") and decide what to search for.
2. **Researcher** — search the web using dork-style queries via DuckDuckGo or SerpAPI. ✅ Implemented.
3. **Explorer** — open result links in a browser, scroll down, click pagination (`1,2,3,4...`), and collect page snapshots.
4. **Inspector** — analyze collected HTML with the local LLM to classify site type and fields.
5. **Coder** — generate a Phoenix adapter for the site and register it.
6. **Critic** — validate adapter output against collected pages and retry if fields are missing.

#### Implemented CLI Commands

```bash
phoenix discover --query "..." --engine duckduckgo --max-results N
phoenix architect generate --goal "..." --max-pages N
phoenix architect generate --url "..." --max-pages N
phoenix architect generate --url "..." --with-fixtures
phoenix architect fixtures <platform> --snapshot-dir <dir>
```

These commands are live; see the API specification for full option lists.

---

## Stage 3 — Assembly & Delivery
**Objective**: Compile all documents into a cohesive project management package.

- Convert all markdown documents to professional Word (.docx) format
- Create master index/navigation document
- Package all deliverables

---

## File Structure
```
/mnt/agents/output/phoenix-engine-project/
├── plan.md                          # This plan
├── 01-project-charter.md
├── 02-team-structure.md
├── 03-phases-milestones.md
├── 04-task-breakdown-wbs.md
├── 05-product-requirements.md
├── 06-technical-architecture.md
├── 07-api-specification.md
├── 08-development-standards.md
├── 09-testing-qa-plan.md
├── 10-risk-management.md
├── 11-communication-plan.md
├── 12-definition-of-done.md
├── master-index.md                  # Navigation hub
├── scripts/
│   └── scraping_assistant.py        # Interactive local Ollama coding helper
├── src/phoenix/adapters/
│   └── generated/                   # AI-generated site adapters (persisted)
└── /home/salazar/Projects/realstate/  # Standalone real-estate learning scraper
```
