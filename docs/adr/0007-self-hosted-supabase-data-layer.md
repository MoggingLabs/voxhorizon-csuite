# ADR 0007: Self-hosted Supabase data layer

- Status: Accepted
- Date: 2026-05-23

## Context

The C-Suite Data Brain must be isolated from production data. The VoxHorizon
Supabase org is at its two free-project limit (the live control panel and a
populated campaign-data project), and the owner does not want a paid plan. A new
cloud project is therefore not available for free.

## Decision

Self-host Supabase on the VPS as its own compose project (`csuite-supabase`,
loopback ports), at $0. The Data Brain runs against it. Agents read it through the
read-only MCP (ADR 0006).

## Consequences

Full isolation from production data with no plan change. We run the official
self-hosted Supabase stack (Postgres, PostgREST, Auth, Realtime, Storage), heavier
on the box but acceptable. Browser-facing Supabase URL is exposed via Tailscale
Serve, not publicly.
