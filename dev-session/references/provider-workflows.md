# Provider Workflows

## GitHub

Use GitHub Flow by default: deployable default branch, short-lived branches, PR review, CI/status checks, merge, deploy when applicable.

Team truth enforcement:

- Prefer `.github/CODEOWNERS`.
- Cover `.dev-session/profile.json`, `.claude/skills/dev-session/`, `CLAUDE.md`, `.mcp.json`, and CODEOWNERS itself.
- Enable branch protection or rulesets that require Code Owner review on the default branch.

## GitLab

Use GitLab Flow when environments, release branches, or GitLab CI/MR workflows are present.

Team truth enforcement:

- Use `CODEOWNERS`, `docs/CODEOWNERS`, or `.gitlab/CODEOWNERS`.
- Cover `.dev-session/profile.json`, `.claude/skills/dev-session/`, `CLAUDE.md`, `.mcp.json`, and CODEOWNERS itself.
- Protect the default branch and enable Code Owner approvals.
- Use MR approval rules for expertise that does not map neatly to file paths.

## Common Policy

Read provider state freely. Prepare comments and PR/MR bodies freely. Do not post, assign, label, merge, deploy, or change provider settings without explicit user confirmation unless autonomous action is granted for the run.
