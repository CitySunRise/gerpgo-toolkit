---
name: gerpgo-erp
description: >-
  使用 gerpgo-cli 配置和查询积加 ERP。适用于 gerpgo-erp、Gerpgo、gerpgo-cli、积加、积加 ERP、积加 CLI、积加开放接口，以及积加产品、库存、销售表现、Review、买家之声、利润、ASIN、关键词查询和积加配置、登录、会话，也支持采购、调拨、货件装箱、分类账、报表和多平台查询。
metadata:
  version: "0.3.2"
  requires:
    bins: ["gerpgo-cli"]
  cliHelp: "gerpgo-cli --help"
---

# 积加 ERP

通过 `gerpgo-cli` 完成查询和登录。用户只说“积加”时，先问要查询或配置什么。

## 配置与登录

- 未指定 profile 时使用 `prod`，无需反复确认。优先级：显式 `--profile` > `GERPGO_PROFILE` > `prod`。
- 首次使用或缺少配置时，按 [initialization.md](references/initialization.md) 初始化。
- “积加登录”调用 `gerpgo-cli web auth login`；会话操作见 [web-auth.md](references/web-auth.md)。

## 查询

1. 用 `gerpgo-cli capabilities --format json` 查接口及入参，再看所选命令的 `--help`。枚举、默认值、日期格式以 CLI 为准。
2. 常用查询见 [command-map.md](references/command-map.md) 和 [endpoint-parameters.md](references/endpoint-parameters.md)；其他模块见 [expanded-queries.md](references/expanded-queries.md)。
3. 从用户需求确定产品、店铺及日期范围。必要的单号、SKU、ASIN、市场或仓库 ID 可从相关查询取得；仍缺少业务条件时只问缺少的部分，条件齐全后直接调用。
4. 用户提供名称时优先使用 `--*-name` 参数，详见 [catalog-resolution.md](references/catalog-resolution.md)。标识符按文本处理。
5. 普通查询默认一页。“全部、完整数据、完整分析、导出、所有数据”自动加 `--all-pages --max-pages 100`。分析全量数据前检查 `pagination.complete=true`、`pagination.truncated=false`；超过上限时展示页数和耗时估计，再询问是否提高上限。
6. 默认解析 JSON；用户要原始响应时加 `--response raw --format json`。复杂对象用 `--input -` 传入 JSON。

凭证由用户在终端配置，不写入聊天、命令或仓库。通过 CLI 保持查询范围和串行分页；本工具提供只读 OpenAPI 与 Web 登录会话，不在二者间静默切换。

遇到错误按 [errors.md](references/errors.md) 处理；凭证及输出注意事项见 [openapi-safety.md](references/openapi-safety.md)。
