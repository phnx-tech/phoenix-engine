"""Unit tests for the secure credential vault."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from phoenix.infrastructure.vault import (
    AutoVault,
    FileVault,
    KeyringVault,
    SecretNotFoundError,
    VaultError,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def vault(tmp_path: Path) -> FileVault:
    """Return a file vault using a temporary path."""
    return FileVault(path=tmp_path / "vault.json", key=b"test-key-0000000000000000000000000")


def test_file_vault_store_and_retrieve(vault: FileVault) -> None:
    """Secrets can be stored and retrieved from the file vault."""
    vault.store("openai_api_key", "secret123")

    assert vault.retrieve("openai_api_key") == "secret123"


def test_file_vault_delete(vault: FileVault) -> None:
    """Secrets can be deleted from the file vault."""
    vault.store("key", "value")
    vault.delete("key")

    with pytest.raises(SecretNotFoundError):
        vault.retrieve("key")


def test_file_vault_list_keys(vault: FileVault) -> None:
    """The vault lists stored keys in sorted order."""
    vault.store("b", "2")
    vault.store("a", "1")

    assert vault.list_keys() == ["a", "b"]


def test_file_vault_missing_secret(vault: FileVault) -> None:
    """Retrieving a missing secret raises ``SecretNotFoundError``."""
    with pytest.raises(SecretNotFoundError):
        vault.retrieve("missing")


def test_file_vault_corruption_raises_error(tmp_path: Path) -> None:
    """A corrupted vault file raises ``VaultError``."""
    vault_path = tmp_path / "vault.json"
    vault_path.write_bytes(b"not encrypted")
    vault = FileVault(path=vault_path, key=b"test-key-0000000000000000000000000")

    with pytest.raises(VaultError):
        vault.retrieve("any")


def test_keyring_vault_store_and_retrieve(monkeypatch: pytest.MonkeyPatch) -> None:
    """``KeyringVault`` delegates to the system keyring."""
    passwords: dict[str, str] = {}
    errors = MagicMock()
    fake_keyring = MagicMock()
    fake_keyring.set_password = lambda _service, key, value: passwords.update({key: value})
    fake_keyring.get_password = lambda _service, key: passwords.get(key)
    fake_keyring.delete_password = lambda _service, key: passwords.pop(key, None)
    fake_keyring.errors = errors

    monkeypatch.setattr("phoenix.infrastructure.vault.keyring", fake_keyring)
    monkeypatch.setattr("phoenix.infrastructure.vault.keyring.errors", errors)

    vault = KeyringVault()
    vault.store("key", "value")

    assert vault.retrieve("key") == "value"
    vault.delete("key")
    with pytest.raises(SecretNotFoundError):
        vault.retrieve("key")


def test_keyring_vault_error_raises_vault_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keyring errors are translated to ``VaultError``."""
    errors = MagicMock()
    errors.KeyringError = type("KeyringError", (Exception,), {})
    fake_keyring = MagicMock()
    fake_keyring.set_password = MagicMock(side_effect=errors.KeyringError("fail"))
    fake_keyring.errors = errors

    monkeypatch.setattr("phoenix.infrastructure.vault.keyring", fake_keyring)
    monkeypatch.setattr("phoenix.infrastructure.vault.keyring.errors", errors)

    vault = KeyringVault()
    with pytest.raises(VaultError):
        vault.store("key", "value")


def test_autovault_uses_keyring_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """``AutoVault`` uses the system keyring when it is functional."""
    passwords: dict[str, Any] = {}
    errors = MagicMock()
    errors.KeyringError = type("KeyringError", (Exception,), {})
    fake_keyring = MagicMock()
    fake_keyring.set_password = lambda _service, key, value: passwords.update({key: value})
    fake_keyring.get_password = lambda _service, key: passwords.get(key)
    fake_keyring.delete_password = lambda _service, key: passwords.pop(key, None)
    fake_keyring.errors = errors

    monkeypatch.setattr("phoenix.infrastructure.vault.keyring", fake_keyring)
    monkeypatch.setattr("phoenix.infrastructure.vault.keyring.errors", errors)

    vault = AutoVault()
    assert vault.uses_keyring is True
    vault.store("key", "value")
    assert vault.retrieve("key") == "value"


def test_autovault_falls_back_to_file_vault(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``AutoVault`` falls back to an encrypted file when keyring fails."""
    errors = MagicMock()
    errors.KeyringError = type("KeyringError", (Exception,), {})
    fake_keyring = MagicMock()
    fake_keyring.set_password = MagicMock(side_effect=errors.KeyringError("no keyring"))
    fake_keyring.errors = errors

    monkeypatch.setattr("phoenix.infrastructure.vault.keyring", fake_keyring)
    monkeypatch.setattr("phoenix.infrastructure.vault.keyring.errors", errors)

    vault = AutoVault(file_path=tmp_path / "fallback.json")
    assert vault.uses_keyring is False
    vault.store("key", "value")
    assert vault.retrieve("key") == "value"
