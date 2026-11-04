from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest
from rich.text import Text
from typer.testing import CliRunner

from gerpgo_cli.commands import expanded
from gerpgo_cli.main import app
from gerpgo_sdk.common.errors import ValidationError
from gerpgo_sdk.common.redaction import BusinessResponse, protect_credentials
from gerpgo_sdk.openapi import ENDPOINTS, OpenApiService, get_endpoint
from gerpgo_sdk.openapi.expanded import WRITE_IDS, catalog_documents


def test_expanded_registry_contains_only_reviewed_reads_and_all_fields() -> None:
    documents = {doc["id"]: doc for doc in catalog_documents()}
    assert len(documents) == 288
    routes = []
    for spec in ENDPOINTS.values():
        assert spec.document_id not in WRITE_IDS | {596}
        if spec.cli_route is None:
            continue
        routes.append(spec.cli_route)
        doc = documents[spec.document_id]
        assert spec.path == doc["path"]
        assert spec.method == "POST"
        assert set(spec.fields) == {field["name"] for field in doc["request"]}
        for item in doc["request"]:
            field = spec.fields[item["name"]]
            assert (field.type_name, field.required, field.description) == (
                item["type"],
                item["must"],
                item["description"],
            )
        assert spec.minimum_interval_seconds > 0
        assert spec.default_max_pages == 100
    assert len(routes) == len(set(routes))
    assert len(routes) > 100
    for document_id in (1020, 1021, 4645, 6025, 2453, 4696, 4443, 102, 104, 101):
        assert document_id in {spec.document_id for spec in ENDPOINTS.values()}


def test_nested_object_array_fields_are_validated() -> None:
    spec = get_endpoint("logistics-sta-shipment-box-info-query")
    spec.validate_payload({"shipmentItemQueryDTOS": [{"shipmentId": "SHIPMENT-DEMO"}]})
    with pytest.raises(ValidationError, match="Missing required"):
        spec.validate_payload({"shipmentItemQueryDTOS": [{}]})
    with pytest.raises(ValidationError, match="Unsupported"):
        spec.validate_payload({"shipmentItemQueryDTOS": [{"arbitrary": "DEMO"}]})


def test_official_transfer_enums_are_enforced() -> None:
    spec = get_endpoint("inventory-transfer-page")
    spec.validate_payload({"page": 1, "pagesize": 10, "status": "draft", "pick": 0})
    with pytest.raises(ValidationError, match="Allowed values"):
        spec.validate_payload({"page": 1, "pagesize": 10, "status": "NOT-OFFICIAL"})


def test_raw_output_preserves_unknown_business_fields_and_protects_credentials() -> None:
    data = {
        "code": 200,
        "messages": ["DEMO"],
        "traceId": "DEMO_TRACE_ID",
        "futureField": {
            "username": "示例负责人",
            "marketId": "100001",
            "significance": "DEMO",
            "accessToken": "DEMO_SYNTHETIC_TOKEN",
        },
        "data": {"sku": "000001", "unknown": [1, 2]},
        "password": "DEMO_PASSWORD",
    }
    protected = protect_credentials(data)
    assert protected["futureField"]["username"] == "示例负责人"
    assert protected["futureField"]["marketId"] == "100001"
    assert protected["futureField"]["accessToken"] == "[REDACTED]"
    assert protected["password"] == "[REDACTED]"
    assert protected["data"] == data["data"]
    assert protected["traceId"] == data["traceId"]


class RawPages:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def execute(self, spec: Any, payload: Any, *, response_mode: str = "data") -> Any:
        self.calls.append(dict(payload))
        raw = self.responses.pop(0)
        return raw if response_mode == "raw" else raw["data"]


def test_raw_all_pages_keeps_each_envelope_without_duplicate_rows() -> None:
    client = RawPages(
        [
            {"code": 200, "data": {"rows": [{"sku": "0001"}], "total": 2}, "unknown": 1},
            {"code": 200, "data": {"rows": [{"sku": "0002"}], "total": 2}, "unknown": 2},
        ]
    )
    result = OpenApiService(client).query(  # type: ignore[arg-type]
        get_endpoint("product-inventory"),
        {"page": 1, "pagesize": 1},
        all_pages=True,
        response_mode="raw",
    )
    assert isinstance(result, BusinessResponse)
    assert "rows" not in result
    assert [page["unknown"] for page in result["pages"]] == [1, 2]
    assert result["pagination"]["complete"] is True


def test_records_pagination_does_not_assume_rows() -> None:
    client = RawPages(
        [
            {"data": {"records": [{"value": 1}], "total": 2}},
            {"data": {"records": [{"value": 2}], "total": 2}},
        ]
    )
    spec = replace(get_endpoint("product-inventory"), response_rows_key="records")
    result = OpenApiService(client).query(  # type: ignore[arg-type]
        spec,
        {"page": 1, "pagesize": 1},
        all_pages=True,
    )
    assert len(result["rows"]) == 2
    assert result["pagination"]["complete"] is True


def test_cursor_pagination_uses_documented_extobj() -> None:
    client = RawPages(
        [
            {"code": 200, "data": [{"id": "DEMO_A"}], "extObj": 100001},
            {"code": 200, "data": [], "extObj": None},
        ]
    )
    result = OpenApiService(client).query(  # type: ignore[arg-type]
        get_endpoint("ads-deal-query"),
        {"marketId": 100001, "count": 1, "startDate": "2026-01-01", "endDate": "2026-01-01"},
        all_pages=True,
    )
    assert client.calls[1]["nextId"] == 100001
    assert result["pagination"]["pages_fetched"] == 2
    assert result["pagination"]["complete"] is True


def test_new_cli_forwards_flags_and_input_as_registered_fields(monkeypatch: Any) -> None:
    calls = []

    class Service:
        def query(self, spec: Any, payload: Any, **options: Any) -> Any:
            spec.validate_payload(payload)
            calls.append((spec.key, payload, options))
            return BusinessResponse(code=200, data={"username": "示例负责人", "newField": True})

    monkeypatch.setattr(expanded, "openapi_service", lambda profile: Service())
    result = CliRunner().invoke(
        app,
        [
            "openapi",
            "inventory",
            "transfer-page",
            "--status",
            "draft",
            "--input",
            "-",
            "--response",
            "raw",
        ],
        input='{"codeList":["TF-DEMO"],"pick":0}',
    )
    assert result.exit_code == 0, result.stdout
    assert calls[0][1]["codeList"] == ["TF-DEMO"]
    assert calls[0][1]["pick"] == 0
    assert calls[0][2]["response_mode"] == "raw"
    assert json.loads(result.stdout)["data"]["data"]["username"] == "示例负责人"


def test_all_new_commands_have_help() -> None:
    runner = CliRunner()
    for spec in ENDPOINTS.values():
        if spec.cli_route:
            result = runner.invoke(app, ["openapi", *spec.cli_route, "--help"])
            assert result.exit_code == 0, (spec.key, result.stdout)
            plain_help = Text.from_ansi(result.stdout).plain
            assert "--input" in plain_help
            assert "--response" in plain_help


def test_every_registered_enum_accepts_official_values_and_rejects_others() -> None:
    def verify(spec: Any, name: str, field: Any) -> None:
        for entry in field.enum_values:
            value = [entry.value] if field.type_name.startswith("array") else entry.value
            spec._validate_field(name, value, field)
        if field.enum_values:
            invalid = (
                987654321
                if field.type_name
                in {"int", "long", "short", "number", "array<int>", "array<long>"}
                else "NOT_OFFICIAL"
            )
            value = [invalid] if field.type_name.startswith("array") else invalid
            with pytest.raises(ValidationError):
                spec._validate_field(name, value, field)
        for child_name, child in field.children:
            verify(spec, f"{name}.{child_name}", child)

    for spec in ENDPOINTS.values():
        for name, field in spec.fields.items():
            verify(spec, name, field)


def test_current_size_pagination_uses_the_registered_request_fields() -> None:
    client = RawPages(
        [
            {"data": {"records": [{"value": 1}], "total": 2}},
            {"data": {"records": [{"value": 2}], "total": 2}},
        ]
    )
    result = OpenApiService(client).query(  # type: ignore[arg-type]
        get_endpoint("multiplatform-walmart-order-page"),
        {"current": 1, "size": 1},
        all_pages=True,
    )
    assert [call["current"] for call in client.calls] == [1, 2]
    assert result["pagination"]["rows_fetched"] == 2


def test_nested_pagination_cli_supplies_defaults_without_overriding_input(monkeypatch: Any) -> None:
    captured = []

    class Service:
        def query(self, spec: Any, payload: Any, **options: Any) -> Any:
            spec.validate_payload(payload)
            captured.append(payload)
            return {}

    monkeypatch.setattr(expanded, "openapi_service", lambda profile: Service())
    result = CliRunner().invoke(
        app,
        ["openapi", "procurement", "procure-page", "--input", "-"],
        input='{"pageInfo":{"page":2,"pagesize":10}}',
    )
    assert result.exit_code == 0, result.stdout
    assert captured[0]["pageInfo"] == {"page": 2, "pagesize": 10}


def test_direct_cli_pagination_defaults_do_not_override_input(monkeypatch: Any) -> None:
    captured = []

    class Service:
        def query(self, spec: Any, payload: Any, **options: Any) -> Any:
            spec.validate_payload(payload)
            captured.append(payload)
            return {}

    monkeypatch.setattr(expanded, "openapi_service", lambda profile: Service())
    result = CliRunner().invoke(
        app,
        ["openapi", "inventory", "transfer-page", "--input", "-"],
        input='{"page":2,"pagesize":10}',
    )
    assert result.exit_code == 0, result.stdout
    assert captured[0]["page"] == 2
    assert captured[0]["pagesize"] == 10
