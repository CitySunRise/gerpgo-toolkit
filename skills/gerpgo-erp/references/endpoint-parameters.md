# 常用查询入参

用 `gerpgo-cli capabilities --format json` 或对应命令的 `--help` 查看完整字段、枚举及默认值；本页给出业务条件和最小示例。标识均为虚构值，实际 ID 从目录或相关业务查询取得。

默认 prod、JSON 输出、第一页。全量分析加 `--all-pages --max-pages 100`；嵌套 JSON 用 `--input -`。币种 `YUAN` 表示原币种，其他币种按需求从帮助中选择。

## 查询产品列表

可按 SKU、MSKU、品牌、品类或创建/更新日期筛选；日期为 yyyy-MM-dd。分页由 CLI 默认提供，使用直接分页时无需再传 pageInfo。

示例：`gerpgo-cli openapi product list --sku SKU-DEMO-001 --format json`

## 查询产品库存

按 SKU、ASIN、MSKU、仓库或负责人筛选；名称可用 --warehouse-name 等参数解析。库存数量筛选使用 --filter-quantity / --no-filter-quantity。

示例：`gerpgo-cli openapi inventory product --sku SKU-DEMO-001 --format json`

## 销售表现

需要统计维度、币种及起止日期（yyyy-MM-dd）；例如按 SKU 或 ASIN 汇总，具体 groupByType 取值见帮助。默认每页 200 条。

示例：`gerpgo-cli openapi statistics sales-performance --group-by-type seller_sku --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --format json`

## 搜索词表现

需要店铺/市场及日期；--start-date 与 --end-date 均为 yyyy-MM-dd，且必须是同一天。

示例：`gerpgo-cli openapi ads search-term-performance --market-id 100001 --start-date 2026-01-01 --end-date 2026-01-01 --format json`

## Review

可按 ASIN、订单、店铺、处理状态或日期筛选。评论日期用 yyyy-MM-dd，创建/更新时间用 yyyy-MM-dd HH:mm:ss。

示例：`gerpgo-cli openapi customer review --asin ASIN-DEMO-001 --state 0 --format json`

## 买家之声列表

可按 ASIN、SKU、MSKU、店铺、产品名称或健康状况筛选；pcxHealth 的选项见帮助。

示例：`gerpgo-cli openapi customer buyer-voice --asin ASIN-DEMO-001 --pcx-health Good --format json`

## 查询财务利润分析V2

需要查询维度、成本规则、币种和日期类型。--date-type 0 配合起止日期 yyyy-MM-dd；--date-type 1 配合 --month-date yyyy-MM。产品或店铺范围按用户需求传入。

示例：`gerpgo-cli openapi finance profit-analysis-v2 --query-type sku --cost-values 0 --currency YUAN --date-type 0 --start-date 2026-01-01 --end-date 2026-01-01 --sku SKU-DEMO-001 --format json`

## 关键词表现

需要店铺/市场及日期；--start-date 与 --end-date 为 yyyy-MM-dd，且必须是同一天。

示例：`gerpgo-cli openapi ads keyword-performance --market-id 100001 --start-date 2026-01-01 --end-date 2026-01-01 --format json`

## 商品表现

需要 --group-by-type、币种、起止日期（yyyy-MM-dd）及合计选项 --show-total / --no-show-total。按需求传 ASIN、MSKU 或店铺范围。

示例：`gerpgo-cli openapi statistics listing-performance --group-by-type asin --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --no-show-total --asin ASIN-DEMO-001 --format json`

## 流量统计-ASIN

需要币种、起止日期（yyyy-MM-dd）和 --view-type；日维度可用 day。可按市场、产品等条件筛选，默认每页 500 条。

示例：`gerpgo-cli openapi statistics asin-traffic-statistics --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --view-type day --market-id 100001 --format json`

## 流量数据-ASIN

需要币种及起止日期（yyyy-MM-dd）；可按店铺/市场筛选，默认每页 500 条。

示例：`gerpgo-cli openapi statistics asin-traffic-data --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --market-id 100001 --format json`

## 查询亚马逊店铺信息

可直接列出目录，也可按店铺 ID 或名称筛选。CLI 自动提供分页及 condition。

示例：`gerpgo-cli openapi catalog amazon-shops list --format json`

## 查询所有用户列表

无业务必填参数，用于取得负责人 ID 与名称。

示例：`gerpgo-cli openapi catalog users list --format json`

## 查询仓库信息列表

可按名称、ID、状态或仓库类型筛选；CLI 自动提供 model 和分页。嵌套筛选用 --input。

示例：`gerpgo-cli openapi catalog warehouses list --name 示例仓 --format json`

## 查询品牌资料

可按名称或品牌编码筛选；状态选项见帮助。

示例：`gerpgo-cli openapi catalog brands list --name 示例品牌 --format json`

## 查询品类信息

可按品类编码、名称或状态筛选。

示例：`gerpgo-cli openapi catalog categories list --value CATEGORY-DEMO --format json`

## 查询多平台店铺信息

无业务必填参数，用于取得多平台店铺目录。

示例：`gerpgo-cli openapi catalog multiplatform-shops list --format json`

## 根据亚马逊店铺id查询店铺名称

需要 --market-id；官方原始字段拼写为 markerIds，CLI 已完成转换。

示例：`gerpgo-cli openapi catalog amazon-shops names-by-id --market-id 100001 --format json`

## 根据亚马逊店铺id查询仓库信息

需要 --market-id；官方原始字段为 marketIdList，CLI 已完成转换。

示例：`gerpgo-cli openapi catalog amazon-shops warehouses-by-id --market-id 100001 --format json`
