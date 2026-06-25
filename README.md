# Agent Skills

A small collection of **agent skills** for Claude Code (and other skill-aware runtimes
such as Codex). A skill is a folder of Markdown instructions an AI coding agent loads on
demand to take on a specialized job — here, auditing code and running disciplined dev
sessions.

Each skill is self-contained in its own folder and follows the standard layout:

```
<skill>/
├── SKILL.md          # the instructions the agent reads (with YAML frontmatter)
├── references/       # deep material loaded only when relevant (progressive disclosure)
├── scripts/          # optional executable helpers the skill calls
└── assets/           # optional templates the skill fills in
```

The frontmatter `description:` is what the runtime matches against to decide when to
trigger the skill, so it doubles as the "when to use me" contract.

---

## Skills in this repo

| Skill | One-liner |
|-------|-----------|
| [**Order66**](#order66--multi-perspective-code-audit) | A multi-perspective code audit: review a change from several adversarial points of view to find issues a single read misses. |
| [**dev-session**](#dev-session) | Run a disciplined, Claude-first development session — intake, paved-path workflow, lane evidence, PR composition, and durable handoffs. |

---

## Order66 — Multi-Perspective Code Audit

### What it is

A review *lens*, not a checklist. Its core premise is distrust: an agent's default
failure when reviewing code is **confirmation bias** — it reads the code, finds it
plausible, and stops. Order66 counteracts that by making the agent review the same change
from several incompatible viewpoints and **try to break its own conclusions before
stating them**.

It is a *quality + risk* tool, deliberately scoped:

- **Use it for** changes with real behavior or risk surface — logic, security boundaries,
  concurrency, lifecycle, integrations, releases.
- **Don't use it for** pure polish (formatting, renames, comments, routine dep bumps).

### How it works

1. **Pick a depth.** *Quick* (Adversary + Operator + Maintainer) for small/low-risk
   diffs; *Full* (adds Integrator + Machine) for anything user-facing, packaged, or
   security-sensitive.
2. **Run persona passes.** Each persona is a reviewer with one agenda and a declared
   blind spot, so they cover categories the others structurally can't see:
   - **The Adversary** — "How do I abuse this?" (injection, auth, secrets, sandbox escapes)
   - **The Operator** — "How does this fail, and can I recover?" (lifecycle, leaks, recovery)
   - **The Maintainer** — "Can I safely change this?" (clarity, coupling, simplification)
   - **The Integrator** — "Does the whole workflow actually ship?" (scaffold vs shipped)
   - **The Machine** — "What does tooling say?" (build, types, lint, false-confidence tests)
   - plus conditional personas (Concurrency, Performance, Data-Lifecycle, Cross-Platform,
     Integration-Client) that fire only when their signal is present in the diff.
3. **Disconfirm with a probe.** Where a cheap probe can settle a question — run the
   payload, grep the definition, run the one test — it does that instead of arguing.
   Observed evidence outranks a plausible argument.
4. **Report proportionally.** Lead with a one-line verdict (depth, severity counts,
   ship/don't-ship), then only the sections that carry weight. Findings are P0–P3 with
   `file:line`, evidence, and a confidence label (Confirmed / Suspected / Assumption).

It is built to avoid generating its own red tape: a clean review is a valid result, and a
three-line diff never produces a seven-section report.

### Reference libraries (loaded on demand)

- `references/adversary-patterns.md` — high-yield bypass/injection/leakage classes, each
  with a probe to confirm it. Opened when reviewing a security boundary.
- `references/calibration.md` — one finding worked end-to-end, to calibrate format,
  evidence standard, and conditional severity. A teaching aid, not a template.

### Example triggers

- "Order66 quick on my staged diff" (pre-commit self-review)
- "Order66 on what the agent just wrote in `foo.py`" (vet AI-generated code)
- "Order66 full, focus the Adversary, on the new endpoint" (security boundary)
- "Order66 — is this feature shipped or scaffolded?" (Integrator lens)

---

## dev-session

### What it is

Runs a Claude-first development session as a disciplined "Session Lead": paved-path, not
red tape. It infers first, asks only high-impact questions, matches ceremony to the work,
proves results with real commands ("lane evidence") rather than checklist ticks, and
leaves a durable handoff for the next session.

### How it works

- **Fast lane vs full session.** Trivial single-file fixes get the fast lane (make the
  change, prove it with `verify.py`, stop). Substantial/multi-file/risky work gets the
  full session with logs, snapshots, and recorded decisions.
- **Profile-driven.** `scripts/setup_profile.py` records non-secret workflow truth
  (scale, ownership, provider/branch, commands, CI, lanes, MCP trust) in
  `.dev-session/profile.json` so the workflow adapts to solo vs team repos.
- **Paved path.** Orient → shape outcome + evidence contract → slice → build → prove with
  lane evidence → review → compose PR/handoff → record only useful decisions/risks.
- **Helpers.** `scripts/` holds the executable steps (`new_day_log.py`,
  `session_snapshot.py`, `context_pack.py`, `verify.py`, `compose_pr.py`,
  `make_agent_prompt.py`, `end_session.py`, `workflow_doctor.py`, …);
  `references/` documents the playbooks (pipeline, feature lanes, provider workflows, MCP
  profiles, agent roles, log format, secret patterns); `assets/` holds templates.

### Provider safety

Reads/inspects GitHub/GitLab and prepares PR bodies and commands freely, but never posts,
merges, deploys, or changes settings without explicit confirmation (unless the run grants
autonomous action).

### Requirements

Python 3.x on `PATH` (the scripts are plain Python, no third-party deps). The skill is
written for the Claude Code runtime but the scripts run anywhere Python does.

---

## Installation

A skill becomes active by living in a directory your runtime scans. Install = copy (or
symlink) the skill folder into that directory.

### Claude Code

- **Personal (all projects):** `~/.claude/skills/<skill>/SKILL.md`
- **Project-scoped:** `<repo>/.claude/skills/<skill>/SKILL.md`

```bash
# Copy
cp -r Order66 ~/.claude/skills/
cp -r dev-session ~/.claude/skills/

# …or symlink so edits here stay live (recommended while iterating)
ln -s "$(pwd)/Order66" ~/.claude/skills/Order66
```

On Windows (PowerShell), to symlink:

```powershell
New-Item -ItemType SymbolicLink -Path "$HOME\.claude\skills\Order66" -Target "$PWD\Order66"
```

### Codex

Install into the Codex skills directory (mirrors the same layout):

```bash
cp -r Order66 ~/.codex/skills/
```

> Note: skill `name:` values are conventionally lowercase-kebab. If your runtime is strict
> about casing for invocation, rename `Order66` → `order66` in both the folder name and
> the `name:` frontmatter field.

## Usage

Once installed, the runtime triggers a skill automatically when your request matches its
`description`, or you can invoke it by name (e.g. `/order66`, `/dev-session`) if your
runtime supports slash invocation. Order66 needs no setup. dev-session bootstraps its
per-repo state on first run via `setup_profile.py`.

## Repo layout

```
.
├── README.md
├── Order66/
│   ├── SKILL.md
│   └── references/{adversary-patterns,calibration}.md
└── dev-session/
    ├── SKILL.md
    ├── references/*.md
    ├── scripts/*.py
    └── assets/*.md
```
