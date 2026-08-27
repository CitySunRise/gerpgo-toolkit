from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from platformdirs import user_state_path

from gerpgo_sdk.config.secrets import SecretStore


class WebSessionStore:
    def __init__(
        self,
        secrets_store: SecretStore,
        state_dir: Path | None = None,
    ) -> None:
        override = os.getenv("GERPGO_STATE_DIR")
        self.state_dir = state_dir or (
            Path(override)
            if override
            else user_state_path("gerpgo-toolkit", appauthor="CitySunRise", roaming=False)
        )
        self.path = self.state_dir / "web-sessions.json"
        self.secrets = secrets_store

    def save(self, profile: str, token: str) -> None:
        self.secrets.set(profile, "web_session_token", token)
        state = self._read()
        state[profile] = {
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": None,
        }
        self._write(state)

    def status(self, profile: str) -> dict[str, Any]:
        state = self._read().get(profile, {})
        session_cached = bool(self.secrets.get(profile, "web_session_token"))
        return {
            "profile": profile,
            "authenticated": session_cached,
            "session_cached": session_cached,
            "created_at": state.get("created_at"),
            "expires_at": state.get("expires_at"),
            "checked_online": False,
        }

    def clear(self, profile: str) -> bool:
        removed = self.secrets.delete(profile, "web_session_token")
        state = self._read()
        if profile in state:
            del state[profile]
            self._write(state)
            removed = True
        return removed

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write(self, data: dict[str, dict[str, Any]]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="web-session-", suffix=".json", dir=self.state_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, self.path)
            os.chmod(self.path, 0o600)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
