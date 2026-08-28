# Error handling

Read `error_code` before deciding what to do:

| Error code | Action |
|---|---|
| `GERPGO_CONFIG_MISSING` | If the selected profile is `prod`, direct the user to run `gerpgo-cli profile init prod`; never create it or fall back automatically. |
| `GERPGO_SECRET_UNAVAILABLE` | Let the user repair OS credential-store access or approved environment variables. |
| `GERPGO_AUTH_FAILED` | Stop; ask the user to verify local credentials and permissions without sharing them. |
| `GERPGO_RATE_LIMITED` | Respect the reported delay; do not parallelize the endpoint. |
| `GERPGO_NETWORK_ERROR` | Check connectivity and profile proxy mode; do not disable TLS. |
| `GERPGO_API_ERROR` | Report the sanitized message, upstream code, and trace ID. |
| `GERPGO_VALIDATION_ERROR` | Correct documented fields or types; do not guess enums. |
| `GERPGO_CATALOG_NOT_FOUND` | Check the exact trimmed name or ask for an explicit ID/code; do not try fuzzy alternatives. |
| `GERPGO_CATALOG_AMBIGUOUS` | Use only the safe candidate name/country/platform hints to ask for a disambiguating condition; never select the first result. |
| `GERPGO_PAGE_LIMIT_EXCEEDED` | Show `total_records`, `estimated_pages`, `max_pages`, and `estimated_seconds`, then ask whether to retry with a higher explicit `--max-pages`. Do not raise it automatically or loop pages manually. |
| `GERPGO_NOT_IMPLEMENTED` | Explain the version boundary and stop. |

Never include credentials or headers in an error report. A trace ID is safe to
retain unless the user explicitly identifies it as sensitive.
