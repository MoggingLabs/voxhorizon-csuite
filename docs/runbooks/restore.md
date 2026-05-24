# Runbook: restore from backup

## What is backed up

- `sync-csuite.sh` backs up each agent's repo-owned surface (SOUL + MCP skill)
  to `/opt/voxhorizon-csuite/backups/` before each apply.
- The self-hosted Supabase Postgres holds the Data Brain + the C-Suite dispatch
  and audit tables. Take regular `pg_dump` snapshots of the `csuite-supabase` db.
- `csuite.env` and the Codex `auth.json` live only on the VPS (chmod 600) and in
  your offline vault. They are not in git.

## Restore the agent profiles

1. Identify the backup tarball under `/opt/voxhorizon-csuite/backups/`.
2. Extract into the agent data dir, or simply re-run
   `hermes/sync-csuite.sh --apply --restart` from the repo (the repo is the source
   of truth for SOUL + skills).

## Restore the database

1. Bring up the self-hosted Supabase stack.
2. `pg_restore` (or `psql`) the latest dump into the `csuite-supabase` Postgres.
3. Recreate the `csuite_readonly` role if needed (bootstrap step 11).
4. Re-apply any migrations newer than the dump.

## Restore secrets

1. Recreate `csuite.env` from the vault (or re-run bootstrap step 5 to regenerate
   Supabase secrets, which also rewrites the Supabase stack `.env`).
2. Replace the Codex `auth.json` from the vault and re-sync.

## Drill

M9-4 requires a restore drill: take a backup, tear down the agent data dirs,
restore via `sync-csuite.sh`, and confirm an agent dispatch still works end to end.
