"""Frozen, reviewed read-only public contracts. No network discovery at runtime."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .registry import CURRENCY_ENUM, EndpointSpec, EnumValue, FieldSpec

MODULES = {
    "基础数据": "base",
    "销售": "sales",
    "广告": "ads",
    "客服": "customer",
    "统计": "statistics",
    "产品": "product",
    "库存": "inventory",
    "订单": "orders",
    "采购": "procurement",
    "物流": "logistics",
    "仓库": "warehouse",
    "财务": "finance",
    "报表": "reports",
    "多平台": "multiplatform",
}
# These names describe business mutations, including the misleading scheduling endpoint.
WRITE_IDS = {
    61,
    2033,
    935,
    936,
    3,
    1,
    1019,
    1753,
    59,
    5067,
    5071,
    6693,
    6694,
    3010,
    18,
    1557,
    19,
    1559,
    4737,
    4738,
    3910,
    931,
    932,
    92,
    93,
    2618,
    2634,
    1593,
    2611,
    1060,
    3100,
    689,
    693,
    1739,
    1434,
    1082,
    2875,
    3101,
    3102,
    5094,
    5384,
    5386,
    8412,
    1744,
    2732,
    4624,
    6661,
    6663,
    6681,
}


def catalog_documents() -> list[dict[str, Any]]:
    path = Path(__file__).with_name("official_catalog.json")
    return json.loads(path.read_text(encoding="utf-8"))["documents"]  # type: ignore[no-any-return]


def kebab(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).replace("_", "-").lower()


def route(document: dict[str, Any]) -> tuple[str, str]:
    module = MODULES[document["category"].split("/")[0]]
    # The official service and operation provide a stable, shallow command name.
    parts = document["path"].strip("/").split("/")
    command = "-".join(kebab(x) for x in parts[2:])
    if document["id"] in {1436, 1738}:
        command = kebab(parts[1]) + "-" + command
    return module, command


def field_spec(item: dict[str, Any]) -> FieldSpec:
    description = item["description"]
    children = tuple((child["name"], field_spec(child)) for child in item["children"])
    date_format = next(
        (fmt for fmt in ("yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd", "yyyy-MM") if fmt in description),
        None,
    )
    maximum = re.search(r"(?:最大|最多)\s*(\d+)", description)
    minimum = re.search(r"最小\s*(\d+)", description)
    recommended = re.search(r"建议不超过\s*(\d+)", description)
    enums = tuple(EnumValue(x["value"], x["label"]) for x in item.get("enum_values", []))
    currency = "币种" in description and ("Q&A" in description or "QA" in description)
    if currency:
        enums = CURRENCY_ENUM
    dynamic = (
        bool(re.search(r"(?:id|ids|sku|asin|code|codes|order|serial|outnum)", item["name"], re.I))
        and not enums
    )
    return FieldSpec(
        item["type"],
        item["must"],
        description,
        enum_values=enums,
        enum_status="documented"
        if enums
        else "documented_text"
        if re.search(r"状态|类型|枚举|取值", description)
        and re.search(r"[:：=-].*[，,；;、]", description)
        and "默认" not in description
        else "official_not_published"
        if re.search("状态|类型|枚举", description)
        else "not_applicable",
        enum_document_id=11 if currency else None,
        dynamic_identifier=dynamic,
        date_format=date_format,
        maximum=int(maximum[1])
        if maximum and item["name"] in {"pagesize", "pageSize", "size", "count"}
        else None,
        minimum=int(minimum[1])
        if minimum
        else 1
        if item["name"] in {"page", "pagesize", "pageSize", "current", "size", "count"}
        else None,
        max_items=int(maximum[1]) if maximum and item["type"].startswith("array") else None,
        recommended_maximum=int(recommended[1]) if recommended else None,
        constraints=(description,) if description else (),
        children=children,
    )


def build_endpoints(existing: dict[str, EndpointSpec]) -> dict[str, EndpointSpec]:
    existing_ids = {spec.document_id for spec in existing.values()}
    result = {}
    for doc in catalog_documents():
        if doc["id"] in existing_ids or doc.get("implementation_blocker"):
            continue
        if doc["id"] in WRITE_IDS or doc["id"] == 596 or doc["method"] not in {"Post", "Get"}:
            continue
        if (
            not doc["limit_period"]
            or not doc["limit_times"]
            or doc["limit_unit"] not in {"秒", "分钟", "小时"}
        ):
            continue
        module, command = route(doc)
        fields = {item["name"]: field_spec(item) for item in doc["request"]}
        if any(_needs_enum_review(field) for field in fields.values()):
            continue
        nested_pagination = dict(fields["pageInfo"].children) if "pageInfo" in fields else {}
        page_size = (
            fields.get("pagesize")
            or fields.get("pageSize")
            or fields.get("size")
            or fields.get("count")
            or nested_pagination.get("pagesize")
        )
        interval = (
            doc["limit_period"]
            * {"秒": 1, "分钟": 60, "小时": 3600}[doc["limit_unit"]]
            / doc["limit_times"]
        )
        response_data: dict[str, Any] = next(
            (x for x in doc["response"] if x["name"] == "data"), {}
        )
        response_fields = {x["name"] for x in response_data.get("children", [])}
        rows_key = (
            "rows"
            if "rows" in response_fields
            else "records"
            if "records" in response_fields
            else None
        )
        key = f"{module}-{command}"
        result[key] = EndpointSpec(
            key,
            doc["name"],
            doc["id"],
            "POST",
            doc["path"],
            float(interval),
            MappingProxyType(fields),
            pagination_mode="cursor" if doc["id"] in {101, 104, 575, 576} else "direct",
            request_page_field="current" if doc["id"] in {137, 138} else "page",
            request_page_size_field="size"
            if doc["id"] in {137, 138}
            else "pageSize"
            if doc["id"] in {3424, 5098}
            else "pagesize",
            official_max_page_size=int(page_size.maximum)
            if page_size and page_size.maximum
            else None,
            official_recommended_page_size=int(page_size.recommended_maximum)
            if page_size and page_size.recommended_maximum
            else None,
            default_page_size=min(100, int(page_size.maximum or 100)) if page_size else None,
            request_body_mode="json" if fields else "empty_object",
            response_rows_key=rows_key,
            response_total_key="total" if "total" in response_fields else None,
            cli_route=(module, command),
            combination_constraints=(doc.get("description") or "",),
            public_method_verified_date="2026-11-04" if doc["method"] == "Get" else None,
            metadata_method_difference="Public renderer specifies POST; detail metadata says Get."
            if doc["method"] == "Get"
            else None,
        )
    return result


def _needs_enum_review(field: FieldSpec) -> bool:
    return field.enum_status == "documented_text" or any(
        _needs_enum_review(child) for _, child in field.children
    )
