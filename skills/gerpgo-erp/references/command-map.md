# Supported command map

Use the exact command matching the business request:

For exact method, path, official name, and interval details, read
[endpoint-registry.md](endpoint-registry.md).

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

Read the selected command's `--help` before choosing fields. Primary fields
have dedicated flags. Additional fields documented for that registered
endpoint can be passed in a JSON object with `--input PATH`; unsupported fields
are rejected. `--input -` reads the object from stdin.

Use `--all-pages --max-pages N` only when the user needs multiple pages and has
accepted the resulting request count. The CLI enforces the endpoint's official
request interval between pages.
