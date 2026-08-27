from __future__ import annotations

import typer

from gerpgo_cli.output import emit_success
from gerpgo_sdk.openapi import ENDPOINTS


def capabilities(output_format: str = typer.Option("json", "--format")) -> None:
    data = {
        "openapi": [
            {
                "key": spec.key,
                "official_name": spec.official_name,
                "method": spec.method,
                "path": spec.path,
                "document_id": spec.document_id,
                "documentation_url": spec.documentation_url,
                "minimum_interval_seconds": spec.minimum_interval_seconds,
                "read_only": spec.read_only,
            }
            for spec in ENDPOINTS.values()
        ],
        "webapi": {
            "authentication": ["login", "status", "logout"],
            "business_endpoints": [],
            "raw_request": False,
        },
    }
    emit_success(data, message="capabilities", output_format=output_format)
