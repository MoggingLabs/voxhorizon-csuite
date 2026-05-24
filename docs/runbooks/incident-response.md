# Runbook: incident response

## An agent is crash-looping

1. `docker ps -a --filter name=csuite-hermes-` to see status.
2. Check its data dir stderr / `docker logs csuite-hermes-<name>`.
3. The other agents are unaffected (separate containers). Fix or pause the one
   agent: `docker pause csuite-hermes-<name>` while investigating.
4. Common causes: missing/expired `auth.json`, a bad `config.yaml` patch, MCP DSN
   wrong. Re-sync with `hermes/sync-csuite.sh --apply --restart`.

## A dispatch is stuck

1. The dispatcher records each dispatch with a status and timeout. Find the stuck
   row in the `dispatch` table.
2. The stuck dispatch is timed out and recorded (M8). It does not block dispatch
   to other agents.
3. If the target container is hung, restart just it.

## Suspected secret leak

1. Identify the secret and scope. Run the gitleaks scan locally.
2. Rotate at source per [secret-rotation.md](secret-rotation.md), highest blast
   radius first.
3. Roll the affected containers, smoke test, record in an issue.

## Suspected isolation breach (touching production)

1. Stop the C-Suite stack: `docker compose -p csuite down`.
2. Confirm production containers and networks are intact (`docker ps`,
   `docker network ls`).
3. Run the static isolation guard test; find and fix the offending reference;
   re-deploy only after it passes.
