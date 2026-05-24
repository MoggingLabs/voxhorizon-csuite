# Roadmap

The build is organized into eleven milestones (M0 through M10). Each milestone has
a goal and a Definition of Done. Issues are milestone-prefixed (`M0-1`, `M1-2`,
and so on) and tracked in this repo's GitHub milestones and issues. The detailed
acceptance criteria, tests, and security notes live on each issue.

Critical path: M0 -> M1 -> M2 -> M3 -> M4 -> M6 -> M5 -> M7. Observability (M8)
and security hardening (M9) run alongside from M6 onward. V2 (M10) is last.

## M0 Foundation and repo

Goal: stand up the private repo, conventions, CI skeleton, ADRs, and supply-chain
scanning; rotate the leaked production secret first.

Done when: docs set, `.github/`, and ADRs in; CI green on a lint pass; gitleaks,
dependabot, and CodeQL active (free on the public repo; dependency-review optional
once the Dependency graph is enabled); `WORKER_SHARED_SECRET` rotated on production
and absent here; the static isolation guard passes.

Issues: M0-1 repo + conventions; M0-2 docs skeleton; M0-3 the eight ADRs; M0-4
issue + PR templates (incl. security); M0-5 `ci.yml`; M0-6 supply-chain (gitleaks
+ dependabot + CodeQL); M0-7 rotate prod `WORKER_SHARED_SECRET` (first); M0-8
branch protection.

## M1 Isolation harness

Goal: prove the host, network, user, and port isolation before any container runs.

Done when: `csuite` user, `/opt/voxhorizon-csuite`, `csuite_net`, loopback ports
created by bootstrap; a repo-wide guard test asserts no production path,
container, or network reference and no OpenRouter or OpenAI key; bootstrap
`--dry-run` passes in CI.

Issues: M1-1 bootstrap isolation contract; M1-2 static isolation guard test.

## M2 Self-hosted data layer

Goal: self-hosted Supabase + the Data Brain up, migrations applied, $0.

Done when: Supabase healthy on loopback; Data Brain healthy on 127.0.0.1:3100;
`t01..t91` migrations applied; `csuite_readonly` SELECT-only role proven
write-denied; RLS deny-all baseline on C-Suite tables.

Issues: M2-1 self-hosted Supabase; M2-2 Data Brain build + migrations; M2-3
`csuite_readonly` role + RLS baseline.

## M3 Read MCP and visibility

Goal: the read-only bridge agents use, fully tested, with a documented visibility
map.

Done when: the MCP passes golden allow and deny evals; connects only as
`csuite_readonly`; row-cap, timeout, and read-only transaction verified; the
visibility matrix and the V2 gap register are documented.

Issues: M3-1 read MCP hardening + golden tests; M3-2 visibility matrix + gap
register.

## M4 Hermes agents (passive and isolated)

Goal: six passive, fault-isolated agent containers reachable only by dispatch.

Done when: all six up, passive, with per-container restart; the public-image
passive CMD-override contract confirmed; OpenRouter scrub verified; Codex
`auth.json` present per agent; the kill-one-survives test passes.

Issues: M4-1 confirm passive CMD-override; M4-2 per-agent config patch; M4-3 Codex
auth provisioning; M4-4 fault-isolation proof.

## M5 Mission Control

Goal: the Agents module: roster, dispatch UI, SSE stream, results history, auth
gate.

Done when: roster renders from config + live health; auth gate fail-closed;
dispatch streams over SSE and persists; vitest at or above 90 percent; Playwright
smoke green.

Issues: M5-1 Agents module + auth gate; M5-2 dispatch UI + SSE + history; M5-3
dispatch + audit tables.

## M6 Dispatcher (scoped socket)

Goal: a FastAPI dispatcher that execs agents through the scope-limited socket
proxy, streams SSE, and records to Supabase.

Done when: the dispatcher talks only to the proxy limited to exec on
`csuite-hermes-*`; bearer-authed; name allow-list enforced with argv (no shell);
pytest at or above 90 percent; the negative and abuse tests pass.

Issues: M6-1 dispatcher + scoped proxy; M6-2 dispatcher negative/abuse tests.

## M7 Per-agent rollout

Goal: Rex online, then each specialist verified end to end through Mission
Control.

Done when: Rex daily-brief and delegation work end to end; each specialist has a
SOUL and role doc and at least one MC-driven task with a golden-eval acceptance
and a passing owner-drives-agent e2e.

Issues: M7-1 Rex; M7-2 Dash; M7-3 Closer; M7-4 Vault; M7-5 Bob; M7-6 Pulse.

## M8 Observability

Goal: health, audit, logs, and alerting for every plane.

Done when: container health surfaced in MC; dispatch audit queryable; per-agent
stderr captured; uptime checks for MC and the dispatcher; alerts on crash-loop and
stuck dispatch.

Issues: M8-1 health + audit in MC; M8-2 stderr capture + retention; M8-3 uptime
checks; M8-4 crash-loop / stuck alerts.

## M9 Security hardening

Goal: close every control in the threat model with a proving test.

Done when: the SECURITY.md control-to-test matrix is 100 percent green; secret
scan and CodeQL clean; a restore drill succeeds.

Issues: M9-1 control matrix green; M9-2 prompt-injection guardrails; M9-3
secret-scan + CodeQL clean; M9-4 backup/restore drill.

## M10 V2 integrations and visibility gaps

Goal: add the missing data sources and the Recruiter agent.

Done when: ingest + tables for email engagement, support tickets, churn reasons,
content calendar, webinar metrics, NPS, and audit logs; the Recruiter (Hunter)
agent added behind the same passive, isolated, read-only pattern; each new source
tested with a fake double.

Issues: M10-1..M10-7 the seven gaps; M10-8 Recruiter agent.
