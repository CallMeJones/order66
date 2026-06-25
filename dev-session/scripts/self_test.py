#!/usr/bin/env python3
"""Run smoke tests for the dev-session skill scripts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from dev_session_common import classify_session_mode, should_record_decision


SCRIPT_DIR = Path(__file__).resolve().parent
NEW_DAY = SCRIPT_DIR / "new_day_log.py"
SNAPSHOT = SCRIPT_DIR / "session_snapshot.py"
END = SCRIPT_DIR / "end_session.py"
DOCTOR = SCRIPT_DIR / "doctor.py"
UPDATE = SCRIPT_DIR / "update_session.py"
PRUNE = SCRIPT_DIR / "prune.py"
PROMPT = SCRIPT_DIR / "make_agent_prompt.py"
SETUP = SCRIPT_DIR / "setup_profile.py"
CONTEXT = SCRIPT_DIR / "context_pack.py"
WORKFLOW_DOCTOR = SCRIPT_DIR / "workflow_doctor.py"
COMPOSE = SCRIPT_DIR / "compose_pr.py"
METRIC = SCRIPT_DIR / "record_flow_metric.py"
VERIFY = SCRIPT_DIR / "verify.py"


class TestFailure(Exception):
    pass


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=60,
    )
    if check and result.returncode != 0:
        raise TestFailure(f"Command failed: {' '.join(args)}\n{result.stdout}")
    return result


def git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        raise TestFailure(f"git {' '.join(args)} failed\n{result.stdout}")


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        raise TestFailure(f"git {' '.join(args)} failed\n{result.stdout}")
    return result.stdout.strip()


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise TestFailure(message)


def temp_root(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


def core_files_exist(root: Path) -> bool:
    names = {"SESSION.md", "backlog.md", "decisions.md", "risks.md"}
    found = {path.name for path in (root / ".dev-session").glob("*.md")}
    return names.issubset(found)


def test_full_flow() -> Path:
    root = temp_root("dev-session-full-")
    git(root, "init")
    (root / "README.md").write_text("# Test\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "-c", "user.name=Claude Test", "-c", "user.email=claude@example.test", "commit", "-m", "initial")
    (root / "README.md").write_text("# Test\nDirty change\n", encoding="utf-8")
    (root / "notes.txt").write_text("untracked\n", encoding="utf-8")

    run([str(NEW_DAY), "--root", str(root), "--date", "2026-05-28"])
    run([str(NEW_DAY), "--root", str(root), "--date", "2026-05-28"])
    run([str(SNAPSHOT), "--root", str(root), "--out", "--update-session", "--log-count", "1", "--max-logs", "3", "--max-snapshots", "3"])
    run([str(END), "--root", str(root), "--date", "2026-05-28"])

    log = (root / ".dev-session" / "logs" / "2026-05-28.md").read_text(encoding="utf-8")
    snapshot_path = next((root / ".dev-session" / "snapshots").glob("*.md"))
    snapshot = snapshot_path.read_text(encoding="utf-8")
    state = (root / ".dev-session" / "state.json").read_text(encoding="utf-8")
    assert_true(core_files_exist(root), "core files missing after full flow")
    assert_true("Session resumed." in log, "resume note missing")
    assert_true("Inspect first next session:" in log, "handoff inspect field missing")
    assert_true("notes.txt" in snapshot, "untracked file missing from snapshot")
    assert_true("README.md" in snapshot, "dirty file missing from snapshot")
    assert_true(str(snapshot_path.relative_to(root)).replace("\\", "\\\\") in state or snapshot_path.name in state, "snapshot did not refresh state.json")
    return root


def test_end_first() -> Path:
    root = temp_root("dev-session-end-first-")
    run([str(END), "--root", str(root), "--date", "2026-05-28"])
    log = (root / ".dev-session" / "logs" / "2026-05-28.md").read_text(encoding="utf-8")
    session = (root / ".dev-session" / "SESSION.md").read_text(encoding="utf-8")
    assert_true(core_files_exist(root), "core files missing after end-first flow")
    assert_true((root / ".dev-session" / "snapshots").is_dir(), "snapshots dir missing")
    assert_true("## Current State" in session and "## Pointers" in session, "SESSION.md is incomplete")
    assert_true("## Work Log" in log and "## Handoff" in log, "daily log is incomplete")
    return root


def test_no_git_snapshot() -> Path:
    root = temp_root("dev-session-no-git-")
    run([str(NEW_DAY), "--root", str(root), "--date", "2026-05-28"])
    result = run([str(SNAPSHOT), "--root", str(root), "--out"])
    assert_true("Not a git repository" in result.stdout, "non-git snapshot did not explain state")
    assert_true(".dev-session" in result.stdout, "non-git snapshot did not list dev-session files")
    return root


def test_invalid_inputs() -> Path:
    root = temp_root("dev-session-invalid-")
    bad_date = run([str(NEW_DAY), "--root", str(root), "--date", "../bad"], check=False)
    bad_logs = run([str(SNAPSHOT), "--root", str(root), "--max-logs", "-1"], check=False)
    assert_true(bad_date.returncode != 0 and "--date must use YYYY-MM-DD" in bad_date.stdout, "bad date accepted")
    assert_true(bad_logs.returncode != 0 and "--max-logs must be zero or greater" in bad_logs.stdout, "bad max logs accepted")
    return root


def test_doctor() -> Path:
    root = temp_root("dev-session-doctor-")
    run([str(NEW_DAY), "--root", str(root), "--date", "2026-05-28"])
    result = run([str(DOCTOR), "--root", str(root)], check=False)
    assert_true(result.returncode == 0, f"doctor returned unexpected failure\n{result.stdout}")
    assert_true("state.json" in result.stdout, "doctor did not warn about missing state.json")
    assert_true("repository policy" in result.stdout, "doctor did not warn about repository policy")
    strict = run([str(DOCTOR), "--root", str(root), "--strict"], check=False)
    assert_true(strict.returncode == 1, "doctor strict mode did not fail on warnings")
    run([str(UPDATE), "--root", str(root), "--goal", "Refresh state"])
    refreshed = run([str(DOCTOR), "--root", str(root)], check=False)
    assert_true("state.json" not in refreshed.stdout, "doctor warned about state.json after refresh")
    (root / ".dev-session" / "SESSION.md").unlink()
    broken = run([str(DOCTOR), "--root", str(root)], check=False)
    assert_true(broken.returncode == 2 and "Missing required file" in broken.stdout, "doctor did not fail on missing core file")
    return root


def test_doctor_malformed_state() -> Path:
    root = temp_root("dev-session-doctor-state-")
    run([str(NEW_DAY), "--root", str(root), "--date", "2026-05-28"])
    (root / ".dev-session" / "state.json").write_text("{bad json\n", encoding="utf-8")
    result = run([str(DOCTOR), "--root", str(root)], check=False)
    assert_true(result.returncode == 2 and "Malformed .dev-session/state.json" in result.stdout, "doctor accepted malformed state.json")
    return root


def test_update_session() -> Path:
    root = temp_root("dev-session-update-")
    git(root, "init")
    run([str(NEW_DAY), "--root", str(root), "--date", "2026-05-28"])
    run(
        [
            str(UPDATE),
            "--root",
            str(root),
            "--goal",
            "Ship useful continuity",
            "--next",
            "Run tests",
            "--risk",
            "Repo policy undecided",
            "--command",
            "python scripts/self_test.py",
        ]
    )
    session = (root / ".dev-session" / "SESSION.md").read_text(encoding="utf-8")
    state = (root / ".dev-session" / "state.json").read_text(encoding="utf-8")
    assert_true("Ship useful continuity" in session, "SESSION.md goal was not updated")
    assert_true("Run tests" in session, "SESSION.md next action was not updated")
    assert_true('"goal": "Ship useful continuity"' in state, "state.json goal missing")
    return root


def test_no_git_update_session() -> Path:
    root = temp_root("dev-session-update-no-git-")
    run([str(UPDATE), "--root", str(root), "--goal", "No git project"])
    session = (root / ".dev-session" / "SESSION.md").read_text(encoding="utf-8")
    state = (root / ".dev-session" / "state.json").read_text(encoding="utf-8")
    assert_true("N/A (not a git repository)" in session, "no-git SESSION.md state is misleading")
    assert_true('"dirty_worktree": "N/A (not a git repository)"' in state, "no-git state.json dirty state is misleading")
    return root


def test_detached_head_update_session() -> Path:
    root = temp_root("dev-session-detached-")
    git(root, "init")
    git(root, "config", "user.name", "Claude Test")
    git(root, "config", "user.email", "claude@example.test")
    (root / "README.md").write_text("# Detached\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "initial")
    short_hash = git_output(root, "rev-parse", "--short", "HEAD")
    git(root, "checkout", "--detach", "HEAD")
    run([str(UPDATE), "--root", str(root), "--goal", "Detached review"])
    session = (root / ".dev-session" / "SESSION.md").read_text(encoding="utf-8")
    state = (root / ".dev-session" / "state.json").read_text(encoding="utf-8")
    expected = f"detached at {short_hash}"
    assert_true(f"Branch: {expected}" in session, "detached HEAD branch was not recorded in SESSION.md")
    assert_true(f'"branch": "{expected}"' in state, "detached HEAD branch was not recorded in state.json")
    return root


def test_prune() -> Path:
    root = temp_root("dev-session-prune-")
    logs = root / ".dev-session" / "logs"
    snapshots = root / ".dev-session" / "snapshots"
    logs.mkdir(parents=True)
    snapshots.mkdir(parents=True)
    for index in range(5):
        (logs / f"2026-05-{index + 1:02}.md").write_text("log\n", encoding="utf-8")
        (snapshots / f"202605{index + 1:02}-100000.md").write_text("snap\n", encoding="utf-8")
    dry = run([str(PRUNE), "--root", str(root), "--keep-logs", "2", "--keep-snapshots", "2"])
    assert_true("Dry run only" in dry.stdout, "prune did not default to dry-run")
    run([str(PRUNE), "--root", str(root), "--keep-logs", "2", "--keep-snapshots", "2", "--archive"])
    assert_true(len(list(logs.glob("*.md"))) == 2, "prune did not remove old logs after archive")
    assert_true(len(list(snapshots.glob("*.md"))) == 2, "prune did not remove old snapshots after archive")
    assert_true(any((root / ".dev-session" / "archive").glob("*.zip")), "prune archive was not created")
    return root


def test_setup_profile_and_context_pack() -> Path:
    root = temp_root("dev-session-profile-")
    git(root, "init")
    git(root, "remote", "add", "origin", "https://github.com/example/project.git")
    (root / "package.json").write_text(
        json.dumps({"scripts": {"dev": "vite", "test": "vitest", "lint": "eslint .", "build": "vite build"}}),
        encoding="utf-8",
    )
    workflow_dir = root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (root / "apps" / "web").mkdir(parents=True)

    run([str(SETUP), "--root", str(root), "--mode", "write"])
    profile = json.loads((root / ".dev-session" / "profile.json").read_text(encoding="utf-8"))
    assert_true(profile["provider"] == "github", "setup profile did not detect GitHub")
    assert_true("frontend" in profile["evidence_contracts"], "frontend evidence contract missing")
    assert_true("architecture changed" in profile["decision_thresholds"], "decision thresholds missing")
    claude_skill = root / ".claude" / "skills" / "dev-session" / "SKILL.md"
    assert_true(claude_skill.exists(), "Claude project skill was not scaffolded")
    assert_true((root / ".claude" / "skills" / "dev-session" / "scripts" / "context_pack.py").exists(), "Claude project skill scripts were not copied")
    assert_true("C:\\Users\\Michael" not in claude_skill.read_text(encoding="utf-8"), "Claude project skill contains a personal absolute path")
    assert_true((root / "CLAUDE.md").read_text(encoding="utf-8").startswith("# Claude Project Guidance"), "CLAUDE.md did not start with Claude project guidance")

    pack = run([str(CONTEXT), "--root", str(root), "--prompt", "implement frontend checkout bug"])
    assert_true("Session mode: build" in pack.stdout, "context pack did not classify build mode")
    assert_true("Lane: frontend" in pack.stdout, "context pack did not infer frontend lane")
    assert_true("MCP Readiness" in pack.stdout, "context pack missing MCP readiness")
    assert_true("Ceremony: light" in pack.stdout, "context pack missing fast-lane ceremony hint")

    onboarding = run([str(CONTEXT), "--root", str(root), "--session-mode", "onboarding"])
    assert_true("## Onboarding" in onboarding.stdout, "onboarding mode did not include onboarding checklist")
    return root


def test_setup_profile_preserves_team_truth() -> Path:
    root = temp_root("dev-session-profile-preserve-")
    git(root, "init")
    dev_dir = root / ".dev-session"
    dev_dir.mkdir()
    profile = {
        "provider": "github",
        "ci": {"provider": "github-actions", "files": [".github/workflows/ci.yml"]},
        "commands": {"test": ["custom test"], "build": ["custom build"]},
        "ownership": {
            "workflow_owners": ["@org/dev"],
            "lane_owners": {
                "frontend": ["@org/front"],
                "backend": ["@org/back"],
                "mcp": ["@org/platform"],
                "agentic": ["@org/platform"],
                "iot": ["@org/iot"],
                "ops-security": ["@org/sec"],
                "docs-product": ["@org/product"],
            },
        },
    }
    (dev_dir / "profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")
    run([str(SETUP), "--root", str(root), "--mode", "write"])
    updated = json.loads((dev_dir / "profile.json").read_text(encoding="utf-8"))
    assert_true(updated["ci"]["provider"] == "github-actions", "setup profile overwrote curated CI provider")
    assert_true(updated["commands"]["test"] == ["custom test"], "setup profile overwrote curated test command")
    assert_true(updated["ownership"]["workflow_owners"] == ["@org/dev"], "setup profile overwrote workflow owners")
    return root


def test_workflow_doctor_ownership() -> Path:
    root = temp_root("dev-session-workflow-doctor-")
    git(root, "init")
    run([str(SETUP), "--root", str(root), "--mode", "write"])
    profile_path = root / ".dev-session" / "profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["scale"] = "team"
    profile["ownership"]["workflow_owners"] = ["@org/dev-workflow-owners"]
    for lane in profile["ownership"]["lane_owners"]:
        profile["ownership"]["lane_owners"][lane] = ["@org/dev-workflow-owners"]
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    missing = run([str(WORKFLOW_DOCTOR), "--root", str(root)], check=False)
    assert_true("No CODEOWNERS file found" in missing.stdout, "workflow doctor did not warn on missing CODEOWNERS")

    (root / ".github").mkdir()
    (root / ".github" / "CODEOWNERS").write_text(
        "\n".join(
            [
                "/.dev-session/** @org/dev-workflow-owners",
                "/.claude/skills/dev-session/** @org/dev-workflow-owners",
                "/CLAUDE.md @org/dev-workflow-owners",
                "/.mcp.json @org/dev-workflow-owners",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    covered = run([str(WORKFLOW_DOCTOR), "--root", str(root)], check=False)
    assert_true("CODEOWNERS does not appear to cover" not in covered.stdout, "workflow doctor missed CODEOWNERS coverage")
    assert_true("Provider branch/MR protection was not verified" in covered.stdout, "workflow doctor should warn that provider protection is not verified")
    return root


def test_workflow_doctor_solo() -> Path:
    root = temp_root("dev-session-workflow-solo-")
    git(root, "init")
    run([str(SETUP), "--root", str(root), "--mode", "write"])
    result = run([str(WORKFLOW_DOCTOR), "--root", str(root)], check=False)
    assert_true("Scale: solo" in result.stdout, "workflow doctor did not report solo scale")
    assert_true("No CODEOWNERS file found" not in result.stdout, "solo workflow doctor warned about CODEOWNERS")
    assert_true("No lane owner declared" not in result.stdout, "solo workflow doctor warned about lane owners")
    assert_true(result.returncode == 0, "solo workflow doctor returned nonzero")
    return root


def test_workflow_doctor_accepts_bom_profile() -> Path:
    root = temp_root("dev-session-profile-bom-")
    (root / ".dev-session").mkdir()
    profile = {
        "provider": "github",
        "ownership": {
            "workflow_owners": ["@org/dev"],
            "lane_owners": {
                "frontend": ["@org/dev"],
                "backend": ["@org/dev"],
                "mcp": ["@org/dev"],
                "agentic": ["@org/dev"],
                "iot": ["@org/dev"],
                "ops-security": ["@org/dev"],
                "docs-product": ["@org/dev"],
            },
        },
    }
    (root / ".dev-session" / "profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8-sig")
    result = run([str(WORKFLOW_DOCTOR), "--root", str(root)], check=False)
    assert_true("Malformed .dev-session/profile.json" not in result.stdout, "workflow doctor rejected UTF-8 BOM profile")
    return root


def test_compose_pr() -> Path:
    root = temp_root("dev-session-compose-")
    git(root, "init")
    (root / "service.py").write_text("print('hello')\n", encoding="utf-8")
    git(root, "add", "service.py")
    git(root, "-c", "user.name=Claude Test", "-c", "user.email=claude@example.test", "commit", "-m", "initial")
    (root / "service.py").write_text("print('hello world')\n", encoding="utf-8")
    run([str(SETUP), "--root", str(root), "--mode", "write"])
    profile_path = root / ".dev-session" / "profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["ownership"]["workflow_owners"] = ["@org/dev-workflow-owners"]
    profile["ownership"]["lane_owners"]["backend"] = ["@org/backend-leads"]
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    pr = run([str(COMPOSE), "--root", str(root), "--provider", "github", "--lane", "backend", "--summary", "Update greeting", "--dry-run"])
    for section in ["## Summary", "## Evidence", "## Risks", "## Screenshots / Logs", "## Reviewers", "## Rollout / Rollback"]:
        assert_true(section in pr.stdout, f"PR composer missing {section}")
    assert_true("@org/backend-leads" in pr.stdout, "PR composer did not suggest lane owner")
    assert_true("service.py" in pr.stdout, "PR composer did not list changed file")
    return root


def test_compose_pr_base_branch() -> Path:
    root = temp_root("dev-session-compose-base-")
    git(root, "init")
    (root / "service.py").write_text("print('hello')\n", encoding="utf-8")
    git(root, "add", "service.py")
    git(root, "-c", "user.name=Claude Test", "-c", "user.email=claude@example.test", "commit", "-m", "initial")
    base = git_output(root, "branch", "--show-current")
    git(root, "checkout", "-b", "feature/login")
    (root / "login.py").write_text("print('login')\n", encoding="utf-8")
    git(root, "add", "login.py")
    git(root, "-c", "user.name=Claude Test", "-c", "user.email=claude@example.test", "commit", "-m", "add login")

    # The committed change exists only on the feature branch; a clean worktree must still show it.
    pr = run([str(COMPOSE), "--root", str(root), "--provider", "github", "--base", base, "--summary", "Add login", "--dry-run"])
    assert_true("login.py" in pr.stdout, "PR composer did not list committed change vs base branch")
    assert_true("No changes detected" not in pr.stdout, "PR composer reported no changes for a committed branch")

    # Add an uncommitted change on top: composer must union committed + uncommitted in files and stat.
    (root / "service.py").write_text("print('hello world')\n", encoding="utf-8")
    combined = run([str(COMPOSE), "--root", str(root), "--provider", "github", "--base", base, "--summary", "Add login", "--dry-run"])
    assert_true("login.py" in combined.stdout, "PR composer dropped committed change when worktree was dirty")
    assert_true("service.py" in combined.stdout, "PR composer dropped uncommitted change vs base branch")
    return root


def test_verify() -> Path:
    root = temp_root("dev-session-verify-")
    git(root, "init")
    run([str(SETUP), "--root", str(root), "--mode", "write"])
    run([str(NEW_DAY), "--root", str(root), "--date", "2026-05-28"])
    profile_path = root / ".dev-session" / "profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["commands"]["lint"] = ["echo lint-ok"]
    profile["commands"]["test"] = ["echo test-ok"]
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    passing = run([str(VERIFY), "--root", str(root), "--lane", "backend", "--write-log", "--date", "2026-05-28"])
    assert_true("Result: PASS" in passing.stdout, "verify did not summarize a passing run")
    log = (root / ".dev-session" / "logs" / "2026-05-28.md").read_text(encoding="utf-8")
    assert_true("## Verification" in log, "verify did not append evidence to the daily log")

    profile["commands"]["test"] = ["exit 1"]
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    failing = run([str(VERIFY), "--root", str(root), "--lane", "backend"], check=False)
    assert_true(failing.returncode == 1 and "Result: FAIL" in failing.stdout, "verify did not fail on a failing command")

    empty_root = temp_root("dev-session-verify-empty-")
    run([str(SETUP), "--root", str(empty_root), "--mode", "write"])
    none = run([str(VERIFY), "--root", str(empty_root), "--lane", "backend"], check=False)
    assert_true(none.returncode == 0 and "No verification commands" in none.stdout, "verify did not no-op on an empty command set")
    shutil.rmtree(empty_root, ignore_errors=True)
    return root


def test_decision_thresholds_and_intake() -> Path:
    root = temp_root("dev-session-thresholds-")
    assert_true(classify_session_mode("research unicorn dev pipelines") == "research", "research mode classification failed")
    assert_true(classify_session_mode("write docs for setup") == "docs", "docs mode classification failed")
    assert_true(classify_session_mode("deploy to staging") == "release", "release mode classification failed")
    assert_true("architecture changed" in should_record_decision("The architecture changed to a worker queue."), "architecture decision threshold missed")
    assert_true(not should_record_decision("Ran tests and fixed a typo."), "non-decision text triggered decision threshold")
    return root


def test_mcp_trust_and_flow_metric() -> Path:
    root = temp_root("dev-session-mcp-metrics-")
    run([str(SETUP), "--root", str(root), "--mode", "write"])
    profile_path = root / ".dev-session" / "profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["ownership"]["workflow_owners"] = ["@org/dev-workflow-owners"]
    for lane in profile["ownership"]["lane_owners"]:
        profile["ownership"]["lane_owners"][lane] = ["@org/dev-workflow-owners"]
    profile["mcp_trust_catalog"] = [
        {
            "name": "github",
            "capabilities": "read-write-provider",
            "required_env_vars": ["GITHUB_TOKEN"],
            "safe_smoke_test": "list current repository metadata",
            "owner": "@org/dev-workflow-owners",
            "risk_level": "medium",
        }
    ]
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    doctor = run([str(WORKFLOW_DOCTOR), "--root", str(root)], check=False)
    assert_true("MCP trust catalog item" not in doctor.stdout, "workflow doctor warned on complete MCP trust item")

    metric = run([str(METRIC), "--root", str(root), "--kind", "setup_gap", "--note", "missing GitHub MCP auth"])
    metrics_path = root / ".dev-session" / "flow-metrics.jsonl"
    text = metrics_path.read_text(encoding="utf-8")
    assert_true("No developer names" in text, "flow metric privacy marker missing")
    assert_true("setup_gap" in metric.stdout, "flow metric command output missing kind")
    rejected = run([str(METRIC), "--root", str(root), "--kind", "setup_gap", "--note", "blocked by @alice"], check=False)
    assert_true(rejected.returncode != 0 and "must describe system friction" in rejected.stdout, "flow metric accepted personal identifier")
    return root


def test_make_agent_prompt() -> Path:
    root = temp_root("dev-session-prompt-")
    prompt = run(
        [
            str(PROMPT),
            "--role",
            "QA/Test",
            "--objective",
            "Verify the checkout flow",
            "--lane",
            "frontend",
            "--session-mode",
            "review",
            "--scope",
            "tests/",
        ]
    )
    assert_true("Role: QA/Test" in prompt.stdout, "prompt role missing")
    assert_true("Verify the checkout flow" in prompt.stdout, "prompt objective missing")
    assert_true("Session mode: review" in prompt.stdout, "prompt session mode missing")
    assert_true("Lane: frontend" in prompt.stdout, "prompt lane missing")
    assert_true("Provider state" not in prompt.stdout, "prompt has unexpected case-sensitive provider text")
    assert_true("do not post, assign, label, merge, deploy" in prompt.stdout, "provider mutation policy missing")
    bad = run([str(PROMPT), "--role", "CEO", "--objective", "Do things"], check=False)
    assert_true(bad.returncode != 0 and "--role must be one of" in bad.stdout, "bad role accepted")
    return root


def test_doctor_changed_only_and_allowlist() -> Path:
    root = temp_root("dev-session-doctor-secrets-")
    git(root, "init")
    run([str(NEW_DAY), "--root", str(root), "--date", "2026-05-28"])
    secret_path = root / ".dev-session" / "logs" / "2026-05-28.md"
    secret_path.write_text("token = sk-abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
    result = run([str(DOCTOR), "--root", str(root), "--changed-only", "--strict"], check=False)
    assert_true(result.returncode == 1 and "Secret scan" in result.stdout, "changed-only secret scan missed secret")
    secret_path.write_text(
        "token = sk-abcdefghijklmnopqrstuvwxyz123456 dev-session-secret-allow\n",
        encoding="utf-8",
    )
    allowed = run([str(DOCTOR), "--root", str(root), "--changed-only"], check=False)
    assert_true("Secret scan" not in allowed.stdout, "allowlisted secret line still warned")
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true", help="Keep temporary test projects.")
    args = parser.parse_args()

    tests = [
        test_full_flow,
        test_end_first,
        test_no_git_snapshot,
        test_invalid_inputs,
        test_doctor,
        test_doctor_malformed_state,
        test_update_session,
        test_no_git_update_session,
        test_detached_head_update_session,
        test_prune,
        test_setup_profile_and_context_pack,
        test_setup_profile_preserves_team_truth,
        test_workflow_doctor_ownership,
        test_workflow_doctor_solo,
        test_workflow_doctor_accepts_bom_profile,
        test_compose_pr,
        test_compose_pr_base_branch,
        test_verify,
        test_decision_thresholds_and_intake,
        test_mcp_trust_and_flow_metric,
        test_make_agent_prompt,
        test_doctor_changed_only_and_allowlist,
    ]
    roots: list[Path] = []
    try:
        for test in tests:
            root = test()
            roots.append(root)
            print(f"PASS {test.__name__}")
    except Exception as exc:
        print(f"FAIL {exc}")
        if args.keep:
            print("Kept temp roots:")
            for root in roots:
                print(root)
        return 1
    finally:
        if not args.keep:
            for root in roots:
                shutil.rmtree(root, ignore_errors=True)

    print("All dev-session self tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
