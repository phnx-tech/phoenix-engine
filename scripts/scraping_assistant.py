"""Full Phoenix Engine coding assistant powered by a local Ollama model.

Supports natural-language requests to create, modify, explain, and test
Phoenix Engine code. The assistant loads relevant source files as context,
generates code following project conventions, and can write files after
your approval.

Use `/agent <task>` to let the assistant plan and execute multi-step changes
like Kimi does (experimental). Example:

    $ python scripts/scraping_assistant.py
    You: /agent add an OLX Egypt adapter and register it
    Assistant: Plan: 1) inspect example.com, 2) generate example_com.py,
              3) register the adapter, 4) run checks
              Execute? [y/N] y

Default model: dolphincoder:7b (override with --model or SCRAPING_ASSISTANT_MODEL).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "dolphincoder:7b"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_system_prompt() -> str:
    return (
        "You are PhoenixCoder, a senior Python engineer and expert on the Phoenix Engine "
        "open-source web scraping framework.\n\n"
        "Your job:\n"
        "- Answer questions about the codebase.\n"
        "- Generate new adapters, collectors, CLI commands, tests, and docs.\n"
        "- Fix or refactor existing code.\n"
        "- Keep changes minimal and follow the existing style.\n\n"
        "Project standards:\n"
        "- Python 3.13, asyncio, pydantic, httpx, playwright, typer, pytest.\n"
        "- Type hints everywhere, mypy strict.\n"
        "- ruff all rules, black line-length 100.\n"
        "- pytest with 85% coverage gate.\n"
        "- Adapters subclass BaseAdapter in src/phoenix/adapters/.\n"
        "- Collectors subclass Collector in src/phoenix/collectors/.\n"
        "- Ethical boundary: never generate login automation, CAPTCHA bypass, or private-group scrapers.\n\n"
        "When generating or modifying files:\n"
        "1. Output code inside fenced blocks.\n"
        "2. Put `# file: relative/path.py` on the first line of every block.\n"
        "3. Only generate the file(s) the user asked for.\n"
        "4. Do not create helper/manifest/plugin-loader files unless explicitly asked.\n"
        "5. Use existing imports and patterns from the context.\n"
        "6. Add concise comments for non-obvious logic.\n"
        "7. If you are unsure, ask for clarification.\n"
    )


def build_agent_system_prompt() -> str:
    return (
        "You are PhoenixAgent, an autonomous coding agent for the Phoenix Engine project.\n\n"
        "Given a high-level task, your job is to plan and execute changes to the codebase.\n"
        "You can read files, write files, run shell commands, and run quality checks.\n\n"
        "Rules:\n"
        "1. Produce ONLY a single valid JSON array of action objects. No markdown, no explanation outside JSON.\n"
        "2. Available action types:\n"
        "   - {\"action\": \"read\", \"path\": \"relative/path.py\"}\n"
        "   - {\"action\": \"write\", \"path\": \"relative/path.py\", \"content\": \"full file content\"}\n"
        "   - {\"action\": \"run\", \"command\": \"shell command string\"}\n"
        "   - {\"action\": \"check\"}\n"
        "3. Use relative paths from the project root.\n"
        "4. Only write to src/phoenix/ or tests/ directories.\n"
        "5. Keep changes minimal and follow the existing project style.\n"
        "6. Include a final {\"action\": \"check\"} action in every plan.\n"
        "7. If you need context first, start with read actions.\n"
        "8. Do not generate login automation, CAPTCHA bypass, or private-group scrapers.\n"
        "9. New adapters must also be exported from src/phoenix/adapters/__init__.py.\n"
        "10. Write pytest-style tests (plain assert), not unittest.\n\n"
        "The plan will be shown to the user for approval before destructive actions run.\n"
    )


def ollama_chat(messages: list[dict[str, str]], model: str, timeout: float = 180.0) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.15, "num_ctx": 8192},
    }
    response = httpx.post(OLLAMA_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "")


def read_file(relative_path: str) -> str:
    full_path = PROJECT_ROOT / relative_path
    try:
        return full_path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"# Error reading {relative_path}: {exc}"


def project_tree() -> str:
    lines: list[str] = []
    for path in sorted(PROJECT_ROOT.rglob("*")):
        if ".git" in path.parts or "__pycache__" in path.parts or ".venv" in path.parts:
            continue
        rel = path.relative_to(PROJECT_ROOT)
        depth = len(rel.parts) - 1
        prefix = "  " * depth
        name = path.name + ("/" if path.is_dir() else "")
        lines.append(f"{prefix}{name}")
    return "\n".join(lines)


def grep_code(pattern: str) -> str:
    try:
        result = subprocess.run(
            ["grep", "-RIn", "--include=*.py", pattern, str(PROJECT_ROOT / "src")],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout or f"No matches for '{pattern}'"
    except Exception as exc:
        return f"grep error: {exc}"


def run_checks() -> str:
    commands = [
        ("ruff", ["ruff", "check", "src", "tests"]),
        ("black", ["black", "--check", "src", "tests"]),
        ("mypy", ["mypy", "src"]),
        ("pytest", ["pytest", "--cov=phoenix", "--cov-fail-under=85", "-q"]),
    ]
    outputs: list[str] = []
    for name, cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
            )
            status = "✅" if result.returncode == 0 else "❌"
            outputs.append(f"{status} {name}\n{result.stdout}{result.stderr}")
        except Exception as exc:
            outputs.append(f"❌ {name}\n{exc}")
    return "\n---\n".join(outputs)


def extract_file_suggestions(text: str) -> dict[str, str]:
    suggestions: dict[str, str] = {}
    pattern = re.compile(
        r"```(?:python)?\s*\n" r"#\s*file:\s*(.+?)\n" r"(.*?)" r"```",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        path = match.group(1).strip()
        code = match.group(2).strip()
        suggestions[path] = code
    return suggestions


def apply_suggestions(suggestions: dict[str, str], auto_approve: bool = False) -> None:
    if not suggestions:
        print("No file suggestions found.")
        return
    for path, code in suggestions.items():
        full_path = PROJECT_ROOT / path
        print(f"\nSuggested file: {path}")
        print(code[:400] + ("..." if len(code) > 400 else ""))
        if not path.startswith(("src/phoenix/", "tests/")):
            print(f"⚠️  Path {path} looks unusual. Skipping for safety.")
            continue
        if auto_approve:
            answer = "y"
            print("Auto-approving write.")
        else:
            try:
                answer = input("Write this file? [y/N] ").strip().lower()
            except EOFError:
                print("No input received. Skipping remaining files.")
                return
        if answer in {"y", "yes"}:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(code, encoding="utf-8")
            print(f"Wrote {full_path}")
        else:
            print("Skipped.")


def parse_agent_plan(text: str) -> list[dict[str, Any]]:
    """Extract the first JSON array from the model output."""
    text = text.strip()
    # If wrapped in markdown code block, strip it.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    # The model may prefix the JSON with "Plan:" or explanation text.
    # Find the first '[' and the matching last ']'.
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON array found in model output.")
    json_text = text[start : end + 1]
    try:
        plan = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}") from exc
    if not isinstance(plan, list):
        raise ValueError("Model returned JSON, but it is not an array of actions.")
    return plan


def summarize_plan(plan: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, action in enumerate(plan, start=1):
        kind = action.get("action", "unknown")
        if kind == "read":
            lines.append(f"{idx}. Read {action.get('path')}")
        elif kind == "write":
            lines.append(f"{idx}. Write {action.get('path')}")
        elif kind == "run":
            lines.append(f"{idx}. Run: {action.get('command')}")
        elif kind == "check":
            lines.append(f"{idx}. Run quality checks")
        else:
            lines.append(f"{idx}. Unknown action: {kind}")
    return "\n".join(lines)


def is_safe_path(path: str) -> bool:
    return path.startswith(("src/phoenix/", "tests/", "scripts/"))


def execute_agent_plan(plan: list[dict[str, Any]], model: str, auto_approve: bool = False) -> None:
    context_messages: list[dict[str, str]] = [
        {"role": "system", "content": build_agent_system_prompt()},
    ]

    for action in plan:
        kind = action.get("action")
        if kind == "read":
            path = action.get("path", "")
            content = read_file(path)
            print(f"📖 Read {path} ({len(content)} chars)")
            context_messages.append(
                {"role": "user", "content": f"Content of {path}:\n```\n{content}\n```"}
            )

        elif kind == "write":
            path = action.get("path", "")
            content = action.get("content", "")
            if not is_safe_path(path):
                print(f"⚠️  Refusing to write outside safe dirs: {path}")
                continue
            full_path = PROJECT_ROOT / path
            print(f"\n📝 Proposed write: {path}")
            preview = content[:500] + ("..." if len(content) > 500 else "")
            print(preview)
            try:
                answer = input("Write this file? [y/N] ").strip().lower()
            except EOFError:
                print("No input. Stopping agent.")
                return
            if answer in {"y", "yes"}:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")
                print(f"Wrote {full_path}")
            else:
                print("Skipped.")

        elif kind == "run":
            command = action.get("command", "")
            print(f"\n⚙️  Proposed command: {command}")
            try:
                answer = input("Run this command? [y/N] ").strip().lower()
            except EOFError:
                print("No input. Stopping agent.")
                return
            if answer not in {"y", "yes"}:
                print("Skipped.")
                continue
            try:
                result = subprocess.run(
                    command,
                    cwd=PROJECT_ROOT,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                output = f"{result.stdout}{result.stderr}".strip()
                print(output[:2000])
                context_messages.append(
                    {"role": "user", "content": f"Output of `{command}`:\n{output}"}
                )
            except Exception as exc:
                print(f"Command failed: {exc}")
                context_messages.append(
                    {"role": "user", "content": f"Command `{command}` failed:\n{exc}"}
                )

        elif kind == "check":
            print("\n🔍 Running quality gates...")
            output = run_checks()
            print(output)
            context_messages.append(
                {"role": "user", "content": f"Quality gate output:\n{output}"}
            )

        else:
            print(f"⚠️  Unknown action: {kind}")


def run_agent_mode(task: str, model: str, auto_approve: bool = False) -> None:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": build_agent_system_prompt()},
        {"role": "user", "content": f"Task: {task}\n\nReturn ONLY a JSON plan."},
    ]
    print("🤖 Agent is planning...")
    try:
        reply = ollama_chat(messages, model=model, timeout=240.0)
    except Exception as exc:
        print(f"Error talking to Ollama: {exc}", file=sys.stderr)
        return

    print("\nAgent plan:")
    try:
        plan = parse_agent_plan(reply)
    except ValueError as exc:
        print(f"Could not parse plan: {exc}")
        print("Raw output:")
        print(reply[:2000])
        return

    print(summarize_plan(plan))
    try:
        answer = input("\nExecute this plan? [y/N] ").strip().lower()
    except EOFError:
        print("No input. Aborting.")
        return
    if answer not in {"y", "yes"}:
        print("Aborted.")
        return

    execute_agent_plan(plan, model=model, auto_approve=auto_approve)


def print_help() -> None:
    print(
        "\nCommands:\n"
        "  /agent <task>       - autonomous multi-step coding agent (experimental)\n"
        "  /read <path>        - load a source file into context\n"
        "  /search <pattern>   - grep src/ for pattern\n"
        "  /tree               - show project tree\n"
        "  /model <name>       - switch Ollama model\n"
        "  /apply              - write code blocks from last reply to disk\n"
        "  /check              - run ruff/black/mypy/pytest\n"
        "  /help               - show this help\n"
        "  /quit               - exit\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phoenix Engine coding assistant")
    parser.add_argument(
        "--model",
        default=os.environ.get("SCRAPING_ASSISTANT_MODEL", DEFAULT_MODEL),
        help="Ollama model to use (default: dolphincoder:7b).",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Auto-approve write/run actions (use with caution).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model = args.model
    print(f"🐦 Phoenix Engine Assistant ({model})")
    print("Type /help for commands.\n")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": build_system_prompt()},
    ]
    last_response = ""

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        if not user_input:
            continue

        if user_input.lower() in {"/quit", "/exit", "quit", "exit"}:
            print("Goodbye.")
            return 0

        if user_input.lower() == "/help":
            print_help()
            continue

        if user_input.lower() == "/tree":
            print(project_tree())
            continue

        if user_input.lower().startswith("/model "):
            model = user_input[7:].strip()
            print(f"Switched to model: {model}")
            continue

        if user_input.lower().startswith("/read "):
            path = user_input[6:].strip()
            content = read_file(path)
            messages.append({"role": "user", "content": f"Here is {path}:\n```\n{content}\n```"})
            print(f"Loaded {path} into context.")
            continue

        if user_input.lower().startswith("/search "):
            pattern = user_input[8:].strip()
            results = grep_code(pattern)
            print(results[:2000])
            include = input("\nInclude results in context? [y/N] ").strip().lower()
            if include in {"y", "yes"}:
                messages.append(
                    {"role": "user", "content": f"grep results for '{pattern}':\n{results}"}
                )
            continue

        if user_input.lower().startswith("/agent "):
            task = user_input[7:].strip()
            run_agent_mode(task, model=model, auto_approve=args.yes)
            continue

        if user_input.lower() == "/apply":
            apply_suggestions(extract_file_suggestions(last_response), auto_approve=args.yes)
            continue

        if user_input.lower() == "/check":
            print("Running quality gates...")
            print(run_checks())
            continue

        messages.append({"role": "user", "content": user_input})
        print("Assistant: ", end="", flush=True)
        try:
            reply = ollama_chat(messages, model=model)
        except Exception as exc:
            print(f"\nError talking to Ollama: {exc}", file=sys.stderr)
            continue
        print(reply)
        last_response = reply
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    raise SystemExit(main())
