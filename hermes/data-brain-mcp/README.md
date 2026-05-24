# data-brain-mcp

Read-only MCP server that gives every C-Suite Hermes agent a safe window into the
Data Brain (the self-hosted Supabase Postgres). This is the "bridge" the research
flagged as build item #1: agents read business truth here instead of calling
source SaaS APIs.

## Tools

- `list_tables()` - business tables in the `public` schema (the `t01_..t91_` set).
- `describe_table(table)` - columns + types for one table.
- `run_select(sql)` - one read-only SELECT/WITH, row-capped at 200.

## Read-only by construction (defense in depth)

1. Only read tools exist (no write tool in the vocabulary).
2. Each query runs with `default_transaction_read_only = on` + a statement timeout.
3. `run_select` accepts a single SELECT/WITH only and denies DML keywords.
4. Results are row-capped.
5. Connect as a SELECT-only role (`csuite_readonly`) via `CSUITE_DB_DSN` - the
   outermost guard, so even a bug cannot write.

## Wiring

Referenced from each agent's `config.yaml` (see `../config.csuite.patch.md`):

```yaml
mcp_servers:
  csuite-data-brain:
    command: /opt/hermes/.venv/bin/python
    args: [/opt/data/skills/data-brain-mcp/mcp_server.py]
    env:
      CSUITE_DB_DSN: ${CSUITE_DB_DSN}
```

`sync-csuite.sh` copies this folder into each agent's `data/skills/data-brain-mcp/`.

## Deps + DB role

The Hermes venv needs `psycopg[binary]` and `mcp`. Create the read-only role once
against the self-hosted DB:

```sql
create role csuite_readonly login password 'CHANGE_ME';
grant connect on database postgres to csuite_readonly;
grant usage on schema public to csuite_readonly;
grant select on all tables in schema public to csuite_readonly;
alter default privileges in schema public grant select on tables to csuite_readonly;
```

Then set `CSUITE_DB_DSN=postgresql://csuite_readonly:...@db:5432/postgres` in
`csuite.env` (the `db` host resolves on the Supabase network).
