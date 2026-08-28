from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, cast


class CatalogRecord:
    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(cast(Any, self))}


@dataclass(frozen=True, slots=True)
class AmazonShopRecord(CatalogRecord):
    market_id: str
    market_name: str
    store: str
    country_code: str
    country_name: str
    area_name: str
    state: str


@dataclass(frozen=True, slots=True)
class UserRecord(CatalogRecord):
    id: str
    name: str
    username: str
    status: str


@dataclass(frozen=True, slots=True)
class WarehouseRecord(CatalogRecord):
    id: str
    name: str
    type: str
    status: str
    country: str
    platform_code: str


@dataclass(frozen=True, slots=True)
class BrandRecord(CatalogRecord):
    code: str
    name: str
    state: str


@dataclass(frozen=True, slots=True)
class CategoryRecord(CatalogRecord):
    value: str
    name: str
    state: str
    parent_category: str


@dataclass(frozen=True, slots=True)
class MultiPlatformShopRecord(CatalogRecord):
    shop_id: str
    shop_name: str
    platform_id: str
    country_code: str
    region_name: str
    region_cn_name: str
    status: str


@dataclass(frozen=True, slots=True)
class ShopNameRecord(CatalogRecord):
    market_id: str
    market_name: str


@dataclass(frozen=True, slots=True)
class ShopWarehouseRecord(CatalogRecord):
    market_id: str
    warehouse_id: str
