from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from gerpgo_cli.main import app

runner = CliRunner()


def test_capabilities_lists_twelve_read_only_post_endpoints() -> None:
    result = runner.invoke(app, ["capabilities", "--format", "json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert len(payload["data"]["openapi"]) == 12
    assert {item["method"] for item in payload["data"]["openapi"]} == {"POST"}
    assert payload["data"]["webapi"]["business_endpoints"] == []
    assert payload["data"]["webapi"]["raw_request"] is False


def test_missing_profile_returns_stable_json_error(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setenv("GERPGO_CONFIG_DIR", str(tmp_path))  # type: ignore[attr-defined]
    result = runner.invoke(app, ["profile", "show", "missing"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error_code"] == "GERPGO_CONFIG_MISSING"


def test_profile_init_from_env_does_not_write_to_keyring(
    tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("GERPGO_CONFIG_DIR", str(tmp_path))  # type: ignore[attr-defined]
    monkeypatch.setenv("GERPGO_OPENAPI_APP_ID", "DEMO_APP_ID")  # type: ignore[attr-defined]
    monkeypatch.setenv("GERPGO_OPENAPI_APP_KEY", "DEMO_APP_KEY")  # type: ignore[attr-defined]

    def reject_keyring_write(*args: object) -> None:
        raise AssertionError("keyring should not be written in --from-env mode")

    monkeypatch.setattr("keyring.set_password", reject_keyring_write)  # type: ignore[attr-defined]
    result = runner.invoke(
        app,
        ["profile", "init", "demo", "--from-env", "--no-enable-web"],
    )
    assert result.exit_code == 0, result.stdout
    profile_text = (tmp_path / "profiles.json").read_text(encoding="utf-8")
    assert "DEMO_APP_ID" not in profile_text
    assert "DEMO_APP_KEY" not in profile_text


def test_profile_can_come_from_environment(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setenv("GERPGO_CONFIG_DIR", str(tmp_path))  # type: ignore[attr-defined]
    monkeypatch.setenv("GERPGO_PROFILE", "missing")  # type: ignore[attr-defined]
    result = runner.invoke(app, ["openapi", "product", "list"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["error_code"] == "GERPGO_CONFIG_MISSING"


def test_skill_install_and_update_are_atomic(tmp_path: Path) -> None:
    result = runner.invoke(app, ["skill", "install", "--target-root", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    skill_file = tmp_path / "gerpgo-erp" / "SKILL.md"
    assert skill_file.exists()
    assert 'version: "0.1.0"' in skill_file.read_text(encoding="utf-8")

    result = runner.invoke(app, ["skill", "update", "--target-root", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert not list(tmp_path.glob(".gerpgo-erp.*"))
