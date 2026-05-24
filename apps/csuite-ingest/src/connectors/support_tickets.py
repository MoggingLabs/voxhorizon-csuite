"""M10-2 Support tickets ingest.

Normalized target: one row per support ticket with lifecycle timestamps so
agents can reason about response and resolution times.
"""

from __future__ import annotations

from ..base import Connector

COLUMNS = frozenset(
    {"id", "source", "requester_email", "subject", "status", "priority", "channel",
     "assignee", "created_at", "updated_at", "first_response_at", "resolved_at",
     "satisfaction", "tags", "ingested_at"}
)


class SupportTickets(Connector):
    table = "support_tickets"
    columns = COLUMNS
    source = "support_tickets"

    def normalize(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "id": str(r["id"]),
                "source": self.source,
                "requester_email": r.get("requester"),
                "subject": r.get("subject"),
                "status": r.get("status"),
                "priority": r.get("priority"),
                "channel": r.get("channel"),
                "assignee": r.get("assignee"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "first_response_at": r.get("first_response_at"),
                "resolved_at": r.get("resolved_at"),
                "satisfaction": r.get("satisfaction"),
                "tags": r.get("tags"),
            }
            for r in raw
        ]

    def fake_raw(self) -> list[dict]:
        return [
            {
                "id": "tkt_1",
                "requester": "client@example.com",
                "subject": "Cannot access dashboard",
                "status": "open",
                "priority": "high",
                "channel": "email",
                "assignee": "support",
                "created_at": "2026-05-24T08:00:00Z",
                "updated_at": "2026-05-24T08:30:00Z",
                "first_response_at": "2026-05-24T08:20:00Z",
                "resolved_at": None,
                "satisfaction": None,
                "tags": ["access"],
            }
        ]
