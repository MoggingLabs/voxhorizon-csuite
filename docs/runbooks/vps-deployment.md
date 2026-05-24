# Runbook: VPS deployment (plan of record)

Status: **ON HOLD (2026-05-25).** The build is complete and green; this is the
plan to bring it up on a VPS for real (no fakes) once compute is available.

## Why it is on hold: capacity

The current production VPS cannot host the C-Suite without risking production.
Measured 2026-05-25:

| Metric | Value |
|---|---|
| RAM total / free | 7.8 GiB / **173 MiB** |
| Swap | **2.0 / 2.0 GiB (100% used)** |
| Disk | 70G / 96G (27G free) |
| Running | 10 production containers |

The C-Suite "without fakes" footprint is ~20 containers (self-hosted Supabase
~12, Data Brain, 6 agents, dispatcher + socket-proxy, Mission Control) needing
~6-9 GB RAM. Bringing that up on the current box would trigger the OOM killer and
most likely take down the production worker/web and the live agents, which
violates the hard isolation rule (the C-Suite must never affect production).

**Do not run `bootstrap-csuite.sh` on the production box as-is.**

## Precondition to lift the hold

Compute headroom, one of:
- **Separate VPS (recommended)** ~16 GB for the C-Suite only. Strongest isolation,
  zero risk to production. This matches the original isolation goal.
- **Upgrade the current host** to ~16 GB, then deploy here with headroom.

(A local Docker Desktop smoke test is a separate, lighter path; it proves the
stack runs without fakes but is not the production deployment.)

## Inputs and what is already staged

| Input | State |
|---|---|
| Target host: Docker + compose, root/sudo, git, >= ~16 GB RAM, ~20 GB free disk | needed |
| `DATA_BRAIN_SRC` (business-data-brain-template) | available locally at `License-and-Scale/business-data-brain-template`; pass a path on the host or a git URL |
| Codex `auth.json` | staged at `/opt/voxhorizon-csuite/secrets/codex-auth.json` (current box). On a new host: `docker exec hermes-agent-ekko cat /opt/data/auth.json` into that path |
| `ingest.env` (V2 source creds) | staged at `/opt/voxhorizon-csuite/secrets/ingest.env`; GHL token + location id to be filled |
| `MC_AUTH_PASS`, `MC_AUTH_SECRET`, `CSUITE_DISPATCHER_SECRET` | generate and put in `csuite.env` at deploy |

`CODEX_AUTH_JSON_SRC` already points at the staged auth in `.env.csuite.example`.

## Pre-flight

1. Isolation sanity: deploy uses user `csuite`, root `/opt/voxhorizon-csuite`,
   network `csuite_net`, loopback ports, Supabase project `csuite-supabase`. It
   never touches `/opt/voxhorizon` or production containers/networks.
2. Capacity: `free -h` (multi-GB free + swap headroom), `df -h /` (~20 GB free).
3. Dry run (writes nothing): `DATA_BRAIN_SRC=<path|url> bash infra/bootstrap-csuite.sh --dry-run`.

## Deploy steps

1. **Get the repo on the host**: clone into `/opt/voxhorizon-csuite/repo` (or run
   bootstrap from any checkout; it copies its own scaffold files from the repo).
2. **Stage secrets** (new host only): place `codex-auth.json` and `ingest.env`
   under `/opt/voxhorizon-csuite/secrets/` (chmod 600).
3. **Bootstrap as root**:
   `DATA_BRAIN_SRC=<path|url> bash infra/bootstrap-csuite.sh`
   This: creates the `csuite` user/dirs/net; clones self-hosted Supabase and
   binds its ports to loopback; generates secrets and renders `csuite.env`;
   assembles the Data Brain build; applies migrations `0001/0002/0003`; sets the
   `csuite_readonly` password; brings up Supabase + Data Brain + the 6 agents;
   pushes agent profiles via `hermes/sync-csuite.sh`.
4. **Fill `csuite.env`** (`/home/csuite/.config/voxhorizon-csuite/csuite.env`):
   `MC_AUTH_PASS`, `MC_AUTH_SECRET`, `CSUITE_DISPATCHER_SECRET`.
5. **Re-sync agent profiles** after secrets:
   `bash hermes/sync-csuite.sh --apply --restart`.
6. **Patch agent config** per `hermes/config.csuite.patch.md` (scrub OpenRouter,
   provider `openai-codex`, wire the Data-Brain MCP, channels empty/passive).
7. **Dispatcher up**:
   `docker compose -p csuite --env-file <csuite.env> -f infra/docker-compose.dispatcher.yml up -d`
   (no `FAKE_DOCKER`, no `FAKE_STORE`).
8. **Mission Control up**:
   `docker compose -p csuite --env-file <csuite.env> -f infra/docker-compose.mc.yml up -d`.
9. **Ingest** (optional, after creds): ensure the worker's env includes the
   `ingest.env` values, then schedule the cron from `infra/docker-compose.ingest.yml`
   (`run --rm csuite-ingest`). Start with `audit_feed`, then `email_engagement`.
10. **Expose via Tailscale Serve** (private):
    `tailscale serve --bg --https=8443 http://127.0.0.1:3100` (Mission Control),
    `tailscale serve --bg --https=8543 http://127.0.0.1:8100` (Supabase API).
    Set `NEXT_PUBLIC_SUPABASE_URL` to the served URL and rebuild the Data Brain.

## Verification (the deploy-time unknowns to prove)

- Supabase healthy on loopback (Kong `127.0.0.1:8100`, Studio `127.0.0.1:8101`).
- Migrations applied; `csuite_readonly` exists.
- **Read-only role write-denied**: as `csuite_readonly`, an INSERT/UPDATE fails (C3).
- **RLS deny-all**: anon/PostgREST cannot read the C-Suite + ingest tables (C7).
- **Agents passive**: `docker inspect` shows the `sleep infinity` run contract
  (M4-1); kill one agent, the others stay up and it restarts (fault isolation).
- **Dispatcher scope**: bearer required; reaches only `csuite-hermes-*` via the
  proxy, exec only (C2/C11).
- **Real dispatch end to end**: from Mission Control, dispatch to `rex` -> real
  `hermes chat` via the Codex subscription -> SSE streams to a terminal state ->
  `dispatch` + `audit_log` rows persist (no fakes).
- **Ingest for real**: `audit_feed` writes rows; once GHL creds are set,
  `email_engagement` pulls campaigns.
- **No production impact**: prod containers unaffected; `free -h` healthy.

## Rollback

`docker compose -p csuite down` and `docker compose -p csuite-supabase down`;
optionally remove `/opt/voxhorizon-csuite`. None of this touches production.

## Post-deploy follow-ups

- Rotate the leaked prod `WORKER_SHARED_SECRET` (issue #7) — a separate
  production action, see `docs/runbooks/secret-rotation.md`.
- Optionally enable the repo Dependency graph to re-add `dependency-review`.
