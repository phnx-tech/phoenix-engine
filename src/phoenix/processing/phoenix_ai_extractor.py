"""Phoenix AI extractor for local AI-assisted HTML extraction.

Phoenix AI is the engine's built-in intelligence layer. It talks to a local
Ollama instance over its OpenAI-compatible endpoint by default, so no external
API keys or cloud services are required.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict, cast

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError

if TYPE_CHECKING:
    from openai.types import CompletionUsage
    from openai.types.chat import ChatCompletionMessageParam


class AIExtractionError(Exception):
    """Raised when Phoenix AI extraction fails after all retries."""


class AIJSONParseError(Exception):
    """Raised when a Phoenix AI response cannot be parsed as valid JSON."""


class _CacheEntry(TypedDict):
    data: dict[str, Any]
    timestamp: datetime


class PhoenixAIExtractor:
    """AI-powered HTML extraction using Phoenix AI (local Ollama by default)."""

    MODELS: ClassVar[dict[str, str]] = {
        "lightweight": "qwen2.5:7b",
        "standard": "qwen2.5:7b",
        "enterprise": "qwen2.5-coder:32b",
    }

    DEFAULT_MAX_CHARS_PER_CHUNK = 48000  # ~12000 tokens at 4 chars/token
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 2.0
    DEFAULT_MAX_TOKENS = 8192
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_CACHE_TTL = 3600

    def __init__(  # noqa: PLR0913
        self,
        api_key: str | None = "ollama",
        base_url: str = "http://localhost:11434/v1",
        default_model: str = "qwen2.5:7b",
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = DEFAULT_TIMEOUT,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        max_budget_usd: float = 0.0,
    ) -> None:
        """Initialize the Phoenix AI extractor.

        Args:
            api_key: API key for the AI endpoint. Defaults to ``"ollama"``
                because local Ollama does not require authentication.
            base_url: OpenAI-compatible API base URL. Defaults to the local
                Ollama endpoint.
            default_model: Default model for extraction.
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.
            timeout: API request timeout in seconds.
            cache_ttl: Response cache TTL in seconds.
            max_budget_usd: Hard budget cap for estimated API spend (0 = unlimited).
        """
        self.api_key = api_key or "ollama"
        self.base_url = base_url
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.max_budget_usd = max_budget_usd
        self._cache: dict[str, _CacheEntry] = {}
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
        )
        self.total_tokens_used = 0
        self.total_api_calls = 0
        self.estimated_cost_usd = 0.0

    def _check_budget(self) -> None:
        """Raise if the configured budget cap has been reached."""
        if self.max_budget_usd > 0 and self.estimated_cost_usd >= self.max_budget_usd:
            raise AIExtractionError(
                f"Phoenix AI budget exceeded: ${self.estimated_cost_usd:.4f} >= "
                f"${self.max_budget_usd:.4f}. Set max_budget_usd=0 to disable.",
            )

    async def _try_extract(
        self,
        model_name: str,
        messages: list[ChatCompletionMessageParam],
        *,
        strict: bool,
    ) -> tuple[Any, dict[str, Any] | list[Any] | None, Exception | None]:
        """Call the model and parse JSON with retries.

        Returns:
            Tuple of (response, parsed_data, last_exception). ``response`` and
            ``parsed_data`` are ``None`` when all attempts failed.
        """
        last_exception: Exception | None = None
        for attempt in range(self.DEFAULT_MAX_RETRIES):
            try:
                response = await self._client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                content = response.choices[0].message.content or ""
                extracted_data = self._parse_json(content.strip(), strict=strict)
            except (RateLimitError, APIError) as exc:
                last_exception = exc
                if isinstance(exc, RateLimitError) and attempt < self.DEFAULT_MAX_RETRIES - 1:
                    await asyncio.sleep(self.DEFAULT_BASE_DELAY * (2**attempt))
                    continue
                if isinstance(exc, APITimeoutError) and attempt < self.DEFAULT_MAX_RETRIES - 1:
                    await asyncio.sleep(self.DEFAULT_BASE_DELAY)
                    continue
                break
            except APITimeoutError as exc:
                last_exception = exc
                if attempt < self.DEFAULT_MAX_RETRIES - 1:
                    await asyncio.sleep(self.DEFAULT_BASE_DELAY)
                    continue
                break
            else:
                return response, extracted_data, None

        return None, None, last_exception

    def _cache_key(self, html_hash: str, schema_hash: str) -> str:
        """Generate cache key from HTML and schema hashes."""
        return hashlib.sha256(f"{html_hash}:{schema_hash}".encode()).hexdigest()[:32]

    def _get_cached(self, cache_key: str) -> dict[str, Any] | None:
        """Return cached response if still valid."""
        entry = self._cache.get(cache_key)
        if entry is None:
            return None
        if datetime.now(UTC) - entry["timestamp"] > timedelta(seconds=self.cache_ttl):
            del self._cache[cache_key]
            return None
        return entry["data"]

    def _set_cached(self, cache_key: str, data: dict[str, Any]) -> None:
        """Cache response with TTL."""
        self._cache[cache_key] = _CacheEntry(
            data=data,
            timestamp=datetime.now(UTC),
        )

    @staticmethod
    def _count_tokens(text: str) -> int:
        """Estimate token count (approximate: 1 token ~ 4 chars)."""
        return max(len(text) // 4, 1)

    @staticmethod
    def _message_text(message: ChatCompletionMessageParam) -> str:
        """Extract text content from a message param for token estimation."""
        content = message.get("content")
        if isinstance(content, str):
            return content
        return ""

    def _chunk_html(self, html: str, max_tokens: int = 12000) -> list[str]:
        """Split large HTML into token-safe chunks for API submission."""
        max_chars = max_tokens * 4
        if len(html) <= max_chars:
            return [html]

        chunks: list[str] = []
        start = 0
        while start < len(html):
            end = start + max_chars
            chunk = html[start:end]
            if end < len(html):
                last_tag = chunk.rfind("<")
                if last_tag > max_chars * 0.8:
                    chunk = chunk[:last_tag]
                    end = start + last_tag
            chunks.append(chunk)
            start = end
        return chunks

    def _build_messages(
        self,
        url: str,
        platform: str,
        content_type: str,
        schema_description: str,
        html_chunk: str,
    ) -> list[ChatCompletionMessageParam]:
        """Build the chat messages for extraction."""
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
            f"HTML:\n```html\n{html_chunk}\n```\n\n"
            f"Extract the following fields as JSON:\n{schema_description}\n\n"
            f"Return ONLY valid JSON. No markdown, no explanation."
        )
        return cast(
            "list[ChatCompletionMessageParam]",
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

    def _parse_json(self, content: str, *, strict: bool = True) -> dict[str, Any] | list[Any]:
        """Parse JSON from model response, stripping code fences if needed.

        Args:
            content: Raw model response text.
            strict: If ``True`` (default), require a JSON object. If ``False``,
                arrays are also accepted.

        Returns:
            Parsed JSON dict or list.
        """
        content = content.strip()
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            cleaned = content
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            cleaned = cleaned.removesuffix("```").strip()
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError as parse_exc:
                raise AIJSONParseError(
                    f"Phoenix AI response is not valid JSON: {parse_exc}",
                ) from exc
        if strict and not isinstance(parsed, dict):
            raise AIJSONParseError("Phoenix AI response JSON is not an object.")
        return cast("dict[str, Any] | list[Any]", parsed)

    def _track_usage(self, usage: CompletionUsage | None) -> int:
        """Track token usage and estimated cost from API response usage."""
        if usage is None:
            return 0
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        total_tokens = getattr(usage, "total_tokens", 0) or 0
        self.total_tokens_used += total_tokens
        self.estimated_cost_usd += prompt_tokens * 0.00001 + completion_tokens * 0.00003
        return total_tokens

    async def extract(  # noqa: PLR0913
        self,
        html: str,
        url: str,
        platform: str,
        content_type: str,
        schema_description: str,
        model: str | None = None,
        *,
        strict: bool = True,
    ) -> dict[str, Any] | list[Any]:
        """Extract structured data from HTML using Phoenix AI.

        Args:
            html: Raw HTML content to parse.
            url: Source URL of the HTML.
            platform: Platform identifier.
            content_type: Type of content.
            schema_description: JSON schema describing desired output fields.
            model: Model key (``lightweight``, ``standard``, ``enterprise``) or model name.
            strict: If ``True`` (default), require a JSON object response.

        Returns:
            Parsed JSON dict with extracted fields, or a list when ``strict`` is
            ``False``.

        Raises:
            AIExtractionError: If API call fails after all retries.
            AIJSONParseError: If response cannot be parsed as valid JSON.
        """
        html_hash = hashlib.sha256(html.encode()).hexdigest()[:16]
        schema_hash = hashlib.sha256(schema_description.encode()).hexdigest()[:16]
        cache_key = self._cache_key(html_hash, schema_hash)

        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._check_budget()

        model_name = self.MODELS.get(model, self.default_model) if model else self.default_model

        chunks = self._chunk_html(html)
        chunk = chunks[0]

        messages = self._build_messages(url, platform, content_type, schema_description, chunk)
        estimated_tokens = self._count_tokens(
            self._message_text(messages[0]) + self._message_text(messages[1]),
        )
        self.total_tokens_used += estimated_tokens
        self.total_api_calls += 1

        response, extracted_data, last_exception = await self._try_extract(
            model_name,
            messages,
            strict=strict,
        )

        if response is not None and extracted_data is not None:
            self._track_usage(response.usage)
            if isinstance(extracted_data, dict):
                self._set_cached(cache_key, extracted_data)
            return extracted_data

        if isinstance(last_exception, RateLimitError):
            raise AIExtractionError(
                f"Rate limited after {self.DEFAULT_MAX_RETRIES} retries. "
                "Consider increasing delay between requests.",
            ) from last_exception
        if isinstance(last_exception, APITimeoutError):
            raise AIExtractionError(
                f"Phoenix AI timeout after {self.DEFAULT_MAX_RETRIES} retries. "
                f"Timeout: {self.timeout}s",
            ) from last_exception
        if isinstance(last_exception, APIError):
            raise AIExtractionError(
                f"Phoenix AI error: {last_exception.code} - {last_exception.message}",
            ) from last_exception
        raise AIExtractionError("Phoenix AI extraction failed after all retries.")

    async def suggest_selectors(
        self,
        html_sample: str,
        old_selectors: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Use Phoenix AI to suggest new selectors after a layout change.

        Args:
            html_sample: Representative HTML from the new layout.
            old_selectors: Dict of field names to old (now failing) selectors.

        Returns:
            List of dicts with ``field``, ``old``, ``new``, ``confidence`` keys.

        Raises:
            AIExtractionError: If the API call fails.
            AIJSONParseError: If the response cannot be parsed.
        """
        prompt = (
            "The following CSS selectors no longer match the HTML "
            "(the page layout changed).\n\n"
            f"Old selectors: {json.dumps(old_selectors, indent=2)}\n\n"
            "Current HTML structure:\n```html\n"
            f"{html_sample[:8000]}\n"
            "```\n\n"
            "Suggest new CSS selectors that extract the same data. "
            'Return as JSON array: [{"field": "name", "old": "...", '
            '"new": "...", "confidence": 0.95}]'
        )
        messages = cast(
            "list[ChatCompletionMessageParam]",
            [
                {
                    "role": "system",
                    "content": (
                        "You are a CSS selector expert. Suggest precise, "
                        "stable selectors that will work across minor layout changes. "
                        "Prefer data-testid, role, and semantic attributes over classes. "
                        "Return ONLY valid JSON array."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        response = await self._client.chat.completions.create(
            model=self.default_model,
            messages=messages,
            temperature=0.1,
            max_tokens=4096,
        )
        content = response.choices[0].message.content or ""
        content = content.strip()
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            cleaned = content
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            cleaned = cleaned.removesuffix("```").strip()
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError as parse_exc:
                raise AIJSONParseError(
                    f"Phoenix AI selector response is not valid JSON: {parse_exc}",
                ) from exc
        if isinstance(parsed, dict):
            for key in ("selectors", "suggestions", "result", "results"):
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                raise AIJSONParseError("Phoenix AI selector response JSON is not an array.")
        if not isinstance(parsed, list):
            raise AIJSONParseError("Phoenix AI selector response JSON is not an array.")
        return parsed


__all__ = ["AIExtractionError", "AIJSONParseError", "PhoenixAIExtractor"]
