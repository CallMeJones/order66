#!/usr/bin/env python3
"""Initialize .dev-session files and today's daily log."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from dev_session_common import (
    DAILY_LOG_FALLBACK,
    SESSION_FALLBACK,
    ensure_core_files,
    git_branch,
    load_asset,
    parse_date,
    render_template,
    require_existing_root,
    write_if_missing,
)


def append_resume_note(path: Path, time_text: str) -> bool:
    if not path.exists():
        return False

    note = f"- {time_text} - Session resumed."
    text = path.read_text(encoding="utf-8")
    if note in text:
        return False

    marker = "## Work Log\n"
    if marker in text:
        section_start = text.find(marker) + len(marker)
        next_heading = text.find("\n## ", section_start)
        insert_at = len(text) if next_heading == -1 else next_heading
        text = text[:insert_at].rstrip() + "\n" + note + "\n" + text[insert_at:]
    else:
        text = text.rstrip() + f"\n\n## Work Log\n{note}\n"
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--no-resume-note", action="store_true", help="Do not append a resume note when today's log already exists.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)

    try:
        today = parse_date(args.date)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    now = dt.datetime.now().strftime("%H:%M")
    branch = git_branch(root)

    base = root / ".dev-session"
    logs = base / "logs"
    snapshots = base / "snapshots"
    logs.mkdir(parents=True, exist_ok=True)
    snapshots.mkdir(parents=True, exist_ok=True)

    created = []
    session_template = load_asset("session-template.md", SESSION_FALLBACK)
    daily_template = load_asset("daily-log-template.md", DAILY_LOG_FALLBACK)
    files = {
        base / "SESSION.md": session_template,
        logs / f"{today}.md": render_template(
            daily_template,
            {"date": today, "time": now, "branch": branch},
        ),
    }

    created.extend(ensure_core_files(base))

    for path, content in files.items():
        if write_if_missing(path, content):
            created.append(path)

    log_path = logs / f"{today}.md"
    resumed = False
    if not args.no_resume_note and log_path not in created:
        resumed = append_resume_note(log_path, now)

    if created:
        print("Created:")
        for path in created:
            print(f"- {path}")
        if resumed:
            print(f"Updated resume note in {log_path}")
    elif resumed:
        print(f"Updated resume note in {log_path}")
    else:
        print("Dev session files already exist for today.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
