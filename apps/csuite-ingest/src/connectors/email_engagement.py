"""M10-1 Email engagement ingest.

Normalized target: one row per email event (sent/open/click/...). The live
fetch() is wired once the sending platform is confirmed; normalize() + the FAKE
fixture lock the schema now.
"""

from __future__ import annotations

from ..base import Connector

COLUMNS = frozenset(
    {"id", "source", "contact_email", "campaign", "event_type", "subject",
     "occurred_at", "meta", "ingested_at"}
)


class EmailEngagement(Connector):
    table = "email_engagement"
    columns = COLUMNS
    source = "email_engagement"

    def normalize(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "id": str(r["id"]),
                "source": self.source,
                "contact_email": r.get("email"),
                "campaign": r.get("campaign"),
                "event_type": r.get("event"),
                "subject": r.get("subject"),
                "occurred_at": r.get("timestamp"),
                "meta": r.get("meta"),
            }
            for r in raw
        ]

    def fake_raw(self) -> list[dict]:
        return [
            {
                "id": "ev_1",
                "email": "lead@example.com",
                "campaign": "may-nurture",
                "event": "open",
                "subject": "Your strategy call",
                "timestamp": "2026-05-24T09:00:00Z",
                "meta": {"device": "mobile"},
            }
        ]
