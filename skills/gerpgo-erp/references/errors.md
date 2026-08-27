# Error handling

Read `error_code` before deciding what to do:

| Error code | Action |
|---|---|
| `GERPGO_CONFIG_MISSING` | Initialize or select the correct profile. |
| `GERPGO_SECRET_UNAVAILABLE` | Let the user repair OS credential-store access or approved environment variables. |
| `GERPGO_AUTH_FAILED` | Stop; ask the user to verify local credentials and permissions without sharing them. |
| `GERPGO_RATE_LIMITED` | Respect the reported delay; do not parallelize the endpoint. |
| `GERPGO_NETWORK_ERROR` | Check connectivity and profile proxy mode; do not disable TLS. |
| `GERPGO_API_ERROR` | Report the sanitized message, upstream code, and trace ID. |
| `GERPGO_VALIDATION_ERROR` | Correct documented fields or types; do not guess enums. |
| `GERPGO_NOT_IMPLEMENTED` | Explain the version boundary and stop. |

Never include credentials or headers in an error report. A trace ID is safe to
retain unless the user explicitly identifies it as sensitive.
