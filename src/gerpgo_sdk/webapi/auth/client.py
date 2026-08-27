from __future__ import annotations

import base64
import logging
import secrets
import string
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from gerpgo_sdk.common.errors import AuthError, NetworkError, ValidationError
from gerpgo_sdk.common.redaction import redact
from gerpgo_sdk.config.models import ProxyMode


@dataclass(slots=True)
class WebAuthConnection:
    base_url: str
    public_key_endpoint: str = "/api/auth/system/account/publicKey"
    login_endpoint: str = "/v2/system/account/login"
    request_timeout_seconds: float = 30.0
    proxy_mode: ProxyMode = ProxyMode.SYSTEM
    proxy_url: str | None = None
    common_headers: dict[str, str] = field(default_factory=dict)


class WebAuthClient:
    """Perform only the verified Gerpgo Web login flow."""

    def __init__(
        self,
        connection: WebAuthConnection,
        *,
        logger: logging.Logger | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.connection = connection
        self.logger = logger or logging.getLogger("gerpgo")
        self.session = session or requests.Session()
        self.last_trace_id: str | None = None
        self._configure_session()
        self._validate_connection()

    def login(self, username: str, password: str) -> str:
        if not username or not password:
            raise ValidationError("Web username and password must be configured.")
        session_id = self._session_id()
        public_key = self._get_public_key(session_id)
        encrypted_password = self._encrypt_password(password, public_key)
        try:
            response = self.session.post(
                self._build_url(self.connection.login_endpoint),
                headers={"g-session": session_id, "g-login-from": "page"},
                files={
                    "username": (None, username),
                    "password": (None, encrypted_password),
                    "sevenDaysNoPassword": (None, "true"),
                    "loginOrigin": (None, "PAGE"),
                },
                timeout=self.connection.request_timeout_seconds,
            )
        except (requests.ConnectionError, requests.Timeout, requests.exceptions.SSLError) as exc:
            raise NetworkError("Gerpgo Web login could not reach the configured host.") from exc
        self.last_trace_id = response.headers.get("g-trace-id") or response.headers.get(
            "x-trace-id"
        )
        result = self._response_json(response, "Web login")
        token = result.get("data")
        if result.get("code") != 0 or not isinstance(token, str) or not token.strip():
            raise AuthError(
                "Web login failed. Verify locally stored credentials and permissions.",
                trace_id=self.last_trace_id,
            )
        self.logger.info("gerpgo web login succeeded")
        return token

    def _get_public_key(self, session_id: str) -> str:
        try:
            response = self.session.get(
                self._build_url(self.connection.public_key_endpoint),
                headers={"x-auth-token": "undefined", "g-session": session_id},
                timeout=self.connection.request_timeout_seconds,
            )
        except (requests.ConnectionError, requests.Timeout, requests.exceptions.SSLError) as exc:
            raise NetworkError(
                "Gerpgo Web public-key request could not reach the configured host."
            ) from exc
        self.last_trace_id = response.headers.get("g-trace-id") or response.headers.get(
            "x-trace-id"
        )
        result = self._response_json(response, "Web public-key lookup")
        data = result.get("data")
        public_key = data.get("publicKey") if isinstance(data, dict) else None
        if result.get("code") != 0 or not isinstance(public_key, str) or not public_key.strip():
            raise AuthError(
                f"Web public-key lookup failed: {self._safe_message(result)}",
                trace_id=self.last_trace_id,
            )
        return public_key

    def _response_json(self, response: requests.Response, action: str) -> dict[str, Any]:
        try:
            result = response.json()
        except ValueError as exc:
            if not response.ok:
                raise AuthError(f"{action} returned HTTP {response.status_code}.") from exc
            raise AuthError(f"{action} returned a non-JSON response.") from exc
        if not isinstance(result, dict):
            raise AuthError(f"{action} returned an invalid JSON object.")
        if not response.ok:
            raise AuthError(
                f"{action} returned HTTP {response.status_code}: {self._safe_message(result)}",
                trace_id=self.last_trace_id,
            )
        return result

    @staticmethod
    def _safe_message(result: dict[str, Any]) -> str:
        messages = result.get("messages")
        message = messages[0] if isinstance(messages, list) and messages else result.get("message")
        return str(redact(message or "authentication rejected"))

    @staticmethod
    def _session_id(length: int = 21) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def _encrypt_password(password: str, public_key_der_base64: str) -> str:
        try:
            key = RSA.import_key(base64.b64decode(public_key_der_base64, validate=True))
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(password.encode("utf-8"))
        except (ValueError, TypeError, IndexError) as exc:
            raise AuthError("Gerpgo returned an invalid login public key.") from exc
        return base64.b64encode(encrypted).decode("ascii")

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
        parsed = urlparse(self.connection.base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValidationError("Web base_url must be an HTTPS URL.")
        if self.connection.request_timeout_seconds <= 0:
            raise ValidationError("request_timeout_seconds must be greater than zero.")

    def _build_url(self, endpoint: str) -> str:
        return f"{self.connection.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
