from __future__ import annotations

import logging

from gerpgo_sdk.config import ProfileStore, SecretStore
from gerpgo_sdk.openapi import OpenApiClient, OpenApiConnection, OpenApiService
from gerpgo_sdk.webapi.auth import (
    WebAuthClient,
    WebAuthConnection,
    WebAuthService,
    WebSessionStore,
)


def openapi_service(
    profile_name: str,
    *,
    profiles: ProfileStore | None = None,
    secrets: SecretStore | None = None,
    logger: logging.Logger | None = None,
) -> OpenApiService:
    profiles = profiles or ProfileStore()
    secrets = secrets or SecretStore()
    profile = profiles.get(profile_name)
    connection = OpenApiConnection(
        app_id=secrets.get_required(profile_name, "openapi_app_id"),
        app_key=secrets.get_required(profile_name, "openapi_app_key"),
        base_url=profile.openapi_base_url,
        access_token_endpoint=profile.openapi_access_token_endpoint,
        request_timeout_seconds=profile.request_timeout_seconds,
        sign_enabled=profile.openapi_sign_enabled,
        proxy_mode=profile.proxy_mode,
        proxy_url=profile.proxy_url,
    )
    return OpenApiService(OpenApiClient(connection, logger=logger))


def web_auth_service(
    profile_name: str,
    *,
    profiles: ProfileStore | None = None,
    secrets: SecretStore | None = None,
    logger: logging.Logger | None = None,
) -> tuple[WebAuthService, str, str]:
    profiles = profiles or ProfileStore()
    secrets = secrets or SecretStore()
    profile = profiles.get(profile_name)
    if not profile.web_enabled or not profile.web_base_url:
        from gerpgo_sdk.common.errors import ConfigError

        raise ConfigError(f"Web authentication is not enabled for profile '{profile_name}'.")
    connection = WebAuthConnection(
        base_url=profile.web_base_url,
        public_key_endpoint=profile.web_public_key_endpoint,
        login_endpoint=profile.web_login_endpoint,
        request_timeout_seconds=profile.request_timeout_seconds,
        proxy_mode=profile.proxy_mode,
        proxy_url=profile.proxy_url,
    )
    service = WebAuthService(
        WebAuthClient(connection, logger=logger),
        WebSessionStore(secrets),
    )
    return (
        service,
        secrets.get_required(profile_name, "web_username"),
        secrets.get_required(profile_name, "web_password"),
    )
