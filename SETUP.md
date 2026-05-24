# Setup

How to stand up the C-Suite on the VPS, isolated from production. Everything runs
under a dedicated `csuite` user in `/opt/voxhorizon-csuite`. The production stack
is never touched.

## Prerequisites

- The existing Hostinger VPS (Ubuntu 24.04) with Docker installed.
- A ChatGPT/Codex subscription login to produce the `auth.json` the agents use.
- `gh` and `git` for repo operations from your workstation.
- Tailscale on the VPS (the C-Suite is private; reached over Tailscale Serve).

## One-time bootstrap (on the VPS, as root)

1. Rotate the leaked production `WORKER_SHARED_SECRET` first (see
   [docs/runbooks/secret-rotation.md](docs/runbooks/secret-rotation.md)). This is
   a production action and is separate from this stack.
2. Place this repo at `/opt/voxhorizon-csuite/repo`.
3. Export `DATA_BRAIN_SRC` as the `business-data-brain-template` source (a local
   path or a git URL). The bootstrap copies or clones it to build the Data Brain.
4. Run the isolated bootstrap:
   ```
   cd /opt/voxhorizon-csuite/repo/infra
   sudo DATA_BRAIN_SRC=<path-or-git-url> ./bootstrap-csuite.sh
   ```
   It creates the `csuite` user, self-hosts Supabase (with published ports bound
   to 127.0.0.1), builds the Data Brain, applies the warehouse + C-Suite
   migrations (incl. the SELECT-only `csuite_readonly` role from
   `db/migrations/0001`), scaffolds each agent data dir, and brings up the passive
   agent containers. It refuses to run against `/opt/voxhorizon`. Use
   `--dry-run` to print the plan without writing anything.
5. Fill `/home/csuite/.config/voxhorizon-csuite/csuite.env`: `MC_AUTH_PASS`,
   `MC_AUTH_SECRET`, `CSUITE_DISPATCHER_SECRET`.
6. Provide the Codex `auth.json` once and point `CODEX_AUTH_JSON_SRC` at it, then
   push the agent profiles:
   ```
   bash /opt/voxhorizon-csuite/repo/hermes/sync-csuite.sh --apply --restart
   ```
7. Apply the Data Brain migrations:
   ```
   sudo /opt/voxhorizon-csuite/repo/infra/bootstrap-csuite.sh migrate
   ```
8. Bring up the dispatcher + scoped socket proxy:
   ```
   docker compose -p csuite --env-file /home/csuite/.config/voxhorizon-csuite/csuite.env \
     -f /opt/voxhorizon-csuite/repo/infra/docker-compose.dispatcher.yml up -d
   ```

## Expose Mission Control (private)

```
tailscale serve --bg --https=8443 http://127.0.0.1:3100   # Mission Control
tailscale serve --bg --https=8543 http://127.0.0.1:8100   # Supabase API (if needed)
```

Then set `NEXT_PUBLIC_SUPABASE_URL` in `csuite.env` to the Supabase https URL and
rebuild the Data Brain image.

## Verify

- Mission Control loads over Tailscale and the agent roster shows live status.
- Dispatch a task to Rex; output streams and a dispatch + audit row appear.
- `docker ps` shows `csuite-hermes-*` passive and `restart: unless-stopped`.
- `grep -i openrouter` across the agent configs returns nothing.

## Ports (loopback only)

Mission Control 3100, dispatcher 8200 (internal), Supabase API 8100, Supabase
Studio 8101. No public ports; production Caddy owns 80/443.
