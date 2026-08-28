# OpenAPI safety

Before a business query, resolve the profile as explicit `--profile`, then
`GERPGO_PROFILE`, then `prod`. Do not ask for routine confirmation of `prod`.
Confirm the scope of identifiers and dates when it is ambiguous or broad. Do
not broaden shop, marketplace, warehouse, SKU, ASIN, or time ranges without
user intent.

Read `gerpgo-cli capabilities --format json` before constructing a query. Use
only a registered field and the exact enum value reported there. An
`official_not_published` enum status means the official document does not give
a complete fixed list; do not invent one. A `dynamic_identifier: true` field is
account-specific data, never a fixed enum. It may come from the user or the
registered catalog resolver. Prefer exact-name flags when the user knows a
name but not an ID. Missing required conditions must be asked for rather than
discovered by repeated failing ERP requests.

Catalog output is a strict SDK whitelist. Do not request, expose, save, or infer
tokens, contact details, addresses, authorization state, server/account data,
or other fields omitted by the CLI. Treat returned IDs/codes and names as
business identifiers: do not place real values in source, logs, filenames,
issues, tests, commits, or Skill examples.

Use registered flags or a local JSON input file. Do not echo a potentially
sensitive input file, and do not place ERP identifiers in temporary filenames.

The CLI may retry only transient connection failures, HTTP 429, and HTTP 5xx
for registered read-only endpoints. Authentication, validation, permission,
and other HTTP 4xx failures require inspection rather than retries.

Ordinary queries fetch one page. Explicit full-data intent uses
`--all-pages --max-pages 100`. Check `pagination.complete=true` and
`pagination.truncated=false` before analysis or export. If the first page shows
that more than 100 pages are needed, stop on `GERPGO_PAGE_LIMIT_EXCEEDED` and
show only the reported record count, estimated pages, and estimated seconds;
ask whether the user wants to raise `--max-pages`. Do not raise it without that
confirmation. When upstream omits `total`, reaching the limit while a full page
is still returned is also an error, never a successful truncation.

Never manually call successive page numbers to bypass the CLI's limiter. Full
pagination must preserve the user's original markets, shops, SKUs, ASINs,
warehouses, and date range exactly.

Keep stdout available for the result envelope. Diagnostic output belongs on
stderr. Do not enable verbose logs merely to discover credentials, tokens, or
request headers.

Never disable TLS verification. Use the profile's `system`, `direct`, or
`custom` proxy mode instead. Direct mode is scoped to the Gerpgo client session;
it must not change global proxy settings.
