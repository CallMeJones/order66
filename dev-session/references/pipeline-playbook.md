# Paved-Path Pipeline

Use this as the high-level operating model for dev sessions.

## Lifecycle

1. Orient: read context pack, profile, session files, git/provider state, and MCP readiness.
2. Shape: identify mode, lane, outcome, constraints, and evidence contract.
3. Slice: keep work small enough for review and rollback.
4. Build or research: use the minimal useful tool and agent set.
5. Prove: collect lane evidence before calling work complete. Run `verify.py` to execute the profile's real lint/test/build/smoke commands instead of ticking a manual checklist.
6. Review: check correctness, security, maintainability, and release readiness.
7. Ship or hand off: compose PR/MR or session handoff.
8. Learn: record durable decisions, risks, and workflow friction only.

## Ceremony

Match ceremony to the work, not the calendar.

- Fast lane: trivial, low-risk, single-file changes get the change plus `verify.py`. No logs, snapshots, or decisions.
- Full session: substantial, multi-file, risky, or multi-session work gets the Start steps, a daily log, a snapshot, and durable decisions/risks.

`context_pack.py` prints a suggested ceremony level. Start light and escalate the moment the work grows multi-file or touches security or release.

## Smart Intake

Infer mode before asking. Ask only when an answer changes implementation, verification, risk, or ownership.

- Orient: ask what to resume only when context cannot identify it.
- Research: ask what decision the research must inform.
- Plan: ask for success criteria and fixed constraints.
- Build: ask for lane and done evidence only if unclear.
- Review: ask scope and review lens if unclear.
- Docs: ask audience and source-of-truth status.
- Release: ask environment and rollback/monitoring evidence.
- Onboarding: ask target role and whether setup should be read-only or corrective.

## Decision Thresholds

Record a decision only when architecture, workflow, dependency, security/release posture, or team convention changes.
