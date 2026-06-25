# Project Phases & Milestones: Phoenix Engine

## Universal Web Scraping Engine — v1.0 MVP Delivery Plan | Powered by Ollama (Local AI)

---

| **Field** | **Value** |
|-----------|-----------|
| **Project** | Phoenix Engine |
| **Document** | Phases & Milestones Plan |
| **Version** | 1.0 |
| **Date** | July 2025 |
| **Classification** | Confidential — Internal Use Only |
| **Owner** | AI Project Manager (AI-PM-01) |
| **Approver** | Human Product Owner (Human-PO-01) |
| **Total Duration** | 18 Weeks (MVP) + Ongoing (Post-Launch) |

---

## Document Overview

This document defines the phased execution plan for Phoenix Engine v1.0. It serves as the operational playbook for AI agent execution — every task, criterion, and dependency is specified with sufficient precision for autonomous agent action. Each phase includes: objectives, deliverables, task breakdown, entry criteria, exit criteria, dependencies, risk factors, and role assignments.

**Phase Summary Table:**

| **Phase** | **Name** | **Weeks** | **Duration** | **Status** | **Primary Deliverables** | **Critical Path** |
|-----------|----------|-----------|--------------|------------|-------------------------|-------------------|
| Phase 0 | Foundation | 1–2 | 2 weeks | ✅ Completed | Architecture, repo, CI/CD, standards | ✅ Yes |
| Phase 1 | Core Engine | 3–5 | 3 weeks | ✅ Completed | Pipeline, normalizer with confidence scoring, error handler, logger | ✅ Yes |
| Phase 2 | Platform Adapters | 6–9 | 4 weeks | ✅ Completed | 6 built-in social/generic adapters + plugin framework | ✅ Yes |
| Phase 2.5 | PhoenixArchitect | 9–10 | 1–2 weeks | ✅ Completed | Autonomous adapter generation: browse → inspect → code → critic, persisted to disk | ✅ Yes |
| Phase 3 | **Local AI Intelligence Layer (Ollama)** | 10–11 | 2 weeks | ✅ Completed | **Ollama** local AI extraction (`dolphincoder:7b`), model management, hardware-aware selection, selector repair, classifier, extraction confidence; entity resolution remains planned | ⬜ Parallel |
| Phase 4 | Infrastructure | 12–13 | 2 weeks | ✅ Completed | Sessions, storage, archive, adaptive rate control, stealth/anti-detection module | ⬜ Parallel |
| Phase 5 | Developer Experience | 14–15 | 2 weeks | ✅ Completed | CLI polish, SDK, docs, quick-start, AI coding assistant (`scripts/scraping_assistant.py`) | ⬜ Parallel |
| Phase 6 | Quality & Hardening | 16–17 | 2 weeks | 🔄 In Progress | Operational automation (learning memory, change detection, fixture generation); perf testing, security audit, compliance; 559 tests passing, ~91% coverage | ✅ Yes |
| Phase 7 | Release & Launch | 18 | 1 week | ⬜ Planned | PyPI package, docs, marketing, community | ✅ Yes |
| Phase 8 | Post-Launch | Ongoing | Continuous | ⬜ Planned | Monitoring, support, v1.x planning | Ongoing |
| Phase 9 | PhoenixArchitect | 19–21 | 3 weeks | ✅ Completed | Autonomous adapter generation: discover → explore → inspect → code → critic, persisted to disk | ✅ Yes |

---

## Phase 0 — Foundation (Weeks 1–2)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Finalize and approve system architecture | ADR-001 signed off by AI Tech Lead + Human PO |
| O2 | Establish development environment | All agents can execute code within 1 hour of onboarding |
| O3 | Deploy CI/CD pipeline with quality gates | Every PR triggers lint, test, coverage, and security checks |
| O4 | Define and document coding standards | Zero style deviations in first 100 PRs |
| O5 | Onboard all AI agents to project context | Each agent passes project-knowledge quiz (≥90%) |
| O6 | Define target hardware profile for Ollama deployment | GPU/CPU requirements documented, model tier selection criteria defined |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | Architecture Decision Record (ADR-001) | Markdown | AI-TL-01 | `/docs/architecture/ADR-001-core-architecture.md` |
| D2 | Development environment setup guide | Markdown | AI-DO-01 | `/docs/development/setup.md` |
| D3 | CI/CD pipeline configuration | YAML (GitHub Actions) | AI-DO-01 | `/.github/workflows/` |
| D4 | Coding standards document | Markdown | AI-TL-01 | `/docs/development/standards.md` |
| D5 | Project repository structure | Git repo | AI-DO-01 | GitHub repository |
| D6 | Hello-world integration test | Python test file | AI-QA-01 | `/tests/integration/test_hello_world.py` |
| D7 | Agent onboarding checklist | Markdown | AI-PM-01 | `/docs/team/onboarding.md` |

### Task Breakdown

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Define module structure and interfaces | AI-TL-01 | 2d | — |
| T2 | Select core dependencies (httpx, playwright, pydantic, etc.) | AI-TL-01 | 1d | T1 |
| T3 | Write ADR-001 with rationale | AI-TL-01 | 2d | T1, T2 |
| T4 | Initialize GitHub repository | AI-DO-01 | 0.5d | — |
| T5 | Set up Python project structure (pyproject.toml, src layout) | AI-DO-01 | 1d | T4 |
| T6 | Configure linting (ruff), formatting (black), type checking (mypy) | AI-DO-01 | 1d | T5 |
| T7 | Configure test framework (pytest) with coverage | AI-DO-01 | 1d | T5 |
| T8 | Configure CI pipeline (lint → test → coverage → security) | AI-DO-01 | 2d | T6, T7 |
| T9 | Configure CD pipeline (PyPI publish on tag) | AI-DO-01 | 1d | T8 |
| T10 | Write hello-world integration test | AI-QA-01 | 0.5d | T7 |
| T11 | Write coding standards document | AI-TL-01 | 1d | T3 |
| T12 | Create agent onboarding materials | AI-PM-01 | 1d | All above |
| T13 | Conduct architecture review meeting | AI-PM-01 | 0.5d | T3 |
| T14 | Define Ollama target hardware profile (GPU/CPU requirements) | AI-TL-01 | 0.5d | T3 |
| T15 | Document Ollama deployment requirements | AI-TL-01 | 0.5d | T14 |

### Entry Criteria
- Project charter approved and signed
- GitHub organization and repository names finalized
- All AI agent roles assigned and provisioned with compute access
- Human Product Owner confirmed availability for weekly syncs

### Exit Criteria (Phase Gate M0→M1)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | ADR-001 approved | Review + sign-off in PR | AI-TL-01 and Human-PO-01 approval |
| EC2 | CI pipeline passing | GitHub Actions green | All jobs green on latest commit |
| EC3 | Hello-world test passes | pytest execution | Exit code 0, coverage report generated |
| EC4 | All agents onboarded | Onboarding checklist complete | 100% agents signed off |
| EC5 | Coding standards published | Document in repo | Merged to `main` |
| EC6 | Ollama hardware profile defined | Document in repo | GPU/CPU requirements documented, model tiers defined |

### Dependencies
- **External**: GitHub organization access; PyPI account credentials (for CD setup)
- **Internal**: Project charter approval (Document 01)

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| Architecture decision delays | Medium | High | Pre-align on 3 architecture options; timebox decision to 3 days |
| CI service limits | Low | Medium | Monitor GitHub Actions minutes; fallback to self-hosted runners |
| Agent onboarding friction | Medium | Medium | Detailed setup scripts; containerized dev environment |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Coordination, scheduling, gate preparation, stakeholder sync |
| AI-TL-01 | Architecture, standards, technical decisions |
| AI-DO-01 | Repository, CI/CD, tooling |
| AI-QA-01 | Test framework setup, first test |
| AI-CO-01 | Review architecture for compliance implications |
| Human-PO-01 | Approve ADR-001 |

---

## Phase 1 — Core Engine (Weeks 3–5)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Universal URL receiver accepts and validates any input URL | 100% valid URLs accepted; 100% invalid URLs rejected with clear error |
| O2 | Mode selector auto-detects optimal collection strategy | Correct mode selected in ≥95% of test cases |
| O3 | Output normalizer produces consistent structured data | 100% adapter outputs conform to unified schema |
| O4 | Error handler provides actionable diagnostics | ≥90% of errors include remediation guidance |
| O5 | Logging system supports debug, audit, and telemetry use cases | All pipeline stages emit structured logs |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | URL receiver module | Python module | AI-BE-01 | `/src/phoenix/receiver.py` |
| D2 | Mode selector engine | Python module | AI-BE-01 | `/src/phoenix/selector.py` |
| D3 | Output normalizer | Python module | AI-BE-01 | `/src/phoenix/normalizer.py` |
| D4 | Error handler & diagnostics | Python module | AI-BE-01 | `/src/phoenix/errors.py` |
| D5 | Structured logging system | Python module | AI-BE-01 | `/src/phoenix/logging.py` |
| D6 | Unified output schema (JSON Schema) | JSON Schema | AI-TL-01 | `/schemas/output-v1.json` |
| D7 | Pipeline orchestrator | Python module | AI-BE-01 | `/src/phoenix/pipeline.py` |
| D8 | Core engine test suite | Python tests | AI-QA-01 | `/tests/core/` |
| D9 | Pipeline integration tests | Python tests | AI-QA-01 | `/tests/integration/test_pipeline.py` |

### Task Breakdown

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Design URL validation and parsing | AI-BE-01 | 1d | ADR-001 |
| T2 | Implement URL receiver with platform detection | AI-BE-01 | 2d | T1 |
| T3 | Define unified output schema (JSON Schema) | AI-TL-01 | 1d | — |
| T4 | Implement mode selector (direct/browser/API) | AI-BE-01 | 3d | T2 |
| T5 | Implement output normalizer | AI-BE-01 | 2d | T3 |
| T6 | Implement structured error hierarchy | AI-BE-01 | 2d | — |
| T7 | Implement error diagnostics formatter | AI-BE-01 | 2d | T6 |
| T8 | Implement structured logging | AI-BE-01 | 1d | — |
| T9 | Implement pipeline orchestrator (4-step flow) | AI-BE-01 | 3d | T2, T4, T5 |
| T10 | Write unit tests for all core modules | AI-QA-01 | 3d | T2-T9 |
| T11 | Write pipeline integration tests | AI-QA-01 | 2d | T9 |
| T12 | Performance benchmark baseline | AI-QA-01 | 1d | T9 |
| T13 | Document core engine API | AI-TW-01 | 2d | T2-T9 |

### Entry Criteria
- Phase 0 exit criteria all passed (M1 gate approved)
- ADR-001 accessible and understood by all dev agents
- CI pipeline operational and blocking merges on failure

### Exit Criteria (Phase Gate M1→M2)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | 4-step pipeline functional | Integration test suite | 100% tests passing |
| EC2 | Any supported URL processes end-to-end | Manual + automated test | 7/7 platform URL types succeed |
| EC3 | Test coverage ≥70% | pytest-cov report | Line coverage ≥70% |
| EC4 | Output schema validation passes | Schema validation tests | 100% outputs validate |
| EC5 | Error messages are actionable | Review sample of error outputs | ≥90% include guidance |
| EC6 | Documentation complete | Review | All public functions documented |

### Dependencies
- **Phase 0**: Architecture, CI/CD, standards (must be complete)
- **External**: None blocking

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| Schema design instability | Medium | High | Lock schema v1.0 at mid-phase; changes require TL approval |
| Mode selector accuracy | Medium | High | Extensive test matrix; fallback to safe default (browser) |
| Pipeline race conditions | Low | High | Comprehensive integration tests; stress testing |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Track progress, unblock tasks, gate preparation |
| AI-TL-01 | Schema design, code review, architecture compliance |
| AI-BE-01 | All core engine implementation |
| AI-QA-01 | Test design, test implementation, coverage tracking |
| AI-TW-01 | Core engine API documentation |
| AI-CO-01 | Review data handling in pipeline for compliance |

---

## Phase 2 — Platform Adapters (Weeks 6–9)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Instagram adapter extracts public profiles, posts, comments | ≥95% extraction success on public content |
| O2 | X/Twitter adapter collects tweets, profiles, threads | ≥95% extraction success on public content |
| O3 | TikTok adapter extracts video metadata, comments, profiles | ≥95% extraction success on public content |
| O4 | LinkedIn adapter collects public company pages, posts, jobs | ≥95% extraction success on public content |
| O5 | Facebook adapter extracts public pages, posts, events | ≥95% extraction success on public content |
| O6 | YouTube adapter collects video metadata, comments, transcripts | ≥95% extraction success on public content |
| O7 | Generic Web adapter handles any URL fallback | ≥90% extraction success on article-type content |
| O8 | Plugin system framework enables third-party adapters | Working example plugin built in <2 hours |
| O9 | All adapters have ≥80% test coverage | pytest-cov report |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | Instagram adapter | Python module | AI-BE-02 | `/src/phoenix/adapters/instagram.py` |
| D2 | X/Twitter adapter | Python module | AI-BE-02 | `/src/phoenix/adapters/twitter.py` |
| D3 | TikTok adapter | Python module | AI-BE-02 | `/src/phoenix/adapters/tiktok.py` |
| D4 | LinkedIn adapter | Python module | AI-BE-02 | `/src/phoenix/adapters/linkedin.py` |
| D5 | Facebook adapter | Python module | AI-BE-03 | `/src/phoenix/adapters/facebook.py` |
| D6 | YouTube adapter | Python module | AI-BE-03 | `/src/phoenix/adapters/youtube.py` |
| D7 | Generic Web adapter | Python module | AI-BE-03 | `/src/phoenix/adapters/generic_web.py` |
| D8 | Plugin system framework | Python package | AI-BE-03 | `/src/phoenix/plugins/` |
| D9 | Adapter base class & interfaces | Python module | AI-TL-01 | `/src/phoenix/adapters/base.py` |
| D10 | Adapter integration tests | Python tests | AI-QA-01 | `/tests/adapters/` |
| D11 | Plugin example + guide | Python + Markdown | AI-BE-03, AI-TW-01 | `/examples/plugin/` |
| D12 | Generated adapter persistence | Python module + package | AI-BE-03 | `/src/phoenix/adapters/generated/` |

### Task Breakdown

**Week 6 — Adapter Foundation + Social (Batch 1)**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Design adapter base class and interface | AI-TL-01 | 1d | Phase 1 complete |
| T2 | Implement adapter registration system | AI-BE-01 | 1d | T1 |
| T3 | Implement Instagram adapter | AI-BE-02 | 3d | T1, T2 |
| T4 | Implement X/Twitter adapter | AI-BE-02 | 3d | T1, T2 |
| T5 | Write Instagram + X tests | AI-QA-01 | 2d | T3, T4 |
| T6 | Document Instagram + X adapters | AI-TW-01 | 1d | T3, T4 |

**Week 7 — Social (Batch 2)**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T7 | Implement TikTok adapter | AI-BE-02 | 3d | T1, T2 |
| T8 | Implement LinkedIn adapter | AI-BE-02 | 3d | T1, T2 |
| T9 | Write TikTok + LinkedIn tests | AI-QA-01 | 2d | T7, T8 |
| T10 | Document TikTok + LinkedIn adapters | AI-TW-01 | 1d | T7, T8 |

**Week 8 — Web Adapters**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T11 | Implement Facebook adapter | AI-BE-03 | 3d | T1, T2 |
| T12 | Implement YouTube adapter | AI-BE-03 | 3d | T1, T2 |
| T13 | Implement Generic Web adapter | AI-BE-03 | 3d | T1, T2 |
| T14 | Write Facebook + YouTube + Generic tests | AI-QA-01 | 2d | T11-T13 |
| T15 | Document Facebook + YouTube + Generic adapters | AI-TW-01 | 1d | T11-T13 |

**Week 9 — Plugin System + Integration**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T16 | Design plugin SDK architecture | AI-TL-01 | 1d | All adapters |
| T17 | Implement plugin loader and registry | AI-BE-03 | 2d | T16 |
| T18 | Implement plugin base classes and decorators | AI-BE-03 | 1d | T16 |
| T19 | Build example plugin (weather data adapter) | AI-BE-03 | 1d | T17, T18 |
| T20 | Write plugin system tests | AI-QA-01 | 1d | T17-T19 |
| T21 | Write plugin development guide | AI-TW-01 | 2d | T16-T19 |
| T22 | Full adapter integration test run | AI-QA-01 | 1d | All above |
| T23 | Coverage analysis and gap remediation | AI-QA-01 | 1d | T22 |

### Entry Criteria
- Phase 1 exit criteria all passed (M2 gate approved)
- Core pipeline functional with schema locked
- Adapter interface design approved by AI Tech Lead

### Exit Criteria (Phase Gate M2→M3)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | All 7 adapters functional | Integration tests | 100% passing |
| EC2 | Test coverage ≥80% per adapter | pytest-cov per-module | All adapters ≥80% |
| EC3 | Plugin system functional | Example plugin test | Build + register + execute in <2h |
| EC4 | All adapters produce valid normalized output | Schema validation | 100% outputs valid |
| EC5 | Adapter documentation complete | Review | All adapters documented |
| EC6 | No P0 or P1 bugs open | Bug tracker review | Zero open P0/P1 |

### Dependencies
- **Phase 1**: Core engine pipeline (must be complete)
- **External**: Platform API documentation access; test accounts for each platform

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| Platform anti-bot measures | High | Critical | Multi-mode extraction; rate limiting; respectful headers; monitoring |
| API changes mid-development | Medium | High | Weekly API health checks; adapter versioning; rapid patch process |
| Test flakiness (browser-based) | High | Medium | Retry logic; test isolation; mock fallback for CI |
| Adapter interface instability | Medium | High | Lock interface at Week 6; changes require TL review |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Coordinate parallel adapter work, resolve blockers |
| AI-TL-01 | Interface design, cross-adapter consistency, code review |
| AI-BE-02 | Instagram, X, TikTok, LinkedIn adapters |
| AI-BE-03 | Facebook, YouTube, Generic Web adapters; Plugin SDK |
| AI-BE-01 | Adapter registration; pipeline integration |
| AI-QA-01 | Adapter tests; integration tests; coverage tracking |
| AI-TW-01 | Adapter documentation; plugin guide |
| AI-CO-01 | Per-adapter ToS compliance review; data handling audit |

---

## Phase 3 — Local AI Intelligence Layer (Ollama) (Weeks 10–11)

### Phase Overview

Phase 3 integrates **Ollama (Local AI)** as the AI extraction engine for Phoenix Engine. Ollama runs entirely on local hardware at `http://localhost:11434` with the default model `dolphincoder:7b` and fallback `qwen2.5:7b`, providing intelligent HTML parsing and structured data extraction with zero external API dependencies, zero cost, and full privacy.

When standard CSS selectors and XPath fail (due to site layout changes or unknown page structures), raw HTML is sent to the local Ollama instance for intelligent parsing and structured data extraction. Ollama is also used for selector repair suggestions, content classification, and cross-platform entity resolution.

**Prerequisite**: Ollama Infrastructure Setup (can be completed as a Phase 0 task or pre-Phase-1):
- Ollama installed and running on target hardware
- `dolphincoder:7b` model pulled and verified (with `qwen2.5:7b` as fallback)
- GPU passthrough configured (if using Docker) or local installation confirmed
- Hardware profile documented (GPU VRAM or CPU-only)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Ollama-powered extraction works for unknown page types | ≥80% success on novel page structures |
| O2 | Smart fallback system cascades through extraction methods | Graceful degradation: selectors → browser → Ollama (local AI) → error |
| O3 | Ollama content classifier categorizes extracted content | ≥90% accuracy on type classification |
| O4 | Ollama entity resolution links related entities across platforms | ≥85% confidence on cross-platform matches |
| O5 | Ollama service auto-detection and setup works on fresh install | Auto-detection succeeds in <30s, auto-pull completes in <10min |
| O6 | Model auto-pull on first run completes successfully | `dolphincoder:7b` downloaded and verified without manual intervention |
| O7 | Hardware-aware model selection picks correct tier | Correct model (7b/14b) selected based on available VRAM in 100% of test cases |
| O8 | Ollama selector repair automatically fixes broken selectors | ≥70% of broken selectors repaired without human intervention |
| O9 | OOM handling and model fallback work under resource pressure | Graceful fallback to smaller model or CPU when VRAM exhausted |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | Ollama AI extraction module (`OllamaAIEngine`) | Python module | AI-BE-01 | `/src/phoenix/intelligence/ollama_engine.py` |
| D2 | Ollama HTTP client wrapper (`OllamaClient`) | Python module | AI-BE-01 | `/src/phoenix/intelligence/ollama_client.py` |
| D3 | ModelManager (pull, verify, select, unload) | Python module | AI-BE-01 | `/src/phoenix/intelligence/model_manager.py` |
| D4 | HardwareMonitor (GPU/CPU detection, VRAM tracking) | Python module | AI-BE-01 | `/src/phoenix/intelligence/hardware_monitor.py` |
| D5 | ModelSelector (auto-select 7b/14b based on hardware) | Python module | AI-BE-01 | `/src/phoenix/intelligence/model_selector.py` |
| D6 | Smart fallback orchestrator | Python module | AI-BE-01 | `/src/phoenix/intelligence/fallback.py` |
| D7 | Ollama content classifier | Python module | AI-BE-01 | `/src/phoenix/intelligence/classifier.py` |
| D8 | Ollama entity resolution module | Python module | AI-BE-01 | `/src/phoenix/intelligence/entities.py` |
| D9 | Ollama selector repair module | Python module | AI-BE-01 | `/src/phoenix/intelligence/selector_repair.py` |
| D10 | HTML chunker for Ollama context window limits | Python module | AI-BE-01 | `/src/phoenix/intelligence/html_chunker.py` |
| D11 | AI response cache | Python module | AI-BE-01 | `/src/phoenix/intelligence/ai_cache.py` |
| D12 | Ollama prompt templates | Python | AI-BE-01 | `/src/phoenix/intelligence/prompts/` |
| D13 | Intelligence layer tests | Python tests | AI-QA-01 | `/tests/intelligence/` |
| D14 | Ollama feature documentation | Markdown | AI-TW-01 | `/docs/features/ollama-ai-extraction.md` |

### Task Breakdown

**Week 10 — Ollama Core Integration**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Design Ollama extraction prompt chain for dolphincoder:7b | AI-BE-01 | 1d | Phase 2 adapters |
| T2 | Implement Ollama HTTP client wrapper (httpx → localhost:11434) | AI-BE-01 | 1d | T1 |
| T3 | Implement ModelManager (model pull, verify, select, unload) | AI-BE-01 | 1d | T2 |
| T4 | Implement HardwareMonitor (GPU/CPU detection, VRAM tracking) | AI-BE-01 | 1d | T2 |
| T5 | Implement ModelSelector (auto-select 7b/14b based on available VRAM) | AI-BE-01 | 1d | T3, T4 |
| T6 | Implement HTML chunker for Ollama context window limits (16384 tokens) | AI-BE-01 | 1d | T2 |
| T7 | Implement Ollama extraction with structured JSON output | AI-BE-01 | 2d | T2, T5, T6 |
| T8 | Implement model auto-pull on first run | AI-BE-01 | 0.5d | T3 |
| T9 | Implement Ollama selector repair (broken → suggested new) | AI-BE-01 | 1d | T2 |
| T10 | Implement AI response cache (reduce redundant inference) | AI-BE-01 | 1d | T2 |
| T11 | Implement smart fallback orchestrator (selectors → Ollama → error) | AI-BE-01 | 1d | T7, T9 |
| T12 | Write Ollama integration unit tests (with mock Ollama server) | AI-QA-01 | 2d | T7-T11 |

**Week 11 — Ollama Classifier + Entity Resolution + Hardware Validation**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T13 | Implement Ollama content type classifier | AI-BE-01 | 2d | T7 |
| T14 | Implement Ollama entity extraction and cross-platform resolution | AI-BE-01 | 2d | T7 |
| T15 | Implement OOM handling and model fallback (7b → 7b → CPU) | AI-BE-01 | 1d | T5, T7 |
| T16 | Write classifier, entity, and OOM handling tests | AI-QA-01 | 2d | T13-T15 |
| T17 | Hardware compatibility matrix testing (GPU 8GB/16GB, CPU-only) | AI-QA-01 | 1d | T4, T5 |
| T18 | Inference accuracy validation on local deployment | AI-QA-01 | 1d | T7 |
| T19 | Document Ollama features and hardware requirements | AI-TW-01 | 1d | All above |

### Entry Criteria
- Phase 2 exit criteria passed (M3 gate approved)
- Ollama installed and running on target hardware (`http://localhost:11434` accessible)
- `dolphincoder:7b` model pulled and verified (`ollama show dolphincoder:7b` succeeds); `qwen2.5:7b` fallback available
- Target hardware profile defined (GPU VRAM available or CPU-only mode confirmed)
- `httpx` already in project dependencies (no additional HTTP client needed)
- AI response caching strategy documented (in-memory or Redis)
- Ollama service auto-detection mechanism designed (check localhost:11434 on startup)

### Exit Criteria (Phase Gate M3→M4)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | Ollama fallback extracts structured data | Test on 20 novel pages | ≥80% structured output rate |
| EC2 | Ollama selector repair fixes broken selectors | 10 known-broken selector scenarios | ≥70% auto-repaired |
| EC3 | Smart fallback cascades correctly | Forced failure tests | selectors → browser → Ollama (local AI) → error |
| EC4 | Ollama content classifier accuracy | Labeled test set | ≥90% accuracy |
| EC5 | Ollama entity resolution confidence | Cross-platform entity pairs | ≥85% match confidence |
| EC6 | Ollama auto-detection works on fresh install | Test on clean environment | Auto-detection succeeds in <30s |
| EC7 | Model auto-pull completes successfully | Clean environment test | `dolphincoder:7b` downloaded and ready in <10min |
| EC8 | Hardware-aware selection picks correct tier | Test on 3 hardware profiles (8GB GPU, 16GB GPU, CPU-only) | Correct model (7b/14b) selected in 100% of cases |
| EC9 | AI response cache functional | Cache hit/miss test | Hit rate ≥30% on repeated pages |
| EC10 | Tests passing with ≥80% coverage | pytest report | All green, coverage ≥80% |
| EC11 | OOM handling triggers graceful fallback | Simulated memory pressure test | Falls back to CPU mode or skips AI |
| EC12 | Ollama error handling verified | Simulated service failure tests | Graceful fallback on service down/timeout/OOM/error |
| EC13 | Inference latency within target | Benchmark on reference hardware | ≤10s per extraction on target GPU, ≤30s on CPU |

### Dependencies
- **Phase 2**: All adapters complete (intelligence wraps around them)
- **External**: Ollama installed and running on target hardware (`http://localhost:11434`)
- **Hardware**: GPU with ≥8GB VRAM recommended for 7b model; CPU-only supported with 7b model

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| Ollama service not running on target machine | Medium | Critical | Auto-detection on startup; clear error message with setup instructions; Docker Compose option |
| Insufficient VRAM for selected model | Medium | High | HardwareMonitor detects VRAM; ModelSelector auto-picks smaller model; graceful CPU fallback |
| Ollama model download failure or corruption | Low | High | Model verification post-pull; retry with resume; fallback to CPU mode if 7b fails |
| Local 7b model JSON output inconsistency | High | Medium | Structured output mode (`format: "json"`); Pydantic validation; retry with adjusted prompt; fallback to `qwen2.5:7b` if `dolphincoder:7b` drifts |
| Ollama inference latency too high (>30s) | Medium | Medium | Timeout handling (60s default); async processing; hardware upgrade guidance; model tier fallback |
| Ollama API compatibility changes | Low | Medium | Abstracted client wrapper; Ollama version pinning; monitoring Ollama releases |
| AI extraction accuracy (hallucination) | Medium | High | Low temperature (0.1); confidence scores; human-verified golden test set |
| GPU driver incompatibility | Low | High | Test matrix covers NVIDIA/AMD; CPU fallback always available; Docker GPU passthrough option |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Ollama deployment coordination, hardware requirement tracking, inference latency monitoring |
| AI-TL-01 | Ollama architecture review, fallback chain design, model selection strategy, hardware profile design |
| AI-BE-01 | All Ollama intelligence layer implementation — client, ModelManager, HardwareMonitor, ModelSelector, extraction, repair, classifier |
| AI-QA-01 | Ollama integration tests; mock Ollama server testing; hardware compatibility matrix validation; inference accuracy testing |
| AI-TW-01 | Ollama feature documentation; prompt template guide; hardware requirements guide |
| AI-CO-01 | Local AI privacy review (data never leaves machine); PII handling in prompts; hardware data handling compliance |

---

## Phase 4 — Infrastructure (Weeks 12–13)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Session manager securely stores and retrieves credentials | AES-256 encryption; keychain integration; zero plaintext |
| O2 | Storage layer supports local (SQLite) and PostgreSQL backends | Both backends pass identical test suite |
| O3 | Source archive system saves raw source with extracted data | 100% of extractions optionally archived |
| O4 | Rate controller enforces per-platform polite limits | No rate limit violations; user-customizable |
| O5 | Configuration management supports env vars, files, and code | All config sources tested |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | Session manager | Python module | AI-DO-01 | `/src/phoenix/infrastructure/sessions.py` |
| D2 | Credential vault (encrypted storage) | Python module | AI-DO-01 | `/src/phoenix/infrastructure/vault.py` |
| D3 | Storage abstraction layer | Python module | AI-DO-01 | `/src/phoenix/infrastructure/storage/` |
| D4 | SQLite backend | Python module | AI-DO-01 | `/src/phoenix/infrastructure/storage/sqlite.py` |
| D5 | PostgreSQL backend | Python module | AI-DO-01 | `/src/phoenix/infrastructure/storage/postgres.py` |
| D6 | Source archive system | Python module | AI-DO-01 | `/src/phoenix/infrastructure/archive.py` |
| D7 | Rate controller | Python module | AI-DO-01 | `/src/phoenix/infrastructure/rate_controller.py` |
| D8 | Configuration manager | Python module | AI-DO-01 | `/src/phoenix/infrastructure/config.py` |
| D9 | Infrastructure tests | Python tests | AI-QA-01 | `/tests/infrastructure/` |
| D10 | Infrastructure documentation | Markdown | AI-TW-01 | `/docs/infrastructure/` |

### Task Breakdown

**Week 12 — Sessions, Storage, Archive**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Design storage abstraction interface | AI-TL-01 | 0.5d | — |
| T2 | Implement credential vault (encryption) | AI-DO-01 | 2d | — |
| T3 | Implement session manager (CRUD, expiry) | AI-DO-01 | 2d | T2 |
| T4 | Implement storage abstraction layer | AI-DO-01 | 1d | T1 |
| T5 | Implement SQLite backend | AI-DO-01 | 1d | T4 |
| T6 | Implement PostgreSQL backend | AI-DO-01 | 2d | T4 |
| T7 | Implement source archive system | AI-DO-01 | 2d | T5 |
| T8 | Write session + storage tests | AI-QA-01 | 2d | T2-T7 |

**Week 13 — Rate Control + Configuration**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T9 | Implement rate controller with per-platform defaults | AI-DO-01 | 2d | — |
| T10 | Implement user-customizable rate limits | AI-DO-01 | 1d | T9 |
| T11 | Implement configuration manager (env/file/code) | AI-DO-01 | 2d | — |
| T12 | Write rate controller + config tests | AI-QA-01 | 2d | T9-T11 |
| T13 | Integration test: full pipeline with infrastructure | AI-QA-01 | 1d | All above |
| T14 | Document infrastructure setup | AI-TW-01 | 1d | All above |

### Entry Criteria
- Phase 3 exit criteria passed (M4 gate approved) OR parallel execution approved
- PostgreSQL test instance available
- Encryption key management approach approved by Human Legal

### Exit Criteria (Phase Gate M4→M5)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | Session persistence works across restarts | Integration test | 100% session recovery |
| EC2 | No credentials stored in plaintext | Security scan | Zero plaintext findings |
| EC3 | Both storage backends pass tests | pytest | 100% passing on both |
| EC4 | Rate limits enforced | Rate limit tests | Exceeding limit triggers polite delay |
| EC5 | Source archive functional | Integration test | Raw source saved alongside extraction |
| EC6 | Configuration loads from all sources | Config tests | All three sources verified |

### Dependencies
- **Phase 2**: Adapters must be stable (infrastructure integrates with them)
- **External**: PostgreSQL instance for testing

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| Encryption implementation flaws | Low | Critical | Use well-audited libraries (cryptography); security review |
| PostgreSQL compatibility issues | Medium | Medium | Test on multiple versions; SQLite fallback always works |
| Rate limit defaults too aggressive/conservative | Medium | Medium | Start conservative; telemetry-driven adjustment |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Infrastructure coordination |
| AI-TL-01 | Storage interface design; security review |
| AI-DO-01 | All infrastructure implementation |
| AI-QA-01 | Infrastructure tests; security test cases |
| AI-TW-01 | Infrastructure documentation |
| AI-CO-01 | Encryption compliance; data retention review |

---

## Phase 5 — Developer Experience (Weeks 14–15)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | CLI is polished with intuitive commands, help, progress bars | Walkthrough test passes |
| O2 | Library API is finalized and documented | 100% public API documented |
| O3 | Plugin SDK is usable with complete documentation | Example plugin built in <2 hours |
| O4 | New user can install and collect in <15 minutes | Fresh environment telemetry |
| O5 | README communicates value proposition clearly | Human PO + DevRel approval |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | Polished CLI (click/typer-based) | Python module | AI-BE-01 | `/src/phoenix/cli/` |
| D2 | Progress indicators and spinners | Python module | AI-BE-01 | `/src/phoenix/cli/progress.py` |
| D3 | Help system and error hints | Python module | AI-BE-01 | `/src/phoenix/cli/help.py` |
| D4 | Library API finalization | Python package | AI-TL-01 | `/src/phoenix/api/` |
| D5 | Plugin SDK package | Python package | AI-BE-03 | `/src/phoenix/sdk/` |
| D6 | README.md | Markdown | AI-TW-01 | `/README.md` |
| D7 | Quick-start guide | Markdown | AI-TW-01 | `/docs/quickstart.md` |
| D8 | Plugin development guide | Markdown | AI-TW-01 | `/docs/plugin-development.md` |
| D9 | API reference documentation | Markdown | AI-TW-01 | `/docs/api-reference.md` |
| D10 | DX tests (walkthrough simulation) | Python tests | AI-QA-01 | `/tests/dx/` |

### Task Breakdown

**Week 14 — CLI + API**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Design CLI command structure | AI-TL-01 | 0.5d | All prior phases |
| T2 | Implement CLI commands (collect, config, plugin, etc.) | AI-BE-01 | 3d | T1 |
| T3 | Implement progress bars and status indicators | AI-BE-01 | 1d | T2 |
| T4 | Implement help system with examples | AI-BE-01 | 1d | T2 |
| T5 | Finalize library public API | AI-TL-01 | 1d | All prior |
| T6 | API consistency review and refactoring | AI-BE-01 | 2d | T5 |
| T7 | Write CLI and API tests | AI-QA-01 | 2d | T2-T6 |

**Week 15 — SDK + Documentation**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T8 | Package Plugin SDK | AI-BE-03 | 2d | Plugin framework from Phase 2 |
| T9 | Write example plugin using SDK | AI-BE-03 | 1d | T8 |
| T10 | Write README.md | AI-TW-01 | 1d | All features complete |
| T11 | Write quick-start guide | AI-TW-01 | 1d | T10 |
| T12 | Write plugin development guide | AI-TW-01 | 1d | T8 |
| T13 | Generate API reference | AI-TW-01 | 1d | T5 |
| T14 | DX walkthrough test (fresh install → first collection) | AI-QA-01 | 1d | All above |
| T15 | README + docs review by Human PO and DevRel | Human-PO-01, Human-DR-01 | 0.5d | T10-T13 |

### Entry Criteria
- Core functionality complete (Phases 1-4)
- All adapters functional
- Human PO and DevRel available for review

### Exit Criteria (Phase Gate M5→M6)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | Install-to-collect time ≤15 minutes | Fresh environment walkthrough | Median ≤15 min |
| EC2 | All CLI commands documented | Review | Help text for every command |
| EC3 | 100% public API documented | API doc coverage | Full coverage |
| EC4 | Plugin SDK works end-to-end | Example plugin test | Build + run in <2 hours |
| EC5 | README communicates clearly | Human review | PO + DevRel approval |
| EC6 | Quick-start guide validated | New user test | Successful completion |

### Dependencies
- **Phases 1-4**: All functional components must be complete
- **Human**: PO and DevRel availability for review

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| API breaking changes needed late | Medium | High | API freeze at Week 14; only additive changes after |
| Documentation quality gaps | Medium | Medium | Human review gate; TW agent dedicated to this phase |
| CLI complexity exceeds intuition | Medium | Medium | User testing; iterative refinement |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | DX coordination; time-to-collect tracking |
| AI-TL-01 | CLI design; API finalization |
| AI-BE-01 | CLI implementation; API polishing |
| AI-BE-03 | Plugin SDK packaging |
| AI-QA-01 | DX walkthrough testing |
| AI-TW-01 | All documentation |
| Human-PO-01 | README and docs review |
| Human-DR-01 | Developer experience review |

---

## Phase 6 — Quality & Hardening (Weeks 16–17)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Performance meets baseline benchmarks | p95 <30s for standard single-page collection |
| O2 | Security audit reveals zero critical/high vulnerabilities | Bandit, Safety, CodeQL all clean |
| O3 | GDPR/CCPA compliance certification complete | 100% compliance checklist passed |
| O4 | Load testing validates stability under concurrent use | Stable at 10 concurrent collections |
| O5 | Documentation is accurate and complete | Zero undocumented public APIs |
| O6 | Ollama local AI integration is robust and performant | Ollama extraction <10s on target GPU; <30s on CPU; cache hit ≥30%; zero external cost |
| O7 | Ollama extraction accuracy validated on local deployment | ≥80% accuracy on golden test set; ≤5% hallucination rate; hardware-aware model selection verified |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | Performance test suite | Python tests | AI-QA-01 | `/tests/performance/` |
| D2 | Performance benchmark report | Markdown | AI-QA-01 | `/reports/performance.md` |
| D3 | Security audit report | Markdown | AI-CO-01 | `/reports/security-audit.md` |
| D4 | GDPR compliance checklist | Markdown | AI-CO-01 | `/reports/gdpr-compliance.md` |
| D5 | CCPA compliance checklist | Markdown | AI-CO-01 | `/reports/ccpa-compliance.md` |
| D6 | Load test results | Markdown | AI-QA-01 | `/reports/load-test.md` |
| D7 | Documentation accuracy review | Markdown | AI-TW-01 | `/reports/doc-review.md` |
| D8 | Quality gate sign-off | Markdown | AI-QA-01 | `/reports/quality-gates.md` |
| D9 | Remediation log (if issues found) | Markdown | AI-PM-01 | `/reports/remediation.md` |
| D10 | Ollama integration test report | Markdown | AI-QA-01 | `/reports/ollama-integration-test.md` |
| D11 | Ollama extraction accuracy report | Markdown | AI-QA-01 | `/reports/ollama-accuracy-test.md` |
| D12 | Ollama hardware compatibility report | Markdown | AI-QA-01 | `/reports/ollama-hardware-compatibility.md` |
| D13 | Ollama inference latency benchmark report | Markdown | AI-QA-01 | `/reports/ollama-latency-benchmark.md` |
| D14 | Operational automation components | Python modules | AI-BE-01 | `src/phoenix/processing/domain_memory.py`, `src/phoenix/intelligence/change_detector.py`, `src/phoenix/infrastructure/audit_logger.py`, `src/phoenix/architect/fixture_generator.py` |
| D15 | Operational automation tests | Python tests | AI-QA-01 | `tests/unit/test_domain_memory.py`, `tests/unit/test_change_detector.py`, `tests/unit/test_audit_logger.py`, `tests/unit/test_fixture_generator.py` |

### Task Breakdown

**Week 16 — Performance + Security**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Build performance benchmark suite | AI-QA-01 | 1d | All code complete |
| T2 | Run performance benchmarks per adapter | AI-QA-01 | 1d | T1 |
| T3 | Profile and optimize slow paths | AI-BE-01, AI-BE-02, AI-BE-03 | 2d | T2 |
| T4 | Re-run benchmarks after optimization | AI-QA-01 | 0.5d | T3 |
| T5 | Run security static analysis (Bandit) | AI-CO-01 | 0.5d | All code |
| T6 | Run dependency vulnerability scan (Safety) | AI-CO-01 | 0.5d | All code |
| T7 | Run CodeQL analysis | AI-CO-01 | 1d | All code |
| T8 | Ollama integration stress test (service down, OOM, timeouts) | AI-QA-01 | 1d | All code |
| T9 | Ollama extraction accuracy validation (golden test set) | AI-QA-01 | 1d | All code |
| T10 | Hardware compatibility matrix validation (GPU 8GB/16GB, CPU-only) | AI-QA-01 | 1d | All code |
| T10b | Ollama inference latency benchmark on reference hardware | AI-QA-01 | 0.5d | All code |
| T11 | Remediate critical/high security findings | AI-BE-01 | 2d | T5-T10 |
| T12 | Re-run security scans | AI-CO-01 | 0.5d | T11 |

**Week 17 — Compliance + Load + Final Review + Ollama QA**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T13 | Complete GDPR compliance checklist | AI-CO-01 | 1d | All features |
| T14 | Complete CCPA compliance checklist | AI-CO-01 | 1d | All features |
| T15 | Ollama local AI privacy review (all data stays on local machine) | AI-CO-01 | 0.5d | All features |
| T16 | Human Legal Counsel review of compliance | Human-LC-01 | 1d | T13, T14 |
| T17 | Run load tests (concurrent collections) | AI-QA-01 | 1d | T4 |
| T18 | Review and fix load test issues | AI-BE-01 | 1d | T17 |
| T19 | Documentation accuracy review | AI-TW-01 | 1d | All docs |
| T20 | Fix documentation errors | AI-TW-01 | 0.5d | T19 |
| T21 | Final quality gate assessment | AI-QA-01 | 0.5d | All above |
| T22 | Remediation of any gate failures | Team | 1d | T21 |
| T23 | Final sign-off preparation | AI-PM-01 | 0.5d | T22 |

### Entry Criteria
- All functional phases complete (0-5)
- All code merged to `main` branch
- No known P0 bugs

### Exit Criteria (Phase Gate M6→M7)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | Performance: p95 <30s | Benchmark report | p95 ≤30s for standard content |
| EC2 | Security: zero critical/high vulns | Scan reports | Zero critical, zero high |
| EC3 | GDPR compliance: 100% checklist | Compliance checklist | All items passed |
| EC4 | CCPA compliance: 100% checklist | Compliance checklist | All items passed |
| EC5 | Load: stable at 10 concurrent | Load test report | No crashes, no data corruption |
| EC6 | Documentation: 100% accurate | Doc review report | Zero inaccuracies in public docs |
| EC7 | Ollama extraction accuracy ≥80% | Golden test set report | ≥80% accuracy, ≤5% hallucination |
| EC8 | Ollama error handling robust | Simulated failure tests | Graceful fallback on service down/OOM/timeout |
| EC9 | Ollama inference latency within target | Benchmark report | ≤10s on target GPU, ≤30s on CPU |
| EC10 | Ollama hardware compatibility verified | Hardware matrix report | Passes on all 3 target profiles (GPU 8GB, GPU 16GB, CPU-only) |
| EC11 | Ollama local AI privacy compliant | Privacy audit report | Zero data leaves local machine; no external API calls |
| EC12 | Human Legal sign-off | Signed approval | Human-LC-01 approval |
| EC13 | All quality gates passed | Gate report | 100% gates green |

### Dependencies
- **All prior phases**: Code must be complete
- **Human**: Legal Counsel availability for compliance review

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| Security scan finds critical issue | Medium | Critical | Early scans in Phase 0; remediation time budgeted |
| Compliance gap discovered | Low | Critical | Continuous compliance review from Phase 0; CO assigned throughout |
| Performance target missed | Medium | High | Profiling early; optimization time budgeted in Week 16 |
| Load test reveals concurrency bugs | Medium | High | Stress testing in CI from Phase 1; isolation review |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Quality coordination; remediation tracking |
| AI-TL-01 | Technical review of all remediation |
| AI-BE-01 | Performance optimization; security remediation |
| AI-BE-02 | Adapter-specific performance fixes |
| AI-BE-03 | Adapter-specific performance fixes |
| AI-DO-01 | Load test infrastructure |
| AI-QA-01 | All testing; gate assessment |
| AI-CO-01 | Security audit; compliance certification |
| AI-TW-01 | Documentation review |
| Human-LC-01 | Legal compliance sign-off |

---

## Phase 7 — Release & Launch (Week 18)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Package published to PyPI with clean install | `pip install phoenix-engine` succeeds on Python 3.9-3.12 |
| O2 | Documentation site live and accessible | 100% docs pages load; search functional |
| O3 | Release notes published | All changes documented with migration guide |
| O4 | Marketing site live with value proposition | Human DevRel approval |
| O5 | Community channels established | GitHub Discussions, issue templates ready |
| O6 | Launch announcement ready | Human PO + DevRel approval |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | PyPI package (wheel + sdist) | Python package | AI-DO-01 | PyPI registry |
| D2 | Release notes (CHANGELOG) | Markdown | AI-PM-01 | `/CHANGELOG.md` |
| D3 | Documentation site (GitHub Pages/MkDocs) | HTML | AI-TW-01 | `https://docs.phoenixengine.dev` |
| D4 | Marketing site page | HTML | Human-DR-01 | `https://phoenixengine.dev` |
| D5 | GitHub issue templates | Markdown | AI-PM-01 | `/.github/ISSUE_TEMPLATE/` |
| D6 | GitHub discussion categories | Config | Human-DR-01 | GitHub settings |
| D7 | Launch announcement | Markdown | Human-DR-01 | Blog/social |
| D8 | Installation validation report | Markdown | AI-QA-01 | `/reports/install-validation.md` |

### Task Breakdown

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Final version bump and tagging | AI-DO-01 | 0.5d | All quality gates |
| T2 | Build wheel and sdist packages | AI-DO-01 | 0.5d | T1 |
| T3 | Publish to PyPI test registry | AI-DO-01 | 0.5d | T2 |
| T4 | Validate test PyPI install (3.9-3.12) | AI-QA-01 | 1d | T3 |
| T5 | Publish to production PyPI | AI-DO-01 | 0.5d | T4 |
| T6 | Validate production install | AI-QA-01 | 0.5d | T5 |
| T7 | Generate and publish documentation site | AI-TW-01 | 1d | All docs |
| T8 | Write release notes / changelog | AI-PM-01 | 0.5d | All merged PRs |
| T9 | Set up GitHub issue templates | AI-PM-01 | 0.5d | — |
| T10 | Set up GitHub discussion categories | Human-DR-01 | 0.5d | — |
| T11 | Prepare marketing site content | Human-DR-01 | 1d | T7 |
| T12 | Publish marketing site | Human-DR-01 | 0.5d | T11 |
| T13 | Prepare launch announcement | Human-DR-01 | 0.5d | T12 |
| T14 | Final launch approval | Human-PO-01 | 0.5d | All above |
| T15 | Publish launch announcement | Human-DR-01 | 0.5d | T14 |

### Entry Criteria
- Phase 6 exit criteria all passed (M7 gate approved)
- Human Legal Counsel compliance sign-off obtained
- PyPI credentials and namespace secured
- Domain and hosting for docs site ready

### Exit Criteria (Phase Gate M7→M8 / LAUNCH)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | PyPI install succeeds | Fresh venv test | 100% on Python 3.9-3.12 |
| EC2 | Documentation site live | URL check | 200 OK; all pages accessible |
| EC3 | Release notes published | Review | Complete changelog |
| EC4 | GitHub community features ready | Visual inspection | Templates and discussions active |
| EC5 | Human PO go/no-go | Explicit approval | Signed off |
| EC6 | Human DevRel go/no-go | Explicit approval | Signed off |

### Dependencies
- **Phase 6**: Quality certification must be complete
- **Human**: PO and DevRel availability for final approval and launch execution
- **External**: PyPI namespace; domain registrar; hosting

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| PyPI namespace taken | Low | Critical | Pre-registered; verified in Phase 0 |
| Install failure on user machines | Medium | Critical | Test across OS (Linux, macOS, Windows); CI matrix |
| Docs site deployment failure | Low | Medium | Staged deployment; rollback plan |
| Launch timing conflict | Low | Medium | Flexible launch day within Week 18 |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Release coordination; changelog; issue templates |
| AI-DO-01 | Package build; PyPI publish; docs deployment |
| AI-QA-01 | Install validation across environments |
| AI-TW-01 | Documentation site generation and review |
| Human-PO-01 | Final go/no-go decision |
| Human-DR-01 | Marketing site; community setup; launch announcement |

---

## Phase 8 — Post-Launch (Ongoing)

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Stable operation with rapid bug triage | P0 bugs fixed within 24h; P1 within 72h |
| O2 | Community support and engagement | Issue response within 48h; discussion participation |
| O3 | Telemetry-informed improvement | Weekly telemetry review; top issues prioritized |
| O4 | v1.x feature planning initiated | Roadmap published within 4 weeks post-launch |
| O5 | Technical debt managed | Debt items triaged; ≤5 P2 items at any time |

### Ongoing Activities

| **Activity** | **Frequency** | **Owner** | **Description** |
|--------------|--------------|-----------|-----------------|
| Bug triage | Daily | AI-QA-01 | Review new issues; assign severity; route to owners |
| Community issue response | Daily | AI-BE-01, AI-BE-02, AI-BE-03 | Respond to GitHub issues; provide workarounds |
| Telemetry review | Weekly | AI-PM-01 | Analyze usage patterns; error rates; performance |
| Security monitoring | Weekly | AI-CO-01 | Review new CVEs in dependencies; scan for vulnerabilities |
| Dependency updates | Weekly | AI-DO-01 | Update packages; run tests; merge if green |
| Community engagement | Weekly | Human-DR-01 | Discussions; content; events |
| Roadmap refinement | Bi-weekly | AI-PM-01 + Human-PO-01 | Prioritize v1.x features based on feedback |
| Performance monitoring | Monthly | AI-QA-01 | Benchmark regression detection |
| Documentation updates | As needed | AI-TW-01 | Update for bug fixes; new features; community contributions |

### Entry Criteria
- Phase 7 launch complete
- Monitoring and alerting operational
- Team availability for support confirmed

### Exit Criteria (This Phase Never Exits — Continuous)
- v1.0 maintenance continues until v1.x supersedes
- Project formally closed only by Steering Committee decision

### Dependencies
- **Phase 7**: Must be launched
- **External**: GitHub community engagement; user feedback channels

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| Critical bug in production | Medium | Critical | Hotfix process; feature flag rollback; rapid patch release |
| Community toxicity/drama | Low | Medium | Code of conduct; moderated discussions; swift enforcement |
| Maintainer burnout (AI capacity) | Medium | High | Rotating responsibilities; clear escalation paths |
| Platform changes break adapters | High | High | Monitoring; rapid patch process; community adapter contributions |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Ongoing coordination; roadmap; stakeholder sync |
| AI-TL-01 | Technical direction; architecture decisions |
| AI-BE-01, AI-BE-02, AI-BE-03 | Bug fixes; community support; v1.x development |
| AI-DO-01 | Infrastructure; deployments; monitoring |
| AI-QA-01 | Bug triage; regression testing; quality monitoring |
| AI-CO-01 | Compliance monitoring; security updates |
| AI-TW-01 | Documentation maintenance; community content |
| Human-PO-01 | Product direction; prioritization |
| Human-DR-01 | Community; events; advocacy |

---

## Phase 9 — PhoenixArchitect Autonomous Adapter Generation (Weeks 19–21)

### Phase Overview

**PhoenixArchitect** is the next major capability for Phoenix Engine: an autonomous AI agent that turns a natural-language scraping goal into a working, validated adapter plugin. It discovers candidate sites through search, explores their pages (handling pagination and infinite scroll), inspects the HTML with the local Ollama model, generates adapter code, validates it against collected snapshots, and registers the new adapter with the plugin registry.

### Phase Objectives

| **#** | **Objective** | **KPI** |
|-------|---------------|---------|
| O1 | Search-driven discovery returns relevant candidate URLs | ≥80% top-10 results relevant to goal |
| O2 | Browser exploration captures multiple pages respectfully | ≤`max-pages` snapshots per site; no rate-limit violations |
| O3 | Inspector identifies correct site type and data fields | ≥85% field coverage on collected snapshots |
| O4 | Coder generates syntactically valid adapter modules | 100% pass ruff/black/mypy; import successfully |
| O5 | Critic validates adapters and triggers retry on low coverage | ≥70% of generated adapters pass validation after ≤3 iterations |
| O6 | Generated adapters are auto-registered and prioritized | Matching URLs route to generated adapter before generic fallback |
| O7 | CLI commands `phoenix discover` and `phoenix architect` shipped | Both commands documented and covered by e2e tests |

### Deliverables

| **#** | **Deliverable** | **Format** | **Owner** | **Location** |
|-------|-----------------|------------|-----------|--------------|
| D1 | PhoenixArchitect planner module | Python module | AI-BE-01 | `/src/phoenix/architect/planner.py` |
| D2 | Search-driven researcher (DuckDuckGo/SerpAPI) | Python module | AI-BE-01 | `/src/phoenix/architect/researcher.py` |
| D3 | Browser/HTTP explorer with scroll/pagination | Python module | AI-BE-01 | `/src/phoenix/architect/explorer.py` |
| D4 | HTML inspector using Ollama | Python module | AI-BE-01 | `/src/phoenix/architect/inspector.py` |
| D5 | Adapter code generator | Python module | AI-BE-01 | `/src/phoenix/architect/coder.py` |
| D6 | Adapter validation critic | Python module | AI-BE-01 | `/src/phoenix/architect/critic.py` |
| D7 | PhoenixArchitect orchestrator | Python module | AI-BE-01 | `/src/phoenix/architect/__init__.py` |
| D8 | CLI commands `discover` and `architect` | Typer commands | AI-BE-01 | `/src/phoenix/cli/main.py` |
| D9 | PhoenixArchitect tests | Python tests | AI-QA-01 | `/tests/intelligence/test_architect*.py` |
| D10 | PhoenixArchitect feature documentation | Markdown | AI-TW-01 | `/docs/features/phoenix-architect.md` |

### Task Breakdown

**Week 19 — Discovery & Exploration**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T1 | Design agent JSON plan schema and role contracts | AI-TL-01 | 1d | Phase 6 complete |
| T2 | Implement query builder and search backends | AI-BE-01 | 2d | T1 |
| T3 | Implement result ranking / filtering | AI-BE-01 | 1d | T2 |
| T4 | Implement browser explorer with scroll/pagination detection | AI-BE-01 | 3d | T1 |
| T5 | Implement snapshot archiver for exploration | AI-BE-01 | 1d | T4 |
| T6 | Write researcher/explorer tests | AI-QA-01 | 2d | T2-T5 |

**Week 20 — Inspection & Code Generation**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T7 | Implement Inspector prompts and HTML analysis | AI-BE-01 | 2d | T4 |
| T8 | Implement adapter code generator (selectors + normalizer) | AI-BE-01 | 3d | T7 |
| T9 | Implement generated code formatting and lint gate | AI-BE-01 | 1d | T8 |
| T10 | Write inspector/coder tests | AI-QA-01 | 2d | T7-T9 |

**Week 21 — Validation, CLI & Hardening**

| **#** | **Task** | **Owner** | **Effort** | **Dependencies** |
|-------|----------|-----------|------------|------------------|
| T11 | Implement Critic validation loop and coverage metric | AI-BE-01 | 2d | T8 |
| T12 | Implement plugin registration for validated adapters | AI-BE-01 | 1d | T11 |
| T13 | Implement `phoenix discover` and `phoenix architect` CLI | AI-BE-01 | 2d | T2, T11 |
| T14 | Write end-to-end architect tests | AI-QA-01 | 2d | T13 |
| T15 | Document PhoenixArchitect usage and safety guidelines | AI-TW-01 | 1d | All above |

### Entry Criteria
- Phase 6 quality gates passed (or parallel execution approved)
- Ollama AI layer stable with `dolphincoder:7b`
- Plugin registry supports dynamic adapter registration
- Browser scraper supports scroll/pagination hooks

### Exit Criteria (Phase Gate M8→M9)

| **#** | **Criterion** | **Verification Method** | **Pass Threshold** |
|-------|---------------|------------------------|-------------------|
| EC1 | Search returns relevant URLs | Manual + automated query test | ≥80% top-10 relevance |
| EC2 | Exploration respects limits | Mock site test | No more than `max-pages` snapshots per site |
| EC3 | Inspector field coverage | Snapshot test set | ≥85% expected fields identified |
| EC4 | Generated code quality | Static analysis | 100% pass ruff/black/mypy |
| EC5 | Critic validation loop | Low-coverage adapter test | ≥70% pass after ≤3 iterations |
| EC6 | Auto-registration works | Plugin registry test | Generated adapter routed before generic fallback |
| EC7 | CLI commands functional | e2e tests | `phoenix discover` and `phoenix architect` succeed |
| EC8 | Tests passing with ≥80% coverage | pytest report | All green, coverage ≥80% |
| EC9 | Documentation complete | Review | User guide and safety notes published |

### Dependencies
- **Phases 1-5**: Core engine, adapters, plugin framework, Ollama layer
- **External**: DuckDuckGo availability or SerpAPI key; test target sites with permissive robots.txt

### Risk Factors

| **Risk** | **Probability** | **Impact** | **Mitigation** |
|----------|----------------|------------|----------------|
| Search engine blocking or rate limiting | Medium | High | Cache results; support SerpAPI fallback; polite delays |
| Generated selectors brittle | High | High | Critic loop; validate across multiple snapshots; human review option |
| LLM hallucinates field names | Medium | High | Low temperature; Pydantic validation; coverage threshold |
| Ethical/legal concerns with autonomous scraping | Medium | Critical | Hard-coded ToS checks; block known restricted domains; human approval gate |

### Role Assignments

| **Role** | **Responsibilities in Phase** |
|----------|------------------------------|
| AI-PM-01 | Roadmap coordination; safety review scheduling |
| AI-TL-01 | Agent architecture; role contracts; code review |
| AI-BE-01 | PhoenixArchitect implementation and CLI integration |
| AI-QA-01 | Search/explore/inspect/code/critic tests; e2e validation |
| AI-TW-01 | Feature documentation and safety guidelines |
| AI-CO-01 | Ethical scope review; domain blocklist; compliance sign-off |
| Human-PO-01 | Approve PhoenixArchitect scope and safety gates |

---

## Cross-Phase Dependencies & Critical Path

### Dependency Map

```
Phase 0 (Foundation)
    │
    ▼
Phase 1 (Core Engine) ─────────────────────────┐
    │  (HTTP scraper, Playwright, selectors)     │
    ▼                                            │
Phase 2 (Platform HTML Scrapers) ◄─────────────┘
    │  (Instagram, X, TikTok, LinkedIn, FB,
    │   YouTube, Generic Web — all via HTML)
    ├──► Phase 3 (Local AI Intelligence Layer — Ollama) ──┐
    │  (Ollama: local AI extraction, model management,      │
    │   hardware-aware selection, selector repair)           │
    ├──► Phase 4 (Infrastructure) ────────────┤
    │  (cookies, proxies, browser pool,         │
    │   rate limiting, HTML archive)            │
    └──► Phase 5 (Plugin SDK + DX) ◄──────────┘
                          │
                          ▼
                   Phase 6 (Quality + Ollama Validation) [CRITICAL PATH]
                          │
                          ▼
                   Phase 7 (Release to PyPI)
                          │
                          ▼
                   Phase 8 (Post-Launch + Ollama monitoring)
                          │
                          ▼
                   Phase 9 (PhoenixArchitect Autonomous Adapter Generation)
```

### Buffer Analysis

| **Phase** | **Planned Duration** | **Buffer** | **Compressed If Needed** |
|-----------|---------------------|------------|--------------------------|
| Phase 0 | 2 weeks | None | — |
| Phase 1 | 3 weeks | 0.5 week | Reduce doc tasks |
| Phase 2 | 4 weeks | 0.5 week | Parallelize adapter batches |
| Phase 3 | 2 weeks | 0.5 week | Reduce entity resolution scope; defer hardware matrix to Phase 6 |
| Phase 4 | 2 weeks | 0.5 week | Defer PostgreSQL to v1.1 |
| Phase 5 | 2 weeks | 0.5 week | Reduce SDK polish |
| Phase 6 | 2 weeks | None | — |
| Phase 7 | 1 week | None | — |

**Total buffer**: 2.5 weeks distributed across Phases 1-5. Any slippage beyond buffer consumes Week 18 or requires scope reduction.

---

## Appendix A: Milestone Gate Checklist Template

Each gate review uses this standardized checklist:

| **Category** | **Item** | **Status** | **Evidence** | **Approver** |
|--------------|----------|------------|--------------|--------------|
| Code Quality | All tests passing | ☐ | CI report | AI-QA-01 |
| Code Quality | Coverage threshold met | ☐ | Coverage report | AI-QA-01 |
| Code Quality | Lint/type checks clean | ☐ | CI report | AI-DO-01 |
| Code Quality | Code review complete | ☐ | PR approvals | AI-TL-01 |
| Functionality | All deliverables implemented | ☐ | Deliverable list | AI-PM-01 |
| Functionality | Integration tests passing | ☐ | Test report | AI-QA-01 |
| Documentation | API docs complete | ☐ | Doc review | AI-TW-01 |
| Documentation | User-facing docs updated | ☐ | Doc review | AI-TW-01 |
| Compliance | Security scan clean | ☐ | Scan report | AI-CO-01 |
| Compliance | No legal concerns | ☐ | CO sign-off | AI-CO-01 |
| Performance | Benchmarks acceptable | ☐ | Benchmark report | AI-QA-01 |
| Dependencies | All external deps available | ☐ | Dependency list | AI-DO-01 |
| Budget | Phase spend within plan | ☐ | Budget report | AI-PM-01 |
| **GATE DECISION** | **APPROVED / CONDITIONAL / REJECTED** | | | **Human-PO-01** |

---

## Appendix B: Risk Triggers & Escalation

| **Trigger** | **Action** | **Escalation Level** |
|-------------|-----------|----------------------|
| Phase exit criteria not met by deadline | 48h extension granted; if still failing, scope reduction review | Level 2 (AI PM) |
| Security scan finds critical vulnerability | All work stops; emergency remediation; legal notified | Level 3 (Human PO) |
| Budget overrun >10% | Immediate freeze on discretionary spending; PO review | Level 3 (Human PO) |
| Legal/compliance question arises | Work paused on affected component; legal counsel engaged | Level 3 (Human Legal) |
| Key AI agent unavailable >24h | Work redistribution; if >48h, human contractor engagement | Level 2 (AI PM) |
| Platform blocks extraction method | Emergency adapter patch; fallback mode activation | Level 2 (AI PM) |

---

*This document is a living plan. Updates require AI PM approval and Human PO notification. The authoritative version resides in the project repository at `/docs/phases-milestones.md`.*

**Related Documents**:
- [01-Project Charter](01-project-charter.md)
- [11-Communication & Collaboration Plan](11-communication-plan.md)
