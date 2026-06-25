"""Unit tests for Phoenix Engine core data models."""

from __future__ import annotations

from datetime import datetime

import pytest
from bs4 import BeautifulSoup

from phoenix.models import (
    Config,
    HTMLDocument,
    ScrapingStrategy,
    Session,
    UnifiedOutput,
)
from phoenix.models.output import (
    CollectionResult,
    Diagnostics,
    ErrorRecord,
    ScrapingResult,
)

pytestmark = pytest.mark.unit


class TestUnifiedOutput:
    """Tests for UnifiedOutput creation and validation."""

    def test_unified_output_defaults(self) -> None:
        """UnifiedOutput can be created with required fields only."""
        output = UnifiedOutput(url="https://example.com", platform="generic")

        assert output.url == "https://example.com"
        assert output.platform == "generic"
        assert output.content_type == "post"
        assert output.media_urls == []
        assert output.tags == []
        assert output.scraped_at is not None

    def test_unified_output_full(self, unified_output: UnifiedOutput) -> None:
        """Factory-built UnifiedOutput passes validation."""
        assert isinstance(unified_output.url, str)
        assert isinstance(unified_output.platform, str)
        assert isinstance(unified_output.likes, int) or unified_output.likes is None
        assert isinstance(unified_output.scraped_at, datetime)

    def test_unified_output_extra_fields_allowed(self) -> None:
        """UnifiedOutput allows extra fields for platform-specific data."""
        output = UnifiedOutput(
            url="https://example.com",
            platform="generic",
            custom_field="extra",
        )

        assert output.custom_field == "extra"


class TestScrapingResult:
    """Tests for ScrapingResult creation and validation."""

    def test_scraping_result_defaults(self) -> None:
        """ScrapingResult can be created with required fields only."""
        result = ScrapingResult(success=True)

        assert result.success is True
        assert result.output is None
        assert result.selectors_used == []
        assert result.fallback_triggered is False

    def test_scraping_result_with_output(self, scraping_result: ScrapingResult) -> None:
        """Factory-built ScrapingResult contains a valid UnifiedOutput."""
        assert isinstance(scraping_result, ScrapingResult)
        if scraping_result.output is not None:
            assert isinstance(scraping_result.output, UnifiedOutput)

    def test_collection_result_alias(self, scraping_result: ScrapingResult) -> None:
        """CollectionResult is a backward-compatible alias for ScrapingResult."""
        assert CollectionResult is ScrapingResult
        assert isinstance(scraping_result, CollectionResult)


class TestErrorRecord:
    """Tests for ErrorRecord creation and immutability."""

    def test_error_record_creation(self, error_record: ErrorRecord) -> None:
        """Factory-built ErrorRecord has required fields."""
        assert isinstance(error_record.error_id, str)
        assert isinstance(error_record.code, str)
        assert isinstance(error_record.message, str)
        assert isinstance(error_record.url, str)
        assert isinstance(error_record.timestamp, datetime)

    def test_error_record_is_frozen(self, error_record: ErrorRecord) -> None:
        """ErrorRecord instances are immutable."""
        with pytest.raises(ValueError, match="frozen"):  # pydantic frozen model raises ValueError
            error_record.message = "changed"


class TestDiagnostics:
    """Tests for Diagnostics creation and defaults."""

    def test_diagnostics_creation(self, diagnostics: Diagnostics) -> None:
        """Factory-built Diagnostics contains required fields."""
        assert isinstance(diagnostics.url, str)
        assert isinstance(diagnostics.timestamp, datetime)

    def test_diagnostics_defaults(self) -> None:
        """Diagnostics can be created with just a URL."""
        diag = Diagnostics(url="https://example.com")

        assert diag.platform is None
        assert diag.strategies_attempted == []
        assert diag.selectors_tried == []
        assert diag.retries == 0

    def test_diagnostics_strategy_used_alias(self) -> None:
        """strategy_used is a backward-compatible alias for primary_strategy."""
        diag = Diagnostics(url="https://example.com", primary_strategy="http")

        assert diag.strategy_used == "http"
        assert diag.primary_strategy == "http"


class TestHTMLDocument:
    """Tests for HTMLDocument model."""

    def test_html_document_creation(self) -> None:
        """HTMLDocument can be instantiated with a BeautifulSoup object."""
        soup = BeautifulSoup("<html><body>Hello</body></html>", "html.parser")
        document = HTMLDocument(
            url="https://example.com",
            raw_html="<html><body>Hello</body></html>",
            soup=soup,
        )

        assert document.url == "https://example.com"
        assert document.status_code == 200
        assert document.soup.get_text() == "Hello"


class TestSession:
    """Tests for Session model."""

    def test_session_creation(self) -> None:
        """Session can be instantiated with platform and cookies."""
        session = Session(platform="generic", cookies=[{"name": "sessionid", "value": "abc"}])

        assert session.platform == "generic"
        assert len(session.cookies) == 1
        assert session.created_at is not None


class TestConfig:
    """Tests for Config model."""

    def test_config_defaults(self) -> None:
        """Config has sensible defaults."""
        config = Config()

        assert config.timeout == 30.0
        assert config.archive_enabled is True
        assert config.ai_enabled is False
        assert config.ai_base_url == "http://localhost:11434/v1"
        assert config.ai_model == "qwen2.5:7b"
        assert config.stealth_enabled is False
        assert config.stealth_profiles == ["chrome_windows"]
        assert config.proxy_list == []
        assert config.delay_min_ms == 0.0
        assert config.delay_max_ms == 0.0
        assert config.captcha_action == "flag"

    def test_config_openai_property(self) -> None:
        """Config exposes a PhoenixAIConfig derived from flattened settings."""
        config = Config(
            ai_enabled=True,
            ai_api_key="sk-test",
            ai_model="qwen2.5:7b",
            ai_temperature=0.2,
            ai_max_tokens=4096,
            ai_timeout=60.0,
            ai_cache_ttl=7200,
        )
        phoenix_ai_config = config.phoenix_ai

        assert phoenix_ai_config.api_key == "sk-test"
        assert phoenix_ai_config.model == "qwen2.5:7b"
        assert phoenix_ai_config.temperature == 0.2
        assert phoenix_ai_config.max_tokens == 4096
        assert phoenix_ai_config.timeout == 60.0
        assert phoenix_ai_config.cache_ttl == 7200

    def test_config_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config reads AI settings from PHOENIX_* environment variables."""
        monkeypatch.setenv("PHOENIX_AI_ENABLED", "true")
        monkeypatch.setenv("PHOENIX_AI_API_KEY", "env-key")
        monkeypatch.setenv("PHOENIX_AI_MODEL", "qwen2.5:7b")

        config = Config()

        assert config.ai_enabled is True
        assert config.ai_api_key == "env-key"
        assert config.ai_model == "qwen2.5:7b"


class TestScrapingStrategy:
    """Tests for the ScrapingStrategy enum."""

    @pytest.mark.parametrize(
        ("member", "expected"),
        [
            (ScrapingStrategy.HTTP, "http"),
            (ScrapingStrategy.BROWSER, "browser"),
        ],
    )
    def test_scraping_strategy_values(self, member: ScrapingStrategy, expected: str) -> None:
        """ScrapingStrategy members have the documented string values."""
        assert member.value == expected
        assert str(member) == expected

    def test_scraping_strategy_from_string(self) -> None:
        """ScrapingStrategy can be constructed from its string values."""
        assert ScrapingStrategy("http") is ScrapingStrategy.HTTP
        assert ScrapingStrategy("browser") is ScrapingStrategy.BROWSER
