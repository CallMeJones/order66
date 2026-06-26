# Agent guide for this repository

This repository is not a normal application codebase. It is a collection of Claude Code agent skills and supporting scripts.

## What this repo contains

- `Order66/` — a multi-perspective code audit skill. It is a review lens, not a feature implementation. Use it when you want the agent to evaluate code changes from adversarial, operational, maintainer, integrator, and tooling perspectives.
- `dev-session/` — a disciplined development session skill. It orchestrates intake, proof/evidence commands, handoff notes, and workflow checks for a development task.
- `README.md` — the main overview and installation guidance for these skills.

## Key conventions

- Each skill lives in its own directory and follows the pattern:
  - `SKILL.md` — the lean instructions the agent reads first
  - `references/` — deeper documentation opened only when needed
  - `scripts/` — executable helpers for the skill
  - `assets/` — optional templates used by the skill
- Preserve this structure when editing or extending the repo. Keep `SKILL.md` concise and link to deeper material in `references/`.
- The frontmatter in `SKILL.md` matters: it is used by the runtime to select and describe the skill.
- The scripts are plain Python and assume Python 3 is available on `PATH`.

## How to use these skills

- For audit work, use `Order66` as a review lens. It is designed to review code changes, surface risks, and avoid confirmation bias.
- For development sessions, use `dev-session` to manage a Claude-first workflow, run evidence commands, and compose handoffs.
- `dev-session/scripts/verify.py` is the main verification entry point for proving lane evidence.

## What an AI agent should do here

- Treat this repo as a skills repository, not a product-service codebase.
- When asked "what does this skill do?", explain the skill's intent and how it is structured rather than describing a user-facing application feature.
- Do not add unrelated runtime code at the root. New work should normally extend or adjust the existing skill directories and their references.
- If you add a new skill, follow the same package pattern and keep documentation minimal in `SKILL.md`, with details in `references/`.

## Useful entry points

- `README.md` — repo overview and install guidance
- `Order66/SKILL.md` — audit skill instructions
- `dev-session/SKILL.md` — session skill instructions
- `dev-session/references/` — detailed workflow and dev-session playbooks

This `AGENTS.md` file helps AI coding agents understand the repo's purpose and avoid treating it like a standard app repository.