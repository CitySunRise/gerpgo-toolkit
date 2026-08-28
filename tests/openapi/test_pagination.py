from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from gerpgo_sdk.common.errors import PageLimitExceededError, ValidationError
from gerpgo_sdk.openapi import ENDPOINTS, OpenApiService, get_endpoint


class PageClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def execute(self, spec: Any, payload: dict[str, Any] | None) -> dict[str, Any]:
        spec.validate_payload(payload)
        assert payload is not None
        self.calls.append(deepcopy(payload))
        return self.responses.pop(0)


def test_all_business_endpoints_define_default_page_sizes() -> None:
    business = [spec for spec in ENDPOINTS.values() if spec.endpoint_group == "business"]
    assert len(business) == 12
    assert all(spec.default_page_size is not None for spec in business)
    assert {spec.key: spec.default_page_size for spec in business} == {
        "product-list": 100,
        "product-inventory": 100,
        "sales-performance": 200,
        "search-term-performance": 100,
        "review": 100,
        "buyer-voice": 100,
        "profit-analysis-v2": 100,
        "keyword-performance": 100,
        "product-performance": 100,
        "listing-performance": 100,
        "asin-traffic-statistics": 500,
        "asin-traffic-data": 500,
    }
    assert all(spec.default_max_pages == 100 for spec in business)


def test_runtime_statistical_page_size_range_is_validated_before_request() -> None:
    keys = {
        "sales-performance",
        "product-performance",
        "listing-performance",
        "asin-traffic-statistics",
        "asin-traffic-data",
    }
    for key in keys:
        spec = ENDPOINTS[key]
        assert spec.runtime_verified is True
        assert spec.runtime_min_page_size == 10
        assert spec.runtime_max_page_size == 1000
        payload = _minimal_statistical_payload(key, page_size=9)
        with pytest.raises(ValidationError, match="at least 10"):
            spec.validate_payload(payload)
        payload["pagesize"] = 10
        spec.validate_payload(payload)


def test_full_query_uses_total_and_merges_every_page() -> None:
    client = PageClient(
        [
            {"rows": [{"row": 1}, {"row": 2}], "total": 5},
            {"rows": [{"row": 3}, {"row": 4}], "total": 5},
            {"rows": [{"row": 5}], "total": 5},
        ]
    )
    service = OpenApiService(client)  # type: ignore[arg-type]

    result = service.query(
        get_endpoint("product-inventory"),
        {"page": 1, "pagesize": 2},
        all_pages=True,
    )

    assert [row["row"] for row in result["rows"]] == [1, 2, 3, 4, 5]
    assert [call["page"] for call in client.calls] == [1, 2, 3]
    assert result["pagination"] == {
        "total_records": 5,
        "page_size": 2,
        "estimated_pages": 3,
        "pages_fetched": 3,
        "rows_fetched": 5,
        "estimated_seconds": 1,
        "complete": True,
        "truncated": False,
    }


def test_known_total_over_default_limit_stops_after_first_page() -> None:
    client = PageClient([{"rows": [{}] * 500, "total": 150000}])
    service = OpenApiService(client)  # type: ignore[arg-type]

    with pytest.raises(PageLimitExceededError) as captured:
        service.query(
            get_endpoint("asin-traffic-data"),
            _minimal_statistical_payload("asin-traffic-data", page_size=500),
            all_pages=True,
        )

    assert len(client.calls) == 1
    assert captured.value.code.value == "GERPGO_PAGE_LIMIT_EXCEEDED"
    assert captured.value.details == {
        "total_records": 150000,
        "page_size": 500,
        "estimated_pages": 300,
        "max_pages": 100,
        "estimated_seconds": 17940,
    }


def test_missing_total_finishes_on_empty_page() -> None:
    client = PageClient(
        [
            {"rows": [{"row": 1}, {"row": 2}]},
            {"rows": [{"row": 3}, {"row": 4}]},
            {"rows": []},
        ]
    )
    result = OpenApiService(client).query(  # type: ignore[arg-type]
        get_endpoint("product-inventory"),
        {"page": 1, "pagesize": 2},
        all_pages=True,
        max_pages=3,
    )

    assert len(result["rows"]) == 4
    assert result["pagination"]["total_records"] == 4
    assert result["pagination"]["estimated_pages"] is None
    assert result["pagination"]["complete"] is True
    assert result["pagination"]["truncated"] is False


def test_missing_total_at_limit_returns_nonzero_error_instead_of_truncation() -> None:
    client = PageClient(
        [
            {"rows": [{"row": 1}, {"row": 2}]},
            {"rows": [{"row": 3}, {"row": 4}]},
        ]
    )
    service = OpenApiService(client)  # type: ignore[arg-type]

    with pytest.raises(PageLimitExceededError) as captured:
        service.query(
            get_endpoint("product-inventory"),
            {"page": 1, "pagesize": 2},
            all_pages=True,
            max_pages=2,
        )

    assert len(client.calls) == 2
    assert captured.value.details["total_records"] is None
    assert captured.value.details["max_pages"] == 2


def test_known_total_row_mismatch_is_not_reported_as_complete() -> None:
    client = PageClient(
        [
            {"rows": [{"row": 1}, {"row": 2}], "total": 3},
            {"rows": [], "total": 3},
        ]
    )
    with pytest.raises(ValidationError, match="did not match"):
        OpenApiService(client).query(  # type: ignore[arg-type]
            get_endpoint("product-inventory"),
            {"page": 1, "pagesize": 2},
            all_pages=True,
        )


def _minimal_statistical_payload(key: str, *, page_size: int) -> dict[str, Any]:
    common = {"page": 1, "pagesize": page_size}
    if key == "sales-performance":
        return {
            **common,
            "groupByType": "seller_sku",
            "showCurrencyType": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
        }
    if key == "product-performance":
        return {
            **common,
            "showCurrencyType": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
        }
    if key == "listing-performance":
        return {
            **common,
            "groupByType": "asin",
            "showCurrencyType": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
            "isShowTotal": False,
        }
    if key == "asin-traffic-statistics":
        return {
            **common,
            "currency": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
            "viewType": "day",
        }
    if key == "asin-traffic-data":
        return {
            **common,
            "currency": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
        }
    raise AssertionError(key)
