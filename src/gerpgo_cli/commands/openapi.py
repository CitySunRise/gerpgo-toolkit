from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer

from gerpgo_cli.output import execute_safely
from gerpgo_cli.runtime import openapi_service
from gerpgo_sdk.common.errors import ValidationError
from gerpgo_sdk.openapi import get_endpoint

app = typer.Typer(help="Use registered read-only Gerpgo OpenAPI endpoints.")
product_app = typer.Typer(help="产品资料。")
inventory_app = typer.Typer(help="产品库存。")
statistics_app = typer.Typer(help="销售、产品、商品和 ASIN 流量统计。")
ads_app = typer.Typer(help="搜索词和关键词表现。")
customer_app = typer.Typer(help="Review 和买家之声。")
finance_app = typer.Typer(help="财务利润分析。")

app.add_typer(product_app, name="product")
app.add_typer(inventory_app, name="inventory")
app.add_typer(statistics_app, name="statistics")
app.add_typer(ads_app, name="ads")
app.add_typer(customer_app, name="customer")
app.add_typer(finance_app, name="finance")


@product_app.command("list")
def product_list(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(
        None, "--input", help="JSON object file, or - for stdin."
    ),
    sku: list[str] | None = typer.Option(None, "--sku"),
    msku: list[str] | None = typer.Option(None, "--msku"),
    platform_msku: list[str] | None = typer.Option(None, "--platform-msku"),
    brand: list[str] | None = typer.Option(None, "--brand"),
    category: list[str] | None = typer.Option(None, "--category"),
    state: int | None = typer.Option(None),
    date_type: int | None = typer.Option(None, "--date-type"),
    start_date: str | None = typer.Option(None, "--start-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(100, "--page-size", min=1, max=100),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
    )


@inventory_app.command("product")
def product_inventory(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    sku: list[str] | None = typer.Option(None, "--sku"),
    asin: list[str] | None = typer.Option(None, "--asin"),
    msku: list[str] | None = typer.Option(None, "--msku"),
    warehouse_id: list[int] | None = typer.Option(None, "--warehouse-id"),
    filter_quantity: bool | None = typer.Option(None, "--filter-quantity/--no-filter-quantity"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(20, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "product-inventory",
        profile,
        input_file,
        {
            "skuList": sku,
            "asinList": asin,
            "mskuList": msku,
            "warehouseIds": warehouse_id,
            "filterQuantity": filter_quantity,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
    )


@statistics_app.command("sales-performance")
def sales_performance(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    group_by_type: str | None = typer.Option(None, "--group-by-type"),
    currency: str | None = typer.Option(None, "--currency"),
    begin_date: str | None = typer.Option(None, "--begin-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    view_type: str | None = typer.Option(None, "--view-type"),
    sku: str | None = typer.Option(None),
    asin: str | None = typer.Option(None),
    msku: str | None = typer.Option(None),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(20, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    currency: str | None = typer.Option(None, "--currency"),
    begin_date: str | None = typer.Option(None, "--begin-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(10, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    group_by_type: str | None = typer.Option(None, "--group-by-type"),
    currency: str | None = typer.Option(None, "--currency"),
    begin_date: str | None = typer.Option(None, "--begin-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    is_show_total: bool | None = typer.Option(None, "--show-total/--no-show-total"),
    market_id: list[int] | None = typer.Option(None, "--market-id"),
    asin: list[str] | None = typer.Option(None, "--asin"),
    msku: list[str] | None = typer.Option(None, "--msku"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(20, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
            "asinList": asin,
            "mskuList": msku,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
    )


@statistics_app.command("asin-traffic-statistics")
def asin_traffic_statistics(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    currency: str | None = typer.Option(None, "--currency"),
    begin_date: str | None = typer.Option(None, "--begin-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    view_type: str | None = typer.Option(None, "--view-type"),
    market_id: list[int] | None = typer.Option(None, "--market-id"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(10, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
    )


@statistics_app.command("asin-traffic-data")
def asin_traffic_data(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    currency: str | None = typer.Option(None, "--currency"),
    begin_date: str | None = typer.Option(None, "--begin-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    market_id: list[int] | None = typer.Option(None, "--market-id"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(10, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
    )


@ads_app.command("search-term-performance")
def search_term_performance(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    market_id: int | None = typer.Option(None, "--market-id"),
    start_date: str | None = typer.Option(None, "--start-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(20, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
    )


@ads_app.command("keyword-performance")
def keyword_performance(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    market_id: int | None = typer.Option(None, "--market-id"),
    start_date: str | None = typer.Option(None, "--start-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(20, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
    )


@customer_app.command("review")
def review(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    asin: list[str] | None = typer.Option(None, "--asin"),
    market_id: list[int] | None = typer.Option(None, "--market-id"),
    review_date_begin: str | None = typer.Option(None, "--review-date-begin"),
    review_date_end: str | None = typer.Option(None, "--review-date-end"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(20, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "review",
        profile,
        input_file,
        {
            "asins": asin,
            "marketIds": market_id,
            "reviewDateBegin": review_date_begin,
            "reviewDateEnd": review_date_end,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
    )


@customer_app.command("buyer-voice")
def buyer_voice(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    asin: list[str] | None = typer.Option(None, "--asin"),
    sku: list[str] | None = typer.Option(None, "--sku"),
    msku: list[str] | None = typer.Option(None, "--msku"),
    market_id: list[int] | None = typer.Option(None, "--market-id"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(20, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _query(
        "buyer-voice",
        profile,
        input_file,
        {"asins": asin, "skus": sku, "mskus": msku, "marketIds": market_id},
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
    )


@finance_app.command("profit-analysis-v2")
def profit_analysis_v2(
    profile: str = typer.Option(..., envvar="GERPGO_PROFILE"),
    input_file: str | None = typer.Option(None, "--input"),
    query_type: str | None = typer.Option(None, "--query-type"),
    cost_values: int | None = typer.Option(None, "--cost-values"),
    date_type: int | None = typer.Option(None, "--date-type"),
    currency: str | None = typer.Option(None, "--currency"),
    month_date: str | None = typer.Option(None, "--month-date"),
    start_date: str | None = typer.Option(None, "--start-date"),
    end_date: str | None = typer.Option(None, "--end-date"),
    market_id: list[int] | None = typer.Option(None, "--market-id"),
    asin: list[str] | None = typer.Option(None, "--asin"),
    sku: list[str] | None = typer.Option(None, "--sku"),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(20, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(10, "--max-pages", min=1),
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
            "asinList": asin,
            "skuList": sku,
        },
        page,
        page_size,
        all_pages,
        max_pages,
        output_format,
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
) -> None:
    spec = get_endpoint(endpoint_key)

    def operation() -> Any:
        payload = _load_payload(input_file)
        for key, value in overrides.items():
            if value is not None and value != []:
                payload[key] = value
        if "pageInfo" not in payload:
            payload.setdefault("page", page)
            payload.setdefault("pagesize", page_size)
        return openapi_service(profile).query(
            spec,
            payload,
            all_pages=all_pages,
            max_pages=max_pages,
        )

    execute_safely(operation, message=spec.official_name, output_format=output_format)


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
