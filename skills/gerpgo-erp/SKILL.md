---
name: gerpgo-erp
description: Safely configure and use gerpgo-cli for the supported read-only Gerpgo OpenAPI queries or Web login-session management. Use for product, inventory, performance, Review, buyer-voice, profit, ASIN traffic, profile, or Gerpgo authentication requests. Do not use it to invent or call unsupported Web business APIs.
metadata:
  version: "0.1.0"
  requires:
    bins: ["gerpgo-cli"]
  cliHelp: "gerpgo-cli --help"
---

# Gerpgo ERP

Use `gerpgo-cli` as the execution boundary. Do not construct Gerpgo URLs or call
the ERP with a generic HTTP client.

## Route the request

- For first-time setup, missing credentials, profile selection, or doctor
  checks, read [references/initialization.md](references/initialization.md).
- For a supported business query, read
  [references/command-map.md](references/command-map.md) and use the exact
  registered command.
- Before transmitting identifiers or choosing retries, read
  [references/openapi-safety.md](references/openapi-safety.md).
- For Web login, session status, logout, or a request for a Web business API,
  read [references/web-auth.md](references/web-auth.md).
- When a command fails, read [references/errors.md](references/errors.md).

## Invariants

- Prefer `--format json`; parse the top-level `ok`, `data`, `error_code`, and
  `trace_id` fields.
- Keep SKU, MSKU, FNSKU, ASIN, order numbers, and other business identifiers as
  strings.
- Never ask the user to paste App Key, password, Cookie, session, JWT, or token
  into chat. Let the user enter credentials in their terminal through
  `gerpgo-cli profile init`.
- The supported OpenAPI commands are read-only even though the official method
  is POST. Do not infer that an unregistered POST is safe.
- V0.1 exposes only Web login, local status, and logout. It has no Web business
  data commands and no raw request escape hatch.
- Never silently switch between OpenAPI and Web API.
