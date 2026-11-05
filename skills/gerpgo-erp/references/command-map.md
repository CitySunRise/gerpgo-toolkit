# 常用查询命令

默认 profile 为 `prod`。查询前用 `gerpgo-cli capabilities --format json` 和命令的 `--help` 获取入参；条件与示例见 [endpoint-parameters.md](endpoint-parameters.md)。

| 查询 | 命令 |
|---|---|
| 产品资料 | `gerpgo-cli openapi product list` |
| 产品库存 | `gerpgo-cli openapi inventory product` |
| 销售表现 | `gerpgo-cli openapi statistics sales-performance` |
| 搜索词表现 | `gerpgo-cli openapi ads search-term-performance` |
| Review | `gerpgo-cli openapi customer review` |
| 买家之声 | `gerpgo-cli openapi customer buyer-voice` |
| 财务利润分析 | `gerpgo-cli openapi finance profit-analysis-v2` |
| 关键词表现 | `gerpgo-cli openapi ads keyword-performance` |
| 商品表现 | `gerpgo-cli openapi statistics listing-performance` |
| 流量统计-ASIN | `gerpgo-cli openapi statistics asin-traffic-statistics` |
| 流量数据-ASIN | `gerpgo-cli openapi statistics asin-traffic-data` |
| 亚马逊店铺 | `gerpgo-cli openapi catalog amazon-shops list` |
| 负责人 | `gerpgo-cli openapi catalog users list` |
| 仓库 | `gerpgo-cli openapi catalog warehouses list` |
| 品牌 | `gerpgo-cli openapi catalog brands list` |
| 品类 | `gerpgo-cli openapi catalog categories list` |
| 多平台店铺 | `gerpgo-cli openapi catalog multiplatform-shops list` |
| 店铺 ID 查名称 | `gerpgo-cli openapi catalog amazon-shops names-by-id` |
| 店铺 ID 查仓库 | `gerpgo-cli openapi catalog amazon-shops warehouses-by-id` |

采购、调拨、货件、装箱、库存流水、报表等命令从 capabilities 的 `official_name` 和 `cli_command` 查找，见 [expanded-queries.md](expanded-queries.md)。
