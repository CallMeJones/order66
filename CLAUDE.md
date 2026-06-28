# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is a **repository of Claude Code agent skills**, not an application. Each top-level
skill directory is a self-contained unit of agent instructions that a skill-aware runtime
(Claude Code, Codex) loads on demand. There is no product to run, no service to deploy.

When asked "what does X do?", explain the skill's intent and structure — do not describe a
user-facing app feature. Do not add unrelated runtime code at the repo root; extend the
existing skill directories.

Three skills live here:
- **`Order66/`** — a multi-perspective code-audit *lens* (pure prose, no scripts). Makes
  the agent review a diff from several adversarial reviewer personas and disprove its own
  conclusions before reporting.
- **`dev-session/`** — a disciplined development-session orchestrator (prose + Python
  helper scripts). Runs "paved-path" sessions: intake, lane-evidence proof, PR composition,
  durable handoffs.
- **`blender-production/`** — a paved-path workflow for the `blender` MCP server (Blender
  Agent Bridge); pure prose, no scripts. Drives 3D/2D animation, modeling, simulation, and
  rendering through a plan→inspect→helper→preview→commit→save→render loop, with verified
  gotchas and per-domain recipes in `references/`.

`README.md` is the human-facing overview/install guide; `AGENTS.md` is the cross-runtime
agent guide. Both overlap heavily with this file — keep the three consistent when editing.

## Skill anatomy (the load-bearing convention)

Every skill follows the same layout, and the split is intentional — **progressive
disclosure**:

```
<skill>/
├── SKILL.md      # lean orchestrator the agent reads first; YAML frontmatter
├── references/   # deep material opened only when a situation calls for it
├── scripts/      # optional executable helpers the skill invokes
└── assets/       # optional templates the skill fills in
```

- The frontmatter `description:` is the **trigger contract** — the runtime matches against
  it to decide when to fire the skill. Editing it changes when the skill activates.
- Keep `SKILL.md` concise; push depth into `references/` so the main pass stays cheap. When
  adding detail, prefer a new/edited `references/*.md` over growing `SKILL.md`.
- Skill `name:` values are conventionally lowercase-kebab; `Order66` is the exception (its
  folder and `name:` are capitalized). Some runtimes are strict about casing for `/`
  invocation.

## dev-session script architecture

All scripts are **plain Python 3, no third-party dependencies** (the `.venv/` at the root
holds only pip and is incidental — scripts run with bare `python3`). Every script:

- shares helpers from [dev-session/scripts/dev_session_common.py](dev-session/scripts/dev_session_common.py)
  — profile load/merge/detect, git helpers, session-mode/lane inference, CODEOWNERS
  matching, decision-threshold logic. **Change shared behavior here, not in each script.**
- takes `--root .` and operates on a generated `.dev-session/` runtime directory.

`.dev-session/` is **generated per-repo runtime state and is `.gitignore`d** — it is not
part of the skill. It holds `profile.json` (the workflow-truth config that drives behavior),
`SESSION.md`, daily logs, `decisions.md`, `risks.md`, `backlog.md`, and snapshots. This repo
itself has no `.dev-session/`; it is created on first run in a target repo.

Behavior is **profile- and scale-driven**: `setup_profile.py` auto-detects provider,
default branch, commands, CI, services, and scale (`solo` vs `team`). On a solo repo
(one author, no CODEOWNERS) the ownership/CODEOWNERS checks are skipped so they aren't
noise. The default profile shape lives in `DEFAULT_PROFILE` in `dev_session_common.py`.

Lane evidence is the anti-hand-waving core: `verify.py` runs the profile's *real*
lint/test/build/smoke commands rather than asserting "tests pass." Default lanes:
`frontend`, `backend`, `mcp`, `agentic`, `iot`, `ops-security`, `docs-product`.

## Commands

```bash
# Run the dev-session script test suite (the only test entry point in this repo).
# Spins up temp git repos, exercises every script end-to-end, prints PASS/FAIL per test.
python3 dev-session/scripts/self_test.py
python3 dev-session/scripts/self_test.py --keep   # keep temp roots for debugging on failure

# Maintenance / health checks (run against a target repo via --root):
python3 dev-session/scripts/doctor.py --root .          # scan .dev-session for leaked secrets
python3 dev-session/scripts/workflow_doctor.py --root . # workflow/ownership sanity checks
```

There is **no build, lint, or package step** — the skills are Markdown + standalone Python.
After editing any `dev-session/scripts/*.py`, run `self_test.py`; it is the regression gate
and adding a new script means adding a test to its `tests` list.

## When editing skills

- Adding a new skill: replicate the four-folder pattern, write a tight `description:`, and
  keep `SKILL.md` lean with depth in `references/`.
- Order66 is a *lens, not a checklist* — it deliberately scales effort to risk and treats a
  clean review as a valid result. Preserve that proportionality if you edit it.
- Keep secrets, tokens, and personal paths out of anything committed (including profile
  data and `.dev-session/` content); `doctor.py` exists to catch leaks before commit.
