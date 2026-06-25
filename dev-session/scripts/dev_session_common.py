#!/usr/bin/env python3
"""Shared helpers for dev-session scripts."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any


SESSION_FALLBACK = """\
# Dev Session

## Current State
- Branch:
- Goal:
- Last meaningful change:
- Dirty worktree:

## Next Start
1.
2.
3.

## Active Risks
- 

## Key Commands
- 

## Pointers
- Latest log:
- Latest snapshot:
- Important decisions:
"""

DAILY_LOG_FALLBACK = """\
# {date}

## Start
- Goal:
- Branch: {branch}
- Starting point:

## Work Log
- {time} - Session started.

## Agent Runs
- 

## Verification
- 

## Handoff
- Changed:
- Why:
- Tests/checks:
- Decisions:
- Risks:
- Next action:
- Inspect first next session:
"""

CORE_FILE_DEFAULTS = {
    "backlog.md": "# Backlog\n\n",
    "decisions.md": "# Decisions\n\n",
    "risks.md": "# Risks\n\n",
}

ROLE_NAMES = {
    "Product Strategist",
    "Project Researcher",
    "Project Manager",
    "Explorer",
    "Developer",
    "QA/Test",
    "Reviewer/Simplifier",
    "Ops/Security Reviewer",
}

LANE_NAMES = {
    "frontend",
    "backend",
    "mcp",
    "agentic",
    "iot",
    "ops-security",
    "docs-product",
}

SESSION_MODES = {
    "orient",
    "research",
    "plan",
    "build",
    "review",
    "docs",
    "release",
    "onboarding",
}

DEFAULT_EVIDENCE_CONTRACTS = {
    "frontend": [
        "Run focused UI/unit checks where available.",
        "Smoke the changed browser flow.",
        "Capture screenshot or accessibility evidence when visual behavior changes.",
    ],
    "backend": [
        "Run focused tests for changed behavior.",
        "Prove migration or data-shape safety when storage changes.",
        "Prove API contract behavior for public or cross-service interfaces.",
    ],
    "mcp": [
        "Verify the server/tool schema loads.",
        "Call at least one safe read-only tool through the intended client when possible.",
        "Record auth, approval, and tool-safety limits.",
    ],
    "agentic": [
        "Run an eval, trace, fixture, or replay for the changed agent path.",
        "Check tool permission boundaries and prompt-injection exposure.",
        "Record fallback and recovery behavior.",
    ],
    "iot": [
        "Run simulator, bench, or device smoke when available.",
        "Record firmware/hardware version and connection path.",
        "Capture safe rollback or recovery instructions.",
    ],
    "ops-security": [
        "Run relevant config, secret, auth, deployment, or policy checks.",
        "Record rollback, monitoring, and alerting evidence.",
        "Confirm no secrets or sensitive data were added to durable logs.",
    ],
    "docs-product": [
        "Identify audience and source-of-truth status.",
        "Verify examples, links, commands, and screenshots where applicable.",
        "Record review owner or product decision needed before publishing.",
    ],
}

DEFAULT_DECISION_THRESHOLDS = [
    "architecture changed",
    "workflow changed",
    "dependency added",
    "security/release posture changed",
    "team convention changed",
]

DEFAULT_INTAKE = {
    "ask_max": 3,
    "defaults": {
        "autonomy": "confirm-provider-mutations",
        "evidence": "lane-contract",
        "style": "infer-first",
    },
}

DEFAULT_PROFILE = {
    "schema_version": 1,
    "provider": "unknown",
    "default_branch": "",
    "workflow": "paved-path",
    "scale": "",
    "ownership": {
        "workflow_owners": [],
        "lane_owners": {
            "frontend": [],
            "backend": [],
            "mcp": [],
            "agentic": [],
            "iot": [],
            "ops-security": [],
            "docs-product": [],
        },
    },
    "commands": {
        "install": [],
        "dev": [],
        "test": [],
        "lint": [],
        "build": [],
        "smoke": [],
    },
    "services": [],
    "ci": {
        "provider": "unknown",
        "files": [],
    },
    "deploy": {
        "environments": [],
        "rollback": "",
    },
    "evidence_contracts": DEFAULT_EVIDENCE_CONTRACTS,
    "decision_thresholds": DEFAULT_DECISION_THRESHOLDS,
    "mcp_trust_catalog": [],
    "onboarding": {
        "harmless_smoke": [],
        "access_checks": [],
    },
    "flow_metrics": {
        "enabled": True,
        "purpose": "Find workflow friction; do not score individual developers.",
        "allowed_kinds": [
            "review_age",
            "blocked_reason",
            "flaky_check",
            "setup_gap",
            "handoff_gap",
        ],
    },
    "intake": DEFAULT_INTAKE,
}


def require_existing_root(parser: argparse.ArgumentParser, value: str) -> Path:
    root = Path(value).resolve()
    if not root.is_dir():
        parser.error(f"--root must be an existing directory: {root}")
    return root


def git_branch(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except FileNotFoundError:
        return ""
    except subprocess.TimeoutExpired:
        return ""
    branch = result.stdout.strip()
    if branch:
        return branch

    try:
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except FileNotFoundError:
        return ""
    except subprocess.TimeoutExpired:
        return ""
    if inside.stdout.strip() != "true":
        return ""

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "detached HEAD"
    short_hash = commit.stdout.strip()
    if commit.returncode == 0 and short_hash:
        return f"detached at {short_hash}"
    return "detached HEAD"


def is_git_repo(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        return False
    return result.stdout.strip() == "true"


def run_git(root: Path, args: list[str], timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError:
        return ""
    except subprocess.TimeoutExpired:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def run_command(root: Path, args: list[str], timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError:
        return ""
    except subprocess.TimeoutExpired:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def git_dirty_summary(root: Path) -> str:
    if not is_git_repo(root):
        return "N/A (not a git repository)"
    status = run_git(root, ["status", "--short"], timeout=10)
    if not status:
        return "clean"
    staged = run_git(root, ["diff", "--cached", "--name-only"], timeout=10).splitlines()
    tracked = run_git(root, ["diff", "--name-only"], timeout=10).splitlines()
    untracked = run_git(root, ["ls-files", "--others", "--exclude-standard"], timeout=10).splitlines()
    parts = []
    if staged:
        parts.append(f"{len(staged)} staged")
    if tracked:
        parts.append(f"{len(tracked)} tracked")
    if untracked:
        parts.append(f"{len(untracked)} untracked")
    return ", ".join(parts) if parts else f"{len(status.splitlines())} changed/untracked file(s)"


def parse_date(value: str | None) -> str:
    if value is None:
        return dt.date.today().isoformat()
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--date must use YYYY-MM-DD") from exc


def load_asset(name: str, fallback: str) -> str:
    asset_path = Path(__file__).resolve().parents[1] / "assets" / name
    if not asset_path.exists():
        return fallback
    return asset_path.read_text(encoding="utf-8")


def render_template(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{" + key + "}", value)
    return rendered


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def ensure_core_files(base: Path) -> list[Path]:
    created = []
    for name, content in CORE_FILE_DEFAULTS.items():
        path = base / name
        if write_if_missing(path, content):
            created.append(path)
    return created


def latest_file(directory: Path, pattern: str = "*.md") -> Path | None:
    if not directory.is_dir():
        return None
    files = sorted(path for path in directory.glob(pattern) if path.is_file())
    return files[-1] if files else None


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = deep_merge(merged[key], value) if key in merged else value
        return merged
    return override


def profile_path(root: Path) -> Path:
    return root / ".dev-session" / "profile.json"


def load_profile(root: Path) -> dict[str, Any]:
    path = profile_path(root)
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_PROFILE))
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return json.loads(json.dumps(DEFAULT_PROFILE))
    return deep_merge(json.loads(json.dumps(DEFAULT_PROFILE)), data)


def save_profile(root: Path, profile: dict[str, Any]) -> None:
    write_json(profile_path(root), profile)


def detect_provider(root: Path) -> str:
    remotes = run_git(root, ["remote", "-v"], timeout=10).lower()
    if "github.com" in remotes or "github." in remotes:
        return "github"
    if "gitlab.com" in remotes or "gitlab." in remotes:
        return "gitlab"
    if (root / ".github").exists():
        return "github"
    if (root / ".gitlab-ci.yml").exists() or (root / ".gitlab").exists():
        return "gitlab"
    return "unknown"


def detect_default_branch(root: Path) -> str:
    origin_head = run_git(root, ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], timeout=10)
    if origin_head.startswith("origin/"):
        return origin_head.removeprefix("origin/")
    branch = git_branch(root)
    return branch if branch and not branch.startswith("detached ") else ""


def distinct_commit_authors(root: Path, limit: int = 50) -> int:
    output = run_git(root, ["log", "--no-merges", f"--max-count={limit}", "--format=%ae"], timeout=10)
    return len({line.strip().lower() for line in output.splitlines() if line.strip()})


def detect_scale(root: Path) -> str:
    """Heuristic project scale: 'team' when there are signs of multiple contributors, else 'solo'.

    Solo is the lighter default: team ownership, CODEOWNERS, and approval checks only make
    sense once a repo actually has more than one contributor or has opted into them.
    """
    if find_codeowners(root, detect_provider(root)) is not None:
        return "team"
    if distinct_commit_authors(root) > 1:
        return "team"
    return "solo"


def detect_ci(root: Path) -> dict[str, Any]:
    files: list[str] = []
    provider = "unknown"
    github_workflows = root / ".github" / "workflows"
    if github_workflows.is_dir():
        for path in sorted(github_workflows.glob("*.y*ml")):
            files.append(str(path.relative_to(root)))
        if files:
            provider = "github-actions"
    gitlab_ci = root / ".gitlab-ci.yml"
    if gitlab_ci.exists():
        files.append(str(gitlab_ci.relative_to(root)))
        provider = "gitlab-ci"
    return {"provider": provider, "files": files}


def detect_commands(root: Path) -> dict[str, list[str]]:
    commands = json.loads(json.dumps(DEFAULT_PROFILE["commands"]))
    package_json = root / "package.json"
    if package_json.exists():
        try:
            scripts = json.loads(package_json.read_text(encoding="utf-8")).get("scripts", {})
        except json.JSONDecodeError:
            scripts = {}
        package_runner = "npm"
        if (root / "pnpm-lock.yaml").exists():
            package_runner = "pnpm"
        elif (root / "yarn.lock").exists():
            package_runner = "yarn"
        for name in ["dev", "test", "lint", "build"]:
            if name in scripts:
                commands[name].append(f"{package_runner} run {name}")
        if package_runner == "pnpm":
            commands["install"].append("pnpm install")
        elif package_runner == "yarn":
            commands["install"].append("yarn install")
        else:
            commands["install"].append("npm install")
    if (root / "Makefile").exists() or (root / "makefile").exists():
        commands["test"].append("make test")
        commands["build"].append("make build")
    if (root / "pyproject.toml").exists():
        commands["test"].append("pytest")
    return commands


def detect_services(root: Path) -> list[str]:
    candidates = ["apps", "packages", "services", "src", "mcp", "firmware", "infra", "docs"]
    return [name for name in candidates if (root / name).exists()]


def useful_detected(value: Any) -> bool:
    return value not in ("", "unknown", [], {}, None)


def merge_unique(existing: list[Any], detected: list[Any]) -> list[Any]:
    merged = list(existing)
    for item in detected:
        if item not in merged:
            merged.append(item)
    return merged


def merge_detected_value(current: Any, detected: Any) -> Any:
    if not useful_detected(detected):
        return current
    if isinstance(current, dict) and isinstance(detected, dict):
        merged = dict(current)
        for key, value in detected.items():
            merged[key] = merge_detected_value(merged.get(key), value)
        return merged
    if isinstance(current, list) and isinstance(detected, list):
        return merge_unique(current, detected)
    if not useful_detected(current):
        return detected
    return current


def build_profile(root: Path, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = existing or load_profile(root)
    detected = {
        "provider": detect_provider(root),
        "default_branch": detect_default_branch(root),
        "scale": detect_scale(root),
        "commands": detect_commands(root),
        "services": detect_services(root),
        "ci": detect_ci(root),
    }
    for key, value in detected.items():
        profile[key] = merge_detected_value(profile.get(key), value)
    return profile


def profile_summary(profile: dict[str, Any]) -> str:
    provider = profile.get("provider") or "unknown"
    default_branch = profile.get("default_branch") or "(unknown)"
    workflow_owners = profile.get("ownership", {}).get("workflow_owners", [])
    owners = ", ".join(workflow_owners) if workflow_owners else "(not set)"
    return f"Provider: {provider}\nDefault branch: {default_branch}\nWorkflow owners: {owners}"


def evidence_contract(profile: dict[str, Any], lane: str) -> list[str]:
    contracts = profile.get("evidence_contracts", {})
    return list(contracts.get(lane, DEFAULT_EVIDENCE_CONTRACTS.get(lane, [])))


def should_record_decision(text: str, profile: dict[str, Any] | None = None) -> list[str]:
    haystack = text.lower()
    thresholds = (profile or DEFAULT_PROFILE).get("decision_thresholds", DEFAULT_DECISION_THRESHOLDS)
    matched = []
    keyword_map = {
        "architecture changed": ["architecture", "architectural", "service boundary", "data model"],
        "workflow changed": ["workflow", "process", "pipeline", "dev-session", "codeowners"],
        "dependency added": ["dependency", "package", "library", "sdk", "added dep"],
        "security/release posture changed": ["security", "auth", "permission", "release", "deploy", "rollback"],
        "team convention changed": ["convention", "standard", "team rule", "coding guideline"],
    }
    for threshold in thresholds:
        words = keyword_map.get(threshold, [threshold])
        if any(word in haystack for word in words):
            matched.append(threshold)
    return matched


def classify_session_mode(prompt: str) -> str:
    text = prompt.lower()
    if any(word in text for word in ["onboard", "new dev", "new developer", "setup my machine"]):
        return "onboarding"
    if any(word in text for word in ["research", "investigate options", "competitor", "market"]):
        return "research"
    if any(word in text for word in ["plan", "design", "architecture", "spec"]):
        return "plan"
    if any(word in text for word in ["review", "audit", "pr ", "merge request", "mr "]):
        return "review"
    if any(word in text for word in ["docs", "documentation", "readme", "write guide"]):
        return "docs"
    if any(word in text for word in ["release", "deploy", "rollback", "production"]):
        return "release"
    if any(word in text for word in ["fix", "build", "implement", "add feature", "code"]):
        return "build"
    return "orient"


def infer_lane(prompt: str, changed_files: list[str] | None = None) -> str:
    text = " ".join([prompt, *(changed_files or [])]).lower()
    if any(word in text for word in ["frontend", "react", "vue", "svelte", "css", "browser", "ui", "playwright"]):
        return "frontend"
    if any(word in text for word in ["mcp", "tool schema", "tools/list", "server"]):
        return "mcp"
    if any(word in text for word in ["agent", "eval", "prompt", "trace", "tool use"]):
        return "agentic"
    if any(word in text for word in ["iot", "firmware", "device", "arduino", "sensor"]):
        return "iot"
    if any(word in text for word in ["deploy", "infra", "security", "auth", "secret", "ops"]):
        return "ops-security"
    if any(word in text for word in ["docs", "readme", "product", "requirements"]):
        return "docs-product"
    return "backend"


def current_issue_hint(root: Path) -> str:
    branch = git_branch(root)
    match = re_search_issue(branch)
    return match or ""


def re_search_issue(text: str) -> str:
    import re

    match = re.search(r"(?:issue|bug|fix|feat|feature|pr|mr)[-/ _#]*(\d+)", text.lower())
    return f"#{match.group(1)}" if match else ""


def codeowners_candidates(root: Path, provider: str) -> list[Path]:
    if provider == "github":
        return [root / ".github" / "CODEOWNERS", root / "CODEOWNERS", root / "docs" / "CODEOWNERS"]
    if provider == "gitlab":
        return [root / "CODEOWNERS", root / "docs" / "CODEOWNERS", root / ".gitlab" / "CODEOWNERS"]
    return [root / ".github" / "CODEOWNERS", root / "CODEOWNERS", root / "docs" / "CODEOWNERS", root / ".gitlab" / "CODEOWNERS"]


def find_codeowners(root: Path, provider: str) -> Path | None:
    for path in codeowners_candidates(root, provider):
        if path.exists():
            return path
    return None


def codeowners_covers(root: Path, codeowners: Path, expected_paths: list[str]) -> list[str]:
    text = codeowners.read_text(encoding="utf-8", errors="replace")
    missing = []
    patterns = []
    for line in text.replace("\\", "/").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("["):
            continue
        patterns.append(stripped.split()[0])
    for item in expected_paths:
        if not any(codeowners_pattern_covers(pattern, item) for pattern in patterns):
            missing.append(item)
    return missing


def codeowners_pattern_covers(pattern: str, expected_path: str) -> bool:
    path = expected_path.strip("/").replace("\\", "/")
    pattern = pattern.strip().replace("\\", "/")
    pattern_no_slash = pattern.strip("/")

    if not path:
        return False
    if pattern_no_slash == path:
        return True

    if pattern_no_slash.endswith("/**"):
        prefix = pattern_no_slash[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")

    if pattern_no_slash.endswith("/*"):
        prefix = pattern_no_slash[:-2].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")

    if pattern_no_slash.endswith("/"):
        prefix = pattern_no_slash.rstrip("/")
        return path == prefix or path.startswith(prefix + "/")

    if "*" in pattern_no_slash or "?" in pattern_no_slash:
        return fnmatch.fnmatch(path, pattern_no_slash) or fnmatch.fnmatch("/" + path, pattern)

    return path.startswith(pattern_no_slash.rstrip("/") + "/")


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default
