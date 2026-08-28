from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from gerpgo_sdk.common.errors import AuthError
from gerpgo_sdk.config import ProxyMode
from gerpgo_sdk.openapi import OpenApiClient, OpenApiConnection, get_endpoint


class FakeResponse:
    def __init__(self, data: dict[str, Any], status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code
        self.headers = {"g-trace-id": "DEMO_TRACE_ID"}
        self.ok = status_code < 400

    def json(self) -> dict[str, Any]:
        return self._data


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.headers: dict[str, str] = {}
        self.proxies: dict[str, str] = {}
        self.trust_env = True

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


class NoWaitLimiter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, float]] = []

    def wait(self, key: str, interval: float) -> None:
        self.calls.append((key, interval))


def test_client_authenticates_signs_and_calls_registered_post() -> None:
    session = FakeSession(
        [
            FakeResponse({"code": 200, "data": {"accessToken": "DEMO_TOKEN", "expiresIn": 3600}}),
            FakeResponse({"code": 200, "data": {"rows": [{"sku": "SKU-DEMO-001"}]}}),
        ]
    )
    limiter = NoWaitLimiter()
    connection = OpenApiConnection(
        app_id="DEMO_APP_ID",
        app_key="DEMO_APP_KEY",
        proxy_mode=ProxyMode.DIRECT,
    )
    client = OpenApiClient(connection, session=session, limiter=limiter)  # type: ignore[arg-type]
    payload = {"page": 1, "pagesize": 100, "skuList": ["SKU-DEMO-001"]}

    result = client.execute(get_endpoint("product-list"), payload)

    assert result == {"rows": [{"sku": "SKU-DEMO-001"}]}
    assert session.trust_env is False
    assert session.calls[0][0:2] == (
        "POST",
        "https://open.gerpgo.com/api/open/api_token",
    )
    method, url, kwargs = session.calls[1]
    assert method == "POST"
    assert url.endswith("/purchase/goods/product/page")
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    expected_sign = hashlib.md5(f"{body}DEMO_APP_KEY".encode()).hexdigest()  # noqa: S324
    assert kwargs["headers"]["sign"] == expected_sign
    assert kwargs["headers"]["accessToken"] == "DEMO_TOKEN"
    assert limiter.calls[-1] == ("product-list", 0.5)


def test_authentication_error_does_not_echo_upstream_identity() -> None:
    session = FakeSession(
        [
            FakeResponse(
                {
                    "code": 401,
                    "messages": ["appId DEMO_APP_ID was rejected"],
                },
                status_code=401,
            )
        ]
    )
    client = OpenApiClient(
        OpenApiConnection(app_id="DEMO_APP_ID", app_key="DEMO_APP_KEY"),
        session=session,  # type: ignore[arg-type]
        limiter=NoWaitLimiter(),  # type: ignore[arg-type]
    )

    with pytest.raises(AuthError) as captured:
        client.test_authentication()

    assert "DEMO_APP_ID" not in captured.value.message


def test_catalog_body_modes_do_not_fall_back_to_get() -> None:
    session = FakeSession(
        [
            FakeResponse({"code": 200, "data": {"accessToken": "DEMO_TOKEN"}}),
            FakeResponse({"code": 200, "data": []}),
            FakeResponse({"code": 200, "data": []}),
        ]
    )
    client = OpenApiClient(
        OpenApiConnection(app_id="DEMO_APP_ID", app_key="DEMO_APP_KEY"),
        session=session,  # type: ignore[arg-type]
        limiter=NoWaitLimiter(),  # type: ignore[arg-type]
    )

    client.execute(get_endpoint("catalog-users"), None)
    client.execute(get_endpoint("catalog-multiplatform-shops"), {})

    bodyless_method, _, bodyless_kwargs = session.calls[1]
    empty_method, _, empty_kwargs = session.calls[2]
    assert bodyless_method == empty_method == "POST"
    assert "data" not in bodyless_kwargs
    assert empty_kwargs["data"] == b"{}"
