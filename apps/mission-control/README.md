# Mission Control (Agents module)

The only interface to the C-Suite. Implemented in M5 as an "Agents" module added
to the Data Brain Next.js + Supabase app (not a separate app), so it reuses the
existing auth gate, Supabase Realtime, and chat/SSE patterns.

Scope (M5):
- Agent roster + live container status from the dispatcher.
- Per-agent dispatch surface: submit a task, stream output over SSE, persist the
  result.
- Rex's daily task board.
- Dispatch + audit history (reads the `dispatch` and `audit_log` tables).

Auth: single-operator gate, fail-closed (`MC_AUTH_PASS` / `MC_AUTH_SECRET`).
Reached privately over Tailscale Serve on loopback port 3100.

This directory holds the module source overlay and its tests. Until M5 lands it
is a placeholder, and the `mission-control` CI job skips (guarded on
`package.json`).
