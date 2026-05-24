"""Per-connector logic: the internal audit_feed and the derived fields."""

from src.connectors.audit_feed import AuditFeed
from src.connectors.nps_feedback import NpsFeedback, _bucket
from src.connectors.webinar_metrics import WebinarMetrics
from src.config import Settings
from src import runner
from src.store import FakeStore


def test_audit_feed_is_internal():
    assert AuditFeed().internal is True


def test_audit_feed_reads_and_normalizes():
    store = FakeStore(
        seed={
            "dispatch": [
                {
                    "id": "d1",
                    "agent": "rex",
                    "requested_by": "diogo",
                    "status": "succeeded",
                    "created_at": "2026-05-24T10:00:00Z",
                }
            ],
            "audit_log": [
                {
                    "id": 7,
                    "actor": "dispatcher",
                    "action": "exec",
                    "target": "csuite-hermes-rex",
                    "detail": "hermes chat -q",
                    "created_at": "2026-05-24T10:00:01Z",
                }
            ],
        }
    )
    c = AuditFeed()
    rows = c.normalize(c.read_source(store))
    by_id = {r["id"]: r for r in rows}
    assert set(by_id) == {"dispatch:d1", "audit_log:7"}
    assert by_id["dispatch:d1"]["action"] == "dispatch"
    assert by_id["dispatch:d1"]["target"] == "rex"
    assert by_id["dispatch:d1"]["actor"] == "diogo"
    assert by_id["audit_log:7"]["source_table"] == "audit_log"
    assert by_id["audit_log:7"]["action"] == "exec"


def test_audit_feed_fake_raw_normalizes():
    c = AuditFeed()
    rows = c.normalize(c.fake_raw())
    assert len(rows) == 2
    assert all(set(r).issubset(c.columns) for r in rows)


def test_runner_internal_path_reads_store():
    store = FakeStore(
        seed={
            "dispatch": [
                {
                    "id": "d1",
                    "agent": "rex",
                    "requested_by": "diogo",
                    "status": "ok",
                    "created_at": "t",
                }
            ],
            "audit_log": [],
        }
    )
    s = Settings(supabase_url="", supabase_key="", fake_source=False, fake_store=True)
    results = runner.run(s, store, names=["audit_feed"])
    assert results[0].ok is True
    assert results[0].rows == 1
    assert store.tables["audit_feed"]


def test_nps_bucket_thresholds():
    assert _bucket(10) == "promoter"
    assert _bucket(9) == "promoter"
    assert _bucket(8) == "passive"
    assert _bucket(7) == "passive"
    assert _bucket(6) == "detractor"
    assert _bucket(None) is None


def test_nps_category_derivation_and_passthrough():
    rows = NpsFeedback().normalize(
        [
            {"id": "n", "score": 9},
            {"id": "m", "score": 5},
            {"id": "p", "score": 2, "category": "promoter"},
        ]
    )
    by = {r["id"]: r for r in rows}
    assert by["n"]["category"] == "promoter"
    assert by["m"]["category"] == "detractor"
    assert by["p"]["category"] == "promoter"  # explicit value preserved


def test_webinar_attendance_rate_derived():
    rows = WebinarMetrics().normalize([{"id": "w", "registrants": 200, "attendees": 90}])
    assert rows[0]["attendance_rate"] == 0.45


def test_webinar_rate_none_without_registrants():
    rows = WebinarMetrics().normalize([{"id": "w"}])
    assert rows[0]["attendance_rate"] is None


def test_webinar_rate_explicit_passthrough():
    rows = WebinarMetrics().normalize(
        [{"id": "w", "registrants": 10, "attendees": 5, "attendance_rate": 0.9}]
    )
    assert rows[0]["attendance_rate"] == 0.9
