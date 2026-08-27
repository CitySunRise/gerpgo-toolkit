from __future__ import annotations

from copy import deepcopy
from typing import Any

from gerpgo_sdk.common.errors import ValidationError

from .client import OpenApiClient
from .registry import EndpointSpec


class OpenApiService:
    def __init__(self, client: OpenApiClient) -> None:
        self.client = client

    def query(
        self,
        spec: EndpointSpec,
        payload: dict[str, Any],
        *,
        all_pages: bool = False,
        max_pages: int = 10,
    ) -> Any:
        if not all_pages:
            return self.client.execute(spec, payload)
        if max_pages < 1:
            raise ValidationError("max_pages must be at least 1.")
        working = deepcopy(payload)
        rows: list[Any] = []
        pages_fetched = 0
        upstream_total: int | float | None = None
        while pages_fetched < max_pages:
            page_data = self.client.execute(spec, working)
            pages_fetched += 1
            if not isinstance(page_data, dict) or not isinstance(page_data.get("rows"), list):
                raise ValidationError(
                    f"{spec.official_name} did not return a pageable rows collection."
                )
            current_rows = page_data["rows"]
            rows.extend(current_rows)
            total = page_data.get("total")
            if isinstance(total, int | float):
                upstream_total = total
            page_size = self._page_size(working)
            if not current_rows or len(current_rows) < page_size:
                break
            if upstream_total is not None and len(rows) >= upstream_total:
                break
            self._increment_page(working)
        return {
            "rows": rows,
            "pages_fetched": pages_fetched,
            "total": upstream_total if upstream_total is not None else len(rows),
            "truncated": pages_fetched >= max_pages
            and (upstream_total is None or len(rows) < upstream_total),
        }

    @staticmethod
    def _page_size(payload: dict[str, Any]) -> int:
        if isinstance(payload.get("pageInfo"), dict):
            return int(payload["pageInfo"].get("pagesize", 100))
        return int(payload.get("pagesize", 100))

    @staticmethod
    def _increment_page(payload: dict[str, Any]) -> None:
        if isinstance(payload.get("pageInfo"), dict):
            payload["pageInfo"]["page"] = int(payload["pageInfo"].get("page", 1)) + 1
        else:
            payload["page"] = int(payload.get("page", 1)) + 1
