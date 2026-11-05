# 名称与 ID

用户知道店铺、仓库、负责人、品牌或品类名称时，优先使用业务命令的名称参数：

```shell
gerpgo-cli openapi inventory product --warehouse-name 示例仓 --sku SKU-DEMO-001
gerpgo-cli openapi ads keyword-performance --shop-name 示例店铺 --country-code US --start-date 2026-01-01 --end-date 2026-01-01
gerpgo-cli openapi product list --brand-name 示例品牌 --category-name 示例品类
```

CLI 按去除首尾空格后的完整名称匹配；同名时补充国家或 ID。ID 与对应名称参数选用一种即可。当前支持的关系见 `gerpgo-cli capabilities --format json` 的 `catalog_resolution`。

需要直接取得名称或标识时，用 [command-map.md](command-map.md) 中的目录查询。订单号、SKU、ASIN 等也可从对应业务列表获取，并保留原查询范围；详情查询使用同一条记录的关联标识。
