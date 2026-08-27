#!/usr/bin/env python3
from __future__ import annotations

import sys
from typing import Any

import requests

from gerpgo_sdk.openapi import ENDPOINTS

DETAIL_URL = "https://open.gerpgo.com/api/openAdmin/doc/detail"


def fetch(document_id: int) -> dict[str, Any]:
    response = requests.get(DETAIL_URL, params={"id": document_id}, timeout=30)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict) or result.get("code") != 0:
        raise RuntimeError(f"Official document {document_id} returned an invalid result.")
    data = result.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"Official document {document_id} did not contain a data object.")
    return data


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


def verify() -> list[str]:
    findings: list[str] = []
    for spec in ENDPOINTS.values():
        document = fetch(spec.document_id)
        expected = {
            "apiName": spec.official_name,
            "erpMethod": spec.method.casefold(),
            "apiUrl": spec.path,
        }
        actual = {
            "apiName": document.get("apiName"),
            "erpMethod": str(document.get("erpMethod", "")).casefold(),
            "apiUrl": document.get("apiUrl"),
        }
        for key, expected_value in expected.items():
            if actual[key] != expected_value:
                findings.append(
                    f"document {spec.document_id} {key}: expected {expected_value!r}, "
                    f"got {actual[key]!r}"
                )
        actual_interval = interval_seconds(document)
        if actual_interval != spec.minimum_interval_seconds:
            findings.append(
                f"document {spec.document_id} rate: expected "
                f"{spec.minimum_interval_seconds}, got {actual_interval}"
            )
        body = document.get("requestBody")
        if not isinstance(body, list):
            findings.append(f"document {spec.document_id} requestBody is not a list")
            continue
        actual_fields = {
            str(item.get("name")): bool(item.get("must"))
            for item in body
            if isinstance(item, dict) and item.get("name")
        }
        expected_fields = {name: field.required for name, field in spec.fields.items()}
        if actual_fields != expected_fields:
            findings.append(
                f"document {spec.document_id} top-level request fields changed; review required"
            )
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
    print(f"Official document verification passed: {len(ENDPOINTS)} endpoints checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
