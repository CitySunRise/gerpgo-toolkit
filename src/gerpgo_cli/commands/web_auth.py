from __future__ import annotations

import typer

from gerpgo_cli.output import execute_safely
from gerpgo_cli.runtime import web_auth_service
from gerpgo_sdk.config import ProfileStore, SecretStore
from gerpgo_sdk.webapi.auth import WebSessionStore

app = typer.Typer(help="Authenticate a Web session; no Web business endpoints are exposed.")

_PROFILE_HELP = "Profile name; precedence: --profile, GERPGO_PROFILE, prod."


@app.command("login")
def login(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    def operation() -> dict[str, object]:
        service, username, password = web_auth_service(profile)
        return service.login(profile, username, password)

    execute_safely(operation, message="web login success", output_format=output_format)


@app.command("status")
def status(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    def operation() -> dict[str, object]:
        ProfileStore().get(profile)
        return WebSessionStore(SecretStore()).status(profile)

    execute_safely(operation, message="web session status", output_format=output_format)


@app.command("logout")
def logout(
    profile: str = typer.Option(
        "prod", envvar="GERPGO_PROFILE", help=_PROFILE_HELP, show_default=True, show_envvar=True
    ),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    def operation() -> dict[str, object]:
        ProfileStore().get(profile)
        removed = WebSessionStore(SecretStore()).clear(profile)
        return {"profile": profile, "authenticated": False, "session_removed": removed}

    execute_safely(operation, message="web session removed", output_format=output_format)
