from __future__ import annotations

import base64
from typing import Any

from Crypto.PublicKey import RSA

from gerpgo_sdk.webapi.auth import WebAuthClient, WebAuthConnection


class FakeResponse:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self.status_code = 200
        self.ok = True
        self.headers = {"g-trace-id": "DEMO_TRACE_ID"}

    def json(self) -> dict[str, Any]:
        return self._data


class FakeSession:
    def __init__(self, public_key: str) -> None:
        self.public_key = public_key
        self.headers: dict[str, str] = {}
        self.proxies: dict[str, str] = {}
        self.trust_env = True
        self.post_kwargs: dict[str, Any] = {}

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        assert url.endswith("/api/auth/system/account/publicKey")
        assert kwargs["headers"]["x-auth-token"] == "undefined"
        return FakeResponse({"code": 0, "data": {"publicKey": self.public_key}})

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        assert url.endswith("/v2/system/account/login")
        self.post_kwargs = kwargs
        return FakeResponse({"code": 0, "data": "DEMO_SESSION_TOKEN"})


def test_web_login_encrypts_password_and_returns_token_only_to_session_layer() -> None:
    key = RSA.generate(1024)
    public_der = base64.b64encode(key.public_key().export_key(format="DER")).decode()
    session = FakeSession(public_der)
    client = WebAuthClient(
        WebAuthConnection(base_url="https://erp.example.invalid"),
        session=session,  # type: ignore[arg-type]
    )

    token = client.login("demo-user", "DEMO_PASSWORD")

    assert token == "DEMO_SESSION_TOKEN"
    encrypted = session.post_kwargs["files"]["password"][1]
    assert encrypted != "DEMO_PASSWORD"
    assert session.post_kwargs["files"]["username"][1] == "demo-user"
