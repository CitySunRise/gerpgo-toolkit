from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from platformdirs import user_config_path

from gerpgo_sdk.common.errors import ConfigError, ValidationError

from .models import Profile


class ProfileStore:
    def __init__(self, config_dir: Path | None = None) -> None:
        override = os.getenv("GERPGO_CONFIG_DIR")
        self.config_dir = config_dir or (
            Path(override)
            if override
            else user_config_path("gerpgo-toolkit", appauthor="CitySunRise", roaming=False)
        )
        self.path = self.config_dir / "profiles.json"

    def list(self) -> list[Profile]:
        data = self._read()
        return [Profile.from_dict(item) for _, item in sorted(data["profiles"].items())]

    def get(self, name: str) -> Profile:
        data = self._read()
        raw = data["profiles"].get(name)
        if raw is None:
            raise ConfigError(
                f"Profile '{name}' does not exist. Run 'gerpgo-cli profile init {name}'."
            )
        return Profile.from_dict(raw)

    def save(self, profile: Profile) -> None:
        if not profile.name or any(char in profile.name for char in "/\\"):
            raise ValidationError(
                "Profile name must be non-empty and cannot contain path separators."
            )
        data = self._read()
        data["profiles"][profile.name] = profile.to_dict()
        self._write(data)

    def delete(self, name: str) -> bool:
        data = self._read()
        removed = data["profiles"].pop(name, None) is not None
        if removed:
            self._write(data)
        return removed

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "profiles": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigError("Profile file is unreadable.") from exc
        if not isinstance(data, dict) or not isinstance(data.get("profiles"), dict):
            raise ConfigError("Profile file has an unsupported structure.")
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="profiles-", suffix=".json", dir=self.config_dir)
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
