"""M10-3 Churn reasons capture.

Normalized target: one row per cancellation with the categorized reason and the
MRR lost, so Vault/Pulse can quantify and explain churn.
"""

from __future__ import annotations

from ..base import Connector

COLUMNS = frozenset(
    {"id", "source", "account", "customer_email", "plan", "mrr_lost",
     "reason_category", "reason_text", "canceled_at", "tenure_days", "ingested_at"}
)


class ChurnReasons(Connector):
    table = "churn_reasons"
    columns = COLUMNS
    source = "churn_reasons"

    def normalize(self, raw: list[dict]) -> list[dict]:
        return [
            {
                "id": str(r["id"]),
                "source": self.source,
                "account": r.get("account"),
                "customer_email": r.get("email"),
                "plan": r.get("plan"),
                "mrr_lost": r.get("mrr_lost"),
                "reason_category": r.get("reason_category"),
                "reason_text": r.get("reason_text"),
                "canceled_at": r.get("canceled_at"),
                "tenure_days": r.get("tenure_days"),
            }
            for r in raw
        ]

    def fake_raw(self) -> list[dict]:
        return [
            {
                "id": "churn_1",
                "account": "Acme Co",
                "email": "owner@acme.example",
                "plan": "growth",
                "mrr_lost": 2500,
                "reason_category": "price",
                "reason_text": "Switching to in-house team",
                "canceled_at": "2026-05-20T00:00:00Z",
                "tenure_days": 210,
            }
        ]
