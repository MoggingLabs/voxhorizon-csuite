# csuite-dispatcher

A small FastAPI service that drives the passive Hermes agents on behalf of Mission
Control. Built in M6. Until then this is a placeholder and the `dispatcher` CI job
skips (guarded on `pyproject.toml`).

Responsibilities:
- Accept a task for an agent from Mission Control, bearer-authed
  (`CSUITE_DISPATCHER_SECRET`, constant-time compare), loopback only (8200).
- Validate the target against `^csuite-hermes-(rex|dash|closer|vault|bob|pulse)$`.
- Run `hermes chat -q ...` in the target container through the scoped socket proxy
  (`DOCKER_HOST=tcp://csuite-socket-proxy:2375`), using an argv array, never a
  shell string.
- Stream agent output back as SSE; record the dispatch and an audit row in
  Supabase.

Security tests (M6-2): rejects foreign containers, rejects shell-injection in the
name, rejects missing/wrong bearer, and the proxy denies non-exec verbs. Built and
tested with `FAKE_DOCKER` + a `FakeSupabase` double so CI makes zero external
calls. Coverage gate: 90 percent.

Layout (M6): `src/` (FastAPI app), `tests/`, `pyproject.toml` (uv), `Dockerfile`.
