"""Interactive setup command for Phoenix Engine."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.panel import Panel

from phoenix.cli.main import app
from phoenix.exceptions import LicenseError
from phoenix.infrastructure.license_manager import LicenseManager
from phoenix.models.config import Config

console = Console()

_OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


def _playwright_browser_installed() -> tuple[bool, str | None]:
    """Check whether a Chromium browser is available to Playwright."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        return False, "playwright package not installed"

    try:
        with sync_playwright() as playwright:
            executable = playwright.chromium.executable_path
            if executable and Path(executable).exists():
                return True, f"Chromium found at {executable}"
    except Exception as exc:  # noqa: BLE001
        return False, f"Playwright check failed: {exc}"
    return False, "Chromium browser not installed"


def _install_chromium() -> tuple[bool, str]:
    """Install the Playwright Chromium browser."""
    command = [sys.executable, "-m", "playwright", "install", "chromium"]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)  # noqa: S603
    except subprocess.CalledProcessError as exc:
        return False, f"Install failed: {exc.stderr or exc.stdout or str(exc)}"
    except FileNotFoundError:
        return False, "playwright CLI not found"
    return True, "Chromium installed"


def _ollama_ok() -> tuple[bool, str]:
    """Check whether Ollama is reachable."""
    try:
        response = httpx.get(_OLLAMA_TAGS_URL, timeout=5.0)
        response.raise_for_status()
        models = response.json().get("models", [])
        names = [m.get("name", "unknown") for m in models[:5]]
        return True, f"Ollama running; models: {', '.join(names) or 'none pulled yet'}"
    except httpx.HTTPError as exc:
        return False, f"Cannot reach Ollama at {_OLLAMA_TAGS_URL}: {exc}"


def _license_ok(config: Config) -> tuple[bool, str]:
    """Validate the license key when enforcement is enabled."""
    if not config.license_enforcement_enabled:
        return True, "License enforcement is disabled"
    if not config.license_key:
        return False, "License enforcement is enabled but no key is configured"
    manager = LicenseManager.from_config(config)
    try:
        manager.validate()
    except LicenseError as exc:
        return False, str(exc)
    return True, f"License key valid ({manager.masked_key})"


@app.command(name="setup")
def setup_command(
    *,
    skip_playwright: bool = typer.Option(
        False,
        "--skip-playwright",
        help="Skip Playwright browser check.",
    ),
    skip_ollama: bool = typer.Option(
        False,
        "--skip-ollama",
        help="Skip Ollama check.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Automatically install missing browsers without prompting.",
    ),
) -> None:
    """Check and set up runtime dependencies for Phoenix Engine."""
    console.print(Panel.fit("Phoenix Engine Setup", style="bold cyan"))

    config = Config()
    report: list[dict[str, Any]] = []

    if skip_playwright:
        report.append({"item": "Playwright", "ok": True, "message": "Skipped"})
    else:
        installed, browser_message = _playwright_browser_installed()
        if installed:
            report.append({"item": "Playwright", "ok": True, "message": browser_message})
        else:
            console.print(f"[yellow]Playwright: {browser_message}[/yellow]")
            if yes or typer.confirm("Install Chromium browser now?", default=True):
                install_ok, install_message = _install_chromium()
                report.append({"item": "Playwright", "ok": install_ok, "message": install_message})
            else:
                report.append(
                    {
                        "item": "Playwright",
                        "ok": False,
                        "message": f"{browser_message} (install skipped)",
                    },
                )

    if skip_ollama:
        report.append({"item": "Ollama", "ok": True, "message": "Skipped"})
    else:
        ok, message = _ollama_ok()
        report.append({"item": "Ollama", "ok": ok, "message": message})

    ok, message = _license_ok(config)
    report.append({"item": "License", "ok": ok, "message": message})

    console.print("\n[bold]Setup report:[/bold]")
    for row in report:
        symbol = "[green]✓[/green]" if row["ok"] else "[red]✗[/red]"
        console.print(f"{symbol} {row['item']}: {row['message']}")

    if any(not row["ok"] for row in report):
        console.print(
            Panel(
                "Some checks failed. Fix the items above and run 'phoenix setup' again.",
                style="red",
            ),
        )
        raise typer.Exit(code=1)

    console.print(Panel("All checks passed. Phoenix Engine is ready.", style="green"))
