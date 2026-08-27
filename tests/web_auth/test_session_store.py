from __future__ import annotations

from pathlib import Path

from gerpgo_sdk.webapi.auth import WebSessionStore


class MemorySecrets:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def set(self, profile: str, key: str, value: str) -> None:
        self.values[(profile, key)] = value

    def get(self, profile: str, key: str) -> str | None:
        return self.values.get((profile, key))

    def delete(self, profile: str, key: str) -> bool:
        return self.values.pop((profile, key), None) is not None


def test_session_metadata_never_contains_token(tmp_path: Path) -> None:
    secrets = MemorySecrets()
    store = WebSessionStore(secrets, tmp_path)  # type: ignore[arg-type]
    store.save("demo", "DEMO_SESSION_TOKEN")

    assert "DEMO_SESSION_TOKEN" not in store.path.read_text(encoding="utf-8")
    assert store.status("demo")["authenticated"] is True
    assert store.clear("demo") is True
    assert store.status("demo")["authenticated"] is False
