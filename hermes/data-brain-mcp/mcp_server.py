"""Data-Brain read MCP server for the Vox Horizon C-Suite.

A read-only window over the self-hosted Supabase Postgres (the Data Brain), so
C-Suite Hermes agents can answer questions from business data without calling
source SaaS APIs directly. Defense-in-depth, modeled on the justcall-readonly
pattern: read-only by construction at several layers.

1. Tool vocabulary: only list_tables / describe_table / run_select are exposed.
   There is no insert/update/delete tool.
2. Every query runs in a READ ONLY transaction with a statement timeout.
3. run_select rejects anything that is not a single SELECT/WITH and denies DML
   keywords as a second guard.
4. Results are row-capped.
5. Connect with a SELECT-only DB role (CSUITE_DB_DSN -> csuite_readonly) as the
   outermost guard, so even a bug here cannot write.

Env:
  CSUITE_DB_DSN  postgresql DSN for the read-only role into the Data Brain DB.

Run (by Hermes, via config.yaml mcp_servers):
  /opt/hermes/.venv/bin/python /opt/data/skills/data-brain-mcp/mcp_server.py
Deps: psycopg[binary], mcp
"""

from __future__ import annotations

import os
import re
import sys

import psycopg
from mcp.server.fastmcp import FastMCP

DSN = os.environ.get("CSUITE_DB_DSN", "")
ROW_CAP = 200
STATEMENT_TIMEOUT_MS = 8000

# Single-statement SELECT/WITH only. Reject anything else up front.
_SELECT_RE = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)
_DENY_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|"
    r"vacuum|reindex|call|do|merge)\b",
    re.IGNORECASE,
)

mcp = FastMCP("csuite-data-brain")


def _audit(tool: str, detail: str) -> None:
    # Stderr is captured into the agent's logs; one line per call.
    print(f"[data-brain-mcp] {tool}: {detail}", file=sys.stderr, flush=True)


def _connect() -> psycopg.Connection:
    if not DSN:
        raise RuntimeError("CSUITE_DB_DSN is not set")
    # autocommit so we control the read-only transaction explicitly per query.
    return psycopg.connect(DSN, autocommit=True)


def _read_only(cur: psycopg.Cursor) -> None:
    cur.execute(f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}")
    cur.execute("SET default_transaction_read_only = on")


@mcp.tool()
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


@mcp.tool()
def describe_table(table: str) -> list[dict]:
    """Return column name + type for one table in the Data Brain."""
    if not re.fullmatch(r"[a-zA-Z0-9_]+", table):
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


@mcp.tool()
def run_select(sql: str) -> dict:
    """Run a single read-only SELECT against the Data Brain and return rows.

    Only one SELECT/WITH statement is allowed. Results are capped at 200 rows.
    """
    one = sql.strip().rstrip(";")
    if ";" in one:
        raise ValueError("only a single statement is allowed")
    if not _SELECT_RE.match(one):
        raise ValueError("only SELECT/WITH queries are allowed")
    if _DENY_RE.search(one):
        raise ValueError("query contains a disallowed keyword")

    with _connect() as conn, conn.cursor() as cur:
        _read_only(cur)
        cur.execute(f"select * from ({one}) _q limit {ROW_CAP}")
        columns = [d.name for d in cur.description] if cur.description else []
        rows = [dict(zip(columns, r)) for r in cur.fetchall()]
    _audit("run_select", f"{len(rows)} rows for: {one[:120]}")
    return {"columns": columns, "rows": rows, "row_cap": ROW_CAP}


if __name__ == "__main__":
    mcp.run()
