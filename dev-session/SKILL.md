---
name: dev-session
description: Claude-first paved-path development sessions with smart intake, repo workflow profiles, scale-aware ownership checks, curated MCP use, automated lane evidence, PR/MR composition, onboarding, flow-friction metrics, and durable handoffs. Use when starting, resuming, planning, researching, building, reviewing, documenting, onboarding, releasing, or handing off development work.
---

# Dev Session

Run a Claude-first development session as a disciplined Session Lead. Paved-path, not red tape: infer first, ask only high-impact questions, match ceremony to the work, prove with lane evidence, and leave a durable handoff.

Use Claude Code as the runtime. The skill lives at `.claude/skills/dev-session/SKILL.md` and drives the scripts and references in this directory.

## Fast Lane vs Full Session

Match ceremony to the work. Do not run the full ritual for a one-line fix.

- **Fast lane** (trivial, low-risk, single-file): make the change, prove it with `verify.py`, and stop. No logs, snapshots, or decisions needed.
- **Full session** (substantial, multi-file, risky, or spanning sessions): run the Start steps, keep a daily log and snapshot, and record durable decisions and risks.

`context_pack.py` prints a suggested ceremony level. When unsure, start light and escalate the moment the work grows multi-file or touches security/release.

## Start (full sessions)

```bash
python <skill>/scripts/setup_profile.py --root . --mode inspect
python <skill>/scripts/new_day_log.py --root .
python <skill>/scripts/session_snapshot.py --root . --out --update-session
python <skill>/scripts/context_pack.py --root . --prompt "<user request>"
```

If `.dev-session/profile.json` is missing or stale:

```bash
python <skill>/scripts/setup_profile.py --root . --mode write
python <skill>/scripts/workflow_doctor.py --root .
```

Read `.dev-session/SESSION.md`, today's log, decisions, risks, backlog, the latest snapshot, and the context pack before planning.

## Smart Intake

Infer the session mode first: `orient`, `research`, `plan`, `build`, `review`, `docs`, `release`, `onboarding`.

Ask at most 2-3 questions, only when a missing answer changes implementation, verification, risk, or ownership. If the prompt is clear, proceed. See `references/pipeline-playbook.md` and `references/feature-lanes.md`.

## Paved Path

1. Orient from repo, profile, provider state, MCP readiness, and durable logs.
2. Shape the work into a clear outcome and evidence contract.
3. Slice into a small, reviewable batch.
4. Build or research with the minimal useful agent set.
5. Prove with lane evidence — run `verify.py` to execute the real commands.
6. Review for correctness, security, maintainability, and release readiness.
7. Compose PR/MR or handoff.
8. Record only useful decisions, risks, and friction.

Use `references/provider-workflows.md` for GitHub/GitLab flow. Use `references/mcp-profiles.md` before relying on MCP tools.

## Scale (solo vs team)

`setup_profile.py` records `scale` in the profile. On a solo repo (one contributor, no CODEOWNERS), `workflow_doctor.py` skips team ownership and CODEOWNERS checks so they never become noise. Set `"scale": "team"` in the profile — or add CODEOWNERS / a second contributor — to enable workflow-owner, lane-owner, and CODEOWNERS-coverage enforcement.

Store non-secret workflow truth in `.dev-session/profile.json`: scale, ownership, provider/default branch, commands, services, CI, deploy hints, evidence contracts, decision thresholds, MCP trust catalog, onboarding checks, and flow-metric policy. Keep secrets, tokens, local paths, and personal preferences out of committed profile data; use `CLAUDE.local.md`, `.claude/settings.local.json`, local MCP config, or personal memory for private state.

## Provider Policy

Read and inspect GitHub/GitLab freely, and prepare comments, PR/MR bodies, and commands freely. Do not post, assign, label, merge, deploy, or alter provider settings without explicit user confirmation unless the user grants autonomous action for the run.

```bash
python <skill>/scripts/compose_pr.py --root . --provider github --dry-run
```

## Evidence And Decisions

Use the lane evidence contract from the profile (default lanes: `frontend`, `backend`, `mcp`, `agentic`, `iot`, `ops-security`, `docs-product`). Prove it by running the real commands rather than ticking a checklist:

```bash
python <skill>/scripts/verify.py --root . --lane backend --write-log
```

Write durable decisions only when architecture, workflow, a dependency, security/release posture, or a team convention changes. Put raw chronology and agent outcomes in the daily log, durable choices in `decisions.md`, unresolved risks in `risks.md`, and deferred work in `backlog.md`. See `references/log-format.md`.

## Agents

Keep the main session as Session Lead. Spawn subagents only when the user authorizes delegation and the task can run independently. Give each one a role, objective, owned scope, constraints, lane, session mode, evidence expectations, and provider mutation policy.

```bash
python <skill>/scripts/make_agent_prompt.py --role "QA/Test" --objective "..." --lane frontend --session-mode review
```

See `references/agent-roles.md`.

## Onboarding And Flow Metrics

For onboarding, verify local commands, MCP readiness, repo workflow, access gaps, and a harmless smoke path; treat missing access as a setup gap, not a stop. Record workflow friction (never developer scores) with:

```bash
python <skill>/scripts/record_flow_metric.py --root . --kind setup_gap --note "..."
```

## End (full sessions)

```bash
python <skill>/scripts/end_session.py --root .
python <skill>/scripts/update_session.py --root . --goal "..." --next "..."
```

Fill the handoff with what changed, why, evidence, decisions, risks, next action, and what to inspect first.

Maintenance: `self_test.py`, `doctor.py --root .`, `workflow_doctor.py --root .`.
