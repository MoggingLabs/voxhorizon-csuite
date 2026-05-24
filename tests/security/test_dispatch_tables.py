"""M5-3 static test: the dispatch + audit tables exist with RLS deny-all (C7, C10)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_dispatch_and_audit_migration():
    sql = (REPO / "db" / "migrations" / "0002_dispatch_audit.sql").read_text(
        encoding="utf-8"
    ).lower()
    assert "create table if not exists dispatch" in sql
    assert "create table if not exists audit_log" in sql
    # RLS deny-all on both, and no grants to anon/authenticated.
    assert "alter table dispatch enable row level security" in sql
    assert "alter table audit_log enable row level security" in sql
    assert "revoke all on dispatch from anon, authenticated" in sql
    assert "revoke all on audit_log from anon, authenticated" in sql
    assert "create policy" not in sql  # deny-all: no policies
