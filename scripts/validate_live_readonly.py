"""Bounded serial CLI probes. Business inputs/results exist only in process memory.

The generated report contains public endpoint names, status categories and counts;
never request bodies, upstream messages, identifiers, headers, or trace IDs.
This historical probe targets the 210-query registry from version 0.3.1.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from gerpgo_cli.commands import catalog_raw, expanded, openapi
from gerpgo_cli.main import app
from gerpgo_cli.runtime import openapi_service
from gerpgo_sdk.openapi import ENDPOINTS, FieldSpec

PREVIOUS = {1020, 1021, 2453, 4645, 6025, 102, 66, 8655}
MASTER_DATA = {
    53,
    153,
    69,
    1035,
    1752,
    54,
    67,
    25,
    3095,
    139,
    2538,
    2537,
    2885,
    3891,
    4212,
    4216,
    4220,
    4224,
    4563,
    4943,
    5066,
    5262,
    3197,
    3059,
    63,
    64,
    212,
    141,
}
LEGACY_ROUTES = {
    53: ["product", "list"],
    15: ["inventory", "product"],
    3375: ["statistics", "sales-performance"],
    100: ["ads", "search-term-performance"],
    1092: ["customer", "review"],
    1014: ["customer", "buyer-voice"],
    2256: ["finance", "profit-analysis-v2"],
    99: ["ads", "keyword-performance"],
    131: ["statistics", "product-performance"],
    140: ["statistics", "listing-performance"],
    122: ["statistics", "asin-traffic-statistics"],
    1018: ["statistics", "asin-traffic-data"],
    153: ["catalog", "amazon-shops", "list"],
    25: ["catalog", "users", "list"],
    1035: ["catalog", "warehouses", "list"],
    1752: ["catalog", "brands", "list"],
    54: ["catalog", "categories", "list"],
    67: ["catalog", "multiplatform-shops", "list"],
    1177: ["catalog", "amazon-shops", "names-by-id"],
    1179: ["catalog", "amazon-shops", "warehouses-by-id"],
}
DATE_PAIRS = [
    ("startDate", "endDate"),
    ("beginDate", "endDate"),
    ("startDateData", "endDateData"),
    ("startDataDate", "endDataDate"),
    ("createStartDate", "createEndDate"),
    ("createdStartDate", "createdEndDate"),
    ("createdTimeBegin", "createdTimeEnd"),
    ("createTimeBegin", "createTimeEnd"),
    ("createTimeStart", "createTimeEnd"),
    ("createTimeBegin", "createTimeEnd"),
    ("startCreateTime", "endCreateTime"),
    ("createTimeStart", "createTimeEnd"),
    ("requestDateBegin", "requestDateEnd"),
    ("createBeginTime", "createEndTime"),
    ("beginCreatedAt", "endCreatedAt"),
    ("recordStartDate", "recordEndDate"),
    ("recordDateStart", "recordDateEnd"),
    ("startRecordDate", "endRecordDate"),
    ("addBeginDate", "addEndDate"),
    ("addStartDate", "addEndDate"),
    ("reportStartDate", "reportEndDate"),
    ("beginReportDate", "endReportDate"),
    ("reportDateStart", "reportDateEnd"),
    ("startTime", "endTime"),
    ("startDateTimeFrom", "startDateTimeTo"),
    ("timeStart", "timeEnd"),
    ("reviewDateBegin", "reviewDateEnd"),
    ("startCreatedDate", "endCreatedDate"),
    ("startTimeQuery", "endTimeQuery"),
    ("startAuditTime", "endAuditTime"),
    ("createdTimeAfter", "createdTimeBefore"),
]
# Formats confirmed in the current public request examples, absent from field prose.
EXAMPLE_FORMATS = {
    (3846, "startTime"): "yyyy-MM-dd HH:mm:ss",
    (3846, "endTime"): "yyyy-MM-dd HH:mm:ss",
    (3847, "startTime"): "yyyy-MM-dd HH:mm:ss",
    (3847, "endTime"): "yyyy-MM-dd HH:mm:ss",
    (1738, "reportDateStart"): "yyyy-MM-dd HH:mm:ss",
    (1738, "reportDateEnd"): "yyyy-MM-dd HH:mm:ss",
    (3188, "month"): "yyyy-MM",
    (6344, "reportMonth"): "yyyy-MM",
}
PUBLIC_ERRORS = {
    40004: "upstream_condition_or_contract_rejected",
    40007: "upstream_required_condition_missing",
    40402: "upstream_api_not_found",
    40403: "permission_denied",
    40404: "upstream_api_offline",
    50099: "upstream_erp_error",
    90008: "upstream_rate_limited",
}
REASONS = {
    "upstream_condition_or_contract_rejected": "上游拒绝参数/条件（40004），未猜值继续重试",
    "upstream_api_not_found": "上游返回 API 不存在（40402）",
    "upstream_erp_error": "上游 ERP 错误（50099）；复合市场标识所需内部店铺 ID 来源未确认",
    "no_purchase_order_code_in_scoped_order_or_association_query": (
        "单日采购单及关联采购查询未取得采购单号"
    ),
    "source_document_1366_has_no_customizedAttachment_sample": "单日配货单未取得定制附件 ID",
    "source_document_70_has_no_orderId_sample": "单日、单市场订单列表未取得订单号",
    "source_document_70_has_no_id_sample": "单日、单市场订单列表未取得订单主键",
    "source_document_70_has_no_parentId_sample": "单日、单市场订单列表未取得补单关联主键",
    "source_document_17_has_no_warehouseId_sample": "移除订单缺少可关联的仓库 ID，未拼接不相关仓库",
    "source_document_69_has_no_msku_sample": "所选单市场商品列表未取得 MSKU 样本",
    "root_array_transport_not_verified": "官方根数组请求体与当前对象传输契约不一致，未绕过 CLI",
    "root_array_transport_and_source_order_not_verified": (
        "根数组传输契约及对应销售出库单来源未确认"
    ),
    "unresolved_required_field_country": "官方未明确 country 值格式，未推测国家编码",
    "source_document_211_has_no_attributeName_sample": "产品详情未取得变体属性名称样本",
    "no_confirmed_numeric_transport_and_correlated_transfer_sample": (
        "未取得同一调拨单对应的两端仓库及数值物流方式 ID"
    ),
    "unresolved_required_field_sort": "官方未公开必填排序字段取值，未猜测 sort/order",
    "source_document_1366_has_no_foOrderNo_sample": "单日配货单列表未取得 FO 单号",
    "no_inbound_plan_id_in_scoped_shipment_or_detail_query": (
        "单日货件及已接入详情未取得入库计划 ID"
    ),
    "unresolved_required_field_startSettleDate": "履约结算开始日期的格式及关联条件未确认",
}
CATEGORIES = {
    "first_page_only": "仅第一页",
    "single_day_date_range": "单日日期范围",
    "single_month_required_by_api": "接口要求的单月范围",
    "single_market_from_directory": "目录取得的单个市场",
    "single_sku_from_product_query": "产品查询取得的单个 SKU",
    "single_official_warehouse_type": "单个官方仓库类型",
}


class MissingCondition(Exception):
    pass


def first_value(value: Any, name: str) -> Any:
    """Read a known response property without persisting its value."""
    if isinstance(value, dict):
        if value.get(name) not in (None, "", []):
            return value[name]
        for item in value.values():
            found = first_value(item, name)
            if found not in (None, "", []):
                return found
    elif isinstance(value, list):
        for item in value:
            found = first_value(item, name)
            if found not in (None, "", []):
                return found
    return None


def rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ("rows", "records"):
            if isinstance(data.get(key), list):
                return rows(data[key])
        return [data] if data else []
    return []


class Probe:
    def __init__(self, run_date: date, output: Path, resume: bool = False) -> None:
        self.day = (run_date - timedelta(days=1)).isoformat()
        self.month = self.day[:7]
        self.output = output
        self.data: dict[int, Any] = {}
        self.records: dict[int, dict[str, Any]] = {}
        self.focus_fba = False
        if resume:
            report = json.loads(output.read_text(encoding="utf-8"))
            self.records = {r["document_id"]: r for r in report["results"]}
            for record in self.records.values():
                record.pop("nonempty", None)
                if record.get("upstream_code") in PUBLIC_ERRORS:
                    record["reason"] = PUBLIC_ERRORS[record["upstream_code"]]
        self.by_id = {s.document_id: s for s in ENDPOINTS.values()}
        self.service = openapi_service("prod")
        self.service.client.test_authentication()
        # Shared authenticated client/limiter, but actual commands and JSON envelopes.
        openapi.openapi_service = lambda profile: self.service
        expanded.openapi_service = lambda profile: self.service
        catalog_raw.openapi_service = lambda profile: self.service
        self.runner = CliRunner()
        self.diagnostic: dict[str, Any] = {}
        self.service.client.session.hooks["response"].append(self.observe)

    def observe(self, response: Any, **kwargs: Any) -> None:
        if response.url.endswith("/api_token"):
            return
        try:
            result = response.json()
        except ValueError:
            self.diagnostic = {"http_status": response.status_code, "reason": "non_json_response"}
            return
        if not isinstance(result, dict):
            return
        message = str(result.get("messages") or result.get("message") or "")
        reason = "upstream_rejected_unclassified"
        if re.search(
            "权限|授权|无权|未开通|套餐|permission|forbidden|access denied", message, re.I
        ):
            reason = "permission_or_subscription_denied"
        elif re.search(
            "必填|不能为空|必传|至少|参数|格式|范围|required|invalid|missing", message, re.I
        ):
            reason = "upstream_condition_or_contract_rejected"
        elif re.search("不存在|未找到|not found", message, re.I):
            reason = "sample_not_found_in_scope"
        elif response.status_code >= 500:
            reason = "upstream_server_error"
        code = result.get("code")
        self.diagnostic = {
            "http_status": response.status_code,
            "upstream_code": code if isinstance(code, int) else None,
            "reason": PUBLIC_ERRORS.get(code, reason) if isinstance(code, int) else reason,
        }

    def sample(self, doc_id: int, key: str) -> Any:
        value = first_value(self.data.get(doc_id), key)
        if value in (None, "", []):
            raise MissingCondition(f"source_document_{doc_id}_has_no_{key}_sample")
        return value

    def market(self) -> Any:
        return self.sample(153, "marketId")

    def convert(self, value: Any, field: FieldSpec) -> Any:
        if field.type_name.startswith("array"):
            raw = value if isinstance(value, list) else [value]
            if field.type_name in {"array<int>", "array<long>"}:
                return [int(x) for x in raw[:1]]
            if field.type_name == "array<string>":
                return [str(x) for x in raw[:1]]
            return raw[:1]
        if field.type_name in {"int", "long", "short", "number"}:
            return int(value)
        return value if field.type_name == "boolean" else str(value)

    def date_value(
        self, field: FieldSpec, end: bool = False, doc_id: int = 0, name: str = ""
    ) -> str:
        description = (
            field.description.lower() + " " + EXAMPLE_FORMATS.get((doc_id, name), "").lower()
        )
        if "yyyy-mm-dd hh:mm:ss" in description or field.date_format == "yyyy-MM-dd HH:mm:ss":
            return self.day + (" 23:59:59" if end else " 00:00:00")
        if "yyyy-mm-dd" in description or field.date_format == "yyyy-MM-dd":
            return self.day
        if "yyyy-mm" in description or field.date_format == "yyyy-MM":
            return self.month
        raise MissingCondition("official_date_format_not_published")

    def build_fields(self, doc_id: int, fields: dict[str, FieldSpec]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for name, field in fields.items():
            if name in {"page", "pageNo", "pageCurrent", "current"}:
                payload[name] = self.convert(1, field)
            elif name in {"pagesize", "pageSize", "size", "count"}:
                payload[name] = self.convert(max(10, int(field.minimum or 1)), field)
            elif name == "pageInfo" and {"page", "pagesize"}.issubset(fields):
                continue
            elif field.children and field.type_name == "object":
                payload[name] = self.build_fields(doc_id, dict(field.children))
            elif (
                field.children
                and field.type_name == "array<object>"
                and {"timeStart", "timeEnd"}.issubset(dict(field.children))
            ):
                payload[name] = [self.build_fields(doc_id, dict(field.children))]
        for start, end in DATE_PAIRS:
            if (
                doc_id not in MASTER_DATA
                and start in fields
                and end in fields
                and "废弃" not in fields[start].description
                and doc_id not in {5136, 6087, 6670}
            ):
                payload[start] = self.date_value(fields[start], doc_id=doc_id, name=start)
                payload[end] = self.date_value(fields[end], end=True, doc_id=doc_id, name=end)
                break
        for name, field in fields.items():
            if name in payload:
                continue
            if field.required:
                payload[name] = self.required(doc_id, name, field)
        return payload

    def required(self, doc_id: int, name: str, field: FieldSpec) -> Any:
        if (doc_id, name) in {(1024, "poCode"), (8808, "poCodeList")}:
            for source, key in ((86, "code"), (90, "poCode")):
                value = first_value(self.data.get(source), key)
                if value not in (None, "", []):
                    return self.convert(value, field)
            raise MissingCondition("no_purchase_order_code_in_scoped_order_or_association_query")
        if doc_id == 1399:
            ledger = next(
                (
                    r
                    for r in rows(self.data.get(773))
                    if all(
                        r.get(k) not in (None, "")
                        for k in (
                            "referenceId",
                            "warehouseId",
                            "msku",
                            "sku",
                            "quantity",
                            "reportDate",
                        )
                    )
                ),
                None,
            )
            if ledger is None:
                raise MissingCondition("no_correlated_ledger_reference_and_quantity_sample")
            value = {
                "skuList": [ledger["sku"]],
                "quantity": int(float(ledger["quantity"]) > 0),
            }.get(name, ledger.get(name))
            return self.convert(value, field)
        if doc_id == 235 and name == "code":
            item = next(
                (r for r in rows(self.data.get(234)) if r.get("type") == "In" and r.get("code")),
                None,
            )
            if item is None:
                raise MissingCondition("no_inbound_record_in_single_day_scope")
            return item["code"]
        if doc_id == 4224 and name == "name":
            return self.sample(25, "groupName")
        if doc_id == 694 and name == "id":
            return self.convert(self.sample(1366, "customizedAttachment"), field)
        if doc_id == 6013 and name == "platformCode":

            def contains_amazon(value: Any) -> bool:
                if isinstance(value, dict):
                    return "AMAZON" in value or any(contains_amazon(v) for v in value.values())
                if isinstance(value, list):
                    return any(contains_amazon(v) for v in value)
                return value == "AMAZON"

            if not contains_amazon(self.data.get(8655)):
                raise MissingCondition("platform_definition_has_no_amazon_code_sample")
            return "AMAZON"
        if doc_id == 84 and name == "warehouseId":
            return self.convert(self.sample(15, "warehouseId"), field)
        if doc_id == 3496:
            raise MissingCondition("no_confirmed_numeric_transport_and_correlated_transfer_sample")
        if field.children:
            item = self.build_fields(doc_id, dict(field.children))
            return [item] if field.type_name.startswith("array") else item
        if name in {"marketId", "marketIds", "marketList", "markerIds", "marketIdList"}:
            return self.convert(self.market(), field)
        if name in {"sku", "skuList", "skus"}:
            return self.convert(self.sample(53, "sku"), field)
        if name in {"msku", "mskuList", "mskus"}:
            return self.convert(self.sample(69, "msku"), field)
        if name in {"asin", "asins", "asinList"}:
            return self.convert(self.sample(69, "asin"), field)
        if name == "countryCode":
            return self.convert(self.sample(153, "countryCode"), field)
        if doc_id == 3420 and name == "list":
            return [self.sample(53, "sku")]
        if doc_id == 301 and name == "queryCurrency":
            return "USD"  # Current official request example, not an inferred enum.
        if doc_id == 3883 and name == "platformCode":
            return "AMAZON"  # Current official request example.
        if name in {"currency", "showCurrencyType", "queryCurrency"} and (
            any(e.value == "YUAN" for e in field.enum_values) or "YUAN" in field.description
        ):
            return "YUAN"
        if field.enum_values:
            values = [e.value for e in field.enum_values]
            # Explicit documented dimensions that minimize scope; no invented enums.
            for value in ("DAY", "day", "SKU", "sku", "asin", 0):
                if value in values:
                    return self.convert(value, field)
            return self.convert(values[0], field)
        if field.type_name == "boolean":
            return False
        if field.date_format:
            return self.convert(
                self.date_value(field, end=bool(re.search("end|to$", name, re.I))), field
            )
        if name in {"month", "monthList", "reportMonth", "monthDate"}:
            return self.convert(self.date_value(field, doc_id=doc_id, name=name), field)
        if name == "dimension" and "sku" in field.description:
            return "sku"
        if name == "columnType" and "CREATE_TIME" in field.description:
            return "CREATE_TIME"
        if name == "sort" and "createTime" in field.description:
            return "createTime"
        if name == "order" and "asc" in field.description:
            return "asc"
        if doc_id == 211 and name == "id":
            product = next((r for r in rows(self.data.get(53)) if r.get("id")), None)
            if product is None:
                raise MissingCondition("source_document_53_has_no_root_product_id")
            return self.convert(product["id"], field)
        bindings = {
            8: {"orderId": (70, "orderId")},
            119: {"orderId": (70, "id")},
            10: {"fid": (70, "id")},
            16: {"warehouseId": (17, "warehouseId"), "orderId": (17, "orderId")},
            4139: {"parentId": (70, "parentId")},
            4482: {"orderId": (70, "orderId")},
            4006: {"id": (4005, "id")},
            6771: {"businessKey": (6770, "businessKey")},
            1024: {"poCode": (86, "code")},
            90: {"code": (87, "code")},
            1026: {"code": (1025, "code")},
            8808: {"poCodeList": (86, "code")},
            1029: {"code": (1027, "code")},
            1030: {"code": (1027, "code")},
            1032: {"code": (1027, "code")},
            1742: {"codes": (1027, "code")},
            2539: {"shipmentId": (1033, "shipmentId")},
            4443: {"shipmentId": (1033, "shipmentId")},
            5070: {"attributeName": (211, "attributeName")},
        }
        if name in bindings.get(doc_id, {}):
            source, key = bindings[doc_id][name]
            return self.convert(self.sample(source, key), field)
        raise MissingCondition("unresolved_required_field_" + name)

    def payload(self, doc_id: int) -> tuple[dict[str, Any], list[str]]:
        if doc_id == 112:
            raise MissingCondition("composite_country_and_internal_shop_identifier_not_confirmed")
        spec = self.by_id[doc_id]
        fields = dict(spec.fields)
        payload = self.build_fields(doc_id, fields)
        categories: list[str] = []
        if doc_id == 1035 and self.focus_fba:
            payload["model"]["typeList"] = ["FBA"]
            categories.append("single_official_warehouse_type")
        # A single, observed market; never silently fan out across markets.
        for name in ("marketId", "marketIds", "marketIdList", "marketList"):
            if name in fields:
                payload[name] = self.convert(self.market(), fields[name])
                categories.append("single_market_from_directory")
                break
        # A single SKU for snapshot queries without a date filter.
        if doc_id not in {53, 153, 69} and not any(
            re.search("date|time|month", name, re.I) for name in payload
        ):
            for name in ("skuList", "skus", "sku"):
                if name in fields and 53 in self.data:
                    payload[name] = self.convert(self.sample(53, "sku"), fields[name])
                    categories.append("single_sku_from_product_query")
                    break
        if doc_id == 2256:
            payload.update(startDate=self.day, endDate=self.day)
        if doc_id == 1022:
            payload.update(
                dateType="DAY", beginDate=self.day + " 00:00:00", endDate=self.day + " 23:59:59"
            )
        if doc_id == 1449:
            payload["dateType"] = "4"  # official creation-date dimension
        if doc_id == 3686:
            payload["dateType"] = "createDate"
        if doc_id == 301:
            payload["dateType"] = 1  # Official invoice issue-date dimension.
        if doc_id == 3419:
            # A country format is not inferred from an unrelated country identifier.
            raise MissingCondition("country_value_format_requires_official_confirmation")
        if doc_id == 3420:
            payload["list"] = [self.sample(53, "sku")]
        if doc_id == 1049:
            raise MissingCondition("root_array_transport_not_verified")
        if doc_id == 1455:
            raise MissingCondition("root_array_transport_and_source_order_not_verified")
        if doc_id == 5516:
            payload["foOrderCodeList"] = [self.sample(1366, "foOrderNo")]
        if doc_id == 4696:
            value = first_value(self.data.get(2539), "inboundPlanId") or first_value(
                self.data.get(1033), "inboundPlanId"
            )
            if not value:
                raise MissingCondition("no_inbound_plan_id_in_scoped_shipment_or_detail_query")
            payload["inboundPlanId"] = value
        if doc_id == 1080:
            raise MissingCondition("root_array_transport_not_verified")
        if doc_id == 15:
            payload["skuList"] = [self.sample(53, "sku")]
        if doc_id == 6670:
            payload["skuList"] = [self.sample(53, "sku")]
        if doc_id in {5136, 6087, 6013}:
            warehouse = next(
                (
                    r
                    for r in rows(self.data.get(1035))
                    if r.get("type") == ("WFS" if doc_id == 6087 else "FBA") and r.get("id")
                ),
                None,
            )
            if warehouse is None:
                raise MissingCondition("no_matching_platform_warehouse_in_directory_sample")
            payload["erpWarehouseIds" if doc_id == 6013 else "warehouseIdList"] = [warehouse["id"]]
        if doc_id == 131:
            payload["pagesize"] = spec.default_page_size
        if doc_id == 1028:
            payload["deliveryCodes"] = [self.sample(1027, "code")]
        if doc_id == 1052:
            payload["sellingList"] = [
                {"marketId": int(self.market()), "msku": self.sample(69, "msku")}
            ]
        if doc_id == 3493:
            raise MissingCondition("settlement_date_format_and_platform_values_not_verified")
        if doc_id == 3496:
            raise MissingCondition("no_correlated_transfer_warehouse_and_transport_sample")
        if doc_id in {5383, 5385}:
            raise MissingCondition("sort_contract_and_correlated_purchase_sample_not_verified")
        spec.validate_payload(None if spec.request_body_mode == "none" else payload)
        if any(re.search("date|time", name, re.I) for name in payload):
            categories.append("single_day_date_range")
        if doc_id in {2284, 1038, 1039, 2658, 6344, 3188}:
            categories.append("single_month_required_by_api")
        if spec.supports_auto_pagination:
            categories.append("first_page_only")
        return payload, sorted(set(categories))

    def invoke(self, doc_id: int) -> None:
        spec = self.by_id[doc_id]
        record: dict[str, Any] = {"document_id": doc_id, "name": spec.official_name}
        if not spec.read_only:
            raise ValueError("Live probe accepts registered read-only endpoints only")
        try:
            payload, categories = self.payload(doc_id)
        except MissingCondition as exc:
            record.update(status="blocked_condition", reason=str(exc))
            self.records[doc_id] = record
            self.save()
            return
        except Exception:
            record.update(status="blocked_contract", reason="registered_payload_validation_failed")
            self.records[doc_id] = record
            self.save()
            return
        command = ["openapi", *(LEGACY_ROUTES.get(doc_id) or list(spec.cli_route or ()))]
        command += ["--profile", "prod", "--format", "json", "--response", "raw"]
        input_text = None
        if spec.request_body_mode != "none":
            command += ["--input", "-"]
            input_text = json.dumps(payload, ensure_ascii=False)
        if doc_id in {1177, 1179}:
            command += ["--market-id", str(self.market())]
        self.diagnostic = {}
        try:
            result = self.runner.invoke(app, command, input=input_text)
            try:
                envelope = json.loads(result.stdout)
            except (ValueError, AttributeError):
                envelope = {}
            upstream = envelope.get("data")
            passed = (
                result.exit_code == 0
                and envelope.get("ok") is True
                and isinstance(upstream, dict)
                and upstream.get("code") == 200
            )
            record.update(
                status="success" if passed else "failed",
                parameter_categories=categories,
                exit_code=result.exit_code,
                json_envelope=bool(envelope),
                upstream_code=self.diagnostic.get("upstream_code"),
                http_status=self.diagnostic.get("http_status"),
            )
            if passed:
                data = upstream.get("data")
                self.data[doc_id] = data
                record.update(
                    structure="object"
                    if isinstance(data, dict)
                    else "array"
                    if isinstance(data, list)
                    else "null"
                    if data is None
                    else "scalar",
                )
            else:
                record["error_code"] = (
                    envelope.get("error_code")
                    if envelope.get("error_code")
                    in {
                        "GERPGO_AUTH_FAILED",
                        "GERPGO_API_ERROR",
                        "GERPGO_VALIDATION_ERROR",
                        "GERPGO_NETWORK_ERROR",
                        "GERPGO_CONFIG_ERROR",
                    }
                    else "CLI_OR_UNKNOWN_ERROR"
                )
                record["reason"] = self.diagnostic.get("reason", "cli_rejected_before_upstream")
        except Exception:
            record.update(
                status="failed", reason="probe_internal_error_no_sensitive_details_emitted"
            )
        self.records[doc_id] = record
        self.save()
        print(
            json.dumps(
                {"document_id": doc_id, "name": spec.official_name, "status": record["status"]},
                ensure_ascii=False,
            ),
            flush=True,
        )
        time.sleep(0.5)

    def save(self) -> None:
        targets = [r for i, r in self.records.items() if i not in PREVIOUS]
        report = {
            "run_date": "2026-11-05",
            "profile": "prod",
            "target_count": 202,
            "counts": dict(Counter(r["status"] for r in targets)),
            "results": targets,
            "privacy": "No request or response values, credentials, headers or trace IDs stored.",
            "scope": "Serial registered read-only CLI calls; first page only. Selected date "
            "pairs span one day, month-only reports use one month. No date widening. "
            "Identifiers come from integrated query results in memory; no raw-request bypass.",
            "success_criteria": "CLI exit 0, ok=true, upstream code=200, parseable JSON. "
            "Empty arrays/null are allowed; business completeness and nonempty rows "
            "are not claimed.",
        }
        self.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.render_report(targets)

    def render_report(self, records: list[dict[str, Any]]) -> None:
        counts = Counter(r["status"] for r in records)
        lines = [
            "# 只读实调用验证记录，2026-11-05",
            "",
            f"目标 202 项；当前记录 {len(records)} 项：成功 {counts['success']} 项，"
            f"上游/CLI 失败 {counts['failed']} 项，条件或契约阻塞未调用 "
            f"{counts['blocked_condition'] + counts['blocked_contract']} 项。",
            "",
            "成功标准：CLI 退出码 0、JSON ok=true、上游 code=200，响应 JSON 可解析。"
            "null、空数组也可成功；不据此声称有业务数据或分析数据完整。",
            "",
            "使用 prod，串行执行并共用 SDK 的限频器，仅查询第一页；选择日期对时使用单日，"
            "只支持月份的报表使用单月。目录及库存快照按已注册字段约束。"
            "未扩大日期来寻找样本；所需标识从已接入接口取得并仅保存在进程内存。",
            "",
            "没有保存业务响应、请求值、凭证、请求头、Cookie、Session 或 Trace ID。"
            "下表编号均为公开官方文档 ID。没有已确认的权限不足错误；"
            "40402 是 API 不存在，50099 是 ERP 错误，不能误称权限问题。",
            "",
            "产品表现按文档参数及已注册默认页大小补测后仍返回 40004；"
            "销售回款分析首次返回 50099，随后确认 marketIds 需要国家 ID 与内部店铺 ID "
            "组成的复合标识，未确认对应来源，不继续猜值请求。",
            "",
            "前一轮 8 项另见 [2026-11-04 记录](live-verification.md)，不重复计入本轮 202 项。",
            "",
            "| 接口（官方文档） | 实调用结果 | 参数类别（不含真实值） "
            "| JSON 结构 | 未通过/未验证原因 |",
            "|---|---|---|---|---|",
        ]
        for record in records:
            doc_id = record["document_id"]
            spec = self.by_id[doc_id]
            called = record["status"] in {"success", "failed"}
            categories = [CATEGORIES.get(c, c) for c in record.get("parameter_categories", [])]
            if called:
                required = [k for k, f in dict(spec.fields).items() if f.required]
                if required:
                    categories.append("注册必填字段：" + ", ".join(required))
                if doc_id == 1028:
                    categories.append("关联发货单号")
                if doc_id in {5136, 6087, 6013}:
                    categories.append("目录取得的单个对应平台仓库")
            reason = record.get("reason", "")
            result = {"success": "成功", "failed": "失败"}.get(record["status"], "未调用")
            structure = record.get("structure", "失败，未通过" if called else "未验证")
            parameters = "；".join(categories) or ("无业务筛选参数" if called else "条件未齐全")
            lines.append(
                f"| [{spec.official_name} ({doc_id})](https://open.gerpgo.com/document?id={doc_id})"
                f" | {result} | {parameters}"
                f" | {structure} | {REASONS.get(reason, reason) or '—'} |"
            )
        self.output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute", action="store_true", help="Authorize bounded live read-only CLI calls"
    )
    parser.add_argument("--resume", action="store_true", help="Retry unresolved targets only")
    parser.add_argument("--only", type=int, nargs="+", help="Registered document IDs to probe")
    args = parser.parse_args()
    if not args.execute:
        parser.error("Explicit --execute is required; no live request sent")
    if len(ENDPOINTS) != 210:
        parser.error("Historical probe requires the v0.3.1 registry; no live request sent")
    probe = Probe(date(2026, 11, 5), Path("docs/live-verification-2026-11-05.json"), args.resume)
    seeds = [
        153,
        53,
        69,
        1035,
        67,
        25,
        8655,
        70,
        17,
        4005,
        6770,
        43,
        87,
        86,
        1024,
        1025,
        1027,
        1033,
        3686,
        211,
        773,
        234,
        1366,
    ]
    targets = [s.document_id for s in ENDPOINTS.values() if s.document_id not in PREVIOUS]
    if args.only and set(args.only).issubset({5136, 6013}):
        probe.focus_fba = True
        sequence = [1035, 8655, *args.only]
    else:
        sequence = [153, 53, 1035, 8655, 15, *args.only] if args.only else seeds + targets
    for doc_id in dict.fromkeys(sequence):
        if args.resume and doc_id not in seeds:
            previous = probe.records.get(doc_id, {})
            if not args.only and (previous.get("status") == "success" or doc_id in {5098, 112}):
                continue
        probe.invoke(doc_id)
    print(
        json.dumps(
            {
                "completed": len([i for i in probe.records if i not in PREVIOUS]),
                "counts": dict(
                    Counter(r["status"] for i, r in probe.records.items() if i not in PREVIOUS)
                ),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
