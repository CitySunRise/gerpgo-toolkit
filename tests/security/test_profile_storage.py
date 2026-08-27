from __future__ import annotations

import json
import stat
from pathlib import Path

from gerpgo_sdk.config import Profile, ProfileStore


def test_profile_file_contains_only_non_secret_settings(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path)
    store.save(Profile(name="demo", web_enabled=True, web_base_url="https://erp.example.invalid"))

    text = store.path.read_text(encoding="utf-8")
    data = json.loads(text)
    assert data["profiles"]["demo"]["name"] == "demo"
    assert "password" not in text.lower()
    assert "app_key" not in text.lower()
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
