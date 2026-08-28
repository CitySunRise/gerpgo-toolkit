from __future__ import annotations

from pathlib import Path

from gerpgo_sdk.openapi import ENDPOINTS, FieldSpec

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
    "product-performance": "gerpgo-cli openapi statistics product-performance",
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
    "catalog-amazon-shop-warehouses": ("gerpgo-cli openapi catalog amazon-shops warehouses-by-id"),
}


def test_skill_maps_all_registered_endpoints_with_synthetic_examples() -> None:
    command_map = (SKILL_ROOT / "references/command-map.md").read_text(encoding="utf-8")
    parameters = (SKILL_ROOT / "references/endpoint-parameters.md").read_text(encoding="utf-8")
    assert set(COMMANDS) == set(ENDPOINTS)
    assert parameters.count("Synthetic minimum example:") == 20
    for command in COMMANDS.values():
        assert command in command_map
        assert command in parameters


def test_skill_enum_snapshot_is_checked_against_sdk_contract() -> None:
    parameters = (SKILL_ROOT / "references/endpoint-parameters.md").read_text(encoding="utf-8")

    def assert_enums(field: FieldSpec) -> None:
        for enum_value in field.enum_values:
            assert f"`{enum_value.value}`" in parameters
            if enum_value.label != "官方未提供中文含义":
                assert enum_value.label in parameters
        for _, child in field.children:
            assert_enums(child)

    for endpoint in ENDPOINTS.values():
        for field in endpoint.fields.values():
            assert_enums(field)
    assert "official document publishes these raw values but no Chinese label" in " ".join(
        parameters.split()
    )


def test_skill_explains_dynamic_identifiers_and_capabilities_precedence() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    parameters = (SKILL_ROOT / "references/endpoint-parameters.md").read_text(encoding="utf-8")
    safety = (SKILL_ROOT / "references/openapi-safety.md").read_text(encoding="utf-8")
    for text in (skill, parameters, safety):
        assert "gerpgo-cli capabilities --format json" in text
    assert "dynamic_identifier: true" in safety
    assert "official_not_published" in safety
    assert "platformCodes" in parameters
    assert "official document does not publish a complete enum" in " ".join(parameters.split())


def test_skill_routes_full_data_intent_through_cli_pagination() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    command_map = (SKILL_ROOT / "references/command-map.md").read_text(encoding="utf-8")
    parameters = (SKILL_ROOT / "references/endpoint-parameters.md").read_text(encoding="utf-8")
    safety = (SKILL_ROOT / "references/openapi-safety.md").read_text(encoding="utf-8")
    errors = (SKILL_ROOT / "references/errors.md").read_text(encoding="utf-8")
    combined = "\n".join((skill, command_map, parameters, safety))

    for intent in ("全部", "完整", "完整分析", "导出", "所有数据"):
        assert intent in combined
    assert "--all-pages --max-pages 100" in skill
    assert "pagination.complete=true" in skill
    assert "pagination.truncated=false" in skill
    assert "Never implement an AI-side page loop" in command_map
    assert "GERPGO_PAGE_LIMIT_EXCEEDED" in errors
