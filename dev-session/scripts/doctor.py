#!/usr/bin/env python3
"""Check .dev-session health for a project."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from dev_session_common import CORE_FILE_DEFAULTS, require_existing_root, run_git


SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("openai-style token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "credential assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}"
        ),
    ),
]

ALLOWLIST_MARKER = "dev-session-secret-allow"


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        yield path, data.decode("utf-8", errors="replace")


def changed_dev_session_files(root: Path) -> list[Path]:
    names = set()
    for command in [
        ["diff", "--name-only", "--", ".dev-session"],
        ["diff", "--cached", "--name-only", "--", ".dev-session"],
        ["ls-files", "--others", "--exclude-standard", "--", ".dev-session"],
    ]:
        output = run_git(root, command, timeout=10)
        for line in output.splitlines():
            if line:
                names.add(line)
    return sorted(root / name for name in names if (root / name).is_file())


def scan_secrets(dev_dir: Path, files: list[Path] | None = None) -> list[str]:
    findings = []
    if files is None:
        items = list(iter_text_files(dev_dir))
    else:
        items = []
        for path in files:
            data = path.read_bytes()
            if b"\0" not in data:
                items.append((path, data.decode("utf-8", errors="replace")))

    for path, text in items:
        for index, line in enumerate(text.splitlines(), start=1):
            if ALLOWLIST_MARKER in line:
                continue
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path.relative_to(dev_dir.parent)}:{index} possible {label}")
                    break
    return findings


def repository_policy_decided(decisions_path: Path) -> bool:
    if not decisions_path.exists():
        return False
    text = read_text(decisions_path).lower()
    if ".dev-session" not in text and "dev session repository policy" not in text:
        return False
    return any(term in text for term in ["commit", "committed", "ignore", "ignored", "local-only", "local only"])


def latest_file(paths: list[Path]) -> Path | None:
    return sorted(paths)[-1] if paths else None


def run_checks(root: Path, max_logs: int, max_snapshots: int, changed_only: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    dev_dir = root / ".dev-session"

    if not dev_dir.exists():
        errors.append(".dev-session/ does not exist. Run new_day_log.py first.")
        return errors, warnings
    if not dev_dir.is_dir():
        errors.append(".dev-session exists but is not a directory.")
        return errors, warnings

    required = ["SESSION.md", *CORE_FILE_DEFAULTS.keys()]
    for name in required:
        path = dev_dir / name
        if not path.exists():
            errors.append(f"Missing required file: .dev-session/{name}")

    state_path = dev_dir / "state.json"
    if not state_path.exists():
        warnings.append("Missing structured index: .dev-session/state.json. Run update_session.py --root . to regenerate it.")
    elif not state_path.is_file():
        errors.append(".dev-session/state.json exists but is not a file.")
    else:
        try:
            json.loads(read_text(state_path))
        except json.JSONDecodeError as exc:
            errors.append(f"Malformed .dev-session/state.json: {exc.msg} at line {exc.lineno}")

    logs_dir = dev_dir / "logs"
    snapshots_dir = dev_dir / "snapshots"
    if not logs_dir.is_dir():
        errors.append("Missing directory: .dev-session/logs")
        log_files: list[Path] = []
    else:
        log_files = sorted(logs_dir.glob("*.md"))
    if not snapshots_dir.is_dir():
        errors.append("Missing directory: .dev-session/snapshots")
        snapshot_files: list[Path] = []
    else:
        snapshot_files = sorted(snapshots_dir.glob("*.md"))

    if len(log_files) > max_logs:
        warnings.append(f"{len(log_files)} daily logs found; consider archiving old logs or relying on snapshot caps.")
    if len(snapshot_files) > max_snapshots:
        warnings.append(f"{len(snapshot_files)} snapshots found; consider pruning old snapshots.")

    latest_log = latest_file(log_files)
    if latest_log is None:
        warnings.append("No daily log files found.")
    else:
        text = read_text(latest_log)
        for section in ["## Work Log", "## Handoff"]:
            if section not in text:
                warnings.append(f"{latest_log.relative_to(root)} is missing {section}.")

    session_path = dev_dir / "SESSION.md"
    if session_path.exists():
        count = line_count(session_path)
        if count > 200:
            warnings.append(f"SESSION.md is {count} lines; keep it under 200 lines when possible.")
        session_text = read_text(session_path)
        if re.search(r"## Next Start\s+1\.\s*\n2\.\s*\n3\.", session_text):
            warnings.append("SESSION.md Next Start still looks blank.")

    decisions_path = dev_dir / "decisions.md"
    if not repository_policy_decided(decisions_path):
        warnings.append("No .dev-session repository policy found in decisions.md.")

    secret_files = changed_dev_session_files(root) if changed_only else None
    if changed_only and not secret_files:
        warnings.append("Changed-only secret scan found no changed .dev-session files.")

    for finding in scan_secrets(dev_dir, secret_files):
        warnings.append(f"Secret scan: {finding}")

    return errors, warnings


def print_report(errors: list[str], warnings: list[str]) -> None:
    print("# Dev Session Doctor")
    print()
    if not errors and not warnings:
        print("OK: no issues found.")
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
    parser.add_argument("--max-logs", type=int, default=90, help="Warn when more daily logs exist.")
    parser.add_argument("--max-snapshots", type=int, default=100, help="Warn when more snapshots exist.")
    parser.add_argument("--changed-only", action="store_true", help="Secret-scan only changed .dev-session files.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when warnings are found.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    if args.max_logs < 0:
        parser.error("--max-logs must be zero or greater")
    if args.max_snapshots < 0:
        parser.error("--max-snapshots must be zero or greater")

    errors, warnings = run_checks(root, args.max_logs, args.max_snapshots, args.changed_only)
    print_report(errors, warnings)
    if errors:
        return 2
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
