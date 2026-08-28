from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer

from gerpgo_cli.commands.catalog import app as catalog_app
from gerpgo_cli.output import execute_safely
from gerpgo_cli.runtime import catalog_resolver_for_service, openapi_service
from gerpgo_sdk.common.errors import ValidationError
from gerpgo_sdk.openapi import CatalogResolver, get_endpoint
from gerpgo_sdk.openapi.catalog import official_integer

app = typer.Typer(help="Use registered read-only Gerpgo OpenAPI endpoints.")
product_app = typer.Typer(help="产品资料。")
inventory_app = typer.Typer(help="产品库存。")
statistics_app = typer.Typer(help="销售、产品、商品和 ASIN 流量统计。")
ads_app = typer.Typer(help="搜索词和关键词表现。")
customer_app = typer.Typer(help="Review 和买家之声。")
finance_app = typer.Typer(help="财务利润分析。")

_PROFILE_HELP = "Profile name; precedence: --profile, GERPGO_PROFILE, prod."


def _field_help(endpoint_key: str, field_name: str) -> str:
    return get_endpoint(endpoint_key).field(field_name).help_text()


def _page_size_option(endpoint_key: str) -> Any:
    spec = get_endpoint(endpoint_key)
    if spec.default_page_size is None:
        raise RuntimeError(f"Missing default page size for {endpoint_key}.")
    details = ["Records per page for ordinary and full queries"]
    if spec.runtime_verified:
        details.append(
            f"runtime-verified range {spec.effective_runtime_min_page_size}"
            f"..{spec.effective_runtime_max_page_size}"
        )
    if spec.official_max_page_size is not None:
        details.append(f"official documented maximum {spec.official_max_page_size}")
    if spec.official_recommended_page_size is not None:
        details.append(f"official recommended maximum {spec.official_recommended_page_size}")
    return typer.Option(
        spec.default_page_size,
        "--page-size",
        min=spec.effective_runtime_min_page_size,
        max=spec.effective_runtime_max_page_size,
        help="; ".join(details) + ".",
        show_default=True,
    )


def _all_pages_option() -> Any:
    return typer.Option(
        False,
        "--all-pages",
        help="Fetch and merge every page serially; complete queries can take a long time.",
    )


def _max_pages_option(endpoint_key: str) -> Any:
    spec = get_endpoint(endpoint_key)
    return typer.Option(
        spec.default_max_pages,
        "--max-pages",
        min=1,
        help="Safety limit for --all-pages; exceeding it returns a non-zero error.",
        show_default=True,
    )


app.add_typer(product_app, name="product")
app.add_typer(inventory_app, name="inventory")
app.add_typer(statistics_app, name="statistics")
app.add_typer(ads_app, name="ads")
app.add_typer(customer_app, name="customer")
app.add_typer(finance_app, name="finance")
app.add_typer(catalog_app, name="catalog")


@product_app.command("list")
def product_list(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(
        None, "--input", help="JSON object file, or - for stdin."
    ),
    sku: list[str] | None = typer.Option(
        None, "--sku", help=_field_help("product-list", "skuList")
    ),
    msku: list[str] | None = typer.Option(
        None, "--msku", help=_field_help("product-list", "mskuList")
    ),
    platform_msku: list[str] | None = typer.Option(
        None, "--platform-msku", help=_field_help("product-list", "platformMskuList")
    ),
    brand: list[str] | None = typer.Option(
        None, "--brand", help=_field_help("product-list", "brandList")
    ),
    brand_name: list[str] | None = typer.Option(
        None, "--brand-name", help="精确品牌名称；与 --brand 互斥。"
    ),
    category: list[str] | None = typer.Option(
        None, "--category", help=_field_help("product-list", "categoryList")
    ),
    category_name: list[str] | None = typer.Option(
        None, "--category-name", help="精确品类名称；与 --category 互斥。"
    ),
    state: int | None = typer.Option(None, help=_field_help("product-list", "state")),
    date_type: int | None = typer.Option(
        None, "--date-type", help=_field_help("product-list", "dateType")
    ),
    start_date: str | None = typer.Option(
        None, "--start-date", help=_field_help("product-list", "startDate")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("product-list", "endDate")
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("product-list"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("product-list"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    overrides = {
        "skuList": sku,
        "mskuList": msku,
        "platformMskuList": platform_msku,
        "brandList": brand,
        "categoryList": category,
        "state": state,
        "dateType": date_type,
        "startDate": start_date,
        "endDate": end_date,
    }
    _query(
        "product-list",
        profile,
        input_file,
        overrides,
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={
            "brandList": ("brand", brand_name or []),
            "categoryList": ("category", category_name or []),
        },
    )


@inventory_app.command("product")
def product_inventory(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    product_state: int | None = typer.Option(
        None, "--product-state", help=_field_help("product-inventory", "productState")
    ),
    product_type: list[int] | None = typer.Option(
        None, "--product-type", help=_field_help("product-inventory", "productTypeList")
    ),
    state: int | None = typer.Option(None, help=_field_help("product-inventory", "state")),
    sku: list[str] | None = typer.Option(
        None, "--sku", help=_field_help("product-inventory", "skuList")
    ),
    asin: list[str] | None = typer.Option(
        None, "--asin", help=_field_help("product-inventory", "asinList")
    ),
    msku: list[str] | None = typer.Option(
        None, "--msku", help=_field_help("product-inventory", "mskuList")
    ),
    warehouse_id: list[str] | None = typer.Option(
        None, "--warehouse-id", help=_field_help("product-inventory", "warehouseIds")
    ),
    warehouse_name: list[str] | None = typer.Option(
        None, "--warehouse-name", help="精确仓库名称；与 --warehouse-id 互斥。"
    ),
    product_manager_id: list[str] | None = typer.Option(
        None,
        "--product-manager-id",
        help=_field_help("product-inventory", "productManagerAccountIdList"),
    ),
    product_manager_name: list[str] | None = typer.Option(
        None,
        "--product-manager-name",
        help="精确负责人名称或用户名；与 --product-manager-id 互斥。",
    ),
    selling_manager_id: list[str] | None = typer.Option(
        None, "--selling-manager-id", help=_field_help("product-inventory", "sellingManagerIdList")
    ),
    selling_manager_name: list[str] | None = typer.Option(
        None,
        "--selling-manager-name",
        help="精确负责人名称或用户名；与 --selling-manager-id 互斥。",
    ),
    filter_quantity: bool | None = typer.Option(
        None,
        "--filter-quantity/--no-filter-quantity",
        help=_field_help("product-inventory", "filterQuantity"),
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("product-inventory"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("product-inventory"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "product-inventory",
        profile,
        input_file,
        {
            "productState": product_state,
            "productTypeList": product_type,
            "state": state,
            "skuList": sku,
            "asinList": asin,
            "mskuList": msku,
            "warehouseIds": warehouse_id,
            "productManagerAccountIdList": product_manager_id,
            "sellingManagerIdList": selling_manager_id,
            "filterQuantity": filter_quantity,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={
            "warehouseIds": ("warehouse", warehouse_name or []),
            "productManagerAccountIdList": ("user", product_manager_name or []),
            "sellingManagerIdList": ("user", selling_manager_name or []),
        },
    )


@statistics_app.command("sales-performance")
def sales_performance(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    group_by_type: str | None = typer.Option(
        None, "--group-by-type", help=_field_help("sales-performance", "groupByType")
    ),
    currency: str | None = typer.Option(
        None, "--currency", help=_field_help("sales-performance", "showCurrencyType")
    ),
    begin_date: str | None = typer.Option(
        None, "--begin-date", help=_field_help("sales-performance", "beginDate")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("sales-performance", "endDate")
    ),
    view_type: str | None = typer.Option(
        None, "--view-type", help=_field_help("sales-performance", "viewType")
    ),
    sku: str | None = typer.Option(None, help=_field_help("sales-performance", "sku")),
    variation_asin: str | None = typer.Option(
        None, "--variation-asin", help=_field_help("sales-performance", "variationAsin")
    ),
    product_name: str | None = typer.Option(
        None, "--product-name", help=_field_help("sales-performance", "productName")
    ),
    asin: str | None = typer.Option(None, help=_field_help("sales-performance", "asin")),
    msku: str | None = typer.Option(None, help=_field_help("sales-performance", "msku")),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("sales-performance"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("sales-performance"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "sales-performance",
        profile,
        input_file,
        {
            "groupByType": group_by_type,
            "showCurrencyType": currency,
            "beginDate": begin_date,
            "endDate": end_date,
            "viewType": view_type,
            "sku": sku,
            "variationAsin": variation_asin,
            "productName": product_name,
            "asin": asin,
            "msku": msku,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
    )


@statistics_app.command("product-performance")
def product_performance(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    currency: str | None = typer.Option(
        None, "--currency", help=_field_help("product-performance", "showCurrencyType")
    ),
    begin_date: str | None = typer.Option(
        None, "--begin-date", help=_field_help("product-performance", "beginDate")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("product-performance", "endDate")
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("product-performance"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("product-performance"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "product-performance",
        profile,
        input_file,
        {"showCurrencyType": currency, "beginDate": begin_date, "endDate": end_date},
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
    )


@statistics_app.command("listing-performance")
def listing_performance(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    group_by_type: str | None = typer.Option(
        None, "--group-by-type", help=_field_help("listing-performance", "groupByType")
    ),
    currency: str | None = typer.Option(
        None, "--currency", help=_field_help("listing-performance", "showCurrencyType")
    ),
    begin_date: str | None = typer.Option(
        None, "--begin-date", help=_field_help("listing-performance", "beginDate")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("listing-performance", "endDate")
    ),
    is_show_total: bool | None = typer.Option(
        None, "--show-total/--no-show-total", help=_field_help("listing-performance", "isShowTotal")
    ),
    market_id: list[str] | None = typer.Option(
        None, "--market-id", help=_field_help("listing-performance", "marketList")
    ),
    shop_name: list[str] | None = typer.Option(
        None, "--shop-name", help="精确店铺名称；与 --market-id 互斥。"
    ),
    country: str | None = typer.Option(None, help="按官方国家名称消除同名店铺歧义。"),
    country_code: str | None = typer.Option(
        None, "--country-code", help="按官方国家代码消除同名店铺歧义。"
    ),
    sku: str | None = typer.Option(None, help=_field_help("listing-performance", "sku")),
    asin_value: str | None = typer.Option(
        None, "--asin-value", help=_field_help("listing-performance", "asin")
    ),
    asin: list[str] | None = typer.Option(
        None, "--asin", help=_field_help("listing-performance", "asinList")
    ),
    msku_value: str | None = typer.Option(
        None, "--msku-value", help=_field_help("listing-performance", "msku")
    ),
    msku: list[str] | None = typer.Option(
        None, "--msku", help=_field_help("listing-performance", "mskuList")
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("listing-performance"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("listing-performance"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "listing-performance",
        profile,
        input_file,
        {
            "groupByType": group_by_type,
            "showCurrencyType": currency,
            "beginDate": begin_date,
            "endDate": end_date,
            "isShowTotal": is_show_total,
            "marketList": market_id,
            "sku": sku,
            "asin": asin_value,
            "asinList": asin,
            "msku": msku_value,
            "mskuList": msku,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={"marketList": ("shop", shop_name or [])},
        country=country,
        country_code=country_code,
    )


@statistics_app.command("asin-traffic-statistics")
def asin_traffic_statistics(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    currency: str | None = typer.Option(
        None, "--currency", help=_field_help("asin-traffic-statistics", "currency")
    ),
    begin_date: str | None = typer.Option(
        None, "--begin-date", help=_field_help("asin-traffic-statistics", "beginDate")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("asin-traffic-statistics", "endDate")
    ),
    view_type: str | None = typer.Option(
        None, "--view-type", help=_field_help("asin-traffic-statistics", "viewType")
    ),
    market_id: list[str] | None = typer.Option(
        None, "--market-id", help=_field_help("asin-traffic-statistics", "marketList")
    ),
    shop_name: list[str] | None = typer.Option(
        None, "--shop-name", help="精确店铺名称；与 --market-id 互斥。"
    ),
    country: str | None = typer.Option(None, help="按官方国家名称消除同名店铺歧义。"),
    country_code: str | None = typer.Option(None, "--country-code"),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("asin-traffic-statistics"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("asin-traffic-statistics"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "asin-traffic-statistics",
        profile,
        input_file,
        {
            "currency": currency,
            "beginDate": begin_date,
            "endDate": end_date,
            "viewType": view_type,
            "marketList": market_id,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={"marketList": ("shop", shop_name or [])},
        country=country,
        country_code=country_code,
    )


@statistics_app.command("asin-traffic-data")
def asin_traffic_data(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    currency: str | None = typer.Option(
        None, "--currency", help=_field_help("asin-traffic-data", "currency")
    ),
    begin_date: str | None = typer.Option(
        None, "--begin-date", help=_field_help("asin-traffic-data", "beginDate")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("asin-traffic-data", "endDate")
    ),
    market_id: list[str] | None = typer.Option(
        None, "--market-id", help=_field_help("asin-traffic-data", "marketList")
    ),
    shop_name: list[str] | None = typer.Option(
        None, "--shop-name", help="精确店铺名称；与 --market-id 互斥。"
    ),
    country: str | None = typer.Option(None, help="按官方国家名称消除同名店铺歧义。"),
    country_code: str | None = typer.Option(None, "--country-code"),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("asin-traffic-data"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("asin-traffic-data"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "asin-traffic-data",
        profile,
        input_file,
        {
            "currency": currency,
            "beginDate": begin_date,
            "endDate": end_date,
            "marketList": market_id,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={"marketList": ("shop", shop_name or [])},
        country=country,
        country_code=country_code,
    )


@ads_app.command("search-term-performance")
def search_term_performance(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    market_id: str | None = typer.Option(
        None, "--market-id", help=_field_help("search-term-performance", "marketId")
    ),
    shop_name: str | None = typer.Option(
        None, "--shop-name", help="精确店铺名称；与 --market-id 互斥。"
    ),
    country: str | None = typer.Option(None, help="按官方国家名称消除同名店铺歧义。"),
    country_code: str | None = typer.Option(None, "--country-code"),
    start_date: str | None = typer.Option(
        None, "--start-date", help=_field_help("search-term-performance", "startDateData")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("search-term-performance", "endDateData")
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("search-term-performance"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("search-term-performance"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "search-term-performance",
        profile,
        input_file,
        {"marketId": market_id, "startDateData": start_date, "endDateData": end_date},
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={"marketId": ("shop", shop_name)} if shop_name else None,
        country=country,
        country_code=country_code,
    )


@ads_app.command("keyword-performance")
def keyword_performance(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    market_id: str | None = typer.Option(
        None, "--market-id", help=_field_help("keyword-performance", "marketId")
    ),
    shop_name: str | None = typer.Option(
        None, "--shop-name", help="精确店铺名称；与 --market-id 互斥。"
    ),
    country: str | None = typer.Option(None, help="按官方国家名称消除同名店铺歧义。"),
    country_code: str | None = typer.Option(None, "--country-code"),
    start_date: str | None = typer.Option(
        None, "--start-date", help=_field_help("keyword-performance", "startDateData")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("keyword-performance", "endDateData")
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("keyword-performance"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("keyword-performance"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "keyword-performance",
        profile,
        input_file,
        {"marketId": market_id, "startDateData": start_date, "endDateData": end_date},
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={"marketId": ("shop", shop_name)} if shop_name else None,
        country=country,
        country_code=country_code,
    )


@customer_app.command("review")
def review(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    review_id: list[str] | None = typer.Option(
        None, "--review-id", help=_field_help("review", "reviewIds")
    ),
    create_date_begin: str | None = typer.Option(
        None, "--create-date-begin", help=_field_help("review", "createDateBegin")
    ),
    create_date_end: str | None = typer.Option(
        None, "--create-date-end", help=_field_help("review", "createDateEnd")
    ),
    update_date_begin: str | None = typer.Option(
        None, "--update-date-begin", help=_field_help("review", "updateDateBegin")
    ),
    update_date_end: str | None = typer.Option(
        None, "--update-date-end", help=_field_help("review", "updateDateEnd")
    ),
    review_date_begin: str | None = typer.Option(
        None, "--review-date-begin", help=_field_help("review", "reviewDateBegin")
    ),
    review_date_end: str | None = typer.Option(
        None, "--review-date-end", help=_field_help("review", "reviewDateEnd")
    ),
    market_id: list[str] | None = typer.Option(
        None, "--market-id", help=_field_help("review", "marketIds")
    ),
    shop_name: list[str] | None = typer.Option(
        None, "--shop-name", help="精确店铺名称；与 --market-id 互斥。"
    ),
    country: str | None = typer.Option(None, help="按官方国家名称消除同名店铺歧义。"),
    country_code: str | None = typer.Option(None, "--country-code"),
    state: list[int] | None = typer.Option(None, "--state", help=_field_help("review", "states")),
    result: list[int] | None = typer.Option(
        None, "--result", help=_field_help("review", "results")
    ),
    order_id: list[str] | None = typer.Option(
        None, "--order-id", help=_field_help("review", "orderIds")
    ),
    name_match_type: str | None = typer.Option(
        None, "--name-match-type", help=_field_help("review", "nameMatchType")
    ),
    asin: list[str] | None = typer.Option(None, "--asin", help=_field_help("review", "asins")),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("review"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("review"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "review",
        profile,
        input_file,
        {
            "reviewIds": review_id,
            "createDateBegin": create_date_begin,
            "createDateEnd": create_date_end,
            "updateDateBegin": update_date_begin,
            "updateDateEnd": update_date_end,
            "asins": asin,
            "marketIds": market_id,
            "reviewDateBegin": review_date_begin,
            "reviewDateEnd": review_date_end,
            "states": state,
            "results": result,
            "orderIds": order_id,
            "nameMatchType": name_match_type,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={"marketIds": ("shop", shop_name or [])},
        country=country,
        country_code=country_code,
    )


@customer_app.command("buyer-voice")
def buyer_voice(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    pcx_health: str | None = typer.Option(
        None, "--pcx-health", help=_field_help("buyer-voice", "pcxHealth")
    ),
    market_id: list[str] | None = typer.Option(
        None, "--market-id", help=_field_help("buyer-voice", "marketIds")
    ),
    shop_name: list[str] | None = typer.Option(
        None, "--shop-name", help="精确店铺名称；与 --market-id 互斥。"
    ),
    country: str | None = typer.Option(None, help="按官方国家名称消除同名店铺歧义。"),
    country_code: str | None = typer.Option(None, "--country-code"),
    product_name: str | None = typer.Option(
        None, "--product-name", help=_field_help("buyer-voice", "productName")
    ),
    sku: list[str] | None = typer.Option(None, "--sku", help=_field_help("buyer-voice", "skus")),
    msku: list[str] | None = typer.Option(None, "--msku", help=_field_help("buyer-voice", "mskus")),
    asin: list[str] | None = typer.Option(None, "--asin", help=_field_help("buyer-voice", "asins")),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("buyer-voice"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("buyer-voice"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "buyer-voice",
        profile,
        input_file,
        {
            "pcxHealth": pcx_health,
            "marketIds": market_id,
            "productName": product_name,
            "skus": sku,
            "mskus": msku,
            "asins": asin,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={"marketIds": ("shop", shop_name or [])},
        country=country,
        country_code=country_code,
    )


@finance_app.command("profit-analysis-v2")
def profit_analysis_v2(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    input_file: str | None = typer.Option(None, "--input"),
    query_type: str | None = typer.Option(
        None, "--query-type", help=_field_help("profit-analysis-v2", "queryType")
    ),
    cost_values: int | None = typer.Option(
        None, "--cost-values", help=_field_help("profit-analysis-v2", "costValues")
    ),
    date_type: int | None = typer.Option(
        None, "--date-type", help=_field_help("profit-analysis-v2", "dateType")
    ),
    currency: str | None = typer.Option(
        None, "--currency", help=_field_help("profit-analysis-v2", "currency")
    ),
    month_date: str | None = typer.Option(
        None, "--month-date", help=_field_help("profit-analysis-v2", "monthDate")
    ),
    start_date: str | None = typer.Option(
        None, "--start-date", help=_field_help("profit-analysis-v2", "startDate")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_field_help("profit-analysis-v2", "endDate")
    ),
    market_id: list[str] | None = typer.Option(
        None, "--market-id", help=_field_help("profit-analysis-v2", "marketIds")
    ),
    shop_name: list[str] | None = typer.Option(
        None, "--shop-name", help="精确店铺名称；与 --market-id 互斥。"
    ),
    country: str | None = typer.Option(None, help="按官方国家名称消除同名店铺歧义。"),
    country_code: str | None = typer.Option(None, "--country-code"),
    category_id: list[str] | None = typer.Option(
        None, "--category-id", help=_field_help("profit-analysis-v2", "categoryIds")
    ),
    category_name: list[str] | None = typer.Option(
        None, "--category-name", help="精确品类名称；与 --category-id 互斥。"
    ),
    brand: list[str] | None = typer.Option(
        None, "--brand", help=_field_help("profit-analysis-v2", "brands")
    ),
    brand_name: list[str] | None = typer.Option(
        None, "--brand-name", help="精确品牌名称；与 --brand 互斥。"
    ),
    decimal_places: int | None = typer.Option(
        None,
        "--decimal-places",
        min=2,
        max=8,
        help=_field_help("profit-analysis-v2", "decimalPlaces"),
    ),
    footer_expand_details: bool | None = typer.Option(
        None,
        "--footer-expand-details/--no-footer-expand-details",
        help=_field_help("profit-analysis-v2", "footerExpandDetails"),
    ),
    platform_code: list[str] | None = typer.Option(
        None, "--platform-code", help=_field_help("profit-analysis-v2", "platformCodes")
    ),
    query_msku: list[str] | None = typer.Option(
        None, "--query-msku", help=_field_help("profit-analysis-v2", "queryMskuList")
    ),
    sku: list[str] | None = typer.Option(
        None, "--sku", help=_field_help("profit-analysis-v2", "skuList")
    ),
    asin: list[str] | None = typer.Option(
        None, "--asin", help=_field_help("profit-analysis-v2", "asinList")
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = _page_size_option("profit-analysis-v2"),
    all_pages: bool = _all_pages_option(),
    max_pages: int = _max_pages_option("profit-analysis-v2"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "profit-analysis-v2",
        profile,
        input_file,
        {
            "queryType": query_type,
            "costValues": cost_values,
            "dateType": date_type,
            "currency": currency,
            "monthDate": month_date,
            "startDate": start_date,
            "endDate": end_date,
            "marketIds": market_id,
            "categoryIds": category_id,
            "brands": brand,
            "decimalPlaces": decimal_places,
            "footerExpandDetails": footer_expand_details,
            "platformCodes": platform_code,
            "queryMskuList": query_msku,
            "skuList": sku,
            "asinList": asin,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
        resolutions={
            "marketIds": ("shop", shop_name or []),
            "categoryIds": ("category", category_name or []),
            "brands": ("brand", brand_name or []),
        },
        country=country,
        country_code=country_code,
    )


def _query(
    endpoint_key: str,
    profile: str,
    input_file: str | None,
    overrides: dict[str, Any],
    page: int,
    page_size: int,
    all_pages: bool,
    max_pages: int,
    output_format: str,
    resolutions: dict[str, tuple[str, str | list[str]]] | None = None,
    country: str | None = None,
    country_code: str | None = None,
) -> None:
    spec = get_endpoint(endpoint_key)

    def operation() -> Any:
        service = openapi_service(profile)
        payload = _load_payload(input_file)
        for key, value in overrides.items():
            if value is not None and value != []:
                payload[key] = value
        active_resolutions = {
            field_name: resolution
            for field_name, resolution in (resolutions or {}).items()
            if resolution[1] not in (None, [], "")
        }
        if active_resolutions:
            _apply_resolutions(
                payload,
                active_resolutions,
                catalog_resolver_for_service(service),
                spec=spec,
                country=country,
                country_code=country_code,
            )
        _coerce_dynamic_numeric_identifiers(spec, payload)
        if "pageInfo" not in payload:
            payload.setdefault("page", page)
            payload.setdefault("pagesize", page_size)
        return service.query(
            spec,
            payload,
            all_pages=all_pages,
            max_pages=max_pages,
        )

    execute_safely(operation, message=spec.official_name, output_format=output_format)


def _apply_resolutions(
    payload: dict[str, Any],
    resolutions: dict[str, tuple[str, str | list[str]]],
    resolver: CatalogResolver,
    *,
    spec: Any,
    country: str | None,
    country_code: str | None,
) -> None:
    for field_name, (kind, supplied_names) in resolutions.items():
        names = supplied_names if isinstance(supplied_names, list) else [supplied_names]
        if not names:
            continue
        resolver.reject_conflict(payload.get(field_name), names, kind)
        resolved: list[str] = []
        for name in names:
            if kind == "shop":
                resolved.append(
                    resolver.amazon_shop(name, country=country, country_code=country_code)
                )
            elif kind == "warehouse":
                resolved.append(resolver.warehouse(name))
            elif kind == "user":
                resolved.append(resolver.user(name))
            elif kind == "brand":
                resolved.append(resolver.brand(name))
            elif kind == "category":
                resolved.append(resolver.category(name))
            else:
                raise ValidationError(f"Unsupported catalog resolver: {kind}.")
        field = spec.field(field_name)
        payload[field_name] = resolved if field.type_name.startswith("array<") else resolved[0]


def _coerce_dynamic_numeric_identifiers(spec: Any, payload: dict[str, Any]) -> None:
    for name, field in spec.fields.items():
        if not field.dynamic_identifier or name not in payload:
            continue
        value = payload[name]
        if field.type_name in {"int", "long"} and isinstance(value, str):
            payload[name] = official_integer(value, name)
        elif field.type_name in {"array<int>", "array<long>"} and isinstance(value, list):
            payload[name] = [
                official_integer(item, name) if isinstance(item, str) else item for item in value
            ]


def _load_payload(input_file: str | None) -> dict[str, Any]:
    if input_file is None:
        return {}
    try:
        text = (
            sys.stdin.read() if input_file == "-" else Path(input_file).read_text(encoding="utf-8")
        )
        data = json.loads(text)
    except (OSError, ValueError) as exc:
        raise ValidationError("Unable to read the JSON input object.") from exc
    if not isinstance(data, dict):
        raise ValidationError("--input must contain one JSON object.")
    return data
