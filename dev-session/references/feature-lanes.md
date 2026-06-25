# Feature Lanes And Evidence Contracts

Use lane contracts to decide what proof is needed before handoff or PR/MR composition.

## Frontend

- Run focused UI/unit checks where available.
- Smoke the changed browser flow.
- Capture screenshot or accessibility evidence when visual behavior changes.

## Backend

- Run focused tests for changed behavior.
- Prove migration or data-shape safety when storage changes.
- Prove API contract behavior for public or cross-service interfaces.

## MCP

- Verify the server/tool schema loads.
- Call at least one safe read-only tool through the intended client when possible.
- Record auth, approval, and tool-safety limits.

## Agentic

- Run an eval, trace, fixture, or replay for the changed agent path.
- Check tool permission boundaries and prompt-injection exposure.
- Record fallback and recovery behavior.

## IoT

- Run simulator, bench, or device smoke when available.
- Record firmware/hardware version and connection path.
- Capture safe rollback or recovery instructions.

## Ops/Security

- Run relevant config, secret, auth, deployment, or policy checks.
- Record rollback, monitoring, and alerting evidence.
- Confirm no secrets or sensitive data were added to durable logs.

## Docs/Product

- Identify audience and source-of-truth status.
- Verify examples, links, commands, and screenshots where applicable.
- Record review owner or product decision needed before publishing.
