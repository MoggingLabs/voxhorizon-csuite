# Security

Security is a first-class concern for this system: it reads the entire business
and runs on a host that also runs production. This document is the threat model,
the controls, and the test that proves each control. Every control must have a
passing test before M9 (Security hardening) can close.

## Security model

- The C-Suite is fully isolated from production (own user, dirs, network, ports,
  database, secrets). The production stack is never modified by this repo.
- Agents are read-only over business data and have no messaging channel, so the
  blast radius of a compromised or prompt-injected agent is "can read, cannot act."
- Irreversible actions are human-gated (manual approval), never autonomous in V1.
- The Docker socket, the one root-equivalent surface, is scope-limited to `exec`
  on `csuite-hermes-*` through a proxy; the dispatcher never holds the raw socket.
- Secrets never enter git; the model auth is a subscription OAuth token file, not
  an API key.

## Threat model

Assets: the business data (Data Brain), the Codex OAuth subscription
(`auth.json`), the Supabase keys, the dispatcher bearer, and the production host
(must be unreachable from here).

Adversaries and entry points:
- A poisoned transcript, lead note, or ad copy ingested into the Data Brain that
  instructs an agent to exfiltrate or mutate data (prompt injection).
- A compromised dependency in the dispatcher or MCP attempting a host pivot.
- An anon-key holder hitting the public Supabase REST endpoint.
- Accidental cross-contamination with the live ad pipeline.
- Secret leakage into git history.

## Controls and proving tests

| # | Threat | Control | Proving test |
|---|---|---|---|
| C1 | Cross-contamination with prod | csuite user, dirs, net, loopback ports; bootstrap refuses prod root | sec_isolation_static, sec_bootstrap_refuses_prod, sec_ports_loopback_only |
| C2 | Docker socket is root-equivalent | scoped proxy (EXEC only, csuite-hermes-*), argv not shell, name allow-list | sec_dispatcher_rejects_foreign_container, sec_proxy_denies_non_exec_verbs, sec_dispatcher_no_shell_injection |
| C3 | Agents mutate business data | read-only MCP guard + SELECT-only role + RLS | golden_sql_guard_allow, golden_sql_guard_deny, sec_readonly_role_write_denied, sec_rls_deny_all |
| C4 | Codex auth.json leak | gitignored, chmod 600, never logged | sec_authjson_not_tracked, sec_authjson_perms |
| C5 | Leaked WORKER_SHARED_SECRET | rotated on prod; absent here | sec_no_worker_shared_secret_in_repo |
| C6 | OpenRouter / API-key drift | scrub; subscription only | sec_grep_no_openrouter, sec_no_api_key_env, sec_active_provider_codex |
| C7 | Public Supabase REST | RLS deny-all, service-role behind the MC gate | sec_rls_deny_all, sec_anon_cannot_write |
| C8 | Prompt injection from ingested content | read-only blast radius + manual approvals + SOUL never-do + dispatcher allow-list | golden_prompt_injection, sec_approvals_manual, sec_agent_no_egress_tools |
| C9 | Secret in git history | gitleaks + .gitignore + custom rules | secret-scan workflow green |
| C10 | Audit gap | dispatch + audit_log tables; every exec writes an audit row | sec_dispatch_writes_audit |
| C11 | Dispatcher bearer | constant-time compare, loopback, fail-closed | sec_bearer_constant_time, sec_bearer_rejects_missing |
| C12 | Supply chain | dependabot + gitleaks + pinned lockfiles + CodeQL (active; CodeQL is free now that the repo is public). dependency-review can be added once the Dependency graph is enabled in repo settings. | secret-scan + codeql green; dependabot active |

## Control status (M9)

Every control has a test enforced in CI, except the two that can only be checked
on a running host (marked deploy):

- C1 isolation: `test_isolation_guard`, `test_bootstrap_contract`, `test_ports_loopback`, `test_agents` (CI).
- C2 scoped socket: `test_dispatch` abuse cases (CI).
- C3 read-only data: MCP `test_guard` golden allow/deny + `test_data_layer` role grants (CI).
- C4 auth.json handling: chmod + not-tracked (deploy; `.gitignore` covers tracking).
- C5 no leaked prod secret: `test_no_prod_secret` (CI).
- C6 OpenRouter / API-key scrub: `test_isolation_guard` (CI).
- C7 RLS deny-all: `test_dispatch_tables` (CI); live RLS at deploy.
- C8 prompt injection: `test_prompt_injection_is_rejected` + the deny golden (CI).
- C9 secret scan: gitleaks workflow (CI).
- C10 audit: dispatcher records audit rows (`test_dispatch`); table in `test_dispatch_tables` (CI).
- C11 dispatcher bearer: `test_dispatch` bearer cases (CI).
- C12 supply chain: dependabot + gitleaks + CodeQL (CI, free on the public repo); dependency-review optional once the Dependency graph is enabled in settings.

## Prompt injection posture

The architecture makes injection low-impact by construction. Agents have no write
tool, no client-messaging channel (Mission Control only), and any irreversible
tool requires manual approval. The proving test (`golden_prompt_injection`) seeds
a malicious transcript that asks the agent to delete rows and asserts that no
state change occurs and the MCP guard rejects the smuggled DML.

## Secrets

The full secret inventory, locations, owners, and rotation cadence are in
[SECRETS.md](SECRETS.md). Highlights: the Codex `auth.json` is treated as a
credential file (gitignored, chmod 600, never logged). The leaked production
`WORKER_SHARED_SECRET` flagged during research must be rotated on the production
stack and must never appear in this repo (enforced by a test).

## Reporting a security issue

This is a private repo. Open an issue using the Security template
([.github/ISSUE_TEMPLATE/security.md](.github/ISSUE_TEMPLATE/security.md)) and do
not disclose details outside the repo. Capture the affected control, blast radius,
isolation impact, any secret exposure, and reproduction.
