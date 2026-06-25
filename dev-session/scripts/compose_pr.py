#!/usr/bin/env python3
"""Compose a GitHub PR or GitLab MR body from dev-session state."""

from __future__ import annotations

import argparse

from dev_session_common import build_profile, detect_default_branch, evidence_contract, git_branch, infer_lane, latest_file, require_existing_root, run_git


def read_recent(path, max_lines: int = 80) -> list[str]:
    if not path or not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]


def owners_for_lane(profile: dict, lane: str) -> list[str]:
    ownership = profile.get("ownership", {})
    lane_owners = ownership.get("lane_owners", {}).get(lane, [])
    return lane_owners or ownership.get("workflow_owners", [])


def branch_diff_range(root, base: str) -> str | None:
    """Range describing this branch's committed changes vs its base, when meaningful."""
    if not base:
        return None
    current = git_branch(root)
    if not current or current == base or current.startswith("detached"):
        return None
    if not run_git(root, ["rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"], timeout=10):
        return None
    return f"{base}...HEAD"


def collect_changes(root, base: str) -> tuple[list[str], str]:
    """Files and a diff stat for the PR: committed changes vs base plus any uncommitted work."""
    diff_range = branch_diff_range(root, base)
    committed: list[str] = []
    stats: list[str] = []
    if diff_range:
        committed = run_git(root, ["diff", "--name-only", diff_range], timeout=10).splitlines()
        committed_stat = run_git(root, ["diff", "--stat", diff_range], timeout=10)
        if committed_stat:
            stats.append(committed_stat)
    worktree = run_git(root, ["diff", "--name-only", "HEAD"], timeout=10).splitlines()
    worktree_stat = run_git(root, ["diff", "--stat", "HEAD"], timeout=10) or run_git(root, ["diff", "--stat"], timeout=10)
    if worktree_stat:
        stats.append(worktree_stat)
    merged: list[str] = []
    seen: set[str] = set()
    for item in [*committed, *worktree]:
        if item and item not in seen:
            seen.add(item)
            merged.append(item)
    return merged, "\n\n".join(stats)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--provider", choices=["github", "gitlab"], help="Provider label. Defaults to profile provider when known.")
    parser.add_argument("--lane", choices=["frontend", "backend", "mcp", "agentic", "iot", "ops-security", "docs-product"], help="Work lane.")
    parser.add_argument("--base", default="", help="Base branch to diff against. Defaults to the detected default branch.")
    parser.add_argument("--title", default="", help="Override generated title.")
    parser.add_argument("--summary", default="", help="Short summary to include.")
    parser.add_argument("--dry-run", action="store_true", help="Print only; never mutate provider state.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    profile = build_profile(root)
    provider = args.provider or profile.get("provider", "github")
    if provider not in {"github", "gitlab"}:
        provider = "github"
    base = args.base or detect_default_branch(root)
    changed, stat = collect_changes(root, base)
    lane = args.lane or infer_lane(args.summary, changed)
    dev_dir = root / ".dev-session"
    latest_log = latest_file(dev_dir / "logs")
    latest_snapshot = latest_file(dev_dir / "snapshots")
    risks_path = dev_dir / "risks.md"
    risks = read_recent(risks_path, 40)
    title = args.title or f"{lane}: {git_branch(root) or 'update'}"
    owner_suggestions = owners_for_lane(profile, lane)

    label = "Pull Request" if provider == "github" else "Merge Request"
    print(f"# {label}: {title}")
    print()
    print("## Summary")
    print(args.summary or "- Describe the user-facing or operational change.")
    print()
    print("## Changes")
    if changed:
        for item in changed:
            print(f"- {item}")
    else:
        print("- No changes detected against the base branch or working tree.")
    if stat:
        print()
        print("```text")
        print(stat)
        print("```")
    print()
    print("## Evidence")
    for item in evidence_contract(profile, lane):
        print(f"- [ ] {item}")
    print()
    print("## Risks")
    useful_risks = [line for line in risks if line.strip() and not line.startswith("#")][:8]
    if useful_risks:
        for line in useful_risks:
            print(f"- {line.lstrip('- ').strip()}")
    else:
        print("- No active risk recorded; add residual risk or say none.")
    print()
    print("## Screenshots / Logs")
    print(f"- Latest log: {latest_log.relative_to(root) if latest_log else '(none)'}")
    print(f"- Latest snapshot: {latest_snapshot.relative_to(root) if latest_snapshot else '(none)'}")
    print()
    print("## Reviewers")
    if owner_suggestions:
        for owner in owner_suggestions:
            print(f"- {owner}")
    else:
        print("- No lane/workflow owner declared.")
    print()
    print("## Rollout / Rollback")
    rollback = profile.get("deploy", {}).get("rollback", "")
    print(f"- Rollout: standard {provider} review and CI path.")
    print(f"- Rollback: {rollback or 'Use the project rollback path if deployment is needed; otherwise revert the PR/MR.'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
