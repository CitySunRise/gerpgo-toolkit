from __future__ import annotations

from typing import Any

import pytest

from gerpgo_sdk.common.errors import CatalogAmbiguousError, CatalogNotFoundError
from gerpgo_sdk.openapi import ENDPOINTS
from gerpgo_sdk.openapi.catalog import CatalogResolver, CatalogService
from gerpgo_sdk.openapi.catalog.models import (
    AmazonShopRecord,
    BrandRecord,
    CategoryRecord,
    MultiPlatformShopRecord,
    UserRecord,
    WarehouseRecord,
)
from gerpgo_sdk.openapi.catalog.normalizers import (
    normalize_amazon_shops,
    normalize_users,
    normalize_warehouses,
)


class RecordingClient:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def execute(self, spec: Any, payload: dict[str, Any] | None) -> Any:
        spec.validate_payload(payload)
        self.calls.append((spec.key, payload))
        return self.responses.pop(0)


class ResolverCatalog:
    def __init__(self, shops: list[AmazonShopRecord]) -> None:
        self._shops = shops

    def amazon_shops(self, **kwargs: Any) -> list[AmazonShopRecord]:
        return self._shops

    def warehouses(self, **kwargs: Any) -> list[WarehouseRecord]:
        return [WarehouseRecord("200001", "示例仓", "SELF", "enable", "CN", "AMAZON")]

    def users(self) -> list[UserRecord]:
        return [UserRecord("300001", "示例负责人", "demo.user", "enable")]

    def multiplatform_shops(self) -> list[MultiPlatformShopRecord]:
        return [
            MultiPlatformShopRecord(
                "400001", "示例多平台店铺", "PLATFORM-DEMO", "US", "North", "北美", "1"
            )
        ]

    def brands(self, **kwargs: Any) -> list[BrandRecord]:
        return [BrandRecord("BRAND-DEMO", "示例品牌", "Active")]

    def categories(self, **kwargs: Any) -> list[CategoryRecord]:
        return [CategoryRecord("CATEGORY-DEMO", "示例品类", "Active", "")]


def test_eight_catalog_endpoints_are_registered_as_post() -> None:
    catalog = {key: spec for key, spec in ENDPOINTS.items() if spec.endpoint_group == "catalog"}
    assert len(catalog) == 8
    assert {spec.method for spec in catalog.values()} == {"POST"}
    assert catalog["catalog-users"].request_body_mode == "none"
    assert catalog["catalog-multiplatform-shops"].request_body_mode == "empty_object"
    assert set(catalog["catalog-amazon-shop-names"].fields) == {"markerIds"}
    assert set(catalog["catalog-amazon-shop-warehouses"].fields) == {"marketIdList"}


def test_catalog_service_uses_bodyless_and_empty_object_contracts() -> None:
    client = RecordingClient([[], []])
    service = CatalogService(client)  # type: ignore[arg-type]

    assert service.users() == []
    assert service.multiplatform_shops() == []
    assert client.calls == [
        ("catalog-users", None),
        ("catalog-multiplatform-shops", {}),
    ]


def test_catalog_pagination_reaches_final_page() -> None:
    client = RecordingClient(
        [
            {"rows": [{"code": "BRAND-DEMO-1", "name": "示例品牌一"}], "total": 101},
            {"rows": [{"code": "BRAND-DEMO-2", "name": "示例品牌二"}], "total": 101},
        ]
    )
    records = CatalogService(client).brands(all_pages=True)  # type: ignore[arg-type]

    assert [record.code for record in records] == ["BRAND-DEMO-1", "BRAND-DEMO-2"]
    assert [call[1]["page"] for call in client.calls if call[1] is not None] == [1, 2]


@pytest.mark.parametrize(
    ("method_name", "row_one", "row_two"),
    (
        (
            "amazon_shops",
            {"marketListVos": [{"marketId": 100001, "marketName": "示例店铺一"}]},
            {"marketListVos": [{"marketId": 100002, "marketName": "示例店铺二"}]},
        ),
        ("warehouses", {"id": 200001, "name": "示例仓一"}, {"id": 200002, "name": "示例仓二"}),
        (
            "categories",
            {"value": "CATEGORY-DEMO-1", "name": "示例品类一"},
            {"value": "CATEGORY-DEMO-2", "name": "示例品类二"},
        ),
    ),
)
def test_each_other_catalog_pager_reaches_final_page(
    method_name: str, row_one: dict[str, Any], row_two: dict[str, Any]
) -> None:
    client = RecordingClient(
        [
            {"rows": [row_one], "total": 101},
            {"rows": [row_two], "total": 101},
        ]
    )
    service = CatalogService(client)  # type: ignore[arg-type]

    records = getattr(service, method_name)(all_pages=True)

    assert len(records) == 2
    assert [call[1]["page"] for call in client.calls if call[1] is not None] == [1, 2]


def test_catalog_normalizers_use_strict_safe_whitelists() -> None:
    shops = normalize_amazon_shops(
        {
            "rows": [
                {
                    "marketListVos": [
                        {
                            "marketId": 100001,
                            "marketName": "示例店铺-US",
                            "store": "示例店铺",
                            "countryCode": "US",
                            "publicToken": "REDACTED_OMITTED_FIELD",
                            "refreshToken": "REDACTED_OMITTED_FIELD",
                            "session": "REDACTED_OMITTED_FIELD",
                        }
                    ]
                }
            ]
        }
    )
    users = normalize_users(
        [{"id": 300001, "name": "示例负责人", "phone": "REDACTED_OMITTED_FIELD"}]
    )
    warehouses = normalize_warehouses(
        {
            "rows": [
                {
                    "id": 200001,
                    "name": "示例仓",
                    "street": "REDACTED_OMITTED_FIELD",
                    "appkey": "REDACTED_OMITTED_FIELD",
                }
            ]
        }
    )

    combined = [record.to_dict() for record in [*shops, *users, *warehouses]]
    rendered = repr(combined)
    assert "REDACTED_OMITTED_FIELD" not in rendered
    assert shops[0].market_id == "100001"
    assert users[0].id == "300001"
    assert warehouses[0].id == "200001"


def test_resolver_exact_match_country_disambiguation_and_stable_errors() -> None:
    shops = [
        AmazonShopRecord("100001", "示例店铺-US", "示例店铺", "US", "美国", "北美", "1"),
        AmazonShopRecord("100002", "示例店铺-CA", "示例店铺", "CA", "加拿大", "北美", "1"),
    ]
    resolver = CatalogResolver(ResolverCatalog(shops))  # type: ignore[arg-type]

    assert resolver.amazon_shop(" 示例店铺 ", country_code="US") == "100001"
    assert resolver.warehouse("示例仓") == "200001"
    assert resolver.user("demo.user") == "300001"
    assert resolver.brand("示例品牌") == "BRAND-DEMO"
    assert resolver.category("示例品类") == "CATEGORY-DEMO"
    assert resolver.multiplatform_shop("示例多平台店铺") == {
        "shop_id": "400001",
        "platform_id": "PLATFORM-DEMO",
    }
    with pytest.raises(CatalogAmbiguousError) as ambiguous:
        resolver.amazon_shop("示例店铺")
    assert ambiguous.value.code.value == "GERPGO_CATALOG_AMBIGUOUS"
    assert ambiguous.value.details["candidates"] == [
        {
            "market_name": "示例店铺-US",
            "store": "示例店铺",
            "country_code": "US",
            "country_name": "美国",
        },
        {
            "market_name": "示例店铺-CA",
            "store": "示例店铺",
            "country_code": "CA",
            "country_name": "加拿大",
        },
    ]
    with pytest.raises(CatalogNotFoundError) as missing:
        resolver.amazon_shop("不存在店铺")
    assert missing.value.code.value == "GERPGO_CATALOG_NOT_FOUND"
