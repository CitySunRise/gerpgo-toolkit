# Endpoint registry

All supported requests are read-only POST operations confirmed from the
official Gerpgo documentation.

| Official name | Path | Minimum interval |
|---|---|---:|
| 查询产品列表 | `/purchase/goods/product/page` | 0.5 seconds |
| 查询产品库存 | `/purchase/store/inventory/page` | 0.5 seconds |
| 销售表现 | `/operation/sts/salesAnalysis/page` | 5 seconds |
| 搜索词表现 | `/operation/ads/adsKeywordAnalytical/query` | 60 seconds |
| Review | `/operation/crm/review/page` | 1 second |
| 买家之声列表 | `/operation/crm/customerVoice/page` | 1 second |
| 查询财务利润分析V2 | `/finance/sts/financialAnalysis/page/V2` | 10 seconds |
| 关键词表现 | `/operation/ads/adsKeywordAnalytical/page` | 60 seconds |
| 产品表现 | `/operation/sts/productAnalyzeMultiIndex/page` | 60 seconds |
| 商品表现 | `/operation/sts/listingAnalyzeMultiIndex/page` | 5 seconds |
| 流量统计-ASIN | `/operation/sts/traffic/page` | 60 seconds |
| 流量数据-ASIN | `/operation/sts/trafficAnalysis/page` | 60 seconds |

`gerpgo-cli capabilities --format json` is the runtime source of truth. If it
does not list an interface, do not invoke it.
