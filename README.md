# Vox Horizon C-Suite

A team of AI agents that runs Vox Horizon's agency operations and can see
everything about the business, isolated from the live ad pipeline, on the proven
Hermes runtime, driven through a single Mission Control interface.

This repo is the plan of record and the build. It is private and security-first.
Start with [ARCHITECTURE.md](ARCHITECTURE.md), then [SECURITY.md](SECURITY.md),
then [ROADMAP.md](ROADMAP.md). To stand it up, follow [SETUP.md](SETUP.md).

## What this is

Six role agents, each its own isolated container, coordinated by a COO agent and
operated from one dashboard:

| Agent | Role | Sees / does (V1, read-only) |
|---|---|---|
| Rex | COO / orchestrator | Files the daily plan, delegates tasks, escalates to the owner |
| Dash | Data & knowledge | Daily KPI narrative, meeting intel, the cited source of truth |
| Closer | Sales | Follow-up drafts, call scoring, pipeline integrity |
| Vault | Finance | Runway, margin, red flags (strictly read-only) |
| Bob | Marketing | Ad efficiency, content, funnel performance |
| Pulse | Client success | Churn early warning, post-call summaries |

V1 agents are read-only: they see everything, have no write or action tools, and
any irreversible action is a manual approval gate. This is a deliberate security
posture, not a limitation of the design.

## Architecture in one picture

```
You -> Mission Control (the only interface)
          |  bearer
          v
     csuite-dispatcher  ->  docker-socket-proxy (EXEC only, csuite-hermes-*)
          |                        | docker exec ... hermes chat -q
          |  SSE + writes results   v
          v               csuite-hermes-{rex,dash,closer,vault,bob,pulse}
     Supabase (Data Brain) <- read-only MCP   (own container, PASSIVE, isolated)
          ^
   dashboard renders state + history
```

The container boundary plus per-container restart gives fault isolation: one
agent crashing or hanging never affects the others. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the full design and
[docs/adr/](docs/adr/) for the locked decisions.

## Isolation (hard constraint)

Nothing here shares a user, network, port, database, or secret with the live ad
pipeline. Dedicated `csuite` Linux user, `/opt/voxhorizon-csuite`, `csuite_net`,
loopback-only ports. The production stack is read-only reference and is never
modified by this repo.

## Repo structure

```
README SETUP SECRETS ARCHITECTURE SECURITY ROADMAP CONTRIBUTING CODEOWNERS LICENSE
.github/        issue + PR templates, CI + supply-chain workflows, dependabot
docs/adr/       the locked architecture decisions (ADRs)
docs/runbooks/  secret rotation, incident response, add-an-agent, restore
db/             SCHEMA.md (read surface) + forward-only migrations (dispatch + audit)
apps/           mission-control (Agents module) + csuite-dispatcher (FastAPI)
hermes/         agent profiles (SOUL), the read-only Data Brain MCP, the sync script
infra/          compose files, the Data Brain Dockerfile, bootstrap, env example
tests/          e2e (owner drives an agent), security (control proofs), golden evals
```

## Status

M0 (Foundation) is complete and merged: the docs set, ADRs, CI, supply-chain
scanning, the moved scaffold, branch protection, and the full backlog (11
milestones, 46 issues). The one open M0 item is the production secret rotation
(#7), held for an explicit go-ahead. M1 (Isolation harness) is next. The full
plan and progress live in [ROADMAP.md](ROADMAP.md) and the repo's milestones and
issues.

## Conventions

Conventional Commits, one branch per issue, PRs reference the issue they close, no
AI or assistant attribution, no em dashes. See [CONTRIBUTING.md](CONTRIBUTING.md).
