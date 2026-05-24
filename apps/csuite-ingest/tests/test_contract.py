"""Schema contract: every connector normalizes its FAKE payload into rows that
fit its declared columns and carry a primary key. This locks the V2 table schema
(0003_v2_ingest.sql) independently of which source tool is wired."""

import pytest

from src.connectors import REGISTRY

EXPECTED_TABLES = {
    "email_engagement",
    "support_tickets",
    "churn_reasons",
    "content_calendar",
    "webinar_metrics",
    "nps_feedback",
    "audit_feed",
}


def test_registry_covers_every_v2_table():
    assert {REGISTRY[n].table for n in REGISTRY} == EXPECTED_TABLES


@pytest.mark.parametrize("name", list(REGISTRY))
def test_normalize_fits_schema(name):
    c = REGISTRY[name]()
    raw = c.fake_raw()
    assert raw, f"{name}: fake_raw is empty"
    rows = c.normalize(raw)
    assert rows, f"{name}: normalize produced no rows"
    for row in rows:
        extra = set(row) - set(c.columns)
        assert not extra, f"{name}: emitted unknown columns {sorted(extra)}"
        assert row.get(c.pk) not in (None, ""), f"{name}: row missing pk"


@pytest.mark.parametrize("name", [n for n in REGISTRY if not REGISTRY[n].internal])
def test_external_rows_tag_source(name):
    c = REGISTRY[name]()
    rows = c.normalize(c.fake_raw())
    assert all(r["source"] == c.source for r in rows)
