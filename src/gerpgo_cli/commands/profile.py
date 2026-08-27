from __future__ import annotations

import os

import typer

from gerpgo_cli.output import execute_safely
from gerpgo_sdk.common.errors import ValidationError
from gerpgo_sdk.config import Profile, ProfileStore, ProxyMode, SecretStore

app = typer.Typer(help="Manage non-secret profiles and operating-system credentials.")


@app.command("init")
def init_profile(
    name: str = typer.Argument(..., help="Profile name, for example prod."),
    from_env: bool = typer.Option(False, "--from-env", help="Read credentials from environment."),
    enable_openapi: bool = typer.Option(True, "--enable-openapi/--no-enable-openapi"),
    enable_web: bool | None = typer.Option(None, "--enable-web/--no-enable-web"),
    openapi_base_url: str = typer.Option(
        "https://open.gerpgo.com/api/open", help="Official OpenAPI base URL."
    ),
    web_base_url: str | None = typer.Option(
        None, help="ERP Web base URL; no business Web API is enabled."
    ),
    proxy_mode: ProxyMode = typer.Option(ProxyMode.SYSTEM),
    proxy_url: str | None = typer.Option(None, help="Proxy URL when --proxy-mode custom."),
    timeout: float = typer.Option(30.0, min=1.0, help="Request timeout in seconds."),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    def operation() -> dict[str, object]:
        nonlocal enable_web, web_base_url
        profiles = ProfileStore()
        secrets = SecretStore()
        if enable_web is None:
            enable_web = (
                False
                if from_env
                else typer.confirm("Configure Web login for future use?", default=False)
            )
        if proxy_mode == ProxyMode.CUSTOM and not proxy_url:
            raise ValidationError("--proxy-url is required with --proxy-mode custom.")
        if enable_web and not web_base_url:
            web_base_url = (
                os.getenv("GERPGO_WEB_BASE_URL") if from_env else typer.prompt("Web base URL")
            )

        if enable_openapi:
            app_id = _credential("GERPGO_OPENAPI_APP_ID", "OpenAPI App ID", from_env, hidden=False)
            app_key = _credential(
                "GERPGO_OPENAPI_APP_KEY", "OpenAPI App Key", from_env, hidden=True
            )
            if not from_env:
                secrets.set(name, "openapi_app_id", app_id)
                secrets.set(name, "openapi_app_key", app_key)
        if enable_web:
            username = _credential("GERPGO_WEB_USERNAME", "Web username", from_env, hidden=False)
            password = _credential("GERPGO_WEB_PASSWORD", "Web password", from_env, hidden=True)
            if not from_env:
                secrets.set(name, "web_username", username)
                secrets.set(name, "web_password", password)

        profile = Profile(
            name=name,
            openapi_enabled=enable_openapi,
            openapi_base_url=openapi_base_url,
            web_enabled=bool(enable_web),
            web_base_url=web_base_url,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
            request_timeout_seconds=timeout,
        )
        profiles.save(profile)
        return {
            **profile.public_status(),
            "openapi_app_id_configured": bool(enable_openapi),
            "openapi_app_key_configured": bool(enable_openapi),
            "web_username_configured": bool(enable_web),
            "web_password_configured": bool(enable_web),
        }

    execute_safely(operation, message="profile initialized", output_format=output_format)


@app.command("list")
def list_profiles(output_format: str = typer.Option("json", "--format")) -> None:
    execute_safely(
        lambda: [profile.public_status() for profile in ProfileStore().list()],
        message="profiles listed",
        output_format=output_format,
    )


@app.command("show")
def show_profile(
    name: str,
    output_format: str = typer.Option("json", "--format"),
) -> None:
    execute_safely(
        lambda: ProfileStore().get(name).public_status(),
        message="profile shown",
        output_format=output_format,
    )


@app.command("status")
def profile_status(
    name: str,
    output_format: str = typer.Option("json", "--format"),
) -> None:
    def operation() -> dict[str, object]:
        profile = ProfileStore().get(name)
        secrets = SecretStore()
        return {
            **profile.public_status(),
            "openapi_app_id_configured": bool(secrets.get(name, "openapi_app_id")),
            "openapi_app_key_configured": bool(secrets.get(name, "openapi_app_key")),
            "web_username_configured": bool(secrets.get(name, "web_username")),
            "web_password_configured": bool(secrets.get(name, "web_password")),
            "web_session_cached": bool(secrets.get(name, "web_session_token")),
        }

    execute_safely(operation, message="profile status", output_format=output_format)


def _credential(env_name: str, prompt: str, from_env: bool, *, hidden: bool) -> str:
    if from_env:
        value = os.getenv(env_name)
        if not value:
            raise ValidationError(f"{env_name} is required with --from-env.")
        return value
    return str(typer.prompt(prompt, hide_input=hidden, confirmation_prompt=hidden))
