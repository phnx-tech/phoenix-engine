# Phoenix AI Extraction

Phoenix Engine integrates **Phoenix AI**, a built-in intelligence layer that runs
on a local Ollama instance. When CSS selectors, XPath, and regex heuristics fail
to extract structured data, the engine sends raw HTML to Phoenix AI for parsing.
Because Phoenix AI is local, HTML never leaves your infrastructure and no
external API keys are required.

## Design Principles

- **Selectors first**: Phoenix AI is only used after selector extraction fails or
  returns insufficient data.
- **Local by default**: All inference happens on `localhost:11434` via Ollama.
- **Budget-aware**: Hard spend caps prevent runaway costs when an external
  endpoint is configured.
- **Cached**: Identical HTML/schema pairs are cached to reduce repeated calls.
- **Measured**: Token usage and estimated cost are tracked on every call.
- **Compliant**: Only public HTML is submitted; PII scrubbing is the adapter
  author's responsibility.

## Enabling Phoenix AI

Make sure Ollama is running locally (`ollama serve`) and the desired model is
pulled. The recommended default is:

```bash
ollama pull qwen2.5:7b
```

Then configure Phoenix Engine:

```bash
export PHOENIX_AI_ENABLED="true"
# Optional: override the default local model
export PHOENIX_AI_MODEL="qwen2.5:7b"
```

Or programmatically:

```python
from phoenix import PhoenixEngine
from phoenix.models.config import Config

config = Config(
    ai_enabled=True,
    ai_model="qwen2.5:7b",
)
async with PhoenixEngine(config=config) as engine:
    result = await engine.scrape("https://example.com/novel-page")
```

## Fallback Cascade

The pipeline attempts extraction in this order:

1. **CSS/XPath selector chains** in the platform adapter.
2. **Browser rendering** if HTTP fails or the page is JavaScript-heavy.
3. **Phoenix AI extraction** if selectors return empty/missing critical fields.
4. **Structured error** if Phoenix AI also fails or the budget is exhausted.

## Extractor

### PhoenixAIExtractor

`PhoenixAIExtractor` (`src/phoenix/processing/phoenix_ai_extractor.py`) is the
low-level client wrapper for Phoenix AI. It uses an OpenAI-compatible client to
talk to the local Ollama endpoint by default. Features:

- Chunking for large HTML pages.
- Retry with exponential backoff on rate limits/timeouts.
- In-memory response cache with TTL.
- Token usage and estimated cost tracking.
- Hard budget cap via `max_budget_usd`.

```python
from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor

extractor = PhoenixAIExtractor(
    base_url="http://localhost:11434/v1",
    default_model="qwen2.5:7b",
    max_budget_usd=1.00,
)
```

## Intelligence Modules

The intelligence layer (`src/phoenix/intelligence/`) provides higher-level
Phoenix AI capabilities:

### ContentClassifier

Classifies unknown HTML into platform and content type:

```python
from phoenix.intelligence import ContentClassifier

classifier = ContentClassifier(extractor)
result = await classifier.classify(html, url)
# {'platform': 'x_twitter', 'content_type': 'post', 'confidence': 0.95}
```

### EntityResolver

Extracts named entities and resolves cross-platform identity:

```python
from phoenix.intelligence import EntityResolver

resolver = EntityResolver(extractor)
entities = await resolver.extract_entities(html, url, platform="x_twitter")
verdict = await resolver.resolve(entity_a, entity_b)
```

### SelectorRepair

Suggests new CSS selectors after a site layout change:

```python
from phoenix.intelligence import SelectorRepair

repair = SelectorRepair(extractor)
suggestions = await repair.repair(html_sample, {"title": ".old-title"})
```

## Budget Management

Configure a hard budget cap in USD:

```bash
export PHOENIX_AI_MAX_BUDGET_USD="5.00"
```

Once the estimated spend reaches the cap, all Phoenix AI calls raise
`AIExtractionError` until the cap is raised or reset. Set the value to `0`
(the default) for unlimited spending. Local Ollama inference does not incur
per-call cloud costs, so the cap is primarily a safety guardrail.

## Cost Estimation

Estimated cost uses conservative OpenAI-style pricing placeholders:

- Prompt tokens: $0.00001 per token
- Completion tokens: $0.00003 per token

> These are conservative estimates for budget guarding. Local Ollama inference
> has no external per-token cost beyond your own hardware.

## Testing

The intelligence layer tests use a mocked `PhoenixAIExtractor` so they do not
require a live model:

```bash
pytest tests/intelligence/
pytest tests/unit/test_phoenix_ai_extractor.py
```

To validate against a real local Ollama instance:

```bash
ollama serve
pytest tests/intelligence/test_ollama_integration.py -v
```

## Compliance & PII

Before sending HTML to Phoenix AI:

- Ensure the content is public (adapters already enforce this).
- Avoid sending pages with user PII, credentials, or session tokens.
- Review `docs/compliance/ETHICAL-GUARDRAILS.md` and
  `docs/compliance/PLATFORM-TOS-SUMMARY.md`.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `AIExtractionError: extraction failed` | Ollama not running | Start `ollama serve` |
| `AI budget exceeded` | Cap reached | Raise `PHOENIX_AI_MAX_BUDGET_USD` or reset usage |
| `Rate limited after N retries` | Local queue saturated | Reduce concurrency or upgrade hardware |
| JSON parse errors | Model returned markdown/explanation | Lower temperature; add stricter prompts |
