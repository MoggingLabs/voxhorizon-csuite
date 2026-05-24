# Mission Control

The only interface to the C-Suite (no Telegram, no Slack). A self-contained
FastAPI service (ADR 0009) on loopback 3100, reached privately via Tailscale
Serve.

Endpoints:
- `GET /health`
- `GET /login`, `POST /login` (single-operator gate; HMAC-signed session cookie
  keyed on `MC_AUTH_SECRET`, password `MC_AUTH_PASS`, fail-closed).
- `GET /` the dashboard (agent roster).
- `GET /api/agents` the roster (auth required).
- `POST /api/dispatch` `{agent, prompt}` proxies to the dispatcher with the bearer
  and streams the agent output back (SSE).
- `GET /api/history` recent dispatches + audit rows from Supabase.

Tested with FakeDispatcher + FakeStore (no dispatcher or DB needed in CI), at
>=90 percent coverage. Run: `uvicorn src.main:create_app --factory`. The optional
Data Brain BI dashboard runs separately on 3101.
