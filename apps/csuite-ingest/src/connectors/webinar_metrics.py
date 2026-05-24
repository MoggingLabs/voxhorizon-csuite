"""M10-5 Webinar metrics ingest.

Normalized target: one row per webinar with attendance and conversion metrics.
"""

from __future__ import annotations

from ..base import Connector

COLUMNS = frozenset(
    {"id", "source", "webinar_title", "scheduled_for", "registrants", "attendees",
     "attendance_rate", "avg_watch_minutes", "replay_views", "conversions",
     "revenue", "ingested_at"}
)


class WebinarMetrics(Connector):
    table = "webinar_metrics"
    columns = COLUMNS
    source = "webinar_metrics"

    def normalize(self, raw: list[dict]) -> list[dict]:
        out = []
        for r in raw:
            reg = r.get("registrants")
            att = r.get("attendees")
            rate = r.get("attendance_rate")
            if rate is None and reg:
                rate = round(att / reg, 4) if att is not None else None
            out.append(
                {
                    "id": str(r["id"]),
                    "source": self.source,
                    "webinar_title": r.get("title"),
                    "scheduled_for": r.get("scheduled_for"),
                    "registrants": reg,
                    "attendees": att,
                    "attendance_rate": rate,
                    "avg_watch_minutes": r.get("avg_watch_minutes"),
                    "replay_views": r.get("replay_views"),
                    "conversions": r.get("conversions"),
                    "revenue": r.get("revenue"),
                }
            )
        return out

    def fake_raw(self) -> list[dict]:
        return [
            {
                "id": "web_1",
                "title": "Scaling to 50k/mo",
                "scheduled_for": "2026-05-22T17:00:00Z",
                "registrants": 200,
                "attendees": 90,
                "avg_watch_minutes": 38.5,
                "replay_views": 120,
                "conversions": 12,
                "revenue": 18000,
            }
        ]
