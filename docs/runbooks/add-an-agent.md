# Runbook: add an agent

Adding a new C-Suite agent (for example the Recruiter, M10-8) follows the same
passive, isolated, read-only pattern as the rest.

1. Author `hermes/agents/<name>/SOUL.md` (persona, what it sees, never-do list,
   no em dashes). Add any role doc it reads.
2. Add the agent name to the dispatcher allow-list regex and to the Mission
   Control roster config.
3. Add a service to `infra/docker-compose.hermes.yml` using the shared anchor
   (passive, `restart: unless-stopped`, own data dir volume, `csuite_net`).
4. Add the agent to `hermes/sync-csuite.sh`'s agent list so its SOUL + the MCP
   skill + `auth.json` get pushed.
5. Bring it up: `docker compose -p csuite -f infra/docker-compose.hermes.yml up -d
   csuite-hermes-<name>` then `hermes/sync-csuite.sh --apply --restart --agent <name>`.
6. Patch its `config.yaml` per `hermes/config.csuite.patch.md` (scrub OpenRouter,
   provider openai-codex, wire the read MCP, channels empty).
7. Add an owner-drives-agent e2e and a golden eval for its flagship output.

The agent is read-only by default. Any write capability is a separate, gated
decision with its own ADR.
