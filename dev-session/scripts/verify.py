#!/usr/bin/env python3
"""Run a lane's real verification commands and capture pass/fail as evidence.

This turns the lane evidence contract from a manual checklist into automation: it runs
the profile's configured lint/test/build/smoke commands, records the result, and can
append it to today's daily log under a Verification section.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess

from dev_session_common import (
    LANE_NAMES,
    evidence_contract,
    infer_lane,
    load_profile,
    parse_date,
    require_existing_root,
    run_git,
)


DEFAULT_KINDS = ["lint", "test", "build", "smoke"]


def collect_commands(profile: dict, kinds: list[str], extra: list[str]) -> list[tuple[str, str]]:
    """Return (kind, command) pairs to run, in a stable, predictable order."""
    commands: list[tuple[str, str]] = []
    configured = profile.get("commands", {})
    for kind in kinds:
        for command in configured.get(kind, []):
            commands.append((kind, command))
    for command in extra:
        commands.append(("custom", command))
    return commands


def run_command(command: str, root, timeout: int) -> tuple[int, str]:
    try:
        result = subprocess.run(
            command,
            cwd=root,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, f"Command timed out after {timeout}s."
    return result.returncode, (result.stdout or "").strip()


def tail(text: str, lines: int = 15) -> str:
    rows = text.splitlines()
    return "\n".join(rows[-lines:]) if rows else "(no output)"


def build_report(profile: dict, lane: str, results: list[tuple[str, str, int, str]]) -> tuple[str, bool]:
    now = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    lines = [f"## Verification - {lane} - {now}", ""]
    passed = 0
    for kind, command, code, output in results:
        status = "PASS" if code == 0 else "FAIL"
        if code == 0:
            passed += 1
        lines.append(f"- `{command}` ({kind}): {status} (exit {code})")
        if code != 0:
            lines.append("")
            lines.append("  ```text")
            lines.extend(f"  {row}" for row in tail(output).splitlines())
            lines.append("  ```")
    all_passed = passed == len(results)
    lines.append("")
    lines.append(f"Result: {'PASS' if all_passed else 'FAIL'} ({passed}/{len(results)} passed)")
    lines.append("")
    lines.append(f"Lane evidence contract ({lane}):")
    for item in evidence_contract(profile, lane):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n", all_passed


def append_to_log(root, date: str, report: str) -> str | None:
    log_path = root / ".dev-session" / "logs" / f"{date}.md"
    if not log_path.exists():
        return None
    existing = log_path.read_text(encoding="utf-8")
    log_path.write_text(existing.rstrip() + "\n\n" + report, encoding="utf-8")
    return str(log_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--lane", choices=sorted(LANE_NAMES), help="Lane whose evidence contract this proves. Inferred when omitted.")
    parser.add_argument("--prompt", default="", help="Prompt text used to infer the lane when --lane is omitted.")
    parser.add_argument("--kind", action="append", choices=DEFAULT_KINDS, help="Command kinds to run. Defaults to lint, test, build, smoke. May be repeated.")
    parser.add_argument("--command", action="append", default=[], help="Extra raw command to run. May be repeated.")
    parser.add_argument("--timeout", type=int, default=600, help="Per-command timeout in seconds.")
    parser.add_argument("--write-log", action="store_true", help="Append the report to today's daily log.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD for the daily log. Defaults to today.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    try:
        date = parse_date(args.date)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    profile = load_profile(root)
    changed = run_git(root, ["diff", "--name-only"], timeout=10).splitlines()
    lane = args.lane or infer_lane(args.prompt, changed)
    kinds = args.kind or DEFAULT_KINDS

    commands = collect_commands(profile, kinds, args.command)
    print("# Dev Session Verify")
    print()
    print(f"Lane: {lane}")
    print()
    if not commands:
        print(f"No verification commands configured for kinds {', '.join(kinds)}.")
        print("Add commands to .dev-session/profile.json (commands.test, commands.lint, ...) or pass --command.")
        return 0

    results: list[tuple[str, str, int, str]] = []
    for kind, command in commands:
        code, output = run_command(command, root, args.timeout)
        results.append((kind, command, code, output))

    report, all_passed = build_report(profile, lane, results)
    print(report, end="")

    if args.write_log:
        written = append_to_log(root, date, report)
        if written:
            print(f"\nAppended verification to {written}")
        else:
            print(f"\nNo daily log at .dev-session/logs/{date}.md; run new_day_log.py first to record evidence.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
