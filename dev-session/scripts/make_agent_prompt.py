#!/usr/bin/env python3
"""Generate a scoped role/subagent prompt for a dev session."""

from __future__ import annotations

import argparse

from dev_session_common import LANE_NAMES, ROLE_NAMES, SESSION_MODES, evidence_contract, load_asset, load_profile, render_template, require_existing_root


FALLBACK_TEMPLATE = """\
Role: {role}
Objective: {objective}
Session mode: {session_mode}
Lane: {lane}
Context: {context}
Scope: {scope}
Constraints:
{constraints}
Expected output:
{outputs}
"""

DEFAULT_CONSTRAINTS = [
    "You are not alone in the codebase.",
    "Do not revert or overwrite unrelated user/agent changes.",
    "Keep work within the assigned scope.",
]

DEFAULT_OUTPUTS = [
    "Summary",
    "Files inspected/changed",
    "Commands run",
    "Findings or implementation notes",
    "Risks",
    "Recommended next action",
]


def bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, help="Role name.")
    parser.add_argument("--objective", required=True, help="Specific task objective.")
    parser.add_argument("--root", default=".", help="Project root for profile/evidence context.")
    parser.add_argument("--lane", choices=sorted(LANE_NAMES), help="Work lane for evidence expectations.")
    parser.add_argument("--session-mode", choices=sorted(SESSION_MODES), help="Session mode.")
    parser.add_argument("--context", default="", help="Only necessary project/session context.")
    parser.add_argument("--scope", default="", help="Read-only areas or owned write files/modules.")
    parser.add_argument("--constraint", action="append", default=[], help="Additional constraint. May be repeated.")
    parser.add_argument("--output", action="append", default=[], help="Expected output item. May be repeated.")
    args = parser.parse_args()

    role = args.role
    if role not in ROLE_NAMES:
        known = ", ".join(sorted(ROLE_NAMES))
        parser.error(f"--role must be one of: {known}")

    root = require_existing_root(parser, args.root)
    profile = load_profile(root)
    extra_constraints = [
        *args.constraint,
        "Read and prepare provider state freely, but do not post, assign, label, merge, deploy, or alter provider settings without explicit user confirmation.",
    ]
    if args.lane:
        extra_constraints.append(f"Evidence contract for {args.lane}: {'; '.join(evidence_contract(profile, args.lane))}")

    template = load_asset("agent-prompt-template.md", FALLBACK_TEMPLATE)
    prompt = render_template(
        template,
        {
            "role": role,
            "objective": args.objective,
            "session_mode": args.session_mode or "(unspecified)",
            "lane": args.lane or "(unspecified)",
            "context": args.context or "(none provided)",
            "scope": args.scope or "(not specified)",
            "constraints": bullet([*DEFAULT_CONSTRAINTS, *extra_constraints]),
            "outputs": bullet(args.output or DEFAULT_OUTPUTS),
        },
    )
    print(prompt, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
