# Architecture

This document is the locked design for the Vox Horizon C-Suite. Decisions here are
captured as ADRs in [docs/adr/](docs/adr/) and must not be re-litigated without a
new ADR.

## Goal and scope

Give the owner a single place (Mission Control) to direct a team of AI agents that
read the entire business and produce briefs, analyses, and drafts. V1 is
read-only and human-gated. The system is fully isolated from the production ad
pipeline.

Non-goals (V1): no autonomous writes to business systems, no Telegram or Slack,
no multi-tenant, no public exposure, no auto-deploy to production.

## The four planes

```
You -> Mission Control (Agents module on the Data Brain Next.js app, the only UI)
          |  bearer: CSUITE_DISPATCHER_SECRET
          v
     csuite-dispatcher (FastAPI)  ->  docker-socket-proxy (EXEC only, csuite-hermes-*)
          |                                   | docker exec ... hermes chat -q
          |  SSE stream + writes results       v
          v                          csuite-hermes-{rex,dash,closer,vault,bob,pulse}
     Supabase (Data Brain) <- read-only MCP --   (own container, PASSIVE, isolated)
          ^
   dashboard renders state + history (Realtime)
```

### 1. Mission Control (interface)

An "Agents" module added to the existing Data Brain Next.js + Supabase app. It is
the only interface. It shows the agent roster and live status, a per-agent
dispatch surface that streams output over SSE, a task board where Rex files the
daily plan, and the history of every dispatch. Single-operator auth gate,
fail-closed. Reached privately over Tailscale Serve.

### 2. Dispatcher (control)

`csuite-dispatcher`, a small FastAPI service. It receives a task for an agent from
Mission Control (bearer-authed, constant-time compare), validates the agent name
against a strict allow-list, and runs `docker exec csuite-hermes-<name> hermes
chat -q ...` using an argv array (never a shell string). It streams the agent
output back as SSE and records the dispatch and its result to Supabase. It does
not hold the Docker socket directly.

### 3. Agents (work)

Six Hermes agents, each its own container from the public
`ghcr.io/hostinger/hvps-hermes-agent` image. Each is passive (`sleep infinity`,
the live operator pattern) and fault-isolated (`restart: unless-stopped`); a crash
or hang in one never touches the others. Agents have no channel (no Telegram or
Slack). They read business truth only through the read-only Data Brain MCP. The
model is OpenAI via the ChatGPT/Codex OAuth subscription only (`provider:
openai-codex`, `gpt-5.5`, `auth.json`); no OpenRouter, no API key.

### 4. Data (truth)

Self-hosted Supabase (its own project on the VPS, $0) hosting the Data Brain
warehouse (tables `t01..t91`). Agents read it via a SELECT-only Postgres role
through the Data Brain MCP. The dispatcher writes only the dispatch and audit
tables, behind RLS deny-all with service-role writes.

## The Docker socket, scoped

The dispatcher reaches the Docker daemon only through
`tecnativa/docker-socket-proxy` configured with `EXEC=1` and every other verb `0`.
The proxy holds the real socket; the dispatcher holds nothing. The dispatcher also
validates the target against `^csuite-hermes-(rex|dash|closer|vault|bob|pulse)$`
before any exec. This is the production-recommended hardening applied from day one.

## Dispatch sequence

1. Owner picks an agent in Mission Control and submits a task.
2. Mission Control calls the dispatcher with the bearer.
3. The dispatcher validates the name, writes a `dispatch` row (status running) and
   an `audit_log` row, then execs `hermes chat -q` in the target container via the
   scoped proxy.
4. Agent output streams back as SSE to the dashboard and is persisted.
5. The dispatcher marks the dispatch done with a result reference.

## Visibility and integrations (read-only)

Agents see the whole business through the Data Brain, which already ingests around
twenty sources. The mapping of source to table is the read surface documented in
[db/SCHEMA.md](db/SCHEMA.md):

| Source | Sees | Table(s) |
|---|---|---|
| Meta Ads | spend, ROAS, CPL | t02 |
| GoHighLevel | leads, stages | t01 |
| Calendly | bookings, no-shows | t03, t04 |
| Typeform | applications | merged into t01 |
| Grain + Fathom | call transcripts | t17 |
| Whop / Fanbasis / Stripe | payments, cash | t06 |
| Mercury | bank, expenses | t07 |
| Monday | client roster | t09 |
| Slack | EOD, new clients, payments | t05, t08, t19, t20 |
| YouTube / IG / X / LinkedIn / ManyChat | content | t11-t15 |
| Claude scoring | lead quality | t10 |
| Projections / weekly cache | targets, themes | t21, t91 |

Where a live lookup beats the daily snapshot, agents may use the read-only MCP
servers available in the environment: Fathom, Meta Ads, ClickUp, Gmail, Google
Calendar, Google Drive, Supabase, Vercel. V2 visibility gaps are tracked in M10:
email engagement, support tickets, churn reasons, content calendar, webinar
metrics, NPS, audit-log ingest.

## Isolation model

| Concern | Production (untouched) | C-Suite |
|---|---|---|
| User | agents, deploy | csuite |
| Dirs | /opt/voxhorizon, /docker/hermes-* | /opt/voxhorizon-csuite, /home/csuite |
| Network | voxhorizon_default, hermes-agent-ekko_default | csuite_net + the Supabase net |
| Ports | 80/443/3000/8000 | loopback 3100/8200/8100/8101 |
| Data | cloud Supabase | self-hosted Supabase |
| Model auth | (prod auth.json) | own Codex auth.json |

## ADR index

- 0001 Runtime: Hermes, not OpenClaw
- 0002 Interface: Mission Control only
- 0003 Model: Codex OAuth subscription, no OpenRouter
- 0004 Passive, fault-isolated agents
- 0005 Scoped Docker socket proxy
- 0006 Read-only Data Brain MCP
- 0007 Self-hosted Supabase data layer
- 0008 Isolation: csuite user, network, ports
