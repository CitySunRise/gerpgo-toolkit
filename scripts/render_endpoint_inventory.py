"""Render complete inventory from frozen public metadata and registered SDK contracts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from gerpgo_sdk.openapi import ENDPOINTS
from gerpgo_sdk.openapi.expanded import (
    EXCLUDED_READ_IDS,
    WRITE_IDS,
    catalog_documents,
    field_spec,
    route,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    registered = {spec.document_id: spec for spec in ENDPOINTS.values()}
    lines = [
        "# Official endpoint inventory",
        "",
        "Public documentation checked 2026-11-04.",
        "This is metadata only, with no official examples or account data.",
        "",
        "Registered contracts expose full request fields through capabilities and --input.",
        "Blocked items are not CLI commands. No method or enum is invented.",
        "",
        "| Category | Official name / document | Metadata method | Path | Read/write | CLI | "
        "Contract / pagination / rate | Tests / live | Blocker |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    counts: Counter[str] = Counter()
    for doc in catalog_documents():
        spec = registered.get(doc["id"])
        status = (
            "write" if doc["id"] in WRITE_IDS else "authentication" if doc["id"] == 596 else "read"
        )
        counts[status] += 1
        blocker = ""
        command = "—"
        contract = "not registered"
        tests = "not applicable / not called"
        if spec:
            command = (
                " ".join(spec.cli_route)
                if spec.cli_route
                else "existing v0.2 command (see command-map)"
            )
            contract = (
                f"SDK fields; auto-pages={spec.supports_auto_pagination}; "
                f"size={spec.default_page_size}; interval={spec.minimum_interval_seconds}s"
            )
            tests = "offline contract tests / see live-verification.md"
            counts["registered"] += 1
        elif status == "write":
            blocker = "excluded: changes ERP data"
        elif status == "authentication":
            blocker = "SDK authentication only; never a business raw query"
        elif doc["id"] in EXCLUDED_READ_IDS:
            blocker = "not included in the current release"
            counts["excluded_read"] += 1
        else:
            module, target = route(doc)
            command = f"planned: {module} {target}"
            reasons = []
            if doc["method"] not in {"Post", "Get"}:
                reasons.append(
                    "public method/body transport needs verification against detail metadata"
                )
            if not doc["limit_period"] or not doc["limit_times"]:
                reasons.append("official rate period missing")

            def pending(field: object) -> bool:
                from gerpgo_sdk.openapi import FieldSpec

                assert isinstance(field, FieldSpec)
                return field.enum_status == "documented_text" or any(
                    pending(c) for _, c in field.children
                )

            if any(pending(field_spec(f)) for f in doc["request"]):
                reasons.append("prose enum/combination requires manual contract review")
            blocker = "; ".join(reasons) or "contract pending review"
            counts["blocked_read"] += 1
        text = f"[{doc['name']}](https://open.gerpgo.com/document?id={doc['id']})"
        row = [
            doc["category"],
            text,
            str(doc["method"]),
            f"`{doc['path']}`",
            status,
            command,
            contract,
            tests,
            blocker,
        ]
        lines.append(
            "| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in row) + " |"
        )
    lines.extend(
        [
            "",
            f"Counts: {dict(counts)}",
            "",
            "Old endpoints remain explicitly marked (旧); FBA inventory V2 is preferred over 172.",
            "Document 2453 explicitly supports itemType=2 for transfer cartons.",
            "4645 supports inbound/lock order filters; 6025 supports relatedOrders, but its",
            "business semantics are not asserted equal to core querySerial4Transfer.",
            "No Web business endpoint was migrated: no verified missing requirement justifies it.",
        ]
    )
    target = ROOT / "docs/endpoint-inventory.md"
    target.parent.mkdir(exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(dict(counts))


if __name__ == "__main__":
    main()
