# Hermes `config.yaml` deltas for C-Suite agents

Hermes owns the base `config.yaml` (it generates one per agent, `_config_version`
23). We do not author it from scratch; we apply these deltas, the same way
production applies `infra/hermes/config.yaml.patch`. Apply per agent in its
`agents/<name>/data/config.yaml`.

## 1. Model: OpenAI via Codex subscription, OpenRouter scrubbed

Set the `model:` block to exactly this (note: **no `base_url`**):

```yaml
model:
  default: gpt-5.5
  provider: openai-codex
providers: {}
fallback_providers: []
```

**Remove** the OpenRouter remnants that ship in the stock/production config:
- Delete the line `  base_url: https://openrouter.ai/api/v1` under `model:`.
- Delete the whole top-level `openrouter:` block, e.g.:
  ```yaml
  openrouter:
    response_cache: true
    response_cache_ttl: 300
    min_coding_score: 0.65
  ```

Auth is the Codex/ChatGPT OAuth token in `auth.json` at `$HERMES_HOME`
(`/opt/data/auth.json`). There is no `OPENAI_API_KEY` and no OpenRouter key.

Sanity check after sync: `grep -i openrouter config.yaml` must return nothing.

## 2. MCP servers: the Data-Brain reader (drop the ad-pipeline one)

Replace the production `mcp_servers.pipeline-operator` (ad pipeline, and it
carries a secret) with our read-only Data-Brain server:

```yaml
mcp_servers:
  csuite-data-brain:
    timeout: 120
    connect_timeout: 30
    command: /opt/hermes/.venv/bin/python
    args:
      - /opt/data/skills/data-brain-mcp/mcp_server.py
    env:
      CSUITE_DB_DSN: ${CSUITE_DB_DSN}
```

Do NOT copy `WORKER_SHARED_SECRET` or any production MCP env into C-Suite configs.

## 3. Channels: none (Mission Control only)

No Telegram, Slack, or Discord. The agents are passive (no listening gateway);
Mission Control's dispatcher drives them via `docker exec ... hermes chat`. Leave
the channel blocks empty:

```yaml
telegram: {}
slack: {}
discord: {}
```

## 4. Orchestration (Rex, the COO/manager only)

Rex needs delegation + kanban to dispatch to the specialists:

```yaml
delegation:
  orchestrator_enabled: true
  max_concurrent_children: 3
  max_spawn_depth: 1
  inherit_mcp_toolsets: true
kanban:
  dispatch_in_gateway: true
  dispatch_interval_seconds: 60
  auto_decompose: true
```

Specialist agents (Dash, Closer, Vault, Bob, Pulse) keep delegation
`orchestrator_enabled: false` for V1: they execute, Rex routes.

## 5. Approvals + plugins

Keep `approvals.mode: manual` (Hermes default) so money/irreversible tool calls
pause for the owner. Do NOT enable the production `voxhorizon-approvals` plugin
(it is the ad-pipeline launch gate). Leave `plugins.enabled: []` for V1.

## 6. Per-agent identity

`SOUL.md` is the persona (see `agents/<name>/SOUL.md`). Set `display.personality`
to a neutral value (e.g. `concise`); do not ship the stock `kawaii` default for a
business agent.
