"""Unit tests for PhoenixAIExtractor."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from phoenix.processing.phoenix_ai_extractor import (
    AIExtractionError,
    AIJSONParseError,
    PhoenixAIExtractor,
)

pytestmark = pytest.mark.unit

HTML = "<html><body><h1>Title</h1><p>Body</p></body></html>"
URL = "https://example.com/article/1"
PLATFORM = "generic"
CONTENT_TYPE = "post"
SCHEMA = '{"title": "string"}'


@pytest.fixture
def mock_phoenix_ai_client() -> MagicMock:
    """Return a mocked AsyncOpenAI client used by Phoenix AI."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def extractor(mock_phoenix_ai_client: MagicMock) -> PhoenixAIExtractor:
    """Return a PhoenixAIExtractor with a mocked client."""
    with patch.object(PhoenixAIExtractor, "__init__", lambda _self, **_kwargs: None):
        ext = PhoenixAIExtractor()
        ext.api_key = "ollama"
        ext.base_url = "http://localhost:11434/v1"
        ext.default_model = "qwen2.5:7b"
        ext.temperature = 0.1
        ext.max_tokens = 8192
        ext.timeout = 30.0
        ext.cache_ttl = 3600
        ext.max_budget_usd = 0.0
        ext._cache = {}
        ext.total_tokens_used = 0
        ext.total_api_calls = 0
        ext.estimated_cost_usd = 0.0
        ext._client = mock_phoenix_ai_client
        return ext


def _make_response(content: str, usage: dict[str, int] | None = None) -> MagicMock:
    """Build a mocked chat completion response."""
    response = MagicMock()
    choice = MagicMock()
    message = MagicMock()
    message.content = content
    choice.message = message
    response.choices = [choice]
    if usage is not None:
        response.usage = MagicMock(**usage)
    else:
        response.usage = None
    return response


@pytest.mark.asyncio
async def test_extract_success(extractor: PhoenixAIExtractor) -> None:
    """Extract returns parsed JSON on a successful API call."""
    expected = {"title": "Hello", "text": "World"}
    extractor._client.chat.completions.create.return_value = _make_response(
        json.dumps(expected),
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )

    result = await extractor.extract(
        HTML,
        URL,
        PLATFORM,
        CONTENT_TYPE,
        SCHEMA,
    )

    assert result == expected
    assert extractor.total_api_calls == 1
    assert extractor.total_tokens_used >= 15
    assert extractor.estimated_cost_usd > 0.0


@pytest.mark.asyncio
async def test_extract_with_markdown_fences(extractor: PhoenixAIExtractor) -> None:
    """Extract strips markdown fences before parsing JSON."""
    expected = {"title": "Hello"}
    extractor._client.chat.completions.create.return_value = _make_response(
        f"```json\n{json.dumps(expected)}\n```",
    )

    result = await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)

    assert result == expected


@pytest.mark.asyncio
async def test_extract_json_parse_error(extractor: PhoenixAIExtractor) -> None:
    """Extract raises AIJSONParseError for invalid JSON."""
    extractor._client.chat.completions.create.return_value = _make_response("not json")

    with pytest.raises(AIJSONParseError):
        await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)


@pytest.mark.asyncio
async def test_extract_non_object_response(extractor: PhoenixAIExtractor) -> None:
    """Extract raises AIJSONParseError when response JSON is not an object."""
    extractor._client.chat.completions.create.return_value = _make_response("[1, 2, 3]")

    with pytest.raises(AIJSONParseError):
        await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)


@pytest.mark.asyncio
async def test_extract_rate_limit_retry_then_success(extractor: PhoenixAIExtractor) -> None:
    """Extract retries on RateLimitError and eventually succeeds."""
    from openai import RateLimitError

    expected = {"title": "Retry OK"}
    extractor._client.chat.completions.create.side_effect = [
        RateLimitError(
            message="rate limited",
            response=MagicMock(),
            body=None,
        ),
        _make_response(json.dumps(expected)),
    ]

    with patch("asyncio.sleep", new=AsyncMock()):
        result = await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)

    assert result == expected
    assert extractor._client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_extract_rate_limit_exhausted(extractor: PhoenixAIExtractor) -> None:
    """Extract raises AIExtractionError when retries are exhausted."""
    from openai import RateLimitError

    extractor._client.chat.completions.create.side_effect = RateLimitError(
        message="rate limited",
        response=MagicMock(),
        body=None,
    )

    with patch("asyncio.sleep", new=AsyncMock()), pytest.raises(AIExtractionError):
        await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)


@pytest.mark.asyncio
async def test_extract_timeout_exhausted(extractor: PhoenixAIExtractor) -> None:
    """Extract raises AIExtractionError on repeated timeouts."""
    from openai import APITimeoutError

    extractor._client.chat.completions.create.side_effect = APITimeoutError(
        request=MagicMock(),
    )

    with patch("asyncio.sleep", new=AsyncMock()), pytest.raises(AIExtractionError):
        await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)


@pytest.mark.asyncio
async def test_extract_api_error(extractor: PhoenixAIExtractor) -> None:
    """Extract raises AIExtractionError on non-retryable API errors."""
    from openai import APIError

    extractor._client.chat.completions.create.side_effect = APIError(
        message="bad request",
        request=MagicMock(),
        body={"code": "invalid_request"},
    )

    with pytest.raises(AIExtractionError):
        await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)


@pytest.mark.asyncio
async def test_extract_cache_hit(extractor: PhoenixAIExtractor) -> None:
    """Extract returns cached response for identical HTML and schema."""
    expected = {"title": "Cached"}
    extractor._client.chat.completions.create.return_value = _make_response(
        json.dumps(expected),
    )

    result1 = await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)
    result2 = await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)

    assert result1 == result2 == expected
    assert extractor._client.chat.completions.create.await_count == 1


@pytest.mark.asyncio
async def test_extract_cache_expired(extractor: PhoenixAIExtractor) -> None:
    """Extract does not return an expired cached entry."""
    expected = {"title": "Fresh"}
    extractor._client.chat.completions.create.return_value = _make_response(
        json.dumps(expected),
    )

    await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)
    entry = next(iter(extractor._cache.values()))
    entry["timestamp"] = datetime.now(UTC) - timedelta(seconds=extractor.cache_ttl + 1)

    result = await extractor.extract(HTML, URL, PLATFORM, CONTENT_TYPE, SCHEMA)

    assert result == expected
    assert extractor._client.chat.completions.create.await_count == 2


def test_chunk_html_small_input() -> None:
    """Small HTML is returned as a single chunk."""
    ext = PhoenixAIExtractor(api_key="sk-test")
    assert ext._chunk_html("<html></html>") == ["<html></html>"]


def test_chunk_html_large_input() -> None:
    """Large HTML is split into multiple chunks at tag boundaries."""
    ext = PhoenixAIExtractor(api_key="sk-test")
    html = "<p>" + "x" * 50000 + "</p>"
    chunks = ext._chunk_html(html, max_tokens=12000)
    assert len(chunks) > 1


@pytest.mark.asyncio
async def test_suggest_selectors_success(extractor: PhoenixAIExtractor) -> None:
    """suggest_selectors returns parsed selector suggestions."""
    suggestions = [
        {"field": "title", "old": "h1", "new": "h2", "confidence": 0.95},
    ]
    extractor._client.chat.completions.create.return_value = _make_response(
        json.dumps(suggestions),
    )

    result = await extractor.suggest_selectors("<html></html>", {"title": "h1"})

    assert result == suggestions


@pytest.mark.asyncio
async def test_suggest_selectors_invalid_json(extractor: PhoenixAIExtractor) -> None:
    """suggest_selectors raises AIJSONParseError for invalid JSON."""
    extractor._client.chat.completions.create.return_value = _make_response("not json")

    with pytest.raises(AIJSONParseError):
        await extractor.suggest_selectors("<html></html>", {"title": "h1"})


@pytest.mark.asyncio
async def test_suggest_selectors_non_array(extractor: PhoenixAIExtractor) -> None:
    """suggest_selectors raises AIJSONParseError when response is not an array."""
    extractor._client.chat.completions.create.return_value = _make_response('{"foo": "bar"}')

    with pytest.raises(AIJSONParseError):
        await extractor.suggest_selectors("<html></html>", {"title": "h1"})


def test_model_aliases_resolve() -> None:
    """PhoenixAIExtractor resolves model aliases to full model names."""
    ext = PhoenixAIExtractor()
    assert ext.MODELS["lightweight"] == "qwen2.5:7b"
    assert ext.MODELS["standard"] == "qwen2.5:7b"
    assert ext.MODELS["enterprise"] == "qwen2.5-coder:32b"
