# Contributing

Keep the OpenAPI and Web authentication layers separate. Never add silent
fallbacks or an arbitrary URL request command. New ERP enums, methods, paths,
required fields, and rate limits need a link to current official documentation
and a contract test.

Use synthetic values in tests and documentation. Review staged file names,
diffs, generated artifacts, and privacy scan output before committing. Do not
push a commit that contains credentials or production identifiers, even if a
secret scanner does not recognize them.
