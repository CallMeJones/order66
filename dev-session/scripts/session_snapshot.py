#!/usr/bin/env python3
"""Create a git-aware markdown snapshot for a development session."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

from dev_session_common import is_git_repo


def run(root: Path, args: list[str], timeout: int) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError:
        return "Command not available."
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s."
    text = result.stdout.strip()
    return text if text else "(no output)"


def has_commits(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=root,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def fenced(title: str, body: str) -> str:
    return f"## {title}\n\n```text\n{body}\n```\n"


def stash_stats(root: Path, timeout: int) -> str:
    stashes = run(root, ["git", "stash", "list", "--max-count=5"], timeout)
    if stashes == "(no output)":
        return "(no output)"
    blocks = []
    for line in stashes.splitlines():
        name = line.split(":", 1)[0]
        stat = run(root, ["git", "stash", "show", "--stat", name], timeout)
        blocks.append(f"{line}\n{stat}")
    return "\n\n".join(blocks) if blocks else "(no output)"


def dev_session_files(
    root: Path,
    planned_snapshot: str | None = None,
    max_snapshots: int = 8,
    max_logs: int = 14,
) -> str:
    dev_dir = root / ".dev-session"
    if not dev_dir.exists():
        return "(none)"

    core_files = []
    log_files = []
    snapshot_files = []
    for path in dev_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = str(path.relative_to(root))
        if path.parent == dev_dir / "snapshots":
            snapshot_files.append(relative)
        elif path.parent == dev_dir / "logs":
            log_files.append(relative)
        else:
            core_files.append(relative)

    if planned_snapshot and planned_snapshot not in snapshot_files:
        snapshot_files.append(planned_snapshot)

    core_files.sort()
    log_files.sort()
    snapshot_files.sort()
    omitted_logs = max(0, len(log_files) - max_logs)
    omitted = max(0, len(snapshot_files) - max_snapshots)
    if max_logs == 0:
        visible_logs = []
    else:
        visible_logs = log_files[-max_logs:]
    if max_snapshots == 0:
        visible_snapshots = []
    else:
        visible_snapshots = snapshot_files[-max_snapshots:]

    known = core_files + visible_logs + visible_snapshots
    if omitted_logs:
        known.append(f"... {omitted_logs} older log file(s) omitted")
    if omitted:
        known.append(f"... {omitted} older snapshot file(s) omitted")
    return "\n".join(known) if known else "(none)"


def next_snapshot_path(root: Path) -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    relative = Path(".dev-session") / "snapshots" / f"{stamp}.md"
    if not (root / relative).exists():
        return str(relative)

    for index in range(2, 1000):
        relative = Path(".dev-session") / "snapshots" / f"{stamp}-{index}.md"
        if not (root / relative).exists():
            return str(relative)

    raise RuntimeError("could not find an available snapshot filename")


def build_snapshot(
    root: Path,
    log_count: int,
    planned_snapshot: str | None = None,
    max_snapshots: int = 8,
    max_logs: int = 14,
    command_timeout: int = 30,
) -> str:
    now = dt.datetime.now().astimezone()
    lines = [
        f"# Dev Session Snapshot - {now:%Y-%m-%d %H:%M:%S %Z}",
        "",
        f"Root: `{root}`",
        "",
    ]

    if not is_git_repo(root):
        lines.append("Not a git repository. Capture project context from files and user prompt.")
        lines.append("")
        lines.append(fenced("Dev Session Files", dev_session_files(root, planned_snapshot, max_snapshots, max_logs)))
        return "\n".join(lines) + "\n"

    leading_commands = [
        ("Branch", ["git", "branch", "--show-current"]),
        ("Status", ["git", "status", "--short", "--branch"]),
    ]
    trailing_commands = [
        ("Diff Stat", ["git", "diff", "--stat"]),
        ("Staged Diff Stat", ["git", "diff", "--cached", "--stat"]),
        ("Changed Files", ["git", "diff", "--name-only"]),
        ("Staged Files", ["git", "diff", "--cached", "--name-only"]),
        ("Untracked Files", ["git", "ls-files", "--others", "--exclude-standard"]),
        ("Stashes", ["git", "stash", "list", "--max-count=5"]),
        ("Stash Stats", None),
    ]

    for title, command in leading_commands:
        lines.append(fenced(title, run(root, command, command_timeout)))

    lines.append(
        fenced(
            "Recent Commits",
            run(root, ["git", "log", f"--max-count={log_count}", "--oneline", "--decorate"], command_timeout)
            if has_commits(root)
            else "(no commits)",
        )
    )

    for title, command in trailing_commands:
        body = stash_stats(root, command_timeout) if command is None else run(root, command, command_timeout)
        lines.append(fenced(title, body))

    lines.append(fenced("Dev Session Files", dev_session_files(root, planned_snapshot, max_snapshots, max_logs)))

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--out", action="store_true", help="Write to .dev-session/snapshots as well as stdout.")
    parser.add_argument("--log-count", type=int, default=12, help="Number of recent commits to include.")
    parser.add_argument("--max-snapshots", type=int, default=8, help="Number of snapshot files to list.")
    parser.add_argument("--max-logs", type=int, default=14, help="Number of daily log files to list.")
    parser.add_argument("--command-timeout", type=int, default=30, help="Per-git-command timeout in seconds.")
    parser.add_argument("--update-session", action="store_true", help="Refresh SESSION.md and state.json after writing a snapshot.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"--root must be an existing directory: {root}")
    if args.log_count < 0:
        parser.error("--log-count must be zero or greater")
    if args.max_snapshots < 0:
        parser.error("--max-snapshots must be zero or greater")
    if args.max_logs < 0:
        parser.error("--max-logs must be zero or greater")
    if args.command_timeout <= 0:
        parser.error("--command-timeout must be greater than zero")

    planned_snapshot = None
    if args.out:
        planned_snapshot = next_snapshot_path(root)

    snapshot = build_snapshot(
        root,
        args.log_count,
        planned_snapshot,
        args.max_snapshots,
        args.max_logs,
        args.command_timeout,
    )
    print(snapshot, end="")

    if args.out:
        out_dir = root / ".dev-session" / "snapshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = root / planned_snapshot
        out_path.write_text(snapshot, encoding="utf-8")
        print(f"\nWrote {out_path}")
        if args.update_session:
            update_script = Path(__file__).resolve().parent / "update_session.py"
            subprocess.run(
                [sys.executable, str(update_script), "--root", str(root), "--last-change", str(planned_snapshot)],
                cwd=root,
                check=False,
                timeout=30,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
