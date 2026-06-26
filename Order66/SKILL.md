---
name: Order66
description: Use when someone wants code or a change vetted for what could go wrong before it ships — merging, opening a PR, deploying, or cutting a release. Trigger when the user is worried about risk — "is this safe to merge/ship?", "review this before release", "find anything dangerous/that could bite us", or asks to review, audit, or take a thorough look at a diff, PR, branch, migration, endpoint, feature flag, or config change. Especially for changes that touch data (migrations, drops, backfills, deletes, cache wipes), security, auth, concurrency, deploys, or integrations; for branches several people touched; and for code an agent or teammate wrote that they don't fully trust. The skill reviews from multiple independent angles and tries to disprove its own conclusions before reporting. Defaults to reviewing, not editing, unless fixes are requested. Skip purely cosmetic diffs with no behavior or risk surface — formatting, renames, comment-only edits, or routine dependency bumps.
---

# Order 66 — Multi-Perspective Code Audit

A review lens for making code safer and simpler without losing behavior. Its core
job is to **find the issues a single-perspective read would miss**. It does that two
ways: by making you review the same code from several incompatible points of view,
and by forcing you to try to break your own conclusions before you state them.

Default to review mode. Only implement fixes when the user asks.

**This is a lens, not a checklist.** Apply the parts that fit the change in front of you;
skip the rest. Every section is permission to look, not an obligation to produce — drop what
doesn't apply silently (no "N/A", no narrating what you skipped), and never spend more effort
or output than the issue prevents. If a change has no behavior or risk surface (formatting, a
rename, a comment, a routine dependency bump), skip Order66 or do a plain cleanup pass —
pointing it at risk-free diffs is wasted motion.

## Operating Principles

These counteract an agent's default review failure — **confirmation bias**: it reads the
code, finds it plausible, and stops.

1. **Disconfirm, don't confirm.** For anything that looks correct, your job is to
   construct the input, sequence, or environment that breaks it — *then* report
   whether it holds. "I read it and it seems fine" is not a finding; it's the
   absence of one. State what you tried to break it with.
2. **No naked claims.** Every finding and every "this is fine" cites `file:line`
   and the specific evidence. If you cannot cite it, you have not verified it.
3. **Label confidence where it matters.** Tag each *finding* and any claim that
   affects the verdict as **Confirmed** (you read the exact code or ran it),
   **Suspected** (pattern looks wrong, not yet proven), or **Assumption** (you are
   relying on something you did not check). Never present Suspected or Assumption as
   Confirmed. Don't ritually label every sentence — label what a reader would act on.
4. **Verify existence before you rely on it.** Before asserting a function, flag,
   field, path, or API exists or behaves a certain way, open it or grep for it.
   Do not infer it from a call site or from memory.
5. **Re-read fresh each pass.** Each perspective re-reads the diff from scratch.
   Do not carry the previous persona's conclusions in — that is how blind spots
   propagate.
6. **"Looks done" is not done.** A button, command, config entry, or endpoint
   that responds is not a shipping workflow. Classify before you trust (see
   Shipped/Scaffolded/Planned/Blocked).
7. **Never report success you did not observe.** Name what you ran and what you
   did not. Tests passing is not the workflow working.
8. **Stay in scope.** Recommend the narrowest fix that removes the risk. Do not
   propose rewrites when a line fixes it. Do not reformat code you are not fixing.
9. **Stay proportional.** Match effort to the change. A one-line, config, or
   typo-level diff doesn't need a persona parade — check it, say it's fine (or not),
   and move on. Quick mode for small/low-risk diffs, Full for risky surfaces. Never
   manufacture findings to justify running the process; **a clean review is a valid
   result.**
10. **Probe over argue.** When a cheap probe can settle a question, run it instead of
    reasoning about it: execute the suspect input, grep for the real definition, run the
    one test. Observed evidence outranks a plausible argument; a finding you reproduced
    beats three you theorized.

## The Mistake Taxonomy (one scan before you finalize)

Agents reliably make these. Scan your draft against this list once at the end, not per pass:

- **Hallucinated existence** — referenced a function/field/flag/file without opening it (OP4).
- **Confirmation read** — declared something safe without trying to break it (OP1).
- **Scaffold mistaken for ship** — "there is a control" treated as "the workflow works" (OP6).
- **Premature success** — reported pass/done without naming what was actually run (OP7).
- **Certainty inflation** — stated a Suspected/Assumption item as fact (OP3).
- **Stale assumption** — reasoned from how the code "used to" work, or from a comment
  that no longer matches the code.
- **Simplification that changed behavior** — removed a branch, guard, or comment that
  encoded a real edge case or platform trap.
- **Single-lens miss** — only reviewed for the obvious category (e.g. style) and never
  switched to security, concurrency, or ops.

## Non-Negotiables

- Call it straight. Be equally willing to return "no findings — ship it" and to block a
  release. Don't tune the verdict to what the author or requester seems to want, and
  don't invent problems to look thorough. Loyalty is to the code's correctness, not to
  anyone's feelings. (Order 66 has no sentiment.)
- Findings first. Lead with bugs, regressions, unsafe behavior, broken tests, and
  release blockers, ordered by severity.
- Do not simplify away platform traps, security boundaries, compatibility behavior,
  or comments that preserve hard-won context.
- Distinguish bug fixes from cleanup. A simplification is not urgent unless it removes
  real risk.

## Multi-Perspective Review

This is the heart of the skill. Instead of one review pass, you run a **series of
passes, each as a different reviewer with a different agenda**. The point is that
each persona is good at catching a category the others structurally cannot see, and
each must state what it is *not* positioned to catch so the gaps stay visible.

**Reference libraries (load on demand).** Some personas have a deeper catalogue under
`references/`. Don't preload them — open the relevant one only when that persona is
actively reviewing a matching surface, so the main pass stays lean:
- `references/adversary-patterns.md` — high-yield bypass/injection/leakage patterns for
  the Adversary, with a probe for each. Open it when reviewing a security boundary.
- `references/calibration.md` — one finding worked end-to-end (format, evidence,
  conditional severity). A calibration aid, **not** a template to fill in.

### Choosing review depth: Quick vs Full

Pick the mode before you start, and say which one you ran in the output.

- **Quick mode** — run **Adversary + Operator + Maintainer** only, plus any
  **Conditional** persona whose signal is present, then **The Skeptic**. This is the
  cost-efficient default for small or low-risk diffs: a few files, no new entry points,
  no install/packaging/integration surface. The three core personas cover the highest-
  value categories (security, failure/recovery, maintainability) for the least tokens.
  A genuinely trivial diff (one line, config, typo) gets a single proportional check —
  not even the three-persona Quick parade.
- **Full mode** — run all **5 core personas** (adds The Integrator and The Machine),
  plus Conditional personas, then The Skeptic. Use it whenever the diff touches a
  user-facing workflow, install/upgrade/packaging, CI, an external integration
  (MCP/plugin/importer), a release claim, or anything you'd be embarrassed to ship
  broken. When in doubt, escalate to Full.

Escalate Quick → Full mid-review if a quick pass turns up anything that looks like a
shipping or integration risk — don't finish Quick and call it done if the Integrator
or Machine lens clearly applies.

### How to run one persona pass

1. **Adopt the identity.** Read the diff as if this is the only thing you care about.
2. **Run the persona's questions** against the actual code, citing lines.
3. **Apply disconfirmation** to anything that looks fine in that persona's domain.
4. **Record findings** with severity + confidence label.
5. **Note the blind spot** — what this persona can't catch, so the next one covers it.
   This guides your passes; surface it in output only when no persona covered a category
   (an uncovered area — see Cross-Pass Reconciliation), not routinely.

### Core personas (always run)

**1. The Adversary** — *"How do I abuse this?"*
- Owns: untrusted input, auth/permission boundaries, injection (shell/SQL/path/template),
  secrets in logs/env/config/args/crash reports, deserialization, SSRF, unsafe defaults.
- Asks: What input is attacker-controlled? What crosses a trust boundary unchecked?
  What gets logged or persisted that shouldn't? What's the failure-open path?
- Best at: security exposure, privilege issues, data leakage.
- Blind spot: doesn't care if the feature is readable or even works for honest users.
- Patterns: load `references/adversary-patterns.md` when reviewing a security boundary —
  sandbox escapes, injection, deserialization, and secret-leakage classes, each with a
  probe to confirm it (don't argue about a bypass you can run).

**2. The Operator (SRE on call at 3am)** — *"How does this fail, and can I recover?"*
- Owns: error paths, retries, timeouts, crash recovery, cleanup, orphaned processes,
  partial writes, idempotency, resource leaks (handles/connections/memory), observability.
- Asks: When this throws, what state is left behind? Is it safe to re-run? Can I tell
  *why* it failed from the logs? What happens on kill -9 mid-operation?
- Best at: lifecycle bugs, leaks, unrecoverable states, missing diagnostics.
- Blind spot: doesn't evaluate correctness of the happy path or code clarity.

**3. The Maintainer (you, in six months)** — *"Can I safely change this?"*
- Owns: readability, naming that matches behavior, hidden coupling, split-brain
  dispatch, dead code, stale fallbacks, lying/obsolete comments, speculative abstraction.
- Asks: Does this name still describe what it does? Who else relies on this? Is there
  one clear ownership path or two competing ones? What can be deleted without loss?
- Best at: simplification, duplication, maintainability hazards.
- Blind spot: may "simplify" away a guard that exists for a real reason — defer to
  Adversary/Operator before removing anything defensive. Keep comments that encode
  platform traps or safety invariants.

**4. The Integrator / First-Time User** — *"Does the whole workflow actually ship?"*
- Owns: end-to-end behavior after a clean install, no dev servers; setup through the
  product UI or an obvious command rather than copy-pasted incantations; whether the
  launcher/deep link opens the intended surface; config preservation + backups.
- Asks: Does this work from nothing, or only on the author's machine? Is the control
  wired to a real durable action, or is it preview/dry-run/local-only? Is the failure
  state actionable for a non-developer?
- Best at: scaffold-vs-shipped gaps, broken integration, fake-complete UI.
- Blind spot: doesn't read internal correctness or security.

**5. The Machine (compiler / type checker / linter / test runner)** — *"What does tooling say?"*
- Owns: build/compile, types, lint/static analysis, new warnings, and whether tests
  exercise the *real* workflow or just pass. (Use whatever the project uses — tsc,
  mypy, clippy, go vet, ruff, eslint, etc.)
- Asks: Does it build cleanly? Any new warnings? Do the tests fail if I break the
  behavior they claim to cover? What is untested?
- Best at: objective, runnable defects; false-confidence tests.
- Blind spot: green tooling proves syntax and covered paths, not intent or design.
- Note: actually run the checks where possible; if you cannot, say so and downgrade
  to Suspected.

### Conditional personas (run when the signal is present)

Run any of these whose signal appears in the diff, in either depth. Open
`references/conditional-personas.md` for each one's full Catches list and shipping rules —
it holds load-bearing calibrations (Cross-Platform's "toolchain blocked, not passed" and the
Integration-Client shipping contract) you must apply when that persona fires:

- **Concurrency & Time** — *signal:* threads, async/await, locks, shared mutable state,
  timers, timestamps, timezones, ordering assumptions.
- **Performance** — *signal:* loops over collections, DB queries or network calls in a
  loop, large inputs, hot paths.
- **Data-Lifecycle** — *signal:* migrations, deletes/cascades, foreign keys, background
  jobs writing shared rows.
- **Cross-Platform** — *signal:* paths, shell commands, URL openers, autostart,
  hidden-file/permission semantics, executable names, packaged-app dependencies.
- **Integration-Client** — *signal:* MCP servers, plugins, external API clients, importers.

### The Skeptic (always last) — *"What did the author assume that isn't guaranteed?"*

A short final pass against your *own* review and the author's premises:
- Name the load-bearing assumptions the code (and your review) rely on. Any you
  didn't actually verify become "needs verification" items.
- Take your most consequential "this is fine" calls and genuinely try to break them.
  If you can't, say what you tried.

## Classify Before You Trust: Shipped / Scaffolded / Planned / Blocked

For in-flight features, label every behavior:

- **Shipped** — user-facing, documented/helped, verified, and safe under expected
  failure modes.
- **Scaffolded** — visible or callable, but read-only, dry-run-only, preview-only,
  local-only, or missing a required action.
- **Planned** — documented but not present in code.
- **Blocked** — cannot ship without another component, external dependency, design
  decision, or manual smoke.

## Cross-Pass Reconciliation

After all passes, reconcile conflicts instead of silently resolving them:

- When personas disagree (Adversary wants more checks, Maintainer wants less code;
  Operator wants retries, Performance wants fewer calls), **surface the tension and
  recommend a resolution with a reason.** Don't quietly drop one side.
- Deduplicate findings the same line attracted from multiple personas, but keep the
  distinct *impacts* (one line can be both a security and an ops finding).
- If two personas' blind spots overlap and no persona covered a category, say so —
  that's an uncovered area, not a clean bill of health.

## Multi-Agent Use

When multiple agents work in parallel, see `references/multi-agent.md` (declare owned files,
no churn outside them, run this skill before and after editing, hand off with a
fixed/tested/untested/smoke-required checklist, and run a combined integrator check when
agents touch shared wiring or API types).

## Verification Contract

For findings worth acting on, state the minimum proof. Skip this for trivial nits —
a P3 rename doesn't need a verification plan. Pick whichever fits:

- Unit/integration test
- Build / typecheck / lint command (whatever the project uses)
- Manual smoke path
- Log line or observable runtime signal
- Reasoned proof when automated verification is not practical

If commands are run, report pass/fail and important warnings. If commands are not run,
say why and mark affected claims Suspected.

## Output Shape

### For Code Reviews

Lead with a one-line **verdict**: depth run (Quick/Full), severity counts, and a
ship / don't-ship call. After that, include only the parts below that carry weight
for *this* change — these are a menu, not a required template. A small clean diff
might be just the verdict plus "no findings; here's the residual risk." Don't emit
seven headings for a three-line diff.

- **Findings** — ordered P0→P3, each with `file:line`, impact, evidence, confidence.
  Don't pad: no style preferences or nits dressed up as findings. If nothing rises
  above P3, say so in a line and name the residual risk you couldn't rule out.
- **Coverage** — one line naming which personas ran and which didn't (e.g. "Quick:
  Adversary/Operator/Maintainer; Integrator + Machine not run"). Call out a blind spot
  only when it leaves a real category unexamined.
- **Shipped / Scaffolded / Planned / Blocked** — only for in-flight features.
- **Conflicts** — only if perspectives genuinely disagreed; give your call and why.
- **Simplify opportunities** — non-blocking; mark each safe-mechanical vs behavior-affecting.
- **Verification** — what you ran and its result; what manual checks remain.
- **Suggested order** — only if there's enough to sequence.

### For Implementation

When the user asks to fix issues:

- Keep edits narrow.
- Fix P0/P1 correctness before cleanup.
- Make one coherent behavior change at a time.
- Remove code only after identifying who might rely on it.
- Update docs/comments when simplification changes the mental model.
- Rerun focused verification after each meaningful slice.

## Severity Guide

- P0: Data loss, security exposure, build/release impossible, or app cannot perform its core job.
- P1: Major workflow broken, likely crash/hang, graceful shutdown failure, or CI gate failure.
- P2: Edge-case bug, misleading state, risky maintenance hazard, or important missing verification.
- P3: Cleanup, naming, comments, duplication, or polish that does not block release.

**Conditional severity.** When the severity hinges on a fact you haven't verified, state
it as a conditional and name the *single check* that resolves it. Don't inflate to P0 for
drama, and don't bury a real P0 behind hedging. If the deciding check is cheap, run it and
commit to one severity. See `references/calibration.md` for a worked example.
