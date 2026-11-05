# gerpgo-toolkit

Independent, cross-platform tooling for approved Gerpgo ERP interfaces:

- `gerpgo_sdk`: OpenAPI client and Web login foundation.
- `gerpgo-cli`: human- and AI-friendly command line interface.
- `gerpgo-erp`: Codex Skill that selects safe CLI commands.

The project does not import or require `cy-automation-core`. The core repository
was used only to verify established authentication and networking behavior.

## V0.3.2 scope

The complete public inventory is [docs/endpoint-inventory.md](docs/endpoint-inventory.md):
288 items across 14 categories, including the STA shipment subtree. Of these,
238 describe reads, 49 mutate business data, and one is authentication.
186 read queries are available (19 common commands and 167 expanded commands).
The other 52 read entries remain documentation inventory only and are not CLI commands.
This release removes 24 queries from the previous command set and streamlines the bundled Skill.

New commands use `gerpgo-cli openapi MODULE SERVICE-OPERATION`, for example:

```shell
gerpgo-cli openapi inventory transfer-page --status draft --create-date-start 2026-01-01 --create-date-end 2026-01-01
gerpgo-cli openapi logistics delivery-carton-query --item-type 2 --relate-code TF-DEMO
gerpgo-cli openapi logistics sta-shipment-box-info-query --input request.json
```

Use `capabilities` for the exact `cli_command`, all official field descriptions,
enums, nested schemas, and pagination support. Complex filters use `--input`;
unknown fields and nested fields are rejected. Prose enums that have not been
converted and reviewed block registration rather than becoming invented choices.

Every business and directory command accepts `--response raw` for the full
upstream envelope inside the CLI `data`: unknown fields, business identifiers,
messages and trace IDs are preserved. Only authentication material is protected.
Use JSON output. Default `--response data` retains v0.2 output compatibility,
including normalized directory results. Raw directories accept official --input;
local normalized `--exact-name` filters do not apply to raw results.

With `--response raw --all-pages`, output contains each full upstream envelope in
`pages` plus `pagination`; business rows are not duplicated in a merged array.
Normal full queries keep the merged `rows` structure. SDK pagination supports
documented `rows/total`, `records/total`, and deal/coupon `extObj` cursors. Other
unverified pagination shapes reject --all-pages rather than guessing. All modes
enforce max-pages and completeness. Directory pagination now also errors instead
of silently stopping at the page limit.

The SDK handles per-interface request intervals and pagination; capabilities exposes
the current rules and local defaults.

Official document 2453 explicitly supports transfer cartons through itemType=2.
4645 exposes batch inventory; 6025 exposes batch flows. These are not claimed to
be identical to core's transfer-specific serial query. No Web business query is
added without proof of a missing official capability. See the inventory and
[live validation report](docs/live-verification.md) for per-interface status.

## Common business and directory commands

The CLI provides eleven common read-only business OpenAPI queries and eight
official directory queries with SDK-owned field contracts, exact name-to-ID
resolution, safe output normalization, official enums, date/combination
validation, and discoverable CLI capabilities. It also implements
the Gerpgo Web public-key login flow, local session status, and local logout.
It does **not** expose Web business APIs, ERP writes, silent OpenAPI/Web
fallbacks, or an arbitrary URL request command.

Every supported business endpoint uses the official `POST` method:

| Official name | OpenAPI path | Official documentation |
|---|---|---|
| 查询产品列表 | `/purchase/goods/product/page` | [document 53](https://open.gerpgo.com/document?id=53) |
| 查询产品库存 | `/purchase/store/inventory/page` | [document 15](https://open.gerpgo.com/document?id=15) |
| 销售表现 | `/operation/sts/salesAnalysis/page` | [document 3375](https://open.gerpgo.com/document?id=3375) |
| 搜索词表现 | `/operation/ads/adsKeywordAnalytical/query` | [document 100](https://open.gerpgo.com/document?id=100) |
| Review | `/operation/crm/review/page` | [document 1092](https://open.gerpgo.com/document?id=1092) |
| 买家之声列表 | `/operation/crm/customerVoice/page` | [document 1014](https://open.gerpgo.com/document?id=1014) |
| 查询财务利润分析V2 | `/finance/sts/financialAnalysis/page/V2` | [document 2256](https://open.gerpgo.com/document?id=2256) |
| 关键词表现 | `/operation/ads/adsKeywordAnalytical/page` | [document 99](https://open.gerpgo.com/document?id=99) |
| 商品表现 | `/operation/sts/listingAnalyzeMultiIndex/page` | [document 140](https://open.gerpgo.com/document?id=140) |
| 流量统计-ASIN | `/operation/sts/traffic/page` | [document 122](https://open.gerpgo.com/document?id=122) |
| 流量数据-ASIN | `/operation/sts/trafficAnalysis/page` | [document 1018](https://open.gerpgo.com/document?id=1018) |

Official directory endpoints are also fixed to POST:

| Official name | OpenAPI path | Official documentation |
|---|---|---|
| 查询亚马逊店铺信息 | `/middle/base/market/page` | [document 153](https://open.gerpgo.com/document?id=153) |
| 查询所有用户列表 | `/middle/base/allUser/list` | [document 25](https://open.gerpgo.com/document?id=25) |
| 查询仓库信息列表 | `/purchase/store/multiTypeWarehouse/page` | [document 1035](https://open.gerpgo.com/document?id=1035) |
| 查询品牌资料 | `/purchase/goods/brand/page` | [document 1752](https://open.gerpgo.com/document?id=1752) |
| 查询品类信息 | `/purchase/goods/category/page` | [document 54](https://open.gerpgo.com/document?id=54) |
| 查询多平台店铺信息 | `/platform/multiplatform/multiShop/query` | [document 67](https://open.gerpgo.com/document?id=67) |
| 根据亚马逊店铺id查询店铺名称 | `/middle/base/marketNames/query` | [document 1177](https://open.gerpgo.com/document?id=1177) |
| 根据亚马逊店铺id查询仓库信息 | `/middle/base/warehouseIds/query` | [document 1179](https://open.gerpgo.com/document?id=1179) |

Documents 25, 67, 1177, and 1179 have stale detail metadata that says GET;
their public documentation pages specify POST. The toolkit never implements or
falls back to GET for these endpoints.

## Install

Use a stable release rather than `main`:

```shell
pipx install "git+https://github.com/CitySunRise/gerpgo-toolkit.git@v0.3.2"
gerpgo-cli skill install
gerpgo-cli doctor --read-only
```

The same commands work in macOS Terminal, Windows PowerShell, and Windows
Terminal when Python and `pipx` are installed.

For local development:

```shell
python -m venv .venv
python -m pip install -e ".[dev]"
pytest
```

## Initialize a profile

Run the interactive setup locally:

```shell
gerpgo-cli profile init prod
gerpgo-cli profile status prod --format json
gerpgo-cli doctor --profile prod --read-only --format json
```

Secrets are stored through Python `keyring` in macOS Keychain or Windows
Credential Manager. The profile JSON contains only non-secret values. Do not
paste App Keys, passwords, cookies, or session tokens into chat, command-line
arguments, logs, issues, or commits.

Environment variables are available for approved CI or unattended hosts:

```text
GERPGO_PROFILE
GERPGO_OPENAPI_APP_ID
GERPGO_OPENAPI_APP_KEY
GERPGO_WEB_BASE_URL
GERPGO_WEB_USERNAME
GERPGO_WEB_PASSWORD
```

Use `profile init --from-env`; never print the values.

Business and Web authentication commands select profiles in this order:

1. Explicit `--profile NAME`.
2. `GERPGO_PROFILE`.
3. Default `prod`.

The CLI never creates a missing profile or falls back to another profile. If
`prod` is not initialized, run `gerpgo-cli profile init prod` in your own
terminal.

## CLI examples

Inspect supported capabilities and one command's exact options:

```shell
gerpgo-cli capabilities --format json
gerpgo-cli openapi statistics listing-performance --help
```

`capabilities` is generated from the SDK registry and is the machine-readable
source of truth for every registered field: type, required status, official
enum values and Chinese labels, date format, default, dynamic-identifier flag,
field combinations, pagination metadata, document ID, and request interval.
The CLI and bundled Skill consume that contract instead of maintaining separate
enum implementations.

Account-specific market, warehouse, responsible-person, category, brand, SKU,
MSKU, ASIN, order, and review identifiers are dynamic values, not fixed enums.
Obtain them from the user's own account context and never place real values in
source, tests, documentation, logs, or commits. The official profit document
publishes `AMAZON` as the `platformCodes` default but does not publish a complete
platform enum; the CLI therefore does not invent or restrict that list.

When a user knows a name but not an account-specific ID/code, use the formal
name options. Matching trims surrounding whitespace and then requires one exact
result; it never selects a fuzzy result automatically:

```shell
gerpgo-cli openapi inventory product --warehouse-name "示例仓" --sku SKU-DEMO-001
gerpgo-cli openapi ads search-term-performance --shop-name "示例店铺" --country-code US --start-date 2026-01-01 --end-date 2026-01-01
gerpgo-cli openapi product list --brand-name "示例品牌" --category-name "示例品类"
```

Explicit directory inspection is available under `openapi catalog`, for
example `gerpgo-cli openapi catalog amazon-shops list --format json`. Directory
results are rebuilt from strict safe-field models; upstream credentials,
tokens, contacts, addresses, server/account details, and authorization state
are never returned. IDs remain text in CLI input/output and are converted to
the official numeric request type only inside the SDK.

Query a registered endpoint:

```shell
gerpgo-cli openapi product list --sku SKU-DEMO-001 --format json
```

Ordinary queries fetch one page. Use `--all-pages` only for an intentional
complete dataset; the default safety limit is 100 pages:

```shell
gerpgo-cli openapi inventory product --sku SKU-DEMO-001 --all-pages --max-pages 100
```

The first response's `total` is used to estimate page count and minimum request
time before continuing. A complete result contains `pagination.complete=true`
and `pagination.truncated=false`. If the estimate exceeds the safety limit, the
CLI returns `GERPGO_PAGE_LIMIT_EXCEEDED` before requesting page two. Raising
`--max-pages` requires an explicit user decision; the CLI never silently
returns truncated data.

Pagination defaults are SDK-owned and visible through capabilities. Sales performance
uses 200 rows; ASIN traffic statistics and ASIN traffic data use 500; the other
common business queries use 100. Use each command's --help for its effective range.

Complex official filters may be supplied through `--input request.json`. The
file must contain one JSON object, the target endpoint remains fixed, and
unknown fields are rejected.

Web authentication is explicit and separate:

```shell
gerpgo-cli web auth login --format json
gerpgo-cli web auth status --format json
gerpgo-cli web auth logout --format json
```

These examples use the default `prod` profile. Use `--profile test` only when
you explicitly want another initialized profile; it overrides both
`GERPGO_PROFILE` and `prod`.

`status` does not make a business request. `logout` removes the locally cached
session and does not claim server-side revocation.

## Result contract

JSON output uses a stable envelope:

```json
{
  "ok": true,
  "data": {},
  "message": "success",
  "error_code": null,
  "trace_id": "DEMO_TRACE_ID"
}
```

Business output goes to stdout. Diagnostics go to stderr. Sensitive headers,
credentials, identity, and session values are redacted and are never included
in a successful login result.

## Skill lifecycle

```shell
gerpgo-cli skill status
gerpgo-cli skill install
gerpgo-cli skill update
```

Install refuses to overwrite an existing Skill. Update copies the bundled
Skill to a temporary directory and replaces the installed directory atomically,
with rollback if replacement fails.

## Public-repository safety

Before every commit, inspect the staged diff and run:

```shell
python scripts/privacy_check.py --all
python scripts/verify_official_docs.py
pytest
```

Do not commit credentials, real ERP identifiers, private hosts, captures,
exports, logs, screenshots, or profile/session files. See [SECURITY.md](SECURITY.md)
and [CONTRIBUTING.md](CONTRIBUTING.md).
