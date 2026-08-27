# Security policy

This is a public repository. Do not include ERP credentials, OpenAPI keys,
cookies, session tokens, captured request headers, customer data, internal
hostnames, real shop or warehouse names, or production exports in issues,
commits, fixtures, screenshots, or release artifacts.

Report a vulnerability privately to the repository owner. Do not open a public
issue containing credentials or production data. Revoke any exposed secret
before starting code remediation.

Before every commit, run:

```shell
python scripts/privacy_check.py --all
pytest
```

The CI workflow also runs privacy and secret scanning. A passing scan reduces
risk but does not replace human review of the staged diff.
