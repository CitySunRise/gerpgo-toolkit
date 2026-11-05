from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from gerpgo_cli.commands import catalog_raw, expanded, openapi
from gerpgo_cli.main import app
from gerpgo_sdk.openapi import ENDPOINTS
from gerpgo_sdk.openapi.expanded import EXCLUDED_READ_IDS, catalog_documents, route

SKILL_ROOT = Path("skills/gerpgo-erp")

COMMANDS = {
    "product-list": "gerpgo-cli openapi product list",
    "product-inventory": "gerpgo-cli openapi inventory product",
    "sales-performance": "gerpgo-cli openapi statistics sales-performance",
    "search-term-performance": "gerpgo-cli openapi ads search-term-performance",
    "review": "gerpgo-cli openapi customer review",
    "buyer-voice": "gerpgo-cli openapi customer buyer-voice",
    "profit-analysis-v2": "gerpgo-cli openapi finance profit-analysis-v2",
    "keyword-performance": "gerpgo-cli openapi ads keyword-performance",
    "listing-performance": "gerpgo-cli openapi statistics listing-performance",
    "asin-traffic-statistics": "gerpgo-cli openapi statistics asin-traffic-statistics",
    "asin-traffic-data": "gerpgo-cli openapi statistics asin-traffic-data",
    "catalog-amazon-shops": "gerpgo-cli openapi catalog amazon-shops list",
    "catalog-users": "gerpgo-cli openapi catalog users list",
    "catalog-warehouses": "gerpgo-cli openapi catalog warehouses list",
    "catalog-brands": "gerpgo-cli openapi catalog brands list",
    "catalog-categories": "gerpgo-cli openapi catalog categories list",
    "catalog-multiplatform-shops": "gerpgo-cli openapi catalog multiplatform-shops list",
    "catalog-amazon-shop-names": "gerpgo-cli openapi catalog amazon-shops names-by-id",
    "catalog-amazon-shop-warehouses": "gerpgo-cli openapi catalog amazon-shops warehouses-by-id",
}


def test_skill_maps_common_commands_with_examples() -> None:
    command_map = (SKILL_ROOT / "references/command-map.md").read_text(encoding="utf-8")
    parameters = (SKILL_ROOT / "references/endpoint-parameters.md").read_text(encoding="utf-8")
    assert set(COMMANDS) == {key for key, spec in ENDPOINTS.items() if spec.cli_route is None}
    examples = re.findall(r"示例：`(gerpgo-cli [^`]+)`", parameters)
    assert len(examples) == len(COMMANDS) == 19
    for command in COMMANDS.values():
        assert command in command_map
        assert any(example.startswith(command) for example in examples)


def test_skill_examples_parse_and_validate_without_erp(monkeypatch: pytest.MonkeyPatch) -> None:
    called = []

    class OfflineService:
        def query(self, spec: Any, payload: Any, **kwargs: Any) -> dict[str, Any]:
            spec.validate_payload(payload)
            called.append(spec.key)
            return {"code": 200, "data": {}}

    for module in (openapi, catalog_raw, expanded):
        monkeypatch.setattr(module, "openapi_service", lambda profile: OfflineService())
    parameters = (SKILL_ROOT / "references/endpoint-parameters.md").read_text(encoding="utf-8")
    examples = re.findall(r"示例：`(gerpgo-cli [^`]+)`", parameters)
    runner = CliRunner()
    for example in examples:
        command = shlex.split(example)[1:] + ["--response", "raw"]
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.stdout
        assert json.loads(result.stdout)["ok"] is True
    assert set(called) == set(COMMANDS)
    assert len(called) == 19


def test_skill_links_and_removed_commands() -> None:
    texts = []
    for path in SKILL_ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        texts.append(text)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in target:
                assert (path.parent / target).is_file(), (path, target)
    combined = "\n".join(texts)
    for doc in catalog_documents():
        if doc["id"] not in EXCLUDED_READ_IDS:
            continue
        module, command = route(doc)
        if doc["id"] == 131:
            command = "product-performance"
        assert f"gerpgo-cli openapi {module} {command}" not in combined
    assert "live-verification" not in combined


def test_skill_preserves_full_query_workflow() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for intent in ("全部", "完整数据", "完整分析", "导出", "所有数据"):
        assert intent in skill
    assert "--all-pages --max-pages 100" in skill
    assert "pagination.complete=true" in skill
    assert "pagination.truncated=false" in skill
