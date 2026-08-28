from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    CONFIG_MISSING = "GERPGO_CONFIG_MISSING"
    SECRET_UNAVAILABLE = "GERPGO_SECRET_UNAVAILABLE"
    AUTH_FAILED = "GERPGO_AUTH_FAILED"
    SESSION_EXPIRED = "GERPGO_SESSION_EXPIRED"
    RATE_LIMITED = "GERPGO_RATE_LIMITED"
    NETWORK_ERROR = "GERPGO_NETWORK_ERROR"
    API_ERROR = "GERPGO_API_ERROR"
    VALIDATION_ERROR = "GERPGO_VALIDATION_ERROR"
    NOT_IMPLEMENTED = "GERPGO_NOT_IMPLEMENTED"
    PRIVACY_BLOCKED = "GERPGO_PRIVACY_BLOCKED"
    CATALOG_NOT_FOUND = "GERPGO_CATALOG_NOT_FOUND"
    CATALOG_AMBIGUOUS = "GERPGO_CATALOG_AMBIGUOUS"
    PAGE_LIMIT_EXCEEDED = "GERPGO_PAGE_LIMIT_EXCEEDED"


class GerpgoError(Exception):
    """A user-safe SDK error with a stable machine-readable code."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        trace_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.trace_id = trace_id
        self.details = details or {}


class ConfigError(GerpgoError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.CONFIG_MISSING, message)


class SecretError(GerpgoError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.SECRET_UNAVAILABLE, message)


class AuthError(GerpgoError):
    def __init__(self, message: str, *, trace_id: str | None = None) -> None:
        super().__init__(ErrorCode.AUTH_FAILED, message, trace_id=trace_id)


class ValidationError(GerpgoError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details=details)


class CatalogNotFoundError(GerpgoError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.CATALOG_NOT_FOUND, message, details=details)


class CatalogAmbiguousError(GerpgoError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.CATALOG_AMBIGUOUS, message, details=details)


class PageLimitExceededError(GerpgoError):
    def __init__(self, message: str, *, details: dict[str, Any]) -> None:
        super().__init__(ErrorCode.PAGE_LIMIT_EXCEEDED, message, details=details)


class NetworkError(GerpgoError):
    def __init__(self, message: str, *, trace_id: str | None = None) -> None:
        super().__init__(ErrorCode.NETWORK_ERROR, message, trace_id=trace_id)


class ApiError(GerpgoError):
    def __init__(
        self,
        message: str,
        *,
        trace_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(ErrorCode.API_ERROR, message, trace_id=trace_id, details=details)
