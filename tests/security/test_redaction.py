from gerpgo_sdk.common.redaction import REDACTED, redact


def test_nested_sensitive_values_are_redacted() -> None:
    result = redact(
        {
            "appId": "DEMO_APP_ID",
            "appKey": "DEMO_APP_KEY",
            "nested": {"x-auth-token": "DEMO_SESSION_TOKEN"},
            "safe": "SKU-DEMO-001",
        }
    )
    assert result == {
        "appId": REDACTED,
        "appKey": REDACTED,
        "nested": {"x-auth-token": REDACTED},
        "safe": "SKU-DEMO-001",
    }
