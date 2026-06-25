"""Unit tests for the offline license manager."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from phoenix.exceptions import (
    LicenseError,
    LicenseExpiredError,
    LicenseInvalidError,
    LicenseMissingError,
    LicenseUsesExceededError,
)
from phoenix.infrastructure.license_manager import LicenseManager
from phoenix.models.config import Config

pytestmark = pytest.mark.unit

SECRET = "super-secret-signing-key"  # noqa: S105


def _make_manager(tmp_path: Path, key: str | None = None) -> LicenseManager:
    return LicenseManager(
        secret=SECRET,
        license_key=key,
        state_path=tmp_path / "license_state.json",
    )


def test_generate_and_validate_key(tmp_path: Path) -> None:
    """A freshly generated key validates successfully."""
    manager = _make_manager(tmp_path)
    key = manager.generate_key()

    validator = _make_manager(tmp_path, key)
    payload = validator.validate()

    assert payload["v"] == 1
    assert payload["exp"] is None
    assert payload["max_uses"] is None


def test_validate_records_uses_up_to_max(tmp_path: Path) -> None:
    """Validation increments uses until max_uses is reached."""
    manager = _make_manager(tmp_path)
    key = manager.generate_key(max_uses=2)

    for _ in range(2):
        validator = _make_manager(tmp_path, key)
        assert validator.validate() is not None

    final = _make_manager(tmp_path, key)
    with pytest.raises(LicenseUsesExceededError):
        final.validate()


def test_expired_key_is_rejected(tmp_path: Path) -> None:
    """A key past its expiration date is rejected."""
    manager = _make_manager(tmp_path)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    key = manager.generate_key(expires_at=yesterday)

    validator = _make_manager(tmp_path, key)
    with pytest.raises(LicenseExpiredError):
        validator.validate()


def test_invalid_signature_is_rejected(tmp_path: Path) -> None:
    """Tampering with the signature causes validation to fail."""
    manager = _make_manager(tmp_path)
    key = manager.generate_key()
    tampered = key[:-6] + "abcdef"

    validator = _make_manager(tmp_path, tampered)
    with pytest.raises(LicenseInvalidError):
        validator.validate()


def test_malformed_key_is_rejected(tmp_path: Path) -> None:
    """A random string is rejected as malformed."""
    validator = _make_manager(tmp_path, "not-a-real-key")
    with pytest.raises(LicenseInvalidError):
        validator.validate()


def test_missing_key_raises(tmp_path: Path) -> None:
    """Validation with no key configured raises LicenseMissingError."""
    manager = _make_manager(tmp_path, None)
    with pytest.raises(LicenseMissingError):
        manager.validate()


def test_no_secret_for_generation_raises(tmp_path: Path) -> None:
    """Generating a key without a secret raises LicenseError."""
    manager = LicenseManager(secret=None, license_key=None, state_path=tmp_path / "state.json")
    with pytest.raises(LicenseError):
        manager.generate_key()


def test_invalid_max_uses_raises(tmp_path: Path) -> None:
    """max_uses < 1 is rejected at generation time."""
    manager = _make_manager(tmp_path)
    with pytest.raises(LicenseError):
        manager.generate_key(max_uses=0)


def test_validate_no_raise_on_failure(tmp_path: Path) -> None:
    """When raise_on_failure is False, invalid keys return None."""
    validator = _make_manager(tmp_path, "bad-key")
    assert validator.validate(raise_on_failure=False) is None


def test_inspect_decodes_without_signature_check(tmp_path: Path) -> None:
    """inspect() decodes metadata but does not enforce expiration or uses."""
    manager = _make_manager(tmp_path)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    key = manager.generate_key(expires_at=yesterday, max_uses=1, note="demo")

    validator = _make_manager(tmp_path, key)
    payload = validator.inspect()
    assert payload["note"] == "demo"
    assert payload["exp"] is not None


def test_masked_key(tmp_path: Path) -> None:
    """masked_key hides the middle portion of the key."""
    manager = _make_manager(tmp_path)
    key = manager.generate_key()
    validator = _make_manager(tmp_path, key)

    masked = validator.masked_key
    assert masked is not None
    assert masked.startswith(key[:6])
    assert masked.endswith(key[-6:])
    assert "..." in masked


def test_from_config(tmp_path: Path) -> None:
    """LicenseManager can be constructed from a Config instance."""
    manager = _make_manager(tmp_path)
    key = manager.generate_key(max_uses=5)

    config = Config(
        data_dir=str(tmp_path),
        license_key=key,
        license_secret=SECRET,
        license_enforcement_enabled=False,
    )
    from_config = LicenseManager.from_config(config)
    assert from_config.validate() is not None


def test_state_persists_across_instances(tmp_path: Path) -> None:
    """Use counts are persisted and shared across manager instances."""
    manager = _make_manager(tmp_path)
    key = manager.generate_key(max_uses=3)

    for _ in range(3):
        validator = _make_manager(tmp_path, key)
        validator.validate()

    assert (tmp_path / "license_state.json").exists()
