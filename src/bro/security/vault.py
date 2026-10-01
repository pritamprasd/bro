"""Secure Local Credential Vault using Linux Keyring and secure fallback.

The vault uses a three-tier priority for retrieval:
  1. Environment variable (KEY_NAME in uppercase)
  2. System keyring (GNOME Keyring / libsecret via keyring library)
  3. Encrypted fallback JSON (~/.bro/.vault_store)

Since the keyring API does not support key enumeration, we maintain a
separate key-name index (~/.bro/.vault_index) that is updated on every
set/delete operation. This ensures `list_keys()` is always accurate
regardless of which backend stored the secret.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import keyring
from keyring.errors import KeyringError

SERVICE_NAME = "bro_assistant"
FALLBACK_VAULT_PATH = Path.home() / ".bro" / ".vault_store"
KEY_INDEX_PATH = Path.home() / ".bro" / ".vault_index"


class SecretVault:
    def __init__(self):
        self.fallback_file = FALLBACK_VAULT_PATH
        self.index_file = KEY_INDEX_PATH
        self._ensure_vault_dir()

    def _ensure_vault_dir(self) -> None:
        self.fallback_file.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_secret(self, key: str, value: str) -> bool:
        """Store a secret securely (keyring preferred, fallback JSON otherwise)."""
        stored_in_keyring = False
        try:
            keyring.set_password(SERVICE_NAME, key, value)
            stored_in_keyring = True
        except KeyringError:
            pass

        if not stored_in_keyring:
            # Fallback to local user-readable-only file
            store = self._read_fallback()
            store[key] = value
            self._write_fallback(store)

        # Always update the key-name index so list_keys() stays accurate
        self._add_to_index(key)
        return True

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret (env → keyring → fallback JSON)."""
        # 1. Environment variable takes highest precedence
        env_val = os.getenv(key.upper())
        if env_val:
            return env_val

        # 2. System keyring
        try:
            val = keyring.get_password(SERVICE_NAME, key)
            if val is not None:
                return val
        except KeyringError:
            pass

        # 3. Fallback JSON store
        store = self._read_fallback()
        return store.get(key)

    def get_secrets(self, keys: List[str]) -> Dict[str, Optional[str]]:
        """Batch-retrieve multiple secrets in a single call."""
        return {k: self.get_secret(k) for k in keys}

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from all backends and remove from index."""
        try:
            keyring.delete_password(SERVICE_NAME, key)
        except Exception:
            pass
        store = self._read_fallback()
        if key in store:
            del store[key]
            self._write_fallback(store)
        self._remove_from_index(key)
        return True

    def list_keys(self) -> List[str]:
        """List all stored secret key names.

        Reads from the key-name index (~/.bro/.vault_index) which is kept
        in sync with both keyring and fallback-JSON backends so that keys
        stored exclusively in the system keyring are also returned.
        """
        return self._read_index()

    # ------------------------------------------------------------------
    # Fallback JSON helpers
    # ------------------------------------------------------------------

    def _read_fallback(self) -> Dict[str, str]:
        if not self.fallback_file.exists():
            return {}
        try:
            with open(self.fallback_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_fallback(self, store: Dict[str, str]) -> None:
        # 0600 permissions: read/write only by owner
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        fd = os.open(str(self.fallback_file), flags, 0o600)
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(store, f)

    # ------------------------------------------------------------------
    # Key-name index helpers
    # ------------------------------------------------------------------

    def _read_index(self) -> List[str]:
        if not self.index_file.exists():
            # Seed from fallback store if index doesn't exist yet (migration)
            existing_keys = list(self._read_fallback().keys())
            if existing_keys:
                self._write_index(existing_keys)
            return existing_keys
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _write_index(self, keys: List[str]) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        fd = os.open(str(self.index_file), flags, 0o600)
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(sorted(set(keys)), f)

    def _add_to_index(self, key: str) -> None:
        keys = self._read_index()
        if key not in keys:
            keys.append(key)
            self._write_index(keys)

    def _remove_from_index(self, key: str) -> None:
        keys = self._read_index()
        if key in keys:
            keys.remove(key)
            self._write_index(keys)

