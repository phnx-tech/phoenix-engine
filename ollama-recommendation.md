# Phoenix Engine: Ollama Migration Recommendation & Plan

## Executive Summary

Migrating from Kimi API (cloud) to **Ollama (self-hosted local AI)** eliminates all external API dependencies, reduces operational costs to zero, guarantees data privacy (HTML never leaves your infrastructure), and removes rate limiting bottlenecks. This document provides model recommendations, hardware planning, and the full migration strategy.

---

## Why Ollama Over Kimi API

| Factor | Kimi API (Cloud) | Ollama (Local) |
|--------|------------------|----------------|
| **Cost** | Pay per token ($$$) | Zero ongoing cost (hardware only) |
| **Privacy** | HTML sent to external servers | HTML stays on your machine |
| **Latency** | Network round-trip + queue | Local inference (GPU-speed) |
| **Availability** | Dependent on Kimi uptime | 100% uptime (your hardware) |
| **Rate Limits** | Subject to Kimi quotas | Unlimited (your capacity) |
| **Customization** | Fixed models | Choose any model, fine-tune |
| **Offline** | Requires internet | Works fully offline |
| **Data Residency** | China/US servers | Your own infrastructure |

---

## Model Recommendation: Qwen2.5-Coder

After evaluating all available Ollama models for **HTML parsing and structured data extraction**, the clear winner is:

### Primary Choice: `qwen2.5:7b`

**Why Qwen2.5-Coder?**
- **Built for code/structured tasks** — HTML is structured markup; this model excels at parsing it
- **128K context window** — can ingest large HTML pages in a single pass
- **Strong JSON output** — reliably returns valid structured data
- **Multilingual** — handles content in any language (Arabic, English, Chinese, etc.)
- **Excellent instruction following** — follows complex extraction schemas precisely
- **Ollama-native** — first-class support, optimized inference
- **Apache 2.0 license** — fully commercial, no restrictions

**Hardware: Single GPU (RTX 4090 / A6000 / L40) or CPU with 32GB+ RAM**

### Tiers (Choose Based on Hardware)

| Tier | Model | Hardware | Speed | Quality | Best For |
|------|-------|----------|-------|---------|----------|
| **Enterprise** | `qwen2.5-coder:32b` | Dual GPU / A100 80GB | Medium | Excellent | Production deployments, maximum accuracy |
| **Professional** | `qwen2.5:7b` | Single GPU (8GB VRAM) | Fast | Very Good | **Recommended default** — best price/performance |
| **Lightweight** | `qwen2.5:7b` | Single GPU (16GB VRAM) | Very Fast | Good | Development, testing, smaller HTML pages |
| **CPU-Only** | `qwen2.5:7b` (Q4 quant) | 32GB RAM, no GPU | Slow | Good | Proof of concept, low-budget deployments |

### Alternative Models

| Model | Strengths | When to Use |
|-------|-----------|-------------|
| `deepseek-coder-v2:16b` | Strong code reasoning, fast | If Qwen unavailable; good fallback |
| `codestral:22b` | Excellent structured output | If you have 40GB+ VRAM |
| `llama3.1:70b` | General purpose, very capable | If you need general AI + extraction |
| `phi4:14b` | Fast, efficient, Microsoft-backed | Speed-critical deployments |

---

## Architecture Migration Plan

### What Changes

```
BEFORE (Kimi API):
HTML → KimiAPIClient → HTTPS → api.moonshot.cn → JSON
               ↑ API key, rate limits, token costs

AFTER (Ollama):
HTML → OllamaClient → HTTP localhost:11434 → Local GPU → JSON
               ↑ No auth, no limits, no cost, full privacy
```

### Files to Update

| File | Changes |
|------|---------|
| `06-technical-architecture.md` | Replace `KimiAIEngine` with `OllamaAIEngine`; update stack |
| `07-api-specification.md` | Replace `KimiAPIClient` with `OllamaClient`; update endpoints |
| `05-product-requirements.md` | Rename F14, F21-F24; update ACs for Ollama |
| `08-development-standards.md` | Replace Kimi prompts with Ollama prompts; model management |
| `10-risk-management.md` | Replace Kimi risks with Ollama risks (HW failure, model loading) |
| `03-phases-milestones.md` | Rename Phase 3; update deliverables |
| `02-team-structure.md` | Update Dev-1 role for Ollama ops |
| `master-index.md` | Update architecture diagram |

### New Components Needed

1. **OllamaClient** — HTTP client talking to `localhost:11434`
2. **ModelManager** — Download, load, verify, swap models
3. **HardwareMonitor** — GPU/CPU/RAM usage tracking
4. **ModelSelector** — Auto-select model tier based on HTML size

### Hardware Requirements

| Deployment | GPU | VRAM | RAM | Storage | Est. Cost |
|------------|-----|------|-----|---------|-----------|
| **Dev/Test (7B)** | RTX 3060 or CPU | 12GB | 32GB | 50GB SSD | $0 (existing) |
| **Production (14B)** | RTX 4090 / A6000 | 24GB | 64GB | 100GB SSD | ~$1,500-3,000 |
| **Enterprise (32B)** | Dual A100 / H100 | 80GB | 128GB | 200GB SSD | ~$10,000-30,000 |

---

## Implementation Phases

### Step 1: Infrastructure (Week 0 — Pre-Project)
- Install Ollama on all dev machines
- Pull `qwen2.5:7b` (primary) and `qwen2.5:7b` (larger fallback)
- Verify GPU/CUDA setup
- Document hardware requirements

### Step 2: Core Integration (Phase 1 — alongside engine)
- Build `OllamaClient` (HTTP client for Ollama API)
- Build `ModelManager` (model lifecycle)
- Build `HardwareMonitor` (resource tracking)
- Implement prompt templates for HTML extraction

### Step 3: Intelligence Layer (Phase 3 — dedicated)
- HTML extraction via Ollama
- Selector repair via Ollama
- Content classification via Ollama
- Entity resolution via Ollama
- Model auto-selection based on task

---

## Final Recommendation

| Decision | Choice |
|----------|--------|
| **Primary Model** | `qwen2.5:7b` |
| **Fallback Model** | `qwen2.5:7b` |
| **Enterprise Model** | `qwen2.5-coder:32b` |
| **Hardware Target** | Single GPU with 8GB VRAM (RTX 4050 class) or CPU |
| **Runtime** | Ollama 0.3+ |
| **API** | Ollama REST API on `localhost:11434` |

---

*This is a living document. Update as hardware and models evolve.*
