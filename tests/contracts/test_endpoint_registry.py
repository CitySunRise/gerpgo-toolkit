from __future__ import annotations

import pytest

from gerpgo_sdk.common.errors import ValidationError
from gerpgo_sdk.openapi import CURRENCY_ENUM, ENDPOINTS

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
    "catalog-amazon-shops": ("查询亚马逊店铺信息", 153, "/middle/base/market/page", 1.0),
    "catalog-users": ("查询所有用户列表", 25, "/middle/base/allUser/list", 1.0),
    "catalog-warehouses": (
        "查询仓库信息列表",
        1035,
        "/purchase/store/multiTypeWarehouse/page",
        0.5,
    ),
    "catalog-brands": ("查询品牌资料", 1752, "/purchase/goods/brand/page", 0.5),
    "catalog-categories": ("查询品类信息", 54, "/purchase/goods/category/page", 0.5),
    "catalog-multiplatform-shops": (
        "查询多平台店铺信息",
        67,
        "/platform/multiplatform/multiShop/query",
        0.5,
    ),
    "catalog-amazon-shop-names": (
        "根据亚马逊店铺id查询店铺名称",
        1177,
        "/middle/base/marketNames/query",
        0.1,
    ),
    "catalog-amazon-shop-warehouses": (
        "根据亚马逊店铺id查询仓库信息",
        1179,
        "/middle/base/warehouseIds/query",
        1.0,
    ),
}

EXPECTED_FIELDS = {
    "product-list": {
        "brandList",
        "categoryList",
        "pageInfo",
        "page",
        "pagesize",
        "skuList",
        "platformMskuList",
        "mskuList",
        "state",
        "dateType",
        "startDate",
        "endDate",
    },
    "product-inventory": {
        "page",
        "pagesize",
        "productState",
        "productTypeList",
        "state",
        "warehouseIds",
        "productManagerAccountIdList",
        "sellingManagerIdList",
        "skuList",
        "asinList",
        "mskuList",
        "filterQuantity",
    },
    "sales-performance": {
        "groupByType",
        "viewType",
        "showCurrencyType",
        "beginDate",
        "endDate",
        "sku",
        "variationAsin",
        "productName",
        "asin",
        "msku",
        "page",
        "pagesize",
    },
    "search-term-performance": {"page", "pagesize", "marketId", "startDateData", "endDateData"},
    "review": {
        "page",
        "pagesize",
        "reviewIds",
        "createDateBegin",
        "createDateEnd",
        "updateDateBegin",
        "updateDateEnd",
        "reviewDateBegin",
        "reviewDateEnd",
        "marketIds",
        "states",
        "results",
        "orderIds",
        "nameMatchType",
        "asins",
    },
    "buyer-voice": {
        "pcxHealth",
        "marketIds",
        "productName",
        "skus",
        "mskus",
        "asins",
        "page",
        "pagesize",
    },
    "profit-analysis-v2": {
        "queryType",
        "costValues",
        "page",
        "pagesize",
        "currency",
        "dateType",
        "monthDate",
        "startDate",
        "endDate",
        "marketIds",
        "categoryIds",
        "brands",
        "decimalPlaces",
        "footerExpandDetails",
        "platformCodes",
        "queryMskuList",
        "skuList",
        "asinList",
    },
    "keyword-performance": {"page", "pagesize", "marketId", "startDateData", "endDateData"},
    "product-performance": {"showCurrencyType", "beginDate", "endDate", "page", "pagesize"},
    "listing-performance": {
        "groupByType",
        "showCurrencyType",
        "beginDate",
        "endDate",
        "isShowTotal",
        "page",
        "pagesize",
        "marketList",
        "sku",
        "asin",
        "asinList",
        "msku",
        "mskuList",
    },
    "asin-traffic-statistics": {
        "marketList",
        "currency",
        "beginDate",
        "endDate",
        "page",
        "pagesize",
        "viewType",
    },
    "asin-traffic-data": {"marketList", "currency", "beginDate", "endDate", "page", "pagesize"},
    "catalog-amazon-shops": {"page", "pagesize", "condition"},
    "catalog-users": set(),
    "catalog-warehouses": {"model", "page", "pagesize"},
    "catalog-brands": {"code", "name", "state", "page", "pagesize"},
    "catalog-categories": {"state", "page", "pagesize", "valueList"},
    "catalog-multiplatform-shops": set(),
    "catalog-amazon-shop-names": {"markerIds"},
    "catalog-amazon-shop-warehouses": {"marketIdList"},
}

EXPECTED_CURRENCIES = {
    "YUAN": "原币种",
    "USD": "美元",
    "JPY": "日元",
    "GBP": "英镑",
    "EUR": "欧元",
    "CAD": "加元",
    "MXN": "墨西哥比索",
    "AUD": "澳大利亚元",
    "INR": "印度卢比",
    "CNY": "人民币",
    "AED": "阿联酋迪拉姆",
    "SGD": "新加坡元",
    "SAR": "沙特里亚尔",
    "BRL": "巴西雷亚尔",
    "SEK": "瑞典克朗",
    "TRY": "土耳其里拉",
    "PLN": "波兰兹罗提",
    "HKD": "港币",
    "ANG": "荷兰盾",
    "CHF": "瑞士法郎",
    "RON": "罗马尼亚新列伊",
    "MYR": "林吉特",
    "VND": "越南盾",
    "PHP": "菲律宾比索",
    "THB": "泰国铢",
    "IDR": "印尼卢比",
    "COP": "哥伦比亚比索",
    "CLP": "智利比索",
    "TWD": "新台币",
    "KRW": "韩国元",
    "CNH": "离岸人民币",
    "NGN": "尼日利亚奈拉",
    "BYN": "白俄罗斯卢布",
    "KZT": "哈萨克斯坦坚戈",
    "RUB": "俄罗斯卢布",
    "BGN": "保加利亚列弗",
    "HUF": "匈牙利福林",
    "EGP": "埃及镑",
    "ZAR": "南非兰特",
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
        assert set(spec.fields) == EXPECTED_FIELDS[key]
        for field in spec.fields.values():
            assert field.type_name
            assert field.description


def test_all_official_currency_values_and_labels_are_registered() -> None:
    assert {str(item.value): item.label for item in CURRENCY_ENUM} == EXPECTED_CURRENCIES


def test_documented_enum_values_and_labels_are_complete() -> None:
    expected = {
        ("product-list", "state"): {0: "正常", 1: "停用"},
        ("product-list", "dateType"): {0: "创建时间", 1: "更新时间"},
        ("product-inventory", "productState"): {0: "正常", 1: "停用"},
        ("product-inventory", "productTypeList"): {
            0: "成品",
            1: "包材",
            2: "组合产品",
            3: "半成品",
        },
        ("product-inventory", "state"): {0: "异常", 1: "正常"},
        ("sales-performance", "groupByType"): {
            "seller_sku": "msku",
            "asin": "asin",
            "variation_asin": "父asin",
            "sku": "sku",
            "spu": "spu",
            "country": "国家",
            "market": "店铺",
            "date": "日期",
        },
        ("sales-performance", "viewType"): {"DAY": "日", "WEEK": "周", "MONTH": "月"},
        ("review", "states"): {0: "未处理", 1: "处理中", 2: "已完成", 3: "无"},
        ("review", "results"): {
            0: "无",
            1: "无变化-客户不同意",
            3: "已删除",
            4: "无变化-邮件无回复",
            5: "分数变化-调高",
            6: "分数变化-调低",
        },
        ("review", "nameMatchType"): {
            "fuzzyMatch": "模糊匹配",
            "exact": "精准匹配",
            "contactBuyer": "亚马逊",
            "handAdd": "手动发送",
        },
        ("buyer-voice", "pcxHealth"): {
            "Good": "良好",
            "Excellent": "优秀",
            "Fair": "一般",
            "Poor": "不佳",
            "Verypoor": "极差",
        },
        ("profit-analysis-v2", "queryType"): {
            value: "官方未提供中文含义"
            for value in ("market", "category", "father_asin", "asin", "spu", "sku", "msku")
        },
        ("profit-analysis-v2", "costValues"): {
            0: "先进先出",
            1: "月末平均",
            2: "自定义成本",
            3: "混合成本",
        },
        ("profit-analysis-v2", "dateType"): {0: "按开始日期与结束日期", 1: "按月份"},
        ("listing-performance", "groupByType"): {"asin": "ASIN维度", "seller_sku": "MSKU维度"},
        ("asin-traffic-statistics", "viewType"): {"day": "日", "week": "周", "month": "月"},
        ("catalog-brands", "state"): {"Active": "启用", "Inactive": "停用"},
        ("catalog-categories", "state"): {"Active": "启用", "Inactive": "停用"},
    }
    currency_fields = {
        ("sales-performance", "showCurrencyType"),
        ("profit-analysis-v2", "currency"),
        ("product-performance", "showCurrencyType"),
        ("listing-performance", "showCurrencyType"),
        ("asin-traffic-statistics", "currency"),
        ("asin-traffic-data", "currency"),
    }
    actual_enum_fields = {
        (endpoint_key, field_name)
        for endpoint_key, endpoint in ENDPOINTS.items()
        for field_name, field in endpoint.fields.items()
        if field.enum_values
    }
    assert actual_enum_fields == set(expected) | currency_fields
    for (endpoint_key, field_name), values in expected.items():
        field = ENDPOINTS[endpoint_key].fields[field_name]
        assert {item.value: item.label for item in field.enum_values} == values


def test_every_registered_enum_value_passes_validation() -> None:
    payloads = {
        "product-list": {"page": 1, "pagesize": 10},
        "product-inventory": {"page": 1, "pagesize": 10},
        "sales-performance": {
            "groupByType": "seller_sku",
            "viewType": "DAY",
            "showCurrencyType": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
            "page": 1,
            "pagesize": 10,
        },
        "review": {"page": 1, "pagesize": 10},
        "buyer-voice": {"page": 1, "pagesize": 10},
        "profit-analysis-v2": {
            "queryType": "market",
            "costValues": 0,
            "page": 1,
            "pagesize": 10,
            "currency": "YUAN",
            "dateType": 0,
            "monthDate": "2026-01",
            "startDate": "2026-01-01",
            "endDate": "2026-01-01",
        },
        "product-performance": {
            "showCurrencyType": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
            "page": 1,
            "pagesize": 10,
        },
        "listing-performance": {
            "groupByType": "asin",
            "showCurrencyType": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
            "isShowTotal": False,
            "page": 1,
            "pagesize": 10,
        },
        "asin-traffic-statistics": {
            "currency": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
            "page": 1,
            "pagesize": 10,
            "viewType": "day",
        },
        "asin-traffic-data": {
            "currency": "YUAN",
            "beginDate": "2026-01-01",
            "endDate": "2026-01-01",
            "page": 1,
            "pagesize": 10,
        },
    }
    for endpoint_key, payload in payloads.items():
        spec = ENDPOINTS[endpoint_key]
        for field_name, field in spec.fields.items():
            for enum_value in field.enum_values:
                candidate = dict(payload)
                candidate[field_name] = (
                    [enum_value.value] if field.type_name.startswith("array<") else enum_value.value
                )
                spec.validate_payload(candidate)


def test_catalog_nested_warehouse_enums_are_official_and_validated() -> None:
    spec = ENDPOINTS["catalog-warehouses"]
    children = dict(spec.fields["model"].children)
    assert {item.value: item.label for item in children["status"].enum_values} == {
        "enable": "启用",
        "disable": "停用",
    }
    assert {item.value for item in children["typeList"].enum_values} == {
        "SELF",
        "SUPPLIER",
        "FBA",
        "THIRD",
        "WFS",
        "FULL",
        "EBAY",
        "ALIEXPRESS",
        "AMAZON_VC",
        "AMAZON_AWD",
        "CDISCOUNT_FBC",
        "WAYFAIR_CG",
        "EMAG_FBE",
        "TIKTOK_FBT",
        "WILDBERRIES_FBW",
        "YANDEX_FBY",
        "OZON_FBO",
    }
    spec.validate_payload(
        {"model": {"status": "enable", "typeList": ["SELF"]}, "page": 1, "pagesize": 10}
    )
    with pytest.raises(ValidationError, match="Invalid value"):
        spec.validate_payload({"model": {"status": "guessed"}, "page": 1, "pagesize": 10})


def test_dynamic_identifiers_are_not_fixed_enums() -> None:
    dynamic_fields = [
        (endpoint_key, field_name, field)
        for endpoint_key, endpoint in ENDPOINTS.items()
        for field_name, field in endpoint.fields.items()
        if field.dynamic_identifier
    ]
    assert dynamic_fields
    assert all(not field.enum_values for _, _, field in dynamic_fields)
    assert ENDPOINTS["search-term-performance"].fields["marketId"].dynamic_identifier is True
    platform_codes = ENDPOINTS["profit-analysis-v2"].fields["platformCodes"]
    assert platform_codes.enum_status == "official_not_published"
    assert platform_codes.enum_values == ()


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
