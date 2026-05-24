"""M10-1 Email engagement ingest - GoHighLevel.

Source: GoHighLevel (LeadConnector) email campaigns. We PULL campaigns with
stats via `GET /emails/schedule?showStats=true` rather than receive the
per-recipient LCEmailStats webhook, because the C-Suite host is outbound-only and
isolated (no inbound/public webhook endpoint). One row per campaign; whatever
stats GHL returns are preserved in `meta` (jsonb), so the row stays valid even as
GHL's stat field names evolve.

Credentials (csuite.env / secrets/ingest.env):
- EMAIL_ENGAGEMENT_API_KEY      Private Integration token (emails read scope)
- EMAIL_ENGAGEMENT_LOCATION_ID  the GHL sub-account/location id
- EMAIL_ENGAGEMENT_API_URL      optional, default https://services.leadconnectorhq.com
- EMAIL_ENGAGEMENT_API_VERSION  optional, default 2021-07-28
- EMAIL_ENGAGEMENT_PAGE_LIMIT   optional, default 100
"""

from __future__ import annotations

from ..base import Connector

COLUMNS = frozenset(
    {"id", "source", "contact_email", "campaign", "event_type", "subject",
     "occurred_at", "meta", "ingested_at"}
)

# Large/derived fields we keep out of meta to bound row size.
_GHL_DROP = {"downloadUrl", "templateDataDownloadUrl", "child"}
_GHL_HOST = "https://services.leadconnectorhq.com"
_GHL_VERSION = "2021-07-28"


def _ghl_to_records(schedules: list[dict]) -> list[dict]:
    """Map GHL ScheduleDto campaigns to the connector's intermediate shape."""
    records: list[dict] = []
    for s in schedules:
        sid = s.get("_id") or s.get("id")
        if not sid:
            continue
        records.append(
            {
                "id": str(sid),
                "email": None,  # campaign-level, not a single recipient
                "campaign": s.get("name"),
                "event": "campaign",
                "subject": s.get("name"),
                "timestamp": s.get("updatedAt") or s.get("createdAt"),
                "meta": {k: v for k, v in s.items() if k not in _GHL_DROP},
            }
        )
    return records


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

    def fetch(self, env: dict[str, str]) -> list[dict]:  # pragma: no cover
        import httpx

        token = (env.get("EMAIL_ENGAGEMENT_API_KEY") or "").strip()
        location = (env.get("EMAIL_ENGAGEMENT_LOCATION_ID") or "").strip()
        if not (token and location):
            return []  # not configured: stays a no-op, never errors the run
        base = (env.get("EMAIL_ENGAGEMENT_API_URL") or _GHL_HOST).rstrip("/")
        version = (env.get("EMAIL_ENGAGEMENT_API_VERSION") or _GHL_VERSION).strip()
        limit = int(env.get("EMAIL_ENGAGEMENT_PAGE_LIMIT") or "100")
        headers = {
            "Authorization": f"Bearer {token}",
            "Version": version,
            "Accept": "application/json",
        }
        schedules: list[dict] = []
        offset = 0
        with httpx.Client(timeout=30, headers=headers) as client:
            while True:
                resp = client.get(
                    f"{base}/emails/schedule",
                    params={
                        "locationId": location,
                        "showStats": "true",
                        "limit": limit,
                        "offset": offset,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                page = data.get("schedules") or []
                schedules.extend(page)
                offset += limit
                if not page or offset >= (data.get("total") or 0):
                    break
        return _ghl_to_records(schedules)

    def fake_raw(self) -> list[dict]:
        return [
            {
                "id": "camp_1",
                "email": None,
                "campaign": "May Nurture",
                "event": "campaign",
                "subject": "May Nurture",
                "timestamp": "2026-05-24T09:00:00Z",
                "meta": {"status": "sent", "hasTracking": True, "opened": 42},
            }
        ]
