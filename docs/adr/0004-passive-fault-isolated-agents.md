# ADR 0004: Agents are passive and fault-isolated

- Status: Accepted
- Date: 2026-05-23

## Context

The owner requires that if one agent goes down the others are unaffected. A single
container running many roles (in-process delegation) is one failure domain, and
ports-in-one-container shares that domain. Live inspection showed the operator
runs passive (`Cmd: sleep infinity`) and is dispatched via `docker exec`. The
Hermes image is ~9.94 GB but shared across containers, so separate containers cost
little extra disk.

## Decision

Each agent is its own container, passive (`sleep infinity`), with
`restart: unless-stopped`. Fault isolation comes from the container boundary, not
ports. Agents are reached only by the dispatcher.

## Consequences

A crash or hang in one agent never affects the others; Docker restarts just that
one. Idle agents use near-zero RAM. Cross-container orchestration cannot use
Hermes in-process delegation, so it goes through the dispatcher (ADR 0005). Storage
cost of six containers is negligible because the image is shared.
