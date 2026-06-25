"""Live integration tests against a local Ollama instance.

These tests are skipped when Ollama is not running locally.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from phoenix.collectors.base import StubCollector
from phoenix.engine import PhoenixEngine
from phoenix.intelligence import ContentClassifier, EntityResolver, SelectorRepair
from phoenix.models.config import Config
from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor

pytestmark = [pytest.mark.integration, pytest.mark.unit]


def _ollama_available() -> bool:
    """Return ``True`` when Ollama appears to be running locally."""
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen("http://localhost:11434/", timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def _model_available(model_name: str) -> bool:
    """Return ``True`` when ``model_name`` is pulled in the local Ollama library."""
    import json
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(
            "http://localhost:11434/api/tags",
            timeout=2,
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
            models = {m.get("name", "") for m in data.get("models", [])}
            return model_name in models
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return False


@pytest.fixture
def phoenix_ai_extractor() -> PhoenixAIExtractor | None:
    """Return a live PhoenixAIExtractor if Ollama and the model are available."""
    if not _ollama_available():
        pytest.skip("Ollama is not running on localhost:11434")
    model = os.environ.get("PHOENIX_TEST_OLLAMA_MODEL", "qwen2.5:7b")
    if not _model_available(model):
        pytest.skip(f"Ollama model {model!r} is not pulled locally")
    return PhoenixAIExtractor(
        default_model=model,
        max_tokens=512,
        timeout=120.0,
    )


@pytest.mark.asyncio
async def test_phoenix_ai_extractor_live(phoenix_ai_extractor: PhoenixAIExtractor) -> None:
    """PhoenixAIExtractor extracts structured data from synthetic HTML."""
    html = """
    <html><body>
        <article>
            <h1>Local AI Test</h1>
            <p>This is a sample article about Phoenix Engine.</p>
            <span>By testauthor</span>
        </article>
    </body></html>
    """
    schema = "Return JSON with title, text, author."
    result = await phoenix_ai_extractor.extract(
        html,
        "https://example.com/test",
        "generic",
        "article",
        schema,
    )

    assert isinstance(result, dict)
    assert "Local AI Test" in str(result.get("title", ""))
    assert "testauthor" in str(result.get("author", ""))


@pytest.mark.asyncio
async def test_phoenix_ai_classifier_live(phoenix_ai_extractor: PhoenixAIExtractor) -> None:
    """ContentClassifier identifies a tweet using local Ollama."""
    classifier = ContentClassifier(phoenix_ai_extractor)
    html = '<html><body><article data-testid="tweet"><div>Tweet text</div></article></body></html>'

    result = await classifier.classify(html, "https://x.com/user/status/123")

    assert result["platform"] == "x_twitter"
    assert result["content_type"] == "post"
    assert result["confidence"] > 0.0


@pytest.mark.asyncio
async def test_phoenix_ai_entity_resolver_live(phoenix_ai_extractor: PhoenixAIExtractor) -> None:
    """EntityResolver extracts named entities using local Ollama."""
    resolver = EntityResolver(phoenix_ai_extractor)
    html = "<html><body><p>News about OpenAI and Sam Altman.</p></body></html>"

    entities = await resolver.extract_entities(html, "https://example.com/", "generic")

    names = {str(e.get("name", "")).lower() for e in entities}
    assert "openai" in names or "sam altman" in names


@pytest.mark.asyncio
async def test_phoenix_ai_selector_repair_live(phoenix_ai_extractor: PhoenixAIExtractor) -> None:
    """SelectorRepair suggests a new selector using local Ollama."""
    repair = SelectorRepair(phoenix_ai_extractor)
    html = '<html><body><h1 class="new-title">Title</h1></body></html>'

    suggestions = await repair.repair(html, {"title": ".old-title"})

    assert isinstance(suggestions, list)
    assert len(suggestions) > 0


@pytest.mark.asyncio
async def test_engine_phoenix_ai_fallback_live() -> None:
    """PhoenixEngine uses Phoenix AI for AI fallback end-to-end."""
    if not _ollama_available():
        pytest.skip("Ollama is not running on localhost:11434")
    model = os.environ.get("PHOENIX_TEST_OLLAMA_MODEL", "qwen2.5:7b")
    if not _model_available(model):
        pytest.skip(f"Ollama model {model!r} is not pulled locally")

    config = Config(
        ai_enabled=True,
        ai_model=model,
    )
    collectors: dict[str, Any] = {
        "http": StubCollector(
            strategy="http",
            html=(
                "<html><body><article>"
                "<h1>AI Fallback Test</h1>"
                "<p>Minimal page.</p>"
                "<span>By author</span>"
                "</article></body></html>"
            ),
        ),
        "browser": StubCollector(strategy="browser", html=""),
    }
    engine = PhoenixEngine(config=config, collectors=collectors)

    result = await engine.scrape("https://example.com/article/123")

    assert result.success is True
    assert result.ai_assisted is True
    assert result.output is not None
    assert "AI Fallback Test" in str(result.output.title)
