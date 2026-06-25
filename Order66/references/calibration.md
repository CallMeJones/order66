# Calibration

One finding worked end-to-end, so you can calibrate **format, evidence standard, and
conditional severity**. This is a reference for *quality*, not a form to fill in — a real
review includes only the parts that carry weight (see the Output Shape menu). Do not
reproduce these headings mechanically.

The example below is illustrative (filenames are placeholders): a static-analysis security
gate — an AST/denylist `guard.py` that decides whether untrusted code may run in a host
process.

---

## What a strong P0 finding looks like

> **P0 — Static denylist is bypassable; "safe" code executes arbitrary commands.**
> *(Confirmed by execution.)*
> The guard keys off names, import modules, and a few reflection patterns
> ([guard.py:120-180](.)); it never touches the object graph. Both of these return
> `blocked=False, risk=low`:
> - `().__class__.__bases__[0].__subclasses__()` — reaches `os`/`subprocess` via the
>   type hierarchy; needs no builtins and no import statement, so name/import denylists
>   never see it.
> - `getattr(builtins, 'op'+'en')(...)` — the resolver only handles constant strings, so a
>   computed attribute name slips it.
>
> **Severity is conditional** on a fact I verified second: if the host auto-runs
> "approved" code without a human in the loop ([runner.py:88](.)), this guard is the
> *sole* barrier before `exec` ([:140](.)) — so it's **P0 in auto-run mode**, **P1** if
> every run still requires explicit approval. *Resolved by reading how the runner consumes
> the approved flag.*
>
> **Fix direction:** not "extend the denylist" (whack-a-mole). Enforcement-level —
> restricted subprocess / restricted builtins, or no auto-run of anything that can reach
> interpreter internals.

Why this is strong:
- **Reproduced, not theorized** — `blocked=False` came from running the payloads, so the
  confidence tag is *Confirmed*, not *Suspected*. (Operating Principle 10.)
- **Cited** — exact files/lines for both the gap and the execution chain.
- **Honest severity** — stated the conditional and the one check that decides it, then did
  the check and committed. No P0-for-drama; no burying it under hedging.
- **Right altitude of fix** — names the class of fix, resists the tempting wrong one.

## The same rigor, scaled down (a P3)

> **P3 — Size guard runs after the parser.** `parse(source)` executes before the
> `MAX_SIZE` check, so an oversized payload is fully parsed before rejection. Low impact.
> Cheap fix: length-check before parsing.

Note what's *absent*: no verification plan, no persona writeup, no severity essay. A P3
gets a sentence. Spending P0 effort on a P3 is its own kind of mistake — Operating
Principle 9.

## Calibration takeaways

- Confidence tag must match how you know it: ran it = Confirmed; pattern-matched =
  Suspected; didn't check = Assumption.
- A finding without a `file:line` and a concrete trigger is an opinion, not a finding.
- When severity depends on an unread fact, make the dependency explicit and resolve it if
  the check is cheap.
- Match output weight to severity. One clean line for a nit; the full chain for a P0.
