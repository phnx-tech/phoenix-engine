"""Unit tests for AIAssistant."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from phoenix.models.document import RawResponse
from phoenix.processing.ai_assistant import AIAssistant

pytestmark = pytest.mark.unit

URL = "https://example.com/article/1"


@pytest.fixture
def mock_extractor() -> MagicMock:
    """Return a mocked PhoenixAIExtractor."""
    extractor = MagicMock()
    extractor.extract = AsyncMock(return_value={"title": "AI title", "author": "AI author"})
    extractor.suggest_selectors = AsyncMock(
        return_value=[{"field": "title", "old": "h1", "new": "h2", "confidence": 0.9}],
    )
    extractor.total_tokens_used = 123
    return extractor


@pytest.fixture
def raw_response() -> RawResponse:
    """Return a sample raw response."""
    return RawResponse(
        url=URL,
        final_url=URL,
        status_code=200,
        headers={},
        html="<html><body>Hello</body></html>",
        strategy="http",
        timestamp=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_extract_calls_phoenix_ai_extractor(
    mock_extractor: MagicMock,
    raw_response: RawResponse,
) -> None:
    """AIAssistant.extract delegates to PhoenixAIExtractor.extract."""
    assistant = AIAssistant(extractor=mock_extractor)

    result = await assistant.extract(raw_response, "generic", "post")

    assert result["title"] == "AI title"
    assert result["author"] == "AI author"
    mock_extractor.extract.assert_awaited_once()


@pytest.mark.asyncio
async def test_extract_uses_final_url(
    mock_extractor: MagicMock,
    raw_response: RawResponse,
) -> None:
    """AIAssistant passes the final URL to the extractor."""
    assistant = AIAssistant(extractor=mock_extractor)
    raw = raw_response
    raw.final_url = "https://example.com/final"

    await assistant.extract(raw, "generic", "post")

    call_kwargs = mock_extractor.extract.await_args.kwargs
    assert call_kwargs["url"] == "https://example.com/final"


@pytest.mark.asyncio
async def test_extract_schema_description_includes_unified_fields(
    mock_extractor: MagicMock,
    raw_response: RawResponse,
) -> None:
    """AIAssistant builds a schema description from UnifiedOutput fields."""
    assistant = AIAssistant(extractor=mock_extractor)

    await assistant.extract(raw_response, "generic", "post")

    schema = mock_extractor.extract.await_args.kwargs["schema_description"]
    assert "title" in schema
    assert "text" in schema
    assert "author" in schema


@pytest.mark.asyncio
async def test_suggest_selectors_delegates(mock_extractor: MagicMock) -> None:
    """AIAssistant.suggest_selectors delegates to PhoenixAIExtractor."""
    assistant = AIAssistant(extractor=mock_extractor)

    result = await assistant.suggest_selectors("<html></html>", {"title": "h1"})

    assert result[0]["field"] == "title"
    mock_extractor.suggest_selectors.assert_awaited_once_with(
        "<html></html>",
        {"title": "h1"},
    )


def test_default_extractor_created_when_none_provided() -> None:
    """AIAssistant creates a default PhoenixAIExtractor when none is supplied."""
    with patch("phoenix.processing.ai_assistant.PhoenixAIExtractor") as mock_cls:
        mock_cls.return_value = MagicMock()
        AIAssistant()
        mock_cls.assert_called_once()
