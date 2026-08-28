# Web authentication boundary

V0.2 supports only:

```shell
gerpgo-cli web auth login --format json
gerpgo-cli web auth status --format json
gerpgo-cli web auth logout --format json
```

These commands select `prod` when neither `--profile` nor `GERPGO_PROFILE` is
set. Do not ask the user to confirm `prod` each time. An explicit
`--profile NAME` overrides the environment and default. A missing selected
profile is an error; never create one or fall back to OpenAPI, another profile,
or another authentication path.

`login` is an explicit network action. It retrieves the Gerpgo public key,
encrypts the locally stored password, authenticates, and stores the resulting
session token in the operating-system credential store. Its output contains
status only, never identity or token data.

`status` checks only local session state. `logout` removes the local cached
token; it does not claim to revoke a server session.

If the user asks for Web reports, catalog, shipment, purchasing, export, raw
request, or another Web business endpoint, state that the installed version
does not implement it. Do not use browser network calls, a generic HTTP tool,
or OpenAPI as a silent substitute.
