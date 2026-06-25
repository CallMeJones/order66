#!/usr/bin/env python3
"""Check paved-path profile, ownership, MCP trust, and workflow readiness."""

from __future__ import annotations

import argparse
import json

from dev_session_common import (
    LANE_NAMES,
    codeowners_covers,
    detect_scale,
    find_codeowners,
    load_profile,
    profile_path,
    require_existing_root,
)


EXPECTED_OWNER_PATHS = [
    ".dev-session/profile.json",
    ".claude/skills/dev-session/",
    "CLAUDE.md",
    ".mcp.json",
]


def check_profile(root) -> tuple[list[str], list[str], str]:
    errors: list[str] = []
    warnings: list[str] = []
    path = profile_path(root)
    if not path.exists():
        warnings.append("Missing .dev-session/profile.json. Run setup_profile.py --root . --mode write.")
    else:
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            errors.append(f"Malformed .dev-session/profile.json: {exc.msg} at line {exc.lineno}")
    profile = load_profile(root)
    scale = profile.get("scale") or detect_scale(root)

    if scale == "team":
        ownership = profile.get("ownership", {})
        if not ownership.get("workflow_owners"):
            warnings.append("No workflow owners are declared in profile ownership.workflow_owners.")
        lane_owners = ownership.get("lane_owners", {})
        for lane in sorted(LANE_NAMES):
            if not lane_owners.get(lane):
                warnings.append(f"No lane owner declared for {lane}.")

    if not profile.get("decision_thresholds"):
        errors.append("Profile decision_thresholds is empty.")

    for lane in sorted(LANE_NAMES):
        if not profile.get("evidence_contracts", {}).get(lane):
            errors.append(f"Missing evidence contract for {lane}.")

    catalog = profile.get("mcp_trust_catalog", [])
    for index, item in enumerate(catalog, start=1):
        for key in ["name", "capabilities", "safe_smoke_test", "owner", "risk_level"]:
            if not item.get(key):
                warnings.append(f"MCP trust catalog item {index} is missing {key}.")

    if scale == "team":
        provider = profile.get("provider", "unknown")
        codeowners = find_codeowners(root, provider)
        if codeowners is None:
            warnings.append("No CODEOWNERS file found for workflow ownership enforcement.")
        else:
            missing = codeowners_covers(root, codeowners, EXPECTED_OWNER_PATHS)
            for item in missing:
                warnings.append(f"CODEOWNERS does not appear to cover {item}.")
            warnings.append("Provider branch/MR protection was not verified. Confirm Code Owner approval is required on the default branch.")

    return errors, warnings, scale


def print_report(errors: list[str], warnings: list[str], scale: str) -> None:
    print("# Dev Session Workflow Doctor")
    print()
    print(f"Scale: {scale}" + ("" if scale == "team" else " (team ownership and CODEOWNERS checks skipped)"))
    print()
    if not errors and not warnings:
        print("OK: paved-path workflow checks passed.")
        return
    if errors:
        print("## Errors")
        for item in errors:
            print(f"- {item}")
        print()
    if warnings:
        print("## Warnings")
        for item in warnings:
            print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when warnings are found.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    errors, warnings, scale = check_profile(root)
    print_report(errors, warnings, scale)
    if errors:
        return 2
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
