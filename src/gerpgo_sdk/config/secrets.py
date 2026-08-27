from __future__ import annotations

import os

import keyring
from keyring.errors import KeyringError

from gerpgo_sdk.common.errors import SecretError

_SERVICE_NAME = "gerpgo-toolkit"
_ENV_NAMES = {
    "openapi_app_id": "GERPGO_OPENAPI_APP_ID",
    "openapi_app_key": "GERPGO_OPENAPI_APP_KEY",
    "web_username": "GERPGO_WEB_USERNAME",
    "web_password": "GERPGO_WEB_PASSWORD",
}


class SecretStore:
    def __init__(self, service_name: str = _SERVICE_NAME) -> None:
        self.service_name = service_name

    def get(self, profile: str, key: str) -> str | None:
        env_name = _ENV_NAMES.get(key)
        if env_name and os.getenv(env_name):
            return os.environ[env_name]
        try:
            return keyring.get_password(self.service_name, self._account(profile, key))
        except KeyringError as exc:
            raise SecretError("The operating-system credential store is unavailable.") from exc

    def get_required(self, profile: str, key: str) -> str:
        value = self.get(profile, key)
        if not value:
            env_name = _ENV_NAMES.get(key, key)
            raise SecretError(
                f"Credential '{key}' is not configured for profile '{profile}'. "
                f"Run profile init or set {env_name}."
            )
        return value

    def set(self, profile: str, key: str, value: str) -> None:
        if not value:
            raise SecretError(f"Credential '{key}' cannot be empty.")
        try:
            keyring.set_password(self.service_name, self._account(profile, key), value)
        except KeyringError as exc:
            raise SecretError("The operating-system credential store is unavailable.") from exc

    def delete(self, profile: str, key: str) -> bool:
        try:
            existing = keyring.get_password(self.service_name, self._account(profile, key))
            if existing is None:
                return False
            keyring.delete_password(self.service_name, self._account(profile, key))
            return True
        except KeyringError as exc:
            raise SecretError("The operating-system credential store is unavailable.") from exc

    @staticmethod
    def _account(profile: str, key: str) -> str:
        return f"{profile}:{key}"
