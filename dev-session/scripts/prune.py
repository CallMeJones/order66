#!/usr/bin/env python3
"""Prune or archive old .dev-session logs and snapshots. Dry-run by default."""

from __future__ import annotations

import argparse
import datetime as dt
import zipfile
from pathlib import Path

from dev_session_common import require_existing_root


def old_files(directory: Path, keep: int) -> list[Path]:
    if not directory.is_dir():
        return []
    files = sorted(path for path in directory.glob("*.md") if path.is_file())
    if keep == 0:
        return files
    return files[:-keep] if len(files) > keep else []


def archive_files(root: Path, files: list[Path]) -> Path:
    archive_dir = root / ".dev-session" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = archive_dir / f"prune-{stamp}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(root))
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--keep-logs", type=int, default=90, help="Number of newest daily logs to keep.")
    parser.add_argument("--keep-snapshots", type=int, default=100, help="Number of newest snapshots to keep.")
    parser.add_argument("--delete", action="store_true", help="Delete old files instead of dry-run.")
    parser.add_argument("--archive", action="store_true", help="Archive old files to .dev-session/archive before deleting.")
    args = parser.parse_args()

    root = require_existing_root(parser, args.root)
    if args.keep_logs < 0:
        parser.error("--keep-logs must be zero or greater")
    if args.keep_snapshots < 0:
        parser.error("--keep-snapshots must be zero or greater")

    dev_dir = root / ".dev-session"
    targets = [
        *old_files(dev_dir / "logs", args.keep_logs),
        *old_files(dev_dir / "snapshots", args.keep_snapshots),
    ]

    print("# Dev Session Prune")
    if not targets:
        print("No files eligible for pruning.")
        return 0

    for path in targets:
        print(f"- {path.relative_to(root)}")

    if not args.delete and not args.archive:
        print("\nDry run only. Add --delete or --archive to modify files.")
        return 0

    if args.archive:
        archive_path = archive_files(root, targets)
        print(f"\nArchived to {archive_path}")

    if args.delete or args.archive:
        for path in targets:
            path.unlink()
        print(f"Removed {len(targets)} file(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
