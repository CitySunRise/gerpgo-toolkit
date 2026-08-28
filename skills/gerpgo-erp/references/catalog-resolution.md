# Catalog lookup and exact name resolution

Read `gerpgo-cli capabilities --format json` first. Its
`catalog_resolution` section is authoritative for current name/ID relations.
The SDK, not this Skill, implements matching and conversion.

## Rules

- Prefer a business command's `--*-name` option when the user supplied a name.
- Matching trims surrounding whitespace and is otherwise exact. Never choose a
  partial, similar, or fuzzy result.
- Amazon shops match either official `store` or `marketName`. If duplicates
  exist, ask for `--country` or `--country-code`, or ask for an explicit ID.
- Do not pass an ID/code option and the corresponding name option together.
- `GERPGO_CATALOG_NOT_FOUND` means ask the user to check the exact name.
- `GERPGO_CATALOG_AMBIGUOUS` means ask for a disambiguating condition or ID.
- IDs remain strings in CLI input/output. The SDK converts them to the
  documented OpenAPI numeric type only at the request boundary.
- Never access raw catalog responses. The CLI intentionally omits credentials,
  tokens, contacts, addresses, authorization state, and server/account fields.

## Safe directory inspection

Use only when the user asks to inspect a directory or needs help resolving an
ambiguous name:

```shell
gerpgo-cli openapi catalog amazon-shops list --format json
gerpgo-cli openapi catalog users list --format json
gerpgo-cli openapi catalog warehouses list --format json
gerpgo-cli openapi catalog brands list --format json
gerpgo-cli openapi catalog categories list --format json
gerpgo-cli openapi catalog multiplatform-shops list --format json
```

Examples of direct resolution within business commands:

```shell
gerpgo-cli openapi inventory product --warehouse-name 示例仓 --sku SKU-DEMO-001 --format json
gerpgo-cli openapi ads keyword-performance --shop-name 示例店铺 --country-code US --start-date 2026-01-01 --end-date 2026-01-01 --format json
gerpgo-cli openapi product list --brand-name 示例品牌 --category-name 示例品类 --format json
```

All values above are synthetic.
