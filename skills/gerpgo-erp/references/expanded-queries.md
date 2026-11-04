# Expanded read-only modules

Search official_name in `gerpgo-cli capabilities --format json` for the user's
business intent. Each expanded entry supplies its exact cli_command. Modules
include base, sales, ads, customer, statistics, product, inventory, orders,
procurement, logistics, warehouse, finance, reports and multiplatform.

Synthetic examples:

- 调拨列表: `gerpgo-cli openapi inventory transfer-page --code-list TF-DEMO`
- 调拨详情: `gerpgo-cli openapi inventory transfer-detail --code TF-DEMO`
- 调拨装箱: `gerpgo-cli openapi logistics delivery-carton-query --item-type 2 --relate-code TF-DEMO`
- 批次库存: `gerpgo-cli openapi inventory storage-serial-page --sku-list SKU-DEMO`
- 批次流水: `gerpgo-cli openapi inventory storage-serial-flow-page --related-orders TF-DEMO`
- STA: `gerpgo-cli openapi logistics sta-shipment-info-detail --inbound-plan-id PLAN-DEMO`
- STA 装箱: `gerpgo-cli openapi logistics sta-shipment-box-info-query --input request.json`
  where request.json is `{"shipmentItemQueryDTOS":[{"shipmentId":"SHIPMENT-DEMO"}]}`.

Required fields, enums, date formats and intervals live only in the SDK. Read
--help for scalar/list filters; use --input file or --input - for nested fields.
Required fields may come from --input. CLI defaults do not override input values.
Keep identifiers text in user-facing commands; requests use official numeric types.

Choose OpenAPI first. There is no Web business supplement. Document 2453 allows
transfer cartons, but batch flows are not asserted identical to core transfer
inventory serials. Do not construct raw URLs, writes or unsupported methods.

Ordinary queries fetch one page. Complete intent adds --all-pages --max-pages 100.
Check supports_auto_pagination. Missing pagination contracts block full queries;
never implement an AI-side page loop. Deal/coupon use count/nextId with extObj
as the next cursor and require a documented date range. Preserve the user's scope.

For 原始/完整 JSON add --response raw --format json. Single responses preserve
the upstream envelope inside CLI data. Full queries contain pages and pagination.
Require complete=true and truncated=false. Business IDs, unknown fields and
Trace IDs are preserved; App Keys, passwords, tokens, cookies and sessions are
protected. Never copy real query results into the repository or release files.

An absent capabilities entry is not implemented. The repository inventory records
blocked prose enums, missing rate periods and unverified PostParam transport.
