from __future__ import annotations

from copy import deepcopy
from math import ceil
from typing import Any

from gerpgo_sdk.common.errors import PageLimitExceededError, ValidationError

from .client import OpenApiClient
from .registry import EndpointSpec


class OpenApiService:
    def __init__(self, client: OpenApiClient) -> None:
        self.client = client

    def query(
        self,
        spec: EndpointSpec,
        payload: dict[str, Any] | None,
        *,
        all_pages: bool = False,
        max_pages: int | None = None,
    ) -> Any:
        if not all_pages:
            return self.client.execute(spec, payload)
        if payload is None:
            raise ValidationError("A bodyless endpoint cannot be paginated.")
        page_limit = spec.default_max_pages if max_pages is None else max_pages
        if page_limit < 1:
            raise ValidationError("max_pages must be at least 1.")
        if not spec.supports_auto_pagination:
            raise ValidationError(f"{spec.official_name} does not support automatic pagination.")
        working = deepcopy(payload)
        if self._page_number(working) != 1:
            raise ValidationError("Automatic full pagination must start from page 1.")
        page_size = self._page_size(working)
        first_page = self._page_data(spec, working)
        rows = list(first_page["rows"])
        pages_fetched = 1
        upstream_total = self._total_records(first_page.get("total"))

        if upstream_total is not None:
            estimated_pages = ceil(upstream_total / page_size) if upstream_total else 0
            estimated_seconds = self._estimated_seconds(spec, estimated_pages)
            if estimated_pages > page_limit:
                raise PageLimitExceededError(
                    f"完整查询预计需要 {estimated_pages} 页，超过默认安全上限 {page_limit}。"
                    "请确认后提高 --max-pages。",
                    details={
                        "total_records": upstream_total,
                        "page_size": page_size,
                        "estimated_pages": estimated_pages,
                        "max_pages": page_limit,
                        "estimated_seconds": estimated_seconds,
                    },
                )
            while pages_fetched < estimated_pages:
                self._increment_page(working)
                page_data = self._page_data(spec, working)
                rows.extend(page_data["rows"])
                pages_fetched += 1
            if len(rows) != upstream_total:
                raise ValidationError(
                    "Full pagination row count did not match the upstream total.",
                    details={
                        "total_records": upstream_total,
                        "rows_fetched": len(rows),
                        "pages_fetched": pages_fetched,
                    },
                )
        else:
            estimated_pages = None
            current_rows = first_page["rows"]
            while current_rows and len(current_rows) >= page_size:
                if pages_fetched >= page_limit:
                    raise PageLimitExceededError(
                        f"完整查询已达到安全上限 {page_limit} 页，但上游未返回 total，"
                        "仍可能存在后续数据。请确认后提高 --max-pages。",
                        details={
                            "total_records": None,
                            "page_size": page_size,
                            "estimated_pages": None,
                            "max_pages": page_limit,
                            "estimated_seconds": self._estimated_seconds(spec, page_limit),
                        },
                    )
                self._increment_page(working)
                page_data = self._page_data(spec, working)
                current_rows = page_data["rows"]
                rows.extend(current_rows)
                pages_fetched += 1
            estimated_seconds = self._estimated_seconds(spec, pages_fetched)

        return {
            "rows": rows,
            "pagination": {
                "total_records": upstream_total if upstream_total is not None else len(rows),
                "page_size": page_size,
                "estimated_pages": estimated_pages,
                "pages_fetched": pages_fetched,
                "rows_fetched": len(rows),
                "estimated_seconds": estimated_seconds,
                "complete": True,
                "truncated": False,
            },
        }

    def _page_data(self, spec: EndpointSpec, payload: dict[str, Any]) -> dict[str, Any]:
        page_data = self.client.execute(spec, payload)
        if not isinstance(page_data, dict) or not isinstance(page_data.get("rows"), list):
            raise ValidationError(
                f"{spec.official_name} did not return a pageable rows collection."
            )
        return page_data

    @staticmethod
    def _total_records(value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValidationError("The upstream pagination total was not numeric.")
        total = int(value)
        if total < 0 or total != value:
            raise ValidationError("The upstream pagination total was not a non-negative integer.")
        return total

    @staticmethod
    def _estimated_seconds(spec: EndpointSpec, pages: int) -> int | float:
        seconds = max(0, pages - 1) * spec.minimum_interval_seconds
        return int(seconds) if seconds.is_integer() else seconds

    @staticmethod
    def _page_size(payload: dict[str, Any]) -> int:
        if isinstance(payload.get("pageInfo"), dict):
            return int(payload["pageInfo"].get("pagesize", 100))
        return int(payload.get("pagesize", 100))

    @staticmethod
    def _page_number(payload: dict[str, Any]) -> int:
        if isinstance(payload.get("pageInfo"), dict):
            return int(payload["pageInfo"].get("page", 1))
        return int(payload.get("page", 1))

    @staticmethod
    def _increment_page(payload: dict[str, Any]) -> None:
        if isinstance(payload.get("pageInfo"), dict):
            payload["pageInfo"]["page"] = int(payload["pageInfo"].get("page", 1)) + 1
        else:
            payload["page"] = int(payload.get("page", 1)) + 1
