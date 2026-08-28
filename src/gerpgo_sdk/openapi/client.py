from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import requests

from gerpgo_sdk.common.errors import ApiError, AuthError, NetworkError, ValidationError
from gerpgo_sdk.common.rate_limit import PersistentRateLimiter
from gerpgo_sdk.common.redaction import redact
from gerpgo_sdk.config.models import ProxyMode

from .registry import EndpointSpec


@dataclass(slots=True)
class OpenApiConnection:
    app_id: str
    app_key: str
    base_url: str = "https://open.gerpgo.com/api/open"
    access_token_endpoint: str = "/api_token"
    request_timeout_seconds: float = 30.0
    sign_enabled: bool = True
    proxy_mode: ProxyMode = ProxyMode.SYSTEM
    proxy_url: str | None = None
    common_headers: dict[str, str] = field(default_factory=dict)


class OpenApiClient:
    def __init__(
        self,
        connection: OpenApiConnection,
        *,
        logger: logging.Logger | None = None,
        session: requests.Session | None = None,
        limiter: PersistentRateLimiter | None = None,
    ) -> None:
        self.connection = connection
        self.logger = logger or logging.getLogger("gerpgo")
        self.session = session or requests.Session()
        self.limiter = limiter or PersistentRateLimiter()
        self._access_token: str | None = None
        self._access_token_expires_at: float | None = None
        self.last_trace_id: str | None = None
        self._configure_session()
        self._validate_connection()

    def execute(self, spec: EndpointSpec, payload: dict[str, Any] | None) -> Any:
        if not spec.read_only:
            raise ValidationError("Only registered read-only endpoints are supported.")
        spec.validate_payload(payload)
        self._ensure_access_token()
        body = (
            ""
            if spec.request_body_mode == "none"
            else json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        )
        headers = {"accessToken": self._access_token or "", "Content-Type": "application/json"}
        if self.connection.sign_enabled:
            headers["sign"] = hashlib.md5(  # noqa: S324 - required by Gerpgo protocol
                f"{body}{self.connection.app_key}".encode()
            ).hexdigest()
        request_kwargs: dict[str, Any] = {}
        if spec.request_body_mode != "none":
            request_kwargs["data"] = body.encode("utf-8")
        result = self._request_json(
            spec.method,
            spec.path,
            headers=headers,
            rate_key=spec.key,
            minimum_interval_seconds=spec.minimum_interval_seconds,
            authenticated=True,
            **request_kwargs,
        )
        return self._extract_data(result, action=spec.official_name, auth=False)

    def test_authentication(self) -> dict[str, Any]:
        self._ensure_access_token(force_refresh=True)
        return {"authenticated": True, "token_cached": True}

    def _ensure_access_token(self, *, force_refresh: bool = False) -> None:
        if (
            not force_refresh
            and self._access_token
            and (
                self._access_token_expires_at is None or time.time() < self._access_token_expires_at
            )
        ):
            return
        result = self._request_json(
            "POST",
            self.connection.access_token_endpoint,
            json={"appId": self.connection.app_id, "appKey": self.connection.app_key},
            rate_key="access-token",
            minimum_interval_seconds=0.1,
            authenticated=False,
        )
        data = self._extract_data(result, action="OpenAPI authentication", auth=True)
        if not isinstance(data, dict) or not isinstance(data.get("accessToken"), str):
            raise AuthError("OpenAPI authentication response did not contain an access token.")
        self._access_token = data["accessToken"]
        ttl = data.get("expiresOut", data.get("expiresIn"))
        if isinstance(ttl, int | float):
            self._access_token_expires_at = time.time() + max(0.0, float(ttl) - 60.0)

    def _request_json(
        self,
        method: str,
        endpoint: str,
        *,
        rate_key: str,
        minimum_interval_seconds: float,
        authenticated: bool,
        **kwargs: Any,
    ) -> dict[str, Any]:
        url = self._build_url(endpoint)
        attempts = 3
        for attempt in range(1, attempts + 1):
            self.limiter.wait(rate_key, minimum_interval_seconds)
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.connection.request_timeout_seconds,
                    **kwargs,
                )
            except (
                requests.ConnectionError,
                requests.Timeout,
                requests.exceptions.SSLError,
            ) as exc:
                if attempt == attempts:
                    hostname = urlparse(url).hostname or "the configured host"
                    raise NetworkError(f"Gerpgo request could not reach {hostname}.") from exc
                time.sleep(float(attempt))
                continue

            self.last_trace_id = response.headers.get("g-trace-id") or response.headers.get(
                "x-trace-id"
            )
            if (response.status_code == 429 or response.status_code >= 500) and attempt < attempts:
                time.sleep(self._retry_delay(response, attempt))
                continue
            try:
                result = response.json()
            except ValueError as exc:
                if not response.ok:
                    raise ApiError(
                        f"Gerpgo returned HTTP {response.status_code}.", trace_id=self.last_trace_id
                    ) from exc
                raise ApiError(
                    "Gerpgo returned a non-JSON response.", trace_id=self.last_trace_id
                ) from exc
            if not isinstance(result, dict):
                raise ApiError(
                    "Gerpgo returned an invalid JSON object.", trace_id=self.last_trace_id
                )
            if not response.ok:
                self._raise_api_error(result, response.status_code, authenticated)
            return result
        raise NetworkError("Gerpgo request failed after retry attempts.")

    def _extract_data(self, result: dict[str, Any], *, action: str, auth: bool) -> Any:
        if result.get("code") != 200:
            self._raise_api_error(result, None, auth, action=action)
        return result.get("data")

    def _raise_api_error(
        self,
        result: dict[str, Any],
        status_code: int | None,
        authenticated: bool,
        *,
        action: str = "request",
    ) -> None:
        messages = result.get("messages")
        message = messages[0] if isinstance(messages, list) and messages else result.get("message")
        safe_message = str(redact(message or "Gerpgo rejected the request."))
        details = {"upstream_code": result.get("code")}
        if status_code is not None:
            details["http_status"] = status_code
        if authenticated is False or status_code in {401, 403}:
            raise AuthError(
                f"{action} failed. Verify locally stored credentials and permissions.",
                trace_id=self.last_trace_id,
            )
        raise ApiError(
            f"{action} failed: {safe_message}",
            trace_id=self.last_trace_id,
            details=details,
        )

    @staticmethod
    def _retry_delay(response: requests.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After")
        if value:
            try:
                return max(0.0, min(float(value), 120.0))
            except ValueError:
                pass
        return float(attempt)

    def _configure_session(self) -> None:
        self.session.headers.update(self.connection.common_headers)
        if self.connection.proxy_mode == ProxyMode.DIRECT:
            self.session.trust_env = False
            self.session.proxies.clear()
        elif self.connection.proxy_mode == ProxyMode.CUSTOM:
            if not self.connection.proxy_url:
                raise ValidationError("proxy_url is required when proxy_mode is custom.")
            self.session.trust_env = False
            self.session.proxies.update(
                {"http": self.connection.proxy_url, "https": self.connection.proxy_url}
            )
        else:
            self.session.trust_env = True

    def _validate_connection(self) -> None:
        for label, value in (
            ("app_id", self.connection.app_id),
            ("app_key", self.connection.app_key),
            ("base_url", self.connection.base_url),
        ):
            if not value.strip():
                raise ValidationError(f"{label} cannot be empty.")
        parsed = urlparse(self.connection.base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValidationError("OpenAPI base_url must be an HTTPS URL.")
        if self.connection.request_timeout_seconds <= 0:
            raise ValidationError("request_timeout_seconds must be greater than zero.")

    def _build_url(self, endpoint: str) -> str:
        return f"{self.connection.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
