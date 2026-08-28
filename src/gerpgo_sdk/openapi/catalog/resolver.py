from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, TypeVar

from gerpgo_sdk.common.errors import (
    CatalogAmbiguousError,
    CatalogNotFoundError,
    ValidationError,
)

from .service import CatalogService

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ResolutionRelation:
    name_option: str
    id_option: str
    payload_field: str
    catalog_endpoint: str
    match_fields: tuple[str, ...]
    result_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name_option": self.name_option,
            "id_option": self.id_option,
            "payload_field": self.payload_field,
            "catalog_endpoint": self.catalog_endpoint,
            "match_fields": list(self.match_fields),
            "result_fields": list(self.result_fields),
            "matching": "exact_after_trim",
        }


RESOLUTION_RELATIONS = (
    ResolutionRelation(
        "--shop-name",
        "--market-id",
        "marketId/marketIds/marketList",
        "catalog-amazon-shops",
        ("store", "market_name"),
        ("marketId",),
    ),
    ResolutionRelation(
        "catalog multiplatform-shops list --exact-name",
        "catalog output",
        "shopId/platformId",
        "catalog-multiplatform-shops",
        ("shop_name",),
        ("shopId", "platformId"),
    ),
    ResolutionRelation(
        "--warehouse-name",
        "--warehouse-id",
        "warehouseIds",
        "catalog-warehouses",
        ("name",),
        ("warehouseId",),
    ),
    ResolutionRelation(
        "--product-manager-name",
        "--product-manager-id",
        "productManagerAccountIdList",
        "catalog-users",
        ("name", "username"),
        ("id",),
    ),
    ResolutionRelation(
        "--selling-manager-name",
        "--selling-manager-id",
        "sellingManagerIdList",
        "catalog-users",
        ("name", "username"),
        ("id",),
    ),
    ResolutionRelation(
        "--brand-name",
        "--brand",
        "brandList/brands",
        "catalog-brands",
        ("name",),
        ("code",),
    ),
    ResolutionRelation(
        "--category-name",
        "--category/--category-id",
        "categoryList/categoryIds",
        "catalog-categories",
        ("name",),
        ("value",),
    ),
    ResolutionRelation(
        "catalog amazon-shops names-by-id --market-id",
        "--market-id",
        "marketName",
        "catalog-amazon-shop-names",
        ("marketId",),
        ("marketName",),
    ),
    ResolutionRelation(
        "catalog amazon-shops warehouses-by-id --market-id",
        "--market-id",
        "warehouseId",
        "catalog-amazon-shop-warehouses",
        ("marketId",),
        ("warehouseId",),
    ),
)


class CatalogResolver:
    def __init__(self, catalog: CatalogService) -> None:
        self.catalog = catalog

    def amazon_shop(
        self,
        name: str,
        *,
        country: str | None = None,
        country_code: str | None = None,
    ) -> str:
        candidates = self.catalog.amazon_shops(all_pages=True, max_pages=None)
        target = name.strip()
        matches = [
            item for item in candidates if target in {item.store.strip(), item.market_name.strip()}
        ]
        if country:
            matches = [item for item in matches if item.country_name.strip() == country.strip()]
        if country_code:
            matches = [
                item for item in matches if item.country_code.strip() == country_code.strip()
            ]
        return self._single(
            "Amazon shop",
            name,
            matches,
            lambda item: item.market_id,
            candidate=lambda item: {
                "market_name": item.market_name,
                "store": item.store,
                "country_code": item.country_code,
                "country_name": item.country_name,
            },
        )

    def multiplatform_shop(self, name: str) -> dict[str, str]:
        matches = self._exact(self.catalog.multiplatform_shops(), name, lambda item: item.shop_name)
        shop_id = self._single(
            "multi-platform shop",
            name,
            matches,
            lambda item: item.shop_id,
            candidate=lambda item: {
                "shop_name": item.shop_name,
                "platform_id": item.platform_id,
                "country_code": item.country_code,
            },
        )
        selected = next(item for item in matches if item.shop_id == shop_id)
        return {"shop_id": selected.shop_id, "platform_id": selected.platform_id}

    def warehouse(self, name: str) -> str:
        return self._single(
            "warehouse",
            name,
            self._exact(
                self.catalog.warehouses(all_pages=True, max_pages=None),
                name,
                lambda item: item.name,
            ),
            lambda item: item.id,
            candidate=lambda item: {
                "name": item.name,
                "country": item.country,
                "type": item.type,
            },
        )

    def user(self, name: str) -> str:
        target = name.strip()
        matches = [
            item
            for item in self.catalog.users()
            if target in {item.name.strip(), item.username.strip()}
        ]
        return self._single(
            "user",
            name,
            matches,
            lambda item: item.id,
            candidate=lambda item: {"name": item.name, "username": item.username},
        )

    def brand(self, name: str) -> str:
        return self._single(
            "brand",
            name,
            self._exact(
                self.catalog.brands(all_pages=True, max_pages=None),
                name,
                lambda item: item.name,
            ),
            lambda item: item.code,
            candidate=lambda item: {"name": item.name, "state": item.state},
        )

    def category(self, name: str) -> str:
        return self._single(
            "category",
            name,
            self._exact(
                self.catalog.categories(all_pages=True, max_pages=None),
                name,
                lambda item: item.name,
            ),
            lambda item: item.value,
            candidate=lambda item: {
                "name": item.name,
                "parent_category": item.parent_category,
                "state": item.state,
            },
        )

    @staticmethod
    def reject_conflict(identifier: Any, name: Any, label: str) -> None:
        if identifier not in (None, [], "") and name not in (None, [], ""):
            raise ValidationError(f"Use either {label} ID/code or {label} name, not both.")

    @staticmethod
    def _exact(records: Iterable[T], name: str, value: Callable[[T], str]) -> list[T]:
        target = name.strip()
        return [item for item in records if value(item).strip() == target]

    @staticmethod
    def _single(
        label: str,
        supplied_name: str,
        matches: list[T],
        identifier: Callable[[T], str],
        candidate: Callable[[T], dict[str, str]] | None = None,
    ) -> str:
        if not matches:
            raise CatalogNotFoundError(
                f"No exact {label} match was found.",
                details={"resource": label, "supplied_name": supplied_name.strip()},
            )
        identifiers = {identifier(item) for item in matches}
        if len(identifiers) != 1:
            raise CatalogAmbiguousError(
                f"The {label} name is ambiguous; add a disambiguating condition "
                "or use its ID/code.",
                details={
                    "resource": label,
                    "match_count": len(matches),
                    "candidates": [candidate(item) for item in matches] if candidate else [],
                },
            )
        return next(iter(identifiers))


def official_integer(value: str, label: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError(f"{label} must be an integer represented as text.") from exc
