"""Secure credential vault for Phoenix Engine.

Provides pluggable secret storage. The default ``AutoVault`` tries the system
keyring first and falls back to an encrypted file when keyring is unavailable
or raises an error. All values are stored as strings and returned as strings.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

import keyring
import keyring.errors
from cryptography.fernet import Fernet, InvalidToken


class VaultError(Exception):
    """Raised when a vault operation fails."""


class SecretNotFoundError(VaultError):
    """Raised when a requested secret does not exist in the vault."""


class VaultBackend(ABC):
    """Abstract secure credential storage backend."""

    @abstractmethod
    def store(self, key: str, value: str) -> None:
        """Store ``value`` under ``key``."""

    @abstractmethod
    def retrieve(self, key: str) -> str:
        """Retrieve the secret stored under ``key``."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the secret stored under ``key``."""

    @abstractmethod
    def list_keys(self) -> list[str]:
        """Return all stored secret keys."""


class KeyringVault(VaultBackend):
    """System keyring-backed vault.

    Uses the ``keyring`` library to store secrets in the OS credential store.
    """

    SERVICE_NAME = "phoenix-engine"

    def __init__(self, service_name: str = SERVICE_NAME) -> None:
        """Initialize the keyring vault.

        Args:
            service_name: Service namespace passed to keyring.
        """
        self._keyring = keyring
        self._errors = keyring.errors
        self._service_name = service_name

    def store(self, key: str, value: str) -> None:
        """Store ``value`` under ``key`` in the system keyring."""
        try:
            self._keyring.set_password(self._service_name, key, value)
        except self._errors.KeyringError as exc:
            raise VaultError(f"Failed to store secret '{key}' in keyring: {exc}") from exc

    def retrieve(self, key: str) -> str:
        """Retrieve the secret stored under ``key`` from the system keyring."""
        try:
            value = self._keyring.get_password(self._service_name, key)
        except self._errors.KeyringError as exc:
            raise VaultError(f"Failed to retrieve secret '{key}' from keyring: {exc}") from exc
        if value is None:
            raise SecretNotFoundError(f"Secret '{key}' not found in keyring")
        return value

    def delete(self, key: str) -> None:
        """Delete the secret stored under ``key`` from the system keyring."""
        try:
            self._keyring.delete_password(self._service_name, key)
        except self._errors.PasswordDeleteError as exc:
            raise VaultError(f"Failed to delete secret '{key}' from keyring: {exc}") from exc
        except self._errors.KeyringError as exc:
            raise VaultError(f"Failed to delete secret '{key}' from keyring: {exc}") from exc

    def list_keys(self) -> list[str]:
        """Return all stored secret keys from the system keyring.

        The system keyring API does not provide a portable way to list all
        stored keys. This method returns an empty list and relies on callers
        tracking known keys.
        """
        return []


class FileVault(VaultBackend):
    """Encrypted file-backed vault using Fernet.

    Secrets are stored in a JSON file encrypted at rest. The encryption key is
    derived from a password or loaded from ``PHOENIX_VAULT_KEY``.
    """

    DEFAULT_FILENAME = "phoenix-vault.json"

    def __init__(
        self,
        path: str | os.PathLike[str] | None = None,
        *,
        key: bytes | str | None = None,
    ) -> None:
        """Initialize the file vault.

        Args:
            path: Path to the encrypted vault file. Defaults to
                ``~/.phoenix/phoenix-vault.json``.
            key: Fernet key or base64-encoded string. If omitted, the
                ``PHOENIX_VAULT_KEY`` environment variable is used. If that is
                also missing, a deterministic key is derived from the file path
                (suitable only for local development).
        """
        self._path = Path(path) if path is not None else self._default_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(self._resolve_key(key))

    @classmethod
    def _default_path(cls) -> Path:
        return Path.home() / ".phoenix" / cls.DEFAULT_FILENAME

    @staticmethod
    def _normalize_key_material(material: bytes) -> bytes:
        """Pad or truncate ``material`` to 32 bytes and base64-urlsafe encode."""
        return base64.urlsafe_b64encode(material[:32].ljust(32, b"\0"))

    def _resolve_key(self, key: bytes | str | None) -> bytes:
        """Resolve a Fernet key from the provided value, env var, or path."""
        if isinstance(key, str):
            return self._normalize_key_material(base64.urlsafe_b64decode(key.encode()))
        if isinstance(key, bytes):
            return self._normalize_key_material(key)
        env_key = os.environ.get("PHOENIX_VAULT_KEY")
        if env_key:
            return self._normalize_key_material(base64.urlsafe_b64decode(env_key.encode()))
        # Deterministic development-only key derived from the vault path.
        digest = hashlib.sha256(str(self._path).encode()).digest()
        return self._normalize_key_material(digest)

    def _load_blob(self) -> dict[str, str]:
        """Decrypt and parse the vault file."""
        if not self._path.exists():
            return {}
        try:
            encrypted = self._path.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            data: dict[str, str] = json.loads(decrypted.decode("utf-8"))
        except InvalidToken as exc:
            raise VaultError("Vault file is corrupted or uses a different key") from exc
        except json.JSONDecodeError as exc:
            raise VaultError(f"Vault file contains invalid JSON: {exc}") from exc
        else:
            return data

    def _save_blob(self, data: dict[str, str]) -> None:
        """Serialize and encrypt the vault file."""
        plaintext = json.dumps(data, sort_keys=True).encode("utf-8")
        encrypted = self._fernet.encrypt(plaintext)
        self._path.write_bytes(encrypted)

    def store(self, key: str, value: str) -> None:
        """Store ``value`` under ``key`` in the encrypted file vault."""
        data = self._load_blob()
        data[key] = value
        self._save_blob(data)

    def retrieve(self, key: str) -> str:
        """Retrieve the secret stored under ``key`` from the encrypted file vault."""
        data = self._load_blob()
        if key not in data:
            raise SecretNotFoundError(f"Secret '{key}' not found in vault")
        return data[key]

    def delete(self, key: str) -> None:
        """Delete the secret stored under ``key`` from the encrypted file vault."""
        data = self._load_blob()
        data.pop(key, None)
        self._save_blob(data)

    def list_keys(self) -> list[str]:
        """Return all stored secret keys from the encrypted file vault."""
        return sorted(self._load_blob().keys())


class AutoVault(VaultBackend):
    """Vault that prefers the system keyring and falls back to an encrypted file."""

    def __init__(
        self,
        file_path: str | os.PathLike[str] | None = None,
        *,
        file_key: bytes | str | None = None,
        service_name: str = "phoenix-engine",
    ) -> None:
        """Initialize the auto vault.

        Args:
            file_path: Path for the encrypted fallback file vault.
            file_key: Encryption key for the fallback file vault.
            service_name: Service namespace passed to keyring.
        """
        self._file_vault = FileVault(path=file_path, key=file_key)
        self._keyring_vault: VaultBackend | None = None
        try:
            self._keyring_vault = KeyringVault(service_name=service_name)
            # Probe the keyring to confirm it is functional.
            self._keyring_vault.store("__phoenix_probe__", "ok")
            self._keyring_vault.delete("__phoenix_probe__")
        except Exception:  # noqa: BLE001
            self._keyring_vault = None

    def _backend(self) -> VaultBackend:
        """Return the active backend (keyring preferred, file fallback)."""
        return self._keyring_vault or self._file_vault

    def store(self, key: str, value: str) -> None:
        """Store ``value`` under ``key``."""
        self._backend().store(key, value)

    def retrieve(self, key: str) -> str:
        """Retrieve the secret stored under ``key``."""
        return self._backend().retrieve(key)

    def delete(self, key: str) -> None:
        """Delete the secret stored under ``key``."""
        self._backend().delete(key)

    def list_keys(self) -> list[str]:
        """Return all stored secret keys."""
        return self._backend().list_keys()

    @property
    def uses_keyring(self) -> bool:
        """Return ``True`` when the system keyring is being used."""
        return self._keyring_vault is not None


def get_default_vault(
    file_path: str | os.PathLike[str] | None = None,
    *,
    file_key: bytes | str | None = None,
    service_name: str = "phoenix-engine",
) -> VaultBackend:
    """Return the default vault backend for the current environment."""
    return AutoVault(
        file_path=file_path,
        file_key=file_key,
        service_name=service_name,
    )


__all__ = [
    "AutoVault",
    "FileVault",
    "KeyringVault",
    "SecretNotFoundError",
    "VaultBackend",
    "VaultError",
    "get_default_vault",
]
