"""Adapter persistence for PhoenixArchitect.

Writes AI-generated adapter modules to a dedicated package so they are
automatically discovered on the next engine startup.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any


class GeneratedAdapterWriter:
    """Write generated adapter source files safely to disk."""

    DEFAULT_OUTPUT_DIR: Path = Path(__file__).resolve().parents[1] / "adapters" / "generated"

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize the writer.

        Args:
            output_dir: Directory where generated adapters are written.
                Defaults to ``src/phoenix/adapters/generated/``.
        """
        self._output_dir = (output_dir or self.DEFAULT_OUTPUT_DIR).resolve()
        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def output_dir(self) -> Path:
        """Return the resolved output directory."""
        return self._output_dir

    def write(self, platform: str, code: str) -> Path:
        """Persist ``code`` as a generated adapter for ``platform``.

        Args:
            platform: Short platform identifier used to derive the filename.
            code: Python source for the adapter.

        Returns:
            Path to the written file.

        Raises:
            ValueError: If ``platform`` cannot be sanitized or the resulting
                path would escape the output directory.
        """
        if ".." in platform or "/" in platform or "\\" in platform:
            raise ValueError(
                f"Platform identifier contains path separators: {platform!r}",
            )

        safe_name = self._sanitize(platform)
        if not safe_name:
            raise ValueError(f"Invalid platform identifier: {platform!r}")

        target = (self._output_dir / f"{safe_name}.py").resolve()
        if not self._is_safe(target):
            raise ValueError(f"Refusing to write outside output directory: {target}")

        try:
            import black  # noqa: PLC0415

            code = black.format_str(code, mode=black.Mode(line_length=100))
        except ImportError:
            pass
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).warning("Failed to format generated adapter: %s", exc)

        target.write_text(code, encoding="utf-8")
        return target

    def list_adapters(self) -> list[Path]:
        """Return all generated adapter files currently on disk."""
        return sorted(self._output_dir.glob("*.py"))

    def read(self, platform: str) -> str | None:
        """Return the source of a previously generated adapter, if any."""
        safe_name = self._sanitize(platform)
        target = self._output_dir / f"{safe_name}.py"
        if not target.exists():
            return None
        return target.read_text(encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        """Return a summary of the writer state."""
        return {
            "output_dir": str(self._output_dir),
            "adapter_count": len(self.list_adapters()),
        }

    @staticmethod
    def _sanitize(platform: str) -> str:
        """Return a filesystem-safe module name for ``platform``."""
        normalized = platform.lower().strip().replace("-", "_").replace(" ", "_")
        return re.sub(r"[^a-z0-9_]+", "_", normalized).strip("_")

    def _is_safe(self, target: Path) -> bool:
        """Return ``True`` when ``target`` is inside the output directory."""
        try:
            target.relative_to(self._output_dir)
        except ValueError:
            return False
        return True


__all__ = ["GeneratedAdapterWriter"]
