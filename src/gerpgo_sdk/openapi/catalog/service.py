from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from gerpgo_sdk.common.errors import ValidationError

from ..client import OpenApiClient
from ..registry import get_endpoint
from .models import (
    AmazonShopRecord,
    BrandRecord,
    CatalogRecord,
    CategoryRecord,
    MultiPlatformShopRecord,
    ShopNameRecord,
    ShopWarehouseRecord,
    UserRecord,
    WarehouseRecord,
)
from .normalizers import (
    normalize_amazon_shops,
    normalize_brands,
    normalize_categories,
    normalize_multiplatform_shops,
    normalize_shop_names,
    normalize_shop_warehouses,
    normalize_users,
    normalize_warehouses,
)

RecordT = TypeVar("RecordT", bound=CatalogRecord)


class CatalogService:
    def __init__(self, client: OpenApiClient) -> None:
        self.client = client

    def amazon_shops(
        self,
        *,
        market_ids: list[str] | None = None,
        record_date_start: str | None = None,
        record_date_end: str | None = None,
        page: int = 1,
        page_size: int = 100,
        all_pages: bool = False,
        max_pages: int | None = 100,
    ) -> list[AmazonShopRecord]:
        condition = self._compact(
            {
                "marketIds": self._integer_ids(market_ids, "market ID") if market_ids else None,
                "recordDateStart": record_date_start,
                "recordDateEnd": record_date_end,
            }
        )
        return self._paged(
            "catalog-amazon-shops",
            {"page": page, "pagesize": page_size, "condition": condition},
            normalize_amazon_shops,
            all_pages=all_pages,
            max_pages=max_pages,
        )

    def users(self) -> list[UserRecord]:
        return normalize_users(self.client.execute(get_endpoint("catalog-users"), None))

    def warehouses(
        self,
        *,
        warehouse_name: str | None = None,
        warehouse_ids: list[str] | None = None,
        status: str | None = None,
        type_list: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 100,
        all_pages: bool = False,
        max_pages: int | None = 100,
    ) -> list[WarehouseRecord]:
        model = self._compact(
            {
                "warehouseName": warehouse_name,
                "warehouseIdList": (
                    self._integer_ids(warehouse_ids, "warehouse ID") if warehouse_ids else None
                ),
                "status": status,
                "typeList": type_list,
                "startDate": start_date,
                "endDate": end_date,
            }
        )
        return self._paged(
            "catalog-warehouses",
            {"model": model, "page": page, "pagesize": page_size},
            normalize_warehouses,
            all_pages=all_pages,
            max_pages=max_pages,
        )

    def brands(
        self,
        *,
        code: str | None = None,
        name: str | None = None,
        state: str | None = None,
        page: int = 1,
        page_size: int = 100,
        all_pages: bool = False,
        max_pages: int | None = 100,
    ) -> list[BrandRecord]:
        payload = self._compact({"code": code, "name": name, "state": state})
        payload.update({"page": page, "pagesize": page_size})
        return self._paged(
            "catalog-brands",
            payload,
            normalize_brands,
            all_pages=all_pages,
            max_pages=max_pages,
        )

    def categories(
        self,
        *,
        state: str | None = None,
        value_list: list[str] | None = None,
        page: int = 1,
        page_size: int = 100,
        all_pages: bool = False,
        max_pages: int | None = 100,
    ) -> list[CategoryRecord]:
        payload = self._compact({"state": state, "valueList": value_list})
        payload.update({"page": page, "pagesize": page_size})
        return self._paged(
            "catalog-categories",
            payload,
            normalize_categories,
            all_pages=all_pages,
            max_pages=max_pages,
        )

    def multiplatform_shops(self) -> list[MultiPlatformShopRecord]:
        data = self.client.execute(get_endpoint("catalog-multiplatform-shops"), {})
        return normalize_multiplatform_shops(data)

    def amazon_shop_names(self, market_ids: list[str]) -> list[ShopNameRecord]:
        ids = self._integer_ids(market_ids, "market ID")
        data = self.client.execute(get_endpoint("catalog-amazon-shop-names"), {"markerIds": ids})
        return normalize_shop_names(data, market_ids)

    def amazon_shop_warehouses(self, market_ids: list[str]) -> list[ShopWarehouseRecord]:
        ids = self._integer_ids(market_ids, "market ID")
        data = self.client.execute(
            get_endpoint("catalog-amazon-shop-warehouses"), {"marketIdList": ids}
        )
        return normalize_shop_warehouses(data)

    def _paged(
        self,
        endpoint_key: str,
        payload: dict[str, Any],
        normalizer: Callable[[Any], list[RecordT]],
        *,
        all_pages: bool,
        max_pages: int | None,
    ) -> list[RecordT]:
        if max_pages is not None and max_pages < 1:
            raise ValidationError("max_pages must be at least 1.")
        records: list[RecordT] = []
        pages_fetched = 0
        while True:
            data = self.client.execute(get_endpoint(endpoint_key), payload)
            page_records = normalizer(data)
            records.extend(page_records)
            pages_fetched += 1
            if not all_pages or not isinstance(data, dict):
                break
            page = int(payload["page"])
            pagesize = int(payload["pagesize"])
            total = data.get("total")
            if not page_records or (isinstance(total, int | float) and page * pagesize >= total):
                break
            if max_pages is not None and pages_fetched >= max_pages:
                break
            payload = {**payload, "page": page + 1}
        return records

    @staticmethod
    def _compact(values: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in values.items() if value not in (None, [], "")}

    @staticmethod
    def _integer_ids(values: list[str], label: str) -> list[int]:
        try:
            return [int(value) for value in values]
        except ValueError as exc:
            raise ValidationError(f"Each {label} must be an integer represented as text.") from exc
