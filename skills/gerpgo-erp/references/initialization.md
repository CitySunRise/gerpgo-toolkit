# Initialization

Start with local, non-secret inspection:

```shell
gerpgo-cli version
gerpgo-cli capabilities --format json
gerpgo-cli profile list --format json
```

If the selected profile does not exist, ask the user to run this in their own
terminal:

```shell
gerpgo-cli profile init prod
```

The interactive initializer stores App ID, App Key, Web username, and Web
password in macOS Keychain or Windows Credential Manager. It stores only
non-secret settings in the profile file. Do not request those values in chat
and do not turn on shell tracing while the user initializes a profile.

For a non-interactive machine where the user has already populated approved
environment variables:

```shell
gerpgo-cli profile init prod --from-env --enable-web
```

Do not print the environment variables. After initialization, verify locally:

```shell
gerpgo-cli profile status prod --format json
gerpgo-cli doctor --profile prod --read-only --format json
```

Only perform connectivity when the user authorizes a live authentication
request:

```shell
gerpgo-cli doctor --profile prod --connectivity --read-only --format json
```

The connectivity check obtains an OpenAPI token but does not query business
data. Web login is always a separate explicit command.
