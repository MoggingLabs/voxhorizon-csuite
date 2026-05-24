# ADR 0005: Dispatch through a scope-limited Docker socket proxy

- Status: Accepted
- Date: 2026-05-23

## Context

Driving passive agents means running `docker exec ... hermes chat` from a
dispatcher. A raw Docker socket is root-equivalent on the host, which also runs
production. The production SECRETS doc itself recommends a scoped
`tecnativa/docker-socket-proxy` as the hardening for exactly this.

## Decision

The `csuite-dispatcher` never holds the raw socket. It talks to
`tecnativa/docker-socket-proxy` configured with `EXEC=1` and every other verb `0`.
The dispatcher validates the target against
`^csuite-hermes-(rex|dash|closer|vault|bob|pulse)$` and execs with an argv array,
never a shell string. It is bearer-authed with a constant-time compare and bound
to loopback.

## Consequences

A compromised dispatcher can only exec into the allow-listed agent containers, not
manage the daemon or touch production. Negative tests prove foreign containers,
non-exec verbs, and shell injection are all rejected (C2). Adds one small proxy
container to the stack.
