# Secret Patterns

`doctor.py` uses lightweight pattern matching to catch likely secrets in `.dev-session/` text files.

Allow a false positive on the same line with:

```text
dev-session-secret-allow
```

Current checks:

- Private key blocks
- GitHub tokens beginning with `ghp_`, `gho_`, `ghu_`, `ghs_`, or `ghr_`
- OpenAI-style tokens beginning with `sk-`
- Slack tokens beginning with `xox...`
- Assignments containing names such as `api_key`, `secret`, `token`, or `password`

These checks are intentionally conservative and do not replace a dedicated repository secret scanner.
