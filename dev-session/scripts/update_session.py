#!/usr/bin/env python3
"""Update .dev-session/SESSION.md and state.json from current project state."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from dev_session_common import (
    ensure_core_files,
    git_branch,
    git_dirty_summary,
    latest_file,
    require_existing_root,
    write_json,
)


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- "


def numbered_lines(items: list[str]) -> str:
    if not items:
        return "1.\n2.\n3."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def relative_or_blank(path: Path | None, root: Path) -> str:
    return str(path.relative_to(root)) if path else ""


def build_session(root: Path, args: argparse.Namespace, latest_log: Path | None, latest_snapshot: Path | None) -> str:
    branch = git_branch(root) or "N/A (not a git repository)"
    dirty = git_dirty_summary(root)
    updated = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    last_change = args.last_change or relative_or_blank(latest_snapshot, root) or relative_or_blank(latest_log, root)

    return f"""# Dev Session

## Current State
- Branch: {branch}
- Goal: {args.goal or ""}
- Last meaningful change: {last_change}
- Dirty worktree: {dirty}
- Updated: {updated}

## Next Start
{numbered_lines(args.next)}

## Active Risks
{bullet_lines(args.risk)}

## Key Commands
{bullet_lines(args.command)}

## Pointers
- Latest log: {relative_or_blank(latest_log, root)}
- Latest snapshot: {relative_or_blank(latest_snapshot, root)}
- Important decisions: .dev-session/decisions.md
"""


def build_state(root: Path, args: argparse.Namespace, latest_log: Path | None, latest_snapshot: Path | None) -> dict:
    now = dt.datetime.now().astimezone().isoformat()
    return {
        "updated_at": now,
        "branch": git_branch(root) or "N/A (not a git repository)",
        "dirty_worktree": git_dirty_summary(root),
        "goal": args.goal or "",
        "next_actions": args.next,
        "active_risks": args.risk,
        "key_commands": args.command,
        "latest_log": relative_or_blank(latest_log, root),
        "latest_snapshot": relative_or_blank(latest_snapshot, root),
        "decisions": ".dev-session/decisions.md",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--goal", default="", help="Current project/session goal.")
    parser.add_argument("--next", action="append", default=[], help="Next-start action. May be repeated.")
    parser.add_argument("--risk", action="append", default=[], help="Active risk. May be repeated.")
    parser.add_argument("--command", action="append", default=[], help="Key command. May be repeated.")
    parser.add_argument("--last-change", default="", help="Short description of the last meaningful change.")
    parser.add_argument("--dry-run", action="store_true", help="Print output without writing files.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    base = root / ".dev-session"
    ensure_core_files(base)
    (base / "logs").mkdir(parents=True, exist_ok=True)
    (base / "snapshots").mkdir(parents=True, exist_ok=True)

    latest_log = latest_file(base / "logs")
    latest_snapshot = latest_file(base / "snapshots")
    session_text = build_session(root, args, latest_log, latest_snapshot)
    state = build_state(root, args, latest_log, latest_snapshot)

    if args.dry_run:
        print(session_text, end="")
        return 0

    (base / "SESSION.md").write_text(session_text, encoding="utf-8")
    write_json(base / "state.json", state)
    print(f"Updated {base / 'SESSION.md'}")
    print(f"Updated {base / 'state.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
