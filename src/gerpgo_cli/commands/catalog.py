from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer

from gerpgo_cli.output import execute_safely
from gerpgo_cli.runtime import catalog_service
from gerpgo_sdk.openapi import get_endpoint
from gerpgo_sdk.openapi.catalog import CatalogService, dictionaries

app = typer.Typer(help="官方 OpenAPI 目录查询与名称解析数据源；仅输出安全白名单字段。")
amazon_shops_app = typer.Typer(help="亚马逊店铺目录。")
users_app = typer.Typer(help="负责人/用户目录。")
warehouses_app = typer.Typer(help="仓库目录。")
brands_app = typer.Typer(help="品牌目录。")
categories_app = typer.Typer(help="品类目录。")
multiplatform_shops_app = typer.Typer(help="多平台店铺目录。")

app.add_typer(amazon_shops_app, name="amazon-shops")
app.add_typer(users_app, name="users")
app.add_typer(warehouses_app, name="warehouses")
app.add_typer(brands_app, name="brands")
app.add_typer(categories_app, name="categories")
app.add_typer(multiplatform_shops_app, name="multiplatform-shops")

_PROFILE_HELP = "Profile name; precedence: --profile, GERPGO_PROFILE, prod."


def _profile() -> Any:
    return typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    )


def _field_help(endpoint_key: str, field_name: str) -> str:
    return get_endpoint(endpoint_key).field(field_name).help_text()


def _child_help(endpoint_key: str, field_name: str, child_name: str) -> str:
    children = dict(get_endpoint(endpoint_key).field(field_name).children)
    return children[child_name].help_text()


def _emit(
    profile: str,
    action: Callable[[CatalogService], Any],
    message: str,
    output_format: str,
) -> None:
    execute_safely(
        lambda: dictionaries(action(catalog_service(profile))),
        message=message,
        output_format=output_format,
    )


def _exact_name(records: list[Any], name: str | None, *attributes: str) -> list[Any]:
    if name is None:
        return records
    target = name.strip()
    return [
        record
        for record in records
        if target in {str(getattr(record, attribute, "")).strip() for attribute in attributes}
    ]


@amazon_shops_app.command("list")
def amazon_shops_list(
    profile: str = _profile(),
    market_id: list[str] | None = typer.Option(
        None, "--market-id", help=_child_help("catalog-amazon-shops", "condition", "marketIds")
    ),
    record_date_start: str | None = typer.Option(
        None,
        "--record-date-start",
        help=_child_help("catalog-amazon-shops", "condition", "recordDateStart"),
    ),
    record_date_end: str | None = typer.Option(
        None,
        "--record-date-end",
        help=_child_help("catalog-amazon-shops", "condition", "recordDateEnd"),
    ),
    exact_name: str | None = typer.Option(
        None, "--exact-name", help="对安全结果中的 store 或 marketName 精确匹配。"
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(100, "--page-size", min=1, max=100),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(100, "--max-pages", min=1),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _emit(
        profile,
        lambda service: _exact_name(
            service.amazon_shops(
                market_ids=market_id,
                record_date_start=record_date_start,
                record_date_end=record_date_end,
                page=page,
                page_size=page_size,
                all_pages=all_pages,
                max_pages=max_pages,
            ),
            exact_name,
            "store",
            "market_name",
        ),
        "查询亚马逊店铺信息",
        output_format,
    )


@amazon_shops_app.command("names-by-id")
def amazon_shop_names(
    market_id: list[str] = typer.Option(..., "--market-id", help="站点 ID；按文本接收。"),
    profile: str = _profile(),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _emit(
        profile,
        lambda service: service.amazon_shop_names(market_id),
        "根据亚马逊店铺id查询店铺名称",
        output_format,
    )


@amazon_shops_app.command("warehouses-by-id")
def amazon_shop_warehouses(
    market_id: list[str] = typer.Option(..., "--market-id", help="站点 ID；按文本接收。"),
    profile: str = _profile(),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _emit(
        profile,
        lambda service: service.amazon_shop_warehouses(market_id),
        "根据亚马逊店铺id查询仓库信息",
        output_format,
    )


@users_app.command("list")
def users_list(
    profile: str = _profile(),
    exact_name: str | None = typer.Option(
        None, "--exact-name", help="对安全结果中的 name 或 username 精确匹配。"
    ),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _emit(
        profile,
        lambda service: _exact_name(service.users(), exact_name, "name", "username"),
        "查询所有用户列表",
        output_format,
    )


@warehouses_app.command("list")
def warehouses_list(
    profile: str = _profile(),
    name: str | None = typer.Option(None, "--name", help="仓库名称，官方接口为模糊筛选。"),
    exact_name: str | None = typer.Option(
        None, "--exact-name", help="对安全结果中的仓库名称精确匹配。"
    ),
    warehouse_id: list[str] | None = typer.Option(None, "--warehouse-id"),
    status: str | None = typer.Option(
        None, help=_child_help("catalog-warehouses", "model", "status")
    ),
    warehouse_type: list[str] | None = typer.Option(
        None, "--type", help=_child_help("catalog-warehouses", "model", "typeList")
    ),
    start_date: str | None = typer.Option(
        None, "--start-date", help=_child_help("catalog-warehouses", "model", "startDate")
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help=_child_help("catalog-warehouses", "model", "endDate")
    ),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(100, "--page-size", min=1, max=100),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(100, "--max-pages", min=1),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _emit(
        profile,
        lambda service: _exact_name(
            service.warehouses(
                warehouse_name=name,
                warehouse_ids=warehouse_id,
                status=status,
                type_list=warehouse_type,
                start_date=start_date,
                end_date=end_date,
                page=page,
                page_size=page_size,
                all_pages=all_pages,
                max_pages=max_pages,
            ),
            exact_name,
            "name",
        ),
        "查询仓库信息列表",
        output_format,
    )


@brands_app.command("list")
def brands_list(
    profile: str = _profile(),
    code: str | None = typer.Option(None, help=_field_help("catalog-brands", "code")),
    name: str | None = typer.Option(None, help=_field_help("catalog-brands", "name")),
    exact_name: str | None = typer.Option(None, "--exact-name"),
    state: str | None = typer.Option(None, help=_field_help("catalog-brands", "state")),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(100, "--page-size", min=1),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(100, "--max-pages", min=1),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _emit(
        profile,
        lambda service: _exact_name(
            service.brands(
                code=code,
                name=name,
                state=state,
                page=page,
                page_size=page_size,
                all_pages=all_pages,
                max_pages=max_pages,
            ),
            exact_name,
            "name",
        ),
        "查询品牌资料",
        output_format,
    )


@categories_app.command("list")
def categories_list(
    profile: str = _profile(),
    value: list[str] | None = typer.Option(None, "--value", help="品类编码；按文本接收。"),
    exact_name: str | None = typer.Option(None, "--exact-name"),
    state: str | None = typer.Option(None, help=_field_help("catalog-categories", "state")),
    page: int = typer.Option(1, min=1),
    page_size: int = typer.Option(100, "--page-size", min=1, max=100),
    all_pages: bool = typer.Option(False, "--all-pages"),
    max_pages: int = typer.Option(100, "--max-pages", min=1),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _emit(
        profile,
        lambda service: _exact_name(
            service.categories(
                state=state,
                value_list=value,
                page=page,
                page_size=page_size,
                all_pages=all_pages,
                max_pages=max_pages,
            ),
            exact_name,
            "name",
        ),
        "查询品类信息",
        output_format,
    )


@multiplatform_shops_app.command("list")
def multiplatform_shops_list(
    profile: str = _profile(),
    exact_name: str | None = typer.Option(None, "--exact-name"),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    _emit(
        profile,
        lambda service: _exact_name(service.multiplatform_shops(), exact_name, "shop_name"),
        "查询多平台店铺信息",
        output_format,
    )
