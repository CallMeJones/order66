# Conditional Personas (load when the signal is present)

`SKILL.md` lists each conditional persona's name and trigger signal inline. This file holds
the full Catches list and the shipping/classification rules — open it when a matching signal
appears in the diff. The Cross-Platform "toolchain blocked, not passed" rule and the
Integration-Client shipping contract are load-bearing calibrations, not catalogue padding.

- **The Concurrency & Time reviewer** — *signal:* threads, async/await, locks, shared
  mutable state, timers, timestamps, timezones, ordering assumptions. Catches races,
  deadlocks, blocking-in-async, stale state, off-by-one-clock, ordering bugs.
- **The Performance Engineer** — *signal:* loops over collections, DB queries, network
  in a loop, large inputs, hot paths. Catches N+1 queries, missing indexes, unbounded
  result sets, accidental quadratic behavior, needless allocation; checks pathological
  inputs, not just typical ones.
- **The Data-Lifecycle reviewer** — *signal:* migrations, deletes/cascades, foreign
  keys, background jobs writing shared rows. Catches orphan rows, cascade gaps, races
  between jobs, irreversible migrations without backout.
- **The Cross-Platform reviewer** — *signal:* paths, shell commands, URL openers,
  autostart, hidden-file/permission semantics, executable names. Catches hard-coded
  separators/paths, host-specific tools that vanish after a clean install, dev-server
  or source-checkout / dependency-folder dependencies (e.g. `node_modules`, `.venv`,
  vendored libs) in packaged apps. Do at least one native check on the current OS; if a
  cross-target check fails before project code compiles (missing compiler/SDK/linker),
  call it "toolchain blocked," not "passed."
- **The Integration-Client reviewer** — *signal:* MCP servers, plugins, external API
  clients, importers. (Distinct from the Integrator: the Integrator asks whether the
  *user's workflow* ships; Integration-Client asks whether the *consuming client* can
  mechanically load and call the thing.) Don't stop at "config has an entry" or "endpoint
  responds": verify
  the consuming client can list/load it and complete one safe read-only call. If the
  client blocks on approval/trust, classify config/load as shipped and the tool-call
  approval path as manual smoke until an interactive run proves it. For importers,
  separate generic file ingestion from schema-aware extraction — a file-extension importer
  is not a domain-specific importer (for the records the product actually claims to ingest)
  until fixture tests prove it extracts those records; require at least one dry-run fixture
  and one idempotent non-dry-run smoke before "shipped."
