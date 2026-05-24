# Runbook: observability

## What you can see

- Mission Control `GET /api/health-summary`: each agent's latest dispatch status.
- Mission Control `GET /api/history`: recent dispatches + the audit log (every
  dispatch and rejection writes an audit row, control C10).
- `GET /health` on Mission Control and the dispatcher for liveness.
- Per-agent container logs: `docker logs csuite-hermes-<name>` (the dispatcher's
  exec output is also captured in the dispatch result).

## Log retention

Containers log to stdout/stderr; configure the Docker daemon's `json-file` driver
with rotation (`max-size`, `max-file`) on the VPS, or ship to a collector. The MCP
and dispatcher redact secrets and never log credentials.

## Uptime checks (free)

Add Healthchecks.io monitors (no API key needed) for:
- Mission Control `https://<tailscale-host>/health`
- the dispatcher `/health` (loopback; check from the host)
- the self-hosted Supabase Kong `/health`

Store the ping URLs on the VPS only (treat like secrets), not in git.

## Crash-loop and stuck dispatch

- A crash-looping agent restarts on its own (`restart: unless-stopped`) and does
  not affect the others; investigate with `docker logs` and re-sync.
- A dispatch that never finishes is visible in `/api/history` with status
  `running` and an old `created_at`. The deploy-time watchdog (cron) marks a
  dispatch stuck past its timeout and alerts; until that is wired, the history
  view surfaces stuck rows for the operator.
