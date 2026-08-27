from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"

_SENSITIVE_KEY_PARTS = {
    "access_token",
    "accesstoken",
    "app_id",
    "appid",
    "app_key",
    "appkey",
    "authorization",
    "cookie",
    "g_session",
    "gsession",
    "password",
    "proxy",
    "proxy_url",
    "secret",
    "session",
    "sign",
    "token",
    "username",
    "x-auth-token",
    "x_auth_token",
    "xauthtoken",
}
_BEARER_RE = re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]+")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")


def is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")
    compact = normalized.replace("_", "")
    return normalized in _SENSITIVE_KEY_PARTS or compact in _SENSITIVE_KEY_PARTS


def redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if is_sensitive_key(key) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_text(value: str) -> str:
    value = _BEARER_RE.sub(r"\1" + REDACTED, value)
    return _JWT_RE.sub(REDACTED, value)
