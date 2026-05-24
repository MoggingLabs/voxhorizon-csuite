# Tests

- `security/` control-proving tests for the SECURITY.md matrix (C1..C12). The
  static isolation guard (`isolation_guard.py`, control C1/C6) runs in CI today.
- `golden/` JSON fixtures that gate sensitive logic: the read-only SQL guard
  allow/deny sets, dispatch routing, per-agent flagship output, and the
  prompt-injection fixture.
- `e2e/` Playwright "owner drives an agent from Mission Control end to end"
  (chromium, serialized, all `FAKE_*` on, zero external calls).

Coverage gates (CI): Mission Control vitest, dispatcher pytest, and the MCP pytest
each at or above 90 percent. The security suite runs as its own CI job so a
regression fails the PR.
