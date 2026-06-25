#!/usr/bin/env python3
"""Generate a compact start-of-session context pack."""

from __future__ import annotations

import argparse

from dev_session_common import (
    build_profile,
    classify_session_mode,
    current_issue_hint,
    evidence_contract,
    git_branch,
    git_dirty_summary,
    infer_lane,
    latest_file,
    profile_summary,
    require_existing_root,
    run_git,
)


def bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- (none)"


def command_summary(commands: dict) -> list[str]:
    lines = []
    for name in ["install", "dev", "test", "lint", "build", "smoke"]:
        values = commands.get(name, [])
        if values:
            lines.append(f"{name}: {', '.join(values)}")
    return lines


def mcp_summary(catalog: list[dict]) -> list[str]:
    lines = []
    for item in catalog:
        name = item.get("name", "(unnamed)")
        risk = item.get("risk_level", "unknown")
        mode = item.get("capabilities", "unspecified")
        owner = item.get("owner", "unowned")
        lines.append(f"{name}: {mode}; risk={risk}; owner={owner}")
    return lines


def suggest_ceremony(mode: str, changed_count: int) -> str:
    """Match ceremony to the work: light for small/low-risk changes, full otherwise."""
    if mode in {"plan", "release"} or changed_count > 3:
        return "full"
    return "light"


def onboarding_block(profile: dict) -> str:
    checks = [
        "Confirm repository commands from the profile run locally.",
        "Confirm required MCPs are installed and can complete their safe smoke tests.",
        "Read CLAUDE.md for project-specific working agreements.",
        "Run one harmless smoke command before making changes.",
        "Record missing access as setup gaps instead of blocking the whole session.",
    ]
    custom_smoke = profile.get("onboarding", {}).get("harmless_smoke", [])
    if custom_smoke:
        checks.append("Harmless smoke: " + ", ".join(custom_smoke))
    return "## Onboarding\n\n" + bullet(checks) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--prompt", default="", help="User prompt to classify for smart intake.")
    parser.add_argument("--session-mode", choices=["orient", "research", "plan", "build", "review", "docs", "release", "onboarding"], help="Override inferred session mode.")
    parser.add_argument("--lane", choices=["frontend", "backend", "mcp", "agentic", "iot", "ops-security", "docs-product"], help="Override inferred lane.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    profile = build_profile(root)
    changed_files = run_git(root, ["diff", "--name-only"], timeout=10).splitlines()
    mode = args.session_mode or classify_session_mode(args.prompt)
    lane = args.lane or infer_lane(args.prompt, changed_files)
    dev_dir = root / ".dev-session"
    latest_log = latest_file(dev_dir / "logs")
    latest_snapshot = latest_file(dev_dir / "snapshots")
    risks_path = dev_dir / "risks.md"
    risks = risks_path.read_text(encoding="utf-8", errors="replace").splitlines()[:20] if risks_path.exists() else []

    print("# Dev Session Context Pack")
    print()
    print("## Repo")
    print()
    print(profile_summary(profile))
    print(f"Branch: {git_branch(root) or '(unknown)'}")
    print(f"Dirty worktree: {git_dirty_summary(root)}")
    print(f"Session mode: {mode}")
    print(f"Lane: {lane}")
    issue = current_issue_hint(root)
    print(f"Current issue/PR/MR hint: {issue or '(not detected)'}")
    if suggest_ceremony(mode, len(changed_files)) == "light":
        print("Ceremony: light - quick change; skip logs/snapshots, make the change and run verify.py. Escalate to full if it grows multi-file or risky.")
    else:
        print("Ceremony: full - substantial or risky; keep a daily log, snapshot, and durable decisions.")
    print()
    print("## Commands")
    print()
    print(bullet(command_summary(profile.get("commands", {}))))
    print()
    print("## Services And CI")
    print()
    print(bullet([f"services: {', '.join(profile.get('services', [])) or '(none detected)'}", f"ci: {profile.get('ci', {}).get('provider', 'unknown')}"]))
    print(bullet(profile.get("ci", {}).get("files", [])))
    print()
    print("## MCP Readiness")
    print()
    print(bullet(mcp_summary(profile.get("mcp_trust_catalog", []))))
    print()
    print("## Evidence Contract")
    print()
    print(bullet(evidence_contract(profile, lane)))
    print()
    print("## Pointers")
    print()
    print(bullet([
        f"latest log: {latest_log.relative_to(root) if latest_log else '(none)'}",
        f"latest snapshot: {latest_snapshot.relative_to(root) if latest_snapshot else '(none)'}",
    ]))
    print()
    print("## Open Risks")
    print()
    print(bullet([line for line in risks if line.strip()][:8]))
    if mode == "onboarding":
        print()
        print(onboarding_block(profile), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
