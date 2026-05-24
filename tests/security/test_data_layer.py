"""M2 data-layer static tests (controls C1, C3).

These assert the repo-side data-layer wiring is correct without needing a live
database. The live "Supabase healthy + role write-denied" verification happens
when bootstrap runs on the VPS.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_readonly_role_grants_select_only():
    """sec_readonly_role_write_denied (static): the role gets SELECT, never write."""
    sql = (REPO / "db" / "migrations" / "0001_csuite_readonly.sql").read_text(
        encoding="utf-8"
    ).lower()
    assert "grant select on all tables" in sql
    assert "create role csuite_readonly login" in sql
    for forbidden in (
        "grant insert",
        "grant update",
        "grant delete",
        "grant truncate",
        "grant all",
    ):
        assert forbidden not in sql, f"read-only role must not have: {forbidden}"


def test_bootstrap_uses_data_brain_src():
    """The Data Brain source is configurable, not a hardcoded missing sibling."""
    boot = (REPO / "infra" / "bootstrap-csuite.sh").read_text(encoding="utf-8")
    assert "DATA_BRAIN_SRC" in boot
    assert "business-data-brain-template/." not in boot


def test_bootstrap_binds_supabase_loopback():
    """sec_ports_loopback_only (supabase): bootstrap rewrites published ports to loopback."""
    boot = (REPO / "infra" / "bootstrap-csuite.sh").read_text(encoding="utf-8")
    assert "127.0.0.1:" in boot
    assert "KONG_HTTP_PORT" in boot
