from __future__ import annotations

import typer

from gerpgo_cli.output import emit_success
from gerpgo_sdk.openapi import ENDPOINTS, RESOLUTION_RELATIONS


def capabilities(output_format: str = typer.Option("json", "--format")) -> None:
    data = {
        "openapi": [spec.contract() for spec in ENDPOINTS.values()],
        "catalog_resolution": {
            "matching": "exact_after_trim",
            "not_found_error": "GERPGO_CATALOG_NOT_FOUND",
            "ambiguous_error": "GERPGO_CATALOG_AMBIGUOUS",
            "relations": [relation.to_dict() for relation in RESOLUTION_RELATIONS],
            "identifier_output_type": "string",
            "openapi_webapi_fallback": False,
        },
        "webapi": {
            "authentication": ["login", "status", "logout"],
            "business_endpoints": [],
            "raw_request": False,
        },
    }
    emit_success(data, message="capabilities", output_format=output_format)
