"""Reduce the public snapshot and encode only unambiguous enum declarations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PATH = Path(__file__).resolve().parents[1] / "src/gerpgo_sdk/openapi/official_catalog.json"

# Reviewed field layouts, not guessed field-name conventions. Values remain in official metadata.
PROSE_LAYOUTS = {
    4216: {"status": "digit_space"},
    4220: {"status": "reverse_equal"},
    69: {"isVague": "forward"},
    3095: {"marketState": "slash", "apiState": "forward", "sort": "forward", "order": "forward"},
    6770: {"procStatus": "forward"},
    5765: {"orderStatus": "forward"},
    5766: {
        "ackStatusList": "forward",
        "invoiceStatusList": "forward",
        "invoiceSubmitStatus": "forward_incomplete",
        "shipType": "values",
        "prOrderType": "values",
        "purchaseOrderState": "forward",
        "purchaseOrderTypes": "values",
        "shipmentStatusList": "forward",
        "columnType": "forward",
    },
    5768: {
        "abnormalTypeList": "values",
        "shipmentShippingStatusList": "forward",
        "shipmentStatusList": "forward",
    },
    4604: {"state": "forward"},
    4005: {"status": "space"},
    309: {"transactionStatusList": "forward"},
    112: {"fundTransferStatus": "space"},
    5638: {"thirdSkuStatusList": "values", "matchStatus": "forward", "state": "forward"},
    6349: {"replaceStatus": "forward"},
    1399: {"quantity": "values"},
    4615: {"productStatus": "forward", "productTypeList": "forward"},
    7706: {"status": "forward"},
    1366: {"orderType": "forward"},
    1033: {"typeList": "values", "fbaPackage": "forward", "compartmentFlag": "forward"},
    3059: {"status": "values"},
    6670: {"statusList": "reverse", "printStatus": "reverse", "appointmentStatusList": "reverse"},
    1449: {
        "receiveStatusList": "forward",
        "orderStatusList": "forward",
        "billType": "forward",
        "dateType": "forward",
        "rnType": "forward",
    },
    3686: {"dateType": "reverse_colon", "statusList": "reverse"},
    5972: {"orderStatusList": "forward", "orderType": "forward"},
    6023: {"outboundStatus": "forward", "type": "forward"},
    6662: {
        "qcStatusList": "forward",
        "qcType": "digit_space",
        "qcWay": "digit_space",
        "qcResult": "digit_space",
    },
    3493: {"matchingStatus": "digit_space"},
    1377: {"platformOrderPerformingParty": "forward_comma"},
    137: {"dateType": "forward"},
    5592: {"dateType": "digit_space", "orderStatuss": "forward", "orderTypes": "forward"},
    1040: {"dateType": "values", "type": "values"},
    113: {"typeCode": "forward"},
    138: {"orderStatuses": "values", "deliveryStatuses": "values"},
}


def prose(field: dict[str, Any], layout: str) -> None:
    text = field["description"].strip().strip("[]")
    pairs = []
    if layout in {"forward", "forward_incomplete", "forward_comma"}:
        separators = r"[，,；;)\]]" if layout == "forward_comma" else r"[，,；;、)\]]"
        pairs = re.findall(
            r"([A-Za-z][A-Za-z0-9_]*|\d+)\s*[-：:]+\s*(.+?)"
            r"(?=" + separators + r"|\s+(?:[A-Za-z][A-Za-z0-9_]*|\d+)\s*[-：:]|$)",
            text,
        )
        if layout == "forward_incomplete":
            trailing = re.search(r"(\d+)-$", text)
            if trailing:
                pairs.append((trailing[1], "官方未提供中文含义"))
        if field["name"] in {"sort", "order"}:
            pairs = [(value, label.split("不传")[0].strip()) for value, label in pairs]
    elif layout == "space":
        pairs = re.findall(r"([A-Za-z][A-Za-z0-9_]*)\s+(?:--)?([\u4e00-\u9fff]+)", text)
    elif layout == "slash":
        pairs = re.findall(r"(\d+)\s*//\s*([\u4e00-\u9fff]+)", text)
    elif layout == "digit_space":
        pairs = re.findall(r"(\d+)\s*([\u4e00-\u9fff]+)", text)
    elif layout == "reverse_equal":
        pairs = [(v, label) for label, v in re.findall(r"([\u4e00-\u9fff]+)=(\d+)", text)]
    elif layout in {"reverse", "reverse_colon"}:
        separator = r"[:：]" if layout == "reverse_colon" else "-"
        pairs = [
            (value, label.split("：")[-1].split(":")[-1].strip())
            for label, value in re.findall(
                r"([^，,；;、]+?)\s*" + separator + r"\s*([A-Za-z][A-Za-z0-9_]*)", text
            )
        ]
    elif layout == "values":
        tail = re.split(r"[:：]", text)[-1]
        if field["name"] == "type" and tail.startswith("维度 "):
            tail = tail.removeprefix("维度 ")
        pairs = [(value.strip(), "官方未提供中文含义") for value in re.split(r"[，,、]", tail)]
    converted = []
    for value, label in pairs:
        if field["type"] in {"int", "long", "short", "array<int>", "array<long>"}:
            value = int(value)
        converted.append({"value": value, "label": label.strip()})
    if len(converted) < 2:
        raise ValueError(f"Reviewed enum layout drifted: {field['name']}")
    field["enum_values"] = converted


def prepare_field(field: dict[str, Any]) -> None:
    if field["type"] == "boolean":
        field.pop("enum_values", None)
        return
    for child in field["children"]:
        prepare_field(child)
    text = field["description"]
    # Only complete square-bracket value/label tables qualify for automatic conversion.
    values: list[dict[str, Any]] = []
    for table in re.findall(r"\[([^\[\]]+)\]", text):
        parts = re.split(r"[，,；;、]", table.strip().rstrip(";；"))
        parsed = []
        for part in parts:
            forward = re.fullmatch(r"\s*([A-Za-z0-9_]+)\s*[-:：]\s*(.+?)\s*", part)
            reverse = re.fullmatch(r"\s*(.+?)\s*[:：]\s*([A-Za-z0-9_]+)\s*", part)
            if forward:
                value, label = forward.groups()
            elif reverse:
                label, value = reverse.groups()
            else:
                parsed = []
                break
            if field["type"] in {"int", "long", "short", "number", "array<int>", "array<long>"}:
                if not value.isdigit():
                    parsed = []
                    break
                value = int(value)
            parsed.append({"value": value, "label": label})
        if len(parsed) >= 2:
            values = parsed
    if values:
        field["enum_values"] = values


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    for doc in data["documents"]:
        for field in doc["request"]:
            prepare_field(field)

            def apply_layout(item: dict[str, Any], document_id: int = doc["id"]) -> None:
                layout = PROSE_LAYOUTS.get(document_id, {}).get(item["name"])
                if layout:
                    prose(item, layout)
                for child in item["children"]:
                    apply_layout(child, document_id)

            apply_layout(field)
            if doc["id"] == 4645 and field["name"] in {"inboundTypeList", "outboundTypeList"}:
                text = field["description"].split(",", 1)[1]
                field["enum_values"] = [
                    {"value": part.strip().split("-", 1)[0], "label": part.strip().split("-", 1)[1]}
                    for part in text.split(",")
                ]
            if doc["id"] == 6025 and field["name"] == "quality":
                field["enum_values"] = [
                    {"value": "normal", "label": "良品"},
                    {"value": "bad", "label": "次品"},
                ]
        # Keep documented pagination shape, never examples or business rows.
        for field in doc["response"]:
            for child in field["children"]:
                child["children"] = []
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
