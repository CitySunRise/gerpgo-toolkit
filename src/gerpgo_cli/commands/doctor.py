from __future__ import annotations

import typer

from gerpgo_cli.output import execute_safely
from gerpgo_cli.runtime import openapi_service
from gerpgo_sdk.config import ProfileStore, SecretStore


def doctor(
    profile: str | None = typer.Option(None, help="Profile to inspect.", envvar="GERPGO_PROFILE"),
    connectivity: bool = typer.Option(False, help="Perform an OpenAPI authentication request."),
    read_only: bool = typer.Option(True, "--read-only/--no-read-only", hidden=True),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    def operation() -> dict[str, object]:
        profiles = ProfileStore()
        result: dict[str, object] = {
            "read_only": read_only,
            "config_storage": "platformdirs-user-config",
            "profile_count": len(profiles.list()),
            "connectivity_checked": False,
        }
        if profile:
            selected = profiles.get(profile)
            secrets = SecretStore()
            result["profile"] = selected.public_status()
            result["credentials"] = {
                "openapi_app_id_configured": bool(secrets.get(profile, "openapi_app_id")),
                "openapi_app_key_configured": bool(secrets.get(profile, "openapi_app_key")),
                "web_username_configured": bool(secrets.get(profile, "web_username")),
                "web_password_configured": bool(secrets.get(profile, "web_password")),
            }
            if connectivity:
                result["openapi"] = openapi_service(profile).client.test_authentication()
                result["connectivity_checked"] = True
        return result

    execute_safely(operation, message="doctor completed", output_format=output_format)
