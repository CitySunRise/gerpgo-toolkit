from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class ProxyMode(StrEnum):
    SYSTEM = "system"
    DIRECT = "direct"
    CUSTOM = "custom"


@dataclass(slots=True)
class Profile:
    name: str
    openapi_enabled: bool = True
    openapi_base_url: str = "https://open.gerpgo.com/api/open"
    openapi_access_token_endpoint: str = "/api_token"
    openapi_sign_enabled: bool = True
    web_enabled: bool = False
    web_base_url: str | None = None
    web_public_key_endpoint: str = "/api/auth/system/account/publicKey"
    web_login_endpoint: str = "/v2/system/account/login"
    proxy_mode: ProxyMode = ProxyMode.SYSTEM
    proxy_url: str | None = None
    request_timeout_seconds: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["proxy_mode"] = self.proxy_mode.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        values = dict(data)
        values["proxy_mode"] = ProxyMode(values.get("proxy_mode", ProxyMode.SYSTEM))
        return cls(**values)

    def public_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "openapi_enabled": self.openapi_enabled,
            "openapi_base_url": self.openapi_base_url,
            "web_enabled": self.web_enabled,
            "web_base_url": self.web_base_url,
            "proxy_mode": self.proxy_mode.value,
            "proxy_configured": bool(self.proxy_url),
            "request_timeout_seconds": self.request_timeout_seconds,
        }
