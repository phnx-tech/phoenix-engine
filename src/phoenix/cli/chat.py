"""Interactive AI assistant for the Phoenix Engine CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import typer
from openai import OpenAI

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from phoenix.cli.main import app
from phoenix.models.config import Config

console = Console()

_SYSTEM_PROMPT = (
    "You are the Phoenix Engine assistant. Help the user with web scraping tasks. "
    "Phoenix Engine is a Python library and CLI that extracts structured data from public "
    "web pages using HTTP requests or headless browser automation. "
    "Be concise. When the user asks how to scrape a platform, suggest a CLI command like "
    "`phoenix scrape <url>` or a Python snippet using `PhoenixEngine`. "
    "If the user wants to use AI extraction, remind them to enable `--ai` or set "
    "`ai_enabled: true` and have Ollama running."
)

_OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


def _ollama_reachable(base_url: str, timeout: float = 5.0) -> bool:
    """Return True when the configured AI endpoint is reachable."""
    health_url = base_url.replace("/v1", "/api/tags")
    try:
        response = httpx.get(health_url, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError:
        return False
    return True


def _chat_loop(model: str, base_url: str, api_key: str) -> None:
    """Run an interactive chat session with the local AI."""
    client = OpenAI(base_url=base_url, api_key=api_key)
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
    ]

    console.print(
        Panel(
            "Ask me anything about scraping with Phoenix Engine.\n"
            "Type /help for commands, /exit to quit.",
            title=f"Phoenix AI Chat ({model})",
        ),
    )

    while True:
        try:
            user_input = console.input("[bold cyan]> [/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye.")
            break

        text = user_input.strip()
        if not text:
            continue
        if text.lower() in {"/exit", "/quit"}:
            console.print("Goodbye.")
            break
        if text.lower() == "/help":
            console.print(
                "[bold]/help[/bold]  Show this help\n[bold]/exit[/bold]  Quit the chat",
            )
            continue

        messages.append({"role": "user", "content": text})
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]AI error: {exc}[/red]")
            continue

        reply = response.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": reply})
        console.print(Markdown(reply))


@app.command(name="chat")
def chat_command(
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use (defaults to PHOENIX_AI_MODEL or qwen2.5:7b).",
    ),
) -> None:
    """Start an interactive AI assistant for Phoenix Engine."""
    config = Config()
    ai_config = config.phoenix_ai
    chosen_model = model or ai_config.model
    base_url = ai_config.base_url
    api_key = ai_config.api_key or "ollama"

    if not _ollama_reachable(base_url):
        console.print(
            Panel(
                "Ollama is not reachable.\n\n"
                "1. Install Ollama: https://ollama.com/download\n"
                "2. Start Ollama\n"
                f"3. Pull a model: ollama pull {chosen_model}\n\n"
                f"Expected endpoint: {base_url}",
                title="AI not available",
                style="red",
            ),
        )
        raise typer.Exit(code=1)

    _chat_loop(chosen_model, base_url, api_key)
