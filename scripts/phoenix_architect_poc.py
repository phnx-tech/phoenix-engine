"""PhoenixArchitect proof-of-concept.

Usage:
    python scripts/phoenix_architect_poc.py \
        --url "https://quotes.toscrape.com/" \
        --max-pages 2

The script explores the URL, generates a Phoenix Engine adapter with the local
LLM, validates it with the Critic, and persists it to
``src/phoenix/adapters/generated/``.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Make the project source importable when running the script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from phoenix.architect.orchestrator import PhoenixArchitect


def parse_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(description="PhoenixArchitect PoC")
    parser.add_argument(
        "--url",
        required=True,
        help="URL to generate an adapter for.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=2,
        help="Maximum pagination pages to collect from the target site.",
    )
    parser.add_argument(
        "--repair-iterations",
        type=int,
        default=2,
        help="Maximum Critic-driven repair iterations.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Generate a new adapter even if one already handles the URL.",
    )
    return parser.parse_args()


async def main() -> int:
    """Run the PhoenixArchitect PoC."""
    args = parse_args()

    print(f"🌐 Target URL: {args.url}")
    print("🤖 Starting PhoenixArchitect...")

    architect = PhoenixArchitect()
    try:
        adapter, report = await architect.generate_adapter(
            args.url,
            max_pages=args.max_pages,
            max_repair_iterations=args.repair_iterations,
            force=args.force,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Adapter generation failed: {exc}", file=sys.stderr)
        return 1

    manifest = adapter.manifest
    print(f"✅ Generated adapter: {manifest.name}")
    print(f"   Platforms: {manifest.platforms}")
    print(f"   URL patterns: {manifest.url_patterns}")
    print(f"   Critic score: {report.score}")
    print(f"   Extracted fields: {list(report.extracted_fields.keys())}")
    print("\n⚠️  This is a PoC. Review the generated adapter before using it in production.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
