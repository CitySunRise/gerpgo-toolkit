# gerpgo-toolkit

Independent, cross-platform tooling for approved Gerpgo ERP interfaces:

- `gerpgo_sdk`: OpenAPI client and Web login foundation.
- `gerpgo-cli`: human- and AI-friendly command line interface.
- `gerpgo-erp`: Codex Skill that selects safe CLI commands.

The project does not import or require `cy-automation-core`. The core repository
was used only to verify established authentication and networking behavior.

## V0.1 boundary

V0.1 implements twelve registered, read-only OpenAPI queries. It also implements
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
| 产品表现 | `/operation/sts/productAnalyzeMultiIndex/page` | [document 131](https://open.gerpgo.com/document?id=131) |
| 商品表现 | `/operation/sts/listingAnalyzeMultiIndex/page` | [document 140](https://open.gerpgo.com/document?id=140) |
| 流量统计-ASIN | `/operation/sts/traffic/page` | [document 122](https://open.gerpgo.com/document?id=122) |
| 流量数据-ASIN | `/operation/sts/trafficAnalysis/page` | [document 1018](https://open.gerpgo.com/document?id=1018) |

## Install

Use a stable release rather than `main`:

```shell
pipx install "git+https://github.com/CitySunRise/gerpgo-toolkit.git@v0.1.0"
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

## CLI examples

Inspect supported capabilities and one command's exact options:

```shell
gerpgo-cli capabilities --format json
gerpgo-cli openapi statistics product-performance --help
```

Query a registered endpoint:

```shell
gerpgo-cli openapi product list --profile prod --sku SKU-DEMO-001 --format json
```

Complex official filters may be supplied through `--input request.json`. The
file must contain one JSON object, the target endpoint remains fixed, and
unknown fields are rejected.

Web authentication is explicit and separate:

```shell
gerpgo-cli web auth login --profile prod --format json
gerpgo-cli web auth status --profile prod --format json
gerpgo-cli web auth logout --profile prod --format json
```

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
