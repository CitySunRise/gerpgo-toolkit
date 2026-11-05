# Web 登录与会话

“积加登录”使用 login；“积加会话状态”使用 status；“积加退出登录”使用 logout：

```shell
gerpgo-cli web auth login --format json
gerpgo-cli web auth status --format json
gerpgo-cli web auth logout --format json
```

默认使用 prod；显式 `--profile NAME` 或 `GERPGO_PROFILE` 可覆盖。缺少配置时按 [initialization.md](initialization.md) 初始化。

login 使用本地保存的账号登录并缓存会话；status 查看本地会话；logout 清除本地缓存。此处仅管理登录会话，业务查询使用 OpenAPI。
