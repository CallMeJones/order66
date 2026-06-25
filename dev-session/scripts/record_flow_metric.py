#!/usr/bin/env python3
"""Record lightweight workflow friction metrics without developer scoring."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re

from dev_session_common import load_profile, require_existing_root


IDENTIFIER_PATTERN = re.compile(
    r"(@[A-Za-z0-9_.-]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\b(developer|dev|user|owner|assignee)\s*[:=])",
    re.IGNORECASE,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--kind", required=True, help="Metric kind such as review_age, blocked_reason, flaky_check, setup_gap, or handoff_gap.")
    parser.add_argument("--note", default="", help="Short non-personal note.")
    parser.add_argument("--value", default="", help="Optional value such as hours or check name.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    profile = load_profile(root)
    flow = profile.get("flow_metrics", {})
    allowed = set(flow.get("allowed_kinds", []))
    if allowed and args.kind not in allowed:
        parser.error(f"--kind must be one of: {', '.join(sorted(allowed))}")
    if not flow.get("enabled", True):
        print("Flow metrics are disabled in profile.")
        return 0
    if IDENTIFIER_PATTERN.search(args.note) or IDENTIFIER_PATTERN.search(args.value):
        parser.error("Flow metrics must describe system friction, not developer identifiers. Remove names, handles, emails, or assignee fields.")

    path = root / ".dev-session" / "flow-metrics.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "recorded_at": dt.datetime.now().astimezone().isoformat(),
        "kind": args.kind,
        "note": args.note,
        "value": args.value,
        "privacy": "No developer names or performance scores.",
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    print(f"Recorded {args.kind} in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
