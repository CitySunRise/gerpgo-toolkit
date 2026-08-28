---
name: gerpgo-erp
description: >-
  Safely configure and use gerpgo-cli for supported read-only Gerpgo OpenAPI queries and Web login-session management. Trigger for gerpgo-erp, Gerpgo, gerpgo-cli, 积加, 积加 ERP, 积加 CLI, 积加开放接口, 积加产品、库存、销售表现、Review、买家之声、利润、ASIN、关键词查询, and 积加配置、登录、会话. Do not use it to invent or call unsupported Web business APIs.
metadata:
  version: "0.2.0"
  requires:
    bins: ["gerpgo-cli"]
  cliHelp: "gerpgo-cli --help"
---

# Gerpgo ERP

Use `gerpgo-cli` as the execution boundary. Do not construct Gerpgo URLs or call
the ERP with a generic HTTP client.

If the user's entire request is only "积加" or another equally ambiguous name-only
mention, ask what they want to query or configure. Do not run any CLI or ERP
request until the intent is known. The user does not need to say "use Skill",
"use CLI", or `$gerpgo-erp` for this Skill to apply.

## Route the request

- For first-time setup, missing credentials, profile selection, or doctor
  checks, read [references/initialization.md](references/initialization.md).
- For a supported business query, read
  [references/command-map.md](references/command-map.md), then read
  [references/endpoint-parameters.md](references/endpoint-parameters.md) for
  the selected interface and use the exact registered command.
- When the user supplies a shop, warehouse, responsible-person, brand, or
  category name instead of an ID/code, read
  [references/catalog-resolution.md](references/catalog-resolution.md). Prefer the
  business command's `--*-name` flag; use catalog list commands only when the
  user explicitly wants to inspect the directory or disambiguate matches.
- Before transmitting identifiers or choosing retries, read
  [references/openapi-safety.md](references/openapi-safety.md).
- For Web login, session status, logout, or a request for a Web business API,
  read [references/web-auth.md](references/web-auth.md).
- When a command fails, read [references/errors.md](references/errors.md).

## Invariants

- Resolve the profile without asking every time: explicit `--profile NAME`
  takes precedence over `GERPGO_PROFILE`, which takes precedence over the
  default `prod`. Only an explicit user choice should override that result.
- When neither the user nor the environment selects a profile, use `prod`. The
  CLI command may include `--profile prod`, but the user never needs to mention
  it in their prompt. If `prod` is missing, stop and direct the user to run
  `gerpgo-cli profile init prod` in their own terminal; never create, switch, or
  fall back to another profile.
- Prefer `--format json`; parse the top-level `ok`, `data`, `error_code`, and
  `trace_id` fields.
- Before forming a business query, read
  `gerpgo-cli capabilities --format json`. Its SDK-derived field contract is
  authoritative for required fields, official enums and labels, date formats,
  dynamic identifiers, defaults, combinations, pagination, document IDs, and
  request intervals. Do not rely on memorized values when capabilities is
  available.
- Ask only for missing required business conditions or an intentionally narrow
  query scope. Never guess an enum, dynamic ID, date, SKU, ASIN, shop, market,
  or warehouse. Once the conditions are complete, make one correctly formed
  call without asking the user to reconfirm unrelated defaults.
- Name resolution is an SDK operation: trim surrounding whitespace and require
  one exact match. Never guess from a fuzzy/partial match. For Amazon shops,
  `--country` or `--country-code` may disambiguate equal `store` or
  `marketName` values. Never show raw catalog responses; use only the CLI's
  safe whitelist output.
- Treat “全部”, “完整”, “完整数据”, “完整分析”, “导出”, “所有数据”, or an
  equivalent explicit full-dataset request as full-query intent. Add
  `--all-pages --max-pages 100` automatically; the user does not need to
  understand pagination flags. Ordinary “查一下” or “看看” requests remain a
  single page.
- A successful full query must contain `pagination.complete=true` and
  `pagination.truncated=false`. Never loop over page numbers outside the CLI or
  bypass its registered request interval. Never broaden the user's market,
  shop, SKU, ASIN, warehouse, or date scope to obtain more rows.
- Keep SKU, MSKU, FNSKU, ASIN, order numbers, and other business identifiers as
  strings.
- Never ask the user to paste App Key, password, Cookie, session, JWT, or token
  into chat. Let the user enter credentials in their terminal through
  `gerpgo-cli profile init`.
- The supported OpenAPI commands are read-only even though the official method
  is POST. Do not infer that an unregistered POST is safe.
- V0.2 exposes only Web login, local status, and logout. It has no Web business
  data commands and no raw request escape hatch.
- Never silently switch between OpenAPI and Web API.
