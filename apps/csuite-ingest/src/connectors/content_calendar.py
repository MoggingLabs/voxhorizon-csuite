"""M10-4 Content calendar ingest.

Normalized target: one row per planned/published content item across channels,
so Bob can see the pipeline and cadence.
"""

from __future__ import annotations

from ..base import Connector

COLUMNS = frozenset(
    {"id", "source", "title", "channel", "status", "owner", "scheduled_for",
     "published_at", "url", "tags", "ingested_at"}
)


class ContentCalendar(Connector):
    table = "content_calendar"
    columns = COLUMNS
    source = "content_calendar"

    def normalize(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "id": str(r["id"]),
                "source": self.source,
                "title": r.get("title"),
                "channel": r.get("channel"),
                "status": r.get("status"),
                "owner": r.get("owner"),
                "scheduled_for": r.get("scheduled_for"),
                "published_at": r.get("published_at"),
                "url": r.get("url"),
                "tags": r.get("tags"),
            }
            for r in raw
        ]

    def fake_raw(self) -> list[dict]:
        return [
            {
                "id": "post_1",
                "title": "How agencies scale with AI",
                "channel": "youtube",
                "status": "scheduled",
                "owner": "bob",
                "scheduled_for": "2026-05-28T15:00:00Z",
                "published_at": None,
                "url": None,
                "tags": ["ai", "growth"],
            }
        ]
