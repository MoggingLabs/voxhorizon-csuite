# Golden evals

JSON fixtures that gate sensitive logic. A change that breaks a golden case fails
CI. Planned sets:

- `sql_guard/` allow (plain SELECT, CTE, joins) and deny (insert, update, delete,
  drop, multi-statement, comment-smuggled DML, casing tricks) for the read MCP.
- `dispatch_routing/` agent name to container allow-list.
- `agent_output/` per-agent flagship output given seeded rows (e.g. Vault red
  flags).
- `prompt_injection/` a malicious transcript asking for a write; expectation is no
  state change and the MCP guard refuses.
