# MCP Profiles

Use curated MCP profiles. Do not connect random tools just because they exist.

## Trust Catalog Fields

Each `mcp_trust_catalog` entry should include:

- `name`
- `capabilities`: read-only, read-write, browser, provider, observability, design, database, local-device, or custom
- `required_env_vars`
- `safe_smoke_test`
- `owner`
- `risk_level`: low, medium, or high

## Defaults

- Provider MCP: GitHub or GitLab for issues, PRs/MRs, and CI/provider state.
- Docs MCP: current framework, SDK, or platform documentation.
- UI MCP: browser, Playwright, or Chrome tools for visual proof.
- Observability MCP: Sentry/log/cloud only when approved by profile.
- Design MCP: Figma only when the task needs design context.
- MCP/agentic tools: use only after schema and one safe tool call are verified.
- IoT/hardware tools: use simulator or read-only status before mutating devices.

Provider mutations require explicit user confirmation unless the user grants autonomous action for the run.
