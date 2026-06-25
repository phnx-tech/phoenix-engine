"""Persistent storage backends for Phoenix Engine results, archives, and sessions.

The module exposes an abstract :class:`StorageBackend` plus concrete SQLAlchemy
backends for SQLite and PostgreSQL. All backends share the same relational
schema so that application code can switch between them by only changing the
connection URL.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from phoenix.models.output import ScrapingResult
from phoenix.models.session import Session as PlatformSession


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


class ResultRecord(Base):
    """Persisted scraping result."""

    __tablename__ = "scrape_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url: Mapped[str] = mapped_column(String(2048), index=True)
    platform: Mapped[str] = mapped_column(String(64), index=True)
    content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    success: Mapped[int] = mapped_column(default=1)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    archive_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column()
    scraping_strategy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_assisted: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"<ResultRecord(id={self.id}, url={self.url}, platform={self.platform})>"


class ArchiveRecord(Base):
    """Persisted raw HTML archive."""

    __tablename__ = "archives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    archive_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(2048), index=True)
    raw_html: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column()

    def __repr__(self) -> str:
        return f"<ArchiveRecord(archive_id={self.archive_id}, url={self.url})>"


class SessionRecord(Base):
    """Persisted authenticated session."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    platform: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    cookies_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    is_valid: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column()
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<SessionRecord(platform={self.platform}, is_valid={self.is_valid})>"


class DomainMemoryRecord(Base):
    """Persisted per-domain learning memory."""

    __tablename__ = "domain_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    domain: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    strategy_memory_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    selector_memory_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    aggregates_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(default=_utc_now)

    def __repr__(self) -> str:
        return f"<DomainMemoryRecord(domain={self.domain})>"


class HTMLBaselineRecord(Base):
    """Persisted structural baseline for a URL or URL pattern."""

    __tablename__ = "html_baselines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url: Mapped[str] = mapped_column(String(2048), index=True)
    platform: Mapped[str] = mapped_column(String(64), index=True)
    content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    structural_fingerprint: Mapped[str] = mapped_column(String(64))
    selectors_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    critical_fields_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    html_size_bytes: Mapped[int] = mapped_column(default=0)
    archive_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=_utc_now)

    def __repr__(self) -> str:
        return f"<HTMLBaselineRecord(url={self.url}, platform={self.platform})>"


class ChangeAlertRecord(Base):
    """Persisted change-detection alert."""

    __tablename__ = "change_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url: Mapped[str] = mapped_column(String(2048), index=True)
    platform: Mapped[str] = mapped_column(String(64), index=True)
    content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16))
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    baseline_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_utc_now)

    def __repr__(self) -> str:
        return f"<ChangeAlertRecord(url={self.url}, type={self.alert_type})>"


class StorageBackend(ABC):
    """Abstract persistent storage backend."""

    @abstractmethod
    def save_scrape_result(
        self,
        result: ScrapingResult,
        *,
        raw_html: str | None = None,
        archive_id: str | None = None,
    ) -> str:
        """Persist a scraping result and return its storage identifier."""

    @abstractmethod
    def get_scrape_result(self, result_id: str) -> ScrapingResult | None:
        """Fetch a scraping result by storage identifier."""

    @abstractmethod
    def list_scrape_results(
        self,
        *,
        platform: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ScrapingResult]:
        """List scraping results with optional filtering and pagination."""

    @abstractmethod
    def save_archive(
        self,
        archive_id: str,
        url: str,
        raw_html: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persist a raw HTML archive and return its storage identifier."""

    @abstractmethod
    def get_archive(self, archive_id: str) -> dict[str, Any] | None:
        """Fetch a raw HTML archive by archive identifier."""

    @abstractmethod
    def save_session(self, session: PlatformSession) -> str:
        """Persist a platform session and return its storage identifier."""

    @abstractmethod
    def get_session(self, platform: str) -> PlatformSession | None:
        """Fetch the active session for a platform."""

    @abstractmethod
    def list_sessions(self) -> list[PlatformSession]:
        """List all persisted sessions."""

    @abstractmethod
    def get_domain_memory(self, domain: str) -> dict[str, Any] | None:
        """Fetch persisted learning memory for a domain."""

    @abstractmethod
    def save_domain_memory(self, domain: str, memory: dict[str, Any]) -> str:
        """Persist learning memory for a domain and return its identifier."""

    @abstractmethod
    def get_latest_baseline(self, url: str) -> dict[str, Any] | None:
        """Fetch the most recent structural baseline for a URL."""

    @abstractmethod
    def save_baseline(  # noqa: PLR0913
        self,
        url: str,
        platform: str,
        *,
        content_type: str | None = None,
        structural_fingerprint: str,
        selectors_snapshot: dict[str, Any],
        critical_fields_hash: str | None = None,
        html_size_bytes: int = 0,
        archive_id: str | None = None,
    ) -> str:
        """Persist or update a structural baseline and return its identifier."""

    @abstractmethod
    def save_alert(self, alert: dict[str, Any]) -> str:
        """Persist a change-detection alert and return its identifier."""

    @abstractmethod
    def close(self) -> None:
        """Release storage resources."""


class SQLAlchemyStorageBackend(StorageBackend):
    """Storage backend backed by any SQLAlchemy-compatible database.

    Works out of the box with SQLite (``sqlite:///...``) and can target
    PostgreSQL by providing a ``postgresql+psycopg://...`` URL.
    """

    def __init__(self, database_url: str, *, echo: bool = False) -> None:
        """Initialize the backend.

        Args:
            database_url: SQLAlchemy connection URL.
            echo: When ``True``, echo SQL statements (useful for debugging).
        """
        self._database_url = database_url
        self._engine = create_engine(database_url, echo=echo)
        Base.metadata.create_all(self._engine)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine)

    def _new_session(self) -> Session:
        return self._session_factory()

    def save_scrape_result(
        self,
        result: ScrapingResult,
        *,
        raw_html: str | None = None,
        archive_id: str | None = None,
    ) -> str:
        """Persist a scraping result and return its storage identifier."""
        record = ResultRecord(
            id=str(uuid.uuid4()),
            url=result.url or "",
            platform=result.output.platform if result.output else "unknown",
            content_type=result.output.content_type if result.output else None,
            success=1 if result.success else 0,
            output_json=result.model_dump(mode="json") if result.output else None,
            raw_html=raw_html,
            archive_id=archive_id,
            created_at=_utc_now(),
            scraping_strategy=result.output.scraping_strategy if result.output else None,
            ai_assisted=1 if result.ai_assisted else 0,
        )
        with self._new_session() as db_session:
            db_session.add(record)
            db_session.commit()
            return str(record.id)

    def get_scrape_result(self, result_id: str) -> ScrapingResult | None:
        """Fetch a scraping result by storage identifier."""
        with self._new_session() as db_session:
            record = db_session.get(ResultRecord, result_id)
            if record is None or record.output_json is None:
                return None
            return ScrapingResult.model_validate(record.output_json)

    def list_scrape_results(
        self,
        *,
        platform: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ScrapingResult]:
        """List scraping results with optional filtering and pagination."""
        with self._new_session() as db_session:
            stmt = select(ResultRecord).order_by(ResultRecord.created_at.desc())
            if platform is not None:
                stmt = stmt.where(ResultRecord.platform == platform)
            stmt = stmt.limit(limit).offset(offset)
            records = db_session.scalars(stmt).all()
            return [
                ScrapingResult.model_validate(record.output_json)
                for record in records
                if record.output_json is not None
            ]

    def save_archive(
        self,
        archive_id: str,
        url: str,
        raw_html: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persist a raw HTML archive and return its storage identifier."""
        record = ArchiveRecord(
            id=str(uuid.uuid4()),
            archive_id=archive_id,
            url=url,
            raw_html=raw_html,
            metadata_json=metadata or {},
            created_at=_utc_now(),
        )
        with self._new_session() as db_session:
            db_session.merge(record)
            db_session.commit()
            return str(record.id)

    def get_archive(self, archive_id: str) -> dict[str, Any] | None:
        """Fetch a raw HTML archive by archive identifier."""
        with self._new_session() as db_session:
            stmt = select(ArchiveRecord).where(ArchiveRecord.archive_id == archive_id)
            record = db_session.scalars(stmt).first()
            if record is None:
                return None
            return {
                "archive_id": record.archive_id,
                "url": record.url,
                "raw_html": record.raw_html,
                "metadata": record.metadata_json,
                "created_at": record.created_at,
            }

    def save_session(self, session: PlatformSession) -> str:
        """Persist a platform session and return its storage identifier."""
        record = SessionRecord(
            id=str(uuid.uuid4()),
            platform=session.platform,
            cookies_json=session.cookies,
            is_valid=1 if session.is_valid else 0,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        with self._new_session() as db_session:
            existing = db_session.scalars(
                select(SessionRecord).where(SessionRecord.platform == session.platform),
            ).first()
            if existing is not None:
                existing.cookies_json = session.cookies
                existing.is_valid = 1 if session.is_valid else 0
                existing.updated_at = _utc_now()
                record = existing
            else:
                db_session.add(record)
            db_session.commit()
            return str(record.id)

    def get_session(self, platform: str) -> PlatformSession | None:
        """Fetch the active session for a platform."""
        with self._new_session() as db_session:
            stmt = select(SessionRecord).where(SessionRecord.platform == platform)
            record = db_session.scalars(stmt).first()
            if record is None:
                return None
            return PlatformSession(
                platform=record.platform,
                cookies=list(record.cookies_json),
                created_at=record.created_at,
                updated_at=record.updated_at,
                is_valid=bool(record.is_valid),
            )

    def list_sessions(self) -> list[PlatformSession]:
        """List all persisted sessions."""
        with self._new_session() as db_session:
            stmt = select(SessionRecord).order_by(SessionRecord.platform)
            records = db_session.scalars(stmt).all()
            return [
                PlatformSession(
                    platform=record.platform,
                    cookies=list(record.cookies_json),
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    is_valid=bool(record.is_valid),
                )
                for record in records
            ]

    def get_domain_memory(self, domain: str) -> dict[str, Any] | None:
        """Fetch persisted learning memory for a domain."""
        with self._new_session() as db_session:
            stmt = select(DomainMemoryRecord).where(DomainMemoryRecord.domain == domain)
            record = db_session.scalars(stmt).first()
            if record is None:
                return None
            return {
                "domain": record.domain,
                "strategy_memory": record.strategy_memory_json,
                "selector_memory": record.selector_memory_json,
                "aggregates": record.aggregates_json,
                "updated_at": record.updated_at,
            }

    def save_domain_memory(self, domain: str, memory: dict[str, Any]) -> str:
        """Persist learning memory for a domain and return its identifier."""
        with self._new_session() as db_session:
            existing = db_session.scalars(
                select(DomainMemoryRecord).where(DomainMemoryRecord.domain == domain),
            ).first()
            if existing is not None:
                existing.strategy_memory_json = memory.get("strategy_memory", {})
                existing.selector_memory_json = memory.get("selector_memory", {})
                existing.aggregates_json = memory.get("aggregates", {})
                existing.updated_at = _utc_now()
                record = existing
            else:
                record = DomainMemoryRecord(
                    id=str(uuid.uuid4()),
                    domain=domain,
                    strategy_memory_json=memory.get("strategy_memory", {}),
                    selector_memory_json=memory.get("selector_memory", {}),
                    aggregates_json=memory.get("aggregates", {}),
                    updated_at=_utc_now(),
                )
                db_session.add(record)
            db_session.commit()
            return str(record.id)

    def get_latest_baseline(self, url: str) -> dict[str, Any] | None:
        """Fetch the most recent structural baseline for a URL."""
        with self._new_session() as db_session:
            stmt = (
                select(HTMLBaselineRecord)
                .where(HTMLBaselineRecord.url == url)
                .order_by(HTMLBaselineRecord.updated_at.desc())
            )
            record = db_session.scalars(stmt).first()
            if record is None:
                return None
            return {
                "id": str(record.id),
                "url": record.url,
                "platform": record.platform,
                "content_type": record.content_type,
                "structural_fingerprint": record.structural_fingerprint,
                "selectors_snapshot": record.selectors_snapshot_json,
                "critical_fields_hash": record.critical_fields_hash,
                "html_size_bytes": record.html_size_bytes,
                "archive_id": record.archive_id,
                "updated_at": record.updated_at,
            }

    def save_baseline(  # noqa: PLR0913
        self,
        url: str,
        platform: str,
        *,
        content_type: str | None = None,
        structural_fingerprint: str,
        selectors_snapshot: dict[str, Any],
        critical_fields_hash: str | None = None,
        html_size_bytes: int = 0,
        archive_id: str | None = None,
    ) -> str:
        """Persist or update a structural baseline and return its identifier."""
        with self._new_session() as db_session:
            existing = db_session.scalars(
                select(HTMLBaselineRecord).where(HTMLBaselineRecord.url == url),
            ).first()
            if existing is not None:
                existing.platform = platform
                existing.content_type = content_type
                existing.structural_fingerprint = structural_fingerprint
                existing.selectors_snapshot_json = selectors_snapshot
                existing.critical_fields_hash = critical_fields_hash
                existing.html_size_bytes = html_size_bytes
                existing.archive_id = archive_id
                existing.updated_at = _utc_now()
                record = existing
            else:
                record = HTMLBaselineRecord(
                    id=str(uuid.uuid4()),
                    url=url,
                    platform=platform,
                    content_type=content_type,
                    structural_fingerprint=structural_fingerprint,
                    selectors_snapshot_json=selectors_snapshot,
                    critical_fields_hash=critical_fields_hash,
                    html_size_bytes=html_size_bytes,
                    archive_id=archive_id,
                    updated_at=_utc_now(),
                )
                db_session.add(record)
            db_session.commit()
            return str(record.id)

    def save_alert(self, alert: dict[str, Any]) -> str:
        """Persist a change-detection alert and return its identifier."""
        record = ChangeAlertRecord(
            id=str(uuid.uuid4()),
            url=alert.get("url", ""),
            platform=alert.get("platform", ""),
            content_type=alert.get("content_type"),
            alert_type=alert.get("alert_type", "unknown"),
            severity=alert.get("severity", "info"),
            details_json=alert.get("details", {}),
            baseline_id=alert.get("baseline_id"),
            created_at=_utc_now(),
        )
        with self._new_session() as db_session:
            db_session.add(record)
            db_session.commit()
            return str(record.id)

    def close(self) -> None:
        """Release storage resources."""
        self._engine.dispose()


class SQLiteStorageBackend(SQLAlchemyStorageBackend):
    """Convenient SQLite storage backend."""

    def __init__(self, path: str = "phoenix.db", *, echo: bool = False) -> None:
        """Initialize a SQLite backend.

        Args:
            path: Filesystem path to the SQLite database. Use ``:memory:`` for
                an in-memory database.
            echo: When ``True``, echo SQL statements.
        """
        super().__init__(f"sqlite:///{path}", echo=echo)


class PostgresStorageBackend(SQLAlchemyStorageBackend):
    """Convenient PostgreSQL storage backend."""

    def __init__(  # noqa: PLR0913
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "phoenix",
        user: str = "phoenix",
        password: str = "",
        *,
        echo: bool = False,
    ) -> None:
        """Initialize a PostgreSQL backend using psycopg.

        Args:
            host: PostgreSQL host.
            port: PostgreSQL port.
            database: Database name.
            user: Database user.
            password: Database password.
            echo: When ``True``, echo SQL statements.
        """
        url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
        super().__init__(url, echo=echo)


__all__ = [
    "ArchiveRecord",
    "Base",
    "ChangeAlertRecord",
    "DomainMemoryRecord",
    "HTMLBaselineRecord",
    "PostgresStorageBackend",
    "ResultRecord",
    "SQLAlchemyStorageBackend",
    "SQLiteStorageBackend",
    "SessionRecord",
    "StorageBackend",
]
