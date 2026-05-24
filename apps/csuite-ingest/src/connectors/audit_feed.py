"""M10-7 Audit-log ingest (internal, no external credential).

Consolidates the C-Suite's own dispatch and audit_log tables into one
compliance-friendly timeline (audit_feed). Reads through the Store, so it works
the same against FakeStore (CI) and the live Supabase.
"""

from __future__ import annotations

from ..base import Connector

COLUMNS = frozenset(
    {"id", "occurred_at", "actor", "action", "target", "source_table", "detail", "ingested_at"}
)


class AuditFeed(Connector):
    table = "audit_feed"
    columns = COLUMNS
    source = "internal"
    internal = True

    def read_source(self, store) -> list[dict]:
        rows: list[dict] = []
        for d in store.read("dispatch"):
            rows.append({**d, "_src": "dispatch"})
        for a in store.read("audit_log"):
            rows.append({**a, "_src": "audit_log"})
        return rows

    def normalize(self, raw: list[dict]) -> list[dict]:
        out: list[dict] = []
        for r in raw:
            src = r.get("_src", "audit_log")
            if src == "dispatch":
                out.append(
                    {
                        "id": f"dispatch:{r['id']}",
                        "occurred_at": r.get("created_at"),
                        "actor": r.get("requested_by"),
                        "action": "dispatch",
                        "target": r.get("agent"),
                        "source_table": "dispatch",
                        "detail": r.get("status"),
                    }
                )
            else:
                out.append(
                    {
                        "id": f"audit_log:{r['id']}",
                        "occurred_at": r.get("created_at"),
                        "actor": r.get("actor"),
                        "action": r.get("action"),
                        "target": r.get("target"),
                        "source_table": "audit_log",
                        "detail": r.get("detail"),
                    }
                )
        return out

    def fake_raw(self) -> list[dict]:
        return [
            {
                "_src": "dispatch",
                "id": "11111111-1111-1111-1111-111111111111",
                "agent": "rex",
                "requested_by": "diogo",
                "status": "succeeded",
                "created_at": "2026-05-24T10:00:00Z",
            },
            {
                "_src": "audit_log",
                "id": 42,
                "actor": "dispatcher",
                "action": "exec",
                "target": "csuite-hermes-rex",
                "detail": "hermes chat -q",
                "created_at": "2026-05-24T10:00:01Z",
            },
        ]
