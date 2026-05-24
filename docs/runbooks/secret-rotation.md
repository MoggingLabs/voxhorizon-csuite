# Runbook: secret rotation

## Production WORKER_SHARED_SECRET (do this first, separate stack)

The research flagged a leaked production `WORKER_SHARED_SECRET`. Rotate on the
production stack (this is the one production write we make, with the owner's
go-ahead):

1. Generate: `python -c "import secrets; print(secrets.token_hex(64))"`.
2. SSH to the VPS, edit `/opt/voxhorizon/.env`, set the new value.
3. Roll both consumers: `docker compose -f /opt/voxhorizon/docker-compose.yml up -d worker` and the operator container.
4. Smoke test: `curl https://dashboard.voxhorizon.com/api/health` returns 200.

It must never appear in this repo (`sec_no_worker_shared_secret_in_repo`).

## C-Suite runtime secrets

In `/home/csuite/.config/voxhorizon-csuite/csuite.env` (chmod 600):

- `MC_AUTH_PASS` / `MC_AUTH_SECRET`, `CSUITE_DISPATCHER_SECRET`: regenerate
  (`token_hex`), edit the file, roll Mission Control + the dispatcher.
- Supabase keys (`POSTGRES_PASSWORD`, `JWT_SECRET`, derived anon/service): rotate
  by re-running the relevant bootstrap step and rolling the Supabase + Data Brain
  containers; anon/service are derived from `JWT_SECRET`.
- `csuite_readonly` DSN: rotate the role password (`ALTER ROLE`), update the DSN,
  roll the MCP-using agents.

## Codex auth.json

If the ChatGPT/Codex OAuth expires, redo the Codex login, replace the source file
that `CODEX_AUTH_JSON_SRC` points at, and re-run
`hermes/sync-csuite.sh --apply --restart`. Never commit or log it.
