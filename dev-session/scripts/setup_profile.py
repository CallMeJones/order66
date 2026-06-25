#!/usr/bin/env python3
"""Inspect or write the dev-session paved-path profile for a repository."""

from __future__ import annotations

import argparse
import json
import shutil

from pathlib import Path

from dev_session_common import build_profile, ensure_core_files, profile_path, require_existing_root, save_profile, write_if_missing


CANONICAL_SKILL_DIR = Path(__file__).resolve().parents[1]

CLAUDE_SKILL_TEMPLATE = f"""\
---
name: dev-session
description: Run paved-path development sessions with smart intake, repo workflow profiles, curated MCP use, evidence contracts, PR/MR composition, onboarding, flow metrics, and durable handoffs.
---

# Dev Session

Use this repo-local dev-session implementation. Scripts live in `scripts/`; references live in `references/`.

Start substantial sessions with:

```bash
python .claude/skills/dev-session/scripts/setup_profile.py --root . --mode inspect
python .claude/skills/dev-session/scripts/context_pack.py --root . --prompt "<user request>"
```

Provider policy: read and prepare freely; do not post, assign, label, merge, deploy, or alter GitHub/GitLab settings without explicit user confirmation unless autonomous action is granted for the run.
"""


def copy_tree_missing(source: Path, target: Path) -> None:
    if source.resolve() == target.resolve():
        return
    target.mkdir(parents=True, exist_ok=True)
    for path in source.rglob("*"):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def scaffold_claude_project_skill(root: Path) -> None:
    target = root / ".claude" / "skills" / "dev-session"
    write_if_missing(target / "SKILL.md", CLAUDE_SKILL_TEMPLATE)
    for folder in ["scripts", "references", "assets"]:
        copy_tree_missing(CANONICAL_SKILL_DIR / folder, target / folder)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--mode", choices=["inspect", "write"], default="inspect", help="Inspect detected profile or write .dev-session/profile.json.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    profile = build_profile(root)

    if args.mode == "write":
        base = root / ".dev-session"
        ensure_core_files(base)
        (base / "logs").mkdir(parents=True, exist_ok=True)
        (base / "snapshots").mkdir(parents=True, exist_ok=True)
        save_profile(root, profile)
        claude_body = """# Claude Project Guidance

Use `.claude/skills/dev-session` for paved-path development sessions. Keep durable team workflow truth in `.dev-session/profile.json`; keep secrets and local preferences out of committed files.
"""
        write_if_missing(root / "CLAUDE.md", claude_body)
        scaffold_claude_project_skill(root)
        print(f"Wrote {profile_path(root)}")
    else:
        print(json.dumps(profile, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
