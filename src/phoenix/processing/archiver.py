"""Source archiver for Phoenix Engine.

Preserves raw HTML sources alongside metadata for audit, debugging, and
regulatory compliance. Archives can be stored via a persistent
:class:`~phoenix.infrastructure.storage.StorageBackend` or written to a local
directory when no backend is configured.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phoenix.infrastructure.storage import StorageBackend


class SourceArchiver:
    """Preserves raw HTML sources for audit and debugging."""

    def __init__(
        self,
        storage: StorageBackend | None = None,
        local_dir: str | Path | None = None,
    ) -> None:
        """Initialize the archiver.

        Args:
            storage: Optional persistent storage backend. When provided,
                archives are written to storage in addition to any local copy.
            local_dir: Optional local directory for raw HTML files.
        """
        self._storage = storage
        self._local_dir = Path(local_dir) if local_dir is not None else None
        if self._local_dir is not None:
            self._local_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_archive_id(url: str, raw_html: str) -> str:
        """Generate a deterministic archive identifier for ``url`` and ``raw_html``."""
        digest = hashlib.sha256(f"{url}:{raw_html}".encode()).hexdigest()[:16]
        return f"{uuid.uuid4().hex[:8]}_{digest}"

    def archive(
        self,
        url: str,
        raw_html: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Archive ``raw_html`` for ``url`` and return the archive identifier.

        Args:
            url: Source URL.
            raw_html: Raw or rendered HTML content.
            metadata: Optional archive metadata (status code, headers, etc.).

        Returns:
            Archive identifier.
        """
        archive_id = self.generate_archive_id(url, raw_html)
        full_metadata = {
            "url": url,
            "archive_id": archive_id,
            "created_at": datetime.now(UTC).isoformat(),
            **(metadata or {}),
        }

        if self._local_dir is not None:
            self._write_local(archive_id, raw_html, full_metadata)

        if self._storage is not None:
            self._storage.save_archive(
                archive_id=archive_id,
                url=url,
                raw_html=raw_html,
                metadata=full_metadata,
            )

        return archive_id

    def _write_local(
        self,
        archive_id: str,
        raw_html: str,
        metadata: dict[str, Any],
    ) -> None:
        if self._local_dir is None:
            return
        html_path = self._local_dir / f"{archive_id}.html"
        meta_path = self._local_dir / f"{archive_id}.json"
        html_path.write_text(raw_html, encoding="utf-8")
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def retrieve(self, archive_id: str) -> dict[str, Any] | None:
        """Retrieve an archive by identifier.

        Prefers the storage backend when configured, otherwise reads from the
        local directory.
        """
        if self._storage is not None:
            return self._storage.get_archive(archive_id)
        if self._local_dir is not None:
            return self._read_local(archive_id)
        return None

    def _read_local(self, archive_id: str) -> dict[str, Any] | None:
        """Read an archive from the local directory."""
        if self._local_dir is None:
            return None
        html_path = self._local_dir / f"{archive_id}.html"
        meta_path = self._local_dir / f"{archive_id}.json"
        if not html_path.exists():
            return None
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        return {
            "archive_id": archive_id,
            "url": metadata.get("url", ""),
            "raw_html": html_path.read_text(encoding="utf-8"),
            "metadata": metadata,
        }
