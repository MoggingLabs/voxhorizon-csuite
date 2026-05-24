# ADR 0008: Isolation by dedicated user, network, and ports

- Status: Accepted
- Date: 2026-05-23

## Context

The C-Suite runs on the same VPS as the production ad pipeline. A hard constraint
is that it must share nothing with production and never modify it.

## Decision

Run the C-Suite under a dedicated `csuite` Linux user, in `/opt/voxhorizon-csuite`
and `/home/csuite`, on a dedicated `csuite_net` Docker network plus the Supabase
project network, with loopback-only host ports (3100 / 8200 / 8100 / 8101). Never
join `voxhorizon_default` or `hermes-agent-ekko_default`. The bootstrap refuses to
run against `/opt/voxhorizon`. Build only from the License-and-Scale repos;
production is read-only reference.

## Consequences

The two stacks cannot cross-contaminate at the user, filesystem, network, or port
level. A static isolation guard test and bootstrap refusal enforce it (C1). Public
exposure is via Tailscale Serve only; production Caddy keeps 80/443.
