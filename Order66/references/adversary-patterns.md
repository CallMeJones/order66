# Adversary Patterns

High-yield classes the Adversary persona should actively try, not just look for. Each
entry is **pattern → why it bites → probe to confirm**. Per Operating Principle 10,
prefer the probe: a bypass you *run* is a finding; one you describe is a hypothesis.

This is a catalogue to draw from, not a checklist to complete. Use the entries whose
surface is actually present in the diff.

---

## Python execution boundaries (denylist / "safe eval" / plugin runners)

Denylisting names/imports via AST or regex is **not** a security boundary — CPython has
too many paths to the same capability. If a denylist is the only gate before `exec`,
`eval`, `compile`, or an untrusted `import`, treat it as bypassable until proven
otherwise, and say so.

- **Object-graph escape** — `().__class__.__bases__[0].__subclasses__()` walks from any
  object up to `object` and back down to dangerous classes (`subprocess.Popen`, file
  openers, importers). Reaches `os`/`subprocess` via `<cls>.__init__.__globals__` or a
  `BuiltinImporter`. Needs **no** builtins and **no** import statement, so name/import
  denylists never see it. Watch for `__class__`, `__bases__`, `__mro__`,
  `__subclasses__`, `__globals__`, `__builtins__`.
  - *Probe:* run the payload through the analyzer; if it returns "allowed/clean", the gate
    is bypassed. `exec("().__class__.__bases__[0].__subclasses__()", {})` enumerates the
    reachable classes.
- **Computed attribute names** — `getattr(__builtins__, 'ev'+'al')`,
  `getattr(m, ''.join([...]))`, `m.__dict__['op'+'en']`. Any analyzer that only resolves
  *constant* strings misses these. *Probe:* feed a concatenated/`join`ed name and check
  it isn't flagged.
- **Reflection wrappers around blocked ops** — `getattr(mod, 'dangerous_op')()` where the
  bare `mod.dangerous_op()` is blocked. If the block-list check matches the *unresolved*
  call name while only some checks resolve `getattr`, the wrapped form slips through.
  *Probe:* wrap each blocked call in `getattr` and re-run.
- **Deserialization as code-exec** — `pickle.loads`, `marshal.loads`,
  `yaml.load` (without `SafeLoader`), `jsonpickle`. These execute arbitrary objects.
- **Format/template injection** — `str.format` on attacker input reaches attributes
  (`"{0.__class__}".format(obj)`); f-string-like template engines (Jinja `{{ }}`) reach
  the same object graph (SSTI).

**Reporting note:** the right fix is almost never "add the pattern to the denylist"
(whack-a-mole, unwinnable). It's enforcement-level: restricted subprocess, restricted
`__builtins__`, or no auto-run of anything that can reach interpreter internals. Say that.

## Injection (any language)

- **Shell** — string-built commands, `shell=True`, `os.system`, backticks. *Probe:* an
  arg containing `; id` / `$(id)` / `| whoami`.
- **SQL** — string-concatenated queries instead of parameters. *Probe:* `' OR '1'='1`
  and a `;`-stacked statement against a test DB.
- **Path traversal** — user input joined into a path without containment. *Probe:*
  `../../etc/passwd` (or Windows `..\..\`); confirm the resolved path escapes the base.
- **SSRF** — server fetches a user-supplied URL. *Probe:* `http://169.254.169.254/`
  (cloud metadata), `http://localhost:<internal-port>`, and a redirect to those.
- **XXE / entity expansion** — XML parser with external entities or DTDs enabled.

## Trust boundaries & auth

- Identify every point where data crosses from less-trusted to more-trusted, and check
  it's validated *there*, not assumed upstream.
- **Failure-open** — does an exception, timeout, or missing token *allow* the action?
  Auth/guard code should fail closed. *Probe:* make the check throw and see what happens.
- **TOCTOU** — value checked, then re-read/re-fetched before use. The thing you validated
  isn't the thing you act on.
- **Confused deputy / SSRF-of-localhost** — a localhost service that trusts "local"
  callers can be driven by any local process or a CSRF/DNS-rebind from a web page.

## Secrets & data leakage

- Secrets in logs, error messages, crash reports, env dumps, command lines (`ps` shows
  args), config files, or transcripts. *Probe:* grep the diff for the secret's variable
  name flowing into a log/format/exception.
- Tokens that outlive their need (not cleared/rotated), or compared with `==` instead of
  a constant-time compare (timing oracle).

## Resource exhaustion / DoS

- Unbounded input processed before any size check (e.g. parsing a huge payload, then
  rejecting it). Order the cheap guard first.
- `while True` / unbounded recursion / regex catastrophic backtracking on user input.
