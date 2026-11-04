"""Build concrete CLI commands from the SDK's frozen contracts."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

import typer

from gerpgo_cli.output import execute_safely
from gerpgo_cli.runtime import openapi_service
from gerpgo_sdk.openapi import ENDPOINTS, EndpointSpec
from gerpgo_sdk.openapi.expanded import kebab


def register(app: typer.Typer, groups: dict[str, typer.Typer]) -> None:
    for spec in ENDPOINTS.values():
        if spec.cli_route is None:
            continue
        module, command = spec.cli_route
        if module not in groups:
            groups[module] = typer.Typer(help=f"Registered read-only {module} queries.")
            app.add_typer(groups[module], name=module)
        groups[module].command(command, help=spec.official_name)(_command(spec))


def _command(spec: EndpointSpec) -> Callable[..., Any]:
    from .openapi import _load_payload

    def query(**options: Any) -> None:
        def operation() -> Any:
            payload = _load_payload(options.pop("input_file"))
            profile = options.pop("profile")
            output_format = options.pop("output_format")
            # Preserve format for the outer wrapper without passing it upstream.
            options["output_format"] = output_format
            response_mode = options.pop("response_mode")
            all_pages = options.pop("all_pages")
            max_pages = options.pop("max_pages")
            if "pageInfo" in spec.fields:
                nested = payload.setdefault("pageInfo", {})
                nested.setdefault("page", options.pop("nested_page"))
                nested.setdefault("pagesize", options.pop("nested_size"))
            for name, field in spec.fields.items():
                if name in payload and name in {
                    spec.request_page_field,
                    spec.request_page_size_field,
                    "count",
                }:
                    continue
                value = options.get(name)
                if value is None:
                    continue
                if field.type_name in {"int", "long", "short"}:
                    value = int(value)
                elif field.type_name in {"number", "double", "float"}:
                    value = int(value) if field.dynamic_identifier else float(value)
                elif field.type_name in {"array<int>", "array<long>"}:
                    value = [int(item) for item in value]
                payload[name] = value
            for name, default in (
                (spec.request_page_field, 1),
                (spec.request_page_size_field, spec.default_page_size),
                ("count", spec.default_page_size),
            ):
                if name in spec.fields and default is not None:
                    payload.setdefault(name, default)
            return openapi_service(profile).query(
                spec,
                payload,
                all_pages=all_pages,
                max_pages=max_pages,
                response_mode=response_mode,
            )

        execute_safely(
            operation,
            message=spec.official_name,
            output_format=options.get("output_format", "json"),
        )

    parameters = []

    def option(name: str, annotation: Any, default: Any) -> None:
        parameters.append(
            inspect.Parameter(
                name, inspect.Parameter.KEYWORD_ONLY, annotation=annotation, default=default
            )
        )

    option("profile", str, typer.Option("prod", "--profile", envvar="GERPGO_PROFILE"))
    option(
        "input_file",
        str | None,
        typer.Option(None, "--input", help="Official JSON object file or - for stdin."),
    )
    option("output_format", str, typer.Option("json", "--format"))
    option(
        "response_mode",
        str,
        typer.Option(
            "data", "--response", help="data or raw: full upstream envelope, credentials protected."
        ),
    )
    option(
        "all_pages",
        bool,
        typer.Option(
            False,
            "--all-pages",
            help="Complete serial query; may take a long time. Requires documented pagination.",
        ),
    )
    option("max_pages", int, typer.Option(spec.default_max_pages, "--max-pages", min=1))
    if "pageInfo" in spec.fields:
        option("nested_page", int, typer.Option(1, "--page", min=1))
        option("nested_size", int, typer.Option(spec.default_page_size, "--page-size", min=1))
    for name, field in spec.fields.items():
        if field.children or field.type_name in {"object", "array<object>", "array"}:
            continue
        flag = "--page-size" if name == "pagesize" else "--" + kebab(name)
        annotation: Any = str | None
        if field.type_name == "boolean":
            annotation = bool | None
            flag += "/--no-" + kebab(name)
        elif field.type_name.startswith("array<"):
            annotation = list[str] | None
        default = None
        if name in {spec.request_page_size_field, "count"}:
            default = spec.default_page_size
        elif name == spec.request_page_field:
            default = 1
        option(name, annotation, typer.Option(default, flag, help=field.help_text()))
    query.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    query.__name__ = spec.key.replace("-", "_")
    return query
