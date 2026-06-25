"""Global pytest configuration and fixtures for Phoenix Engine."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import factory
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from phoenix.models.config import Config
    from phoenix.models.document import RawResponse
    from phoenix.models.output import (
        Diagnostics,
        ErrorRecord,
        ScrapingResult,
        UnifiedOutput,
    )

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Lazily-created factory classes. Keeping this lazy avoids importing ``phoenix``
# submodules while conftest.py is being loaded, which improves coverage accuracy
# for marker-filtered test runs.
_FACTORY_CACHE: dict[str, type[factory.Factory]] | None = None


# ---------------------------------------------------------------------------
# pytest-asyncio configuration
# ---------------------------------------------------------------------------

pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest-asyncio and register custom markers."""
    config.inicfg["asyncio_mode"] = "auto"
    config.addinivalue_line("markers", "unit: fast, isolated unit tests")
    config.addinivalue_line("markers", "integration: component integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end workflow tests")
    config.addinivalue_line("markers", "slow: tests that take longer than a few seconds")


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_path_fixture(tmp_path: Path) -> Path:
    """Expose pytest's tmp_path as an explicitly named fixture."""
    return tmp_path


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Return a mocked httpx.AsyncClient for unit tests."""
    client = MagicMock()
    client.get = AsyncMock(return_value=MagicMock(status_code=200, text="<html></html>"))
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_browser_context() -> MagicMock:
    """Return a mocked Playwright browser context for unit tests."""
    context = MagicMock()
    page = MagicMock()
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html></html>")
    page.wait_for_selector = AsyncMock()
    page.screenshot = AsyncMock(return_value="screenshot.png")
    context.new_page = AsyncMock(return_value=page)
    context.add_cookies = AsyncMock()
    context.close = AsyncMock()
    return context


@pytest.fixture
def sample_config() -> Config:
    """Return a default Config instance for tests."""
    from phoenix.models.config import Config

    return Config()


# ---------------------------------------------------------------------------
# factory-boy + Faker factories
# ---------------------------------------------------------------------------


def _get_factories() -> dict[str, type[factory.Factory]]:
    """Return a dictionary of factory classes, building them on first call."""
    global _FACTORY_CACHE  # noqa: PLW0603
    if _FACTORY_CACHE is not None:
        return _FACTORY_CACHE

    from phoenix.models.document import RawResponse
    from phoenix.models.output import (
        Diagnostics,
        ErrorRecord,
        ScrapingResult,
        UnifiedOutput,
    )

    class UnifiedOutputFactory(factory.Factory[UnifiedOutput]):
        """Factory for UnifiedOutput model instances."""

        class Meta:
            """Factory metadata."""

            model = UnifiedOutput

        url = factory.Faker("url")
        platform = factory.Faker("word")
        content_type = factory.Iterator(["post", "article", "video", "profile"])
        text = factory.Faker("paragraph", nb_sentences=3)
        author = factory.Faker("name")
        author_url = factory.Faker("url")
        timestamp = factory.Faker("date_time")
        likes = factory.Faker("random_int", min=0, max=100000)
        shares = factory.Faker("random_int", min=0, max=50000)
        comments = factory.Faker("random_int", min=0, max=20000)
        media_urls = factory.List([factory.Faker("image_url"), factory.Faker("image_url")])
        tags = factory.List([factory.Faker("word"), factory.Faker("word"), factory.Faker("word")])
        scraping_strategy = factory.Iterator(["http", "browser"])
        selectors_used = factory.List([factory.Sequence(lambda n: f"div.selector-{n}")])
        ai_assisted = factory.Faker("boolean")
        archive_id = factory.Faker("uuid4")

    class ScrapingResultFactory(factory.Factory[ScrapingResult]):
        """Factory for ScrapingResult model instances."""

        class Meta:
            """Factory metadata."""

            model = ScrapingResult

        success = factory.Faker("boolean")
        url = factory.Faker("url")
        output = factory.SubFactory(UnifiedOutputFactory)
        error = None
        selectors_used = factory.List([factory.Sequence(lambda n: f"div.selector-{n}")])
        fallback_triggered = factory.Faker("boolean", chance_of_getting_true=20)
        ai_assisted = factory.Faker("boolean", chance_of_getting_true=10)
        timing_ms = factory.Dict({"fetch": 100, "extract": 20, "normalize": 5})
        archived_path = factory.Faker("file_path")

    class ErrorRecordFactory(factory.Factory[ErrorRecord]):
        """Factory for ErrorRecord audit log entries."""

        class Meta:
            """Factory metadata."""

            model = ErrorRecord

        error_id = factory.Faker("uuid4")
        code = factory.Iterator(["SCR_001", "SCR_010", "SCR_011", "SCR_030"])
        message = factory.Faker("sentence")
        url = factory.Faker("url")
        platform = factory.Faker("word")
        strategy = factory.Iterator(["http", "browser", None])
        http_status = factory.Iterator([None, 403, 429, 500])
        selectors_tried = factory.List([factory.Sequence(lambda n: f"div.selector-{n}")])
        html_snippet = factory.Faker("text", max_nb_chars=200)
        suggested_fix = factory.Faker("sentence")

    class DiagnosticsFactory(factory.Factory[Diagnostics]):
        """Factory for Diagnostics snapshots."""

        class Meta:
            """Factory metadata."""

            model = Diagnostics

        url = factory.Faker("url")
        platform = factory.Faker("word")
        primary_strategy = factory.Iterator(["http", "browser"])
        strategies_attempted = factory.List(["http", "browser"])
        selectors_tried = factory.List([factory.Sequence(lambda n: f"div.selector-{n}")])
        selector_health = factory.Dict({})
        http_status = factory.Iterator([200, 403, 429, 500])
        response_headers = factory.Dict({"content-type": "text/html"})
        html_size_bytes = factory.Faker("random_int", min=1000, max=500000)
        timing = factory.Dict({"fetch": 150.0, "extract": 25.0, "normalize": 5.0})
        retries = factory.Faker("random_int", min=0, max=3)

    class RawResponseFactory(factory.Factory[RawResponse]):
        """Factory for RawResponse model instances."""

        class Meta:
            """Factory metadata."""

            model = RawResponse

        url = factory.Faker("url")
        final_url = factory.Faker("url")
        status_code = 200
        headers = factory.Dict({"content-type": "text/html"})
        html = factory.Faker("text")
        strategy = factory.Iterator(["http", "browser"])
        screenshot_path = None

    _FACTORY_CACHE = {
        "unified_output": UnifiedOutputFactory,
        "scraping_result": ScrapingResultFactory,
        "error_record": ErrorRecordFactory,
        "diagnostics": DiagnosticsFactory,
        "raw_response": RawResponseFactory,
    }
    return _FACTORY_CACHE


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def unified_output_factory() -> type[factory.Factory]:
    """Return the UnifiedOutput factory class."""
    return _get_factories()["unified_output"]


@pytest.fixture
def scraping_result_factory() -> type[factory.Factory]:
    """Return the ScrapingResult factory class."""
    return _get_factories()["scraping_result"]


@pytest.fixture
def collection_result_factory() -> type[factory.Factory]:
    """Return the ScrapingResult factory class (backward-compatible alias)."""
    return _get_factories()["scraping_result"]


@pytest.fixture
def error_record_factory() -> type[factory.Factory]:
    """Return the ErrorRecord factory class."""
    return _get_factories()["error_record"]


@pytest.fixture
def diagnostics_factory() -> type[factory.Factory]:
    """Return the Diagnostics factory class."""
    return _get_factories()["diagnostics"]


@pytest.fixture
def raw_response_factory() -> type[factory.Factory]:
    """Return the RawResponse factory class."""
    return _get_factories()["raw_response"]


@pytest.fixture
def unified_output() -> UnifiedOutput:
    """Return a built UnifiedOutput instance."""
    return _get_factories()["unified_output"]()


@pytest.fixture
def scraping_result() -> ScrapingResult:
    """Return a built ScrapingResult instance."""
    return _get_factories()["scraping_result"]()


@pytest.fixture
def collection_result() -> ScrapingResult:
    """Return a built ScrapingResult instance (backward-compatible alias)."""
    return _get_factories()["scraping_result"]()


@pytest.fixture
def error_record() -> ErrorRecord:
    """Return a built ErrorRecord instance."""
    return _get_factories()["error_record"]()


@pytest.fixture
def diagnostics() -> Diagnostics:
    """Return a built Diagnostics instance."""
    return _get_factories()["diagnostics"]()


@pytest.fixture
def raw_response() -> RawResponse:
    """Return a built RawResponse instance."""
    return _get_factories()["raw_response"]()


@pytest.fixture
def fixture_html() -> Callable[[str], str]:
    """Return a helper that loads synthetic HTML for a given platform.

    Supported platforms map to the fixture files created for Phase 1:
    ``instagram``, ``x``, ``tiktok``, ``linkedin``, ``facebook``, ``youtube``,
    ``generic``.
    """
    platform_to_file = {
        "instagram": "instagram_post.html",
        "x": "x_tweet.html",
        "tiktok": "tiktok_video.html",
        "linkedin": "linkedin_post.html",
        "facebook": "facebook_post.html",
        "youtube": "youtube_video.html",
        "generic": "generic_page.html",
    }

    def _load(platform: str) -> str:
        file_name = platform_to_file.get(platform)
        if file_name is None:
            raise ValueError(f"Unknown platform fixture: {platform}")
        path = FIXTURES_DIR / file_name
        if not path.exists():
            raise FileNotFoundError(f"HTML fixture not found: {path}")
        return path.read_text(encoding="utf-8")

    return _load


@pytest.fixture
def mock_collector(fixture_html: Callable[[str], str]) -> MagicMock:
    """Return a mock collector that returns a valid RawResponse."""
    from phoenix.models.document import RawResponse

    collector = MagicMock()
    collector.collect = AsyncMock(
        return_value=RawResponse(
            url="https://example.com/placeholder",
            final_url="https://example.com/placeholder",
            status_code=200,
            headers={"content-type": "text/html"},
            html=fixture_html("instagram"),
            strategy="http",
        ),
    )
    return collector
