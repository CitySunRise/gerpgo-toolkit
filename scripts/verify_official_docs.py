#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import sys
from typing import Any

import requests

from gerpgo_sdk.openapi import CURRENCY_ENUM, ENDPOINTS, FieldSpec

DETAIL_URL = "https://open.gerpgo.com/api/openAdmin/doc/detail"
CURRENCY_QA_URL = "https://open.gerpgo.com/api/platform/problemDoc/getDoc/11"


def _official_data(url: str, *, params: dict[str, int] | None = None) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict) or result.get("code") != 0:
        raise RuntimeError(f"Official source {url} returned an invalid result.")
    data = result.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"Official source {url} did not contain a data object.")
    return data


def fetch(document_id: int) -> dict[str, Any]:
    return _official_data(DETAIL_URL, params={"id": document_id})


def interval_seconds(document: dict[str, Any]) -> float:
    times = document.get("defaultLimitTimes")
    period = document.get("defaultLimitPeriod")
    unit = document.get("defaultLimitTypeName")
    if not isinstance(times, int | float) or not isinstance(period, int | float) or times <= 0:
        raise RuntimeError(f"Official document {document.get('id')} has an invalid rate limit.")
    unit_seconds = {"秒": 1.0, "分钟": 60.0, "小时": 3600.0}.get(str(unit))
    if unit_seconds is None:
        raise RuntimeError(f"Official document {document.get('id')} has an unknown limit unit.")
    return float(period) * unit_seconds / float(times)


def _field_contract(field: FieldSpec) -> tuple[str, bool, str]:
    return field.type_name, field.required, field.description


def _official_fields(items: Any, document_id: int) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise RuntimeError(f"Official document {document_id} request fields are not a list.")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            raise RuntimeError(f"Official document {document_id} has an invalid request field.")
        result[str(item["name"])] = item
    return result


def _verify_enum_tokens(
    *, document_id: int, field_name: str, field: FieldSpec, description: str
) -> list[str]:
    findings: list[str] = []
    if field.enum_document_id == 11 or not field.enum_values:
        return findings
    for enum_value in field.enum_values:
        value = str(enum_value.value)
        if value not in description:
            findings.append(
                f"document {document_id} field {field_name} enum value {value!r} disappeared"
            )
        if enum_value.label != "官方未提供中文含义" and enum_value.label not in description:
            findings.append(
                f"document {document_id} field {field_name} enum label "
                f"{enum_value.label!r} disappeared"
            )
    return findings


def _verify_fields(
    *, document_id: int, registered: dict[str, FieldSpec], official_items: Any, prefix: str = ""
) -> list[str]:
    findings: list[str] = []
    official = _official_fields(official_items, document_id)
    if set(official) != set(registered):
        findings.append(
            f"document {document_id} {prefix or 'top-level '}request fields changed; "
            f"expected {sorted(registered)}, got {sorted(official)}"
        )
        return findings
    for name, field in registered.items():
        item = official[name]
        actual_contract = (
            str(item.get("type", "")),
            bool(item.get("must")),
            str(item.get("description", "")),
        )
        expected_contract = _field_contract(field)
        qualified_name = f"{prefix}{name}"
        if actual_contract != expected_contract:
            findings.append(
                f"document {document_id} field {qualified_name}: expected "
                f"{expected_contract!r}, got {actual_contract!r}"
            )
        findings.extend(
            _verify_enum_tokens(
                document_id=document_id,
                field_name=qualified_name,
                field=field,
                description=actual_contract[2],
            )
        )
        children = dict(field.children)
        official_children = item.get("children")
        if children:
            findings.extend(
                _verify_fields(
                    document_id=document_id,
                    registered=children,
                    official_items=official_children,
                    prefix=f"{qualified_name}.",
                )
            )
        elif official_children not in (None, []):
            findings.append(f"document {document_id} field {qualified_name} gained children")
    return findings


def _strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def fetch_currency_qa() -> dict[str, set[str]]:
    document = _official_data(CURRENCY_QA_URL)
    content = document.get("content")
    if not isinstance(content, str):
        raise RuntimeError("Official currency Q&A did not contain HTML content.")
    currencies: dict[str, set[str]] = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", content, flags=re.IGNORECASE | re.DOTALL):
        cells = [
            _strip_tags(cell)
            for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.IGNORECASE | re.DOTALL)
        ]
        if len(cells) >= 2 and re.fullmatch(r"[A-Z]+", cells[0]):
            currencies.setdefault(cells[0], set()).add(cells[1])
    plain_content = _strip_tags(content)
    for value, label in re.findall(r'\(\s*"([A-Z]+)"\s*,\s*"([^"]+)"', plain_content):
        currencies.setdefault(value, set()).add(label)
    if not currencies:
        raise RuntimeError("Official currency Q&A contained no currency rows.")
    return currencies


def _verify_currency_qa() -> list[str]:
    findings: list[str] = []
    official = fetch_currency_qa()
    registered = {str(item.value): item.label for item in CURRENCY_ENUM}
    if set(official) != set(registered):
        findings.append(
            f"currency Q&A values changed; expected {sorted(registered)}, got {sorted(official)}"
        )
    for value in sorted(set(official) & set(registered)):
        if registered[value] not in official[value]:
            findings.append(
                f"currency Q&A label for {value}: expected {registered[value]!r}, "
                f"got {sorted(official[value])!r}"
            )
    return findings


def _response_field_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str):
            names.add(name)
        for child in value.values():
            names.update(_response_field_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(_response_field_names(child))
    return names


def _verify_pagination_contract(spec: Any) -> list[str]:
    findings: list[str] = []
    if not spec.supports_auto_pagination:
        return findings
    if spec.endpoint_group == "business" and spec.default_page_size is None:
        findings.append(f"document {spec.document_id} lacks a business default page size")
    page_size = spec.fields.get("pagesize")
    if page_size is None:
        return findings
    official_max = re.search(r"最大\s*(\d+)", page_size.description)
    documented_max = int(official_max.group(1)) if official_max else None
    if documented_max != spec.official_max_page_size:
        findings.append(
            f"document {spec.document_id} official max page size separation changed; "
            f"description={documented_max}, contract={spec.official_max_page_size}"
        )
    official_recommended = re.search(r"建议不超过\s*(\d+)", page_size.description)
    documented_recommended = int(official_recommended.group(1)) if official_recommended else None
    if documented_recommended != spec.official_recommended_page_size:
        findings.append(
            f"document {spec.document_id} official recommended page size separation changed; "
            f"description={documented_recommended}, "
            f"contract={spec.official_recommended_page_size}"
        )
    if spec.runtime_verified:
        if not (
            spec.runtime_verified_date
            and spec.runtime_verification_note
            and spec.runtime_min_page_size is not None
            and spec.runtime_max_page_size is not None
        ):
            findings.append(
                f"document {spec.document_id} runtime pagination evidence is incomplete"
            )
        if page_size.minimum != spec.runtime_min_page_size:
            findings.append(
                f"document {spec.document_id} runtime minimum is not enforced by the SDK field"
            )
        if page_size.maximum != spec.runtime_max_page_size:
            findings.append(
                f"document {spec.document_id} runtime maximum is not enforced by the SDK field"
            )
    return findings


def verify() -> list[str]:
    findings: list[str] = []
    for spec in ENDPOINTS.values():
        document = fetch(spec.document_id)
        expected = {
            "apiName": spec.official_name,
            "apiUrl": spec.path,
        }
        actual = {
            "apiName": document.get("apiName"),
            "apiUrl": document.get("apiUrl"),
        }
        for key, expected_value in expected.items():
            if actual[key] != expected_value:
                findings.append(
                    f"document {spec.document_id} {key}: expected {expected_value!r}, "
                    f"got {actual[key]!r}"
                )
        metadata_method = str(document.get("erpMethod", "")).casefold()
        if spec.metadata_method_difference:
            if spec.method != "POST" or metadata_method != "get":
                findings.append(
                    f"document {spec.document_id} recorded public POST override changed"
                )
            if not spec.public_method_verified_date:
                findings.append(
                    f"document {spec.document_id} public POST override lacks verification date"
                )
        elif metadata_method != spec.method.casefold():
            findings.append(
                f"document {spec.document_id} erpMethod: expected {spec.method.casefold()!r}, "
                f"got {metadata_method!r}"
            )
        actual_interval = interval_seconds(document)
        if actual_interval != spec.minimum_interval_seconds:
            findings.append(
                f"document {spec.document_id} rate: expected "
                f"{spec.minimum_interval_seconds}, got {actual_interval}"
            )
        findings.extend(
            _verify_fields(
                document_id=spec.document_id,
                registered=dict(spec.fields),
                official_items=document.get("requestBody"),
            )
        )
        response_fields = _response_field_names(document.get("responseBody"))
        missing_response_fields = sorted(set(spec.response_key_fields) - response_fields)
        if missing_response_fields:
            findings.append(
                f"document {spec.document_id} response fields disappeared: "
                f"{missing_response_fields}"
            )
        findings.extend(_verify_pagination_contract(spec))
    findings.extend(_verify_currency_qa())
    return findings


def main() -> int:
    try:
        findings = verify()
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        print(f"Official document verification failed: {exc}", file=sys.stderr)
        return 2
    if findings:
        print("Official document drift detected:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    enum_fields = sum(
        bool(field.enum_values) for spec in ENDPOINTS.values() for field in spec.fields.values()
    )
    print(
        "Official document verification passed: "
        f"{len(ENDPOINTS)} endpoints, {enum_fields} enum fields, and currency Q&A checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
