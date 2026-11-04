"""Add explicit raw output to the existing normalized directory commands."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, get_type_hints

import typer

from gerpgo_cli.output import execute_safely
from gerpgo_cli.runtime import openapi_service
from gerpgo_sdk.common.errors import ValidationError
from gerpgo_sdk.openapi import get_endpoint

FIELDS = {
    "catalog-amazon-shops": {
        "market_id": "condition.marketIds",
        "record_date_start": "condition.recordDateStart",
        "record_date_end": "condition.recordDateEnd",
    },
    "catalog-amazon-shop-names": {"market_id": "markerIds"},
    "catalog-amazon-shop-warehouses": {"market_id": "marketIdList"},
    "catalog-users": {},
    "catalog-warehouses": {
        "name": "model.warehouseName",
        "warehouse_id": "model.warehouseIdList",
        "status": "model.status",
        "warehouse_type": "model.typeList",
        "start_date": "model.startDate",
        "end_date": "model.endDate",
    },
    "catalog-brands": {"code": "code", "name": "name", "state": "state"},
    "catalog-categories": {"value": "valueList", "state": "state"},
    "catalog-multiplatform-shops": {},
}


def raw_output(endpoint_key: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorate(function: Callable[..., Any]) -> Callable[..., Any]:
        signature = inspect.signature(function)
        hints = get_type_hints(function)

        @wraps(function)
        def wrapper(**options: Any) -> Any:
            mode = options.pop("response_mode", "data")
            input_file = options.pop("raw_input", None)
            if mode == "data":
                if input_file:

                    def invalid_input() -> None:
                        raise ValidationError("Directory --input requires --response raw.")

                    return execute_safely(invalid_input)
                return function(**options)

            def operation() -> Any:
                if mode != "raw":
                    raise ValidationError("--response must be data or raw.")
                if options.get("exact_name"):
                    raise ValidationError(
                        "--exact-name is for normalized results; use official filters with raw."
                    )
                from gerpgo_sdk.openapi.catalog import official_integer

                from .openapi import _load_payload

                spec = get_endpoint(endpoint_key)
                payload = _load_payload(input_file)
                for name in ("page", "pagesize"):
                    option_name = "page_size" if name == "pagesize" else name
                    if name in spec.fields:
                        payload.setdefault(
                            name, options.get(option_name, 100 if name == "pagesize" else 1)
                        )
                for source, target in FIELDS[endpoint_key].items():
                    value = options.get(source)
                    if value in (None, []):
                        continue
                    if source in {"market_id", "warehouse_id"}:
                        assert isinstance(value, list)
                        value = [official_integer(x, source) for x in value]
                    container = payload
                    parts = target.split(".")
                    for part in parts[:-1]:
                        container = container.setdefault(part, {})
                    container[parts[-1]] = value
                if endpoint_key == "catalog-amazon-shops":
                    payload.setdefault("condition", {})
                if endpoint_key == "catalog-warehouses":
                    payload.setdefault("model", {})
                if spec.request_body_mode == "none" and payload:
                    raise ValidationError("This directory endpoint accepts no input body.")
                body = None if spec.request_body_mode == "none" else payload
                return openapi_service(options.get("profile", "prod")).query(
                    spec,
                    body,
                    all_pages=options.get("all_pages", False),
                    max_pages=options.get("max_pages", 100),
                    response_mode="raw",
                )

            return execute_safely(operation, output_format=options.get("output_format", "json"))

        parameters = [
            p.replace(annotation=hints.get(p.name, p.annotation))
            for p in signature.parameters.values()
        ]
        parameters.extend(
            [
                inspect.Parameter(
                    "response_mode",
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=str,
                    default=typer.Option("data", "--response", help="data or raw upstream JSON."),
                ),
                inspect.Parameter(
                    "raw_input",
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=str | None,
                    default=typer.Option(
                        None, "--input", help="Official JSON object; raw mode only."
                    ),
                ),
            ]
        )
        wrapper.__signature__ = signature.replace(parameters=parameters)  # type: ignore[attr-defined]
        return wrapper

    return decorate
