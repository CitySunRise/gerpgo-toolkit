# 初始化

profile 优先级：显式 `--profile NAME` > `GERPGO_PROFILE` > `prod`。未另作选择时直接使用 prod，无需每次确认。

先查看本地状态：

```shell
gerpgo-cli version
gerpgo-cli profile list --format json
```

缺少 prod 时，让用户在自己的终端运行：

```shell
gerpgo-cli profile init prod
```

交互输入开放 App ID/App Key；需要 Web 登录时同时配置 Web 账号。凭证保存在 macOS Keychain 或 Windows Credential Manager，profile JSON 只存非敏感设置。不要在聊天或命令参数中填写凭证，也不要自动新建或切换 profile。

已通过环境变量配置凭证的机器可运行：

```shell
gerpgo-cli profile init prod --from-env --enable-web
```

初始化后运行本地自检：

```shell
gerpgo-cli doctor --read-only --format json
```

需要测试开放认证连接时增加 `--connectivity`；Web 登录使用 `gerpgo-cli web auth login`。
