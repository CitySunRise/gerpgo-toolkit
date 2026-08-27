from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from filelock import FileLock
from platformdirs import user_state_path


class PersistentRateLimiter:
    """Serialize request starts across CLI processes without storing business data."""

    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        clock: Callable[[], float] = time.time,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        override = os.getenv("GERPGO_STATE_DIR")
        self.state_dir = state_dir or (
            Path(override)
            if override
            else user_state_path("gerpgo-toolkit", appauthor="CitySunRise", roaming=False)
        )
        self.clock = clock
        self.sleeper = sleeper
        self.path = self.state_dir / "rate-limits.json"
        self.lock_path = self.state_dir / "rate-limits.lock"

    def wait(self, key: str, minimum_interval_seconds: float) -> None:
        if minimum_interval_seconds <= 0:
            return
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.lock_path), timeout=120):
            state = self._read()
            now = self.clock()
            last_start = float(state.get(key, 0.0))
            remaining = minimum_interval_seconds - (now - last_start)
            if remaining > 0:
                self.sleeper(remaining)
                now = self.clock()
            state[key] = now
            self._write(state)

    def _read(self) -> dict[str, float]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {
            str(key): float(value) for key, value in data.items() if isinstance(value, int | float)
        }

    def _write(self, data: dict[str, float]) -> None:
        fd, temp_name = tempfile.mkstemp(prefix="rate-", suffix=".json", dir=self.state_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, separators=(",", ":"), sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, self.path)
            os.chmod(self.path, 0o600)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
