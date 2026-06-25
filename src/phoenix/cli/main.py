"""Typer CLI for Phoenix Engine."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phoenix.collectors.base import Collector

import typer
from rich.console import Console

from phoenix import __version__
from phoenix.architect.explorer import PageSnapshot
from phoenix.architect.fixture_generator import FixtureGenerator
from phoenix.architect.orchestrator import PhoenixArchitect
from phoenix.architect.researcher import Researcher
from phoenix.collectors.browser import BrowserCollector
from phoenix.collectors.browser_pool import BrowserPool
from phoenix.collectors.direct import DirectCollector
from phoenix.engine import PhoenixEngine
from phoenix.exceptions import LicenseError
from phoenix.infrastructure.config import load_config
from phoenix.infrastructure.license_manager import LicenseManager
from phoenix.infrastructure.rate_limiter import RateLimiter
from phoenix.models.config import Config
from phoenix.plugins.loader import PluginLoader

if TYPE_CHECKING:
    from phoenix.models import ScrapingResult

app = typer.Typer(
    name="phoenix",
    help="Universal pure web scraping engine",
    no_args_is_help=True,
)

plugins_app = typer.Typer(
    name="plugins",
    help="Manage Phoenix Engine scraper plugins.",
)
app.add_typer(plugins_app)

config_app = typer.Typer(
    name="config",
    help="Inspect Phoenix Engine configuration.",
)
app.add_typer(config_app)

architect_app = typer.Typer(
    name="architect",
    help="Autonomous adapter generation with PhoenixArchitect.",
)
app.add_typer(architect_app)

license_app = typer.Typer(
    name="license",
    help="Generate and inspect offline license keys.",
)
app.add_typer(license_app)

console = Console()

_state: dict[str, Any] = {}


def _version_callback(*, value: bool) -> None:
    """Print version and exit when ``--version`` is requested."""
    if value:
        typer.echo(f"phoenix-engine {__version__}")
        raise typer.Exit


@app.callback()
def main(
    *,
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a JSON/YAML/TOML configuration file.",
    ),
) -> None:
    """Phoenix Engine CLI."""
    _state["config_path"] = config


def _load_engine_config() -> Config | None:
    """Load configuration from the global ``--config`` path if provided."""
    config_path = _state.get("config_path")
    if config_path is not None:
        return load_config(search_paths=[config_path.parent])
    return None


def _build_real_collectors(
    config: Config,
    rate_limiter: RateLimiter,
) -> dict[str, Collector]:
    """Build real HTTP and browser collectors for CLI use."""
    browser_pool = BrowserPool(
        max_contexts=2,
        stealth_enabled=config.stealth_enabled,
    )
    return {
        "http": DirectCollector(config, rate_limiter),
        "browser": BrowserCollector(browser_pool, rate_limiter),
    }


@app.command(name="version")
def version_command() -> None:
    """Show version information."""
    typer.echo(f"phoenix-engine {__version__}")


def _build_common_options(
    *,
    archive: bool,
    strategy: str | None,
    timeout: float | None,
    max_retries: int | None,
) -> dict[str, object]:
    """Build scraping options shared by single and batch commands."""
    options: dict[str, object] = {
        "archive": archive,
        "strategy": strategy,
    }
    if timeout is not None:
        options["timeout"] = timeout
    if max_retries is not None:
        options["max_retries"] = max_retries
    return options


@app.command(name="scrape")
def scrape_command(
    url: str = typer.Argument(..., help="URL to scrape data from"),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout).",
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json or pretty.",
    ),
    strategy: str | None = typer.Option(
        None,
        "--strategy",
        "-s",
        help="Force scraping strategy: http or browser.",
    ),
    archive: bool = typer.Option(
        True,
        "--archive/--no-archive",
        help="Enable or disable source archiving.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed diagnostics.",
    ),
    timeout: float | None = typer.Option(
        None,
        "--timeout",
        "-t",
        help="Request timeout in seconds.",
    ),
    max_retries: int | None = typer.Option(
        None,
        "--max-retries",
        help="Maximum retry attempts for transient failures.",
    ),
    ai: bool = typer.Option(
        False,
        "--ai",
        help="Enable Phoenix AI fallback extraction.",
    ),
    real: bool = typer.Option(
        False,
        "--real",
        help="Use real HTTP/browser collectors instead of stub collectors.",
    ),
) -> None:
    """Scrape data from a single URL."""
    config = _load_engine_config()
    options = _build_common_options(
        archive=archive,
        strategy=strategy,
        timeout=timeout,
        max_retries=max_retries,
    )

    async def _run() -> ScrapingResult:
        engine_config = config if config is not None else Config()
        if ai:
            engine_config.ai_enabled = True
        if real:
            rate_limiter = RateLimiter(engine_config)
            collectors = _build_real_collectors(engine_config, rate_limiter)
        else:
            rate_limiter = None
            collectors = None
        async with PhoenixEngine(
            config=engine_config,
            collectors=collectors,
            rate_limiter=rate_limiter,
        ) as engine:
            return await engine.scrape(url, **options)

    try:
        result = asyncio.run(_run())
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    _write_result(result, output=output, output_format=output_format, verbose=verbose)

    if not result.success:
        raise typer.Exit(code=2)


@app.command(name="scrape-batch")
def scrape_batch_command(
    urls: list[str] = typer.Argument(..., help="URLs to scrape data from"),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout).",
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json or pretty.",
    ),
    strategy: str | None = typer.Option(
        None,
        "--strategy",
        "-s",
        help="Force scraping strategy: http or browser.",
    ),
    archive: bool = typer.Option(
        True,
        "--archive/--no-archive",
        help="Enable or disable source archiving.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed diagnostics.",
    ),
    timeout: float | None = typer.Option(
        None,
        "--timeout",
        "-t",
        help="Request timeout in seconds.",
    ),
    max_retries: int | None = typer.Option(
        None,
        "--max-retries",
        help="Maximum retry attempts for transient failures.",
    ),
    max_concurrency: int = typer.Option(
        5,
        "--concurrency",
        "-j",
        help="Maximum concurrent scrapes.",
    ),
    ai: bool = typer.Option(
        False,
        "--ai",
        help="Enable Phoenix AI fallback extraction.",
    ),
    real: bool = typer.Option(
        False,
        "--real",
        help="Use real HTTP/browser collectors instead of stub collectors.",
    ),
) -> None:
    """Scrape data from multiple URLs concurrently."""
    config = _load_engine_config()
    options = _build_common_options(
        archive=archive,
        strategy=strategy,
        timeout=timeout,
        max_retries=max_retries,
    )

    async def _run() -> list[ScrapingResult]:
        engine_config = config if config is not None else Config()
        if ai:
            engine_config.ai_enabled = True
        if real:
            rate_limiter = RateLimiter(engine_config)
            collectors = _build_real_collectors(engine_config, rate_limiter)
        else:
            rate_limiter = None
            collectors = None
        async with PhoenixEngine(
            config=engine_config,
            collectors=collectors,
            rate_limiter=rate_limiter,
        ) as engine:
            return await engine.scrape_batch(
                urls,
                max_concurrency=max_concurrency,
                **options,
            )

    try:
        results = asyncio.run(_run())
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    data = {
        "count": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "results": [r.model_dump(mode="json") for r in results],
    }

    if output_format.lower() == "pretty":
        output_text = _format_pretty(data)
    else:
        output_text = json.dumps(data, indent=2, ensure_ascii=False)

    if output:
        output.write_text(output_text, encoding="utf-8")
        typer.echo(f"Batch results written to {output}")
    else:
        typer.echo(output_text)

    if any(not r.success for r in results):
        raise typer.Exit(code=2)


def _write_result(
    result: ScrapingResult,
    *,
    output: Path | None,
    output_format: str,
    verbose: bool,
) -> None:
    """Serialize a single scraping result to stdout or a file."""
    data = result.model_dump(mode="json")
    if verbose and result.diagnostics is not None:
        data["diagnostics"] = result.diagnostics.model_dump(mode="json")

    if output_format.lower() == "pretty":
        output_text = _format_pretty(data)
    else:
        output_text = json.dumps(data, indent=2, ensure_ascii=False)

    if output:
        output.write_text(output_text, encoding="utf-8")
        typer.echo(f"Result written to {output}")
    else:
        typer.echo(output_text)


@plugins_app.command(name="list")
def plugins_list_command() -> None:
    """List installed scraper plugins."""
    loader = PluginLoader()
    loader.load_builtin_adapters()
    manifests = loader.list_adapters()

    if not manifests:
        typer.echo("No plugins installed.")
        return

    table_data = [
        {
            "name": manifest.name,
            "version": manifest.version,
            "platforms": manifest.platforms,
            "url_patterns": manifest.url_patterns,
        }
        for manifest in manifests
    ]

    console.print_json(data=table_data)


@config_app.command(name="show")
def config_show_command(
    hide_secrets: bool = typer.Option(
        True,
        "--hide-secrets/--show-secrets",
        help="Mask sensitive values such as API keys.",
    ),
) -> None:
    """Show the effective configuration."""
    config = _load_engine_config() or Config()
    data = config.model_dump(mode="json")
    if hide_secrets:
        if data.get("ai_api_key"):
            data["ai_api_key"] = "***"
        if data.get("license_secret"):
            data["license_secret"] = "***"  # noqa: S105
    console.print_json(data=data)


@app.command(name="discover")
def discover_command(
    query: str = typer.Argument(..., help="Search query or natural-language goal."),
    engine: str = typer.Option(
        "duckduckgo",
        "--engine",
        "-e",
        help="Search engine: duckduckgo or serpapi.",
    ),
    max_results: int = typer.Option(
        10,
        "--max-results",
        "-n",
        help="Maximum candidate URLs to return.",
    ),
) -> None:
    """Discover candidate target URLs for a query."""

    async def _run() -> list[dict[str, Any]]:
        researcher = Researcher()
        results = await researcher.discover(
            query,
            engine=engine,
            max_results=max_results,
        )
        return [dataclasses.asdict(result) for result in results]

    try:
        data = asyncio.run(_run())
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    console.print_json(data=data)


@architect_app.command(name="generate")
def architect_generate_command(
    goal: str | None = typer.Option(
        None,
        "--goal",
        "-g",
        help="Natural-language scraping goal (triggers search discovery).",
    ),
    url: str | None = typer.Option(
        None,
        "--url",
        "-u",
        help="Single target URL (skips search discovery).",
    ),
    max_pages: int = typer.Option(
        2,
        "--max-pages",
        help="Maximum pagination pages to collect per candidate.",
    ),
    max_results: int = typer.Option(
        3,
        "--max-results",
        help="Maximum URLs to discover when --goal is used.",
    ),
    engine: str = typer.Option(
        "duckduckgo",
        "--engine",
        help="Search engine for discovery.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Regenerate even if an adapter already exists.",
    ),
    with_fixtures: bool = typer.Option(
        False,
        "--with-fixtures",
        help="Generate pytest fixtures and a unit test for each adapter.",
    ),
    fixtures_dir: Path = typer.Option(
        Path("tests/fixtures/html"),
        "--fixtures-dir",
        help="Directory for generated HTML fixtures.",
    ),
    tests_dir: Path = typer.Option(
        Path("tests/unit"),
        "--tests-dir",
        help="Directory for generated unit tests.",
    ),
) -> None:
    """Generate site-specific adapters with PhoenixArchitect."""
    if not goal and not url:
        raise typer.BadParameter("Provide either --goal or --url")

    fixture_generator = FixtureGenerator(
        fixtures_dir=fixtures_dir,
        tests_dir=tests_dir,
    )

    async def _run() -> list[dict[str, object]]:
        architect = PhoenixArchitect(fixture_generator=fixture_generator)
        if url is not None:
            adapter, report = await architect.generate_adapter(
                url,
                max_pages=max_pages,
                force=force,
                with_fixtures=with_fixtures,
            )
            return [
                {
                    "url": url,
                    "platform": adapter.manifest.platforms[0],
                    "name": adapter.manifest.name,
                    "score": report.score,
                },
            ]
        assert goal is not None  # noqa: S101
        return await architect.generate_adapters_for_goal(
            goal,
            max_pages=max_pages,
            max_results=max_results,
            engine=engine,
            with_fixtures=with_fixtures,
        )

    try:
        data = asyncio.run(_run())
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    console.print_json(data=data)


@architect_app.command(name="fixtures")
def architect_fixtures_command(
    platform: str = typer.Argument(..., help="Platform identifier for the generated fixture set."),
    snapshot_dir: Path = typer.Option(
        ...,
        "--snapshot-dir",
        help="Directory containing existing HTML snapshot files.",
    ),
    fixtures_dir: Path = typer.Option(
        Path("tests/fixtures/html"),
        "--fixtures-dir",
        help="Directory for generated HTML fixtures.",
    ),
    tests_dir: Path = typer.Option(
        Path("tests/unit"),
        "--tests-dir",
        help="Directory for generated unit tests.",
    ),
) -> None:
    """Generate pytest fixtures and a unit test from existing HTML snapshots."""
    if not snapshot_dir.exists():
        raise typer.BadParameter(f"Snapshot directory not found: {snapshot_dir}")

    html_files = sorted(snapshot_dir.glob("*.html"))
    if not html_files:
        raise typer.BadParameter(f"No .html files found in {snapshot_dir}")

    snapshots = [
        PageSnapshot(
            url=f"file://{html_file.resolve()}",
            html=html_file.read_text(encoding="utf-8"),
            page_number=index,
        )
        for index, html_file in enumerate(html_files, start=1)
    ]

    generator = FixtureGenerator(fixtures_dir=fixtures_dir, tests_dir=tests_dir)
    fixture_set = generator.generate(platform, snapshots)
    console.print_json(
        data={
            "platform": fixture_set.platform,
            "fixture_dir": str(fixture_set.fixture_dir),
            "test_path": str(fixture_set.test_path),
            "html_count": len(fixture_set.html_paths),
        },
    )


@license_app.command(name="generate")
def license_generate_command(
    count: int = typer.Option(
        1,
        "--count",
        "-n",
        help="Number of license keys to generate.",
        min=1,
        max=100,
    ),
    expires: str | None = typer.Option(
        None,
        "--expires",
        "-e",
        help="Expiration date as ISO-8601 (e.g. 2026-07-31).",
    ),
    max_uses: int | None = typer.Option(
        None,
        "--max-uses",
        "-u",
        help="Maximum number of successful validations.",
        min=1,
    ),
    note: str = typer.Option(
        "",
        "--note",
        help="Optional note embedded in the license payload.",
    ),
    secret: str | None = typer.Option(
        None,
        "--secret",
        help="HMAC signing secret (defaults to PHOENIX_LICENSE_SECRET env var).",
    ),
) -> None:
    """Generate signed Phoenix Engine license keys."""
    signing_secret = secret or os.getenv("PHOENIX_LICENSE_SECRET")
    if not signing_secret:
        typer.echo(
            "Error: Provide --secret or set the PHOENIX_LICENSE_SECRET environment variable.",
            err=True,
        )
        raise typer.Exit(code=1)

    expires_at: datetime | None = None
    if expires is not None:
        try:
            expires_at = datetime.fromisoformat(expires).replace(
                hour=23,
                minute=59,
                second=59,
                tzinfo=UTC,
            )
        except ValueError as exc:
            typer.echo(f"Error: Invalid expiration date: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    manager = LicenseManager(secret=signing_secret, license_key=None)
    keys = [
        manager.generate_key(expires_at=expires_at, max_uses=max_uses, note=note)
        for _ in range(count)
    ]
    console.print_json(data={"keys": keys, "expires": expires, "max_uses": max_uses, "note": note})


@license_app.command(name="validate")
def license_validate_command(
    key: str = typer.Argument(..., help="License key to validate."),
    secret: str | None = typer.Option(
        None,
        "--secret",
        help="HMAC signing secret (defaults to PHOENIX_LICENSE_SECRET env var).",
    ),
) -> None:
    """Validate a license key's signature, expiration, and use limit."""
    signing_secret = secret or os.getenv("PHOENIX_LICENSE_SECRET")
    if not signing_secret:
        typer.echo(
            "Error: Provide --secret or set the PHOENIX_LICENSE_SECRET environment variable.",
            err=True,
        )
        raise typer.Exit(code=1)

    manager = LicenseManager(secret=signing_secret, license_key=key)
    try:
        payload = manager.validate()
    except LicenseError as exc:
        typer.echo(f"Invalid: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    console.print_json(data={"valid": True, "payload": payload})


@license_app.command(name="status")
def license_status_command() -> None:
    """Show the license key configured for the engine."""
    config = _load_engine_config() or Config()
    data: dict[str, Any] = {
        "enforcement_enabled": config.license_enforcement_enabled,
        "key_configured": config.license_key is not None,
        "key": None,
    }
    if config.license_key is not None:
        manager = LicenseManager.from_config(config)
        data["key"] = manager.masked_key
        try:
            payload = manager.validate(raise_on_failure=False)
            data["status"] = "valid" if payload is not None else "invalid"
            if payload is not None:
                data["payload"] = payload
        except LicenseError as exc:
            data["status"] = f"invalid: {exc}"
    else:
        data["status"] = "no key configured"

    console.print_json(data=data)


def _format_pretty(data: dict[str, object]) -> str:
    """Format result data as a pretty Rich JSON string."""
    with console.capture() as capture:
        console.print_json(data=data)
    return capture.get()


# Register additional CLI commands. These imports intentionally happen after the
# Typer app is created so the decorators can attach to it.
import phoenix.cli.chat  # noqa: E402
import phoenix.cli.setup  # noqa: E402, F401
