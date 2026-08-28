# Supported command map

Use the exact command matching the business request:

Commands default to profile `prod`. Do not ask the user to confirm that profile
on every query. Respect an explicit `--profile NAME` first, then
`GERPGO_PROFILE`, then `prod`; never fall back to another profile when the
selected one is missing.

For exact method, path, official name, and interval details, read
[endpoint-registry.md](endpoint-registry.md).
For required business conditions, fields, official enums, date formats,
dynamic identifiers, constraints, and synthetic minimum examples, read the
selected section in [endpoint-parameters.md](endpoint-parameters.md). First
read `gerpgo-cli capabilities --format json`; that SDK-derived output is the
runtime source of truth.

| Official interface name | Command |
|---|---|
| 查询产品列表 | `gerpgo-cli openapi product list` |
| 查询产品库存 | `gerpgo-cli openapi inventory product` |
| 销售表现 | `gerpgo-cli openapi statistics sales-performance` |
| 搜索词表现 | `gerpgo-cli openapi ads search-term-performance` |
| Review | `gerpgo-cli openapi customer review` |
| 买家之声列表 | `gerpgo-cli openapi customer buyer-voice` |
| 查询财务利润分析V2 | `gerpgo-cli openapi finance profit-analysis-v2` |
| 关键词表现 | `gerpgo-cli openapi ads keyword-performance` |
| 产品表现 | `gerpgo-cli openapi statistics product-performance` |
| 商品表现 | `gerpgo-cli openapi statistics listing-performance` |
| 流量统计-ASIN | `gerpgo-cli openapi statistics asin-traffic-statistics` |
| 流量数据-ASIN | `gerpgo-cli openapi statistics asin-traffic-data` |
| 查询亚马逊店铺信息 | `gerpgo-cli openapi catalog amazon-shops list` |
| 查询所有用户列表 | `gerpgo-cli openapi catalog users list` |
| 查询仓库信息列表 | `gerpgo-cli openapi catalog warehouses list` |
| 查询品牌资料 | `gerpgo-cli openapi catalog brands list` |
| 查询品类信息 | `gerpgo-cli openapi catalog categories list` |
| 查询多平台店铺信息 | `gerpgo-cli openapi catalog multiplatform-shops list` |
| 根据亚马逊店铺id查询店铺名称 | `gerpgo-cli openapi catalog amazon-shops names-by-id` |
| 根据亚马逊店铺id查询仓库信息 | `gerpgo-cli openapi catalog amazon-shops warehouses-by-id` |

Read the selected command's `--help` before choosing fields. If a required
business condition is absent, ask the user instead of guessing. Primary fields
have dedicated flags. Additional fields documented for that registered
endpoint can be passed in a JSON object with `--input PATH`; unsupported fields
are rejected. `--input -` reads the object from stdin.

For ordinary “查一下” or “看看” requests, use the default first page. For
explicit “全部”, “完整”, “完整数据”, “完整分析”, “导出”, or “所有数据” intent,
automatically add `--all-pages --max-pages 100`; do not require the user to
understand these flags. The CLI estimates total pages from the first response,
enforces the registered interval, and either returns verified complete metadata
or a non-zero error. Never implement an AI-side page loop.

Business commands accept exact-name alternatives such as `--shop-name`,
`--warehouse-name`, `--product-manager-name`, `--selling-manager-name`,
`--brand-name`, and `--category-name`. Read
[catalog-resolution.md](catalog-resolution.md) before using them. Never pass the ID
flag and its name alternative together.
