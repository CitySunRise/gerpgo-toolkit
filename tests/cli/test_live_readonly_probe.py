"""Offline checks for the bounded live-verification harness; no ERP connections."""

from datetime import date
from pathlib import Path
from runpy import run_path
from types import SimpleNamespace

import pytest

from gerpgo_sdk.openapi import ENDPOINTS

_probe_module = run_path(
    str(Path(__file__).resolve().parents[2] / "scripts/validate_live_readonly.py")
)
MissingCondition = _probe_module["MissingCondition"]
Probe = _probe_module["Probe"]


def offline_probe(tmp_path: Path) -> Probe:
    probe = Probe.__new__(Probe)
    probe.day = date(2026, 1, 2).isoformat()
    probe.month = "2026-01"
    probe.output = tmp_path / "report.json"
    probe.data = {}
    probe.records = {}
    probe.by_id = {s.document_id: s for s in ENDPOINTS.values()}
    probe.diagnostic = {}
    return probe


def test_product_probe_uses_one_registered_pagination_shape(tmp_path: Path) -> None:
    probe = offline_probe(tmp_path)
    payload, _ = probe.payload(53)
    assert payload["page"] == 1
    assert "pageInfo" not in payload
    probe.by_id[53].validate_payload(payload)


@pytest.mark.parametrize("document_id", [2658, 3188, 6344])
def test_monthly_probe_uses_smallest_documented_period(tmp_path: Path, document_id: int) -> None:
    probe = offline_probe(tmp_path)
    probe.data[153] = {"marketId": "42"}
    payload, _ = probe.payload(document_id)
    assert any(value == "2026-01" or value == ["2026-01"] for value in payload.values())
    probe.by_id[document_id].validate_payload(payload)


def test_missing_correlated_ledger_sample_blocks_without_request(tmp_path: Path) -> None:
    probe = offline_probe(tmp_path)
    with pytest.raises(MissingCondition, match="correlated_ledger"):
        probe.payload(1399)


def test_public_error_classification_never_saves_upstream_message(tmp_path: Path) -> None:
    probe = offline_probe(tmp_path)
    response = SimpleNamespace(
        url="https://example.invalid/registered-endpoint",
        status_code=400,
        json=lambda: {"code": 40403, "messages": ["EXAMPLE_PRIVATE_MESSAGE"]},
    )
    probe.observe(response)
    assert probe.diagnostic == {
        "http_status": 400,
        "upstream_code": 40403,
        "reason": "permission_denied",
    }
    probe.records[53] = {"document_id": 53, "status": "failed", **probe.diagnostic}
    probe.data[53] = {"sku": "EXAMPLE_BUSINESS_VALUE", "traceId": "EXAMPLE_TRACE"}
    probe.save()
    report = probe.output.read_text()
    assert "EXAMPLE_PRIVATE_MESSAGE" not in report
    assert "EXAMPLE_BUSINESS_VALUE" not in report
    assert "EXAMPLE_TRACE" not in report


def test_delivery_detail_requires_observed_delivery_code(tmp_path: Path) -> None:
    probe = offline_probe(tmp_path)
    with pytest.raises(MissingCondition, match="source_document_1027"):
        probe.payload(1028)
    probe.data[1027] = {"rows": [{"code": "EXAMPLE_DELIVERY"}]}
    payload, _ = probe.payload(1028)
    assert payload["deliveryCodes"] == ["EXAMPLE_DELIVERY"]
