# OpenAPI safety

Before a business query, confirm the selected profile and the scope of
identifiers and dates. Do not broaden shop, marketplace, warehouse, SKU, ASIN,
or time ranges without user intent.

Use registered flags or a local JSON input file. Do not echo a potentially
sensitive input file, and do not place ERP identifiers in temporary filenames.

The CLI may retry only transient connection failures, HTTP 429, and HTTP 5xx
for registered read-only endpoints. Authentication, validation, permission,
and other HTTP 4xx failures require inspection rather than retries.

Keep stdout available for the result envelope. Diagnostic output belongs on
stderr. Do not enable verbose logs merely to discover credentials, tokens, or
request headers.

Never disable TLS verification. Use the profile's `system`, `direct`, or
`custom` proxy mode instead. Direct mode is scoped to the Gerpgo client session;
it must not change global proxy settings.
