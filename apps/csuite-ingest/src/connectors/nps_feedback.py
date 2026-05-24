"""M10-6 NPS and feedback ingest.

Normalized target: one row per survey response with the NPS bucket derived from
the 0..10 score when the source does not provide it.
"""

from __future__ import annotations

from ..base import Connector

COLUMNS = frozenset(
    {"id", "source", "respondent_email", "score", "category", "comment", "survey",
     "submitted_at", "ingested_at"}
)


def _bucket(score: int | None) -> str | None:
    if score is None:
        return None
    if score >= 9:
        return "promoter"
    if score >= 7:
        return "passive"
    return "detractor"


class NpsFeedback(Connector):
    table = "nps_feedback"
    columns = COLUMNS
    source = "nps_feedback"

    def normalize(self, raw: list[dict]) -> list[dict]:
        out = []
        for r in raw:
            score = r.get("score")
            out.append(
                {
                    "id": str(r["id"]),
                    "source": self.source,
                    "respondent_email": r.get("email"),
                    "score": score,
                    "category": r.get("category") or _bucket(score),
                    "comment": r.get("comment"),
                    "survey": r.get("survey"),
                    "submitted_at": r.get("submitted_at"),
                }
            )
        return out

    def fake_raw(self) -> list[dict]:
        return [
            {
                "id": "nps_1",
                "email": "client@example.com",
                "score": 9,
                "comment": "Great results, responsive team",
                "survey": "q2-nps",
                "submitted_at": "2026-05-21T12:00:00Z",
            },
            {
                "id": "nps_2",
                "email": "other@example.com",
                "score": 5,
                "comment": "Onboarding was slow",
                "survey": "q2-nps",
                "submitted_at": "2026-05-21T13:00:00Z",
            },
        ]
