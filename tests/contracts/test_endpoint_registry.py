from __future__ import annotations

import pytest

from gerpgo_sdk.common.errors import ValidationError
from gerpgo_sdk.openapi import ENDPOINTS

EXPECTED = {
    "product-list": ("查询产品列表", 53, "/purchase/goods/product/page", 0.5),
    "product-inventory": ("查询产品库存", 15, "/purchase/store/inventory/page", 0.5),
    "sales-performance": ("销售表现", 3375, "/operation/sts/salesAnalysis/page", 5.0),
    "search-term-performance": (
        "搜索词表现",
        100,
        "/operation/ads/adsKeywordAnalytical/query",
        60.0,
    ),
    "review": ("Review", 1092, "/operation/crm/review/page", 1.0),
    "buyer-voice": ("买家之声列表", 1014, "/operation/crm/customerVoice/page", 1.0),
    "profit-analysis-v2": (
        "查询财务利润分析V2",
        2256,
        "/finance/sts/financialAnalysis/page/V2",
        10.0,
    ),
    "keyword-performance": (
        "关键词表现",
        99,
        "/operation/ads/adsKeywordAnalytical/page",
        60.0,
    ),
    "product-performance": (
        "产品表现",
        131,
        "/operation/sts/productAnalyzeMultiIndex/page",
        60.0,
    ),
    "listing-performance": (
        "商品表现",
        140,
        "/operation/sts/listingAnalyzeMultiIndex/page",
        5.0,
    ),
    "asin-traffic-statistics": ("流量统计-ASIN", 122, "/operation/sts/traffic/page", 60.0),
    "asin-traffic-data": (
        "流量数据-ASIN",
        1018,
        "/operation/sts/trafficAnalysis/page",
        60.0,
    ),
}


def test_registry_matches_official_contracts() -> None:
    assert set(ENDPOINTS) == set(EXPECTED)
    for key, (name, document_id, path, interval) in EXPECTED.items():
        spec = ENDPOINTS[key]
        assert spec.official_name == name
        assert spec.document_id == document_id
        assert spec.method == "POST"
        assert spec.path == path
        assert spec.minimum_interval_seconds == interval
        assert spec.read_only is True


def test_required_and_unknown_fields_are_rejected() -> None:
    spec = ENDPOINTS["asin-traffic-data"]
    with pytest.raises(ValidationError, match="Missing required fields"):
        spec.validate_payload({"page": 1, "pagesize": 10})
    with pytest.raises(ValidationError, match="Unsupported fields"):
        spec.validate_payload(
            {
                "currency": "USD",
                "beginDate": "2026-01-01",
                "endDate": "2026-01-02",
                "page": 1,
                "pagesize": 10,
                "rawUrl": "https://erp.example.invalid",
            }
        )


def test_sku_and_asin_fields_require_strings() -> None:
    spec = ENDPOINTS["product-inventory"]
    with pytest.raises(ValidationError, match="skuList"):
        spec.validate_payload({"page": 1, "pagesize": 20, "skuList": "SKU-DEMO-001"})
    with pytest.raises(ValidationError, match=r"skuList\[0\]"):
        spec.validate_payload({"page": 1, "pagesize": 20, "skuList": [10001]})


def test_product_pagination_modes_are_exclusive() -> None:
    spec = ENDPOINTS["product-list"]
    with pytest.raises(ValidationError, match="not both"):
        spec.validate_payload(
            {"page": 1, "pagesize": 100, "pageInfo": {"page": 1, "pagesize": 100}}
        )
    spec.validate_payload({"pageInfo": {"page": 1, "pagesize": 100}})
