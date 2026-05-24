# ADR 0009: Mission Control as a self-contained service

- Status: Accepted
- Date: 2026-05-24
- Refines: ADR 0002

## Context

ADR 0002 set Mission Control as the only interface and sketched it as an "Agents
module" on the Data Brain Next.js app. In practice the Data Brain app is external
to this repo (pulled via `DATA_BRAIN_SRC` at deploy), so there is no in-repo
Next.js app to extend, and the agents read the database through the read-only MCP
rather than through the Data Brain app. A separate, self-contained Mission Control
is simpler to build, test, and isolate.

## Decision

Implement Mission Control as a self-contained FastAPI service in
`apps/mission-control`, the same reliable, fully CI-testable pattern as the
dispatcher. It is the sole interface (no Telegram, no Slack, per ADR 0002): a
single-operator auth gate, an agent roster, a dispatch surface that proxies to the
dispatcher and streams output, and a history view that reads Supabase. The Data
Brain Next.js dashboard remains an optional, separate human BI view; the database
is the shared source of truth.

## Consequences

Mission Control is built and verified in CI without a Node toolchain, and stays
isolated (loopback, reached via Tailscale Serve). ADR 0002's "Mission Control is
the only interface" holds. The Data Brain app is decoupled from the agent
interface. If a unified Next.js dashboard is wanted later, it can embed or link
this service.
