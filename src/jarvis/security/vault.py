"""Secure Local Credential Vault using Linux Keyring and secure fallback."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import keyring
from keyring.errors import KeyringError

SERVICE_NAME = "jarvis_assistant"
FALLBACK_VAULT_PATH = Path.home() / ".jarvis" / ".vault_store"

class SecretVault:
    def __init__(self):
        self.fallback_file = FALLBACK_VAULT_PATH
        self._ensure_fallback_dir()

    def _ensure_fallback_dir(self) -> None:
        self.fallback_file.parent.mkdir(parents=True, exist_ok=True)

    def set_secret(self, key: str, value: str) -> bool:
        """Store a secret securely."""
        try:
            keyring.set_password(SERVICE_NAME, key, value)
            return True
        except KeyringError:
            # Fallback to local user-readable-only file
            store = self._read_fallback()
            store[key] = value
            self._write_fallback(store)
            return True

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret."""
        # 1. Check environment variable first
        env_val = os.getenv(key.upper())
        if env_val:
            return env_val

        # 2. Check system keyring
        try:
            val = keyring.get_password(SERVICE_NAME, key)
            if val is not None:
                return val
        except KeyringError:
            pass

        # 3. Check fallback store
        store = self._read_fallback()
        return store.get(key)

    def delete_secret(self, key: str) -> bool:
        try:
            keyring.delete_password(SERVICE_NAME, key)
        except Exception:
            pass
        store = self._read_fallback()
        if key in store:
            del store[key]
            self._write_fallback(store)
        return True

    def list_keys(self) -> List[str]:
        """List keys present in fallback store (keyring API does not support enumeration natively)."""
        store = self._read_fallback()
        return list(store.keys())

    def _read_fallback(self) -> Dict[str, str]:
        if not self.fallback_file.exists():
            return {}
        try:
            with open(self.fallback_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_fallback(self, store: Dict[str, str]) -> None:
        # Create file with 0600 permissions (read/write only by owner)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        fd = os.open(str(self.fallback_file), flags, 0o600)
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(store, f)
