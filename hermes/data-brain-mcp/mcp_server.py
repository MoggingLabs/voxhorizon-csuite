"""Data-Brain read MCP server for the Vox Horizon C-Suite.

A read-only window over the self-hosted Supabase Postgres (the Data Brain), so
C-Suite Hermes agents can answer questions from business data without calling
source SaaS APIs directly. Read-only by construction (security control C3):

1. Tool vocabulary: only list_tables / describe_table / run_select are exposed.
2. Every query runs in a READ ONLY transaction with a statement timeout.
3. run_select accepts a single SELECT/WITH only and denies DML (see guard.py).
4. Results are row-capped.
5. Connect as a SELECT-only DB role (CSUITE_DB_DSN -> csuite_readonly).

The security-critical SQL guard lives in guard.py (pure, unit-tested). This
module is the thin DB + MCP wiring.

Env: CSUITE_DB_DSN  postgresql DSN for the read-only role into the Data Brain DB.
Run (by Hermes, via config.yaml mcp_servers):
  python /opt/data/skills/data-brain-mcp/mcp_server.py
Runtime deps (optional extra): mcp, psycopg[binary].
"""

from __future__ import annotations

import os
import sys

import psycopg
from mcp.server.fastmcp import FastMCP

import guard

DSN = os.environ.get("CSUITE_DB_DSN", "")

mcp = FastMCP("csuite-data-brain")


def _audit(tool: str, detail: str) -> None:
    print(f"[data-brain-mcp] {tool}: {detail}", file=sys.stderr, flush=True)


def _connect():
    if not DSN:
        raise RuntimeError("CSUITE_DB_DSN is not set")
    return psycopg.connect(DSN, autocommit=True)  # pragma: no cover


def _read_only(cur) -> None:
    cur.execute(f"SET statement_timeout = {guard.STATEMENT_TIMEOUT_MS}")
    cur.execute("SET default_transaction_read_only = on")


def list_tables() -> list[str]:
    """List the business tables in the Data Brain (public schema)."""
    with _connect() as conn, conn.cursor() as cur:
        _read_only(cur)
        cur.execute(
            "select table_name from information_schema.tables "
            "where table_schema = 'public' and table_type = 'BASE TABLE' "
            "order by table_name"
        )
        rows = [r[0] for r in cur.fetchall()]
    _audit("list_tables", f"{len(rows)} tables")
    return rows


def describe_table(table: str) -> list[dict]:
    """Return column name + type for one table in the Data Brain."""
    if not guard.valid_table_name(table):
        raise ValueError("invalid table name")
    with _connect() as conn, conn.cursor() as cur:
        _read_only(cur)
        cur.execute(
            "select column_name, data_type from information_schema.columns "
            "where table_schema = 'public' and table_name = %s "
            "order by ordinal_position",
            (table,),
        )
        cols = [{"column": c, "type": t} for c, t in cur.fetchall()]
    _audit("describe_table", f"{table}: {len(cols)} cols")
    return cols


def run_select(sql: str) -> dict:
    """Run a single read-only SELECT against the Data Brain and return rows."""
    one = guard.validate_select(sql)
    with _connect() as conn, conn.cursor() as cur:
        _read_only(cur)
        cur.execute(f"select * from ({one}) _q limit {guard.ROW_CAP}")
        columns = [d.name for d in cur.description] if cur.description else []
        rows = [dict(zip(columns, r)) for r in cur.fetchall()]
    _audit("run_select", f"{len(rows)} rows")
    return {"columns": columns, "rows": rows, "row_cap": guard.ROW_CAP}


# Register the tools with the MCP server (kept as plain functions above so the
# guard logic stays importable/testable without the MCP runtime).
mcp.tool()(list_tables)
mcp.tool()(describe_table)
mcp.tool()(run_select)


if __name__ == "__main__":  # pragma: no cover
    mcp.run()
