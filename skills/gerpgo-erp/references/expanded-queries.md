# 其他查询模块

用 `gerpgo-cli capabilities --format json` 按 `official_name` 找到接口，并使用它的 `cli_command`。模块包括基础数据、销售、广告、客服、统计、产品、库存、订单、采购、物流、仓库、财务、报表和多平台。

## 入参与条件

- `fields` 提供字段类型、必填项、枚举及日期格式；`pagination` 提供页大小与全量分页选项。具体 CLI 参数见所选命令的 `--help`。
- 必要单号从对应列表取得，详情使用同一条记录的 ID。SKU、ASIN、市场和仓库 ID 来自产品、商品、店铺及仓库查询。
- 日期按用户需求选取。只支持月份的接口用 `yyyy-MM`；库存快照可直接按产品或仓库筛选。缺少业务范围时询问所缺条件。
- 嵌套对象或对象数组用 `--input -` 传入 JSON；普通字段可直接用命令参数。

## 示例

以下标识均为虚构值：

```shell
gerpgo-cli openapi inventory transfer-page --status draft --create-date-start 2026-01-01 --create-date-end 2026-01-01
gerpgo-cli openapi inventory transfer-detail --code TF-DEMO
gerpgo-cli openapi logistics delivery-carton-query --item-type 2 --relate-code TF-DEMO
gerpgo-cli openapi inventory storage-serial-page --sku-list SKU-DEMO
gerpgo-cli openapi inventory storage-serial-flow-page --related-orders TF-DEMO
gerpgo-cli openapi logistics sta-shipment-box-info-query --input -
```

最后一条通过 stdin 传入：

```json
{"shipmentItemQueryDTOS":[{"shipmentId":"SHIPMENT-DEMO"}]}
```

普通查询一页；全量查询加 `--all-pages --max-pages 100`。原始 JSON 加 `--response raw --format json`；全量原始响应放在 `pages`，完整性信息放在 `pagination`。
