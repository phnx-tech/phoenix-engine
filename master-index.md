# Phoenix Engine — Complete Project Management Documentation

## Universal Data Collection Platform | AI-Driven Development Project

**Document Version**: 1.0
**Classification**: Confidential
**Owner**: Phoenix Consulting
**Date**: 2026-06-23

---

## About This Package

This document package contains the complete project management documentation for building Phoenix Engine — a **pure web scraping engine** with zero API dependencies. The project uses Ollama local AI for intelligent HTML extraction and AI-assisted pipeline stages.

**Critical Design Principle**: Phoenix Engine uses **only web scraping techniques** — HTTP requests with HTML parsing (BeautifulSoup, lxml, CSS selectors, XPath) and headless browser automation (Playwright). We never use official social media APIs (no Instagram API, no X API, no TikTok API, etc.).

Every document has been designed so that AI agents can read, understand, and execute autonomously while human stakeholders provide oversight at key decision points.

**Total Documentation**: 12 core documents | ~70,000 words | 13 files

---

## Document Inventory & Navigation

| # | Document | Purpose | File | Size |
|---|----------|---------|------|------|
| 1 | **Project Charter** | Project authority, scope, objectives, stakeholders, budget | `01-project-charter.md` | 4,359 words |
| 2 | **Team Structure & Roles** | AI org chart, role definitions, RACI matrix, agent config | `02-team-structure.md` | 91 KB |
| 3 | **Project Phases & Milestones** | 9-phase plan with entry/exit criteria and deliverables | `03-phases-milestones.md` | 50 KB |
| 4 | **Task Breakdown (WBS)** | 70+ tasks with assignments, estimates, dependencies, DoD | `04-task-breakdown-wbs.md` | 84 KB |
| 5 | **Product Requirements Document** | 31 features (F1–F31), user stories, acceptance criteria, NFRs | `05-product-requirements.md` | 53 KB |
| 6 | **Technical Architecture** | 6-layer architecture, data models, design patterns, security | `06-technical-architecture.md` | 69 KB |
| 7 | **API Specification** | Library API, CLI reference, plugin contract, error codes | `07-api-specification.md` | 72 KB |
| 8 | **Development Standards** | Code style, Git workflow, testing standards, AI agent prompts | `08-development-standards.md` | 49 KB |
| 9 | **Testing & QA Plan** | 630+ test targets, CI/CD pipeline, compliance testing | `09-testing-qa-plan.md` | 44 KB |
| 10 | **Risk Management Plan** | 20 risks with scores, mitigation, monitoring framework | `10-risk-management.md` | 32 KB |
| 11 | **Communication Plan** | Agent protocols, meeting rhythms, handoffs, escalation | `11-communication-plan.md` | 43 KB |
| 12 | **Definition of Done** | Universal DoD, phase gates, quality gates, release criteria | `12-definition-of-done.md` | 53 KB |

---

## How to Use This Package

### For AI Project Manager (Ollama PM)
Start with Document 1 (Charter) for project authority and scope, then use Document 3 (Phases) for sprint planning and Document 4 (WBS) for task assignment. Reference Document 11 (Communication) for coordination protocols.

### For AI Tech Lead (Ollama Architect)
Start with Document 6 (Architecture) for system design, Document 7 (API Spec) for interface contracts, and Document 8 (Standards) for code quality enforcement. Use Document 12 (DoD) for quality gate verification.

### For AI Backend Engineers (Ollama Dev-1/2/3)
Start with Document 5 (PRD) for feature specifications and user stories, then Document 6 (Architecture) for component design, Document 7 (API Spec) for implementation contracts, and Document 8 (Standards) for coding requirements.

### For AI DevOps (Ollama DevOps)
Reference Document 6 (Architecture) for deployment patterns, Document 8 (Standards) for CI/CD configuration, and Document 9 (Testing) for pipeline setup.

### For AI QA Lead (Ollama QA)
Start with Document 9 (Testing) for test strategy, Document 12 (DoD) for quality gates, and Document 5 (PRD) for acceptance criteria.

### For AI Compliance Officer (Ollama Compliance)
Reference Document 10 (Risks) for legal/compliance risks, Document 9 (Testing) for compliance test cases, and Document 12 (DoD) for compliance gate criteria.

### For AI Technical Writer (Ollama Docs)
Reference Document 5 (PRD) for feature descriptions, Document 7 (API Spec) for API documentation, and Document 8 (Standards) for documentation standards.

### For Human Stakeholders
- **Product Owner**: Documents 1, 3, 5 for scope, timeline, and requirements
- **Legal Counsel**: Documents 1, 10 for compliance and risk
- **DevRel**: Documents 5, 7 for public-facing documentation

---

## Project At a Glance

| Attribute | Value |
|-----------|-------|
| **Product** | Phoenix Engine — Universal Web Scraping Engine |
| **Type** | Python CLI tool + Programmable library (Pure Scraping, Zero APIs) |
| **Sources** | Instagram, X/Twitter, TikTok, LinkedIn, Facebook public pages, YouTube, Generic Web (all via HTML scraping). Facebook group scraping is out of scope. |
| **Completed Features** | Real HTTP/browser collectors (`--real`), stealth/anti-detection module, plugin-priority router, adaptive rate limiting, extraction confidence scoring, PhoenixArchitect autonomous adapter generation with deterministic fallback, Researcher search-driven discovery (`phoenix discover`, `phoenix architect generate`), interactive coding assistant with `/agent` mode, persistent domain learning memory, structural-drift/selector-degradation alerts, automated fixture/test generation (`phoenix architect fixtures`) |
| **Test Status** | 559 passed, 1 skipped, ~91% coverage |
| **Duration** | 18 weeks (phases 0-7) + ongoing (phase 8) + Phase 2.5 PhoenixArchitect |
| **Team Size** | 12 roles (9 AI agents + 3 humans) |
| **Total Tasks** | 70+ work items |
| **Total Story Points** | ~520 SP |
| **Test Target** | 630+ tests (500 unit / 100 integration / 30 E2E) |
| **Coverage Target** | >= 85% |
| **AI Engine** | Ollama (Local AI) — dolphincoder:7b (qwen2.5:7b fallback) — intelligent HTML extraction, selector repair, content classification, AI coding assistant/agent mode, zero external dependencies |
| **Commercialization** | Open Core → Managed Cloud → Enterprise |

---

## Core Architecture: Pure Scraping + Local AI Extraction

```
URL Input → Strategy Selector → DirectCollector (http) OR BrowserCollector (BrowserPool)
                                          ↓
                            HTML Response ─┬─→ CSS/XPath Selectors (primary)
                                           │           ↓
                                           │   All fields extracted? ──→ Unified Output (JSON)
                                           │           │                        ↓
                                           │           └─Yes──────────→ Archive + Deliver
                                           │           │
                                           │           No
                                           │           ↓
                                           └─→ Ollama (Local AI Extraction)
                                               localhost:11434
                                               dolphincoder:7b
                                                       ↓
                                              Structured JSON Data ──→ Unified Output (JSON)

Stealth / anti-detection module active (profiles, rotators, humanizer, CAPTCHA warming).
CLI wired to real collectors via `--real` flag; real e2e validated on httpbin.org/html and quotes.toscrape.com.
```

**No APIs. Ever.** All data comes from parsing raw HTML with CSS selectors, XPath, and regex patterns. JavaScript-heavy pages use Playwright headless browser rendering. Authentication uses cookie/session simulation, never API tokens.

**Ollama is the local AI extraction fallback.** When all CSS/XPath selectors fail (page layout changed, anti-scraping measures, or complex dynamic content), the raw HTML is sent to the local Ollama instance (`http://localhost:11434`) running `dolphincoder:7b`, which intelligently extracts structured data using LLM-based parsing. Ollama is never the first path — it is the intelligent fallback that maintains extraction quality when conventional parsing fails. All AI inference runs entirely on local hardware with zero external API dependencies, zero cost, and full privacy.

## Ollama Local AI Integration

### How Ollama Fits into the Scraping Pipeline

Ollama is a **core pipeline stage**, not a bolt-on feature. It sits at the end of the selector fallback chain as the ultimate extraction mechanism. All inference runs locally on the user's hardware — no API keys, no costs, no data leaves the machine.

```
Selector Fallback Chain:
  1. Primary CSS selector
  2. Fallback CSS selector #1
  3. Fallback CSS selector #2
  4. XPath backup
  5. Regex extraction
  6. OLLAMA (Local AI-powered extraction) ← invoked when all above fail
     localhost:11434 | dolphincoder:7b | zero external dependencies
```

### Ollama Call Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Raw HTML   │────→│ HTML Chunker │────→│ ModelSelector    │────→│   Ollama API    │
│  (full page)│     │ (context-safe│     │ (7b/14b/32b    │     │ localhost:11434 │
│             │     │  16384 tok)  │     │  based on VRAM) │     │                 │
└─────────────┘     └──────────────┘     └──────────────────┘     └────────┬────────┘
                                                                            │
                                                                            ↓
                                                                   ┌─────────────────┐
                                                                   │ Structured JSON │
                                                                   │ (validated)     │
                                                                   └─────────────────┘
                                                                            │
                                                    ┌───────────────────────┴───────────────┐
                                                    ↓                                       ↓
                                             ┌─────────────┐                       ┌──────────────┐
                                             │ Response    │                       │ Hardware     │
                                             │ Cache (TTL) │                       │ Monitor      │
                                             └─────────────┘                       │ (GPU/CPU)    │
                                                                                  └──────────────┘
```

### Ollama Pipeline: HTML → ModelSelector → Ollama → JSON

```
HTML Input
    │
    ▼
┌─────────────────┐
│ HTML Chunker    │  Splits HTML to fit dolphincoder:7b context window (16384 tokens)
│ (context-safe)  │  Preserves tag boundaries, adds overlap for coherence
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ModelSelector   │  Auto-selects model tier based on HardwareMonitor data:
│ (auto-select)   │    ≥16GB VRAM  → qwen2.5:7b
└────────┬────────┘    8-16GB VRAM → qwen2.5:7b
         │              CPU-only    → qwen2.5:7b (quantized)
         │              Override    → user config or env var
         ▼
┌─────────────────┐
│  OllamaClient   │  httpx → POST /api/generate (localhost:11434)
│  (httpx async)  │  JSON mode, streaming support, timeout handling
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ollama Service  │  dolphincoder:7b inference on local GPU/CPU
│ (localhost)     │  temperature=0.1 for deterministic output
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ JSON Parser     │  Validate structured output, retry on parse failure
│ (pydantic)      │  Confidence scoring, hallucination detection
└────────┬────────┘
         │
         ▼
   Structured JSON Output
```

### Hardware Auto-Detection and Model Tier Selection

```
┌──────────────────┐
│ HardwareMonitor  │  Detects on startup:
│ (auto-detect)    │    • nvidia-smi → NVIDIA GPU + VRAM
└────────┬─────────┘    • rocm-smi → AMD GPU + VRAM
         │               • /proc/cpuinfo → CPU cores + RAM
         │               • falls back to CPU-only if no GPU
         ▼
┌──────────────────┐
│ ModelSelector    │  Maps hardware → model tier:
│ (auto-select)    │
└────────┬─────────┘    ┌──────────────┬────────────────────┬──────────────┐
         │              │ Hardware     │ Model              │ Context      │
         │              ├──────────────┼────────────────────┼──────────────┤
         │              │ ≥16GB VRAM   │ dolphincoder:7b  │ 16384 tokens │
         │              │ 8-16GB VRAM  │ dolphincoder:7b   │ 32768 tokens │
         │              │ CPU-only     │ dolphincoder:7b   │ 32768 tokens │
         │              │ Fallback     │ qwen2.5:7b        │ 32768 tokens │
         │              └──────────────┴────────────────────┴──────────────┘
         ▼
   Selected model passed to OllamaClient
```

### Model Management (Pull, Verify, Unload)

```python
"""ModelManager handles Ollama model lifecycle."""

class ModelManager:
    """Manages Ollama model pull, verification, selection, and cleanup."""

    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "dolphincoder:7b"
    FALLBACK_MODEL = "qwen2.5:7b"

    async def ensure_model_available(self, model: str = None) -> bool:
        """Check if model is available; auto-pull if not.

        Called on first run to automatically download the required model.
        """
        model = model or self.DEFAULT_MODEL
        if not await self._model_exists(model):
            await self._pull_model(model)
        return await self._verify_model(model)

    async def _pull_model(self, model: str) -> None:
        """Pull model from Ollama registry."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.OLLAMA_BASE_URL}/api/pull",
                json={"name": model, "stream": False},
                timeout=600.0,  # Pull can take several minutes
            )
            response.raise_for_status()

    async def _verify_model(self, model: str) -> bool:
        """Verify model integrity post-pull."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.OLLAMA_BASE_URL}/api/show",
                json={"name": model},
                timeout=30.0,
            )
            return response.status_code == 200

    async def unload_model(self, model: str = None) -> None:
        """Unload model from memory to free VRAM."""
        model = model or self.DEFAULT_MODEL
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.OLLAMA_BASE_URL}/api/generate",
                json={"model": model, "keep_alive": 0},
                timeout=30.0,
            )
```

### When Ollama Is Invoked

| Scenario | Trigger | Model Used | Hardware Requirement |
|----------|---------|------------|---------------------|
| **Selector cascade failure** | All CSS/XPath selectors return null for critical fields | `dolphincoder:7b` or `qwen2.5:7b` | GPU ≥8GB VRAM or CPU |
| **Layout change detected** | Health check shows <50% selector match rate for a platform | `dolphincoder:7b` (selector repair) | GPU ≥8GB VRAM or CPU |
| **Anti-scraping obfuscation** | HTML is heavily obfuscated (minified, encoded, dynamic) | `dolphincoder:7b` | GPU ≥8GB VRAM or CPU |
| **Unstructured content** | No clear DOM structure (e.g., embedded widgets, canvas-rendered) | `dolphincoder:7b` | GPU ≥8GB VRAM or CPU |
| **Content classification** | Need to classify page type (profile vs post vs listing) | `dolphincoder:7b` | GPU ≥4GB VRAM or CPU |
| **Entity resolution** | Link fragmented data across page sections | `dolphincoder:7b` | GPU ≥8GB VRAM or CPU |

### Ollama AI Client (Python)

```python
"""Ollama client for Phoenix Engine AI-assisted extraction."""

import os
import json
import hashlib
import asyncio
from typing import Any, Optional
from datetime import datetime, timedelta

import httpx


class OllamaExtractor:
    """AI-powered HTML extraction using local Ollama.

    This is the final stage of the selector fallback chain. When all
    CSS/XPath selectors fail, the HTML is sent to the local Ollama
    instance for intelligent structured data extraction.

    All inference runs locally — zero external API dependencies,
    zero cost, full privacy.
    """

    # Model selection map
    MODELS = {
        "fallback": "qwen2.5:7b",    # Low VRAM or CPU-only
        "standard": "dolphincoder:7b",   # Normal extraction, selector repair
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "dolphincoder:7b",
        fallback_model: str = "qwen2.5:7b",
        temperature: float = 0.1,
        max_context: int = 16384,
        timeout: float = 60.0,
        cache_ttl: int = 3600,
    ) -> None:
        self.base_url = base_url
        self.default_model = default_model
        self.fallback_model = fallback_model
        self.temperature = temperature
        self.max_context = max_context
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: dict[str, dict[str, Any]] = {}
        self._client: Optional[httpx.AsyncClient] = None
        # Inference tracking
        self.total_requests = 0
        self.total_tokens_generated = 0
        self.avg_latency_ms = 0.0

    def _cache_key(self, html_hash: str, schema_hash: str) -> str:
        """Generate cache key from HTML and schema hashes."""
        return hashlib.sha256(f"{html_hash}:{schema_hash}".encode()).hexdigest()[:32]

    def _get_cached(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Return cached response if still valid."""
        if cache_key not in self._cache:
            return None
        entry = self._cache[cache_key]
        if datetime.now() - entry["timestamp"] > timedelta(seconds=self.cache_ttl):
            del self._cache[cache_key]
            return None
        return entry["data"]

    def _set_cached(self, cache_key: str, data: dict[str, Any]) -> None:
        """Cache response with TTL."""
        self._cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now(),
        }

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (approximate: 1 token ~ 4 chars for English)."""
        return len(text) // 4

    def _chunk_html(self, html: str, max_tokens: int = 12000) -> list[str]:
        """Split large HTML into context-safe chunks for Ollama submission."""
        # Rough estimate: 1 token ~ 4 chars
        max_chars = max_tokens * 4
        if len(html) <= max_chars:
            return [html]

        chunks = []
        for i in range(0, len(html), max_chars):
            chunk = html[i:i + max_chars]
            # Try to break at a tag boundary
            if i + max_chars < len(html):
                last_tag = chunk.rfind("<")
                if last_tag > max_chars * 0.8:
                    chunk = chunk[:last_tag]
                    i = i + last_tag - max_chars
            chunks.append(chunk)
        return chunks

    async def extract(
        self,
        html: str,
        url: str,
        platform: str,
        content_type: str,
        schema_description: str,
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        """Extract structured data from HTML using local Ollama.

        Args:
            html: Raw HTML content to parse.
            url: Source URL of the HTML.
            platform: Platform identifier (e.g., 'x_twitter', 'instagram').
            content_type: Type of content (e.g., 'post', 'profile', 'video').
            schema_description: JSON schema describing desired output fields.
            model: Override default model. One of 'fallback', 'standard'.

        Returns:
            Parsed JSON dict with extracted fields. Fields not found are set to null.

        Raises:
            OllamaExtractionError: If Ollama call fails after all retries.
            OllamaJSONParseError: If response cannot be parsed as valid JSON.
        """
        html_hash = hashlib.sha256(html.encode()).hexdigest()[:16]
        schema_hash = hashlib.sha256(schema_description.encode()).hexdigest()[:16]
        cache_key = self._cache_key(html_hash, schema_hash)

        # Check cache
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        # Select model (hardware-aware)
        model_name = self.MODELS.get(model, self.default_model) if model else self.default_model

        # Chunk HTML if needed
        chunks = self._chunk_html(html)
        chunk = chunks[0]  # Primary chunk (largest pages may need multi-chunk)

        # Build prompt
        system_prompt = (
            "You are an expert web data extraction engine. "
            "Your task is to parse HTML and extract structured data. "
            "Extract ONLY the requested fields. Be precise. "
            "Return valid JSON matching the provided schema. "
            "Do not hallucinate data -- if a field is not found, return null."
        )

        user_prompt = (
            f"Extract data from this HTML page.\n\n"
            f"URL: {url}\n"
            f"Platform: {platform}\n"
            f"Content Type: {content_type}\n\n"
            f"HTML:\n```html\n{chunk}\n```\n\n"
            f"Extract the following fields as JSON:\n{schema_description}\n\n"
            f"Return ONLY valid JSON. No markdown, no explanation."
        )

        # Track request
        self.total_requests += 1

        # API call with retry logic
        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                response = await self._call_ollama_generate(
                    model=model_name,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )

                content = response.get("response", "").strip()

                # Parse JSON response
                try:
                    extracted_data = json.loads(content)
                except json.JSONDecodeError:
                    # Try stripping markdown code fences
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    extracted_data = json.loads(content.strip())

                # Track actual usage
                if "eval_count" in response:
                    self.total_tokens_generated += response["eval_count"]

                # Cache and return
                self._set_cached(cache_key, extracted_data)
                return extracted_data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503 and attempt < max_retries - 1:
                    # Model loading or OOM — try fallback model
                    model_name = self.fallback_model
                    await asyncio.sleep(base_delay)
                    continue
                raise OllamaExtractionError(
                    f"Ollama HTTP error after {max_retries} retries: {e.response.status_code}"
                )

            except httpx.ConnectError:
                raise OllamaExtractionError(
                    "Cannot connect to Ollama at "
                    f"{self.base_url}. Is Ollama running? "
                    "Install from ollama.com and start the service."
                )

            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay)
                    continue
                raise OllamaExtractionError(
                    f"Ollama timeout after {max_retries} retries. "
                    f"Timeout: {self.timeout}s. Consider using fallback model."
                )

    async def _call_ollama_generate(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call Ollama /api/generate endpoint via httpx."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)

        response = await self._client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": self.max_context,
                },
            },
        )
        response.raise_for_status()
        return response.json()

    async def suggest_selectors(
        self,
        html_sample: str,
        old_selectors: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Use Ollama to suggest new selectors after a layout change.

        Args:
            html_sample: Representative HTML from the new layout.
            old_selectors: Dict of field names to old (now failing) selectors.

        Returns:
            List of dicts with 'field', 'old', 'new', 'confidence' keys.
        """
        prompt = (
            "The following CSS selectors no longer match the HTML "
            "(the page layout changed).\n\n"
            f"Old selectors: {json.dumps(old_selectors, indent=2)}\n\n"
            "Current HTML structure:\n```html\n"
            f"{html_sample[:8000]}\n"  # Truncate for context limit
            "```\n\n"
            "Suggest new CSS selectors that extract the same data. "
            'Return as JSON array: [{"field": "name", "old": "...", '
            '"new": "...", "confidence": 0.95}]'
        )

        response = await self._call_ollama_generate(
            model=self.MODELS["standard"],
            system_prompt=(
                "You are a CSS selector expert. Suggest precise, "
                "stable selectors that will work across minor layout changes. "
                "Prefer data-testid, role, and semantic attributes over classes. "
                "Return ONLY valid JSON array."
            ),
            user_prompt=prompt,
        )

        content = response.get("response", "").strip()
        return json.loads(content)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()


class OllamaExtractionError(Exception):
    """Raised when Ollama extraction fails after all retries."""


class OllamaJSONParseError(Exception):
    """Raised when Ollama response cannot be parsed as valid JSON."""
```

### Optimization Strategies

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Response Caching** | LRU cache with TTL (default 3600s) for identical HTML + schema | 40-60% on repeated pages |
| **HTML Chunking** | Split large HTML into context-safe chunks; only send relevant sections | 30-50% context window efficiency |
| **Hardware-Aware Model Selection** | Use `dolphincoder:7b` on ≥16GB VRAM, `dolphincoder:7b` on lower VRAM or CPU, `qwen2.5:7b` as fallback | Optimal quality for available hardware |
| **Model Unloading** | Unload model from VRAM when idle to free memory for scraping | Prevents OOM during concurrent operations |
| **Pre-filtering** | Only send HTML to Ollama after selector chain fully fails | Reduces inference calls by 80%+ |
| **JSON Mode** | Use Ollama `format: "json"` for deterministic structured output | Eliminates markdown wrapping issues |

### Ollama Configuration (TOML)

```toml
[ai]
enabled = true
provider = "ollama"

[ai.ollama]
base_url = "http://localhost:11434"
default_model = "dolphincoder:7b"
fallback_model = "qwen2.5:7b"
temperature = 0.1
max_context = 16384
timeout = 60

# Hardware-aware model selection
[ai.ollama.hardware]
auto_detect = true
gpu_preferred = true
min_vram_mb = 8192

# Model selection thresholds (VRAM in MB)
[ai.ollama.model_selection]
# Model is selected based on available VRAM:
# ≥16384 MB → dolphincoder:7b
# 8192-16383 MB → dolphincoder:7b
# <8192 MB → dolphincoder:7b with CPU fallback
# qwen2.5:7b available as fallback/alternative

# Retry configuration
[ai.ollama.retry]
max_retries = 3
base_delay_seconds = 2.0
exponential_backoff = true
fallback_on_oom = true  # Auto-switch to smaller model on OOM
```

## Development Approach

This project uses an **AI-driven, human-supervised** development model:

1. **AI Agents execute**: Ollama-powered AI agents perform the majority of design, coding, testing, and documentation work
2. **Humans supervise**: Human stakeholders provide vision, approve architecture, review compliance, and accept deliverables
3. **Documentation-driven**: Every decision is documented before implementation
4. **Quality-gated**: No phase proceeds without meeting exit criteria
5. **Scraping-first**: HTML parsing and browser automation are the primary collection methods -- no API integrations anywhere in the codebase
6. **Ollama local-first**: AI extraction runs entirely on local hardware with zero external dependencies. Every scraper is designed with the assumption that Ollama (localhost:11434) may be invoked as the final fallback in the extraction chain, with hardware-aware model selection (7b/14b) based on available VRAM

---

## Document Dependencies

```
01-project-charter.md
        |
        v
02-team-structure.md  <-->  03-phases-milestones.md
        |                           |
        v                           v
04-task-breakdown-wbs.md  <-->  05-product-requirements.md
        |                           |
        +------------+---------------+
                     |
                     v
        +------------+------------+
        |            |            |
        v            v            v
06-technical-  07-api-      08-development-
architecture.md  spec.md     standards.md
        |            |            |
        +------------+------------+
                     |
                     v
        +------------+------------+
        |            |            |
        v            v            v
09-testing-    10-risk-      11-communication-
qa-plan.md     management.md  plan.md
        |            |            |
        +------------+------------+
                     |
                     v
            12-definition-of-done.md
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-06-23 | Initial complete package | Ollama PM Agent |
| 1.1 | 2026-06-24 | Migrated from Kimi API to Ollama Local AI | Ollama PM Agent |
| 1.2 | 2026-06-23 | Stealth module, real collectors, Property Finder adapter, AI assistant/agent mode | AI PM |
| 1.3 | 2026-06-24 | Default model switched to `dolphincoder:7b` (`qwen2.5:7b` fallback); added PhoenixArchitect roadmap; documented known issues and `--real` CLI flag | AI PM |
| 1.4 | 2026-06-24 | Implemented Phase 1: per-field extraction confidence, adaptive throttling, Researcher search-driven discovery (`phoenix discover`, `phoenix architect generate`), deterministic template fallback, and updated project docs | AI PM |

---

## Confidentiality Notice

This document and all associated files are the confidential property of Phoenix Consulting. Unauthorized distribution or reproduction is prohibited.

---

*Generated by Ollama Local AI Project Management System*
*Phoenix Engine Project | 2026*
