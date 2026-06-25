#!/usr/bin/env python3
"""Ensure today's log has one end-of-session handoff skeleton."""

from __future__ import annotations

import argparse
import datetime as dt

from dev_session_common import (
    DAILY_LOG_FALLBACK,
    SESSION_FALLBACK,
    ensure_core_files,
    git_branch,
    load_asset,
    parse_date,
    render_template,
    require_existing_root,
)

HANDOFF = """\

## Handoff Update - {time}

- Changed:
- Why:
- Tests/checks:
- Decisions:
- Risks:
- Next action:
- Inspect first next session:
"""

BASE_HANDOFF = """\

## Handoff
- Changed:
- Why:
- Tests/checks:
- Decisions:
- Risks:
- Next action:
- Inspect first next session:
"""


def find_last_handoff(text: str) -> int:
    handoff_index = text.rfind("\n## Handoff")
    if handoff_index == -1 and text.startswith("## Handoff"):
        handoff_index = 0
    return handoff_index


def section_end(text: str, start: int) -> int:
    next_heading = text.find("\n## ", start + 1)
    return len(text) if next_heading == -1 else next_heading


def ensure_inspect_line(text: str) -> tuple[str, bool]:
    handoff_index = find_last_handoff(text)
    if handoff_index == -1:
        return text, False
    end = section_end(text, handoff_index)
    if "Inspect first next session:" in text[handoff_index:end]:
        return text, False
    marker = "- Next action:\n"
    marker_index = text.find(marker, handoff_index, end)
    if marker_index == -1:
        return text, False
    insert_at = marker_index + len(marker)
    return text[:insert_at] + "- Inspect first next session:\n" + text[insert_at:], True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format. Defaults to today.")
    parser.add_argument("--force", action="store_true", help="Append a new handoff update even if one already exists.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)

    try:
        today = parse_date(args.date)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    now = dt.datetime.now().strftime("%H:%M")

    base = root / ".dev-session"
    ensure_core_files(base)
    (base / "snapshots").mkdir(parents=True, exist_ok=True)

    log_path = base / "logs" / f"{today}.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    created_log = False
    if not log_path.exists():
        template = load_asset("daily-log-template.md", DAILY_LOG_FALLBACK)
        log_path.write_text(
            render_template(template, {"date": today, "time": now, "branch": git_branch(root)}),
            encoding="utf-8",
        )
        created_log = True

    current = log_path.read_text(encoding="utf-8")
    has_handoff = find_last_handoff(current) != -1

    if args.force:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(render_template(HANDOFF, {"time": now}))
        action = "Appended forced handoff update"
    elif created_log:
        action = "Created daily log with handoff section"
    elif has_handoff:
        upgraded, changed = ensure_inspect_line(current)
        if changed:
            log_path.write_text(upgraded, encoding="utf-8")
            action = "Updated existing handoff section"
        else:
            action = "Handoff section already exists"
    else:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(BASE_HANDOFF)
        action = "Added handoff section"

    session_path = base / "SESSION.md"
    if not session_path.exists():
        session_path.parent.mkdir(parents=True, exist_ok=True)
        session_path.write_text(load_asset("session-template.md", SESSION_FALLBACK), encoding="utf-8")

    print(f"{action} in {log_path}")
    print(f"Review and update {session_path} with the concise next-session state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
