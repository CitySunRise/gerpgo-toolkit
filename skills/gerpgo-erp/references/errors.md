# 错误处理

| 错误 | 下一步 |
|---|---|
| `GERPGO_CONFIG_MISSING` | 让用户在终端运行 `gerpgo-cli profile init prod`，或初始化用户选择的 profile。 |
| `GERPGO_SECRET_UNAVAILABLE` / `GERPGO_AUTH_FAILED` | 提示检查本机凭证或认证配置。 |
| `GERPGO_VALIDATION_ERROR` | 对照命令帮助补充或修正入参。 |
| `GERPGO_CATALOG_NOT_FOUND` / `GERPGO_CATALOG_AMBIGUOUS` | 补充完整名称、国家或 ID。 |
| `GERPGO_PAGE_LIMIT_EXCEEDED` | 展示总记录数、预计页数和耗时，询问是否提高 `--max-pages`。 |
| `GERPGO_API_ERROR` | 说明脱敏后的上游错误及所缺条件。 |
| `GERPGO_RATE_LIMITED` / `GERPGO_NETWORK_ERROR` | 按 CLI 提示等待或检查网络。 |

一次错误只修正有依据的条件，避免猜测参数反复请求。报错时不附带凭证、请求头或真实业务响应。
