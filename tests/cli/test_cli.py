from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from gerpgo_cli.commands import catalog as catalog_commands
from gerpgo_cli.commands import openapi as openapi_commands
from gerpgo_cli.commands import web_auth as web_auth_commands
from gerpgo_cli.main import app
from gerpgo_cli.output import _json_text
from gerpgo_sdk.common.errors import PageLimitExceededError
from gerpgo_sdk.openapi.catalog.models import BrandRecord

runner = CliRunner()


class RecordingOpenApiService:
    def __init__(self, profile: str) -> None:
        self.profile = profile

    def query(self, *args: Any, **kwargs: Any) -> dict[str, str]:
        return {"profile": self.profile}


class RecordingCatalogService:
    def __init__(self, profile: str) -> None:
        self.profile = profile

    def brands(self, **kwargs: Any) -> list[BrandRecord]:
        return [BrandRecord(self.profile, "示例品牌", "Active")]


class ValidatingOpenApiService:
    def query(self, spec: Any, payload: dict[str, Any], **kwargs: Any) -> dict[str, object]:
        spec.validate_payload(payload)
        return {"validated": True, "endpoint": spec.key}


class PayloadOpenApiService:
    def query(self, spec: Any, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        spec.validate_payload(payload)
        return {"endpoint": spec.key, "payload": payload}


class PaginationOpenApiService:
    def query(self, spec: Any, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        spec.validate_payload(payload)
        return {"endpoint": spec.key, "payload": payload, "options": kwargs}


class PageLimitOpenApiService:
    def query(self, spec: Any, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        raise PageLimitExceededError(
            "完整查询预计需要 300 页，超过默认安全上限 100。请确认后提高 --max-pages。",
            details={
                "total_records": 150000,
                "page_size": 500,
                "estimated_pages": 300,
                "max_pages": 100,
                "estimated_seconds": 17940,
            },
        )


class SyntheticCatalogResolver:
    @staticmethod
    def reject_conflict(identifier: Any, name: Any, label: str) -> None:
        if identifier not in (None, [], "") and name not in (None, [], ""):
            from gerpgo_sdk.common.errors import ValidationError

            raise ValidationError(f"Use either {label} ID/code or {label} name, not both.")

    def amazon_shop(self, name: str, **kwargs: Any) -> str:
        return "100001"

    def warehouse(self, name: str) -> str:
        return "200001"

    def user(self, name: str) -> str:
        return "300001"

    def brand(self, name: str) -> str:
        return "BRAND-DEMO"

    def category(self, name: str) -> str:
        return "CATEGORY-DEMO"


class RecordingWebAuthService:
    def login(self, profile: str, username: str, password: str) -> dict[str, object]:
        return {"profile": profile, "authenticated": True}


class RecordingProfileStore:
    selected: list[str] = []

    def get(self, profile: str) -> object:
        self.selected.append(profile)
        return object()


class RecordingWebSessionStore:
    def __init__(self, secrets: object) -> None:
        self.secrets = secrets

    def status(self, profile: str) -> dict[str, object]:
        return {"profile": profile, "authenticated": False}

    def clear(self, profile: str) -> bool:
        return False


def test_json_output_falls_back_to_ascii_for_legacy_windows_console() -> None:
    rendered = _json_text({"official_name": "查询产品列表"}, encoding="cp1252")
    assert json.loads(rendered) == {"official_name": "查询产品列表"}
    rendered.encode("cp1252")


def test_capabilities_lists_twenty_read_only_post_endpoints() -> None:
    result = runner.invoke(app, ["capabilities", "--format", "json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert len(payload["data"]["openapi"]) == 20
    assert {item["method"] for item in payload["data"]["openapi"]} == {"POST"}
    assert payload["data"]["webapi"]["business_endpoints"] == []
    assert payload["data"]["webapi"]["raw_request"] is False
    assert len(payload["data"]["catalog_resolution"]["relations"]) == 9


def test_capabilities_exposes_enum_labels_and_dynamic_identifiers() -> None:
    result = runner.invoke(app, ["capabilities", "--format", "json"])
    assert result.exit_code == 0, result.stdout
    endpoints = {
        endpoint["key"]: endpoint for endpoint in json.loads(result.stdout)["data"]["openapi"]
    }
    inventory_fields = {field["name"]: field for field in endpoints["product-inventory"]["fields"]}
    assert inventory_fields["productTypeList"]["enum_values"] == [
        {"value": 0, "label": "成品"},
        {"value": 1, "label": "包材"},
        {"value": 2, "label": "组合产品"},
        {"value": 3, "label": "半成品"},
    ]
    assert inventory_fields["warehouseIds"]["dynamic_identifier"] is True
    assert inventory_fields["warehouseIds"]["enum_values"] == []
    profit_fields = {field["name"]: field for field in endpoints["profit-analysis-v2"]["fields"]}
    assert profit_fields["platformCodes"]["enum_status"] == "official_not_published"
    assert profit_fields["platformCodes"]["default"] == ["AMAZON"]
    sales_pagination = endpoints["sales-performance"]["pagination"]
    assert sales_pagination["official_max_page_size"] is None
    assert sales_pagination["official_recommended_page_size"] == 200
    assert sales_pagination["runtime_min_page_size"] == 10
    assert sales_pagination["runtime_max_page_size"] == 1000
    assert sales_pagination["default_page_size"] == 200
    assert sales_pagination["default_max_pages"] == 100
    assert sales_pagination["runtime_verified"] is True
    assert sales_pagination["supports_auto_pagination"] is True
    traffic_pagination = endpoints["asin-traffic-data"]["pagination"]
    assert traffic_pagination["official_max_page_size"] == 100
    assert traffic_pagination["runtime_max_page_size"] == 1000
    assert traffic_pagination["default_page_size"] == 500


def test_cli_help_shows_registered_enum_values() -> None:
    cases = (
        (["openapi", "product", "list", "--help"], ("0=", "正常", "1=", "停用")),
        (["openapi", "inventory", "product", "--help"], ("3=", "半成品")),
        (["openapi", "statistics", "sales-performance", "--help"], ("seller_sku=", "msku")),
        (["openapi", "customer", "review", "--help"], ("contactBuyer=", "亚马逊")),
        (["openapi", "customer", "buyer-voice", "--help"], ("Verypoor=", "极差")),
        (["openapi", "finance", "profit-analysis-v2", "--help"], ("3=", "混合成本")),
        (
            ["openapi", "statistics", "listing-performance", "--help"],
            ("seller_sku=", "MSKU维度"),
        ),
        (
            ["openapi", "statistics", "asin-traffic-statistics", "--help"],
            ("month=", "月", "YUAN=", "原币种", "ZAR=", "南非兰特"),
        ),
        (
            ["openapi", "catalog", "warehouses", "list", "--help"],
            ("enable=", "启用", "OZON_FBO=", "Ozon"),
        ),
        (
            ["openapi", "catalog", "brands", "list", "--help"],
            ("Active=", "启用", "Inactive=", "停用"),
        ),
    )
    for command, expected_parts in cases:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.stdout
        normalized = re.sub(r"\s+", " ", result.stdout)
        assert all(part in normalized for part in expected_parts)

    profit_help = runner.invoke(app, ["openapi", "finance", "profit-analysis-v2", "--help"])
    assert "official default:" in profit_help.stdout
    assert "AMAZON" in profit_help.stdout


def test_invalid_enum_returns_stable_json_without_network(monkeypatch: object) -> None:
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands,
        "openapi_service",
        lambda profile: ValidatingOpenApiService(),
    )
    result = runner.invoke(
        app,
        ["openapi", "inventory", "product", "--product-state", "9"],
    )
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error_code"] == "GERPGO_VALIDATION_ERROR"
    assert payload["data"]["field"] == "productState"
    assert payload["data"]["allowed_values"] == [
        {"value": 0, "label": "正常"},
        {"value": 1, "label": "停用"},
    ]


def test_all_twelve_cli_queries_accept_minimal_registered_payloads(monkeypatch: object) -> None:
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands,
        "openapi_service",
        lambda profile: ValidatingOpenApiService(),
    )
    commands = {
        "product-list": ["openapi", "product", "list", "--sku", "SKU-DEMO-001"],
        "product-inventory": [
            "openapi",
            "inventory",
            "product",
            "--sku",
            "SKU-DEMO-001",
        ],
        "sales-performance": [
            "openapi",
            "statistics",
            "sales-performance",
            "--group-by-type",
            "seller_sku",
            "--currency",
            "YUAN",
            "--begin-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
        ],
        "search-term-performance": [
            "openapi",
            "ads",
            "search-term-performance",
            "--market-id",
            "100001",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
        ],
        "review": ["openapi", "customer", "review", "--asin", "ASIN-DEMO-001"],
        "buyer-voice": [
            "openapi",
            "customer",
            "buyer-voice",
            "--asin",
            "ASIN-DEMO-001",
            "--pcx-health",
            "Good",
        ],
        "profit-analysis-v2": [
            "openapi",
            "finance",
            "profit-analysis-v2",
            "--query-type",
            "sku",
            "--cost-values",
            "0",
            "--currency",
            "YUAN",
            "--date-type",
            "0",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
            "--sku",
            "SKU-DEMO-001",
        ],
        "keyword-performance": [
            "openapi",
            "ads",
            "keyword-performance",
            "--market-id",
            "100001",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
        ],
        "product-performance": [
            "openapi",
            "statistics",
            "product-performance",
            "--currency",
            "YUAN",
            "--begin-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
        ],
        "listing-performance": [
            "openapi",
            "statistics",
            "listing-performance",
            "--group-by-type",
            "asin",
            "--currency",
            "YUAN",
            "--begin-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
            "--no-show-total",
            "--asin",
            "ASIN-DEMO-001",
        ],
        "asin-traffic-statistics": [
            "openapi",
            "statistics",
            "asin-traffic-statistics",
            "--currency",
            "YUAN",
            "--begin-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
            "--view-type",
            "day",
            "--market-id",
            "100001",
        ],
        "asin-traffic-data": [
            "openapi",
            "statistics",
            "asin-traffic-data",
            "--currency",
            "YUAN",
            "--begin-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
            "--market-id",
            "100001",
        ],
    }
    for endpoint, command in commands.items():
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{endpoint}: {result.stdout}"
        assert json.loads(result.stdout)["data"]["endpoint"] == endpoint


def test_statistical_cli_defaults_come_from_sdk_pagination_contract(
    monkeypatch: object,
) -> None:
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands, "openapi_service", lambda profile: PaginationOpenApiService()
    )
    cases = (
        (
            [
                "openapi",
                "statistics",
                "sales-performance",
                "--group-by-type",
                "seller_sku",
                "--currency",
                "YUAN",
                "--begin-date",
                "2026-01-01",
                "--end-date",
                "2026-01-01",
            ],
            200,
        ),
        (
            [
                "openapi",
                "statistics",
                "product-performance",
                "--currency",
                "YUAN",
                "--begin-date",
                "2026-01-01",
                "--end-date",
                "2026-01-01",
            ],
            100,
        ),
        (
            [
                "openapi",
                "statistics",
                "listing-performance",
                "--group-by-type",
                "asin",
                "--currency",
                "YUAN",
                "--begin-date",
                "2026-01-01",
                "--end-date",
                "2026-01-01",
                "--no-show-total",
            ],
            100,
        ),
        (
            [
                "openapi",
                "statistics",
                "asin-traffic-statistics",
                "--currency",
                "YUAN",
                "--begin-date",
                "2026-01-01",
                "--end-date",
                "2026-01-01",
                "--view-type",
                "day",
            ],
            500,
        ),
        (
            [
                "openapi",
                "statistics",
                "asin-traffic-data",
                "--currency",
                "YUAN",
                "--begin-date",
                "2026-01-01",
                "--end-date",
                "2026-01-01",
            ],
            500,
        ),
    )
    for command, expected_page_size in cases:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)["data"]
        assert data["payload"]["pagesize"] == expected_page_size
        assert data["options"] == {"all_pages": False, "max_pages": 100}


def test_statistical_cli_help_describes_runtime_range_and_full_pagination() -> None:
    cases = (
        ("product-performance", "100"),
        ("asin-traffic-data", "500"),
    )
    for command, default_page_size in cases:
        result = runner.invoke(
            app,
            ["openapi", "statistics", command, "--help"],
        )
        assert result.exit_code == 0, result.stdout
        normalized = " ".join(result.stdout.split())
        assert "--page-size" in normalized
        assert "10<=x<=1000" in normalized
        assert f"[default: {default_page_size}]" in normalized
        assert "--all-pages" in normalized
        assert "can take a long time" in normalized
        assert "--max-pages" in normalized
        assert "[default: 100]" in normalized


def test_full_query_cli_uses_default_max_pages_100(monkeypatch: object) -> None:
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands, "openapi_service", lambda profile: PaginationOpenApiService()
    )
    result = runner.invoke(
        app,
        ["openapi", "inventory", "product", "--all-pages"],
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)["data"]
    assert data["payload"]["pagesize"] == 100
    assert data["options"] == {"all_pages": True, "max_pages": 100}


def test_full_query_page_limit_returns_stable_nonzero_json(monkeypatch: object) -> None:
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands, "openapi_service", lambda profile: PageLimitOpenApiService()
    )
    result = runner.invoke(
        app,
        [
            "openapi",
            "statistics",
            "asin-traffic-data",
            "--currency",
            "YUAN",
            "--begin-date",
            "2026-01-01",
            "--end-date",
            "2026-01-01",
            "--all-pages",
        ],
    )
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error_code"] == "GERPGO_PAGE_LIMIT_EXCEEDED"
    assert payload["data"]["estimated_pages"] == 300
    assert payload["data"]["estimated_seconds"] == 17940


def test_business_command_resolves_names_to_official_payload_identifiers(
    monkeypatch: object,
) -> None:
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands, "openapi_service", lambda profile: PayloadOpenApiService()
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands,
        "catalog_resolver_for_service",
        lambda service: SyntheticCatalogResolver(),
    )

    result = runner.invoke(
        app,
        [
            "openapi",
            "inventory",
            "product",
            "--warehouse-name",
            "示例仓",
            "--product-manager-name",
            "示例负责人",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["data"]["payload"]
    assert payload["warehouseIds"] == [200001]
    assert payload["productManagerAccountIdList"] == [300001]
    assert "warehouseName" not in payload


def test_business_command_rejects_id_and_name_conflict(monkeypatch: object) -> None:
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands, "openapi_service", lambda profile: PayloadOpenApiService()
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands,
        "catalog_resolver_for_service",
        lambda service: SyntheticCatalogResolver(),
    )
    result = runner.invoke(
        app,
        [
            "openapi",
            "inventory",
            "product",
            "--warehouse-id",
            "200001",
            "--warehouse-name",
            "示例仓",
        ],
    )
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["error_code"] == "GERPGO_VALIDATION_ERROR"


def test_skill_description_contains_chinese_gerpgo_triggers() -> None:
    skill_text = Path("skills/gerpgo-erp/SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill_text.split("---", 2)[1]
    for trigger in ("积加", "积加 ERP", "积加 CLI", "gerpgo-erp", "Gerpgo", "gerpgo-cli"):
        assert trigger in frontmatter


def test_openapi_profile_precedence(monkeypatch: object) -> None:
    monkeypatch.delenv("GERPGO_PROFILE", raising=False)  # type: ignore[attr-defined]
    monkeypatch.setattr(  # type: ignore[attr-defined]
        openapi_commands,
        "openapi_service",
        lambda profile: RecordingOpenApiService(profile),
    )
    cases = (
        ([], {}, "prod"),
        ([], {"GERPGO_PROFILE": "test"}, "test"),
        (["--profile", "qa"], {"GERPGO_PROFILE": "test"}, "qa"),
    )
    for profile_args, environment, expected in cases:
        result = runner.invoke(
            app,
            ["openapi", "inventory", "product", *profile_args],
            env=environment,
        )
        assert result.exit_code == 0, result.stdout
        assert json.loads(result.stdout)["data"]["profile"] == expected


def test_catalog_profile_precedence(monkeypatch: object) -> None:
    monkeypatch.delenv("GERPGO_PROFILE", raising=False)  # type: ignore[attr-defined]
    monkeypatch.setattr(  # type: ignore[attr-defined]
        catalog_commands,
        "catalog_service",
        lambda profile: RecordingCatalogService(profile),
    )
    cases = (
        ([], {}, "prod"),
        ([], {"GERPGO_PROFILE": "test"}, "test"),
        (["--profile", "qa"], {"GERPGO_PROFILE": "test"}, "qa"),
    )
    for profile_args, environment, expected in cases:
        result = runner.invoke(
            app,
            ["openapi", "catalog", "brands", "list", *profile_args],
            env=environment,
        )
        assert result.exit_code == 0, result.stdout
        assert json.loads(result.stdout)["data"][0]["code"] == expected


def test_web_auth_commands_default_to_prod(monkeypatch: object) -> None:
    monkeypatch.delenv("GERPGO_PROFILE", raising=False)  # type: ignore[attr-defined]
    monkeypatch.setattr(  # type: ignore[attr-defined]
        web_auth_commands,
        "web_auth_service",
        lambda profile: (RecordingWebAuthService(), "DEMO_USER", "DEMO_PASSWORD"),
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        web_auth_commands, "ProfileStore", RecordingProfileStore
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        web_auth_commands, "SecretStore", lambda: object()
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        web_auth_commands, "WebSessionStore", RecordingWebSessionStore
    )

    for command in ("login", "status", "logout"):
        result = runner.invoke(app, ["web", "auth", command])
        assert result.exit_code == 0, result.stdout
        assert json.loads(result.stdout)["data"]["profile"] == "prod"


def test_missing_default_prod_returns_stable_json_error(
    tmp_path: Path, monkeypatch: object
) -> None:
    monkeypatch.setenv("GERPGO_CONFIG_DIR", str(tmp_path))  # type: ignore[attr-defined]
    monkeypatch.delenv("GERPGO_PROFILE", raising=False)  # type: ignore[attr-defined]
    result = runner.invoke(app, ["openapi", "inventory", "product"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error_code"] == "GERPGO_CONFIG_MISSING"
    assert "Profile 'prod' does not exist" in payload["message"]
    assert "gerpgo-cli profile init prod" in payload["message"]


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
    assert 'version: "0.2.0"' in skill_file.read_text(encoding="utf-8")

    result = runner.invoke(app, ["skill", "update", "--target-root", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert not list(tmp_path.glob(".gerpgo-erp.*"))
