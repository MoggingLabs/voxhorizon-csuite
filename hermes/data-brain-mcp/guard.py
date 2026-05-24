"""Pure SQL guard for the read-only Data Brain MCP (security control C3).

No external dependencies, so the security-critical logic is unit-tested in CI
without a database or the MCP/psycopg packages. The MCP server imports these.
"""

from __future__ import annotations

import re

ROW_CAP = 200
STATEMENT_TIMEOUT_MS = 8000

# Only a single SELECT or WITH statement is allowed.
_SELECT_RE = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)

# Any write / DDL / data-movement keyword is denied (word-bounded, so columns
# like `created_at` or `deleted_at` are not false positives).
_DENY_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|"
    r"vacuum|reindex|call|do|merge)\b",
    re.IGNORECASE,
)

_TABLE_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def valid_table_name(name: str) -> bool:
    """True only for a bare identifier (no schema, quotes, or punctuation)."""
    return bool(_TABLE_RE.fullmatch(name or ""))


def validate_select(sql: str) -> str:
    """Return the cleaned single SELECT/WITH statement, or raise ValueError.

    Rejects: empty input, multiple statements, anything not starting with
    SELECT/WITH, and any statement containing a write/DDL keyword (including
    smuggled DML inside a subquery, and case variations).
    """
    one = (sql or "").strip().rstrip(";").strip()
    if not one:
        raise ValueError("empty query")
    if ";" in one:
        raise ValueError("only a single statement is allowed")
    if not _SELECT_RE.match(one):
        raise ValueError("only SELECT/WITH queries are allowed")
    if _DENY_RE.search(one):
        raise ValueError("query contains a disallowed keyword")
    return one
