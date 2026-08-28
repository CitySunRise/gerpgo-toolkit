# Endpoint registry

All supported requests are read-only POST operations confirmed from the
official Gerpgo documentation.

| Official name | Document | Method and path | Minimum interval |
|---|---:|---|---:|
| 查询产品列表 | 53 | `POST /purchase/goods/product/page` | 0.5 seconds |
| 查询产品库存 | 15 | `POST /purchase/store/inventory/page` | 0.5 seconds |
| 销售表现 | 3375 | `POST /operation/sts/salesAnalysis/page` | 5 seconds |
| 搜索词表现 | 100 | `POST /operation/ads/adsKeywordAnalytical/query` | 60 seconds |
| Review | 1092 | `POST /operation/crm/review/page` | 1 second |
| 买家之声列表 | 1014 | `POST /operation/crm/customerVoice/page` | 1 second |
| 查询财务利润分析V2 | 2256 | `POST /finance/sts/financialAnalysis/page/V2` | 10 seconds |
| 关键词表现 | 99 | `POST /operation/ads/adsKeywordAnalytical/page` | 60 seconds |
| 产品表现 | 131 | `POST /operation/sts/productAnalyzeMultiIndex/page` | 60 seconds |
| 商品表现 | 140 | `POST /operation/sts/listingAnalyzeMultiIndex/page` | 5 seconds |
| 流量统计-ASIN | 122 | `POST /operation/sts/traffic/page` | 60 seconds |
| 流量数据-ASIN | 1018 | `POST /operation/sts/trafficAnalysis/page` | 60 seconds |
| 查询亚马逊店铺信息 | 153 | `POST /middle/base/market/page` | 1 second |
| 查询所有用户列表 | 25 | `POST /middle/base/allUser/list` with no business body | 1 second |
| 查询仓库信息列表 | 1035 | `POST /purchase/store/multiTypeWarehouse/page` | 0.5 seconds |
| 查询品牌资料 | 1752 | `POST /purchase/goods/brand/page` | 0.5 seconds |
| 查询品类信息 | 54 | `POST /purchase/goods/category/page` | 0.5 seconds |
| 查询多平台店铺信息 | 67 | `POST /platform/multiplatform/multiShop/query` with `{}` | 0.5 seconds |
| 根据亚马逊店铺id查询店铺名称 | 1177 | `POST /middle/base/marketNames/query` | 0.1 seconds |
| 根据亚马逊店铺id查询仓库信息 | 1179 | `POST /middle/base/warehouseIds/query` | 1 second |

Documents 25, 67, 1177, and 1179 currently have stale detail metadata that
says GET, while their public documentation pages specify POST. The registry
records the public-page verification date. Never implement or fall back to GET.
Document 1177 uses the exact official request field `markerIds`; document 1179
uses `marketIdList`.

`gerpgo-cli capabilities --format json` is the runtime source of truth. If it
does not list an interface, do not invoke it.

The official documents publish maximum page size for most endpoints but do not
publish a maximum page count. Do not invent one. `--max-pages` is a local safety
cap for an explicitly requested multi-page operation, not an official limit.
