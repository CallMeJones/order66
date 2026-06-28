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
trigger the skill, so it doubles as the "when to use me" contract. **Progressive
disclosure** is the key idea: `SKILL.md` stays a lean orchestrator, and heavy detail
lives in `references/` that the agent opens only when a given situation calls for it — so
the skill can be deep without bloating every invocation.

---

## Skills in this repo

| Skill | One-liner |
|-------|-----------|
| [**Order66**](#order66--multi-perspective-code-audit) | A multi-perspective code audit: review a change from several adversarial points of view to find issues a single read misses. |
| [**dev-session**](#dev-session) | Run a disciplined, Claude-first development session — intake, paved-path workflow, lane evidence, PR composition, and durable handoffs. |
| [**blender-production**](#blender-production) | Drive the Blender Agent Bridge MCP to build professional 3D/2D work — animation, modeling, simulation, rendering — via a helper-first, plan→preview→commit workflow. |

---

## Order66 — Multi-Perspective Code Audit

### What it is

A review *lens*, not a checklist. Its core premise is distrust: an agent's default
failure when reviewing code is **confirmation bias** — it reads the code, finds it
plausible, and stops. Order66 counteracts that by making the agent review the same change
from several incompatible viewpoints and **try to break its own conclusions before
stating them**.

It is a *quality + risk* tool, deliberately scoped — for changes with real behavior or
risk surface, not pure polish (formatting, renames, comments, routine dep bumps).

### Core features

- **A roster of reviewer personas**, each with one agenda and a *declared blind spot*, so
  together they cover categories a single perspective structurally can't see:
  - **5 core personas** — Adversary (abuse/security), Operator (failure/recovery),
    Maintainer (clarity/simplification), Integrator (does the workflow actually ship?),
    Machine (build/types/lint/test reality).
  - **5 conditional personas** — Concurrency & Time, Performance, Data-Lifecycle,
    Cross-Platform, Integration-Client — that fire **only** when their signal is present
    in the diff.
  - **The Skeptic** — a final pass that attacks the author's *and the reviewer's own*
    assumptions.
- **Two depths.** *Quick* (Adversary + Operator + Maintainer) for small/low-risk diffs;
  *Full* (all five core) for user-facing, packaged, or security-sensitive changes. It
  escalates Quick→Full automatically if a risk surfaces mid-review.
- **Confidence labels** on every finding — *Confirmed* (read/ran it), *Suspected*
  (pattern looks wrong), *Assumption* (relying on something unchecked).
- **Severity model** P0–P3, plus **conditional severity** ("P0 if X, P1 otherwise; here's
  the one check that decides").
- **Shipped / Scaffolded / Planned / Blocked** classification so "there's a button"
  isn't mistaken for "the workflow works."
- **Cross-pass reconciliation** — surfaces tensions between personas (e.g. Adversary wants
  more checks, Maintainer wants less code) instead of silently picking one.
- **On-demand reference libraries** — `references/adversary-patterns.md` (bypass/injection
  catalogues with a probe for each) and `references/calibration.md` (one finding worked
  end-to-end to calibrate format and severity).
- **Built-in anti-bloat guards** — it's a lens not a checklist, output is proportional, a
  clean review is a valid result, and it won't manufacture findings to look busy.

### How it works

1. **Pick a depth**, stated up front.
2. **Run each persona pass:** adopt the identity, ask that persona's questions against the
   actual code citing lines, apply disconfirmation, record findings with severity +
   confidence, and note the blind spot the next persona must cover.
3. **Disconfirm with a probe.** Where a cheap probe can settle a question — run the
   payload, grep the real definition, run the one test, print the actual value — it does
   that instead of arguing. *Observed evidence outranks a plausible argument.*
4. **Reconcile and report.** Lead with a one-line verdict (depth, severity counts,
   ship/don't-ship), then only the sections that carry weight, each finding with
   `file:line`, evidence, and a confidence label.

### What makes it powerful

- **The adversarial multi-perspective design is the whole point.** A real security bypass
  hides in code that reads as clean and well-tested — the Maintainer waves it through; the
  Adversary, *whose only job is to abuse it*, catches it. No single reviewer mindset finds
  everything, so the skill runs several on purpose.
- **Disconfirmation + probe-over-argue turns review from opinion into evidence.** "Looks
  fine" becomes "I built the input that should break it, ran it, and here's what
  happened." Findings come back reproduced, not theorized.
- **The honesty machinery prevents both ways an LLM reviewer fails.** Confidence labels +
  conditional severity stop *over*claiming (no P0-for-drama); the "call it straight"
  rule — be equally willing to clear a change or block it, never tune the verdict to what
  the author seems to want — stops *under*claiming and rubber-stamping.
- **Proportionality keeps it usable.** Because it refuses to generate its own red tape, you
  can reach for it on a 10-line diff and get a one-line verdict, or on a release branch and
  get a full audit — same skill, effort matched to the risk.

### Example triggers

- "Order66 quick on my staged diff" (pre-commit self-review)
- "Order66 on what the agent just wrote in `foo.py`" (vet AI-generated code)
- "Order66 full, focus the Adversary, on the new endpoint" (security boundary)
- "Order66 — is this feature shipped or scaffolded?" (Integrator lens)

---

## dev-session

### What it is

Runs a Claude-first development session as a disciplined "Session Lead": **paved-path, not
red tape.** It infers first, asks only high-impact questions, matches ceremony to the
work, proves results by running real commands ("lane evidence") rather than ticking a
checklist, and leaves a durable handoff for the next session.

### Core features

- **Smart intake** — infers the session *mode* first (`orient`, `research`, `plan`,
  `build`, `review`, `docs`, `release`, `onboarding`) and asks at most 2–3 questions, only
  when an answer would change implementation, verification, risk, or ownership.
- **Ceremony matching** — *fast lane* (trivial single-file: make the change, prove it,
  stop) vs *full session* (substantial/risky/multi-session: logs, snapshots, durable
  decisions). `context_pack.py` suggests the level; you start light and escalate.
- **Lane evidence contracts** — per-lane proof requirements (`frontend`, `backend`, `mcp`,
  `agentic`, `iot`, `ops-security`, `docs-product`), proven by **running the real
  lint/test/build/smoke commands** via `verify.py`, not by asserting "tests pass."
- **Profile-driven workflow truth** — `setup_profile.py` records non-secret facts (scale,
  ownership, provider/branch, commands, CI, lanes, MCP trust) in
  `.dev-session/profile.json` so behavior adapts per repo.
- **Scale awareness** — on a solo repo (one contributor, no CODEOWNERS),
  `workflow_doctor.py` skips team-ownership and CODEOWNERS checks so they never become
  noise; flip the profile to `team` to enable them.
- **Durable session memory** — `SESSION.md`, a daily log, `decisions.md`, `risks.md`, and
  `backlog.md`, with thresholds so only meaningful decisions/risks get recorded.
- **Provider safety** — reads/inspects GitHub/GitLab and prepares PR/MR bodies and
  commands freely, but never posts, merges, deploys, or changes settings without explicit
  confirmation.
- **Secret hygiene** — `doctor.py` scans `.dev-session` content for leaked secrets/tokens
  before they're committed.
- **Agent orchestration** — `make_agent_prompt.py` mints scoped subagent prompts (role,
  objective, owned scope, lane, evidence expectations) when delegation is authorized.

### How it works

The paved-path lifecycle: **orient** (read context pack, profile, session files, git +
provider state, MCP readiness) → **shape** (mode, lane, outcome, evidence contract) →
**slice** (small enough to review and roll back) → **build/research** (minimal useful
tool + agent set) → **prove** (run `verify.py` for the lane's real commands) → **review**
(correctness, security, maintainability, release readiness) → **ship/hand off** (compose
PR/MR or handoff) → **learn** (record only durable decisions, risks, friction). The
`scripts/` are the executable steps; `references/` document the playbooks; `assets/` hold
templates.

### What makes it powerful

- **Lane evidence is the anti-hand-waving core.** Work isn't "done" because the agent says
  so — it's done when the lane's real commands ran and produced evidence. `verify.py`
  executes them; the contract names what proof each kind of change requires (a migration
  proves data-shape safety; an MCP change proves the client can load the tool).
- **Ceremony and scale matching keep it from becoming process for its own sake.** A
  one-line fix gets the fast lane; a solo repo never gets nagged about CODEOWNERS. The
  rigor scales up only when the work's risk does.
- **Durable handoffs make multi-session work resumable.** The next session (or the next
  agent) starts from `SESSION.md` + logs + decisions instead of re-deriving context — and
  only genuinely durable choices are recorded, so the trail stays signal-dense.

### Requirements

Python 3.x on `PATH` (the scripts are plain Python, no third-party deps). Written for the
Claude Code runtime, but the scripts run anywhere Python does.

---

## blender-production

### What it is

A paved-path workflow for driving the **Blender Agent Bridge** MCP server (`blender`) to
produce professional 3D and 2D work — animation, modeling, simulation, and rendering. The
skill's value is *discipline*: the same tool surface can be poked at randomly or driven
through a reliable loop, and this skill encodes the reliable loop so every Blender session
follows it instead of improvising.

### Core features

- **The non-negotiable loop** — `blender_bridge_status` → `plan_advanced_scene_workflow` /
  `plan_animation_workflow` (plan *before* mutating) → inspect → build with catalog helpers
  (`search_blender_tools` → `get_blender_tool_schema` → `invoke_blender_tool`) → review with
  `capture_animation_playblast` → `commit_preview` → `save_blend_file` → `start_render_job`.
- **Helper-first, scripting last.** `draft_script` is reserved for genuine helper gaps; the
  static denylist before `exec()` is treated as bypassable and restricted, so scripting is the
  last resort, never the default.
- **Safety rails** — user-confirmed paths for new-project/open/save-as, checkpoint-before-
  destructive, one-transaction preview/commit discipline, and recover-don't-thrash handling of
  bridge timeouts and long-running bakes/renders.
- **Verified gotchas baked in** — the camera-view playblast trap, default-Cube cleanup,
  Blender 5.1 slotted-action (channelbag) API change, Mantaflow gas-bake OOM, and
  `draft_script` trust limits — so the agent avoids the failures the hard way once.
- **Domain recipes** (`references/recipes.md`) — ordered helper sequences with sensible defaults
  for full professional animation, procedural 3D objects, simulation, and rendering.

### How it works

`SKILL.md` is the lean orchestrator (the loop + hard rules + gotchas); `references/recipes.md`
holds the per-domain sequences, opened only when a given task calls for them. The skill assumes
the `blender` MCP server is connected and its localhost bridge is running.

### Requirements

The `blender` MCP server (Blender Agent Bridge add-on) installed in Blender with the bridge
started. No scripts or Python deps of its own — it is pure prose that drives MCP tools.

### Example triggers

- "Make a storyboard animatic with panels, cutout layers, and a camera dolly"
- "Build a procedural 3D object and give me a turntable render"
- "Set up a smoke sim and bake it"
- "Render this scene to a 1080p MP4"

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
cp -r blender-production ~/.claude/skills/

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
├── dev-session/
│   ├── SKILL.md
│   ├── references/*.md
│   ├── scripts/*.py
│   └── assets/*.md
└── blender-production/
    ├── SKILL.md
    └── references/recipes.md
```
