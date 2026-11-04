from __future__ import annotations

from copy import deepcopy
from math import ceil
from typing import Any

from gerpgo_sdk.common.errors import PageLimitExceededError, ValidationError
from gerpgo_sdk.common.redaction import BusinessResponse

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
        response_mode: str = "data",
    ) -> Any:
        if response_mode not in {"data", "raw"}:
            raise ValidationError("--response must be data or raw.")
        if not all_pages:
            if response_mode == "raw":
                return self.client.execute(spec, payload, response_mode="raw")
            return self.client.execute(spec, payload)
        if payload is None:
            raise ValidationError("A bodyless endpoint cannot be paginated.")
        if spec.pagination_mode == "cursor":
            return self._cursor_query(
                spec, payload, max_pages=max_pages, response_mode=response_mode
            )
        page_limit = spec.default_max_pages if max_pages is None else max_pages
        if page_limit < 1:
            raise ValidationError("max_pages must be at least 1.")
        if not spec.supports_auto_pagination:
            raise ValidationError(f"{spec.official_name} does not support automatic pagination.")
        working = deepcopy(payload)
        if self._page_number(working, spec) != 1:
            raise ValidationError("Automatic full pagination must start from page 1.")
        page_size = self._page_size(working, spec)
        raw_pages: list[dict[str, Any]] = []

        def fetch_page() -> dict[str, Any]:
            if response_mode == "raw":
                raw = self.client.execute(spec, deepcopy(working), response_mode="raw")
                raw_pages.append(raw)
                return self._validated_page_data(spec, raw.get("data"))
            return self._page_data(spec, working)

        first_page = fetch_page()
        effective_size = first_page.get("pagesize")
        if effective_size is not None:
            if (
                isinstance(effective_size, bool)
                or not isinstance(effective_size, int)
                or effective_size < 1
            ):
                raise ValidationError("Invalid upstream pagination page size.")
            page_size = effective_size
        rows_key = spec.response_rows_key or "rows"
        rows = list(first_page[rows_key])
        pages_fetched = 1
        upstream_total = self._total_records(first_page.get(spec.response_total_key or "total"))

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
                self._increment_page(working, spec)
                page_data = fetch_page()
                rows.extend(page_data[rows_key])
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
            current_rows = first_page[rows_key]
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
                self._increment_page(working, spec)
                page_data = fetch_page()
                current_rows = page_data[rows_key]
                rows.extend(current_rows)
                pages_fetched += 1
            estimated_seconds = self._estimated_seconds(spec, pages_fetched)

        result = {
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
        if response_mode == "raw":
            return BusinessResponse(pages=raw_pages, pagination=result["pagination"])
        return result

    def _cursor_query(
        self,
        spec: EndpointSpec,
        payload: dict[str, Any],
        *,
        max_pages: int | None,
        response_mode: str,
    ) -> Any:
        limit = spec.default_max_pages if max_pages is None else max_pages
        spec.validate_payload(payload)
        if limit < 1 or payload.get("nextId") is not None:
            raise ValidationError(
                "Full cursor pagination requires a positive limit and no initial nextId."
            )
        working = deepcopy(payload)
        size = int(working["count"])
        rows: list[Any] = []
        pages = []
        cursors = set()
        for page_number in range(1, limit + 1):
            raw = self.client.execute(spec, working, response_mode="raw")
            batch = raw.get("data")
            if not isinstance(batch, list):
                raise ValidationError("Cursor query did not return a documented data array.")
            pages.append(raw)
            rows.extend(batch)
            if len(batch) < size:
                pagination = {
                    "total_records": len(rows),
                    "page_size": size,
                    "estimated_pages": None,
                    "pages_fetched": page_number,
                    "rows_fetched": len(rows),
                    "estimated_seconds": self._estimated_seconds(spec, page_number),
                    "complete": True,
                    "truncated": False,
                }
                if response_mode == "raw":
                    return BusinessResponse(pages=pages, pagination=pagination)
                return {"rows": rows, "pagination": pagination}
            cursor = raw.get("extObj")
            if isinstance(cursor, bool) or not isinstance(cursor, int) or cursor in cursors:
                raise ValidationError(
                    "The documented next cursor was missing, invalid or repeated."
                )
            cursors.add(cursor)
            working["nextId"] = cursor
        raise PageLimitExceededError(
            "Cursor query reached --max-pages before completion; confirm a higher limit.",
            details={
                "total_records": None,
                "estimated_pages": None,
                "page_size": size,
                "max_pages": limit,
                "estimated_seconds": self._estimated_seconds(spec, limit),
            },
        )

    def _page_data(self, spec: EndpointSpec, payload: dict[str, Any]) -> dict[str, Any]:
        page_data = self.client.execute(spec, deepcopy(payload))
        return self._validated_page_data(spec, page_data)

    @staticmethod
    def _validated_page_data(spec: EndpointSpec, page_data: Any) -> dict[str, Any]:
        if not isinstance(page_data, dict) or not isinstance(
            page_data.get(spec.response_rows_key or "rows"), list
        ):
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
    def _page_size(payload: dict[str, Any], spec: EndpointSpec) -> int:
        if isinstance(payload.get("pageInfo"), dict):
            return int(payload["pageInfo"].get("pagesize", 100))
        return int(payload.get(spec.request_page_size_field, spec.default_page_size or 100))

    @staticmethod
    def _page_number(payload: dict[str, Any], spec: EndpointSpec) -> int:
        if isinstance(payload.get("pageInfo"), dict):
            return int(payload["pageInfo"].get("page", 1))
        return int(payload.get(spec.request_page_field, 1))

    @staticmethod
    def _increment_page(payload: dict[str, Any], spec: EndpointSpec) -> None:
        if isinstance(payload.get("pageInfo"), dict):
            payload["pageInfo"]["page"] = int(payload["pageInfo"].get("page", 1)) + 1
        else:
            payload[spec.request_page_field] = int(payload.get(spec.request_page_field, 1)) + 1
