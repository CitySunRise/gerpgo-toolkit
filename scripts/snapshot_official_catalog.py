"""Capture public contract metadata only; never copy official request/response examples."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]


def fetch(path: str, **params: Any) -> Any:
    response = requests.get(
        "https://open.gerpgo.com/api/openAdmin/doc/" + path, params=params, timeout=40
    )
    response.raise_for_status()
    result = response.json()
    if result.get("code") != 0:
        raise RuntimeError("Official documentation unavailable")
    return result["data"]


def fields(items: Any) -> list[dict[str, Any]]:
    return [
        {
            "name": x["name"],
            "type": x["type"],
            "must": bool(x.get("must")),
            "description": x.get("description") or "",
            "children": fields(x.get("children") or []),
        }
        for x in items or []
    ]


def main() -> None:
    items = []

    def walk(nodes: Any, prefix: str = "") -> None:
        for node in nodes:
            category = prefix + node["menuName"]
            for item in node.get("apiList") or []:
                items.append(
                    {
                        "id": item["id"],
                        "category": category,
                        "name": item["name"],
                        "path": item["url"],
                    }
                )
            walk(node.get("subMenu") or [], category + "/")

    walk(fetch("tree"))

    def detail(item: dict[str, Any]) -> dict[str, Any]:
        data = fetch("detail", id=item["id"])
        return {
            **item,
            "method": data.get("erpMethod"),
            "erp_name": data.get("erpName"),
            "description": data.get("description"),
            "request": fields(data.get("requestBody")),
            "response": fields(data.get("responseBody")),
            "limit_times": data.get("defaultLimitTimes"),
            "limit_period": data.get("defaultLimitPeriod"),
            "limit_unit": data.get("defaultLimitTypeName"),
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        documents = list(pool.map(detail, items))
    target = ROOT / "src/gerpgo_sdk/openapi/official_catalog.json"
    target.write_text(
        json.dumps(
            {"verified_date": "2026-11-04", "documents": documents}, ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Captured {len(documents)} public metadata contracts; examples excluded.")


if __name__ == "__main__":
    main()
