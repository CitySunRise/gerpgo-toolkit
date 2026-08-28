from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeVar

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

RecordT = TypeVar("RecordT", bound=CatalogRecord)


def _text(value: Any) -> str:
    if value is None or isinstance(value, dict | list):
        return ""
    return str(value)


def _objects(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _rows(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    return _objects(data.get("rows"))


def normalize_amazon_shops(data: Any) -> list[AmazonShopRecord]:
    records: list[AmazonShopRecord] = []
    for parent in _rows(data):
        markets = _objects(parent.get("marketListVos")) or [parent]
        for item in markets:
            records.append(
                AmazonShopRecord(
                    market_id=_text(item.get("marketId")),
                    market_name=_text(item.get("marketName")),
                    store=_text(item.get("store")),
                    country_code=_text(item.get("countryCode")),
                    country_name=_text(item.get("countryName")),
                    area_name=_text(item.get("areaName")),
                    state=_text(item.get("state")),
                )
            )
    return records


def normalize_users(data: Any) -> list[UserRecord]:
    return [
        UserRecord(
            id=_text(item.get("id")),
            name=_text(item.get("name")),
            username=_text(item.get("username")),
            status=_text(item.get("status")),
        )
        for item in _objects(data)
    ]


def normalize_warehouses(data: Any) -> list[WarehouseRecord]:
    return [
        WarehouseRecord(
            id=_text(item.get("id")),
            name=_text(item.get("name")),
            type=_text(item.get("type")),
            status=_text(item.get("status")),
            country=_text(item.get("country")),
            platform_code=_text(item.get("platformCode")),
        )
        for item in _rows(data)
    ]


def normalize_brands(data: Any) -> list[BrandRecord]:
    return [
        BrandRecord(
            code=_text(item.get("code")),
            name=_text(item.get("name")),
            state=_text(item.get("state")),
        )
        for item in _rows(data)
    ]


def normalize_categories(data: Any) -> list[CategoryRecord]:
    return [
        CategoryRecord(
            value=_text(item.get("value") or item.get("id")),
            name=_text(item.get("name")),
            state=_text(item.get("state")),
            parent_category=_text(item.get("parentCategory")),
        )
        for item in _rows(data)
    ]


def normalize_multiplatform_shops(data: Any) -> list[MultiPlatformShopRecord]:
    return [
        MultiPlatformShopRecord(
            shop_id=_text(item.get("shopId")),
            shop_name=_text(item.get("shopName")),
            platform_id=_text(item.get("platformId")),
            country_code=_text(item.get("countryCode")),
            region_name=_text(item.get("regionName")),
            region_cn_name=_text(item.get("regionCnName")),
            status=_text(item.get("status")),
        )
        for item in _objects(data)
    ]


def normalize_shop_names(data: Any, market_ids: Iterable[str]) -> list[ShopNameRecord]:
    ids = list(market_ids)
    if isinstance(data, str):
        names = [part.strip() for part in data.split(",")]
    elif isinstance(data, list):
        names = [_text(item) for item in data]
    else:
        names = []
    return [
        ShopNameRecord(market_id=market_id, market_name=name)
        for market_id, name in zip(ids, names, strict=False)
    ]


def normalize_shop_warehouses(data: Any) -> list[ShopWarehouseRecord]:
    return [
        ShopWarehouseRecord(
            market_id=_text(item.get("marketId")),
            warehouse_id=_text(item.get("warehouseId")),
        )
        for item in _objects(data)
    ]


def dictionaries(records: Iterable[CatalogRecord]) -> list[dict[str, Any]]:
    return [record.to_dict() for record in records]
