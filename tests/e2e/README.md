# E2E

Playwright, chromium, serialized. The headline spec: the owner authenticates in
Mission Control, dispatches a task to Rex, the output streams over SSE to a
terminal state, and the result plus an audit row persist and render. Asserts
no-stall (must reach a terminal state).

Runs against a local Supabase with all `FAKE_*` integrations on (including
`FAKE_DOCKER`), so CI makes zero external calls. Added with M5/M7.
