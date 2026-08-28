# OpenAPI endpoint parameters

The SDK contract exposed by `gerpgo-cli capabilities --format json` is the
authoritative source for fields, types, required values, enums, dates, defaults,
constraints, document IDs, and request intervals. This file explains routing
and provides synthetic examples; it is not a second enum implementation. Read
the selected command's `--help` and its capabilities entry before execution.

When a condition listed below is missing, ask only for that business condition.
Do not guess it. Once all required conditions are known, make one correctly
formed call without reconfirming unrelated defaults. All commands default to
profile `prod` and JSON output is preferred.

## Shared pagination behavior

Ordinary requests fetch one page. Explicit requests for “全部”, “完整”,
“完整数据”, “完整分析”, “导出”, or “所有数据” use
`--all-pages --max-pages 100`. Do not ask the user to supply these flags and do
not implement an AI-side page loop. A complete result must report
`pagination.complete=true` and `pagination.truncated=false`.

SDK-owned default page sizes:

| Interface | Default `pagesize` |
|---|---:|
| 销售表现 | 200 |
| 产品表现 | 100 |
| 商品表现 | 100 |
| 流量统计-ASIN | 500 |
| 流量数据-ASIN | 500 |
| Other seven business queries | 100 |

For the five `/operation/sts/*` interfaces above, runtime error 40004 reports
an accepted range of 10 through 1000, while current official documentation
still says maximum 100 for four interfaces and recommends no more than 200 for
销售表现. These are separate contract facts in `capabilities`; never replace
the official documentation record with the runtime constraint. Before this
release, `pagesize=500` succeeded for 销售表现、流量统计-ASIN、流量数据-ASIN.
It failed for 产品表现 and 商品表现 under the same read-only scope, while
`pagesize=10` and `pagesize=100` succeeded, so those two defaults remain 100.

If `GERPGO_PAGE_LIMIT_EXCEEDED` is returned, show the safe page estimate and
estimated duration, then ask whether to retry with a higher `--max-pages`.
Never silently return partial data.

## Shared official currency enum

The official currency Q&A (document 11) currently defines:

`YUAN` 原币种; `USD` 美元; `JPY` 日元; `GBP` 英镑; `EUR` 欧元;
`CAD` 加元; `MXN` 墨西哥比索; `AUD` 澳大利亚元; `INR` 印度卢比;
`CNY` 人民币; `AED` 阿联酋迪拉姆; `SGD` 新加坡元;
`SAR` 沙特里亚尔; `BRL` 巴西雷亚尔; `SEK` 瑞典克朗;
`TRY` 土耳其里拉; `PLN` 波兰兹罗提; `HKD` 港币; `ANG` 荷兰盾;
`CHF` 瑞士法郎; `RON` 罗马尼亚新列伊; `MYR` 林吉特;
`VND` 越南盾; `PHP` 菲律宾比索; `THB` 泰国铢; `IDR` 印尼卢比;
`COP` 哥伦比亚比索; `CLP` 智利比索; `TWD` 新台币;
`KRW` 韩国元; `CNH` 离岸人民币; `NGN` 尼日利亚奈拉;
`BYN` 白俄罗斯卢布; `KZT` 哈萨克斯坦坚戈;
`RUB` 俄罗斯卢布; `BGN` 保加利亚列弗; `HUF` 匈牙利福林;
`EGP` 埃及镑; `ZAR` 南非兰特.

Always re-read capabilities instead of relying on this explanatory snapshot.

## 1. 查询产品列表

- Command: `gerpgo-cli openapi product list`
- Required by the API: one pagination mode; the CLI supplies direct `page=1`
  and `pagesize=100` by default.
- Obtain before calling: a SKU/MSKU/brand/category/date scope, unless the user
  explicitly requested a broad first page.
- Enums: `state`: `0` 正常, `1` 停用; `dateType`: `0` 创建时间,
  `1` 更新时间.
- Dates: `startDate` and `endDate` use `yyyy-MM-dd`.
- Dynamic identifiers: brand/category codes, SKU, platform MSKU, and MSKU.
- Constraint: use direct `page`/`pagesize` or `pageInfo`, never both; maximum
  page size is 100. The official document does not publish a maximum page count.
- Synthetic minimum example:
  `gerpgo-cli openapi product list --sku SKU-DEMO-001 --format json`

## 2. 查询产品库存

- Command: `gerpgo-cli openapi inventory product`
- Required by the API: `page` and `pagesize`; CLI defaults are 1 and 100.
- Obtain before calling: a product, warehouse, or responsible-person scope,
  unless the user explicitly requested a broad first page.
- Enums: `productState`: `0` 正常, `1` 停用; `productTypeList`: `0` 成品,
  `1` 包材, `2` 组合产品, `3` 半成品; `state`: `0` 异常, `1` 正常.
- Dynamic identifiers: warehouse IDs, product/sales responsible-person IDs,
  SKU, ASIN, and MSKU. They are account data, not fixed enums.
- Boolean: `--filter-quantity` / `--no-filter-quantity`.
- Maximum page size 100; SKU/ASIN/MSKU lists maximum 50 items.
- Synthetic minimum example:
  `gerpgo-cli openapi inventory product --sku SKU-DEMO-001 --format json`

## 3. 销售表现

- Command: `gerpgo-cli openapi statistics sales-performance`
- CLI default `pagesize` is 200, preserving the official recommendation.
- Required: grouping, currency, start date, and end date.
- Enums: `groupByType`: `seller_sku` msku, `asin` asin,
  `variation_asin` 父asin, `sku` sku, `spu` spu, `country` 国家,
  `market` 店铺, `date` 日期. `viewType`: `DAY` 日, `WEEK` 周,
  `MONTH` 月. Currency uses the shared official enum.
- Dates: `beginDate` and `endDate` use `yyyy-MM-dd`.
- Constraint: `viewType` is required when `groupByType=date`; recommended page
  size is no more than 200. The official document does not publish a maximum.
- Dynamic identifiers: SKU, parent ASIN, ASIN, and MSKU.
- Synthetic minimum example:
  `gerpgo-cli openapi statistics sales-performance --group-by-type seller_sku --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --format json`

## 4. 搜索词表现

- Command: `gerpgo-cli openapi ads search-term-performance`
- Required: account-specific `marketId`, start date, and end date. Pagination is
  also required and supplied by CLI defaults.
- Enums: none published.
- Dates: `startDateData` and `endDateData` use `yyyy-MM-dd` and must be the same
  day.
- Dynamic identifiers: `marketId`; obtain it from the user's Gerpgo account.
- Maximum page size 100. Official request interval: 60 seconds.
- Synthetic minimum example:
  `gerpgo-cli openapi ads search-term-performance --market-id 100001 --start-date 2026-01-01 --end-date 2026-01-01 --format json`

## 5. Review

- Command: `gerpgo-cli openapi customer review`
- Required by the API: pagination, supplied by CLI defaults.
- Obtain before calling: review/order/ASIN/market/date/status scope, unless the
  user explicitly requested a broad first page.
- Enums: `states`: `0` 未处理, `1` 处理中, `2` 已完成, `3` 无;
  `results`: `0` 无, `1` 无变化-客户不同意, `3` 已删除,
  `4` 无变化-邮件无回复, `5` 分数变化-调高, `6` 分数变化-调低;
  `nameMatchType`: `fuzzyMatch` 模糊匹配, `exact` 精准匹配,
  `contactBuyer` 亚马逊, `handAdd` 手动发送.
- Dates: create/update ranges use `yyyy-MM-dd HH:mm:ss`; review ranges use
  `yyyy-MM-dd`.
- Dynamic identifiers: review IDs, market IDs, order IDs, and ASINs.
- Maximum page size 100.
- Synthetic minimum example:
  `gerpgo-cli openapi customer review --asin ASIN-DEMO-001 --state 0 --format json`

## 6. 买家之声列表

- Command: `gerpgo-cli openapi customer buyer-voice`
- Required by the API: pagination, supplied by CLI defaults.
- Obtain before calling: product/market/health scope, unless the user explicitly
  requested a broad first page.
- Enum `pcxHealth`: `Good` 良好, `Excellent` 优秀, `Fair` 一般,
  `Poor` 不佳, `Verypoor` 极差.
- Dynamic identifiers: market IDs, SKU, MSKU, and ASIN. Product name is free
  text, not an enum.
- Maximum page size 100.
- Synthetic minimum example:
  `gerpgo-cli openapi customer buyer-voice --asin ASIN-DEMO-001 --pcx-health Good --format json`

## 7. 查询财务利润分析V2

- Command: `gerpgo-cli openapi finance profit-analysis-v2`
- Required: query type, cost rule, currency, date type, and pagination.
- Enum `queryType`: `market`, `category`, `father_asin`, `asin`, `spu`, `sku`,
  `msku`. The official document publishes these raw values but no Chinese label;
  do not invent one.
- Enum `costValues`: `0` 先进先出, `1` 月末平均, `2` 自定义成本,
  `3` 混合成本. Enum `dateType`: `0` 按开始日期与结束日期,
  `1` 按月份. Currency uses the shared official enum.
- Dates: `dateType=0` requires `startDate` and `endDate` as `yyyy-MM-dd`;
  `dateType=1` requires `monthDate` as `yyyy-MM`.
- `platformCodes`: official default is `AMAZON`, but the official document does
  not publish a complete enum. Do not validate or suggest other values as fixed
  choices.
- Dynamic identifiers: market IDs, category codes, brand codes, MSKU, SKU, and
  ASIN. Decimal places must be 2 through 8.
- Boolean: `--footer-expand-details` / `--no-footer-expand-details`.
- Synthetic minimum example:
  `gerpgo-cli openapi finance profit-analysis-v2 --query-type sku --cost-values 0 --currency YUAN --date-type 0 --start-date 2026-01-01 --end-date 2026-01-01 --sku SKU-DEMO-001 --format json`

## 8. 关键词表现

- Command: `gerpgo-cli openapi ads keyword-performance`
- Required: account-specific `marketId`, start date, and end date. Pagination is
  supplied by CLI defaults.
- Enums: none published.
- Dates: `startDateData` and `endDateData` use `yyyy-MM-dd` and must be the same
  day.
- Dynamic identifiers: `marketId`; obtain it from the user's Gerpgo account.
- Maximum page size 100. Official request interval: 60 seconds.
- Synthetic minimum example:
  `gerpgo-cli openapi ads keyword-performance --market-id 100001 --start-date 2026-01-01 --end-date 2026-01-01 --format json`

## 9. 产品表现

- Command: `gerpgo-cli openapi statistics product-performance`
- CLI default `pagesize` is the verified value 100; 500 failed in the current
  read-only runtime check.
- Required: currency, start date, end date, and pagination.
- Enum: currency uses the shared official enum.
- Dates: `beginDate` and `endDate` use `yyyy-MM-dd`.
- Maximum page size 100. Official request interval: 60 seconds.
- Synthetic minimum example:
  `gerpgo-cli openapi statistics product-performance --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --format json`

## 10. 商品表现

- Command: `gerpgo-cli openapi statistics listing-performance`
- CLI default `pagesize` is the verified value 100; 500 failed in the current
  read-only runtime check.
- Required: grouping, currency, start date, end date, show-total choice, and
  pagination.
- Enum `groupByType`: `asin` ASIN维度, `seller_sku` MSKU维度. Currency uses
  the shared official enum.
- Dates: `beginDate` and `endDate` use `yyyy-MM-dd`.
- Dynamic identifiers: market IDs, SKU, ASIN, and MSKU. ASIN/MSKU lists are
  recommended to contain no more than 20 values.
- Boolean: `--show-total` / `--no-show-total`. Maximum page size 100.
- Synthetic minimum example:
  `gerpgo-cli openapi statistics listing-performance --group-by-type asin --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --no-show-total --asin ASIN-DEMO-001 --format json`

## 11. 流量统计-ASIN

- Command: `gerpgo-cli openapi statistics asin-traffic-statistics`
- CLI default `pagesize` is the verified value 500.
- Required: currency, start date, end date, view type, and pagination.
- Enum `viewType`: lowercase `day` 日, `week` 周, `month` 月. Currency uses
  the shared official enum.
- Dates: `beginDate` and `endDate` use `yyyy-MM-dd`.
- Dynamic identifiers: market IDs. Maximum page size 100. Official request
  interval: 60 seconds.
- Synthetic minimum example:
  `gerpgo-cli openapi statistics asin-traffic-statistics --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --view-type day --market-id 100001 --format json`

## 12. 流量数据-ASIN

- Command: `gerpgo-cli openapi statistics asin-traffic-data`
- CLI default `pagesize` is the verified value 500.
- Required: currency, start date, end date, and pagination.
- Enum: currency uses the shared official enum.
- Dates: `beginDate` and `endDate` use `yyyy-MM-dd`.
- Dynamic identifiers: market IDs. Maximum page size 100. Official request
  interval: 60 seconds.
- Synthetic minimum example:
  `gerpgo-cli openapi statistics asin-traffic-data --currency YUAN --begin-date 2026-01-01 --end-date 2026-01-01 --market-id 100001 --format json`

## 13. 查询亚马逊店铺信息

- Command: `gerpgo-cli openapi catalog amazon-shops list`
- Required request fields: `page`, `pagesize`, and `condition`; the CLI supplies
  safe defaults. Maximum page size is 100.
- Optional condition fields: account-dynamic `marketIds`, and
  `recordDateStart`/`recordDateEnd` in `yyyy-MM-dd HH:mm:ss`.
- Safe output only: market ID, `marketName`, `store`, country code/name, area,
  and state. Never seek omitted token, session, server, account, or auth fields.
- Synthetic minimum example:
  `gerpgo-cli openapi catalog amazon-shops list --format json`

## 14. 查询所有用户列表

- Command: `gerpgo-cli openapi catalog users list`
- The registered call is POST with no business request body. Never use GET.
- Safe output only: textual ID, name, username, and status. Phone, email,
  organization, role, and other contact/identity fields are intentionally
  omitted.
- Synthetic minimum example:
  `gerpgo-cli openapi catalog users list --format json`

## 15. 查询仓库信息列表

- Command: `gerpgo-cli openapi catalog warehouses list`
- Required: `model`, `page`, `pagesize`; CLI supplies them. Maximum page size
  is 100.
- Enum `status`: `enable` 启用, `disable` 停用.
- Enum `typeList`: `SELF` 自营仓, `SUPPLIER` 供应商仓, `FBA` Amazon.FBA,
  `THIRD` 三方仓, `WFS` Walmart, `FULL` MercadoLibre, `EBAY` eBay,
  `ALIEXPRESS` AliExpress自运营, `AMAZON_VC` Amazon.VC,
  `AMAZON_AWD` Amazon.AWD, `CDISCOUNT_FBC` Cdiscount,
  `WAYFAIR_CG` Wayfair, `EMAG_FBE` eMAG, `TIKTOK_FBT` Tiktok自运营,
  `WILDBERRIES_FBW` Wildberries, `YANDEX_FBY` Yandex, `OZON_FBO` Ozon.
- `warehouseIdList` is dynamic. Dates use `yyyy-MM-dd HH:mm:ss`.
- Safe output intentionally omits contacts, addresses, service-provider keys,
  tokens, domains, and authorization fields.
- Synthetic minimum example:
  `gerpgo-cli openapi catalog warehouses list --name 示例仓 --format json`

## 16. 查询品牌资料

- Command: `gerpgo-cli openapi catalog brands list`
- Required: page and page size, supplied by the CLI. The official document
  publishes no maximum page size.
- Enum `state`: `Active` 启用, `Inactive` 停用. Name and code filters are
  officially fuzzy, but business-command resolution still requires an exact
  unique returned name.
- Synthetic minimum example:
  `gerpgo-cli openapi catalog brands list --name 示例品牌 --format json`

## 17. 查询品类信息

- Command: `gerpgo-cli openapi catalog categories list`
- Required: page and page size, supplied by the CLI; maximum page size 100.
- Enum `state`: `Active` 启用, `Inactive` 停用. `valueList` contains dynamic
  category codes as text.
- Synthetic minimum example:
  `gerpgo-cli openapi catalog categories list --value CATEGORY-DEMO --format json`

## 18. 查询多平台店铺信息

- Command: `gerpgo-cli openapi catalog multiplatform-shops list`
- The registered call is POST with exactly `{}` as its business body. Never use
  GET or add unregistered filters.
- Shop ID and platform ID are dynamic textual identifiers; platform values are
  not a fixed enum. Authorization state is intentionally omitted.
- Synthetic minimum example:
  `gerpgo-cli openapi catalog multiplatform-shops list --format json`

## 19. 根据亚马逊店铺id查询店铺名称

- Command: `gerpgo-cli openapi catalog amazon-shops names-by-id`
- Required exact official field: `markerIds` (`--market-id` in CLI). Do not
  correct the official spelling to `marketIds`.
- IDs are entered and returned as text; SDK converts request values to integers.
- Synthetic minimum example:
  `gerpgo-cli openapi catalog amazon-shops names-by-id --market-id 100001 --format json`

## 20. 根据亚马逊店铺id查询仓库信息

- Command: `gerpgo-cli openapi catalog amazon-shops warehouses-by-id`
- Required exact official field: `marketIdList` (`--market-id` in CLI).
- Market and warehouse IDs are dynamic and represented as text in output.
- Synthetic minimum example:
  `gerpgo-cli openapi catalog amazon-shops warehouses-by-id --market-id 100001 --format json`
