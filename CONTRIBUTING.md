# Contributing

This repo mirrors the production team's conventions so the C-Suite build stays
consistent with the rest of Vox Horizon's engineering.

## Workflow

- One branch per issue: `<type>/<milestone>-<slug>`, for example
  `feat/m5-2-dispatch-sse` or `chore/m0-foundation`.
- Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
- Open a PR that references the issue it closes: `Closes #N`.
- No AI or assistant attribution anywhere in commits or PR bodies.
- No em dashes in any file, commit, or PR. Use commas, periods, or line breaks.
- Commit via a message file, not inline, to keep messages clean.
- `main` is protected: changes land through PRs that pass CI and a CODEOWNERS
  review.

## CI gates (all must pass)

- Mission Control / Next: typecheck, lint, vitest with coverage at or above 90
  percent, build.
- Dispatcher: pytest with `--cov-fail-under=90`.
- Data Brain MCP: pytest for the SQL guard with coverage at or above 90 percent.
- E2E: a no-stall owner-drives-agent run against a local Supabase with all
  `FAKE_*` integrations on (zero external calls).
- Security suite: the `tests/security/` control proofs.
- actionlint and `docker compose config` validation.

## Testing

- Use the `FAKE_*` pattern so CI makes zero external calls: `FAKE_DOCKER` for the
  dispatcher, a `FakeSupabase` double for persistence, per-source fakes for M10.
- Golden evals (JSON fixtures in `tests/golden/`) gate sensitive logic: the SQL
  guard allow and deny sets, dispatch routing, per-agent flagship output, and the
  prompt-injection fixture.
- Fault isolation has its own test: kill or pause one agent and assert the others
  stay up and the target restarts.

## Labels

- Type: `type:feature`, `type:bug`, `type:chore`, `type:security`, `type:docs`,
  `type:test`, `type:infra`.
- Area: `area:isolation`, `area:data-layer`, `area:mcp`, `area:agents`,
  `area:mission-control`, `area:dispatcher`, `area:observability`, `area:ci`,
  `area:integrations`.
- Priority: `prio:critical`, `prio:high`, `prio:normal`, `prio:low`.
- Security: `security:control`, `security:threat`, `security:rotation`.
- Agent: `agent:rex`, `agent:dash`, `agent:closer`, `agent:vault`, `agent:bob`,
  `agent:pulse`, `agent:recruiter`.
- Plus `blocked`.

## Issue template

Every issue (and sub-issue) follows this shape:

```
Title: M<n>-<k> <imperative short title>

## What
One paragraph: the change and why, referencing the milestone goal.

## Sub-issues / checklist
- [ ] atomic step
- [ ] atomic step

## Acceptance criteria (functional)
- [ ] observable outcome

## Required tests
- [ ] unit: name / coverage
- [ ] integration: name
- [ ] e2e: spec (if user-facing)
- [ ] security: C# test id (if a control is touched)
- Coverage gate: package at or above 90 percent

## Security considerations
- Controls touched: C# list or none
- Secrets involved: list or none
- Isolation impact: statement

## Dependencies / order
- Depends on: #
- Blocks: #

## Docs
- [ ] Updated: README / SECRETS / ARCHITECTURE / SECURITY / ADR / runbook
```

## Definition of Done (per milestone)

- All issues in the milestone closed.
- Coverage gates green (Next + Python at or above 90 percent).
- E2E and the security suite pass on CI.
- Docs and ADRs updated if scope changed.
- Any touched secret rotated; the secret scan clean.
