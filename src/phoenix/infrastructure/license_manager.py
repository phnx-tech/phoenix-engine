"""Offline license-key management for Phoenix Engine.

License keys are signed with an HMAC-SHA256 secret. They can carry optional
expiration dates and usage limits, so a maintainer can issue time- or
volume-bounded keys to early clients without building a full billing system.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from phoenix.exceptions import (
    LicenseError,
    LicenseExpiredError,
    LicenseInvalidError,
    LicenseMissingError,
    LicenseUsesExceededError,
)

if TYPE_CHECKING:
    from phoenix.models.config import Config


class LicenseManager:
    """Generate and validate HMAC-signed Phoenix Engine license keys.

    Keys are ``phx.<payload>.<signature>`` where ``payload`` is a JSON object
    with version, creation time, optional expiration, optional maximum uses,
    and an optional note. The signature is HMAC-SHA256 over the canonical JSON
    representation of the payload.

    Usage counting is stored locally in ``<data_dir>/license_state.json`` and
    is keyed by the SHA-256 hash of the license key, so the raw key is never
    persisted.
    """

    KEY_PREFIX = "phx"
    VERSION = 1
    STATE_VERSION = 1
    KEY_PART_COUNT = 3
    MASK_THRESHOLD = 12
    MASK_VISIBLE = 6

    def __init__(
        self,
        secret: str | None,
        license_key: str | None,
        *,
        state_path: Path | str | None = None,
    ) -> None:
        """Create a license manager.

        Args:
            secret: HMAC secret used to sign or verify license keys.
            license_key: License key to validate. May be ``None`` when only
                generating keys.
            state_path: Path to the local license-state file. Defaults to
                ``.phoenix/license_state.json``.
        """
        self.secret = secret
        self.license_key = license_key
        self.state_path = (
            Path(state_path) if state_path is not None else Path(".phoenix") / "license_state.json"
        )

    @classmethod
    def from_config(cls, config: Config) -> LicenseManager:
        """Build a ``LicenseManager`` from application configuration.

        The signing secret can be supplied via ``config.license_secret`` or the
        ``PHOENIX_LICENSE_SECRET`` environment variable.
        """
        return cls(
            secret=config.license_secret,
            license_key=config.license_key,
            state_path=Path(config.data_dir) / "license_state.json",
        )

    def generate_key(
        self,
        *,
        expires_at: datetime | None = None,
        max_uses: int | None = None,
        note: str = "",
    ) -> str:
        """Generate a new signed license key.

        Args:
            expires_at: Optional expiration timestamp (UTC).
            max_uses: Optional maximum number of successful validations.
            note: Optional human-readable note embedded in the payload.

        Returns:
            A ``phx.<payload>.<signature>`` license key.

        Raises:
            LicenseError: If no signing secret is configured.
        """
        if not self.secret:
            raise LicenseError("A license secret is required to generate keys")
        if max_uses is not None and max_uses < 1:
            raise LicenseError("max_uses must be >= 1")

        payload: dict[str, Any] = {
            "v": self.VERSION,
            "created": datetime.now(UTC).isoformat(),
            "exp": expires_at.isoformat() if expires_at is not None else None,
            "max_uses": max_uses,
            "note": note,
        }
        signature = self._sign(payload)
        payload_b64 = (
            base64.urlsafe_b64encode(
                self._canonical_payload(payload).encode("utf-8"),
            )
            .decode("ascii")
            .rstrip("=")
        )
        return f"{self.KEY_PREFIX}.{payload_b64}.{signature}"

    def validate(self, *, raise_on_failure: bool = True) -> dict[str, Any] | None:
        """Validate the configured license key.

        On success, the use counter is incremented when ``max_uses`` is set.

        Args:
            raise_on_failure: If ``True`` (default), raise a ``LicenseError``
                subclass on invalid/missing keys. Otherwise return ``None``.

        Returns:
            The decoded license payload, or ``None`` when validation fails and
            ``raise_on_failure`` is ``False``.
        """
        error: LicenseError | None = None

        if self.license_key is None:
            error = LicenseMissingError("A license key is required")
        elif self.secret is None:
            error = LicenseError("A license secret is required to validate keys")
        else:
            try:
                payload = self._decode_key(self.license_key)
            except LicenseError as exc:
                error = exc
            else:
                exp = payload.get("exp")
                if exp is not None:
                    expires_at = datetime.fromisoformat(exp)
                    if datetime.now(UTC) > expires_at:
                        error = LicenseExpiredError("License key has expired")

                max_uses = payload.get("max_uses")
                if error is None and max_uses is not None and self._get_uses() >= max_uses:
                    error = LicenseUsesExceededError("License key use limit exceeded")

                if error is None:
                    self._record_use()
                    return payload

        if raise_on_failure and error is not None:
            raise error
        return None

    def inspect(self, key: str | None = None) -> dict[str, Any] | None:
        """Decode a license key without validating signature or counters.

        This is useful for displaying metadata. It still raises
        ``LicenseInvalidError`` if the payload cannot be decoded.
        """
        target = key if key is not None else self.license_key
        if target is None:
            return None
        return self._decode_key(target)

    @property
    def masked_key(self) -> str | None:
        """Return the configured key with most characters masked."""
        if self.license_key is None:
            return None
        if len(self.license_key) <= self.MASK_THRESHOLD:
            return "***"
        return (
            f"{self.license_key[:self.MASK_VISIBLE]}"
            f"..."
            f"{self.license_key[-self.MASK_VISIBLE:]}"
        )

    def _decode_key(self, key: str) -> dict[str, Any]:
        """Decode and verify the signature of a license key."""
        parts = key.split(".")
        if len(parts) != self.KEY_PART_COUNT or parts[0] != self.KEY_PREFIX:
            raise LicenseInvalidError("Malformed license key")

        payload_b64, signature = parts[1], parts[2]
        try:
            payload_json = base64.urlsafe_b64decode(self._pad(payload_b64)).decode("utf-8")
            payload = json.loads(payload_json)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LicenseInvalidError(f"Malformed license key payload: {exc}") from exc

        if not isinstance(payload, dict) or payload.get("v") != self.VERSION:
            raise LicenseInvalidError("Unsupported license key version")

        expected_signature = self._sign(payload)
        if not hmac.compare_digest(expected_signature, signature):
            raise LicenseInvalidError("License key signature mismatch")

        return payload

    def _sign(self, payload: dict[str, Any]) -> str:
        """Return the base64url HMAC-SHA256 signature for a payload."""
        if self.secret is None:
            raise LicenseError("A license secret is required to sign keys")
        canonical = self._canonical_payload(payload)
        signature = hmac.new(
            self.secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

    @staticmethod
    def _canonical_payload(payload: dict[str, Any]) -> str:
        """Return a deterministic JSON representation of the payload."""
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _pad(b64: str) -> str:
        """Add base64 padding removed by ``rstrip('=')``."""
        padding_needed = (-len(b64)) % 4
        return b64 + ("=" * padding_needed)

    def _key_id(self) -> str:
        """Return a stable identifier for the configured license key."""
        if self.license_key is None:
            raise LicenseMissingError("No license key configured")
        return hashlib.sha256(self.license_key.encode("utf-8")).hexdigest()

    def _load_state(self) -> dict[str, Any]:
        """Load the local license-state file."""
        if not self.state_path.exists():
            return {"version": self.STATE_VERSION, "uses": {}}
        try:
            return cast("dict[str, Any]", json.loads(self.state_path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return {"version": self.STATE_VERSION, "uses": {}}

    def _save_state(self, state: dict[str, Any]) -> None:
        """Persist the local license-state file."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def _get_uses(self) -> int:
        """Return the number of recorded uses for the configured key."""
        state = self._load_state()
        uses = cast("dict[str, int]", state.get("uses", {}))
        return uses.get(self._key_id(), 0)

    def _record_use(self) -> None:
        """Increment the use counter for the configured key."""
        state = self._load_state()
        key_id = self._key_id()
        state.setdefault("uses", {})[key_id] = state.get("uses", {}).get(key_id, 0) + 1
        self._save_state(state)
